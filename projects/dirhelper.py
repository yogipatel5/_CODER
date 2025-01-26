#!/usr/bin/env python3
import csv
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# trunk-ignore(bandit/B404)
from subprocess import CalledProcessError, run
from typing import Any, Dict, List, Optional, Tuple, Union


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


def create_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def delete_directory(path: str) -> None:
    """Delete directory if it exists."""
    if os.path.exists(path):
        shutil.rmtree(path)


def initialize_git_repo(path: str, branch: Optional[str] = "main") -> None:
    """Initialize a git repository in the given directory."""
    # Remove .git directory if it exists
    git_dir = os.path.join(path, ".git")
    if os.path.exists(git_dir):
        delete_directory(git_dir)

    # Initialize git repo
    safe_run_command(["git", "init"], cwd=path)
    safe_run_command(["git", "checkout", "-b", branch], cwd=path)


def is_git_repo(path: str) -> bool:
    """Check if the directory is a git repository"""
    git_dir = os.path.join(path, ".git")
    return os.path.exists(git_dir)


def get_git_info(path: str) -> Dict[str, Union[str, bool]]:
    """Get git repository information"""
    try:
        # Get remote URL
        result = safe_run_command(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        remote_url = result.stdout.strip()
    except CalledProcessError:
        remote_url = "No remote URL"

    try:
        # Get current branch
        result = safe_run_command(
            ["git", "branch", "--show-current"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        branch = result.stdout.strip()
    except CalledProcessError:
        branch = "Unknown"

    try:
        # Check if there are uncommitted changes
        result = safe_run_command(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        has_changes = bool(result.stdout.strip())
    except CalledProcessError:
        has_changes = False

    return {"remote_url": remote_url, "branch": branch, "has_changes": has_changes}


def get_organization_recommendation(repo_info: Dict[str, Any]) -> Tuple[str, str]:
    """Get recommendation for organizing a directory"""
    name = repo_info["name"].lower()
    remote_url = repo_info["remote_url"].lower()

    # Hidden directories and cache
    if name.startswith("."):
        return "keep", ""

    # Known GitHub repositories
    if "github.com/yogipatel5" in remote_url:
        return "keep", "Active GitHub repository"

    # AI/ML Projects
    if any(x in name for x in ["ai", "gpt", "claude", "devin", "superagi", "crewai", "langflow"]):
        return "move ~/Code/AI_ML/", "AI/ML project"

    # Company Projects
    if any(x in name for x in ["flavorgod", "shipbreeze", "wehandleship"]):
        return "move ~/Code/Company/", "Company project"

    # Development Tools
    if any(x in name for x in ["tools", "docker", "config", "mac-scripts", "proxmox"]):
        return "move ~/Code/DevTools/", "Development tool"

    # Integrations
    if any(x in name for x in ["gapps", "gsheet", "notion", "ebay"]):
        return "move ~/Code/Integrations/", "Integration project"

    # Templates/Boilerplates
    if any(x in name for x in ["template", "boilerplate", "cookiecutter", "pegasus"]):
        return "move ~/Code/Templates/", "Template/Boilerplate"

    # Archives
    if any(x in name for x in ["archive", "old", "backup"]):
        return "move ~/Code/_Archive/", "Archived project"

    # Default for unknown
    return "move ~/Code/Misc/", "Uncategorized project"


def scan_directory() -> List[Dict[str, Any]]:
    """Scan ~/Code directory for git repositories"""
    code_dir = os.path.expanduser("~/Code")
    repos = []

    for item in os.listdir(code_dir):
        full_path = os.path.join(code_dir, item)
        if os.path.isdir(full_path):
            repo_info = {
                "name": item,
                "path": full_path,
                "is_git": is_git_repo(full_path),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S"),
                "size_mb": sum(f.stat().st_size for f in Path(full_path).rglob("*") if f.is_file())
                / (1024 * 1024),  # Convert to MB
                "remote_url": "",
                "branch": "",
                "has_changes": False,
                "action": "keep",  # Default action
                "notes": "",  # Add notes field
            }

            if repo_info["is_git"]:
                git_info = get_git_info(full_path)
                repo_info.update(git_info)

            # Get organization recommendation
            action, notes = get_organization_recommendation(repo_info)
            repo_info["action"] = action
            repo_info["notes"] = notes

            repos.append(repo_info)

    return repos


def save_to_csv() -> str:
    """Save directory information to CSV"""
    repos = scan_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"code_dirs_{timestamp}.csv"

    with open(filename, "w", newline="") as csvfile:
        fieldnames = [
            "name",
            "path",
            "is_git",
            "remote_url",
            "branch",
            "has_changes",
            "last_modified",
            "size_mb",
            "action",
            "notes",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for repo in repos:
            writer.writerow(repo)

    print(f"Directory information saved to {filename}")
    print("Actions in CSV:")
    print("  'keep' - keep directory in current location")
    print("  'remove' - delete directory")
    print("  'backup' - create backup before removing")
    print("  'move [path]' - move directory to specified path")
    return filename


def process_actions(csv_file: str, dry_run: bool = False) -> None:
    """Process the actions from the CSV file"""
    backup_dir = os.path.expanduser("~/Code_Backups")
    if not dry_run and not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    with open(csv_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            action = row["action"].lower().strip()
            path = row["path"]
            name = row["name"]

            if action.startswith("move "):
                target_dir = os.path.expanduser(action[5:])
                if dry_run:
                    print(f"[DRY RUN] Would move {path} to {target_dir}")
                else:
                    try:
                        if not os.path.exists(target_dir):
                            os.makedirs(target_dir)
                        target_path = os.path.join(target_dir, name)
                        print(f"Moving {path} to {target_path}")
                        safe_run_command(["mv", path, target_path])
                        print(f"Successfully moved {path}")
                    except (CalledProcessError, OSError) as e:
                        print(f"Error moving directory {path}: {e}")

            elif action == "remove":
                if dry_run:
                    print(f"[DRY RUN] Would delete directory: {path}")
                else:
                    try:
                        print(f"Deleting directory: {path}")
                        safe_run_command(["rm", "-rf", path])
                        print(f"Successfully deleted {path}")
                    except (CalledProcessError, OSError) as e:
                        print(f"Error deleting directory {path}: {e}")

            elif action == "backup":
                backup_path = os.path.join(backup_dir, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                if dry_run:
                    print(f"[DRY RUN] Would backup {path} to {backup_path}")
                else:
                    try:
                        print(f"Creating backup of {path}")
                        safe_run_command(["cp", "-r", path, backup_path])
                        print(f"Successfully backed up to {backup_path}")
                        print(f"Deleting original directory: {path}")
                        safe_run_command(["rm", "-rf", path])
                        print(f"Successfully deleted {path}")
                    except (CalledProcessError, OSError) as e:
                        print(f"Error processing backup/delete for {path}: {e}")


def print_usage() -> None:
    """Print usage instructions"""
    print("Usage:")
    print("  Create new CSV:        python dirhelper.py")
    print("  Process actions:       python dirhelper.py --process <csv_file> [--dry-run]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # If no arguments provided, create the CSV
        save_to_csv()
    else:
        # Check for action flag
        if sys.argv[1] != "--process":
            print_usage()
            sys.exit(1)

        if len(sys.argv) < 3:
            print("Error: CSV file required")
            print_usage()
            sys.exit(1)

        csv_file = sys.argv[2]
        dry_run = "--dry-run" in sys.argv

        print(f"Processing actions from {csv_file}")
        process_actions(csv_file, dry_run=dry_run)
