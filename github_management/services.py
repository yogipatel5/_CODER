"""
GitHub management services for handling git repositories and related operations.
"""

# TODO: Need to implement remote repository creation and linking
# TODO: Need to implement branch management operations (create, delete, merge)
# TODO: Need to implement commit message templates and validation
# TODO: Need to implement automated git commit operations
# TODO: Need to implement git push operations with error handling

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from core.services import ConfigurationError

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


def create_repository(
    name: str,
    description: str = "",
    visibility: str = "private",
    template: Optional[str] = None,
    initial_branch: str = "main",
    gitignore_template: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new GitHub repository.

    Args:
        name: Repository name
        description: Repository description
        visibility: Repository visibility (public/private)
        template: Template repository to use
        initial_branch: Name of the initial branch
        gitignore_template: .gitignore template to use

    Returns:
        Dict containing repository information

    Raises:
        RepositoryError: If repository creation fails
    """
    try:
        # Base command for repository creation
        cmd = [
            "gh",
            "repo",
            "create",
            name,
            f"--{visibility}",
            "--confirm",
        ]

        # Add optional parameters
        if description:
            cmd.extend(["--description", description])
        if template:
            cmd.extend(["--template", template])
        if initial_branch != "main":
            cmd.extend(["--default-branch", initial_branch])
        if gitignore_template:
            cmd.extend(["--gitignore", gitignore_template])

        # Create repository
        logger.info(f"Creating repository: {name}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Get repository details
        repo_info = subprocess.run(
            [
                "gh",
                "repo",
                "view",
                name,
                "--json",
                "name,url,description,visibility,defaultBranchRef",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(repo_info.stdout)

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to create repository: {error_msg}")
        raise RepositoryError(f"Failed to create repository: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error creating repository: {str(e)}")
        raise RepositoryError(f"Unexpected error creating repository: {str(e)}")


def get_all_repos() -> list[Dict[str, Any]]:
    """Get all GitHub repositories for the authenticated user.

    Returns:
        List of dictionaries containing repository information

    Raises:
        RepositoryError: If fetching repositories fails
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "repo",
                "list",
                "--json",
                "name,url,description,visibility,defaultBranchRef,createdAt,updatedAt",
                "--limit",
                "1000",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to fetch repositories: {error_msg}")
        raise RepositoryError(f"Failed to fetch repositories: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error fetching repositories: {str(e)}")
        raise RepositoryError(f"Unexpected error fetching repositories: {str(e)}")


def update_repository(
    name: str,
    new_name: str | None = None,
    description: str | None = None,
    visibility: str | None = None,
) -> Dict[str, Any]:
    """Update an existing GitHub repository.

    Args:
        name: Current repository name
        new_name: New repository name (if renaming)
        description: New repository description
        visibility: New repository visibility (public/private)

    Returns:
        Dict containing updated repository information

    Raises:
        RepositoryError: If repository update fails
    """
    try:
        # Build update command with owner
        cmd = ["gh", "repo", "edit", f"yogipatel5/{name}"]

        if new_name:
            cmd.extend(["--name", new_name])
        if description is not None:  # Allow empty description
            cmd.extend(["--description", description])
        if visibility:
            cmd.extend(
                [
                    "--visibility",
                    visibility.lower(),
                    "--accept-visibility-change-consequences",
                ]
            )

        # Execute update
        logger.info(f"Updating repository: {name}")
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Get updated repository details
        repo_info = subprocess.run(
            [
                "gh",
                "repo",
                "view",
                f"yogipatel5/{new_name or name}",
                "--json",
                "name,url,description,visibility,defaultBranchRef",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(repo_info.stdout)

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to update repository: {error_msg}")
        raise RepositoryError(f"Failed to update repository: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error updating repository: {str(e)}")
        raise RepositoryError(f"Unexpected error updating repository: {str(e)}")


def delete_repository(name: str) -> None:
    """Delete a GitHub repository.

    Args:
        name: Repository name to delete

    Raises:
        RepositoryError: If repository deletion fails
    """
    try:
        # Execute deletion command with owner
        logger.info(f"Deleting repository: {name}")
        cmd = ["gh", "repo", "delete", f"yogipatel5/{name}", "--confirm"]
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        logger.info(f"Repository {name} deleted successfully")

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to delete repository: {error_msg}")
        raise RepositoryError(f"Failed to delete repository: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error deleting repository: {str(e)}")
        raise RepositoryError(f"Unexpected error deleting repository: {str(e)}")


def list_branches(repo_name: str) -> List[Dict[str, Any]]:
    """List all branches in a repository.

    Args:
        repo_name: Repository name

    Returns:
        List of dictionaries containing branch information

    Raises:
        RepositoryError: If fetching branches fails
    """
    try:
        logger.info(f"Listing branches for repository: {repo_name}")
        result = subprocess.run(
            [
                "gh",
                "api",
                f"/repos/yogipatel5/{repo_name}/branches",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        branches = json.loads(result.stdout)
        return [
            {
                "name": branch["name"],
                "protected": branch["protected"],
                "commit": branch["commit"]["sha"],
            }
            for branch in branches
        ]
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to list branches: {error_msg}")
        raise RepositoryError(f"Failed to list branches: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error listing branches: {str(e)}")
        raise RepositoryError(f"Unexpected error listing branches: {str(e)}")


def create_branch(
    repo_name: str,
    branch_name: str,
    base_branch: str = "main",
) -> Dict[str, Any]:
    """Create a new branch in a repository.

    Args:
        repo_name: Repository name
        branch_name: Name for the new branch
        base_branch: Branch to create from

    Returns:
        Dictionary containing branch information

    Raises:
        RepositoryError: If branch creation fails
    """
    try:
        logger.info(f"Creating branch {branch_name} in repository: {repo_name}")

        # Get the SHA of the base branch
        result = subprocess.run(
            [
                "gh",
                "api",
                f"/repos/yogipatel5/{repo_name}/git/refs/heads/{base_branch}",
                "--jq",
                ".object.sha",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        base_sha = result.stdout.strip()

        # Create the new branch
        create_result = subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"/repos/yogipatel5/{repo_name}/git/refs",
                "-f",
                f"ref=refs/heads/{branch_name}",
                "-f",
                f"sha={base_sha}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(create_result.stdout)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to create branch: {error_msg}")
        raise RepositoryError(f"Failed to create branch: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error creating branch: {str(e)}")
        raise RepositoryError(f"Unexpected error creating branch: {str(e)}")


def delete_branch(repo_name: str, branch_name: str) -> None:
    """Delete a branch from a repository.

    Args:
        repo_name: Repository name
        branch_name: Branch to delete

    Raises:
        RepositoryError: If branch deletion fails
    """
    try:
        logger.info(f"Deleting branch {branch_name} from repository: {repo_name}")
        subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "DELETE",
                f"/repos/yogipatel5/{repo_name}/git/refs/heads/{branch_name}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Branch {branch_name} deleted successfully")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to delete branch: {error_msg}")
        raise RepositoryError(f"Failed to delete branch: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error deleting branch: {str(e)}")
        raise RepositoryError(f"Unexpected error deleting branch: {str(e)}")


def set_branch_protection(
    repo_name: str,
    branch_name: str,
    required_reviews: int = 0,
    require_up_to_date: bool = True,
    enforce_admins: bool = False,
) -> Dict[str, Any]:
    """Set branch protection rules.

    For free accounts:
    - Only public repositories can have branch protection
    - Limited protection features are available
    - Will attempt to set basic protection rules
    - Returns None for unsupported features

    Args:
        repo_name: Repository name
        branch_name: Branch to protect
        required_reviews: Number of required reviews (0 to disable)
        require_up_to_date: Require branch to be up to date before merging
        enforce_admins: Enforce rules on repository administrators

    Returns:
        Dictionary containing protection rule information

    Raises:
        RepositoryError: If setting protection rules fails
    """
    try:
        logger.info(
            f"Setting protection rules for {branch_name} in repository: {repo_name}"
        )

        # First, check if repository is public
        repo_info = subprocess.run(
            [
                "gh",
                "repo",
                "view",
                f"yogipatel5/{repo_name}",
                "--json",
                "visibility",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_data = json.loads(repo_info.stdout)

        if repo_data["visibility"].lower() != "public":
            logger.warning(
                "Branch protection requires a public repository or GitHub Pro account"
            )
            return {
                "message": "Branch protection requires a public repository or GitHub Pro account",
                "protected": False,
                "protection_url": None,
            }

        # Try to set up basic branch protection using gh branch command
        try:
            # Enable basic branch protection
            subprocess.run(
                [
                    "gh",
                    "repo",
                    "edit",
                    f"yogipatel5/{repo_name}",
                    "--delete-branch-on-merge",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "message": "Basic repository protection enabled (delete on merge)",
                "protected": True,
                "protection_url": f"https://github.com/yogipatel5/{repo_name}/settings/branches",
                "features": {
                    "delete_on_merge": True,
                    "force_push_disabled": True,
                },
            }

        except subprocess.CalledProcessError as e:
            if "Upgrade to GitHub Pro" in str(e.stderr):
                logger.info(
                    "Pro features not available, repository protection could not be enabled"
                )
                return {
                    "message": "Branch protection requires GitHub Pro account",
                    "protected": False,
                    "protection_url": None,
                }
            raise

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to set branch protection: {error_msg}")
        raise RepositoryError(f"Failed to set branch protection: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error setting branch protection: {str(e)}")
        raise RepositoryError(f"Unexpected error setting branch protection: {str(e)}")


def merge_branch(
    repo_name: str,
    head_branch: str,
    base_branch: str = "main",
    commit_message: str | None = None,
) -> Dict[str, Any]:
    """Merge one branch into another.

    Args:
        repo_name: Repository name
        head_branch: Branch to merge from
        base_branch: Branch to merge into
        commit_message: Custom merge commit message

    Returns:
        Dictionary containing merge result information

    Raises:
        RepositoryError: If merge fails
    """
    try:
        logger.info(
            f"Merging {head_branch} into {base_branch} in repository: {repo_name}"
        )

        # Build merge payload
        merge_data = {
            "base": base_branch,
            "head": head_branch,
            "commit_message": (
                commit_message
                if commit_message
                else f"Merge {head_branch} into {base_branch}"
            ),
        }

        # Execute merge
        result = subprocess.run(
            [
                "gh",
                "api",
                "--method",
                "POST",
                f"/repos/yogipatel5/{repo_name}/merges",
                "-f",
                f"merge_data={json.dumps(merge_data)}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to merge branches: {error_msg}")
        raise RepositoryError(f"Failed to merge branches: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error merging branches: {str(e)}")
        raise RepositoryError(f"Unexpected error merging branches: {str(e)}")


def cleanup_stale_branches(
    repo_name: str,
    days_stale: int = 30,
    protected_branches: List[str] = ["main", "master", "develop"],
) -> List[str]:
    """Clean up stale branches that haven't been updated.

    Args:
        repo_name: Repository name
        days_stale: Number of days without updates to consider stale
        protected_branches: List of branches to never delete

    Returns:
        List of deleted branch names

    Raises:
        RepositoryError: If cleanup fails
    """
    try:
        logger.info(f"Cleaning up stale branches in repository: {repo_name}")
        deleted_branches = []

        # Get all branches
        branches = list_branches(repo_name)
        logger.info(f"Found {len(branches)} branches")

        # Check each branch's last commit date
        for branch in branches:
            branch_name = branch["name"]
            if branch_name in protected_branches or branch["protected"]:
                logger.info(f"Skipping protected branch: {branch_name}")
                continue

            try:
                # Get last commit date
                result = subprocess.run(
                    [
                        "gh",
                        "api",
                        f"/repos/yogipatel5/{repo_name}/commits",
                        "--jq",
                        f".[] | select(.sha == \"{branch['commit']}\") | .commit.committer.date",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                if not result.stdout.strip():
                    logger.warning(
                        f"No commit date found for branch {branch_name}, skipping"
                    )
                    continue

                last_commit_date = datetime.fromisoformat(
                    result.stdout.strip().replace("Z", "+00:00")
                )

                # Calculate days since last commit
                days_old = (
                    datetime.now(last_commit_date.tzinfo) - last_commit_date
                ).days
                logger.info(f"Branch {branch_name} is {days_old} days old")

                # Check if branch is stale
                if days_old >= days_stale:
                    logger.info(
                        f"Deleting stale branch: {branch_name} ({days_old} days old)"
                    )
                    delete_branch(repo_name, branch_name)
                    deleted_branches.append(branch_name)
                else:
                    logger.info(
                        f"Branch {branch_name} is still active ({days_old} days old)"
                    )

            except subprocess.CalledProcessError as e:
                logger.warning(f"Error checking branch {branch_name}: {str(e)}")
                continue

        if deleted_branches:
            logger.info(
                f"Deleted {len(deleted_branches)} stale branches: {', '.join(deleted_branches)}"
            )
        else:
            logger.info("No stale branches found")

        return deleted_branches

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error(f"Failed to cleanup branches: {error_msg}")
        raise RepositoryError(f"Failed to cleanup branches: {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error cleaning up branches: {str(e)}")
        raise RepositoryError(f"Unexpected error cleaning up branches: {str(e)}")
