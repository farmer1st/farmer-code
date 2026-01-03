"""
Unit tests for WorktreeService query methods.

Tests list_worktrees, get_worktree, and get_branch methods.
Uses mocking to test the service in isolation from git.
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# =============================================================================
# T065: Unit tests for list_worktrees()
# =============================================================================


class TestListWorktrees:
    """Tests for WorktreeService.list_worktrees()."""

    def test_list_worktrees_empty(self) -> None:
        """list_worktrees should return empty list when no worktrees exist."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "_run_git_command") as mock_git:
            # Mock main worktree only (no feature worktrees)
            mock_git.return_value = "worktree /path/to/main\nHEAD abc123\nbranch refs/heads/main\n"

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()

            worktrees = service.list_worktrees()
            assert worktrees == []

    def test_list_worktrees_single(self) -> None:
        """list_worktrees should return single worktree."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "_run_git_command") as mock_git:
            # Mock porcelain output with one feature worktree
            mock_git.return_value = (
                "worktree /path/to/main\nHEAD abc123\nbranch refs/heads/main\n\n"
                "worktree /path/to/main-123-feature\nHEAD def456\nbranch refs/heads/123-feature\n"
            )

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service._parse_worktree_list = WorktreeService._parse_worktree_list.__get__(
                service, WorktreeService
            )

            worktrees = service.list_worktrees()
            assert len(worktrees) == 1
            assert worktrees[0].issue_number == 123
            assert worktrees[0].feature_name == "feature"

    def test_list_worktrees_multiple(self) -> None:
        """list_worktrees should return all feature worktrees."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "_run_git_command") as mock_git:
            mock_git.return_value = (
                "worktree /path/to/main\nHEAD abc123\nbranch refs/heads/main\n\n"
                "worktree /path/to/main-123-feature\nHEAD def456\nbranch refs/heads/123-feature\n\n"
                "worktree /path/to/main-456-other\nHEAD ghi789\nbranch refs/heads/456-other\n"
            )

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service._parse_worktree_list = WorktreeService._parse_worktree_list.__get__(
                service, WorktreeService
            )

            worktrees = service.list_worktrees()
            assert len(worktrees) == 2
            issue_numbers = {wt.issue_number for wt in worktrees}
            assert issue_numbers == {123, 456}

    def test_list_worktrees_excludes_main(self) -> None:
        """list_worktrees should exclude main repository worktree."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "_run_git_command") as mock_git:
            mock_git.return_value = (
                "worktree /path/to/main\nHEAD abc123\nbranch refs/heads/main\n\n"
                "worktree /path/to/main-123-feature\nHEAD def456\nbranch refs/heads/123-feature\n"
            )

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service._parse_worktree_list = WorktreeService._parse_worktree_list.__get__(
                service, WorktreeService
            )

            worktrees = service.list_worktrees()
            # Main should not be in the list
            for wt in worktrees:
                assert wt.path != Path("/path/to/main")


# =============================================================================
# T066: Unit tests for get_worktree()
# =============================================================================


class TestGetWorktree:
    """Tests for WorktreeService.get_worktree()."""

    def test_get_worktree_exists(self) -> None:
        """get_worktree should return worktree when it exists."""
        from worktree_manager import Worktree, WorktreeService

        with patch.object(WorktreeService, "list_worktrees") as mock_list:
            mock_list.return_value = [
                Worktree(
                    issue_number=123,
                    feature_name="feature",
                    path=Path("/path/to/main-123-feature"),
                    main_repo_path=Path("/path/to/main"),
                    branch_name="123-feature",
                    is_clean=True,
                    created_at=datetime.now(UTC),
                )
            ]

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service.list_worktrees = mock_list

            worktree = service.get_worktree(123)
            assert worktree is not None
            assert worktree.issue_number == 123

    def test_get_worktree_not_exists(self) -> None:
        """get_worktree should return None when worktree doesn't exist."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "list_worktrees") as mock_list:
            mock_list.return_value = []

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service.list_worktrees = mock_list

            worktree = service.get_worktree(999)
            assert worktree is None

    def test_get_worktree_finds_correct_issue(self) -> None:
        """get_worktree should find worktree by issue number among many."""
        from worktree_manager import Worktree, WorktreeService

        with patch.object(WorktreeService, "list_worktrees") as mock_list:
            mock_list.return_value = [
                Worktree(
                    issue_number=100,
                    feature_name="first",
                    path=Path("/path/to/main-100-first"),
                    main_repo_path=Path("/path/to/main"),
                    branch_name="100-first",
                    is_clean=True,
                    created_at=datetime.now(UTC),
                ),
                Worktree(
                    issue_number=200,
                    feature_name="second",
                    path=Path("/path/to/main-200-second"),
                    main_repo_path=Path("/path/to/main"),
                    branch_name="200-second",
                    is_clean=True,
                    created_at=datetime.now(UTC),
                ),
                Worktree(
                    issue_number=300,
                    feature_name="third",
                    path=Path("/path/to/main-300-third"),
                    main_repo_path=Path("/path/to/main"),
                    branch_name="300-third",
                    is_clean=True,
                    created_at=datetime.now(UTC),
                ),
            ]

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service.list_worktrees = mock_list

            worktree = service.get_worktree(200)
            assert worktree is not None
            assert worktree.issue_number == 200
            assert worktree.feature_name == "second"


# =============================================================================
# T067: Unit tests for get_branch()
# =============================================================================


class TestGetBranch:
    """Tests for WorktreeService.get_branch()."""

    def test_get_branch_local_only(self) -> None:
        """get_branch should return branch info for local-only branch."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "_run_git_command") as mock_git:
            # Simulate git branch -vv output
            mock_git.return_value = "* 123-feature abc1234 [ahead 2] Latest commit\n"

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service._parse_branch_info = WorktreeService._parse_branch_info.__get__(
                service, WorktreeService
            )

            branch = service.get_branch("123-feature")
            assert branch is not None
            assert branch.name == "123-feature"
            assert branch.is_local is True

    def test_get_branch_tracking_remote(self) -> None:
        """get_branch should return branch with remote tracking info."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "_run_git_command") as mock_git:
            # Simulate tracking branch output
            tracking_output = (
                "* 123-feature abc1234 [origin/123-feature: ahead 2, behind 1] Latest commit\n"
            )
            mock_git.return_value = tracking_output

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service._parse_branch_info = WorktreeService._parse_branch_info.__get__(
                service, WorktreeService
            )

            branch = service.get_branch("123-feature")
            assert branch is not None
            assert branch.name == "123-feature"
            assert branch.remote == "origin"
            assert branch.remote_branch == "123-feature"
            assert branch.ahead == 2
            assert branch.behind == 1
            assert branch.is_tracking is True

    def test_get_branch_not_exists(self) -> None:
        """get_branch should return None when branch doesn't exist."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "_run_git_command") as mock_git:
            # No matching branch
            mock_git.return_value = ""

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service._parse_branch_info = WorktreeService._parse_branch_info.__get__(
                service, WorktreeService
            )

            branch = service.get_branch("nonexistent")
            assert branch is None

    def test_get_branch_synced(self) -> None:
        """get_branch should correctly identify synced branch."""
        from worktree_manager import WorktreeService

        with patch.object(WorktreeService, "_run_git_command") as mock_git:
            # Synced branch - no ahead/behind markers
            mock_git.return_value = "* 123-feature abc1234 [origin/123-feature] Latest commit\n"

            service = WorktreeService.__new__(WorktreeService)
            service.repo_path = Path("/path/to/main")
            service.git = MagicMock()
            service._parse_branch_info = WorktreeService._parse_branch_info.__get__(
                service, WorktreeService
            )

            branch = service.get_branch("123-feature")
            assert branch is not None
            assert branch.is_synced is True
            assert branch.ahead == 0
            assert branch.behind == 0

    def test_get_branch_merged(self) -> None:
        """get_branch should detect merged status."""
        from worktree_manager import WorktreeService

        service = WorktreeService.__new__(WorktreeService)
        service.repo_path = Path("/path/to/main")
        service.git = MagicMock()

        # Mock _run_git_command for branch -vv
        with patch.object(WorktreeService, "_run_git_command") as mock_run:
            mock_run.return_value = "  123-feature abc1234 Latest commit\n"

            # Mock git.run_command for --merged check
            merged_result = MagicMock()
            merged_result.stdout = "  123-feature\n"
            service.git.run_command.return_value = merged_result

            branch = service.get_branch("123-feature")
            assert branch is not None
            assert branch.is_merged is True
