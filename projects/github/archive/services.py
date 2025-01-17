"""Archive services for managing Git repositories."""

import os
import shutil

# trunk-ignore(bandit/B404)
from subprocess import CalledProcessError, run
from typing import Any, List


def safe_run_command(cmd: List[str], **kwargs) -> Any:
    """Safely execute a command with subprocess."""
    if not cmd:
        raise ValueError("Command list cannot be empty")

    # Get full path for executable
    cmd_path = shutil.which(cmd[0])
    if not cmd_path:
        raise ValueError(f"Command not found: {cmd[0]}")

    # Replace command with full path
    cmd[0] = cmd_path

    # Set safe defaults
    kwargs.setdefault("shell", False)
    kwargs.setdefault("check", True)

    # trunk-ignore(bandit/B603)
    return run(cmd, **kwargs)


def archive_repository(repo_path: str, archive_path: str) -> None:
    """Archive a Git repository.

    Args:
        repo_path: Path to the repository
        archive_path: Path where to create the archive
    """
    if not os.path.exists(repo_path):
        raise ValueError(f"Repository path does not exist: {repo_path}")

    # Create archive directory if it doesn't exist
    os.makedirs(os.path.dirname(archive_path), exist_ok=True)

    try:
        # Create archive
        safe_run_command(
            ["git", "archive", "--format=zip", "--output", archive_path, "HEAD"],
            cwd=repo_path,
        )
    except CalledProcessError as e:
        raise RuntimeError(f"Failed to create archive: {e}")


def restore_repository(archive_path: str, restore_path: str) -> None:
    """Restore a Git repository from archive.

    Args:
        archive_path: Path to the archive file
        restore_path: Path where to restore the repository
    """
    if not os.path.exists(archive_path):
        raise ValueError(f"Archive file does not exist: {archive_path}")

    # Create restore directory
    os.makedirs(restore_path, exist_ok=True)

    try:
        # Extract archive
        safe_run_command(["unzip", archive_path], cwd=restore_path)

        # Initialize new repository
        safe_run_command(["git", "init"], cwd=restore_path)

        # Add and commit files
        safe_run_command(["git", "add", "."], cwd=restore_path)
        safe_run_command(
            ["git", "commit", "-m", "Restored from archive"],
            cwd=restore_path,
        )
    except CalledProcessError as e:
        # Cleanup on failure
        shutil.rmtree(restore_path, ignore_errors=True)
        raise RuntimeError(f"Failed to restore repository: {e}")
