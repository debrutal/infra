#!/usr/bin/env python3
"""
Unit tests for deploy.sh script.
Verifies option parsing, defaults, dry-run output, and error handling.
"""

import os
import subprocess
import unittest

SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deploy.sh"))


class TestDeployScript(unittest.TestCase):

    def run_script(self, args):
        cmd = [SCRIPT_PATH] + args
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result

    def test_default_dry_run(self):
        result = self.run_script(["--dry-run"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("ansible-playbook site.yml --tags traefik,gitea", result.stdout)
        self.assertIn("-e traefik_force_restart=false -e traefik_reset_acme=false", result.stdout)

    def test_reset_acme_and_force_restart_flags(self):
        result = self.run_script(["--reset-acme", "--force-restart", "--dry-run"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("traefik_force_restart=true", result.stdout)
        self.assertIn("traefik_reset_acme=true", result.stdout)

    def test_interactive_prompts_when_no_secret_files(self):
        result = self.run_script(["--no-vault", "--no-become", "--dry-run"])
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("--ask-vault-pass", result.stdout)
        self.assertNotIn("-K", result.stdout)

    def test_vault_pass_file(self):
        result = self.run_script(["--vault-pass-file", "/tmp/dummy_vault.txt", "--no-become", "--dry-run"])
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("--ask-vault-pass", result.stdout)
        self.assertNotIn("-K", result.stdout)
        self.assertIn("--vault-password-file /tmp/dummy_vault.txt", result.stdout)

    def test_become_pass_file(self):
        result = self.run_script(["--become-pass-file", "/tmp/dummy_become.txt", "--no-vault", "--dry-run"])
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("--ask-vault-pass", result.stdout)
        self.assertNotIn("-K", result.stdout)
        self.assertIn("--become-password-file /tmp/dummy_become.txt", result.stdout)

    def test_help_flag(self):
        result = self.run_script(["--help"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: ./deploy.sh", result.stdout)

    def test_missing_argument_error(self):
        result = self.run_script(["-t"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires an argument", result.stderr)

    def test_interactive_cli_defaults(self):
        # Interactive mode inputs:
        # 1. 'c' (confirm tag selection with defaults traefik,gitea)
        # 2. '\n' (traefik restart: default N)
        # 3. '\n' (traefik reset acme: default N)
        # 4. '\n' (gitea restart: default N)
        # 5. 'y' (dry-run mode)
        # 6. '\n' (extra vars: none)
        # 7. 'y' (confirm proceed)
        user_input = "c\n\n\n\ny\n\ny\n"
        cmd = [SCRIPT_PATH, "-i"]
        result = subprocess.run(cmd, input=user_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Ansible Infrastructure Deployment CLI - Select Tags", result.stdout)
        self.assertIn("--tags traefik,gitea", result.stdout)
        self.assertIn("[DRY RUN] Command not executed.", result.stdout)

    def test_interactive_cli_custom_tags_and_restart(self):
        # 1. 'n' (clear all)
        # 2. '1 4' (select traefik [1] and common [4])
        # 3. 'c' (confirm tags)
        # 4. 'y' (traefik restart)
        # 5. 'n' (traefik reset acme)
        # 6. 'y' (common restart)
        # 7. 'y' (dry-run mode)
        # 8. 'custom_var=123' (extra vars)
        # 9. 'y' (confirm proceed)
        user_input = "n\n1 4\nc\ny\nn\ny\ny\ncustom_var=123\ny\n"
        cmd = [SCRIPT_PATH, "-i"]
        result = subprocess.run(cmd, input=user_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--tags traefik,common", result.stdout)
        self.assertIn("traefik_force_restart=true", result.stdout)
        self.assertIn("common_force_restart=true", result.stdout)
        self.assertIn("custom_var=123", result.stdout)
        self.assertIn("[DRY RUN] Command not executed.", result.stdout)

    def test_interactive_cli_runner(self):
        # 1. 'n' (clear all)
        # 2. '3' (select runner [3])
        # 3. 'c' (confirm tags)
        # 4. 'y' (enable gitea runner)
        # 5. '8' (8 runner instances)
        # 6. 'y' (restart runner containers)
        # 7. 'y' (dry run)
        # 8. '' (no extra vars)
        # 9. 'y' (confirm)
        user_input = "n\n3\nc\ny\n8\ny\ny\n\ny\n"
        cmd = [SCRIPT_PATH, "-i"]
        result = subprocess.run(cmd, input=user_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--tags runner", result.stdout)
        self.assertIn("gitea_runner_enabled=true", result.stdout)
        self.assertIn("gitea_runner_count=8", result.stdout)
        self.assertIn("runner_force_restart=true", result.stdout)

    def test_interactive_cli_pinchflat(self):
        # 1. 'n' (clear all)
        # 2. '17' (select pinchflat [17])
        # 3. 'c' (confirm tags)
        # 4. 'y' (restart pinchflat container)
        # 5. 'y' (dry run)
        # 6. '' (no extra vars)
        # 7. 'y' (confirm)
        user_input = "n\n17\nc\ny\ny\n\ny\n"
        cmd = [SCRIPT_PATH, "-i"]
        result = subprocess.run(cmd, input=user_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--tags pinchflat", result.stdout)
        self.assertIn("pinchflat_force_restart=true", result.stdout)

    def test_interactive_cli_ebook2audiobook(self):
        # 1. 'n' (clear all)
        # 2. '18' (select ebook2audiobook [18])
        # 3. 'c' (confirm tags)
        # 4. 'y' (restart ebook2audiobook container)
        # 5. 'y' (dry run)
        # 6. '' (no extra vars)
        # 7. 'y' (confirm)
        user_input = "n\n18\nc\ny\ny\n\ny\n"
        cmd = [SCRIPT_PATH, "-i"]
        result = subprocess.run(cmd, input=user_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--tags ebook2audiobook", result.stdout)
        self.assertIn("ebook2audiobook_force_restart=true", result.stdout)

    def test_interactive_cli_restic(self):
        # 1. 'n' (clear all)
        # 2. '19' (select restic [19])
        # 3. 'c' (confirm tags)
        # 4. 'y' (restart restic container/service)
        # 5. 'y' (dry run)
        # 6. '' (no extra vars)
        # 7. 'y' (confirm)
        user_input = "n\n19\nc\ny\ny\n\ny\n"
        cmd = [SCRIPT_PATH, "-i"]
        result = subprocess.run(cmd, input=user_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--tags restic", result.stdout)

    def test_interactive_cli_cancel(self):
        user_input = "c\n\n\n\ny\n\nn\n"
        cmd = [SCRIPT_PATH, "-i"]
        result = subprocess.run(cmd, input=user_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Deployment cancelled.", result.stdout)


if __name__ == "__main__":
    unittest.main()


