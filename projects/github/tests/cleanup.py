import os
import shutil

from ..service import GitService


def cleanup_directories() -> None:
    """Clean up test directories and their Git repositories."""
    directories = [
        "/Users/yp/Code/_CODER/test_repo",
        "/Users/yp/Code/_CODER/test_project",
    ]

    for directory in directories:
        # Try to remove remote first if it exists
        try:
            git = GitService(directory)
            # Get remote URL before deletion
            remote = git.repo.remote()
            remote_url = remote.url
            print(f"Found remote repository for {directory}: {remote_url}")

            # Remove remote using git command
            git.repo.git.remote("remove", "origin")
            print(f"Removed remote repository reference for {directory}")

        except Exception as e:
            print(f"Note for {directory}: {e}")

        # Remove local directory
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                print(f"Removed directory at {directory}")
            else:
                print(f"Directory {directory} does not exist")
        except Exception as e:
            print(f"Error removing directory {directory}: {e}")


if __name__ == "__main__":
    cleanup_directories()
