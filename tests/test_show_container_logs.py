#!/usr/bin/env python3
"""
Unit and integration test suite for show_container_logs.sh script.
"""

import os
import subprocess
import unittest

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(WORKSPACE_DIR, "scripts", "show_container_logs.sh")
SYMLINK_PATH = os.path.join(WORKSPACE_DIR, "show_container_logs.sh")


class TestShowContainerLogsScript(unittest.TestCase):

    def test_script_exists_and_executable(self):
        """Verify the script exists and is executable."""
        self.assertTrue(os.path.exists(SCRIPT_PATH), f"{SCRIPT_PATH} does not exist")
        self.assertTrue(os.access(SCRIPT_PATH, os.X_OK), f"{SCRIPT_PATH} is not executable")
        self.assertTrue(os.path.exists(SYMLINK_PATH), f"Root symlink {SYMLINK_PATH} does not exist")

    def test_help_option(self):
        """Verify script --help outputs usage info and exits with 0."""
        res = subprocess.run([SCRIPT_PATH, "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Usage: show_container_logs.sh", res.stdout)
        self.assertIn("--follow", res.stdout)
        self.assertIn("--all", res.stdout)
        self.assertIn("--tail", res.stdout)

    def test_invalid_option(self):
        """Verify script exits with error code 1 when given invalid argument."""
        res = subprocess.run([SCRIPT_PATH, "--invalid-flag-xyz"], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Error: Unknown option", res.stderr)

    def test_filter_nonexistent(self):
        """Verify script handles non-matching container filter gracefully."""
        res = subprocess.run([SCRIPT_PATH, "-a", "-g", "nonexistent_container_xyz_999"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("No containers matched filter pattern", res.stdout)

    def test_no_color_flag(self):
        """Verify --no-color flag runs without error."""
        res = subprocess.run([SCRIPT_PATH, "-a", "--no-color", "-n", "1"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

    def test_tail_flag_validation(self):
        """Verify --tail flag missing argument error handling."""
        res = subprocess.run([SCRIPT_PATH, "--tail"], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Error: --tail requires an argument", res.stderr)

    def test_remote_flags_validation(self):
        """Verify --remote and --host flag argument validation."""
        res_r = subprocess.run([SCRIPT_PATH, "--remote"], capture_output=True, text=True)
        self.assertNotEqual(res_r.returncode, 0)
        self.assertIn("Error: --remote requires a USER@HOST argument", res_r.stderr)

        res_h = subprocess.run([SCRIPT_PATH, "--host"], capture_output=True, text=True)
        self.assertNotEqual(res_h.returncode, 0)
        self.assertIn("Error: --host requires a host URL argument", res_h.stderr)


if __name__ == "__main__":
    unittest.main()

