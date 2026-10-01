#!/usr/bin/env python3
"""
Unit tests to verify user credentials configuration across all application roles and group variables.
"""

import os
import unittest
import yaml

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
        self.assertIn("lgtm_authentik_enabled: true", content)


if __name__ == "__main__":



    unittest.main()
