"""Tests for git_service module."""

import shutil
import tempfile
import unittest
from pathlib import Path

import pytest

from ..service import GitError, GitService


@pytest.mark.unit
@pytest.mark.git
class TestGitService(unittest.TestCase):
    """Test cases for GitService class."""

    test_dir: str

    def setUp(self) -> None:
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_init_nonexistent_path(self) -> None:
        """Test initialization with non-existent path."""
        with self.assertRaises(GitError) as context:
            GitService("/nonexistent/path")
        self.assertEqual(str(context.exception), "Repository path does not exist")

    def test_init_new_repo(self) -> None:
        """Test initialization of new repository."""
        git = GitService(self.test_dir)
        self.assertIsInstance(git, GitService)  # Verify instance creation
        self.assertTrue((Path(self.test_dir) / ".git").exists())

    def test_stage_and_commit(self) -> None:
        """Test staging and committing files."""
        git = GitService(self.test_dir)

        # Create a test file
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test content")

        # Stage and commit
        git.stage_files()
        commit_hash = git.commit("Initial commit")

        # Verify commit
        self.assertEqual(len(commit_hash), 40)  # SHA-1 hash length
        status = git.get_status()
        self.assertEqual(status["modified"], [])
        self.assertEqual(status["untracked"], [])

    def test_branch_operations(self) -> None:
        """Test branch creation and deletion."""
        git = GitService(self.test_dir)

        # Create initial commit
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test content")
        git.stage_files()
        git.commit("Initial commit")

        # Create main branch first
        git.create_branch("main")

        # Test feature branch creation
        git.create_branch("feature")
        self.assertEqual(git.get_current_branch(), "feature")

        # Switch back to main before deleting feature
        git.create_branch("main")  # This switches to main
        git.delete_branch("feature", force=True)

        # Verify feature branch is gone
        with self.assertRaises(GitError):
            git.delete_branch("feature")

    def test_merge_branch(self) -> None:
        """Test branch merging."""
        git = GitService(self.test_dir)

        # Create initial commit
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test content")
        git.stage_files()
        git.commit("Initial commit")

        # Create and modify feature branch
        git.create_branch("feature")
        test_file.write_text("modified content")
        git.stage_files()
        git.commit("Feature commit")

        # Merge back to main
        git.create_branch("main")
        git.merge_branch("feature")

        # Verify merge
        with open(test_file) as f:
            content = f.read()
        self.assertEqual(content, "modified content")

    def test_invalid_operations(self) -> None:
        """Test invalid operations raise appropriate errors."""
        git = GitService(self.test_dir)

        # Test empty commit message
        with self.assertRaises(GitError) as context:
            git.commit("")
        self.assertEqual(str(context.exception), "Commit message cannot be empty")

        # Test invalid author format
        with self.assertRaises(GitError) as context:
            git.commit("Test commit", author="Invalid Format")
        self.assertEqual(
            str(context.exception), "Invalid author format. Expected 'Name <email>'"
        )


if __name__ == "__main__":
    unittest.main()
