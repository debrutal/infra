# Introduction & Architecture Overview

Welcome to the **Minisforum Infra Developer Guide**. This repository contains the automated infrastructure-as-code (IaC) configuration for the target server (`minisforum` at `192.168.1.8`).

## Purpose & Scope

The goal of this project is to provide deterministic, idempotent, and testable provisioning of core server tools and infrastructure services:
- **Base Utilities**: Essential system tooling (`git`, `jq`, `curl`, `wget`, `ca-certificates`).
- **Development Editor**: Modern binary installation of Neovim (`nvim`).
- **Container Runtime**: Docker Engine (`docker-ce`) and Docker Compose (`docker-compose-plugin`).
- **Reverse Proxy & Edge Ingress**: Traefik v3 reverse proxy supporting automatic wildcard TLS certificate issuance via ACME DNS-01 challenges (`*.mini.debrutal.dev`).

## Infrastructure Topology

The diagram below illustrates how external and internal traffic flows through Traefik into containerized services:

```mermaid
flowchart TD
    subgraph Edge ["DNS & ACME"]
        CF["Cloudflare DNS (mini.debrutal.dev)"]
        LE["Let's Encrypt CA"]
    end

    subgraph Host ["Server: minisforum (192.168.1.8)"]
        subgraph Ports ["Host Ports"]
            P80["Port 80 (HTTP)"]
            P443["Port 443 (HTTPS)"]
            P8080["Port 8080 (Dashboard)"]
        end

        subgraph Containers ["Docker Engine"]
            Traefik["Traefik v3 Proxy Container"]
            App1["Container App 1"]
            App2["Container App 2"]
        end

        subgraph Configs ["Volume Mounts"]
            Static["/opt/traefik/traefik.yml"]
            Dynamic["/opt/traefik/dynamic/dynamic_conf.yml"]
            ACME["/opt/traefik/acme/acme.json (0600)"]
        end
    end

    P80 --> Traefik
    P443 --> Traefik
    P8080 --> Traefik
    LE -- "DNS-01 Challenge TXT Check" --> CF
    Traefik -- "ACME DNS Challenge API" --> CF
    Traefik --> Static
    Traefik --> Dynamic
    Traefik --> ACME
    Traefik -- "traefik-net network" --> App1
    Traefik -- "traefik-net network" --> App2
```

## Key Architectural Principles

1. **Idempotence**: Every Ansible role can be executed repeatedly without unnecessary changes or side effects.
2. **Containerized Ingress**: All public/private web applications are routed through Traefik using Docker container labels.
3. **Automated TLS**: Wildcard certificates (`*.mini.debrutal.dev`) are managed automatically via Let's Encrypt DNS-01 challenge solving.
4. **Three-Tier Testing**: Full test coverage across Static Analysis, Molecule Integration lifecycle, and Testinfra System Verification.
