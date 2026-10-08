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

## 3. `podman` Role (Container Engine)
- **Purpose**: Deploys rootful Podman container engine with systemd socket emulation (`podman.socket`), Docker CLI wrapper (`podman-docker`), Docker Compose v2 compatibility, Netavark networking backend, and Aardvark DNS container name resolution.
- **Tasks (`roles/podman/tasks/main.yml`)**:
  - Configures `/etc/containers/containers.conf` (`netavark` backend, `k8s-file` logging driver).
  - Deploys `/etc/containers/registries.conf` with default registries.
  - Installs `podman`, `podman-docker`, `docker-compose-v2`, `netavark`, `aardvark-dns`.
  - Enables and starts `podman.socket`.
  - Symlinks `/var/run/docker.sock` to `/run/podman/podman.sock` for 100% Docker API compatibility.
  - Ensures `traefik-net` bridge network exists with DNS enabled.

## 3b. `docker` Role (Legacy Compatibility)
- **Purpose**: Legacy Docker CE engine installation role preserved for rollback and backward compatibility.

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

## 12. `lgtm` Role
- **Purpose**: Deploys the complete LGTM Observability Stack:
  - **Loki**: Log aggregation.
  - **Promtail**: Docker socket log shipper.
  - **Prometheus**: Time-series metrics collection.
  - **Tempo**: OTLP distributed tracing backend.
  - **Grafana**: Unified visualization UI with pre-provisioned datasources and Authentik OIDC integration.
- **Domain**: `grafana.mini.debrutal.dev`

## 13. `homepage` Role
- **Purpose**: Deploys Homepage central dashboard portal auto-populated with links and widgets for all infrastructure services.
- **Domain**: `dash.mini.debrutal.dev`

## 14. `bookorbit` Role
- **Purpose**: Deploys BookOrbit self-hosted library and reading platform with dedicated PostgreSQL and pgvector backend.
- **Domain**: `bookorbit.mini.debrutal.dev`

## 15. `agentzero` Role
- **Purpose**: Deploys Agent Zero AI agent framework container with optional tool execution and persistent workspace.
- **Domain**: `agentzero.mini.debrutal.dev`

## 16. `pinchflat` Role
- **Purpose**: Deploys Pinchflat YouTube media downloader and content archiver (powered by Elixir, Phoenix LiveView, and yt-dlp).
- **Domain**: `pinchflat.mini.debrutal.dev` (Port `8945`)
- **Key Features**:
  - Traefik HTTPS routing with automatic Let's Encrypt certificates.
  - Persistent volume mounts for configuration/database (`/opt/pinchflat/config`) and media library (`/opt/pinchflat/downloads`).
  - Authentik ForwardAuth Single Sign-On integration via Traefik middleware (with fallback basic authentication).
  - AutoKuma health monitoring integration (`/healthcheck`) and Homepage dashboard tile.

## 17. `ebook2audiobook` Role
- **Purpose**: Deploys eBook2Audiobook containerized platform to convert non-DRM e-books (.epub, .pdf, .mobi, .txt) into audiobooks with TTS engines and optional voice cloning.
- **Domain**: `ebook2audiobook.mini.debrutal.dev` (Port `7860`)
- **Key Features**:
  - Traefik HTTPS routing with automatic Let's Encrypt certificates.
  - Persistent volume mounts for ebooks (`/opt/ebook2audiobook/ebooks`), audiobooks (`/opt/ebook2audiobook/audiobooks`), models, voices, and tmp storage.
  - Authentik ForwardAuth Single Sign-On integration via Traefik middleware.
  - AutoKuma health monitoring and Homepage dashboard integration under Media & Knowledge.

## 18. `restic` Role (Automated Backups)
- **Purpose**: Provides automated, deduplicated, and encrypted backups for key components (Gitea, Authentik, BookOrbit) using Restic with local storage in `/backup`.
- **Target Repository**: `/backup/restic`
- **Staging Dumps Directory**: `/backup/dumps`
- **Key Features**:
  - Installs `restic` and `sqlite3` packages.
  - Safe, consistent database exports:
    - **Authentik**: `pg_dump` of PostgreSQL database (`authentik`).
    - **BookOrbit**: `pg_dump` of PostgreSQL database (`bookorbit`).
    - **Gitea**: Atomic SQLite `.backup` hot-dump of `/opt/gitea/data/gitea/gitea.db`.
  - Comprehensive Restic backup of database dumps and persistent application directories (`/opt/gitea`, `/opt/authentik`, `/opt/bookorbit`), excluding ephemeral/recreatable cache and raw database storage.
  - Retention & pruning policy: `--keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune`.
  - Automated systemd timer (`restic-backup.timer`) scheduled daily at 03:00.
  - Administrative CLI wrapper `/usr/local/bin/restic-infra` for one-command inspection (`sudo restic-infra snapshots`, `sudo restic-infra check`).
