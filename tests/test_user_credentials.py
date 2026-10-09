#!/usr/bin/env python3
"""
Unit tests to verify user credentials configuration across all application roles and group variables.
"""

import os
import unittest
import yaml
import subprocess

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestUserCredentialsConfiguration(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(WORKSPACE_DIR, ".vault_pass"), "r") as f:
            self.vault_password = f.read().strip()

        with open(os.path.join(WORKSPACE_DIR, "inventory", "group_vars", "all", "all.yml"), "r") as f:
            self.all_vars = yaml.safe_load(f)

    def test_vault_password_content(self):
        """Verify .vault_pass contains non-empty content when present."""
        if os.path.exists(os.path.join(WORKSPACE_DIR, ".vault_pass")):
            self.assertTrue(len(self.vault_password) > 0)

    def test_group_vars_default_credentials(self):
        """Verify default_admin_username, email, and password in group_vars/all/all.yml."""
        self.assertEqual(self.all_vars.get("default_admin_username"), "debrutal")
        self.assertEqual(self.all_vars.get("default_admin_email"), "duennes@gmail.com")
        self.assertIn("vault_default_admin_password", str(self.all_vars.get("default_admin_password", "")))

    def test_gitea_defaults(self):
        """Verify Gitea default admin configuration."""
        gitea_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "gitea", "defaults", "main.yml")
        with open(gitea_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_gitea_admin_user | default(default_admin_username", content)
        self.assertIn("vault_gitea_admin_email | default(default_admin_email", content)
        self.assertIn('gitea_version: "28"', content)
        self.assertEqual(str(self.all_vars.get("gitea_version")), "28")
        self.assertIn('gitea_security_egress_mode: "lax"', content)
        self.assertIn("gitea_security_allowed_host_list:", content)
        self.assertNotIn("gitea_webhook_allowed_host_list:", content)

    def test_gitea_mcp_credentials(self):
        """Verify Gitea MCP server token and configuration."""
        gitea_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "gitea", "defaults", "main.yml")
        with open(gitea_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("gitea_mcp_enabled: true", content)
        self.assertIn("vault_gitea_mcp_access_token", content)
        self.assertEqual(self.all_vars.get("gitea_mcp_enabled"), True)
        self.assertIn("vault_gitea_mcp_access_token", str(self.all_vars.get("gitea_mcp_access_token", "")))
        with open(os.path.join(WORKSPACE_DIR, "inventory", "group_vars", "all", "vault.yml"), "r") as f:
            vault_content = f.read()
        self.assertIn("vault_gitea_mcp_access_token:", vault_content)


    def test_espocrm_defaults(self):
        """Verify EspoCRM default admin configuration."""
        espocrm_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "espocrm", "defaults", "main.yml")
        with open(espocrm_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_espocrm_admin_username | default(default_admin_username", content)

    def test_sentry_defaults(self):
        """Verify Sentry default admin configuration."""
        sentry_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "sentry", "defaults", "main.yml")
        with open(sentry_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_sentry_admin_user | default(default_admin_username", content)
        self.assertIn("sentry_authentik_enabled: true", content)
        self.assertIn("sentry_authentik_client_id", content)

    def test_invoiceninja_defaults(self):
        """Verify Invoice Ninja default admin configuration."""
        invoiceninja_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "invoiceninja", "defaults", "main.yml")
        with open(invoiceninja_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_invoiceninja_admin_user | default(default_admin_username", content)

    def test_lago_defaults(self):
        """Verify Lago default admin configuration."""
        lago_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "lago", "defaults", "main.yml")
        with open(lago_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_lago_admin_user | default(default_admin_username", content)

    def test_uptime_kuma_defaults(self):
        """Verify Uptime Kuma default admin configuration."""
        uptime_kuma_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "uptime_kuma", "defaults", "main.yml")
        with open(uptime_kuma_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_uptime_kuma_username | default(default_admin_username", content)

    def test_authentik_defaults(self):
        """Verify Authentik default admin configuration."""
        authentik_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "authentik", "defaults", "main.yml")
        with open(authentik_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_authentik_admin_username | default(default_admin_username", content)
        self.assertIn("vault_authentik_admin_email | default(default_admin_email", content)
        self.assertIn("authentik_grafana_client_id", content)
        self.assertIn("authentik_glitchtip_client_id", content)

    def test_lgtm_defaults(self):
        """Verify LGTM default admin configuration."""
        lgtm_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "lgtm", "defaults", "main.yml")
        with open(lgtm_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_lgtm_admin_username | default(default_admin_username", content)
        self.assertIn("vault_lgtm_admin_password | default(default_admin_password", content)
        self.assertIn("lgtm_authentik_enabled:", content)

    def test_agentzero_defaults(self):
        """Verify Agent Zero default configuration."""
        az_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "agentzero", "defaults", "main.yml")
        with open(az_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_agentzero_auth_login | default(default_admin_username", content)
        self.assertIn("vault_agentzero_auth_password | default(default_admin_password", content)
        self.assertEqual(self.all_vars.get("agentzero_domain"), "agentzero.mini.debrutal.dev")
        self.assertEqual(self.all_vars.get("agentzero_dir"), "/opt/agentzero")

    def test_pinchflat_defaults(self):
        """Verify Pinchflat default configuration."""
        pf_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "pinchflat", "defaults", "main.yml")
        with open(pf_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("vault_pinchflat_auth_username | default(default_admin_username", content)
        self.assertIn("vault_pinchflat_auth_password | default(default_admin_password", content)
        self.assertIn("pinchflat_authentik_enabled: true", content)
        self.assertEqual(self.all_vars.get("pinchflat_domain"), "pinchflat.mini.debrutal.dev")
        self.assertEqual(self.all_vars.get("pinchflat_dir"), "/opt/pinchflat")
        self.assertEqual(self.all_vars.get("pinchflat_authentik_enabled"), True)

        authentik_tasks_path = os.path.join(WORKSPACE_DIR, "roles", "authentik", "tasks", "main.yml")
        with open(authentik_tasks_path, "r") as f:
            ak_tasks = f.read()
        self.assertIn("Pinchflat ForwardAuth", ak_tasks)
        self.assertIn("slug='pinchflat'", ak_tasks)

    def test_ebook2audiobook_defaults(self):
        """Verify eBook2Audiobook default configuration."""
        eb_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "ebook2audiobook", "defaults", "main.yml")
        with open(eb_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("ebook2audiobook_image: \"athomasson2/ebook2audiobook\"", content)
        self.assertIn("ebook2audiobook_authentik_enabled: true", content)
        self.assertEqual(self.all_vars.get("ebook2audiobook_domain"), "ebook2audiobook.mini.debrutal.dev")
        self.assertEqual(self.all_vars.get("ebook2audiobook_dir"), "/opt/ebook2audiobook")
        self.assertEqual(self.all_vars.get("ebook2audiobook_port"), 7860)

        authentik_tasks_path = os.path.join(WORKSPACE_DIR, "roles", "authentik", "tasks", "main.yml")
        with open(authentik_tasks_path, "r") as f:
            ak_tasks = f.read()
        self.assertIn("eBook2Audiobook ForwardAuth", ak_tasks)
        self.assertIn("slug='ebook2audiobook'", ak_tasks)

        compose_path = os.path.join(WORKSPACE_DIR, "roles", "ebook2audiobook", "templates", "docker-compose.yml.j2")
        with open(compose_path, "r") as f:
            compose_content = f.read()
        self.assertIn("image: {{ ebook2audiobook_image }}:{{ ebook2audiobook_version }}", compose_content)
        self.assertIn("/app/ebooks", compose_content)
        self.assertIn("/app/audiobooks", compose_content)

    def test_restic_backup_defaults(self):
        """Verify Restic backup role default configuration and templates."""
        restic_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "restic", "defaults", "main.yml")
        with open(restic_defaults_path, "r") as f:
            content = f.read()
        self.assertIn("restic_backup_root: \"/backup\"", content)
        self.assertIn("restic_repo_dir: \"{{ restic_backup_root }}/restic\"", content)
        self.assertIn("restic_dumps_dir: \"{{ restic_backup_root }}/dumps\"", content)
        self.assertEqual(self.all_vars.get("restic_backup_root"), "/backup")
        self.assertEqual(self.all_vars.get("restic_keep_daily"), 7)

        # Verify orchestration script template
        backup_sh_path = os.path.join(WORKSPACE_DIR, "roles", "restic", "templates", "restic-backup.sh.j2")
        with open(backup_sh_path, "r") as f:
            sh_content = f.read()
        self.assertIn("authentik-db", sh_content)
        self.assertIn("bookorbit-db", sh_content)
        self.assertIn("espocrm-db", sh_content)
        self.assertIn("invoiceninja-db", sh_content)
        self.assertIn("sentry-postgres", sh_content)
        self.assertIn("lago-db", sh_content)
        self.assertIn("gitea.db", sh_content)
        self.assertIn("restic backup", sh_content)
        self.assertIn('"--tag" "gitea"', sh_content)
        self.assertIn('"--tag" "authentik"', sh_content)
        self.assertIn('"--tag" "bookorbit"', sh_content)
        self.assertIn('"--tag" "espocrm"', sh_content)
        self.assertIn('"--tag" "invoiceninja"', sh_content)
        self.assertIn('"--tag" "sentry"', sh_content)

        # Verify systemd service & timer templates
        svc_path = os.path.join(WORKSPACE_DIR, "roles", "restic", "templates", "restic-backup.service.j2")
        self.assertTrue(os.path.exists(svc_path))
        timer_path = os.path.join(WORKSPACE_DIR, "roles", "restic", "templates", "restic-backup.timer.j2")
        self.assertTrue(os.path.exists(timer_path))

        # Verify restic-backup.sh.j2 renders valid bash
        import jinja2
        template = jinja2.Template(sh_content)
        rendered = template.render(
            restic_env_file="/etc/restic/env.sh",
            restic_dumps_dir="/backup/dumps",
            restic_authentik_enabled=True,
            authentik_postgres_user="authentik",
            authentik_postgres_db="authentik",
            restic_bookorbit_enabled=True,
            bookorbit_db_user="bookorbit",
            bookorbit_db_name="bookorbit",
            restic_espocrm_enabled=True,
            espocrm_db_user="espocrm",
            espocrm_db_password="changeme",
            espocrm_db_name="espocrm",
            restic_invoiceninja_enabled=True,
            invoiceninja_db_user="ninja",
            invoiceninja_db_password="changeme",
            invoiceninja_db_name="ninja",
            restic_sentry_enabled=True,
            sentry_db_user="sentry",
            sentry_db_name="sentry",
            restic_lago_enabled=True,
            lago_postgres_user="lago",
            lago_postgres_db="lago",
            restic_uptime_kuma_enabled=True,
            restic_pinchflat_enabled=True,
            restic_traefik_enabled=True,
            restic_homepage_enabled=True,
            restic_agentzero_enabled=True,
            restic_gitea_enabled=True,
            restic_keep_daily=7,
            restic_keep_weekly=4,
            restic_keep_monthly=6,
        )
        proc = subprocess.run(["bash", "-n"], input=rendered, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, f"restic-backup.sh syntax error: {proc.stderr}")

    def test_homepage_services_configuration(self):
        """Verify dash.mini.debrutal.dev services configuration includes all new sites and no fusion."""
        services_path = os.path.join(WORKSPACE_DIR, "roles", "homepage", "templates", "services.yaml.j2")
        with open(services_path, "r") as f:
            content = f.read()

        # Fusion must be completely removed
        self.assertNotIn("Fusion:", content)
        self.assertNotIn("fusion.mini.debrutal.dev", content)

        # All new and existing key sites must be included
        expected_sites = [
            "Authentik",
            "Traefik Proxy",
            "Homepage Dashboard",
            "Lago",
            "Invoice Ninja",
            "EspoCRM",
            "Uptime Kuma",
            "Sentry (GlitchTip)",
            "Grafana (LGTM)",
            "Prometheus",
            "Gitea",
            "BookOrbit",
            "Pinchflat",
            "eBook2Audiobook",
            "Agent Zero",
            "Home Assistant",
        ]
        for site in expected_sites:
            self.assertIn(site, content, f"Expected site {site} missing from dash.mini.debrutal.dev services")

    def test_traefik_acme_wildcard_domains(self):
        """Verify Traefik ACME wildcard domains configuration for mini.debrutal.dev and staging.kita-kit.de."""
        domains = self.all_vars.get("traefik_acme_domains", [])
        self.assertTrue(len(domains) >= 2, "traefik_acme_domains must contain at least 2 domains")

        domain_names = [d.get("main") for d in domains]
        self.assertIn("mini.debrutal.dev", domain_names)
        self.assertIn("staging.kita-kit.de", domain_names)

        # Check SANs for both domains
        mini_entry = next(d for d in domains if d.get("main") == "mini.debrutal.dev")
        self.assertIn("*.mini.debrutal.dev", mini_entry.get("sans", []))

        staging_entry = next(d for d in domains if d.get("main") == "staging.kita-kit.de")
        self.assertIn("*.staging.kita-kit.de", staging_entry.get("sans", []))

        # Check DNS challenge provider & token
        self.assertEqual(self.all_vars.get("traefik_acme_challenge_type"), "dns")
        self.assertEqual(self.all_vars.get("traefik_acme_dns_provider"), "cloudflare")
        dns_env = self.all_vars.get("traefik_acme_dns_env", {})
        self.assertIn("vault_cf_dns_api_token", str(dns_env.get("CF_DNS_API_TOKEN", "")))

    def test_traefik_templates_wildcard_domains_rendering(self):
        """Verify traefik.yml.j2 and docker-compose.yml.j2 render both wildcard domains properly."""
        import jinja2

        env = jinja2.Environment()

        # Test traefik.yml.j2
        with open(os.path.join(WORKSPACE_DIR, "roles", "traefik", "templates", "traefik.yml.j2"), "r") as f:
            template_str = f.read()

        rendered_traefik = env.from_string(template_str).render(self.all_vars)
        self.assertIn('main: "mini.debrutal.dev"', rendered_traefik)
        self.assertIn('*.mini.debrutal.dev', rendered_traefik)
        self.assertIn('main: "staging.kita-kit.de"', rendered_traefik)
        self.assertIn('*.staging.kita-kit.de', rendered_traefik)

        # Test docker-compose.yml.j2
        with open(os.path.join(WORKSPACE_DIR, "roles", "traefik", "templates", "docker-compose.yml.j2"), "r") as f:
            compose_template_str = f.read()

        rendered_compose = env.from_string(compose_template_str).render(self.all_vars)
        self.assertIn("traefik_api.tls.domains[0].main=mini.debrutal.dev", rendered_compose)
        self.assertIn("traefik_api.tls.domains[0].sans=*.mini.debrutal.dev", rendered_compose)
        self.assertIn("traefik_api.tls.domains[1].main=staging.kita-kit.de", rendered_compose)
        self.assertIn("traefik_api.tls.domains[1].sans=*.staging.kita-kit.de", rendered_compose)

    def test_traefik_multi_token_configuration(self):
        """Verify multi-token configuration when a separate token is provided for kita-kit.de."""
        import jinja2

        env = jinja2.Environment()
        multi_vars = dict(self.all_vars)
        multi_vars["traefik_acme_kitakit_token"] = "mock_kitakit_token_12345"

        # 1. In dynamic_conf.yml.j2, certificates entry must be rendered
        with open(os.path.join(WORKSPACE_DIR, "roles", "traefik", "templates", "dynamic_conf.yml.j2"), "r") as f:
            dyn_tpl = f.read()
        rendered_dyn = env.from_string(dyn_tpl).render(multi_vars)
        self.assertIn("staging.kita-kit.de.crt", rendered_dyn)
        self.assertIn("staging.kita-kit.de.key", rendered_dyn)

        # 2. In cert-kitakit.sh.j2, mock token must be rendered
        with open(os.path.join(WORKSPACE_DIR, "roles", "traefik", "templates", "cert-kitakit.sh.j2"), "r") as f:
            script_tpl = f.read()
        rendered_script = env.from_string(script_tpl).render(multi_vars)
        self.assertIn("CF_DNS_API_TOKEN=mock_kitakit_token_12345", rendered_script)
        self.assertIn("staging.kita-kit.de", rendered_script)
        self.assertIn("*.staging.kita-kit.de", rendered_script)
        self.assertIn("goacme/lego:latest", rendered_script)

        # 3. In traefik.yml.j2, only main domain is rendered when separate token is used
        with open(os.path.join(WORKSPACE_DIR, "roles", "traefik", "templates", "traefik.yml.j2"), "r") as f:
            traefik_tpl = f.read()
        rendered_traefik = env.from_string(traefik_tpl).render(multi_vars)
        self.assertIn('main: "mini.debrutal.dev"', rendered_traefik)
        self.assertNotIn('main: "staging.kita-kit.de"', rendered_traefik)

    def test_container_improvements(self):
        """Verify bug fixes and improvements from container audit."""
        # 1. Homepage allowed hosts include internal container names
        homepage_defaults_path = os.path.join(WORKSPACE_DIR, "roles", "homepage", "defaults", "main.yml")
        with open(homepage_defaults_path, "r") as f:
            hp_defaults = f.read()
        self.assertIn("'homepage'", hp_defaults)
        self.assertIn("'homepage:3000'", hp_defaults)
        self.assertIn("'homepage'", self.all_vars.get("homepage_allowed_hosts", ""))
        self.assertIn("'homepage:3000'", self.all_vars.get("homepage_allowed_hosts", ""))

        # 2. LGTM telemetry disabled
        with open(os.path.join(WORKSPACE_DIR, "roles", "lgtm", "templates", "loki-config.yaml.j2"), "r") as f:
            loki_cfg = f.read()
        self.assertIn("reporting_enabled: false", loki_cfg)

        with open(os.path.join(WORKSPACE_DIR, "roles", "lgtm", "templates", "tempo-config.yaml.j2"), "r") as f:
            tempo_cfg = f.read()
        self.assertIn("reporting_enabled: false", tempo_cfg)

        # 3. Traefik forwardAuth maxResponseBodySize configured
        with open(os.path.join(WORKSPACE_DIR, "roles", "traefik", "templates", "dynamic_conf.yml.j2"), "r") as f:
            dyn_cfg = f.read()
        self.assertIn("maxResponseBodySize: 1048576", dyn_cfg)

        # 4. Invoice Ninja Kuma URL uses HTTPS domain
        with open(os.path.join(WORKSPACE_DIR, "roles", "invoiceninja", "templates", "docker-compose.yml.j2"), "r") as f:
            inv_cfg = f.read()
        self.assertIn("kuma.invoiceninja.http.url=https://{{ invoiceninja_domain }}", inv_cfg)


if __name__ == "__main__":
    unittest.main()


