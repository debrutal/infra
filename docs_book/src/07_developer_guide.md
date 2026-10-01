# Developer Guide (Entwicklerhandbuch)

Welcome to the **Developer Guide** for the Minisforum Infrastructure repository. This chapter details codebase conventions, environment setup, configuration patterns, and command invocations for developing, testing, and operating this infrastructure.

---

## 1. Environment & Prerequisites

### Required System Packages & Tools
- **OS**: Linux (Ubuntu 22.04 / 24.04 recommended)
- **Python**: `python3` (v3.10+) with `python3-venv`
- **Ansible**: `ansible-core` (v2.15+) and `ansible-lint`
- **Docker**: Engine & Docker Compose v2 plugin (`docker compose`)
- **Documentation Engine**: `mdbook` (v0.4+)

### Virtual Environment Setup
Always use the workspace virtual environment located at `.venv/`:

```bash
# Create virtual environment if missing
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.yml  # Python & Ansible requirements
```

---

## 2. Repository Conventions & Standards

### Naming Conventions
1. **Role Variable Prefixing**: Every variable declared within a role `defaults/main.yml` MUST be prefixed with `<role_name>_` (e.g., `lgtm_domain`, `gitea_site_url`, `traefik_network_name`).
2. **Vault Overrides**: Variable defaults should follow the pattern `{{ vault_<var_name> | default(default_admin_<property>) }}` to allow seamless override via Ansible Vault.
3. **Single Underscore Rule for Environment Variables**: All environment variable names in `docker-compose.yml.j2` templates and Ansible plays MUST use single underscores (e.g., `GF_SECURITY_ADMIN_USER`) rather than double underscores (`GF_SECURITY_ADMIN__USER`).

### Secret Management & Vault
- **Ansible Vault Password**: Stored locally in `.vault_pass` (or `.vault_password`).
- **Become / Sudo Password**: Stored locally in `.become_pass` (or `.become_password`).
- **Encrypted Variables**: Maintained in `inventory/group_vars/all/vault.yml`.

### Role Directory Pattern
All roles under `roles/<role_name>` must follow standard Ansible layout:
```text
roles/<role_name>/
├── defaults/
│   └── main.yml        # Role default variables (with fallback logic)
├── tasks/
│   └── main.yml        # Role execution tasks
├── templates/
│   └── *.j2            # Jinja2 configuration templates (docker-compose, configs)
└── handlers/
    └── main.yml        # Optional notification handlers (e.g. systemd/service restart)
```

---

## 3. Configuration Guide

### Target Hosts (`inventory/hosts.ini`)
Configures target IP addresses and connection settings:
```ini
[servers]
server192 ansible_host=192.168.1.8 ansible_user=debrutal
```

### Global Variables (`inventory/group_vars/all/all.yml`)
Central reference for shared domains, default admin credentials, and network names:
- **Base Domain**: `mini.debrutal.dev`
- **Traefik Network**: `traefik-net`
- **Default Admin**: `debrutal` (`duennes@gmail.com`)

---

## 4. Command Invocations & Workflows

### 1. Executing Infrastructure Deployment (`deploy.sh`)

The root `deploy.sh` script is the main CLI wrapper for running Ansible deployments.

```bash
# 1. Interactive Deployment Menu (launches CLI tag selector)
./deploy.sh

# 2. Targeted Tag Deployment
./deploy.sh -t lgtm                  # Deploy LGTM stack (Loki, Grafana, Tempo, Prometheus)
./deploy.sh -t traefik,gitea         # Deploy Traefik and Gitea
./deploy.sh -t all                   # Deploy full site.yml playbook

# 3. Dry-Run Verification (prints ansible-playbook command without executing)
./deploy.sh --dry-run
./deploy.sh -t lgtm --dry-run

# 4. Traefik Force Restart & ACME Reset
./deploy.sh --force-restart          # Force restart Traefik proxy
./deploy.sh --reset-acme             # Wipe acme.json and request fresh LE certificates
```

### 2. Inspecting Container Logs (`show_container_logs.sh`)

```bash
# View recent logs from all running containers
./show_container_logs.sh

# Follow logs in real-time filtered by container name
./show_container_logs.sh -f -g grafana
./show_container_logs.sh -f -g loki
```

### 3. Static Analysis & Linting

Run linters prior to committing changes:

```bash
# YAML formatting check
yamllint .

# Ansible best practices lint
ansible-lint .

# Playbook syntax verification
ansible-playbook site.yml --syntax-check
```

### 4. Running Test Suites (`tests/run_tests.sh`)

The project contains a comprehensive automated test framework:

```bash
# Fast Mode: Yamllint, Ansible-lint, syntax check, and Python unit tests
./tests/run_tests.sh fast

# Full Integration Mode: Executes against an isolated Docker container test fixture
./tests/run_tests.sh full

# Run individual Python unit test scripts
python3 tests/test_user_credentials.py
python3 tests/test_deploy_script.py
python3 tests/test_deployment.py
```

### 5. Building & Previewing Documentation (`mdbook`)

```bash
# Build static HTML documentation
cd docs_book && mdbook build

# Serve live preview on localhost:3000
cd docs_book && mdbook serve
```
