"""
Git CLI Wrapper

Low-level wrapper around git commands using subprocess.
Provides type-safe interface for git operations.
"""

import subprocess
from pathlib import Path

from .errors import GitCommandError, GitNotFoundError, NotARepositoryError
from .logger import logger


class GitClient:
    """
    Low-level git CLI wrapper.

    Wraps git commands using subprocess.run() with proper error handling.
    All methods operate on a specific repository path.
    """

    def __init__(self, repo_path: str | Path) -> None:
        """
        Initialize GitClient for a repository.

        Args:
            repo_path: Path to the git repository root

        Raises:
            GitNotFoundError: If git is not installed or not in PATH
            NotARepositoryError: If repo_path is not a git repository
        """
        self.repo_path = Path(repo_path).resolve()

        # T012: Check git availability
        self._check_git_available()

        # T013: Validate repository
        self._validate_repository()

        logger.info(
            "Initialized GitClient",
            extra={"context": {"repo_path": str(self.repo_path)}},
        )

    def _check_git_available(self) -> None:
        """
        Check that git is installed and in PATH.

        Raises:
            GitNotFoundError: If git is not available
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise GitNotFoundError("Git command failed")
        except FileNotFoundError as e:
            raise GitNotFoundError("Git is not installed or not in PATH") from e

    def _validate_repository(self) -> None:
        """
        Validate that repo_path is a git repository.

        Raises:
            NotARepositoryError: If path is not a git repository
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise NotARepositoryError(self.repo_path)
        except FileNotFoundError:
            raise NotARepositoryError(self.repo_path) from None

    def run_command(
        self,
        args: list[str],
        check: bool = True,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        Run a git command.

        Args:
            args: Git command arguments (without 'git' prefix)
            check: If True, raise GitCommandError on non-zero exit
            cwd: Working directory (defaults to repo_path)

        Returns:
            CompletedProcess with stdout/stderr

        Raises:
            GitCommandError: If command fails and check=True

        Example:
            >>> client = GitClient("/path/to/repo")
            >>> result = client.run_command(["status"])
            >>> print(result.stdout)
        """
        command = ["git"] + args
        working_dir = cwd or self.repo_path

        logger.info(
            "Running git command",
            extra={
                "context": {
                    "command": command,
                    "cwd": str(working_dir),
                }
            },
        )

        try:
            result = subprocess.run(
                command,
                cwd=working_dir,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as e:
            raise GitNotFoundError("Git is not installed or not in PATH") from e

        if check and result.returncode != 0:
            raise GitCommandError(
                command=args,
                returncode=result.returncode,
                stderr=result.stderr.strip(),
            )

        return result

    def get_current_branch(self) -> str:
        """
        Get the current branch name.

        Returns:
            Current branch name

        Raises:
            GitCommandError: If not on a branch (detached HEAD)
        """
        result = self.run_command(["rev-parse", "--abbrev-ref", "HEAD"])
        return result.stdout.strip()

    def branch_exists(self, branch_name: str, remote: bool = False) -> bool:
        """
        Check if a branch exists.

        Args:
            branch_name: Name of the branch
            remote: If True, check remote branches

        Returns:
            True if branch exists
        """
        if remote:
            # Check remote branches
            result = self.run_command(
                ["ls-remote", "--heads", "origin", branch_name],
                check=False,
            )
            return bool(result.stdout.strip())
        else:
            # Check local branches
            result = self.run_command(
                ["show-ref", "--verify", f"refs/heads/{branch_name}"],
                check=False,
            )
            return result.returncode == 0

    def get_repo_name(self) -> str:
        """
        Get the repository directory name.

        Returns:
            Name of the repository directory
        """
        return self.repo_path.name
