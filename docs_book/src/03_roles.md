# Ansible Roles Reference

This chapter documents each Ansible role, its task flow, Jinja2 templates, and handlers.

## 1. `common` Role
- **Purpose**: Installs base system packages required across all server management operations.
- **Tasks (`roles/common/tasks/main.yml`)**:
  - Updates APT cache.
  - Installs packages listed in `common_packages` (`git`, `jq`, `curl`, `wget`, `ca-certificates`, `gnupg`, `lsb-release`, `tar`, `unzip`, `ripgrep`).

## 2. `neovim` Role
- **Purpose**: Deploys the latest binary release of Neovim directly from GitHub releases.
- **Key Features**:
  - **Stat Check**: Checks if `/opt/nvim/bin/nvim` already exists for idempotence.
  - **Extraction**: Downloads `nvim-linux-x86_64.tar.gz` to `/tmp` and extracts it into `/opt/nvim`.
  - **PATH Symlink**: Creates a symbolic link from `/opt/nvim/bin/nvim` to `/usr/local/bin/nvim`.

## 3. `docker` Role
- **Purpose**: Configures official Docker APT repository and installs Docker Engine, CLI, Containerd, Buildx, and Compose plugins.
- **Tasks (`roles/docker/tasks/main.yml`)**:
  - Creates `/etc/apt/keyrings` directory (`0755`).
  - Configures GPG key and APT repository.
  - Installs `docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin`.
  - Adds configured users to `docker` group.

## 4. `traefik` Role
- **Purpose**: Deploys Traefik v3 reverse proxy container, static/dynamic YAML configurations, and ACME certificate storage.
- **Tasks (`roles/traefik/tasks/main.yml`)**:
  - Ensures external Docker network `traefik-net` exists.
  - Creates `/opt/traefik/acme/acme.json` (`0600`).
  - Deploys `traefik.yml` (static config) with Cloudflare DNS-01 challenge settings.
  - Deploys `dynamic_conf.yml` (TLS default certs & host gateway routing).
  - Deploys `docker-compose.yml`.

## 5. `lago` Role
- **Purpose**: Deploys Lago usage-based billing platform.
- **Domain**: `lago.mini.debrutal.dev` & `lago-api.mini.debrutal.dev`

## 6. `invoiceninja` Role
- **Purpose**: Deploys Invoice Ninja billing & invoicing application with Nginx vhost proxy.
- **Domain**: `invoiceninja.mini.debrutal.dev`

## 7. `espocrm` Role
- **Purpose**: Deploys EspoCRM Customer Relationship Management platform with MariaDB backend.
- **Domain**: `espocrm.mini.debrutal.dev`

## 8. `uptime_kuma` Role
- **Purpose**: Deploys Uptime Kuma health & status page monitoring system with AutoKuma automated discovery.
- **Domain**: `status.mini.debrutal.dev`

## 9. `sentry` Role
- **Purpose**: Deploys Sentry (GlitchTip) application error tracking platform.
- **Domain**: `sentry.mini.debrutal.dev`

## 10. `gitea` Role
- **Purpose**: Deploys Gitea self-hosted Git service alongside containerized Gitea Act Runner CI/CD builders.
- **Domain**: `gitea.mini.debrutal.dev`

## 11. `authentik` Role
- **Purpose**: Deploys Authentik Identity Provider & Single Sign-On server with PostgreSQL and Redis backends. Automatically registers OIDC providers for applications (Gitea, Grafana).
- **Domain**: `authentik.mini.debrutal.dev`

## 12. `fusion` Role
- **Purpose**: Configures native host service binary and systemd unit file (`/etc/systemd/system/fusion.service`).
- **Domain**: `fusion.mini.debrutal.dev` (Port `4040`)

## 13. `lgtm` Role
- **Purpose**: Deploys the complete LGTM Observability Stack:
  - **Loki**: Log aggregation.
  - **Promtail**: Docker socket log shipper.
  - **Prometheus**: Time-series metrics collection.
  - **Tempo**: OTLP distributed tracing backend.
  - **Grafana**: Unified visualization UI with pre-provisioned datasources and Authentik OIDC integration.
- **Domain**: `grafana.mini.debrutal.dev`

## 14. `homepage` Role
- **Purpose**: Deploys Homepage central dashboard portal auto-populated with links and widgets for all infrastructure services.
- **Domain**: `dash.mini.debrutal.dev`
