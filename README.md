# Infrastructure Provisioning for Server `192.168.1.8`

This Ansible project sets up and configures the target server (`192.168.1.8`) with all requested base software and container infrastructure.

## Software & Components Included

1. **`git`**: Installed via distribution package manager.
2. **`jq`**: Installed via distribution package manager.
3. **`neovim` (latest version)**: Downloaded and installed directly from official Neovim GitHub releases (`nvim-linux-x86_64.tar.gz`) to `/opt/nvim` and symlinked to `/usr/local/bin/nvim`.
4. **`docker`**: Installed via Docker's official APT repository (`docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin`).
5. **`traefik`**: Deployed as a Docker container via Docker Compose on a dedicated Docker network (`traefik-net`) to serve as a reverse proxy for containerized applications.



---

## Directory Structure

```
infra/
├── ansible.cfg                 # Global Ansible configuration
├── site.yml                    # Main playbook
├── inventory/
│   ├── hosts.ini               # Host definitions (192.168.1.8)
│   └── group_vars/
│       └── all.yml             # Global variables (ports, directories, versions)
└── roles/
    ├── common/                 # Installs git, jq, curl, tar, etc.
    ├── neovim/                 # Installs latest Neovim binary release
    ├── docker/                 # Configures official Docker repository & engine
    └── traefik/                # Configures Traefik reverse proxy & network
        ├── defaults/
        ├── handlers/
        ├── tasks/
        └── templates/
            ├── docker-compose.yml.j2
            ├── dynamic_conf.yml.j2
            └── traefik.yml.j2
```

---

## Quick Start

### 1. Prerequisites
Ensure you have SSH access to `192.168.1.8`:
```bash
ssh root@192.168.1.8
# or with sudo user:
# ssh user@192.168.1.8
```

ssh config:

```
Host mini
    Hostname 192.168.1.8
    User debrutal
```

Adjust `inventory/hosts.ini` if using a non-root user (uncomment `ansible_user` and `ansible_become`).

### 2. Run the Playbook
To provision the full stack on `192.168.1.8`:

```bash
# When connecting with a sudo user (e.g. debrutal):
ansible-playbook site.yml -K

# When connecting as root:
ansible-playbook site.yml
```

> **Note**: The `-K` (`--ask-become-pass`) flag prompts for your SSH user's `sudo` password on the target server.

To run a specific role, use tags:
```bash
# Run only Neovim installation
ansible-playbook site.yml --tags neovim -K

# Run only Docker & Traefik configuration
ansible-playbook site.yml --tags "docker,traefik" -K
```

---

## Accessing Traefik Dashboard

By default, the Traefik dashboard is accessible on port `8080`:
- **URL:** `http://192.168.1.8:8080/dashboard/`

---

## Proxying New Container Applications with Traefik

Traefik listens on the `traefik-net` Docker network. To proxy any container app through Traefik, add it to the `traefik-net` network and apply Traefik labels in your `docker-compose.yml`.

### Example `docker-compose.yml` for a container app (e.g., Whoami):

```yaml
services:
  whoami:
    image: traefik/whoami
    container_name: whoami
    restart: unless-stopped
    networks:
      - traefik-net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.whoami.rule=Host(`whoami.192.168.1.8.nip.io`)"
      - "traefik.http.routers.whoami.entrypoints=web"
      - "traefik.http.services.whoami.loadbalancer.server.port=80"

networks:
  traefik-net:
    external: true
```

---

## Viewing Container Logs

A script is provided to display or stream logs from all running or stopped Docker containers on the system:

```bash
# View last 50 lines of logs for all running containers
./show_container_logs.sh

# Stream logs continuously in real-time with color-coded container tags
./show_container_logs.sh -f

# Include stopped containers and show last 100 lines
./show_container_logs.sh -a -n 100

# Filter logs for a specific service or container name (e.g. traefik)
./show_container_logs.sh -g traefik -f
```

---

## Gitea Runners (rootless Docker-in-Docker)

The Gitea runners talk to a per-runner `docker:dind-rootless` daemon over TCP (`DOCKER_TLS_CERTDIR=`).

Ubuntu >= 24.10 ships `kernel.apparmor_restrict_unprivileged_userns=1`, which blocks unprivileged user namespaces created together with other namespace flags. The DinD daemon runs `rootlesskit` as uid 1000 without capabilities, so it aborts on startup with:

```
[rootlesskit:parent] error: failed to start the child: fork/exec /proc/self/exe: operation not permitted
```

The `gitea` role therefore installs `/etc/apparmor.d/usr.local.bin.rootlesskit`, which grants `userns` to that binary only, and reloads AppArmor. This keeps the host-wide hardening intact (unlike setting `kernel.apparmor_restrict_unprivileged_userns=0`).

The `modprobe: can't change directory to '/lib/modules'` and `Device "ip_tables" does not exist` messages in the DinD logs are harmless: no kernel modules are mounted into the container, so `iptables` falls back to the `nf_tables` backend, which is what the daemon uses.

Disable the profile handling with `gitea_dind_apparmor_profile_enabled: false` (e.g. on hosts without AppArmor).

---

## Running Container Integration Tests

An automated container integration test suite is provided in `tests/` to test the full Ansible deployment inside an isolated local Docker container without modifying the remote server.

### Execute the Test Suite:
```bash
./tests/run_tests.sh
# or directly via Python:
python3 tests/test_deployment.py
```

### What the Test Suite Validates:
1. Spawns an isolated `ubuntu:latest` container (`infra-test-container`).
2. Runs `ansible-playbook site.yml` against the container using `ansible_connection=docker`.
3. Verifies common package installations (`git`, `jq`, `curl`).
4. Verifies Neovim installation and execution (`nvim --version`).
5. Verifies Docker APT repository setup and GPG key keyring.
6. Verifies Traefik static configuration (`traefik.yml`) containing ACME `dnsChallenge` for Cloudflare.
7. Verifies Traefik Docker Compose file (`docker-compose.yml`) containing `CF_DNS_API_TOKEN` and domain routing rules.
8. Verifies Traefik dynamic configuration (`dynamic_conf.yml`) containing default generated TLS certificate store for `*.mini.debrutal.dev`.

9. Verifies `/opt/traefik/acme/acme.json` permissions (`0600`).
10. Automatically tears down and cleans up the test container upon completion.
