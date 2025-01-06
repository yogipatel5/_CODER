#!/usr/bin/env python3

"""
GitHub repository management tool.
"""

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime

from .git_service import GitError, GitService
from .services import (
    PushError,
    PushOptions,
    PushProtection,
    get_push_protection,
    schedule_push,
    set_push_protection,
)


def get_all_repos():
    """Get all GitHub repositories for the authenticated user"""
    try:
        result = subprocess.run(
            [
                "gh",
                "repo",
                "list",
                "--json",
                "name,url,description,visibility",
                "--limit",
                "1000",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching repositories: {e}")
        sys.exit(1)


def save_repos_to_csv():
    """Save all repositories to a CSV file with an action column"""
    repos = get_all_repos()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"github_repos_{timestamp}.csv"

    with open(filename, "w", newline="") as csvfile:
        fieldnames = ["name", "url", "description", "visibility", "action"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for repo in repos:
            repo["action"] = "keep"  # Default action
            writer.writerow(repo)

    print(f"Repository list saved to {filename}")
    print("Edit the 'action' column with:")
    print("  'keep' - keep repository as is")
    print("  'remove' - delete repository")
    print("  'update' - update repository description")
    return filename


def update_descriptions(csv_file: str, dry_run: bool = False) -> list[str]:
    """Update GitHub repository descriptions based on CSV file"""
    updated_repos = []
    with open(csv_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Only process repos marked for description update
            if row["action"].lower().strip() == "update" and row["description"]:
                repo_name = row["name"]
                full_repo_name = f"yogipatel5/{repo_name}"  # Add owner prefix
                description = row["description"]
                if dry_run:
                    print(
                        f"[DRY RUN] Would update description for {full_repo_name}: {description}"
                    )
                    updated_repos.append(repo_name)
                else:
                    try:
                        print(f"Updating description for {full_repo_name}")
                        subprocess.run(
                            [
                                "gh",
                                "repo",
                                "edit",
                                full_repo_name,
                                "--description",
                                description,
                            ],
                            check=True,
                        )
                        print(f"Successfully updated description for {full_repo_name}")
                        updated_repos.append(repo_name)
                    except subprocess.CalledProcessError as e:
                        print(f"Error updating repository {full_repo_name}: {e}")

    return updated_repos


def process_deletions(csv_file: str, dry_run: bool = False) -> list[str]:
    """Process the CSV file and delete repositories marked for removal"""
    removed_repos = []
    with open(csv_file, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["action"].lower().strip() == "remove":
                repo_name = row["name"]
                full_repo_name = f"yogipatel5/{repo_name}"  # Add owner prefix
                if dry_run:
                    print(f"[DRY RUN] Would delete repository: {full_repo_name}")
                    removed_repos.append(repo_name)
                else:
                    try:
                        print(f"Deleting repository: {full_repo_name}")
                        subprocess.run(
                            ["gh", "repo", "delete", full_repo_name, "--yes"],
                            check=True,
                        )
                        print(f"Successfully deleted {full_repo_name}")
                        removed_repos.append(repo_name)
                    except subprocess.CalledProcessError as e:
                        print(f"Error deleting repository {full_repo_name}: {e}")

    return removed_repos


def print_usage() -> None:
    """Print usage information."""
    print("Usage:")
    print("  Create new CSV:        python giithelper.py")
    print(
        "  Update descriptions:   python giithelper.py --update <csv_file> [--dry-run]"
    )
    print(
        "  Process deletions:     python giithelper.py --delete <csv_file> [--dry-run]"
    )


def push_repo(args: argparse.Namespace) -> None:
    """Push changes to remote repository."""
    try:
        git_service = GitService(".")

        options = PushOptions(
            remote=args.remote,
            branch=args.branch,
            force=args.force,
            force_with_lease=args.force_with_lease,
            tags=args.tags,
            set_upstream=args.set_upstream,
            protection_level=PushProtection(args.protection),
            scheduled_time=(
                datetime.fromisoformat(args.schedule) if args.schedule else None
            ),
        )

        if args.schedule:
            schedule_push(".", options)
            print(f"Push scheduled for {args.schedule}")
        else:
            git_service.push(
                remote=options.remote, branch=options.branch, force=options.force
            )
            print("Changes pushed successfully")

    except (GitError, PushError) as e:
        print(f"Error pushing changes: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Invalid argument: {e}")
        sys.exit(1)


def get_protection(args: argparse.Namespace) -> None:
    """Get push protection level for repository."""
    try:
        protection = get_push_protection(".")
        print(f"Current push protection level: {protection.value}")
    except PushError as e:
        print(f"Error getting push protection: {e}")
        sys.exit(1)


def set_protection(args: argparse.Namespace) -> None:
    """Set push protection level for repository."""
    try:
        set_push_protection(".", PushProtection(args.level))
        print(f"Push protection level set to: {args.level}")
    except PushError as e:
        print(f"Error setting push protection: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Invalid protection level: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub repository management tool")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Push command
    push_parser = subparsers.add_parser("push", help="Push changes to remote")
    push_parser.add_argument("--remote", default="origin", help="Remote name")
    push_parser.add_argument("--branch", default="main", help="Branch name")
    push_parser.add_argument("--force", action="store_true", help="Force push")
    push_parser.add_argument(
        "--force-with-lease", action="store_true", help="Force push with lease"
    )
    push_parser.add_argument("--tags", action="store_true", help="Push tags")
    push_parser.add_argument(
        "--set-upstream", action="store_true", help="Set upstream branch"
    )
    push_parser.add_argument(
        "--protection",
        choices=[p.value for p in PushProtection],
        default=PushProtection.BASIC.value,
        help="Push protection level",
    )
    push_parser.add_argument(
        "--schedule",
        help="Schedule push for later (ISO format datetime)",
    )

    # Push protection commands
    protection_parser = subparsers.add_parser(
        "protection", help="Manage push protection"
    )
    protection_subparsers = protection_parser.add_subparsers(dest="protection_command")

    get_protection_parser = protection_subparsers.add_parser(
        "get", help="Get push protection level"
    )
    set_protection_parser = protection_subparsers.add_parser(
        "set", help="Set push protection level"
    )
    set_protection_parser.add_argument(
        "level",
        choices=[p.value for p in PushProtection],
        help="Protection level to set",
    )

    args = parser.parse_args()

    if args.command == "push":
        push_repo(args)
    elif args.command == "protection":
        if args.protection_command == "get":
            get_protection(args)
        elif args.protection_command == "set":
            set_protection(args)
        else:
            protection_parser.print_help()
    else:
        parser.print_help()
