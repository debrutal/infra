# Operations & Deployment Guide

This chapter provides operational procedures for deploying to the target server, monitoring services, and proxying new applications.

## 1. Deploying to Server (`192.168.1.8`)

### Prerequisites
Ensure SSH access to `192.168.1.8`:
```bash
ssh root@192.168.1.8
```

### Configure Credentials
Edit `inventory/group_vars/all.yml` and set your Cloudflare API token:
```yaml
traefik_acme_dns_env:
  CF_DNS_API_TOKEN: "your-actual-cloudflare-api-token"
```

### Run Playbook
```bash
# When connecting as a non-root sudo user (e.g. debrutal):
ansible-playbook site.yml -K

# When connecting directly as root:
ansible-playbook site.yml
```

> **Note**: The `-K` (`--ask-become-pass`) option prompts Ansible to ask for `debrutal`'s `sudo` password at run time.

# Deploy using convenience script (recommended):
./deploy.sh

# Target specific roles via tags:
./deploy.sh -t podman
./deploy.sh -t "traefik,authentik"
./deploy.sh -t all

# Alternatively, invoke ansible-playbook directly:
ansible-playbook site.yml --tags "podman,traefik" -K
```

## 2. Accessing Traefik Dashboard

The Traefik dashboard is exposed on port `8080`:
- **Dashboard URL**: `http://192.168.1.8:8080/dashboard/`
- **Domain URL**: `https://traefik.mini.debrutal.dev`

## 3. Proxying New Container Applications

To route any new container application through Traefik with automatic SSL certificate issuance:

1. Attach the application to the `traefik-net` Docker network.
2. Apply Traefik labels in the application's `docker-compose.yml`.

### Example Application `docker-compose.yml`:

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
      - "traefik.http.routers.whoami.rule=Host(`whoami.mini.debrutal.dev`)"
      - "traefik.http.routers.whoami.entrypoints=websecure"
      - "traefik.http.routers.whoami.tls=true"
      - "traefik.http.routers.whoami.tls.certresolver=letsencrypt"
      - "traefik.http.services.whoami.loadbalancer.server.port=80"

networks:
  traefik-net:
    external: true
```

## 4. Viewing & Streaming Container Logs

Use `./show_container_logs.sh` (or `./scripts/show_container_logs.sh`) to inspect or follow logs across all Podman / Docker containers:

- **View latest logs**: `./show_container_logs.sh`
- **Follow logs in real-time**: `./show_container_logs.sh -f`
- **Include stopped containers**: `./show_container_logs.sh -a -n 100`
- **Filter by service name**: `./show_container_logs.sh -g traefik -f`

Or query Podman directly on the server:
```bash
podman ps
podman logs -f <container_name>
systemctl status podman.socket
```

