#!/usr/bin/env bash
# ==============================================================================
# Script: deploy.sh
# Purpose: Execute Ansible deployment with customizable options.
# Default: Asks for vault password & sudo password, forces Traefik restart and ACME reset.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PLAYBOOK="site.yml"
TAGS="traefik,gitea"
ASK_VAULT=1
ASK_BECOME=1
FORCE_RESTART=0
RESET_ACME=0
VAULT_PASS_FILE=""
BECOME_PASS_FILE=""
EXTRA_VARS=()
EXTRA_ANSIBLE_ARGS=()
DRY_RUN=0
INTERACTIVE=0

# Auto-detect default secret password files in repo root
if [[ -f "$SCRIPT_DIR/.vault_pass" ]]; then
  VAULT_PASS_FILE="$SCRIPT_DIR/.vault_pass"
  ASK_VAULT=0
elif [[ -f "$SCRIPT_DIR/.vault_password" ]]; then
  VAULT_PASS_FILE="$SCRIPT_DIR/.vault_password"
  ASK_VAULT=0
fi

if [[ -f "$SCRIPT_DIR/.become_pass" ]]; then
  BECOME_PASS_FILE="$SCRIPT_DIR/.become_pass"
  ASK_BECOME=0
elif [[ -f "$SCRIPT_DIR/.become_password" ]]; then
  BECOME_PASS_FILE="$SCRIPT_DIR/.become_password"
  ASK_BECOME=0
fi

# Auto-enable interactive mode if run with no arguments in an interactive terminal
if [[ $# -eq 0 && -t 0 ]]; then
  INTERACTIVE=1
fi

usage() {
  cat << 'EOF'
Usage: ./deploy.sh [OPTIONS] [-- ANSIBLE_OPTIONS]

Deploy infrastructure using Ansible playbook site.yml.

Defaults:
  - Uses .vault_pass or .vault_password if present (otherwise --ask-vault-pass)
  - Uses .become_pass or .become_password if present (otherwise -K)
  - Preserves Traefik ACME certificate storage
  - Filters by tags: traefik,gitea
  - Launches interactive CLI menu if run without arguments in a terminal

Options:
  -i, --interactive            Launch interactive CLI menu to select tags and configure options
  -t, --tags TAGS              Ansible tags to run (default: "traefik,gitea", use "all" to run full playbook)
  --reset-acme                 Reset / wipe Traefik ACME certificate storage (requests fresh certificates)
  --force-restart              Force restart Traefik container
  --no-vault                   Do not prompt for Vault password or use vault pass file
  --vault-pass-file FILE       Path to Ansible Vault password file
  --no-become                  Do not prompt for sudo / become password (-K) or use become pass file
  --become-pass-file FILE      Path to Ansible become / sudo password file
  -e, --extra-vars VARS        Pass extra variables to ansible-playbook (can be specified multiple times)
  --dry-run                    Print the ansible-playbook command without executing it
  -h, --help                   Display this help message and exit

Examples:
  ./deploy.sh                                      # Interactive deployment menu (if terminal) or default execution
  ./deploy.sh -i                                   # Force launch interactive deployment CLI menu
  ./deploy.sh -t traefik                           # Deploy only traefik role
  ./deploy.sh -t all                               # Deploy all roles in site.yml
  ./deploy.sh --reset-acme                         # Force wipe acme.json and request new certs
  ./deploy.sh --vault-pass-file ~/.vault_pass.txt  # Use custom vault password file
  ./deploy.sh --dry-run                            # Show the command that would be executed
EOF
}

# Parse options
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--interactive)
      INTERACTIVE=1
      shift
      ;;
    -t|--tags)
      if [[ -z "${2:-}" ]]; then
        echo "Error: Option $1 requires an argument." >&2
        exit 1
      fi
      TAGS="$2"
      shift 2
      ;;
    --reset-acme)
      RESET_ACME=1
      shift
      ;;
    --no-reset)
      RESET_ACME=0
      shift
      ;;
    --force-restart)
      FORCE_RESTART=1
      shift
      ;;
    --no-restart)
      FORCE_RESTART=0
      shift
      ;;
    --no-vault)
      ASK_VAULT=0
      VAULT_PASS_FILE=""
      shift
      ;;
    --vault-pass-file|--vault-password-file)
      if [[ -z "${2:-}" ]]; then
        echo "Error: Option $1 requires an argument." >&2
        exit 1
      fi
      VAULT_PASS_FILE="$2"
      ASK_VAULT=0
      shift 2
      ;;
    --no-become)
      ASK_BECOME=0
      BECOME_PASS_FILE=""
      shift
      ;;
    --become-pass-file|--become-password-file)
      if [[ -z "${2:-}" ]]; then
        echo "Error: Option $1 requires an argument." >&2
        exit 1
      fi
      BECOME_PASS_FILE="$2"
      ASK_BECOME=0
      shift 2
      ;;
    -e|--extra-vars)
      if [[ -z "${2:-}" ]]; then
        echo "Error: Option $1 requires an argument." >&2
        exit 1
      fi
      EXTRA_VARS+=("-e" "$2")
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA_ANSIBLE_ARGS+=("$@")
      break
      ;;
    *)
      # Pass through any unknown options to ansible-playbook
      EXTRA_ANSIBLE_ARGS+=("$1")
      shift
      ;;
  esac
done

run_interactive_cli() {
  local tag_keys=("traefik" "gitea" "runner" "common" "podman" "docker" "lago" "invoiceninja" "espocrm" "uptime_kuma" "sentry" "authentik" "homepage" "fusion" "lgtm" "bookorbit" "all")
  local tag_labels=(
    "traefik        - Traefik reverse proxy & ACME SSL"
    "gitea          - Gitea self-hosted Git service"
    "runner         - Gitea Act Runner / CI build runners"
    "common         - Base system packages & firewall"
    "podman         - Podman engine, socket & netavark"
    "docker         - Docker compatibility alias"
    "lago           - Lago usage-based billing platform"
    "invoiceninja   - Invoice Ninja billing & invoicing"
    "espocrm        - EspoCRM customer management"
    "uptime_kuma    - Uptime Kuma monitoring & status"
    "sentry         - Sentry error tracking platform"
    "authentik      - Authentik SSO & identity provider"
    "homepage       - Homepage dashboard portal"
    "fusion         - Fusion native host app & systemd service"
    "lgtm           - LGTM stack (Loki, Grafana, Tempo, Prometheus)"
    "bookorbit      - BookOrbit self-hosted library & reading platform"
    "all            - Run full playbook (all roles)"
  )

  # Initialize selections based on current $TAGS
  local selected=()
  for key in "${tag_keys[@]}"; do
    if [[ ",$TAGS," == *",$key,"* || ( "$TAGS" == "all" && "$key" == "all" ) ]]; then
      selected+=(1)
    else
      selected+=(0)
    fi
  done

  # Colors (if stdout is a terminal)
  local BOLD="" CYAN="" GREEN="" YELLOW="" NC=""
  if [[ -t 1 && "${TERM:-}" != "dumb" ]]; then
    BOLD='\033[1m'
    CYAN='\033[0;36m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    NC='\033[0m'
  fi

  while true; do
    echo -e "${BOLD}${CYAN}==================================================================${NC}"
    echo -e "${BOLD}${CYAN}  Ansible Infrastructure Deployment CLI - Select Tags${NC}"
    echo -e "${BOLD}${CYAN}==================================================================${NC}"
    echo -e "Toggle tags by entering numbers (e.g. '1 4 5' or '1,4')."
    echo -e "Commands: ${BOLD}a${NC} (all), ${BOLD}n${NC} (none), ${BOLD}d${NC} (defaults), ${BOLD}c${NC} or ${BOLD}ENTER${NC} (confirm)\n"

    for i in "${!tag_keys[@]}"; do
      num=$((i + 1))
      if [[ "${selected[$i]}" -eq 1 ]]; then
        mark="${GREEN}[*]${NC}"
      else
        mark="[ ]"
      fi
      printf "  [%2d] %b %s\n" "$num" "$mark" "${tag_labels[$i]}"
    done

    echo ""
    read -rp "Selection [c to confirm]: " input || input=""
    input=$(echo "$input" | xargs)

    if [[ -z "$input" || "$input" == "c" || "$input" == "C" ]]; then
      break
    elif [[ "$input" == "a" || "$input" == "A" ]]; then
      for i in "${!selected[@]}"; do selected[$i]=1; done
    elif [[ "$input" == "n" || "$input" == "N" ]]; then
      for i in "${!selected[@]}"; do selected[$i]=0; done
    elif [[ "$input" == "d" || "$input" == "D" ]]; then
      for i in "${!tag_keys[@]}"; do
        if [[ "${tag_keys[$i]}" =~ ^(traefik|gitea)$ ]]; then
          selected[$i]=1
        else
          selected[$i]=0
        fi
      done
    else
      IFS=', ' read -r -a choices <<< "$input"
      for choice in "${choices[@]}"; do
        if [[ "$choice" =~ ^[0-9]+$ ]]; then
          idx=$((choice - 1))
          if [[ $idx -ge 0 && $idx -lt ${#selected[@]} ]]; then
            if [[ "${selected[$idx]}" -eq 1 ]]; then
              selected[$idx]=0
            else
              selected[$idx]=1
            fi
          fi
        fi
      done
    fi
  done

  # Build selected tags list
  local active_tags=()
  for i in "${!tag_keys[@]}"; do
    if [[ "${selected[$i]}" -eq 1 ]]; then
      active_tags+=("${tag_keys[$i]}")
    fi
  done

  if [[ ${#active_tags[@]} -eq 0 ]]; then
    echo -e "${YELLOW}No tags selected. Defaulting to 'traefik,gitea'.${NC}"
    TAGS="traefik,gitea"
    active_tags=("traefik" "gitea")
  else
    TAGS=$(IFS=,; echo "${active_tags[*]}")
  fi

  echo -e "\n${BOLD}${CYAN}==================================================================${NC}"
  echo -e "${BOLD}${CYAN}  Configure Optional Parameters for Selected Tags${NC}"
  echo -e "${BOLD}${CYAN}==================================================================${NC}"

  for tag in "${active_tags[@]}"; do
    if [[ "$tag" == "traefik" ]]; then
      echo -e "\n${BOLD}[traefik]${NC}"
      local default_restart="N"
      [[ "$FORCE_RESTART" -eq 1 ]] && default_restart="Y"
      read -rp "  - Force restart Traefik container? [y/N] (default $default_restart): " resp || resp=""
      if [[ "$resp" =~ ^[Yy]$ || ( -z "$resp" && "$default_restart" == "Y" ) ]]; then
        FORCE_RESTART=1
      elif [[ -n "$resp" ]]; then
        FORCE_RESTART=0
      fi

      local default_acme="N"
      [[ "$RESET_ACME" -eq 1 ]] && default_acme="Y"
      read -rp "  - Reset ACME certificate storage (wipe acme.json)? [y/N] (default $default_acme): " resp || resp=""
      if [[ "$resp" =~ ^[Yy]$ || ( -z "$resp" && "$default_acme" == "Y" ) ]]; then
        RESET_ACME=1
      elif [[ -n "$resp" ]]; then
        RESET_ACME=0
      fi

    elif [[ "$tag" == "runner" ]]; then
      echo -e "\n${BOLD}[runner]${NC}"
      read -rp "  - Enable Gitea CI Act Runners? [Y/n]: " resp || resp=""
      if [[ "$resp" =~ ^[Nn]$ ]]; then
        EXTRA_VARS+=("-e" "gitea_runner_enabled=false")
      else
        EXTRA_VARS+=("-e" "gitea_runner_enabled=true")
        read -rp "  - Number of runner instances [default 1]: " count_resp || count_resp=""
        if [[ "$count_resp" =~ ^[0-9]+$ ]]; then
          EXTRA_VARS+=("-e" "gitea_runner_count=$count_resp")
        fi
      fi
      read -rp "  - Force restart CI Runner containers? [y/N]: " resp || resp=""
      if [[ "$resp" =~ ^[Yy]$ ]]; then
        EXTRA_VARS+=("-e" "runner_force_restart=true")
      fi

    elif [[ "$tag" == "all" ]]; then
      echo -e "\n${BOLD}[all]${NC}"
      read -rp "  - Force restart Traefik container? [y/N]: " resp || resp=""
      [[ "$resp" =~ ^[Yy]$ ]] && FORCE_RESTART=1
      read -rp "  - Reset ACME certificate storage? [y/N]: " resp || resp=""
      [[ "$resp" =~ ^[Yy]$ ]] && RESET_ACME=1
      read -rp "  - Force restart all service containers? [y/N]: " resp || resp=""
      if [[ "$resp" =~ ^[Yy]$ ]]; then
        EXTRA_VARS+=("-e" "all_force_restart=true")
      fi

    else
      echo -e "\n${BOLD}[$tag]${NC}"
      read -rp "  - Force restart $tag container/service? [y/N]: " resp || resp=""
      if [[ "$resp" =~ ^[Yy]$ ]]; then
        EXTRA_VARS+=("-e" "${tag}_force_restart=true")
      fi
    fi
  done

  echo -e "\n${BOLD}${CYAN}==================================================================${NC}"
  echo -e "${BOLD}${CYAN}  Global Options${NC}"
  echo -e "${BOLD}${CYAN}==================================================================${NC}"

  local default_dry="N"
  [[ "$DRY_RUN" -eq 1 ]] && default_dry="Y"
  read -rp "Enable dry-run mode (print command without executing)? [y/N] (default $default_dry): " resp || resp=""
  if [[ "$resp" =~ ^[Yy]$ || ( -z "$resp" && "$default_dry" == "Y" ) ]]; then
    DRY_RUN=1
  elif [[ -n "$resp" ]]; then
    DRY_RUN=0
  fi

  read -rp "Extra Ansible variables (e.g. key=val, press ENTER for none): " extra_input || extra_input=""
  if [[ -n "$extra_input" ]]; then
    for item in $extra_input; do
      EXTRA_VARS+=("-e" "$item")
    done
  fi
}

if [[ "$INTERACTIVE" -eq 1 ]]; then
  run_interactive_cli
fi

# Build command array
CMD=("ansible-playbook" "$PLAYBOOK")

if [[ -n "$TAGS" && "$TAGS" != "all" ]]; then
  CMD+=("--tags" "$TAGS")
fi

if [[ -n "$VAULT_PASS_FILE" ]]; then
  CMD+=("--vault-password-file" "$VAULT_PASS_FILE")
elif [[ "$ASK_VAULT" -eq 1 ]]; then
  CMD+=("--ask-vault-pass")
fi

if [[ -n "$BECOME_PASS_FILE" ]]; then
  CMD+=("--become-password-file" "$BECOME_PASS_FILE")
elif [[ "$ASK_BECOME" -eq 1 ]]; then
  CMD+=("-K")
fi

if [[ "$FORCE_RESTART" -eq 1 ]]; then
  CMD+=("-e" "traefik_force_restart=true")
else
  CMD+=("-e" "traefik_force_restart=false")
fi

if [[ "$RESET_ACME" -eq 1 ]]; then
  CMD+=("-e" "traefik_reset_acme=true")
else
  CMD+=("-e" "traefik_reset_acme=false")
fi

if [[ ${#EXTRA_VARS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_VARS[@]}")
fi

if [[ ${#EXTRA_ANSIBLE_ARGS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_ANSIBLE_ARGS[@]}")
fi

echo "=================================================================="
echo " Running Ansible Deployment"
echo " Command: ${CMD[*]}"
echo "=================================================================="

if [[ "$INTERACTIVE" -eq 1 ]]; then
  read -rp "Proceed with deployment? [Y/n]: " confirm || confirm=""
  if [[ "$confirm" =~ ^[Nn]$ ]]; then
    echo "Deployment cancelled."
    exit 0
  fi
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[DRY RUN] Command not executed."
  exit 0
fi

exec "${CMD[@]}"

