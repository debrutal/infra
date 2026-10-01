# Codebase Structure & Inventory

This chapter details the layout of the repository, Ansible inventory structure, and configuration variable inheritance.

## Directory Layout

```
infra/
├── ansible.cfg                 # Global Ansible settings & callbacks
├── site.yml                    # Main playbook orchestration
├── requirements.yml            # Ansible Galaxy collection dependencies
├── inventory/
│   ├── hosts.ini               # Target server definition (minisforum @ 192.168.1.8)
│   └── group_vars/
│       └── all.yml             # Global variables (ports, paths, ACME settings)
├── roles/                      # Ansible roles
│   ├── common/                 # Packages & base setup
│   ├── neovim/                 # Neovim binary release installation
│   ├── docker/                 # Official Docker Engine & APT repos
│   └── traefik/                # Traefik proxy, dynamic config & ACME
├── tests/                      # Custom Python integration test suite
│   ├── test_deployment.py      # Container integration test runner
│   └── run_tests.sh            # Unified test execution wrapper
├── molecule/                   # Molecule testing framework
│   └── default/
│       ├── molecule.yml        # Molecule scenario configuration
│       ├── prepare.yml         # Container bootstrap playbook
│       ├── converge.yml        # Playbook execution runner
│       └── tests/
│           └── test_default.py # Testinfra verification assertions
└── docs_book/                  # mdbook Developer Guide source
    ├── book.toml               # mdbook configuration
    └── src/                    # Book chapters (Markdown)
```

## Inventory & Host Variables

### Target Host Definition (`inventory/hosts.ini`)
```ini
[servers]
minisforum ansible_host=192.168.1.8

[servers:vars]
ansible_user=root
```

### Global Variables (`inventory/group_vars/all.yml`)
```yaml
# Common configuration
common_packages:
  - git
  - jq
  - curl
  - wget
  - ca-certificates
  - gnupg
  - lsb-release
  - tar
  - unzip

# Neovim configuration
neovim_version: "latest"
neovim_install_dir: "/opt/nvim"
neovim_bin_symlink: "/usr/local/bin/nvim"

# Docker configuration
docker_users:
  - "{{ ansible_user }}"

# Traefik configuration
traefik_dir: "/opt/traefik"
traefik_network_name: "traefik-net"
traefik_http_port: 80
traefik_https_port: 443
traefik_dashboard_port: 8080
traefik_enable_dashboard: true
traefik_dashboard_insecure: true
traefik_log_level: "INFO"

# ACME & Domain settings
traefik_acme_email: "admin@debrutal.dev"
traefik_acme_enabled: true
traefik_acme_domain_main: "mini.debrutal.dev"
traefik_acme_domain_sans:
  - "*.mini.debrutal.dev"

traefik_acme_challenge_type: "dns"
traefik_acme_dns_provider: "cloudflare"
traefik_acme_dns_resolvers:
  - "1.1.1.1:53"
  - "1.0.0.1:53"
traefik_acme_dns_env:
  CF_DNS_API_TOKEN: "your-cloudflare-api-token-here"
```
