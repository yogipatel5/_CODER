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
from typing import Any, Dict

from core.services import ConfigurationError

logger = logging.getLogger(__name__)


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
