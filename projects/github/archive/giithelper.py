"""Helper functions for GitHub repository management."""

import csv
import json
import subprocess
from typing import List, TypedDict

from ..service import GitError, GitService


class RepoInfo(TypedDict):
    """Type for repository information returned by GitHub CLI."""

    name: str
    url: str
    description: str
    visibility: str


def get_all_repos() -> List[RepoInfo]:
    """Get all repositories from GitHub.

    Returns:
        List of dictionaries containing repository information
    """
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
        return json.loads(result.stdout)  # type: ignore
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return []


def get_repo_branches(repo_path: str) -> List[str]:
    """Get all branches for a repository.

    Args:
        repo_path: Path to the repository

    Returns:
        List of branch names
    """
    try:
        git = GitService(repo_path)
        return git.get_all_branches()
    except GitError as e:
        print(f"Error getting branches: {e}")
        return []


def save_repos_to_csv() -> None:
    """Save repository information to CSV."""
    try:
        repos = get_all_repos()
        if not repos:
            return

        # Write to CSV
        with open("repos.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=repos[0].keys())
            writer.writeheader()
            writer.writerows(repos)

        print("Successfully saved repository information to repos.csv")
    except Exception as e:
        print(f"Error saving to CSV: {e}")


if __name__ == "__main__":
    save_repos_to_csv()
