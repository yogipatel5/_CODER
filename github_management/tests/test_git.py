from github_management.git_service import GitService


def test_errors():
    # Test 1: Try to initialize with non-existent path
    print("\nTest 1: Non-existent path")
    try:
        git = GitService("/nonexistent/path")
    except Exception as e:
        print(f"Error caught: {e}")

    # Test 2: Try operations on non-git repo
    print("\nTest 2: Non-git repository")
    try:
        git = GitService(".")
        git.get_current_branch()
    except Exception as e:
        print(f"Error caught: {e}")

    # Test 3: Try to merge non-existent branch
    print("\nTest 3: Try to merge in non-git repo")
    try:
        git = GitService(".")
        git.merge_branch("nonexistent-branch")
    except Exception as e:
        print(f"Error caught: {e}")


if __name__ == "__main__":
    test_errors()
