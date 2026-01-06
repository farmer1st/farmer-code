"""
Custom Exceptions

Exception hierarchy for worktree management errors with meaningful
error messages and error codes for client handling.
"""

from pathlib import Path


class WorktreeError(Exception):
    """Base exception for all worktree management errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"


class GitNotFoundError(WorktreeError):
    """
    Git is not installed or not in PATH.

    Raised when:
    - git executable cannot be found
    - git command fails with FileNotFoundError
    """

    def __init__(self, message: str = "Git is not installed or not in PATH") -> None:
        super().__init__(message, error_code="GIT_NOT_FOUND")


class NotARepositoryError(WorktreeError):
    """
    Path is not a git repository.

    Raised when:
    - Path doesn't contain .git directory
    - git rev-parse fails
    """

    def __init__(self, path: str | Path) -> None:
        message = f"Not a git repository: {path}"
        super().__init__(message, error_code="NOT_A_REPOSITORY")
        self.path = path


class GitCommandError(WorktreeError):
    """
    Git command execution failed.

    Raised when:
    - git command returns non-zero exit code
    - Unexpected git behavior
    """

    def __init__(
        self,
        command: list[str],
        returncode: int,
        stderr: str,
    ) -> None:
        cmd_str = " ".join(command)
        message = f"Git command failed: {cmd_str}\nExit code: {returncode}\nError: {stderr}"
        super().__init__(message, error_code="GIT_COMMAND_ERROR")
        self.command = command
        self.returncode = returncode
        self.stderr = stderr


class MainBranchNotFoundError(WorktreeError):
    """
    Main branch doesn't exist.

    Raised when:
    - Repository has no 'main' branch
    - Cannot create branch from main
    """

    def __init__(self, message: str = "Main branch not found") -> None:
        super().__init__(message, error_code="MAIN_BRANCH_NOT_FOUND")


class BranchExistsError(WorktreeError):
    """
    Branch already exists.

    Raised when:
    - Trying to create a branch that already exists locally or remotely
    """

    def __init__(self, branch_name: str) -> None:
        message = f"Branch already exists: {branch_name}"
        super().__init__(message, error_code="BRANCH_EXISTS")
        self.branch_name = branch_name


class BranchNotFoundError(WorktreeError):
    """
    Branch doesn't exist.

    Raised when:
    - Trying to checkout a branch that doesn't exist
    - Branch was deleted
    """

    def __init__(self, branch_name: str) -> None:
        message = f"Branch not found: {branch_name}"
        super().__init__(message, error_code="BRANCH_NOT_FOUND")
        self.branch_name = branch_name


class WorktreeExistsError(WorktreeError):
    """
    Worktree path already exists.

    Raised when:
    - Sibling directory for worktree already exists
    - Cannot create worktree at path
    """

    def __init__(self, path: str | Path) -> None:
        message = f"Worktree already exists: {path}"
        super().__init__(message, error_code="WORKTREE_EXISTS")
        self.path = path


class WorktreeNotFoundError(WorktreeError):
    """
    No worktree for issue number.

    Raised when:
    - Looking up worktree by issue number fails
    - Worktree was removed or never created
    """

    def __init__(self, issue_number: int) -> None:
        message = f"No worktree found for issue #{issue_number}"
        super().__init__(message, error_code="WORKTREE_NOT_FOUND")
        self.issue_number = issue_number


class UncommittedChangesError(WorktreeError):
    """
    Worktree has uncommitted changes.

    Raised when:
    - Trying to remove worktree with dirty working tree
    - Operation requires clean working tree
    """

    def __init__(self, message: str = "Worktree has uncommitted changes") -> None:
        super().__init__(message, error_code="UNCOMMITTED_CHANGES")


class PushError(WorktreeError):
    """
    Push to remote failed.

    Raised when:
    - Network error during push
    - Authentication failed
    - Remote rejected push
    """

    def __init__(self, message: str = "Push to remote failed") -> None:
        super().__init__(message, error_code="PUSH_ERROR")
