"""
Git service for handling Git operations using GitPython.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, cast

from git.exc import GitCommandError
from git.objects import Commit
from git.repo import Repo
from git.util import Actor

logger = logging.getLogger(__name__)


class GitError(Exception):
    """Exception raised for errors during Git operations."""

    def __init__(self, message: str):
        # Extract the most relevant part of git error messages
        # Common patterns in git error messages
        patterns = [
            r"fatal: (.+)",  # Git fatal errors
            r"error: (.+)",  # Git errors
            r"failed to (.+)",  # General failure messages
            r"could not (.+)",  # General failure messages
            r"refusing to (.+)",  # Git refusing to do something
            r"^([^:]+)$",  # Fallback: take first line without colon
        ]

        # Try to find a match with each pattern
        cleaned_message = message
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE | re.MULTILINE)
            if match:
                cleaned_message = match.group(1).strip()
                break

        # Ensure the message isn't too long
        if len(cleaned_message) > 100:
            cleaned_message = cleaned_message[:97] + "..."

        super().__init__(cleaned_message)

        # Store full message for logging
        self.full_message = message
        logger.debug(f"Full Git error: {message}")


class GitService:
    """Service class for handling Git operations."""

    def __init__(self, repo_path: Union[str, Path]):
        """Initialize GitService with repository path.

        Args:
            repo_path: Path to Git repository

        Raises:
            GitError: If repository initialization fails
        """
        try:
            self.repo_path = Path(repo_path)
            if not self.repo_path.exists():
                raise GitError("Repository path does not exist")

            if not (self.repo_path / ".git").exists():
                self.repo = Repo.init(str(self.repo_path))
                logger.info(f"Initialized new Git repository at {repo_path}")
            else:
                self.repo = Repo(str(self.repo_path))
                logger.info(f"Opened existing Git repository at {repo_path}")

        except GitCommandError as e:
            raise GitError(str(e))

    def stage_files(self, paths: Optional[List[str]] = None) -> None:
        """Stage files for commit.

        Args:
            paths: List of file paths to stage, or None to stage all changes

        Raises:
            GitError: If staging fails
        """
        try:
            if paths:
                self.repo.index.add(paths)
            else:
                # Stage all changes including untracked files
                self.repo.git.add(A=True)
            logger.info("Files staged successfully")

        except GitCommandError as e:
            raise GitError(str(e))

    def commit(self, message: str, author: Optional[str] = None) -> str:
        """Create a commit with staged changes.

        Args:
            message: Commit message
            author: Optional author string (format: "Name <email>")

        Returns:
            The commit hash

        Raises:
            GitError: If commit fails
        """
        try:
            if not message:
                raise GitError("Commit message cannot be empty")

            # Create commit
            if author:
                # Parse author string into Actor object
                name, email = author.split("<")
                name = name.strip()
                email = email.rstrip(">").strip()
                author_actor = Actor(name, email)
                commit = self.repo.index.commit(message, author=author_actor)
            else:
                commit = self.repo.index.commit(message)

            logger.info(f"Created commit {commit.hexsha[:8]}")
            return commit.hexsha

        except GitCommandError as e:
            raise GitError(str(e))
        except ValueError:
            raise GitError("Invalid author format. Expected 'Name <email>'")

    def get_current_branch(self) -> str:
        """Get name of current branch.

        Returns:
            Name of current branch

        Raises:
            GitError: If getting branch name fails
        """
        try:
            return self.repo.active_branch.name
        except GitCommandError as e:
            raise GitError(str(e))

    def create_branch(self, name: str, start_point: str = "HEAD") -> None:
        """Create a new branch.

        Args:
            name: Name of new branch
            start_point: Starting point for branch (commit/branch name)

        Raises:
            GitError: If branch creation fails
        """
        try:
            new_branch = self.repo.create_head(name, start_point)
            new_branch.checkout()
            logger.info(f"Created and checked out branch: {name}")

        except GitCommandError as e:
            raise GitError(str(e))

    def delete_branch(self, name: str, force: bool = False) -> None:
        """Delete a branch.

        Args:
            name: Name of branch to delete
            force: Whether to force delete unmerged branch

        Raises:
            GitError: If branch deletion fails
        """
        try:
            self.repo.delete_head(name, force=force)
            logger.info(f"Deleted branch: {name}")

        except GitCommandError as e:
            raise GitError(str(e))

    def merge_branch(self, branch: str, message: Optional[str] = None) -> None:
        """Merge a branch into current branch.

        Args:
            branch: Name of branch to merge
            message: Optional merge commit message

        Raises:
            GitError: If merge fails
        """
        try:
            # Get branch reference
            branch_ref = self.repo.heads[branch]

            # Perform merge
            current = self.repo.active_branch
            current.checkout()

            base = self.repo.merge_base(current, branch_ref)
            self.repo.index.merge_tree(branch_ref, base=base)

            if message is None:
                message = f"Merge branch '{branch}' into {current.name}"

            # Cast parent commits to List[Commit] to satisfy type checker
            parents = cast(List[Commit], [current.commit, branch_ref.commit])
            self.repo.index.commit(message, parent_commits=parents)
            logger.info(f"Merged branch {branch} into {current.name}")

        except GitCommandError as e:
            raise GitError(str(e))

    def push(self, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> None:
        """Push commits to remote repository.

        Args:
            remote: Name of remote
            branch: Branch to push (None for current branch)
            force: Whether to force push

        Raises:
            GitError: If push fails
        """
        try:
            if branch is None:
                branch = self.get_current_branch()

            remote_obj = self.repo.remote(remote)
            ref_spec = f"refs/heads/{branch}:refs/heads/{branch}"

            remote_obj.push(refspec=ref_spec, force=force)
            logger.info(f"Pushed {branch} to {remote}")

        except GitCommandError as e:
            raise GitError(str(e))

    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> None:
        """Pull changes from remote repository.

        Args:
            remote: Name of remote
            branch: Branch to pull (None for current branch)

        Raises:
            GitError: If pull fails
        """
        try:
            if branch is None:
                branch = self.get_current_branch()

            remote_obj = self.repo.remote(remote)
            remote_obj.pull(refspec=branch)
            logger.info(f"Pulled changes from {remote}/{branch}")

        except GitCommandError as e:
            raise GitError(str(e))

    def get_status(self) -> Dict[str, List[str]]:
        """Get repository status.

        Returns:
            Dictionary with modified, added, deleted, and untracked files

        Raises:
            GitError: If getting status fails
        """
        try:
            status: Dict[str, List[str]] = {
                "modified": [],
                "added": [],
                "deleted": [],
                "untracked": [],
            }

            # Get status
            for item in self.repo.index.diff(None):
                if item.a_path is None:
                    continue

                if item.change_type == "M":
                    status["modified"].append(item.a_path)
                elif item.change_type == "A":
                    status["added"].append(item.a_path)
                elif item.change_type == "D":
                    status["deleted"].append(item.a_path)

            # Get untracked files
            status["untracked"] = self.repo.untracked_files

            return status

        except GitCommandError as e:
            raise GitError(str(e))

    def get_all_branches(self) -> List[str]:
        """Get all branches in the repository.

        Returns:
            List of branch names

        Raises:
            GitError: If getting branches fails
        """
        try:
            # Get both local and remote branches
            branches = []

            # Add local branches
            for branch in self.repo.heads:
                branches.append(branch.name)

            # Add remote branches
            for ref in self.repo.remote().refs:
                # Convert remote refs (e.g. origin/main) to branch names (main)
                branch_name = ref.name.split("/", 1)[1] if "/" in ref.name else ref.name
                if branch_name not in branches:
                    branches.append(branch_name)

            return sorted(branches)
        except GitCommandError as e:
            raise GitError(str(e))
        except AttributeError:
            # Handle case where repository has no remotes
            return sorted([branch.name for branch in self.repo.heads])
