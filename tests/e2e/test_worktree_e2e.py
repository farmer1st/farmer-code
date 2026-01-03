"""
E2E tests for worktree_manager.

Tests against real repositories (farmer1st/farmcode-tests).
These tests require:
1. A test repository at ../farmcode-tests (sibling directory)
2. Git configured with push access to the test repo

Run with: pytest tests/e2e/test_worktree_e2e.py -v --run-e2e
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

import pytest


# Marker for E2E tests - skip unless --run-e2e flag is provided
def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "journey(id): mark test as covering specific user journey")


# Skip E2E tests unless explicitly requested
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_E2E_TESTS"),
    reason="E2E tests skipped. Set RUN_E2E_TESTS=1 to run",
)


# Test repository path
TEST_REPO_NAME = "farmcode-tests"


@pytest.fixture
def test_repo_path(tmp_path: Path) -> Path | None:
    """
    Get or create a test repository for E2E tests.

    Returns path to test repo or None if not available.
    """
    # Check for existing test repo
    current_dir = Path(__file__).parent.parent.parent
    existing_repo = current_dir.parent / TEST_REPO_NAME

    if existing_repo.exists() and (existing_repo / ".git").exists():
        return existing_repo

    # Create temporary test repo for E2E tests
    repo_path = tmp_path / "e2e-test-repo"
    repo_path.mkdir()

    # Initialize as git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "E2E Test"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit on main
    readme = repo_path / "README.md"
    readme.write_text("# E2E Test Repository\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


# =============================================================================
# T074: E2E test for create_worktree()
# =============================================================================


@pytest.mark.e2e
@pytest.mark.journey("WT-001")
class TestCreateWorktreeE2E:
    """E2E tests for create_worktree()."""

    def test_create_worktree_e2e(self, test_repo_path: Path) -> None:
        """E2E test: Create worktree for a new feature."""
        from worktree_manager import WorktreeService

        if test_repo_path is None:
            pytest.skip("Test repository not available")

        service = WorktreeService(test_repo_path)
        issue_number = int(datetime.now().strftime("%H%M%S"))  # Unique issue number

        try:
            # Create worktree
            worktree = service.create_worktree(issue_number, "e2e-feature")

            # Verify worktree exists
            assert worktree.path.exists()
            assert worktree.issue_number == issue_number
            assert worktree.branch_name == f"{issue_number}-e2e-feature"

            # Verify branch was created
            result = subprocess.run(
                ["git", "branch", "--list", f"{issue_number}-e2e-feature"],
                cwd=test_repo_path,
                capture_output=True,
                text=True,
            )
            assert f"{issue_number}-e2e-feature" in result.stdout

        finally:
            # Cleanup
            if worktree.path.exists():
                service.remove_worktree(issue_number, delete_branch=True, force=True)


# =============================================================================
# T075: E2E test for init_plans()
# =============================================================================


@pytest.mark.e2e
@pytest.mark.journey("WT-002")
class TestInitPlansE2E:
    """E2E tests for init_plans()."""

    def test_init_plans_e2e(self, test_repo_path: Path) -> None:
        """E2E test: Initialize .plans/ structure."""
        from worktree_manager import WorktreeService

        if test_repo_path is None:
            pytest.skip("Test repository not available")

        service = WorktreeService(test_repo_path)
        issue_number = int(datetime.now().strftime("%H%M%S")) + 1

        try:
            # Create worktree first
            worktree = service.create_worktree(issue_number, "e2e-plans")

            # Initialize plans
            plans = service.init_plans(issue_number, "E2E Feature")

            # Verify structure
            assert plans.is_complete
            assert (worktree.path / ".plans" / str(issue_number) / "specs").is_dir()
            assert (worktree.path / ".plans" / str(issue_number) / "plans").is_dir()
            assert (worktree.path / ".plans" / str(issue_number) / "reviews").is_dir()
            assert (worktree.path / ".plans" / str(issue_number) / "README.md").is_file()

            # Verify README content
            readme = worktree.path / ".plans" / str(issue_number) / "README.md"
            content = readme.read_text()
            assert "E2E Feature" in content
            assert f"#{issue_number}" in content

        finally:
            # Cleanup
            if worktree.path.exists():
                service.remove_worktree(issue_number, delete_branch=True, force=True)


# =============================================================================
# T076: E2E test for commit_and_push()
# =============================================================================


@pytest.mark.e2e
@pytest.mark.journey("WT-003")
class TestCommitAndPushE2E:
    """E2E tests for commit_and_push()."""

    def test_commit_e2e(self, test_repo_path: Path) -> None:
        """E2E test: Commit changes (without push for local repo)."""
        from worktree_manager import WorktreeService

        if test_repo_path is None:
            pytest.skip("Test repository not available")

        service = WorktreeService(test_repo_path)
        issue_number = int(datetime.now().strftime("%H%M%S")) + 2

        try:
            # Create worktree
            worktree = service.create_worktree(issue_number, "e2e-commit")

            # Make changes
            test_file = worktree.path / "e2e_test.py"
            test_file.write_text("# E2E test file\n")

            # Commit (no push for local repo)
            result = service.commit_and_push(issue_number, "E2E: Add test file", push=False)

            # Verify commit
            assert result.commit_sha is not None
            assert len(result.commit_sha) >= 7
            assert result.nothing_to_commit is False

            # Verify commit in git log
            log_result = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                cwd=worktree.path,
                capture_output=True,
                text=True,
            )
            assert "E2E: Add test file" in log_result.stdout

        finally:
            # Cleanup
            if worktree.path.exists():
                service.remove_worktree(issue_number, delete_branch=True, force=True)


# =============================================================================
# T077: E2E test for remove_worktree()
# =============================================================================


@pytest.mark.e2e
@pytest.mark.journey("WT-004")
class TestRemoveWorktreeE2E:
    """E2E tests for remove_worktree()."""

    def test_remove_worktree_e2e(self, test_repo_path: Path) -> None:
        """E2E test: Remove worktree and cleanup."""
        from worktree_manager import OperationStatus, WorktreeService

        if test_repo_path is None:
            pytest.skip("Test repository not available")

        service = WorktreeService(test_repo_path)
        issue_number = int(datetime.now().strftime("%H%M%S")) + 3

        # Create worktree
        worktree = service.create_worktree(issue_number, "e2e-remove")
        worktree_path = worktree.path

        assert worktree_path.exists()

        # Remove worktree with branch deletion
        result = service.remove_worktree(
            issue_number,
            delete_branch=True,
            delete_remote_branch=False,
            force=False,
        )

        # Verify removal
        assert result.status == OperationStatus.SUCCESS
        assert not worktree_path.exists()

        # Verify branch deleted
        branch_result = subprocess.run(
            ["git", "branch", "--list", f"{issue_number}-e2e-remove"],
            cwd=test_repo_path,
            capture_output=True,
            text=True,
        )
        assert f"{issue_number}-e2e-remove" not in branch_result.stdout

    def test_remove_with_force_e2e(self, test_repo_path: Path) -> None:
        """E2E test: Force remove worktree with uncommitted changes."""
        from worktree_manager import OperationStatus, WorktreeService

        if test_repo_path is None:
            pytest.skip("Test repository not available")

        service = WorktreeService(test_repo_path)
        issue_number = int(datetime.now().strftime("%H%M%S")) + 4

        # Create worktree with uncommitted changes
        worktree = service.create_worktree(issue_number, "e2e-force-remove")
        dirty_file = worktree.path / "uncommitted.txt"
        dirty_file.write_text("This won't be committed")
        worktree_path = worktree.path

        # Force remove
        result = service.remove_worktree(
            issue_number,
            delete_branch=True,
            force=True,
        )

        # Verify removal
        assert result.status == OperationStatus.SUCCESS
        assert not worktree_path.exists()
