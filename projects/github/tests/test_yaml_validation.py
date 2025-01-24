"""Tests for YAML configuration validation."""

import os
import shutil
import unittest
from pathlib import Path

# trunk-ignore(bandit/B404)
from subprocess import CalledProcessError, run
from typing import Any, Dict, List, Optional, Tuple, Union

import pytest
import yaml

# Constants for executables with full paths
GIT_PATH = shutil.which("git")
GH_PATH = shutil.which("gh")

if not all([GIT_PATH, GH_PATH]):
    raise RuntimeError("Required executables not found")


def safe_run_command(
    cmd: List[Union[str, None]], input: Optional[str] = None, **kwargs: Any
) -> Any:
    """Safely execute a command with subprocess."""
    if not cmd:
        raise ValueError("Command list cannot be empty")

    # Convert all arguments to strings, skipping None values
    cmd_list: List[str] = []
    for arg in cmd:
        if arg is None:
            continue
        try:
            cmd_list.append(str(arg))
        except (TypeError, ValueError):
            raise ValueError(f"Cannot convert argument to string: {arg}")

    if not cmd_list:
        raise ValueError("Command list is empty after filtering None values")

    # Validate first argument is absolute path
    if not os.path.isabs(cmd_list[0]):
        raise ValueError(f"First argument must be absolute path: {cmd_list[0]}")

    kwargs.setdefault("shell", False)
    kwargs.setdefault("timeout", 30)
    kwargs.setdefault("check", True)

    # trunk-ignore(bandit/B603)
    return run(cmd_list, input=input, **kwargs)


def validate_hook_command(cmd_path: str, cmd_name: str) -> bool:
    """Validate a git hook command.

    Args:
        cmd_path: Full path to the command
        cmd_name: Original command name for error messages

    Returns:
        bool: True if command is valid

    Raises:
        ValueError: If command is invalid
    """
    if not cmd_path or not os.path.isabs(cmd_path):
        raise ValueError(f"Hook command {cmd_name} not found or invalid")

    # Add hook command to whitelist temporarily
    ALLOWED_COMMANDS[os.path.basename(cmd_path)] = [("--version",)]
    return True


# Whitelist of allowed commands and their valid arguments
ALLOWED_COMMANDS: Dict[str, List[Tuple[str, ...]]] = {
    "git": [
        ("--version",),
        ("lfs", "version"),
        ("checkout", "-b"),
        ("init",),
        ("add", "."),
        ("commit", "-m"),
        ("push", "-u", "origin"),
    ],
    "gh": [
        ("--version",),
        ("auth", "status"),
        ("repo", "view"),
        ("repo", "delete"),
        ("repo", "create"),
        ("repo", "edit"),
        ("api", "user", "--jq", ".login"),
    ],
}


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
            result = safe_run_command(
                [GIT_PATH, "--version"], capture_output=True, text=True
            )
            self.assertTrue(result.stdout.startswith("git version"))
        except CalledProcessError:
            self.fail("git CLI is not available")

    def test_github_cli_available(self) -> None:
        """Test if GitHub CLI is available."""
        try:
            result = safe_run_command(
                [GH_PATH, "--version"], capture_output=True, text=True
            )
            self.assertTrue("gh version" in result.stdout)
        except CalledProcessError:
            self.fail("GitHub CLI is not available")

    def test_github_cli_auth(self) -> None:
        """Test if GitHub CLI is authenticated."""
        try:
            result = safe_run_command(
                [GH_PATH, "auth", "status"], capture_output=True, text=True
            )
            self.assertTrue("Logged in to" in result.stdout)
        except CalledProcessError:
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
        if "hooks" not in self.config["git"]:
            return

        hooks = self.config["git"]["hooks"]
        for hook_type, commands in hooks.items():
            for cmd in commands:
                cmd_path = shutil.which(cmd)
                try:
                    # Validate hook command before running it
                    validate_hook_command(cmd_path, cmd)
                    result = safe_run_command(
                        [cmd_path, "--version"],
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(
                        result.returncode, 0, f"Hook command {cmd} not available"
                    )
                except (ValueError, CalledProcessError) as e:
                    self.fail(f"Hook command {cmd} validation failed: {str(e)}")

    @pytest.mark.skipif(
        not GIT_PATH
        or safe_run_command(
            [GIT_PATH, "lfs", "version"], capture_output=True
        ).returncode
        != 0,
        reason="Git LFS is not installed",
    )
    def test_git_lfs_available(self) -> None:
        """Test if Git LFS is available when enabled."""
        if self.config["git"].get("lfs", {}).get("enabled", False):
            result = safe_run_command(
                [GIT_PATH, "lfs", "version"],
                capture_output=True,
                text=True,
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
