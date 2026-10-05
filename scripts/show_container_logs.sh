#!/usr/bin/env bash
# ==============================================================================
# Script: show_container_logs.sh
# Purpose: Display or stream logs from all running (or all existing) Docker containers.
# Supports local containers and remote target servers (via -H / --host or -r / --remote).
# ==============================================================================

set -euo pipefail

SHOW_ALL=0
FOLLOW=0
TAIL_LINES="50"
SHOW_TIMESTAMPS=0
SINCE_TIME=""
FILTER_PATTERN=""
USE_COLOR=1
DOCKER_TARGET_HOST=""
REMOTE_SSH_TARGET=""

# Helper function to print usage / help
usage() {
  cat << 'EOF'
Usage: show_container_logs.sh [OPTIONS]

Display or stream logs of Docker containers.

Options:
  -f, --follow           Follow / stream log output continuously
  -a, --all              Include stopped containers (default: running only)
  -n, --tail LINES       Number of lines to show from the end of each log (default: 50, use 'all' for full log)
  -t, --timestamps       Show timestamps in log output
  --since TIME           Show logs since duration or timestamp (e.g., 10m, 1h, 2026-09-18T00:00:00)
  -g, --filter PATTERN   Filter containers matching pattern in name or ID
  -H, --host DOCKER_HOST Specify Docker daemon socket/host (e.g. tcp://192.168.1.8:2375 or ssh://user@192.168.1.8)
  -r, --remote USER@HOST Target a remote server via SSH (e.g. debrutal@192.168.1.8)
  --no-color             Disable colored container name tags
  -h, --help             Display this help message and exit

Examples:
  ./show_container_logs.sh                           # View last 50 lines of local running containers
  ./show_container_logs.sh -f                        # Stream logs from all local running containers in real-time
  ./show_container_logs.sh -r debrutal@192.168.1.8  # View last 50 lines of containers on target server 192.168.1.8
  ./show_container_logs.sh -a -n 100                 # View last 100 lines for all containers (including stopped)
  ./show_container_logs.sh -g traefik -f             # Stream logs for containers matching 'traefik'
EOF
  exit 0
}

# Parse command line options
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--follow)
      FOLLOW=1
      shift
      ;;
    -a|--all)
      SHOW_ALL=1
      shift
      ;;
    -n|--tail)
      if [[ -n "${2:-}" && ! "$2" =~ ^- ]]; then
        TAIL_LINES="$2"
        shift 2
      else
        echo "Error: --tail requires an argument (e.g. 50 or all)." >&2
        exit 1
      fi
      ;;
    -t|--timestamps)
      SHOW_TIMESTAMPS=1
      shift
      ;;
    --since)
      if [[ -n "${2:-}" && ! "$2" =~ ^- ]]; then
        SINCE_TIME="$2"
        shift 2
      else
        echo "Error: --since requires a timestamp or duration argument." >&2
        exit 1
      fi
      ;;
    -g|--filter)
      if [[ -n "${2:-}" && ! "$2" =~ ^- ]]; then
        FILTER_PATTERN="$2"
        shift 2
      else
        echo "Error: --filter requires a pattern argument." >&2
        exit 1
      fi
      ;;
    -H|--host)
      if [[ -n "${2:-}" && ! "$2" =~ ^- ]]; then
        DOCKER_TARGET_HOST="$2"
        shift 2
      else
        echo "Error: --host requires a host URL argument." >&2
        exit 1
      fi
      ;;
    -r|--remote)
      if [[ -n "${2:-}" && ! "$2" =~ ^- ]]; then
        REMOTE_SSH_TARGET="$2"
        shift 2
      else
        echo "Error: --remote requires a USER@HOST argument (e.g. debrutal@192.168.1.8)." >&2
        exit 1
      fi
      ;;
    --no-color)
      USE_COLOR=0
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Error: Unknown option '$1'" >&2
      echo "Run '$0 --help' for usage." >&2
      exit 1
      ;;
  esac
done

# Build base Docker command array
if [[ -n "$REMOTE_SSH_TARGET" ]]; then
  DOCKER_BASE_CMD=("ssh" "$REMOTE_SSH_TARGET" "sudo docker")
elif [[ -n "$DOCKER_TARGET_HOST" ]]; then
  DOCKER_BASE_CMD=("docker" "-H" "$DOCKER_TARGET_HOST")
else
  DOCKER_BASE_CMD=("docker")
fi

# Verify Docker availability
if [[ -z "$REMOTE_SSH_TARGET" ]] && ! command -v docker &> /dev/null; then
  echo "Error: 'docker' command line tool is not installed or not in PATH." >&2
  exit 1
fi

# Build docker ps command
DOCKER_PS_ARGS=("--format" '{{.ID}}\t{{.Names}}\t{{.Status}}')
if [[ "$SHOW_ALL" -eq 1 ]]; then
  DOCKER_PS_CMD=("${DOCKER_BASE_CMD[@]}" "ps" "-a" "${DOCKER_PS_ARGS[@]}")
else
  DOCKER_PS_CMD=("${DOCKER_BASE_CMD[@]}" "ps" "${DOCKER_PS_ARGS[@]}")
fi

# Fetch containers list: ID, Name, Status
PS_ERR_FILE=$(mktemp)
CONTAINER_LIST=$("${DOCKER_PS_CMD[@]}" 2>"$PS_ERR_FILE" || true)
PS_ERR=$(cat "$PS_ERR_FILE")
rm -f "$PS_ERR_FILE"

if [[ -n "$PS_ERR" && -z "$CONTAINER_LIST" ]]; then
  echo "Error connecting to Docker daemon:" >&2
  echo "$PS_ERR" >&2
  echo "" >&2
  echo "Tip: Ensure Docker is running, or run with 'sudo' / add your user to the 'docker' group." >&2
  echo "Tip: For remote servers, pass '-r user@192.168.1.8' or '-H ssh://user@192.168.1.8'." >&2
  exit 1
fi

if [[ -z "$CONTAINER_LIST" ]]; then
  echo "No containers found."
  exit 0
fi

# Filter containers if FILTER_PATTERN is set
if [[ -n "$FILTER_PATTERN" ]]; then
  CONTAINER_LIST=$(echo "$CONTAINER_LIST" | grep -iE "$FILTER_PATTERN" || true)
fi

if [[ -z "$CONTAINER_LIST" ]]; then
  echo "No containers matched filter pattern: '$FILTER_PATTERN'"
  exit 0
fi

# Build docker logs base flags
LOG_FLAGS=()
if [[ "$TAIL_LINES" != "all" ]]; then
  LOG_FLAGS+=("--tail" "$TAIL_LINES")
fi
if [[ "$SHOW_TIMESTAMPS" -eq 1 ]]; then
  LOG_FLAGS+=("--timestamps")
fi
if [[ -n "$SINCE_TIME" ]]; then
  LOG_FLAGS+=("--since" "$SINCE_TIME")
fi

# ANSI Colors for container tags
COLORS=(
  "\033[1;32m" # Green
  "\033[1;36m" # Cyan
  "\033[1;33m" # Yellow
  "\033[1;35m" # Magenta
  "\033[1;34m" # Blue
  "\033[1;92m" # Light Green
  "\033[1;96m" # Light Cyan
  "\033[1;93m" # Light Yellow
)
COLOR_RESET="\033[0m"

# Count containers
CONTAINER_COUNT=$(echo "$CONTAINER_LIST" | wc -l | tr -d ' ')

if [[ "$FOLLOW" -eq 1 ]]; then
  echo "================================================================="
  echo " Streaming logs from $CONTAINER_COUNT container(s) (Press Ctrl+C to stop)..."
  echo "================================================================="

  PIDS=()

  cleanup() {
    echo -e "\nStopping log streams..."
    for pid in "${PIDS[@]}"; do
      kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    exit 0
  }

  trap cleanup SIGINT SIGTERM EXIT

  COLOR_INDEX=0

  while IFS=$'\t' read -r c_id c_name c_status; do
    if [[ -z "$c_id" ]]; then continue; fi
    if [[ "$USE_COLOR" -eq 1 ]]; then
      COLOR="${COLORS[$((COLOR_INDEX % ${#COLORS[@]}))]}"
      COLOR_INDEX=$((COLOR_INDEX + 1))
      TAG="${COLOR}[${c_name}]${COLOR_RESET}"
    else
      TAG="[${c_name}]"
    fi

    # Stream logs in background with line prefixing
    "${DOCKER_BASE_CMD[@]}" logs -f "${LOG_FLAGS[@]}" "$c_id" 2>&1 | awk -v tag="$TAG " '{ print tag $0; fflush() }' &
    PIDS+=("${!}")
  done <<< "$CONTAINER_LIST"

  # Wait for all background tasks
  wait "${PIDS[@]}" 2>/dev/null || true

else
  echo "================================================================="
  echo " Displaying logs from $CONTAINER_COUNT container(s)..."
  echo "================================================================="

  while IFS=$'\t' read -r c_id c_name c_status; do
    if [[ -z "$c_id" ]]; then continue; fi
    echo ""
    echo "-----------------------------------------------------------------"
    if [[ "$USE_COLOR" -eq 1 ]]; then
      echo -e "\033[1;34m=== Container: ${c_name} (ID: ${c_id:0:12}) | Status: ${c_status} ===\033[0m"
    else
      echo "=== Container: ${c_name} (ID: ${c_id:0:12}) | Status: ${c_status} ==="
    fi
    echo "-----------------------------------------------------------------"

    "${DOCKER_BASE_CMD[@]}" logs "${LOG_FLAGS[@]}" "$c_id" 2>&1 || echo "[Error reading logs for $c_name]"
  done <<< "$CONTAINER_LIST"

  echo ""
  echo "================================================================="
  echo " End of container logs"
  echo "================================================================="
fi
