"""
Integration tests for worktree_manager.

Tests the full worktree lifecycle: create → init plans → commit → remove.
Uses temporary git repositories for isolation.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    # Create initial commit on main branch
    readme = repo_path / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    # Ensure we're on main branch
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    return repo_path


# =============================================================================
# T071: Full Worktree Lifecycle Integration Test
# =============================================================================


class TestWorktreeLifecycle:
    """Integration tests for full worktree lifecycle."""

    def test_full_lifecycle_create_init_commit_remove(self, temp_git_repo: Path) -> None:
        """Test complete worktree lifecycle: create → init plans → commit → remove."""
        from worktree_manager import OperationStatus, WorktreeService

        service = WorktreeService(temp_git_repo)

        # 1. Create worktree
        worktree = service.create_worktree(123, "test-feature")
        assert worktree.issue_number == 123
        assert worktree.path.exists()
        assert worktree.branch_name == "123-test-feature"

        # 2. Initialize plans
        plans = service.init_plans(123, "Test Feature")
        assert plans.is_complete
        assert (worktree.path / ".plans" / "123" / "specs").is_dir()
        assert (worktree.path / ".plans" / "123" / "plans").is_dir()
        assert (worktree.path / ".plans" / "123" / "reviews").is_dir()
        assert (worktree.path / ".plans" / "123" / "README.md").is_file()

        # 3. Make changes and commit (without push since no remote)
        test_file = worktree.path / "feature.py"
        test_file.write_text("# New feature code\n")

        result = service.commit_and_push(123, "Add feature", push=False)
        assert result.commit_sha is not None
        assert result.nothing_to_commit is False

        # 4. Verify list_worktrees finds it
        worktrees = service.list_worktrees()
        assert len(worktrees) == 1
        assert worktrees[0].issue_number == 123

        # 5. Remove worktree with branch
        removal = service.remove_worktree(123, delete_branch=True, delete_remote_branch=False)
        assert removal.status == OperationStatus.SUCCESS
        assert not worktree.path.exists()

        # 6. Verify worktree is gone
        worktrees = service.list_worktrees()
        assert len(worktrees) == 0

    def test_multiple_worktrees(self, temp_git_repo: Path) -> None:
        """Test managing multiple worktrees simultaneously."""
        from worktree_manager import WorktreeService

        service = WorktreeService(temp_git_repo)

        # Create 3 worktrees
        wt1 = service.create_worktree(100, "feature-one")
        wt2 = service.create_worktree(200, "feature-two")
        wt3 = service.create_worktree(300, "feature-three")

        # All should exist
        assert wt1.path.exists()
        assert wt2.path.exists()
        assert wt3.path.exists()

        # List should show all
        worktrees = service.list_worktrees()
        assert len(worktrees) == 3
        issue_numbers = {wt.issue_number for wt in worktrees}
        assert issue_numbers == {100, 200, 300}

        # Get specific worktree
        found = service.get_worktree(200)
        assert found is not None
        assert found.issue_number == 200
        assert found.feature_name == "feature-two"

        # Clean up
        for issue in [100, 200, 300]:
            service.remove_worktree(issue, delete_branch=True)

        assert len(service.list_worktrees()) == 0


# =============================================================================
# T072: Existing Branch Checkout Integration Test
# =============================================================================


class TestExistingBranchCheckout:
    """Integration tests for checking out existing branches."""

    def test_create_worktree_from_existing_local(self, temp_git_repo: Path) -> None:
        """Test creating worktree from existing local branch."""
        from worktree_manager import WorktreeService

        service = WorktreeService(temp_git_repo)

        # Create a branch manually (simulating existing work)
        subprocess.run(
            ["git", "branch", "456-existing-feature"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Create worktree from existing branch
        worktree = service.create_worktree_from_existing(
            456, "existing-feature", "456-existing-feature"
        )

        assert worktree.issue_number == 456
        assert worktree.path.exists()
        assert worktree.branch_name == "456-existing-feature"

        # Clean up
        service.remove_worktree(456, delete_branch=True)

    def test_idempotent_plans_init(self, temp_git_repo: Path) -> None:
        """Test that init_plans is idempotent."""
        from worktree_manager import WorktreeService

        service = WorktreeService(temp_git_repo)

        # Create worktree
        service.create_worktree(789, "idempotent-test")

        # Init plans twice
        plans1 = service.init_plans(789)
        plans2 = service.init_plans(789)

        # Both should succeed and return same structure
        assert plans1.is_complete
        assert plans2.is_complete
        assert plans1.path == plans2.path

        # Clean up (force because init_plans creates uncommitted files)
        service.remove_worktree(789, delete_branch=True, force=True)


# =============================================================================
# T073: Error Scenario Integration Tests
# =============================================================================


class TestErrorScenarios:
    """Integration tests for error handling."""

    def test_not_a_repository_error(self, tmp_path: Path) -> None:
        """Test error when path is not a git repository."""
        from worktree_manager import NotARepositoryError, WorktreeService

        non_repo = tmp_path / "not-a-repo"
        non_repo.mkdir()

        with pytest.raises(NotARepositoryError):
            WorktreeService(non_repo)

    def test_worktree_exists_error(self, temp_git_repo: Path) -> None:
        """Test error when worktree already exists."""
        from worktree_manager import WorktreeExistsError, WorktreeService

        service = WorktreeService(temp_git_repo)

        # Create first worktree
        service.create_worktree(111, "duplicate-test")

        # Try to create same one again
        with pytest.raises(WorktreeExistsError):
            service.create_worktree(111, "duplicate-test")

        # Clean up
        service.remove_worktree(111, delete_branch=True)

    def test_branch_exists_error(self, temp_git_repo: Path) -> None:
        """Test error when branch already exists."""
        from worktree_manager import BranchExistsError, WorktreeService

        service = WorktreeService(temp_git_repo)

        # Create branch manually
        subprocess.run(
            ["git", "branch", "222-branch-exists"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Try to create worktree with same branch name
        with pytest.raises(BranchExistsError):
            service.create_worktree(222, "branch-exists")

    def test_worktree_not_found_error(self, temp_git_repo: Path) -> None:
        """Test error when worktree doesn't exist."""
        from worktree_manager import WorktreeNotFoundError, WorktreeService

        service = WorktreeService(temp_git_repo)

        with pytest.raises(WorktreeNotFoundError):
            service.init_plans(999)

        with pytest.raises(WorktreeNotFoundError):
            service.commit_and_push(999, "message")

        with pytest.raises(WorktreeNotFoundError):
            service.remove_worktree(999)

    def test_uncommitted_changes_error(self, temp_git_repo: Path) -> None:
        """Test error when removing worktree with uncommitted changes."""
        from worktree_manager import UncommittedChangesError, WorktreeService

        service = WorktreeService(temp_git_repo)

        # Create worktree
        worktree = service.create_worktree(333, "dirty-worktree")

        # Make uncommitted changes
        dirty_file = worktree.path / "dirty.txt"
        dirty_file.write_text("uncommitted content")

        # Try to remove without force
        with pytest.raises(UncommittedChangesError):
            service.remove_worktree(333)

        # Force removal should work
        result = service.remove_worktree(333, force=True, delete_branch=True)
        assert result.status.value == "success"

    def test_main_branch_not_found_error(self, tmp_path: Path) -> None:
        """Test error when main branch doesn't exist."""
        from worktree_manager import MainBranchNotFoundError, WorktreeService

        # Create repo with no main branch
        repo_path = tmp_path / "no-main-repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        # Create commit on a different branch
        (repo_path / "file.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "branch", "-M", "develop"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        service = WorktreeService(repo_path)

        with pytest.raises(MainBranchNotFoundError):
            service.create_worktree(444, "no-main")
