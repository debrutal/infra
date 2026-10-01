# Testing & Quality Assurance

This chapter describes the 3-tier testing architecture implemented to guarantee code quality, syntax correctness, role idempotence, and system state verification.

## Testing Architecture Overview

```mermaid
flowchart TD
    subgraph Tier1 ["Tier 1: Static Analysis ('Fail Fast')"]
        Y1["yamllint (Formatting & Indentation)"]
        A1["ansible-lint (Best Practices & Deprecations)"]
        S1["ansible-playbook --syntax-check"]
    end

    subgraph Tier2 ["Tier 2: Molecule Integration Lifecycle"]
        M1["dependency"] --> M2["create (Docker instance)"]
        M2 --> M3["prepare (Bootstrap python3)"]
        M3 --> M4["converge (Run site.yml)"]
        M4 --> M5["idempotence (Enforce changed=0)"]
        M5 --> M6["verify (Testinfra assertions)"]
        M6 --> M7["destroy (Teardown container)"]
    end

    subgraph Tier3 ["Tier 3: System Verification (Testinfra)"]
        T1["Package Assertions (git, jq, curl)"]
        T2["Binary Execution (nvim --version)"]
        T3["GPG Key & Repository Verification"]
        T4["Permission Assertions (acme.json -> 0600)"]
        T5["Configuration Content Validation"]
    end

    Tier1 --> Tier2
    M6 --> Tier3
```

## 1. Static Analysis (The "Fail Fast" Layer)
Before executing code, static analysis validates YAML syntax and enforces Ansible best practices:
- **`yamllint`**: Enforces strict YAML rules (`.yamllint`).
- **`ansible-lint`**: Checks playbooks and roles against Ansible community guidelines (`.ansible-lint`).
- **`ansible-playbook --syntax-check`**: Native syntax validation.

### Execution Command:
```bash
yamllint .
ansible-lint
ansible-playbook site.yml --syntax-check
```

## 2. Molecule (Integration Testing Standard)
Molecule automates role testing through an isolated Docker container lifecycle:
1. **Dependency**: Pulls Galaxy requirements (`community.docker`, `ansible.posix`).
2. **Create**: Provisions an `ubuntu:latest` test container (`instance`).
3. **Prepare**: Installs `python3` inside the container.
4. **Converge**: Applies `site.yml` against the container.
5. **Idempotence**: Runs `site.yml` a second time and asserts `changed=0`.
6. **Verify**: Executes Testinfra assertions.
7. **Destroy**: Deletes the temporary container.

### Execution Command:
```bash
export PATH="$PWD/.venv/bin:$PATH"
molecule test
```

## 3. System Verification (Testinfra)
Testinfra (`pytest-testinfra`) verifies actual filesystem and process state inside the container post-deployment (`molecule/default/tests/test_default.py`).

### Verifications Performed:
- **Packages**: `git`, `jq`, `curl`, `ca-certificates` installed.
- **Neovim**: `/usr/local/bin/nvim` executable and version returns `NVIM v...`.
- **Docker**: `/etc/apt/keyrings/docker.asc` exists.
- **Traefik Configs**: `traefik.yml` contains `dnsChallenge` with `cloudflare`; `docker-compose.yml` contains `CF_DNS_API_TOKEN` and domain rules; `dynamic_conf.yml` contains default TLS store for `*.mini.debrutal.dev`.

- **Permissions**: `/opt/traefik/acme/acme.json` permissions are strictly `0600`.

## Unified Test Runner

Run all 3 tiers with a single command:
```bash
./tests/run_tests.sh
```
