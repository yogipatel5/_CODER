"""Tests for YAML configuration validation."""

import os
import subprocess
import unittest
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml


@pytest.mark.integration
class TestYAMLValidation(unittest.TestCase):
    """Test cases for YAML configuration validation."""

    test_yaml_path: Path
    config: Dict[str, Any]

    def setUp(self) -> None:
        """Set up test environment."""
        self.test_yaml_path = Path("_test_project.yaml")
        with open(self.test_yaml_path) as f:
            self.config = yaml.safe_load(f)

    def test_git_cli_available(self) -> None:
        """Test if git CLI is available."""
        try:
            result = subprocess.run(
                ["git", "--version"], capture_output=True, text=True, check=True
            )
            self.assertTrue(result.stdout.startswith("git version"))
        except subprocess.CalledProcessError:
            self.fail("git CLI is not available")

    def test_github_cli_available(self) -> None:
        """Test if GitHub CLI is available."""
        try:
            result = subprocess.run(
                ["gh", "--version"], capture_output=True, text=True, check=True
            )
            self.assertTrue("gh version" in result.stdout)
        except subprocess.CalledProcessError:
            self.fail("GitHub CLI is not available")

    def test_github_cli_auth(self) -> None:
        """Test if GitHub CLI is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, check=True
            )
            self.assertTrue("Logged in to" in result.stdout)
        except subprocess.CalledProcessError:
            self.fail("GitHub CLI is not authenticated")

    def test_required_fields(self) -> None:
        """Test if all required fields are present in YAML."""
        required_fields = {
            "project_name": str,
            "path": str,
            "git": dict,
        }

        for field, field_type in required_fields.items():
            self.assertIn(field, self.config)
            self.assertIsInstance(self.config[field], field_type)

    def test_git_config_fields(self) -> None:
        """Test if git configuration has all required fields."""
        git_config = self.config["git"]
        required_git_fields = {
            "create_local_repo": bool,
            "create_remote_repo": bool,
            "initial_branch": str,
            "commit_message": str,
        }

        for field, field_type in required_git_fields.items():
            self.assertIn(field, git_config)
            self.assertIsInstance(git_config[field], field_type)

    def test_git_hooks_available(self) -> None:
        """Test if specified git hooks are available."""
        if "hooks" in self.config["git"]:
            hooks = self.config["git"]["hooks"]
            for hook_type, commands in hooks.items():
                for cmd in commands:
                    try:
                        result = subprocess.run(
                            [cmd, "--version"], capture_output=True, text=True
                        )
                        self.assertEqual(
                            result.returncode, 0, f"Hook command {cmd} not available"
                        )
                    except FileNotFoundError:
                        self.fail(f"Hook command {cmd} not found")

    @pytest.mark.skipif(
        subprocess.run(
            ["git", "lfs", "version"],
            capture_output=True,
            text=True,
        ).returncode
        != 0,
        reason="Git LFS is not installed",
    )
    def test_git_lfs_available(self) -> None:
        """Test if Git LFS is available when enabled."""
        if self.config["git"].get("lfs", {}).get("enabled", False):
            result = subprocess.run(
                ["git", "lfs", "version"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue("git-lfs" in result.stdout)

    def test_project_path_valid(self) -> None:
        """Test if project path is valid and accessible."""
        path = os.path.expanduser(self.config["path"])
        path = os.path.abspath(path)

        # Create parent directory if it doesn't exist
        parent_dir = os.path.dirname(path)
        os.makedirs(parent_dir, exist_ok=True)

        self.assertTrue(
            os.access(parent_dir, os.W_OK),
            f"Project parent directory {parent_dir} is not writable",
        )


if __name__ == "__main__":
    unittest.main()
