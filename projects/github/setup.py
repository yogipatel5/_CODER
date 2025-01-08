"""Setup script for GitHub repository management."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from .service import GitError, GitService


class ConfigExecutionError(Exception):
    """Exception raised for errors during configuration execution."""

    pass


def execute_config(config_path: str) -> None:
    """Execute repository configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Raises:
        ConfigExecutionError: If configuration execution fails
    """
    # Store original working directory
    original_dir = os.getcwd()
    project_path = None
    repo_created = False
    repo_name = None

    try:
        # Load configuration
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Get absolute project path
        project_path = os.path.abspath(os.path.expanduser(config["path"]))
        repo_name = config["git"]["remote"].get("name", config.get("project_name"))

        print(f"Setting up project at: {project_path}")

        # Create project directory
        os.makedirs(project_path, exist_ok=True)

        try:
            # Change to project directory for all operations
            os.chdir(project_path)

            # Create project structure
            if "structure" in config:
                _create_project_structure(project_path, config["structure"])

            # Initialize Git repository
            git = GitService(project_path)

            # Initialize Git repository
            if config["git"]["create_local_repo"]:
                print("\nInitializing Git repository...")
                subprocess.run(["git", "init"], check=True)
                subprocess.run(["git", "checkout", "-b", "main"], check=True)

            # Create initial Python file if it doesn't exist
            if not os.path.exists("src/__init__.py"):
                os.makedirs("src", exist_ok=True)
                with open("src/__init__.py", "w") as f:
                    f.write('"""Initial package file."""\n')

            # Set up Git hooks before any commits
            if "hooks" in config["git"]:
                _setup_git_hooks(git, config["git"]["hooks"])

            # Create initial commit
            if config["git"]["create_local_repo"]:
                print("\nCreating initial commit...")
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(
                    ["git", "commit", "-m", config["git"]["commit_message"]], check=True
                )

            # Set up Git LFS if enabled
            if config["git"].get("lfs", {}).get("enabled", False):
                _setup_git_lfs(git, config["git"]["lfs"])

            # Create local branches only if not creating remote repo
            # (if creating remote, branches will be created after remote setup)
            if not config["git"]["create_remote_repo"] and config["git"].get(
                "other_branches"
            ):
                print("\nCreating local branches...")
                for branch in config["git"]["other_branches"]:
                    subprocess.run(["git", "checkout", "-b", branch], check=True)
                    print(f"Created branch '{branch}'")
                # Return to main branch
                subprocess.run(["git", "checkout", "main"], check=True)

            # Create remote repository if requested
            if config["git"]["create_remote_repo"]:
                _create_remote_repo(git, config["git"])
                repo_created = True

                # Push all branches
                print("\nPushing all branches...")
                subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
                for branch in config["git"].get("other_branches", []):
                    subprocess.run(["git", "push", "-u", "origin", branch], check=True)
                    print(f"Pushed branch '{branch}'")

            # Configure branch protection
            if config["git"].get("branch_protection"):
                _configure_branch_protection(config["git"])

            print(f"\nRepository setup completed successfully at {project_path}")

        finally:
            # Always return to original directory
            os.chdir(original_dir)

    except Exception as e:
        # Cleanup on failure
        try:
            if repo_created and repo_name:
                print("\nCleaning up: Deleting remote repository...")
                subprocess.run(
                    ["gh", "repo", "delete", repo_name, "--yes"],
                    check=True,
                    capture_output=True,
                )
                print("Remote repository deleted.")

            if project_path and os.path.exists(project_path):
                print("Cleaning up: Deleting local directory...")
                subprocess.run(["rm", "-rf", project_path], check=True)
                print("Local directory deleted.")

        except subprocess.CalledProcessError as cleanup_error:
            print(f"Warning: Cleanup failed: {cleanup_error}", file=sys.stderr)

        raise ConfigExecutionError(f"Failed to execute configuration: {str(e)}")

    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
        # Cleanup on interrupt
        try:
            if repo_created and repo_name:
                print("\nCleaning up: Deleting remote repository...")
                subprocess.run(
                    ["gh", "repo", "delete", repo_name, "--yes"],
                    check=True,
                    capture_output=True,
                )
                print("Remote repository deleted.")

            if project_path and os.path.exists(project_path):
                print("Cleaning up: Deleting local directory...")
                subprocess.run(["rm", "-rf", project_path], check=True)
                print("Local directory deleted.")

        except subprocess.CalledProcessError as cleanup_error:
            print(f"Warning: Cleanup failed: {cleanup_error}", file=sys.stderr)

        sys.exit(1)


def _configure_branch_protection(git_config: Dict[str, Any]) -> None:
    """Configure branch protection rules."""
    try:
        # Get GitHub username
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            check=True,
        )
        username = result.stdout.strip()
        repo_name = git_config["remote"].get("name", git_config.get("project_name"))

        print("\nConfiguring branch protection rules...")
        for branch, rules in git_config["branch_protection"].items():
            protection_data = {
                "required_status_checks": None,
                "enforce_admins": True,
                "required_pull_request_reviews": (
                    {
                        "required_approving_review_count": rules.get(
                            "required_reviews", 1
                        )
                    }
                    if rules.get("required_reviews")
                    else None
                ),
                "restrictions": None,
                "required_signatures": rules.get("require_signatures", False),
                "required_linear_history": rules.get("require_linear_history", False),
                "allow_force_pushes": rules.get("allow_force_push", False),
                "allow_deletions": False,
            }

            # Convert to JSON string
            protection_json = json.dumps(protection_data)

            # Apply branch protection
            subprocess.run(
                [
                    "gh",
                    "api",
                    f"repos/{username}/{repo_name}/branches/{branch}/protection",
                    "--method",
                    "PUT",
                    "--header",
                    "Accept: application/vnd.github+json",
                    "--header",
                    "X-GitHub-Api-Version: 2022-11-28",
                    "--input",
                    "-",
                ],
                input=protection_json,
                text=True,
                check=True,
            )

            print(f"Branch protection configured for '{branch}'")

    except subprocess.CalledProcessError as e:
        raise ConfigExecutionError(f"Failed to configure branch protection: {str(e)}")


def _create_project_structure(base_path: str, structure: Dict[str, Any]) -> None:
    """Create project directory structure."""
    try:
        # Create directories
        for dir_path in structure.get("directories", []):
            os.makedirs(os.path.join(base_path, dir_path), exist_ok=True)

        # Create files
        for file_path in structure.get("files", []):
            path = os.path.join(base_path, file_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            Path(path).touch()

        print("Project structure created")

    except OSError as e:
        raise ConfigExecutionError(f"Failed to create project structure: {str(e)}")


def _create_remote_repo(git: GitService, git_config: Dict[str, Any]) -> None:
    """Create and configure remote repository.

    Raises:
        ConfigExecutionError: With specific error messages for different failure cases
    """
    try:
        remote_config = git_config["remote"]
        repo_name = remote_config.get("name", git_config.get("project_name"))

        if not repo_name:
            raise ConfigExecutionError(
                "Repository name must be specified in configuration"
            )

        # First check if repository already exists
        result = subprocess.run(
            ["gh", "repo", "view", repo_name], capture_output=True, text=True
        )

        if result.returncode == 0:
            # Repository exists, ask user what to do
            print(f"\nRepository '{repo_name}' already exists.")
            print("Options:")
            print("1. Skip remote repository creation")
            print("2. Update existing repository settings")
            print("3. Delete existing and create new")

            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                print("Skipping remote repository creation...")
                return
            elif choice == "2":
                print("Updating existing repository settings...")
                _update_remote_repo(repo_name, remote_config)
                return
            elif choice == "3":
                print("Deleting existing repository...")
                subprocess.run(["gh", "repo", "delete", repo_name, "--yes"], check=True)

                # Re-initialize Git repository after deletion
                print("Re-initializing Git repository...")
                subprocess.run(["rm", "-rf", ".git"], check=True)
                subprocess.run(["git", "init"], check=True)
                subprocess.run(["git", "checkout", "-b", "main"], check=True)

                # Stage and commit all files
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(
                    ["git", "commit", "-m", git_config["commit_message"]], check=True
                )

                # Create other branches
                if git_config.get("other_branches"):
                    print("\nRecreating local branches...")
                    for branch in git_config["other_branches"]:
                        subprocess.run(["git", "checkout", "-b", branch], check=True)
                        print(f"Recreated branch '{branch}'")
                    # Return to main branch
                    subprocess.run(["git", "checkout", "main"], check=True)
            else:
                raise ConfigExecutionError(
                    "Invalid choice. Aborting remote repository creation."
                )

        # Create remote repository
        try:
            # First create empty repository
            subprocess.run(
                [
                    "gh",
                    "repo",
                    "create",
                    repo_name,
                    (
                        "--private"
                        if remote_config["visibility"] == "private"
                        else "--public"
                    ),
                    "--description",
                    remote_config["description"],
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            print("Remote repository created successfully")

            # Add remote
            subprocess.run(
                [
                    "git",
                    "remote",
                    "add",
                    "origin",
                    (
                        f"https://github.com/"
                        f"{remote_config.get('owner', 'yogipatel5')}/"
                        f"{repo_name}.git"
                    ),
                ],
                check=True,
            )

            # Push to remote
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True)

            print("Code pushed to remote repository")

        except subprocess.CalledProcessError as e:
            if "already exists" in e.stderr:
                raise ConfigExecutionError(
                    f"Repository '{repo_name}' already exists and was not handled "
                    f"in pre-check. Please delete it first or choose a different name."
                )
            elif "could not create" in e.stderr:
                raise ConfigExecutionError(
                    "Failed to create repository. Please check your GitHub permissions "
                    "and organization settings."
                )
            else:
                raise ConfigExecutionError(f"Failed to create repository: {e.stderr}")

        # Configure repository features
        _configure_repo_features(repo_name, remote_config)

    except subprocess.CalledProcessError as e:
        if "could not read" in str(e.stderr):
            raise ConfigExecutionError(
                "Failed to check repository existence. Please verify your GitHub "
                "authentication and permissions."
            )
        raise ConfigExecutionError(f"Repository operation failed: {e.stderr}")


def _update_remote_repo(repo_name: str, remote_config: Dict[str, Any]) -> None:
    """Update existing remote repository settings."""
    try:
        # Update basic settings
        subprocess.run(
            [
                "gh",
                "repo",
                "edit",
                repo_name,
                "--description",
                remote_config["description"],
                "--visibility",
                remote_config["visibility"],
            ],
            check=True,
        )

        # Update features
        _configure_repo_features(repo_name, remote_config)

        print("Repository settings updated successfully")

    except subprocess.CalledProcessError as e:
        raise ConfigExecutionError(f"Failed to update repository settings: {e.stderr}")


def _configure_repo_features(repo_name: str, remote_config: Dict[str, Any]) -> None:
    """Configure repository features."""
    try:
        features = remote_config.get("features", {})
        feature_flags = []

        if features.get("issues"):
            feature_flags.extend(["--enable-issues"])
        if features.get("wiki"):
            feature_flags.extend(["--enable-wiki"])
        if features.get("projects"):
            feature_flags.extend(["--enable-projects"])
        if features.get("discussions"):
            feature_flags.extend(["--enable-discussions"])

        if feature_flags:
            # Get GitHub username
            result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                capture_output=True,
                text=True,
                check=True,
            )
            username = result.stdout.strip()

            # Format full repository name
            full_repo_name = f"{username}/{repo_name}"

            subprocess.run(
                ["gh", "repo", "edit", full_repo_name] + feature_flags, check=True
            )
            print("Repository features configured successfully")

    except subprocess.CalledProcessError as e:
        if e.stderr:
            raise ConfigExecutionError(
                f"Failed to configure repository features: {e.stderr}"
            )
        else:
            raise ConfigExecutionError(
                f"Failed to configure repository features: {str(e)}"
            )


def _setup_git_lfs(git: GitService, lfs_config: Dict[str, Any]) -> None:
    """Set up Git LFS for specified patterns."""
    try:
        # Initialize LFS with force to overwrite hooks
        subprocess.run(["git", "lfs", "install", "--force"], check=True)

        # Track patterns
        for pattern in lfs_config.get("patterns", []):
            subprocess.run(["git", "lfs", "track", pattern], check=True)

        # Ensure .gitattributes exists
        if not os.path.exists(".gitattributes"):
            Path(".gitattributes").touch()

        # Stage and commit .gitattributes
        git.stage_files([".gitattributes"])
        git.commit("Configure Git LFS patterns")

        print("Git LFS configured successfully")

    except (subprocess.CalledProcessError, GitError) as e:
        raise ConfigExecutionError(f"Failed to configure Git LFS: {str(e)}")


def _setup_git_hooks(git: GitService, hooks_config: Dict[str, Any]) -> None:
    """Set up Git hooks."""
    try:
        hooks_dir = Path(git.repo.git_dir) / "hooks"

        for hook_type, commands in hooks_config.items():
            hook_path = hooks_dir / hook_type
            hook_content = r"""#!/bin/sh

            # Get list of staged Python files
            files=$(git diff --cached --name-only --diff-filter=d | grep "\.py$")

            # Exit if no Python files are staged
            if [ -z "$files" ]; then
                exit 0
            fi

            # Create a list of staged Python files
            echo "$files" > /tmp/staged_files.txt

            # Run checks only on staged Python files
            """

            # Add each command with proper arguments
            for cmd in commands:
                if cmd == "black":
                    hook_content += 'echo "Running black..."\n'
                    hook_content += f"{cmd} $(cat /tmp/staged_files.txt) || exit 1\n"
                elif cmd == "ruff":
                    hook_content += 'echo "Running ruff..."\n'
                    hook_content += (
                        f"{cmd} check $(cat /tmp/staged_files.txt) || exit 1\n"
                    )
                elif cmd == "mypy":
                    hook_content += 'echo "Running mypy..."\n'
                    hook_content += f"{cmd} $(cat /tmp/staged_files.txt) || exit 1\n"
                elif cmd == "pytest":
                    hook_content += 'echo "Running pytest..."\n'
                    hook_content += f"{cmd} || exit 1\n"
                else:
                    hook_content += f'echo "Running {cmd}..."\n'
                    hook_content += f"{cmd} || exit 1\n"

            # Cleanup
            hook_content += "\n# Cleanup\nrm -f /tmp/staged_files.txt\n"

            # Write hook file
            hook_path.write_text(hook_content)
            hook_path.chmod(0o755)

            print(
                f"Git hook '{hook_type}' configured with commands: {', '.join(commands)}"  # noqa: E501
            )

        print("Git hooks configured successfully")

    except Exception as e:
        raise ConfigExecutionError(f"Failed to configure Git hooks: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m github_management.config_executor <config.yaml>")
        sys.exit(1)

    try:
        execute_config(sys.argv[1])
    except ConfigExecutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
