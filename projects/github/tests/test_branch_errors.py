import pytest

from ..service import GitService


@pytest.mark.unit
@pytest.mark.git
def test_branch_errors() -> None:
    """Test branch error handling."""
    git = GitService(".")

    # Test 1: Try to create branch with invalid name
    print("\nTest 1: Create branch with invalid name")
    try:
        git.create_branch("invalid/branch/name...")
    except Exception as e:
        print(f"Error caught: {e}")

    # Test 2: Try to delete non-existent branch
    print("\nTest 2: Delete non-existent branch")
    try:
        git.delete_branch("nonexistent-branch")
    except Exception as e:
        print(f"Error caught: {e}")

    # Test 3: Try to merge non-existent branch
    print("\nTest 3: Merge non-existent branch")
    try:
        git.merge_branch("nonexistent-branch")
    except Exception as e:
        print(f"Error caught: {e}")

    # Test 4: Try to delete current branch
    print("\nTest 4: Delete current branch")
    try:
        current = git.get_current_branch()
        git.delete_branch(current)
    except Exception as e:
        print(f"Error caught: {e}")


if __name__ == "__main__":
    test_branch_errors()
