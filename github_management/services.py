"""
GitHub management services for handling git repositories and related operations.
"""

# TODO: Need to implement remote repository creation and linking
# TODO: Need to implement branch management operations (create, delete, merge)
# TODO: Need to implement commit message templates and validation
# TODO: Need to implement automated git commit operations
# TODO: Need to implement git push operations with error handling

import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from core.services import ConfigurationError

logger = logging.getLogger(__name__)


class PushError(Exception):
    """Exception raised for errors during push operations."""

    pass


class PushProtection(Enum):
    """Protection levels for push operations."""

    NONE = "none"
    BASIC = "basic"  # Prevents force push
    STRICT = "strict"  # Requires up-to-date branch and passing checks


@dataclass
class PushOptions:
    """Configuration for push operations."""

    remote: str = "origin"
    branch: str = "main"
    force: bool = False
    force_with_lease: bool = False
    tags: bool = False
    set_upstream: bool = False
    protection_level: PushProtection = PushProtection.BASIC
    scheduled_time: Optional[datetime] = None


def push_changes(repo_path: str, options: PushOptions) -> None:
    """Push changes to remote repository with specified options."""
    try:
        original_dir = os.getcwd()
        os.chdir(repo_path)

        try:
            # Check if force push is allowed
            if options.force and options.protection_level != PushProtection.NONE:
                raise PushError(
                    "Force push is not allowed with current protection level"
                )

            # Check if branch is up to date for strict protection
            if options.protection_level == PushProtection.STRICT:
                subprocess.run(
                    ["git", "fetch", options.remote, options.branch],
                    check=True,
                    capture_output=True,
                )
                result = subprocess.run(
                    ["git", "status", "-uno"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if "Your branch is behind" in result.stdout:
                    raise PushError("Branch is not up to date with remote")

            # Build push command
            cmd = ["git", "push"]
            if options.force:
                cmd.append("--force")
            elif options.force_with_lease:
                cmd.append("--force-with-lease")
            if options.set_upstream:
                cmd.extend(["--set-upstream"])
            cmd.extend([options.remote, options.branch])
            if options.tags:
                cmd.append("--tags")

            # Execute push command
            logger.info(f"Pushing changes with command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True)

        finally:
            os.chdir(original_dir)

    except subprocess.CalledProcessError as e:
        raise PushError(f"Push failed: {e.stderr.decode()}")
    except Exception as e:
        raise PushError(f"Push operation failed: {str(e)}")


def schedule_push(repo_path: str, options: PushOptions) -> None:
    """Schedule a push operation for later execution."""
    if not options.scheduled_time:
        raise ValueError("Scheduled time must be provided")

    delay = (options.scheduled_time - datetime.now()).total_seconds()
    if delay < 0:
        raise ValueError("Scheduled time must be in the future")

    try:
        # Create a background process to handle the scheduled push
        cmd = [
            "nohup",
            "python",
            "-c",
            f"import time; time.sleep({delay}); from github_management.services import push_changes, PushOptions; push_changes('{repo_path}', {options})",
            "&",
        ]
        subprocess.Popen(cmd)
        logger.info(f"Push scheduled for {options.scheduled_time}")

    except Exception as e:
        raise PushError(f"Failed to schedule push: {str(e)}")


def get_push_protection(repo_path: str) -> PushProtection:
    """Get the current push protection level for a repository."""
    try:
        # Check for git configuration
        result = subprocess.run(
            ["git", "config", "--get", "push.protection"],
            check=True,
            capture_output=True,
            text=True,
        )
        protection = result.stdout.strip()
        return PushProtection(protection) if protection else PushProtection.BASIC

    except subprocess.CalledProcessError:
        return PushProtection.BASIC
    except Exception as e:
        raise PushError(f"Failed to get push protection: {str(e)}")


def set_push_protection(repo_path: str, level: PushProtection) -> None:
    """Set the push protection level for a repository."""
    try:
        subprocess.run(
            ["git", "config", "push.protection", level.value],
            check=True,
            capture_output=True,
        )
        logger.info(f"Push protection level set to {level.value}")

    except subprocess.CalledProcessError as e:
        raise PushError(f"Failed to set push protection: {e.stderr.decode()}")
    except Exception as e:
        raise PushError(f"Failed to set push protection: {str(e)}")


def initialize_git_repository(config: Dict[str, Any], project_path: str) -> None:
    """Initialize a git repository and create initial commit."""
    if "git" not in config or not config["git"].get("create_repo", True):
        logger.info("Git repository creation not requested")
        return

    try:
        # Change to project directory for git operations
        original_dir = os.getcwd()
        os.chdir(project_path)

        try:
            # Initialize git repository
            logger.info("Initializing git repository")
            subprocess.run(["git", "init"], check=True, capture_output=True)

            # Set initial branch name
            initial_branch = config["git"].get("initial_branch", "main")
            subprocess.run(
                ["git", "checkout", "-b", initial_branch],
                check=True,
                capture_output=True,
            )

            # Add all files
            logger.info("Adding files to git repository")
            subprocess.run(["git", "add", "."], check=True, capture_output=True)

            # Initial commit
            commit_message = config["git"].get(
                "commit_message", "Initial project setup - created by coder"
            )
            logger.info(f"Creating initial commit: {commit_message}")
            subprocess.run(
                ["git", "commit", "-m", commit_message], check=True, capture_output=True
            )

            # Create additional branches if specified
            if "other_branches" in config["git"]:
                for branch in config["git"]["other_branches"]:
                    logger.info(f"Creating branch: {branch}")
                    subprocess.run(
                        ["git", "branch", branch], check=True, capture_output=True
                    )

            logger.info("Git repository initialized successfully")

        finally:
            # Always return to original directory
            os.chdir(original_dir)

    except subprocess.CalledProcessError as e:
        raise ConfigurationError(
            f"Git command failed: {e.cmd}\nOutput: {e.output.decode()}"
        )
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize git repository: {str(e)}")
