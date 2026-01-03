"""
Contract tests for WorktreeService.

Tests the service interface contracts as defined in contracts/worktree-service.md.
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
# US1: create_worktree() and create_worktree_from_existing() contracts
# =============================================================================


class TestCreateWorktreeContract:
    """
    Contract tests for create_worktree().

    Contract: Given issue_number and feature_name, creates branch from main
    and worktree in sibling directory.
    """

    def test_create_worktree_creates_branch_from_main(self, temp_git_repo: Path) -> None:
        """create_worktree should create branch from main."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        result = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Branch should exist
        branch_check = subprocess.run(
            ["git", "show-ref", "--verify", "refs/heads/123-add-auth"],
            cwd=temp_git_repo,
            capture_output=True,
        )
        assert branch_check.returncode == 0
        assert result.branch_name == "123-add-auth"

    def test_create_worktree_creates_sibling_directory(self, temp_git_repo: Path) -> None:
        """create_worktree should create worktree in sibling directory."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        result = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Worktree should be in sibling directory
        expected_path = temp_git_repo.parent / f"{temp_git_repo.name}-123-add-auth"
        assert result.path == expected_path
        assert expected_path.exists()
        assert (expected_path / ".git").exists()

    def test_create_worktree_returns_worktree_model(self, temp_git_repo: Path) -> None:
        """create_worktree should return Worktree model with correct data."""
        from worktree_manager.models import Worktree
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        result = service.create_worktree(issue_number=123, feature_name="add-auth")

        assert isinstance(result, Worktree)
        assert result.issue_number == 123
        assert result.feature_name == "add-auth"
        assert result.branch_name == "123-add-auth"
        assert result.main_repo_path == temp_git_repo
        assert result.is_clean is True

    def test_create_worktree_directory_exists_raises_error(self, temp_git_repo: Path) -> None:
        """create_worktree should raise WorktreeExistsError if directory exists."""
        from worktree_manager.errors import WorktreeExistsError
        from worktree_manager.service import WorktreeService

        # Pre-create the directory
        sibling_path = temp_git_repo.parent / f"{temp_git_repo.name}-123-add-auth"
        sibling_path.mkdir()

        service = WorktreeService(temp_git_repo)
        with pytest.raises(WorktreeExistsError) as exc_info:
            service.create_worktree(issue_number=123, feature_name="add-auth")

        assert "123-add-auth" in str(exc_info.value)

    def test_create_worktree_main_branch_not_found_raises_error(self, tmp_path: Path) -> None:
        """create_worktree should raise MainBranchNotFoundError if no main."""
        from worktree_manager.errors import MainBranchNotFoundError
        from worktree_manager.service import WorktreeService

        # Create repo without main branch
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
        readme = repo_path / "README.md"
        readme.write_text("# Test\n")
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "branch", "-M", "develop"],  # NOT main
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        service = WorktreeService(repo_path)
        with pytest.raises(MainBranchNotFoundError):
            service.create_worktree(issue_number=123, feature_name="add-auth")


class TestCreateWorktreeFromExistingContract:
    """
    Contract tests for create_worktree_from_existing().

    Contract: Given existing remote branch, creates worktree checking out that branch.
    """

    def test_create_worktree_from_existing_checks_out_branch(self, temp_git_repo: Path) -> None:
        """create_worktree_from_existing should checkout existing branch."""
        from worktree_manager.service import WorktreeService

        # Create a branch that would "exist remotely"
        subprocess.run(
            ["git", "checkout", "-b", "123-add-auth"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )
        # Add a commit to this branch
        test_file = temp_git_repo / "feature.txt"
        test_file.write_text("feature content\n")
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Feature commit"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )
        # Go back to main
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        service = WorktreeService(temp_git_repo)
        result = service.create_worktree_from_existing(
            issue_number=123, feature_name="add-auth", branch_name="123-add-auth"
        )

        # Worktree should be created
        expected_path = temp_git_repo.parent / f"{temp_git_repo.name}-123-add-auth"
        assert result.path == expected_path
        assert expected_path.exists()
        # Should have the feature file from that branch
        assert (expected_path / "feature.txt").exists()

    def test_create_worktree_from_existing_returns_worktree(self, temp_git_repo: Path) -> None:
        """create_worktree_from_existing should return Worktree model."""
        from worktree_manager.models import Worktree
        from worktree_manager.service import WorktreeService

        # Create existing branch
        subprocess.run(
            ["git", "checkout", "-b", "456-fix-bug"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        service = WorktreeService(temp_git_repo)
        result = service.create_worktree_from_existing(
            issue_number=456, feature_name="fix-bug", branch_name="456-fix-bug"
        )

        assert isinstance(result, Worktree)
        assert result.issue_number == 456
        assert result.feature_name == "fix-bug"
        assert result.branch_name == "456-fix-bug"

    def test_create_worktree_from_existing_branch_not_found_raises_error(
        self, temp_git_repo: Path
    ) -> None:
        """create_worktree_from_existing should raise BranchNotFoundError."""
        from worktree_manager.errors import BranchNotFoundError
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        with pytest.raises(BranchNotFoundError) as exc_info:
            service.create_worktree_from_existing(
                issue_number=123,
                feature_name="nonexistent",
                branch_name="123-nonexistent",
            )

        assert "123-nonexistent" in str(exc_info.value)


# =============================================================================
# US2: init_plans() and get_plans() contracts
# =============================================================================


class TestInitPlansContract:
    """
    Contract tests for init_plans().

    Contract: Given issue_number, creates .plans/{issue}/ structure.
    """

    def test_init_plans_creates_directory_structure(self, temp_git_repo: Path) -> None:
        """init_plans should create .plans/{issue}/ with subdirectories."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)

        # First create a worktree
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Initialize plans
        service.init_plans(issue_number=123)

        # Verify structure
        plans_path = wt.path / ".plans" / "123"
        assert plans_path.exists()
        assert (plans_path / "specs").is_dir()
        assert (plans_path / "plans").is_dir()
        assert (plans_path / "reviews").is_dir()
        assert (plans_path / "README.md").is_file()

    def test_init_plans_creates_readme_with_metadata(self, temp_git_repo: Path) -> None:
        """init_plans should create README.md with feature metadata."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=456, feature_name="fix-bug")
        service.init_plans(issue_number=456, feature_title="Fix Login Bug")

        readme_path = wt.path / ".plans" / "456" / "README.md"
        readme_content = readme_path.read_text()

        assert "456" in readme_content
        assert "Fix Login Bug" in readme_content

    def test_init_plans_returns_plans_folder_model(self, temp_git_repo: Path) -> None:
        """init_plans should return PlansFolder model."""
        from worktree_manager.models import PlansFolder
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        service.create_worktree(issue_number=123, feature_name="add-auth")
        result = service.init_plans(issue_number=123)

        assert isinstance(result, PlansFolder)
        assert result.issue_number == 123
        assert result.is_complete is True

    def test_init_plans_is_idempotent(self, temp_git_repo: Path) -> None:
        """init_plans should be idempotent (re-running returns same result)."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # First call
        result1 = service.init_plans(issue_number=123)

        # Add a file to specs to ensure it persists
        (wt.path / ".plans" / "123" / "specs" / "test.md").write_text("test")

        # Second call should not fail and should preserve existing content
        result2 = service.init_plans(issue_number=123)

        assert result1.is_complete is True
        assert result2.is_complete is True
        assert (wt.path / ".plans" / "123" / "specs" / "test.md").exists()


class TestGetPlansContract:
    """
    Contract tests for get_plans().

    Contract: Given issue_number, returns PlansFolder if exists, None otherwise.
    """

    def test_get_plans_returns_plans_folder_if_exists(self, temp_git_repo: Path) -> None:
        """get_plans should return PlansFolder if .plans/{issue}/ exists."""
        from worktree_manager.models import PlansFolder
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        service.create_worktree(issue_number=123, feature_name="add-auth")
        service.init_plans(issue_number=123)

        result = service.get_plans(issue_number=123)

        assert isinstance(result, PlansFolder)
        assert result.issue_number == 123
        assert result.is_complete is True

    def test_get_plans_returns_none_if_not_exists(self, temp_git_repo: Path) -> None:
        """get_plans should return None if .plans/{issue}/ doesn't exist."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        service.create_worktree(issue_number=123, feature_name="add-auth")

        # Don't init plans
        result = service.get_plans(issue_number=123)

        assert result is None

    def test_get_plans_returns_partial_if_incomplete(self, temp_git_repo: Path) -> None:
        """get_plans should return PlansFolder with incomplete status if partial."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Manually create partial structure
        plans_path = wt.path / ".plans" / "123"
        plans_path.mkdir(parents=True)
        (plans_path / "specs").mkdir()
        # Missing: plans/, reviews/, README.md

        result = service.get_plans(issue_number=123)

        assert result is not None
        assert result.has_specs is True
        assert result.has_plans is False
        assert result.is_complete is False


# =============================================================================
# US3: commit_and_push() and push() contracts
# =============================================================================


class TestCommitAndPushContract:
    """
    Contract tests for commit_and_push().

    Contract: Stage, commit, and optionally push changes in worktree.
    """

    def test_commit_and_push_with_changes(self, temp_git_repo: Path) -> None:
        """commit_and_push should commit changes and return result."""
        from worktree_manager.models import CommitResult
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Make a change in the worktree
        test_file = wt.path / "test.txt"
        test_file.write_text("Hello World\n")

        result = service.commit_and_push(
            issue_number=123,
            message="Add test file",
            push=False,  # No remote to push to in test
        )

        assert isinstance(result, CommitResult)
        assert result.commit_sha is not None
        assert len(result.commit_sha) > 0
        assert result.nothing_to_commit is False

    def test_commit_and_push_nothing_to_commit(self, temp_git_repo: Path) -> None:
        """commit_and_push should handle nothing to commit."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        service.create_worktree(issue_number=123, feature_name="add-auth")

        # Don't make any changes
        result = service.commit_and_push(
            issue_number=123,
            message="Nothing",
            push=False,
        )

        assert result.nothing_to_commit is True
        assert result.commit_sha is None

    def test_commit_and_push_stages_all_changes(self, temp_git_repo: Path) -> None:
        """commit_and_push should stage all changes (new, modified, deleted)."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Create multiple files
        (wt.path / "new_file.txt").write_text("new content\n")
        (wt.path / "another.txt").write_text("more content\n")

        result = service.commit_and_push(
            issue_number=123,
            message="Add multiple files",
            push=False,
        )

        assert result.commit_sha is not None

        # Verify files are committed (check git log in worktree)
        log_result = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=wt.path,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Add multiple files" in log_result.stdout


class TestPushContract:
    """
    Contract tests for push().

    Contract: Push commits to remote.
    Note: These tests are limited since we don't have a real remote.
    """

    def test_push_without_remote_returns_error(self, temp_git_repo: Path) -> None:
        """push should handle missing remote gracefully."""
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Make and commit a change
        (wt.path / "test.txt").write_text("test\n")
        service.commit_and_push(issue_number=123, message="test", push=False)

        # Try to push without remote configured
        result = service.push(issue_number=123)

        # Should return False since there's no remote
        assert result is False


# =============================================================================
# US4: remove_worktree() contracts
# =============================================================================


class TestRemoveWorktreeContract:
    """
    Contract tests for remove_worktree().

    Contract: Remove worktree and optionally delete branches.
    """

    def test_remove_worktree_removes_directory(self, temp_git_repo: Path) -> None:
        """remove_worktree should remove the worktree directory."""
        from worktree_manager.models import OperationStatus
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Verify worktree exists
        assert wt.path.exists()

        result = service.remove_worktree(issue_number=123)

        assert result.status == OperationStatus.SUCCESS
        assert not wt.path.exists()

    def test_remove_worktree_with_delete_branch(self, temp_git_repo: Path) -> None:
        """remove_worktree should delete local branch when requested."""
        from worktree_manager.models import OperationStatus
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        service.create_worktree(issue_number=123, feature_name="add-auth")

        result = service.remove_worktree(issue_number=123, delete_branch=True)

        assert result.status == OperationStatus.SUCCESS

        # Branch should be deleted
        branch_check = subprocess.run(
            ["git", "show-ref", "--verify", "refs/heads/123-add-auth"],
            cwd=temp_git_repo,
            capture_output=True,
        )
        assert branch_check.returncode != 0  # Branch doesn't exist

    def test_remove_worktree_uncommitted_changes_fails(self, temp_git_repo: Path) -> None:
        """remove_worktree should fail with uncommitted changes."""
        from worktree_manager.errors import UncommittedChangesError
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Make uncommitted change
        (wt.path / "dirty.txt").write_text("dirty\n")

        with pytest.raises(UncommittedChangesError):
            service.remove_worktree(issue_number=123)

        # Worktree should still exist
        assert wt.path.exists()

    def test_remove_worktree_force_with_changes(self, temp_git_repo: Path) -> None:
        """remove_worktree with force should remove even with uncommitted changes."""
        from worktree_manager.models import OperationStatus
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)
        wt = service.create_worktree(issue_number=123, feature_name="add-auth")

        # Make uncommitted change
        (wt.path / "dirty.txt").write_text("dirty\n")

        result = service.remove_worktree(issue_number=123, force=True)

        assert result.status == OperationStatus.SUCCESS
        assert not wt.path.exists()

    def test_remove_worktree_not_found_raises_error(self, temp_git_repo: Path) -> None:
        """remove_worktree should raise error if worktree doesn't exist."""
        from worktree_manager.errors import WorktreeNotFoundError
        from worktree_manager.service import WorktreeService

        service = WorktreeService(temp_git_repo)

        with pytest.raises(WorktreeNotFoundError):
            service.remove_worktree(issue_number=999)
