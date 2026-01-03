"""
Unit tests for worktree_manager exceptions.

Tests the custom exception hierarchy and error messages.
"""


class TestWorkTreeError:
    """Tests for base WorktreeError exception."""

    def test_worktree_error_is_exception(self) -> None:
        """WorktreeError should be an Exception subclass."""
        from worktree_manager.errors import WorktreeError

        assert issubclass(WorktreeError, Exception)

    def test_worktree_error_has_message_and_code(self) -> None:
        """WorktreeError should store message and error_code."""
        from worktree_manager.errors import WorktreeError

        error = WorktreeError("Test error", error_code="TEST_ERROR")
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert str(error) == "Test error"

    def test_worktree_error_default_code(self) -> None:
        """WorktreeError should have default error_code."""
        from worktree_manager.errors import WorktreeError

        error = WorktreeError("Test error")
        assert error.error_code == "UNKNOWN_ERROR"


class TestGitNotFoundError:
    """Tests for GitNotFoundError exception."""

    def test_git_not_found_error_is_worktree_error(self) -> None:
        """GitNotFoundError should be a WorktreeError subclass."""
        from worktree_manager.errors import GitNotFoundError, WorktreeError

        assert issubclass(GitNotFoundError, WorktreeError)

    def test_git_not_found_error_message(self) -> None:
        """GitNotFoundError should have appropriate error code."""
        from worktree_manager.errors import GitNotFoundError

        error = GitNotFoundError("Git not found in PATH")
        assert error.error_code == "GIT_NOT_FOUND"


class TestNotARepositoryError:
    """Tests for NotARepositoryError exception."""

    def test_not_a_repository_error_is_worktree_error(self) -> None:
        """NotARepositoryError should be a WorktreeError subclass."""
        from worktree_manager.errors import NotARepositoryError, WorktreeError

        assert issubclass(NotARepositoryError, WorktreeError)

    def test_not_a_repository_error_stores_path(self) -> None:
        """NotARepositoryError should store the invalid path."""

        from worktree_manager.errors import NotARepositoryError

        error = NotARepositoryError("/some/path")
        assert error.error_code == "NOT_A_REPOSITORY"
        assert "/some/path" in str(error)


class TestGitCommandError:
    """Tests for GitCommandError exception."""

    def test_git_command_error_is_worktree_error(self) -> None:
        """GitCommandError should be a WorktreeError subclass."""
        from worktree_manager.errors import GitCommandError, WorktreeError

        assert issubclass(GitCommandError, WorktreeError)

    def test_git_command_error_stores_details(self) -> None:
        """GitCommandError should store command, returncode, and stderr."""
        from worktree_manager.errors import GitCommandError

        error = GitCommandError(
            command=["git", "status"],
            returncode=128,
            stderr="fatal: not a git repository",
        )
        assert error.error_code == "GIT_COMMAND_ERROR"
        assert error.command == ["git", "status"]
        assert error.returncode == 128
        assert error.stderr == "fatal: not a git repository"


class TestBranchErrors:
    """Tests for branch-related exceptions."""

    def test_main_branch_not_found_error(self) -> None:
        """MainBranchNotFoundError should have correct error code."""
        from worktree_manager.errors import MainBranchNotFoundError, WorktreeError

        assert issubclass(MainBranchNotFoundError, WorktreeError)
        error = MainBranchNotFoundError("main branch not found")
        assert error.error_code == "MAIN_BRANCH_NOT_FOUND"

    def test_branch_exists_error(self) -> None:
        """BranchExistsError should store branch name."""
        from worktree_manager.errors import BranchExistsError, WorktreeError

        assert issubclass(BranchExistsError, WorktreeError)
        error = BranchExistsError("123-feature")
        assert error.error_code == "BRANCH_EXISTS"
        assert "123-feature" in str(error)

    def test_branch_not_found_error(self) -> None:
        """BranchNotFoundError should store branch name."""
        from worktree_manager.errors import BranchNotFoundError, WorktreeError

        assert issubclass(BranchNotFoundError, WorktreeError)
        error = BranchNotFoundError("123-feature")
        assert error.error_code == "BRANCH_NOT_FOUND"
        assert "123-feature" in str(error)


class TestWorktreeErrors:
    """Tests for worktree-related exceptions."""

    def test_worktree_exists_error(self) -> None:
        """WorktreeExistsError should store worktree path."""
        from worktree_manager.errors import WorktreeError, WorktreeExistsError

        assert issubclass(WorktreeExistsError, WorktreeError)
        error = WorktreeExistsError("/path/to/worktree")
        assert error.error_code == "WORKTREE_EXISTS"
        assert "/path/to/worktree" in str(error)

    def test_worktree_not_found_error(self) -> None:
        """WorktreeNotFoundError should store issue number."""
        from worktree_manager.errors import WorktreeError, WorktreeNotFoundError

        assert issubclass(WorktreeNotFoundError, WorktreeError)
        error = WorktreeNotFoundError(123)
        assert error.error_code == "WORKTREE_NOT_FOUND"
        assert "123" in str(error)


class TestOperationErrors:
    """Tests for operation-related exceptions."""

    def test_uncommitted_changes_error(self) -> None:
        """UncommittedChangesError should have correct error code."""
        from worktree_manager.errors import UncommittedChangesError, WorktreeError

        assert issubclass(UncommittedChangesError, WorktreeError)
        error = UncommittedChangesError("Worktree has uncommitted changes")
        assert error.error_code == "UNCOMMITTED_CHANGES"

    def test_push_error(self) -> None:
        """PushError should have correct error code."""
        from worktree_manager.errors import PushError, WorktreeError

        assert issubclass(PushError, WorktreeError)
        error = PushError("Push failed: network error")
        assert error.error_code == "PUSH_ERROR"
