"""
Unit tests for GitClient.

Tests the low-level git CLI wrapper functionality.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGitClient:
    """Tests for GitClient class."""

    def test_init_validates_git_available(self, tmp_path: Path) -> None:
        """GitClient should raise GitNotFoundError if git is not in PATH."""
        from worktree_manager.errors import GitNotFoundError
        from worktree_manager.git_client import GitClient

        # Mock subprocess to simulate git not found
        with patch("worktree_manager.git_client.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("git not found")

            with pytest.raises(GitNotFoundError) as exc_info:
                GitClient(tmp_path)

            assert "git" in str(exc_info.value).lower()

    def test_init_validates_repository(self, tmp_path: Path) -> None:
        """GitClient should raise NotARepositoryError if path is not a git repo."""
        from worktree_manager.errors import NotARepositoryError
        from worktree_manager.git_client import GitClient

        # tmp_path is not a git repository
        with pytest.raises(NotARepositoryError) as exc_info:
            GitClient(tmp_path)

        assert str(tmp_path) in str(exc_info.value)

    def test_init_succeeds_with_valid_repo(self, temp_git_repo: Path) -> None:
        """GitClient should initialize successfully with a valid git repository."""
        from worktree_manager.git_client import GitClient

        client = GitClient(temp_git_repo)
        assert client.repo_path == temp_git_repo

    def test_run_command_executes_git(self, temp_git_repo: Path) -> None:
        """run_command should execute git commands and return output."""
        from worktree_manager.git_client import GitClient

        client = GitClient(temp_git_repo)
        result = client.run_command(["status"])

        assert "On branch" in result.stdout

    def test_run_command_raises_on_failure(self, temp_git_repo: Path) -> None:
        """run_command should raise GitCommandError on failure."""
        from worktree_manager.errors import GitCommandError
        from worktree_manager.git_client import GitClient

        client = GitClient(temp_git_repo)

        with pytest.raises(GitCommandError) as exc_info:
            client.run_command(["invalid-command-that-does-not-exist"])

        assert "invalid-command" in str(exc_info.value).lower()

    def test_run_command_with_check_false(self, temp_git_repo: Path) -> None:
        """run_command with check=False should not raise on failure."""
        from worktree_manager.git_client import GitClient

        client = GitClient(temp_git_repo)
        result = client.run_command(
            ["branch", "--show-current-nonexistent"],
            check=False,
        )

        assert result.returncode != 0


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
    # Create initial commit
    readme = repo_path / "README.md"
    readme.write_text("# Test Repository\n")
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
