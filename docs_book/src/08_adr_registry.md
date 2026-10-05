# Architectural Decision Records (ADR) Registry

This section serves as the **Architectural Decision Record (ADR)** registry for the Minisforum infrastructure repository. It documents explicit design choices, their rationale, context, and long-term implications.

---

## Index of Architectural Decision Records

| ADR ID | Title | Status | Date |
| :--- | :--- | :--- | :--- |
| **ADR-001** | Containerized Service Architecture with Docker Compose & Traefik | **Accepted** | 2026-09-17 |
| **ADR-002** | Cloudflare DNS-01 ACME Challenge for Wildcard SSL Certificates | **Accepted** | 2026-09-17 |
| **ADR-003** | Single Underscore Environment Variable Naming Standard | **Accepted** | 2026-09-18 |
| **ADR-004** | Centralized Authentik Single Sign-On (SSO) & ForwardAuth | **Accepted** | 2026-09-22 |
| **ADR-005** | Unified LGTM Observability Stack (Loki, Grafana, Tempo, Prometheus) | **Accepted** | 2026-09-26 |
| **ADR-006** | Dual-Layer Automated Testing (Unit Tests & Container Test Fixtures) | **Accepted** | 2026-09-25 |

---

## ADR-001: Containerized Service Architecture with Docker Compose & Traefik

### Status
**Accepted**

### Context
The infrastructure hosts multiple disparate applications (Gitea, Authentik, Lago, Invoice Ninja, EspoCRM, Sentry, Uptime Kuma, Homepage, LGTM Stack) on server `192.168.1.8`. Installing all applications directly on the host system creates dependency conflicts, complex systemd service configurations, and difficult backup/upgrade paths.

### Decision
We standardize on containerizing all application services using **Docker Compose v2** (`community.docker.docker_compose_v2`), fronted by a single unified **Traefik v3** edge reverse proxy attached to a shared Docker network (`traefik-net`).

### Consequences
- **Pros**:
  - Application isolation: dependencies, databases, and runtimes remain isolated within Compose environments.
  - Zero-downtime routing: Traefik automatically discovers containers dynamically via Docker socket labels (`traefik.enable=true`).
  - Idempotent configuration: Each service has an explicit `/opt/<service>/docker-compose.yml` managed by Ansible templates.
- **Cons**:
  - Small overhead from Docker containerization.
  - Port binding must be managed to prevent port collisions on host interfaces.

---

## ADR-002: Cloudflare DNS-01 ACME Challenge for Wildcard SSL Certificates

### Status
**Accepted**

### Context
Server `192.168.1.8` resides on an internal local network. Traditional Let's Encrypt HTTP-01 or TLS-ALPN-01 ACME challenges require public port 80/443 exposure from the internet, which is insecure and impractical for internal infrastructure subdomains under `*.mini.debrutal.dev`.

### Decision
We use Traefik's **Cloudflare DNS-01 ACME challenge provider** (`traefik_acme_challenge_type: "dns"`). Traefik uses Cloudflare API tokens (`CF_DNS_API_TOKEN`) to temporarily publish DNS TXT records (`_acme-challenge.mini.debrutal.dev`) to complete Let's Encrypt validation.

### Consequences
- **Pros**:
  - Wildcard certificates (`mini.debrutal.dev`, `*.mini.debrutal.dev`) are requested and renewed automatically.
  - No inbound internet ports (80/443) need to be forwarded through network firewalls.
- **Cons**:
  - Requires valid Cloudflare API tokens stored in Ansible Vault (`vault.yml`).

---

## ADR-003: Single Underscore Environment Variable Naming Standard

### Status
**Accepted**

### Context
In various deployment frameworks, environment variables with double underscores (e.g., `GF_SECURITY_ADMIN__PASSWORD` or `APP__CONFIG`) are sometimes used for nested configuration overrides. However, double underscores introduce variable interpolation issues in POSIX bash scripts, Ansible Jinja2 template parser edge cases, and linters.

### Decision
We enforce a strict project convention: **All environment variables declared in Docker Compose templates and Ansible tasks MUST use single underscores (`_`) instead of double underscores (`__`).**

### Consequences
- **Pros**:
  - 100% shell and Jinja2 parser safety across all deployment scripts and CI runtimes.
  - Eliminates syntax errors during Ansible template evaluation.
- **Cons**:
  - Nested configuration properties must be formatted using standard single-underscore environment variables supported by target applications (e.g., `GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`).

---

## ADR-004: Centralized Authentik Single Sign-On (SSO) & ForwardAuth

### Status
**Accepted**

### Context
Managing separate local user accounts across multiple services (Gitea, Grafana, Homepage, etc.) increases administrative burden and security risks.

### Decision
We implement **Authentik** (`roles/authentik`) as the central Identity Provider (IdP) for the infrastructure. Services integrate via OIDC/OAuth2 (Gitea, Grafana) or ForwardAuth proxying (Homepage).

### Consequences
- **Pros**:
  - Single Sign-On (SSO) experience across all infrastructure portals.
  - Automated provisioning: `roles/authentik/tasks/main.yml` automatically registers OIDC clients and proxy providers upon deployment.
- **Cons**:
  - Authentik becomes a critical core dependency for authentication. Fallback local admin accounts are maintained for emergency break-glass access.

---

## ADR-005: Unified LGTM Observability Stack (Loki, Grafana, Tempo, Prometheus)

### Status
**Accepted**

### Context
Monitoring logs, metrics, and distributed traces across 10+ containerized applications requires an integrated observability platform. Deploying monitoring components as disconnected roles leads to fragmented dashboards and broken cross-correlations.

### Decision
We deploy the complete **LGTM Stack** within a unified role (`roles/lgtm`):
- **Loki** (`3.2.0`): Log aggregation.
- **Promtail** (`3.2.0`): Container log collection via Docker socket.
- **Prometheus** (`v2.54.1`): Time-series metrics DB.
- **Tempo** (`2.6.0`): Distributed tracing backend (OTLP gRPC/HTTP).
- **Grafana** (`11.2.0`): Unified UI with auto-provisioned datasources and pre-linked trace-to-log and trace-to-metric correlations.

### Consequences
- **Pros**:
  - Single command deployment (`./deploy.sh -t lgtm`).
  - Seamless navigation between traces (Tempo), logs (Loki), and metrics (Prometheus) inside Grafana.
  - Auto-provisioned Datasources (`grafana-datasources.yaml.j2`).
- **Cons**:
  - Requires sufficient memory resources to run the observability containers.

---

## ADR-006: Dual-Layer Automated Testing Strategy

### Status
**Accepted**

### Context
Deploying infrastructure updates directly to live production servers without automated verification risks introducing runtime misconfigurations or broken routes.

### Decision
We implement a **Dual-Layer Testing Strategy**:
1. **Fast Static & Unit Testing Layer**: `yamllint`, `ansible-lint`, playbook syntax checks, and Python unit tests (`test_deploy_script.py`, `test_user_credentials.py`).
2. **Containerized Integration Test Fixture Layer**: `test_deployment.py` provisions a temporary Ubuntu Docker container (`infra-test-container`), executes the complete Ansible playbook against it, and validates generated files, unit permissions, and compose structures before tearing down the container.

### Consequences
- **Pros**:
  - 100% reproducible deployment testing without modifying live server state.
  - Executed via `./tests/run_tests.sh full`.
- **Cons**:
  - Integration tests require local Docker daemon access.

---

## ADR-007: Migration from Docker Engine to Rootful Podman Architecture

### Status
**Accepted**

### Context
The platform runs 12+ multi-container stacks orchestrated via Docker Compose v2. To eliminate Docker daemon overhead, align with modern OCI standards, improve security, and benefit from native systemd integration without service degradation, the platform requires transitioning to Podman. The transition must ensure 100% functional parity across Traefik routing, Let's Encrypt ACME renewal, DNS resolution, Docker socket integrations (Traefik, AutoKuma, Authentik worker), and CI/CD builders.

### Decision
We adopt a **Rootful System-Level Podman architecture** with the following components:
1. **`podman.socket` Systemd Service**: Emulates the Docker Engine API socket at `/run/podman/podman.sock` and symlinked to `/var/run/docker.sock`.
2. **`podman-docker` CLI Compatibility Layer**: Provides transparent `/usr/bin/docker` execution.
3. **Netavark + Aardvark-DNS**: Powers inter-container DNS name resolution on user-defined bridge networks (`traefik-net`), matching Docker's embedded DNS.
4. **Preserved Host Bind Mounts and Named Volumes**: Retains `/opt/<app>` bind mounts and migrates named volumes to `/var/lib/containers/storage/volumes/`.
5. **CRI Log Scraping**: Configures Promtail with `static_configs` targeting `/var/lib/containers/storage/overlay-containers/*/userdata/ctr.log` to reliably ingest Podman container logs into Loki.

### Consequences
- **Pros**:
  - Direct systemd unit management and daemonless OCI execution.
  - Preserved Compose v2 syntax (`community.docker.docker_compose_v2`) and automated Ansible deployment flows (`./deploy.sh`).
  - Seamless inter-container DNS resolution via Netavark/Aardvark.
  - Transparent support for socket-reliant services (Traefik, AutoKuma, Authentik).
- **Cons**:
  - Requires maintaining the `/var/run/docker.sock` symlink for backwards compatibility with legacy docker-compose tooling.
  - Promtail requires direct filesystem log globbing rather than the standard Moby Docker API discovery plugin due to Podman list inspect differences.

