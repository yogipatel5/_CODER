"""
GitHub management services for handling git repositories and related operations.
"""

import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict

from core.services import ConfigurationError

from .git_service import GitError, GitService

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Exception raised for errors during repository operations."""

    pass


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


class BackupIncludes(TypedDict):
    """Type for backup includes information."""

    all_branches: bool
    all_tags: bool
    lfs: bool
    wiki: bool


class BackupInfo(TypedDict):
    """Type for backup information."""

    repository: str
    backup_path: str
    timestamp: str
    includes: BackupIncludes


def initialize_git_repository(config: Dict[str, Any], project_path: str) -> None:
    """Initialize a git repository and create initial commit.

    Args:
        config: Configuration dictionary containing git settings
        project_path: Path to project directory

    Raises:
        ConfigurationError: If git initialization fails
    """
    if "git" not in config or not config["git"].get("create_repo", True):
        logger.info("Git repository creation not requested")
        return

    try:
        git_service = GitService(project_path)

        # Add all files
        logger.info("Adding files to git repository")
        git_service.stage_files()

        # Initial commit with simple message
        logger.info("Creating initial commit")
        git_service.commit("Initial project setup")

        # Create additional branches if specified
        if "other_branches" in config["git"]:
            for branch in config["git"]["other_branches"]:
                logger.info(f"Creating branch: {branch}")
                git_service.create_branch(branch)

        # Verify repository state
        status = git_service.get_status()
        if any(status.values()):
            logger.warning("Uncommitted changes remain after initialization")

        logger.info("Git repository initialized successfully")

    except GitError as e:
        logger.error(f"Git command failed: {str(e)}")
        raise ConfigurationError(f"Failed to initialize git repository: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error initializing git repository: {str(e)}")
        raise ConfigurationError(f"Failed to initialize git repository: {str(e)}")


def push_changes(repo_path: str, options: PushOptions) -> None:
    """Push changes to remote repository with specified options."""
    try:
        git_service = GitService(repo_path)

        # Check if force push is allowed
        if options.force and options.protection_level != PushProtection.NONE:
            raise PushError("Force push is not allowed with current protection level")

        # Check if branch is up to date for strict protection
        if options.protection_level == PushProtection.STRICT:
            git_service.pull(options.remote, options.branch)
            status = git_service.get_status()
            if any(status.values()):
                raise PushError("Branch is not up to date with remote")

        # Push changes
        git_service.push(
            remote=options.remote, branch=options.branch, force=options.force
        )
        logger.info("Changes pushed successfully")

    except GitError as e:
        raise PushError(f"Push failed: {str(e)}")
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
            f"import time; time.sleep({delay}); "
            f"from github_management.services import push_changes, PushOptions; "
            f"push_changes('{repo_path}', {options})",
            "&",
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Push scheduled for {options.scheduled_time}")

    except Exception as e:
        raise PushError(f"Failed to schedule push: {str(e)}")


def get_push_protection(repo_path: str) -> PushProtection:
    """Get the current push protection level for a repository."""
    try:
        git_service = GitService(repo_path)
        status = git_service.get_status()

        # If there are uncommitted changes, use BASIC protection
        if any(status.values()):
            return PushProtection.BASIC

        return PushProtection.NONE

    except GitError as e:
        raise PushError(f"Failed to get push protection: {str(e)}")


def set_push_protection(repo_path: str, level: PushProtection) -> None:
    """Set the push protection level for a repository."""
    try:
        git_service = GitService(repo_path)
        status = git_service.get_status()

        # If setting NONE protection but there are changes, prevent it
        if level == PushProtection.NONE and any(status.values()):
            raise PushError("Cannot disable protection with uncommitted changes")

        logger.info(f"Push protection level set to {level.value}")

    except GitError as e:
        raise PushError(f"Failed to set push protection: {str(e)}")


def backup_repository(
    repo_name: str,
    backup_dir: str,
    include_lfs: bool = True,
    include_wiki: bool = True,
) -> BackupInfo:
    """Create a backup of a GitHub repository.

    Args:
        repo_name: Repository name to backup
        backup_dir: Directory to store backup
        include_lfs: Whether to include LFS objects
        include_wiki: Whether to include wiki

    Returns:
        Dictionary containing backup information

    Raises:
        RepositoryError: If backup fails
    """
    try:
        # Create backup directory if it doesn't exist
        backup_path = (
            Path(backup_dir) / f"{repo_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        backup_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Creating backup of {repo_name} in {backup_path}")

        # Clone repository with all branches and tags
        subprocess.run(
            [
                "gh",
                "repo",
                "clone",
                f"yogipatel5/{repo_name}",
                str(backup_path),
                "--",
                "--mirror",
            ],
            check=True,
            capture_output=True,
        )

        backup_info: BackupInfo = {
            "repository": repo_name,
            "backup_path": str(backup_path),
            "timestamp": datetime.now().isoformat(),
            "includes": {
                "all_branches": True,
                "all_tags": True,
                "lfs": False,
                "wiki": False,
            },
        }

        if include_lfs:
            try:
                # Fetch LFS objects
                logger.info("Fetching LFS objects")
                subprocess.run(
                    ["git", "lfs", "fetch", "--all"],
                    cwd=str(backup_path),
                    check=True,
                    capture_output=True,
                )
                backup_info["includes"]["lfs"] = True
            except subprocess.CalledProcessError:
                logger.warning("Failed to fetch LFS objects, skipping")

        if include_wiki:
            try:
                # Clone wiki if it exists
                wiki_path = backup_path / "wiki"
                subprocess.run(
                    [
                        "gh",
                        "repo",
                        "clone",
                        f"yogipatel5/{repo_name}.wiki",
                        str(wiki_path),
                    ],
                    check=True,
                    capture_output=True,
                )
                backup_info["includes"]["wiki"] = True
            except subprocess.CalledProcessError:
                logger.warning("Failed to clone wiki, skipping")

        logger.info(f"Backup completed: {backup_path}")
        return backup_info

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"Failed to backup repository: {error_msg}")
        raise RepositoryError(f"Failed to backup repository: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error backing up repository: {str(e)}")
        raise RepositoryError(f"Unexpected error backing up repository: {str(e)}")
