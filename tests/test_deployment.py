#!/usr/bin/env python3
"""
Integration test suite for Ansible infrastructure deployment on a local Docker container.
Ensures deployment works end-to-end on an isolated container without touching the remote server.
"""

import os
import subprocess
import unittest

CONTAINER_NAME = "infra-test-container"
# Check if pre-built molecule image is available for instant setup
res_img = subprocess.run(["docker", "image", "inspect", "molecule_local/ubuntu:latest"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
IMAGE_NAME = "molecule_local/ubuntu:latest" if res_img.returncode == 0 else "ubuntu:latest"

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTORY_FILE = os.path.join(WORKSPACE_DIR, "tests", "inventory.ini")

class TestContainerDeployment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Spin up a fresh test container and prepare Python environment for Ansible."""
        print(f"\n[+] Cleaning up any pre-existing container named {CONTAINER_NAME}...")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"[+] Spawning local test container ({CONTAINER_NAME} using {IMAGE_NAME})...")
        cmd_run = [
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
            IMAGE_NAME,
            "sleep", "600"
        ]
        res = subprocess.run(cmd_run, capture_output=True, text=True)
        assert res.returncode == 0, f"Failed to start docker container: {res.stderr}"

        # If using standard base image without python3 pre-installed
        if IMAGE_NAME == "ubuntu:latest":
            print("[+] Installing python3 in test container for Ansible compatibility...")
            cmd_prep = [
                "docker", "exec", CONTAINER_NAME,
                "sh", "-c", "apt-get update && apt-get install -y python3 python3-apt ca-certificates"
            ]
            res_prep = subprocess.run(cmd_prep, capture_output=True, text=True)
            assert res_prep.returncode == 0, f"Failed to prepare container environment: {res_prep.stderr}"

        # Write temporary test inventory
        os.makedirs(os.path.dirname(INVENTORY_FILE), exist_ok=True)
        with open(INVENTORY_FILE, "w") as f:
            f.write("[servers]\n")
            f.write(f"{CONTAINER_NAME} ansible_connection=docker ansible_user=root\n")

        print("[+] Running Ansible playbook against test container...")
        cmd_ansible = [
            "ansible-playbook", "site.yml",
            "-i", INVENTORY_FILE
        ]
        res_ansible = subprocess.run(cmd_ansible, cwd=WORKSPACE_DIR, capture_output=True, text=True)
        print("Ansible Playbook Output:\n", res_ansible.stdout)
        if res_ansible.returncode != 0:
            print("Ansible Playbook Error:\n", res_ansible.stderr)
        assert res_ansible.returncode == 0, f"Ansible playbook execution failed with return code {res_ansible.returncode}"

    @classmethod
    def tearDownClass(cls):
        """Remove test container after tests complete."""
        print(f"\n[+] Tearing down test container {CONTAINER_NAME}...")
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(INVENTORY_FILE):
            os.remove(INVENTORY_FILE)

    def test_01_common_packages_installed(self):
        """Verify git, jq, curl, and ripgrep are installed."""
        for pkg_cmd in ["git --version", "jq --version", "curl --version", "rg --version"]:
            res = subprocess.run(["docker", "exec", CONTAINER_NAME, "sh", "-c", pkg_cmd], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Command {pkg_cmd} failed: {res.stderr}")

    def test_02_neovim_installation(self):
        """Verify Neovim binary is installed and executable via symlink."""
        res = subprocess.run(["docker", "exec", CONTAINER_NAME, "nvim", "--version"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Neovim execution failed: {res.stderr}")
        self.assertIn("NVIM", res.stdout)

    def test_03_docker_packages_installed(self):
        """Verify Docker packages & keyrings directory were installed."""
        res = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-f", "/etc/apt/keyrings/docker.asc"], capture_output=True)
        self.assertEqual(res.returncode, 0, "Docker GPG key file /etc/apt/keyrings/docker.asc missing")

    def test_03b_docker_group_user(self):
        """Verify docker group exists."""
        res = subprocess.run(["docker", "exec", CONTAINER_NAME, "getent", "group", "docker"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, "Docker group does not exist")

    def test_04_traefik_directories_and_acme(self):
        """Verify Traefik directories and acme.json permissions (0600)."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/traefik/dynamic"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/traefik/dynamic directory missing")

        res_acme = subprocess.run(["docker", "exec", CONTAINER_NAME, "stat", "-c", "%a", "/opt/traefik/acme/acme.json"], capture_output=True, text=True)
        self.assertEqual(res_acme.returncode, 0, "/opt/traefik/acme/acme.json file missing")
        self.assertEqual(res_acme.stdout.strip(), "600", f"acme.json permissions expected 600, got {res_acme.stdout.strip()}")

    def test_05_traefik_static_config(self):
        """Verify traefik.yml static configuration contains DNS challenge settings."""
        res = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/traefik/traefik.yml"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, "Failed to read /opt/traefik/traefik.yml")
        content = res.stdout
        self.assertIn("dnsChallenge:", content)
        self.assertIn("provider: cloudflare", content)
        self.assertIn("admin@debrutal.dev", content)
        self.assertIn("staging.kita-kit.de", content)
        self.assertIn("*.staging.kita-kit.de", content)

    def test_06_traefik_docker_compose_config(self):
        """Verify docker-compose.yml contains environment vars and domain router rules."""
        res = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/traefik/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, "Failed to read /opt/traefik/docker-compose.yml")
        content = res.stdout
        self.assertIn("CF_DNS_API_TOKEN=", content)
        self.assertIn("mini.debrutal.dev", content)
        self.assertIn("*.mini.debrutal.dev", content)
        self.assertIn("staging.kita-kit.de", content)
        self.assertIn("*.staging.kita-kit.de", content)
        self.assertIn("host.docker.internal:host-gateway", content)

    def test_07_traefik_dynamic_config(self):
        """Verify dynamic_conf.yml contains TLS default generated cert for *.mini.debrutal.dev."""
        res = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/traefik/dynamic/dynamic_conf.yml"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, "Failed to read /opt/traefik/dynamic/dynamic_conf.yml")
        content = res.stdout
        self.assertIn("defaultGeneratedCert:", content)
        self.assertIn("main: \"mini.debrutal.dev\"", content)
        self.assertIn("*.mini.debrutal.dev", content)


    def test_09_gitea_installation(self):
        """Verify Gitea containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/gitea"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/gitea directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/gitea/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/gitea/docker-compose.yml missing")
        self.assertIn("traefik.enable=true", res_compose.stdout)
        self.assertIn("gitea.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("gitea/gitea", res_compose.stdout)
        self.assertIn("GITEA__actions__ENABLED=true", res_compose.stdout)
        self.assertIn("2222:22", res_compose.stdout)

        # Verify runner services and directories
        runner_count = int(os.environ.get("GITEA_RUNNER_COUNT", "4"))
        for i in range(1, runner_count + 1):
            self.assertIn(f"gitea-runner-{i}:", res_compose.stdout)
            self.assertIn(f"gitea-runner-dind-{i}:", res_compose.stdout)
            res_rdir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", f"/opt/gitea/runner-{i}-data"], capture_output=True)
            self.assertEqual(res_rdir.returncode, 0, f"/opt/gitea/runner-{i}-data directory missing")
            res_dinddir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", f"/opt/gitea/runner-{i}-dind-data"], capture_output=True)
            self.assertEqual(res_dinddir.returncode, 0, f"/opt/gitea/runner-{i}-dind-data directory missing")
        self.assertIn("gitea/act_runner", res_compose.stdout)
        self.assertIn("dind-rootless", res_compose.stdout)
        self.assertIn("DOCKER_HOST=tcp://gitea-runner-dind-", res_compose.stdout)

        # Verify gitea-mcp service
        self.assertIn("gitea-mcp:", res_compose.stdout)
        self.assertIn("docker.gitea.com/gitea-mcp-server", res_compose.stdout)
        self.assertIn("gitea-mcp.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("MCP_MODE=http", res_compose.stdout)
        self.assertIn("GITEA_HOST=http://gitea:3000", res_compose.stdout)


    def test_10_homepage_installation(self):
        """Verify Homepage containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/homepage"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/homepage directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/homepage/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/homepage/docker-compose.yml missing")
        self.assertIn("traefik.enable=true", res_compose.stdout)
        self.assertIn("dash.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("dashboard.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("HOMEPAGE_ALLOWED_HOSTS", res_compose.stdout)

    def test_11_lago_installation(self):
        """Verify Lago containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/lago"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/lago directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/lago/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/lago/docker-compose.yml missing")
        self.assertIn("API_URL:", res_compose.stdout)
        self.assertIn("LAGO_DOMAIN:", res_compose.stdout)

    def test_13_lgtm_installation(self):
        """Verify LGTM containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/lgtm"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/lgtm directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/lgtm/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/lgtm/docker-compose.yml missing")
        self.assertIn("traefik.enable=true", res_compose.stdout)
        self.assertIn("grafana.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("grafana/loki", res_compose.stdout)
        self.assertIn("prom/prometheus", res_compose.stdout)
        self.assertIn("grafana/tempo", res_compose.stdout)
        self.assertIn("GF_AUTH_GENERIC_OAUTH_ENABLED:", res_compose.stdout)
        self.assertIn("GF_AUTH_GENERIC_OAUTH_CLIENT_ID:", res_compose.stdout)

    def test_14_bookorbit_installation(self):
        """Verify BookOrbit containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/bookorbit"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/bookorbit directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/bookorbit/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/bookorbit/docker-compose.yml missing")
        self.assertIn("traefik.enable=true", res_compose.stdout)
        self.assertIn("bookorbit.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("ghcr.io/bookorbit/bookorbit", res_compose.stdout)
        self.assertIn("pgvector/pgvector", res_compose.stdout)
        self.assertIn("POSTGRES_USER", res_compose.stdout)
        self.assertIn("JWT_SECRET", res_compose.stdout)
        self.assertIn("OIDC_ALLOW_LOCAL_ISSUERS", res_compose.stdout)

        # Verify data directories
        for subdir in ["data/app", "data/postgres", "books"]:
            res_subdir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", f"/opt/bookorbit/{subdir}"], capture_output=True)
            self.assertEqual(res_subdir.returncode, 0, f"/opt/bookorbit/{subdir} directory missing")

        # Verify app-writable volumes are owned by the PUID/PGID the container drops to
        for subdir in ["data/app", "books"]:
            res_owner = subprocess.run(
                ["docker", "exec", CONTAINER_NAME, "stat", "-c", "%u:%g", f"/opt/bookorbit/{subdir}"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_owner.stdout.strip(), "1000:1000", f"/opt/bookorbit/{subdir} must be owned by 1000:1000")

        # Verify the app process can actually write to its library volume
        res_write = subprocess.run(
            ["docker", "exec", "bookorbit-app", "sh", "-c", "su -s /bin/sh node -c 'mkdir /books/.perm_test && rmdir /books/.perm_test'"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_write.returncode, 0, f"app user cannot write to /books: {res_write.stderr}")

    def test_15_sentry_installation(self):
        """Verify Sentry (GlitchTip) containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/sentry"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/sentry directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/sentry/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/sentry/docker-compose.yml missing")
        self.assertIn("traefik.enable=true", res_compose.stdout)
        self.assertIn("sentry.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("glitchtip/glitchtip", res_compose.stdout)
        self.assertIn("ENABLE_USER_REGISTRATION:", res_compose.stdout)
        self.assertIn("ENABLE_SOCIAL_APPS_USER_REGISTRATION:", res_compose.stdout)

    def test_16_agentzero_installation(self):
        """Verify Agent Zero containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/agentzero"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/agentzero directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/agentzero/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/agentzero/docker-compose.yml missing")
        self.assertIn("traefik.enable=true", res_compose.stdout)
        self.assertIn("agentzero.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("agent0ai/agent-zero", res_compose.stdout)

        # Verify data directory
        res_usr = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/agentzero/usr"], capture_output=True)
        self.assertEqual(res_usr.returncode, 0, "/opt/agentzero/usr directory missing")

    def test_17_pinchflat_installation(self):
        """Verify Pinchflat containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/pinchflat"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/pinchflat directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/pinchflat/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/pinchflat/docker-compose.yml missing")
        self.assertIn("traefik.enable=true", res_compose.stdout)
        self.assertIn("pinchflat.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("ghcr.io/kieraneglin/pinchflat", res_compose.stdout)
        self.assertIn("traefik.http.routers.pinchflat.middlewares=authentik@file", res_compose.stdout)

        for subdir in ["config", "downloads"]:
            res_sub = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", f"/opt/pinchflat/{subdir}"], capture_output=True)
            self.assertEqual(res_sub.returncode, 0, f"/opt/pinchflat/{subdir} directory missing")

    def test_18_ebook2audiobook_installation(self):
        """Verify eBook2Audiobook containerized directory and docker-compose.yml configuration."""
        res_dir = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", "/opt/ebook2audiobook"], capture_output=True)
        self.assertEqual(res_dir.returncode, 0, "/opt/ebook2audiobook directory missing")

        res_compose = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/opt/ebook2audiobook/docker-compose.yml"], capture_output=True, text=True)
        self.assertEqual(res_compose.returncode, 0, "/opt/ebook2audiobook/docker-compose.yml missing")
        self.assertIn("traefik.enable=true", res_compose.stdout)
        self.assertIn("ebook2audiobook.mini.debrutal.dev", res_compose.stdout)
        self.assertIn("athomasson2/ebook2audiobook", res_compose.stdout)
        self.assertIn("traefik.http.routers.ebook2audiobook.middlewares=authentik@file", res_compose.stdout)

        for subdir in ["ebooks", "audiobooks", "models", "voices", "tmp"]:
            res_sub = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", f"/opt/ebook2audiobook/{subdir}"], capture_output=True)
            self.assertEqual(res_sub.returncode, 0, f"/opt/ebook2audiobook/{subdir} directory missing")

    def test_19_restic_backup_installation(self):
        """Verify Restic backup directories, configuration, scripts, and systemd units."""
        for path in ["/backup", "/backup/dumps", "/etc/restic"]:
            res = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-d", path], capture_output=True)
            self.assertEqual(res.returncode, 0, f"{path} directory missing")

        res_pwd = subprocess.run(["docker", "exec", CONTAINER_NAME, "stat", "-c", "%a", "/etc/restic/password"], capture_output=True, text=True)
        self.assertEqual(res_pwd.returncode, 0, "/etc/restic/password missing")
        self.assertEqual(res_pwd.stdout.strip(), "600")

        res_env = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/etc/restic/env.sh"], capture_output=True, text=True)
        self.assertEqual(res_env.returncode, 0, "/etc/restic/env.sh missing")
        self.assertIn("RESTIC_REPOSITORY", res_env.stdout)

        res_script = subprocess.run(["docker", "exec", CONTAINER_NAME, "cat", "/usr/local/bin/restic-backup.sh"], capture_output=True, text=True)
        self.assertEqual(res_script.returncode, 0, "/usr/local/bin/restic-backup.sh missing")
        self.assertIn("authentik-db", res_script.stdout)
        self.assertIn("bookorbit-db", res_script.stdout)
        self.assertIn("gitea.db", res_script.stdout)
        self.assertIn("restic backup", res_script.stdout)

        res_infra = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-x", "/usr/local/bin/restic-infra"], capture_output=True)
        self.assertEqual(res_infra.returncode, 0, "/usr/local/bin/restic-infra not executable")

        res_svc = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-f", "/etc/systemd/system/restic-backup.service"], capture_output=True)
        self.assertEqual(res_svc.returncode, 0, "/etc/systemd/system/restic-backup.service missing")

        res_timer = subprocess.run(["docker", "exec", CONTAINER_NAME, "test", "-f", "/etc/systemd/system/restic-backup.timer"], capture_output=True)
        self.assertEqual(res_timer.returncode, 0, "/etc/systemd/system/restic-backup.timer missing")


if __name__ == "__main__":
    unittest.main(verbosity=2)




