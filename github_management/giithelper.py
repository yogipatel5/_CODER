#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from datetime import datetime


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


def update_descriptions(csv_file, dry_run=False):
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


def process_deletions(csv_file, dry_run=False):
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


def print_usage():
    print("Usage:")
    print("  Create new CSV:        python giithelper.py")
    print(
        "  Update descriptions:   python giithelper.py --update <csv_file> [--dry-run]"
    )
    print(
        "  Process deletions:     python giithelper.py --delete <csv_file> [--dry-run]"
    )


# Create a function to create a github repo using cli and then create the directory and add .vscode folder with a settings.json from the


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # If no arguments provided, create the CSV
        save_repos_to_csv()
    else:
        # Check for action flag
        if sys.argv[1] not in ["--update", "--delete"]:
            print_usage()
            sys.exit(1)

        action = sys.argv[1]
        if len(sys.argv) < 3:
            print("Error: CSV file required")
            print_usage()
            sys.exit(1)

        csv_file = sys.argv[2]
        dry_run = "--dry-run" in sys.argv

        if action == "--update":
            print(f"Processing description updates from {csv_file}")
            update_descriptions(csv_file, dry_run=dry_run)
        else:  # --delete
            print(f"Processing deletions from {csv_file}")
            process_deletions(csv_file, dry_run=dry_run)
