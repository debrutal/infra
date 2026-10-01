# Traefik & ACME DNS-01 Setup

This chapter explains how Traefik is configured to route ACME DNS-01 challenges for wildcard domain certificates (`*.mini.debrutal.dev`).

## Why DNS-01 Challenge for Wildcards?

Under the ACME specification (RFC 8555 / Let's Encrypt), **HTTP-01 challenges cannot issue wildcard domain certificates** (`*.domain.com`). To obtain a single certificate that covers both `mini.debrutal.dev` and all subdomains (`*.mini.debrutal.dev`), Traefik must prove domain control using the **DNS-01 challenge**.

## Architecture & Data Flow

```mermaid
sequenceDiagram
    autonumber
    participant Traefik as Traefik v3 (192.168.1.8)
    participant LE as Let's Encrypt ACME Server
    participant CF as Cloudflare DNS API
    participant DNS as Public DNS Resolvers (1.1.1.1)

    Traefik->>LE: Request wildcard cert for mini.debrutal.dev & *.mini.debrutal.dev
    LE-->>Traefik: Provide DNS-01 challenge token for _acme-challenge.mini.debrutal.dev
    Traefik->>CF: Create TXT record _acme-challenge.mini.debrutal.dev via API (CF_DNS_API_TOKEN)
    CF-->>Traefik: Record created successfully
    Traefik->>DNS: Poll recursive resolvers (1.1.1.1:53) to verify TXT record propagation
    DNS-->>Traefik: Propagation confirmed
    Traefik->>LE: Notify Let's Encrypt challenge is ready for validation
    LE->>CF: Query DNS TXT record _acme-challenge.mini.debrutal.dev
    CF-->>LE: TXT record token matches
    LE-->>Traefik: Issue X.509 Wildcard Certificate
    Traefik->>Traefik: Save certificate to /opt/traefik/acme/acme.json (0600)
    Traefik->>CF: Clean up temporary TXT record
```

## Traefik Static Configuration (`traefik.yml.j2`)

```yaml
entryPoints:
  web:
    address: ":80"
    http:
      aliasHeadersStrategy: "delete"
      encodedCharacters:
        allowEncodedSlash: false
        # ...
  websecure:
    address: ":443"
    http:
      aliasHeadersStrategy: "delete"
      encodedCharacters:
        allowEncodedSlash: false
        # ...

certificatesResolvers:
  letsencrypt:
    acme:
      email: "{{ traefik_acme_email }}"
      storage: "/etc/traefik/acme/acme.json"
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
          - "1.0.0.1:53"
```

## Container Environment & Compose (`docker-compose.yml.j2`)

```yaml
services:
  traefik:
    image: traefik:v3.7.13
    container_name: traefik
    restart: always
    environment:
      - "CF_DNS_API_TOKEN=your-cloudflare-api-token-here"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - /opt/traefik/dynamic:/etc/traefik/dynamic:ro
      - /opt/traefik/acme/acme.json:/etc/traefik/acme/acme.json
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik_api.rule=Host(`traefik.local`) || Host(`traefik.mini.debrutal.dev`) || Host(`dashboard.mini.debrutal.dev`)"
      - "traefik.http.routers.traefik_api.service=api@internal"
      - "traefik.http.routers.traefik_api.entrypoints=websecure"
      - "traefik.http.routers.traefik_api.tls=true"
      - "traefik.http.routers.traefik_api.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik_api.tls.domains[0].main=mini.debrutal.dev"
      - "traefik.http.routers.traefik_api.tls.domains[0].sans=*.mini.debrutal.dev"
```

## Dynamic TLS Store (`dynamic_conf.yml.j2`)

```yaml
tls:
  stores:
    default:
      defaultGeneratedCert:
        resolver: letsencrypt
        domain:
          main: "mini.debrutal.dev"
          sans:
            - "*.mini.debrutal.dev"
```

This configuration ensures that any proxied HTTP router under `*.mini.debrutal.dev` automatically receives valid Let's Encrypt TLS certificates generated via DNS challenge!
