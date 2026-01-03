"""
WorktreeService - High-level service for git worktree management.

Provides create, manage, and remove operations for git worktrees.
"""

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .errors import (
    BranchExistsError,
    BranchNotFoundError,
    MainBranchNotFoundError,
    UncommittedChangesError,
    WorktreeExistsError,
    WorktreeNotFoundError,
)
from .git_client import GitClient
from .logger import logger
from .models import Branch, CommitResult, OperationResult, OperationStatus, PlansFolder, Worktree


class WorktreeService:
    """
    High-level service for managing git worktrees.

    Wraps GitClient with business logic for worktree operations.
    All operations are scoped to a single git repository.
    """

    def __init__(self, repo_path: str | Path) -> None:
        """
        Initialize WorktreeService for a repository.

        Args:
            repo_path: Path to the main git repository

        Raises:
            GitNotFoundError: If git is not installed
            NotARepositoryError: If repo_path is not a git repository
        """
        self.repo_path = Path(repo_path).resolve()
        self.git = GitClient(self.repo_path)

        logger.info(
            "Initialized WorktreeService",
            extra={"context": {"repo_path": str(self.repo_path)}},
        )

    def _get_worktree_path(self, issue_number: int, feature_name: str) -> Path:
        """
        Calculate the worktree path in sibling directory.

        Format: {parent}/{repo_name}-{issue_number}-{feature_name}

        Args:
            issue_number: Issue number
            feature_name: Feature short name

        Returns:
            Path to the worktree directory (may not exist yet)
        """
        repo_name = self.git.get_repo_name()
        worktree_name = f"{repo_name}-{issue_number}-{feature_name}"
        return self.repo_path.parent / worktree_name

    def _check_main_branch_exists(self) -> None:
        """
        Check that main branch exists.

        Raises:
            MainBranchNotFoundError: If main branch doesn't exist
        """
        if not self.git.branch_exists("main"):
            raise MainBranchNotFoundError("Main branch not found. Cannot create feature branches.")

    def create_worktree(self, issue_number: int, feature_name: str) -> Worktree:
        """
        Create a new feature branch from main and worktree in sibling directory.

        Args:
            issue_number: Issue number for the feature
            feature_name: Short name for the feature (lowercase, hyphens)

        Returns:
            Worktree model with created worktree info

        Raises:
            MainBranchNotFoundError: If main branch doesn't exist
            WorktreeExistsError: If worktree directory already exists
            BranchExistsError: If branch already exists locally
        """
        branch_name = f"{issue_number}-{feature_name}"
        worktree_path = self._get_worktree_path(issue_number, feature_name)

        logger.info(
            "Creating worktree",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "feature_name": feature_name,
                    "branch_name": branch_name,
                    "worktree_path": str(worktree_path),
                }
            },
        )

        # Check preconditions
        self._check_main_branch_exists()

        if worktree_path.exists():
            raise WorktreeExistsError(worktree_path)

        if self.git.branch_exists(branch_name):
            raise BranchExistsError(branch_name)

        # Create branch from main (without checkout - just create the ref)
        self.git.run_command(["branch", branch_name, "main"])

        # Create worktree with that branch
        self.git.run_command(["worktree", "add", str(worktree_path), branch_name])

        logger.info(
            "Worktree created",
            extra={
                "context": {
                    "branch_name": branch_name,
                    "worktree_path": str(worktree_path),
                }
            },
        )

        return Worktree(
            issue_number=issue_number,
            feature_name=feature_name,
            path=worktree_path,
            main_repo_path=self.repo_path,
            branch_name=branch_name,
            is_clean=True,
            created_at=datetime.now(UTC),
        )

    def create_worktree_from_existing(
        self,
        issue_number: int,
        feature_name: str,
        branch_name: str,
    ) -> Worktree:
        """
        Create a worktree from an existing branch.

        Args:
            issue_number: Issue number for the feature
            feature_name: Short name for the feature
            branch_name: Name of existing branch to checkout

        Returns:
            Worktree model with created worktree info

        Raises:
            BranchNotFoundError: If branch doesn't exist
            WorktreeExistsError: If worktree directory already exists
        """
        worktree_path = self._get_worktree_path(issue_number, feature_name)

        logger.info(
            "Creating worktree from existing branch",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "feature_name": feature_name,
                    "branch_name": branch_name,
                    "worktree_path": str(worktree_path),
                }
            },
        )

        # Check preconditions
        if worktree_path.exists():
            raise WorktreeExistsError(worktree_path)

        if not self.git.branch_exists(branch_name):
            # Check remote
            if not self.git.branch_exists(branch_name, remote=True):
                raise BranchNotFoundError(branch_name)
            # Fetch and create local tracking branch
            self.git.run_command(["fetch", "origin", branch_name])
            self.git.run_command(["checkout", "-b", branch_name, f"origin/{branch_name}"])
            # Go back to main
            self.git.run_command(["checkout", "main"])

        # Create worktree with existing branch
        self.git.run_command(["worktree", "add", str(worktree_path), branch_name])

        logger.info(
            "Worktree created from existing branch",
            extra={
                "context": {
                    "branch_name": branch_name,
                    "worktree_path": str(worktree_path),
                }
            },
        )

        return Worktree(
            issue_number=issue_number,
            feature_name=feature_name,
            path=worktree_path,
            main_repo_path=self.repo_path,
            branch_name=branch_name,
            is_clean=True,
            created_at=datetime.now(UTC),
        )

    # =========================================================================
    # US2: Plans initialization
    # =========================================================================

    def _find_worktree_path_by_issue(self, issue_number: int) -> Path | None:
        """
        Find the worktree path for an issue number.

        Searches sibling directories for matching worktree pattern.

        Args:
            issue_number: Issue number to find

        Returns:
            Path to worktree if found, None otherwise
        """
        repo_name = self.git.get_repo_name()

        for path in self.repo_path.parent.iterdir():
            if path.is_dir() and path.name.startswith(f"{repo_name}-{issue_number}-"):
                # Verify it's a git worktree
                if (path / ".git").exists():
                    return path

        return None

    def init_plans(
        self,
        issue_number: int,
        feature_title: str | None = None,
    ) -> PlansFolder:
        """
        Initialize .plans/{issue_number}/ structure in worktree.

        Creates specs/, plans/, reviews/ subdirectories and README.md.
        Idempotent: safe to call multiple times.

        Args:
            issue_number: Issue number for the feature
            feature_title: Optional title for README metadata

        Returns:
            PlansFolder model with structure status

        Raises:
            WorktreeNotFoundError: If no worktree for issue number
        """
        worktree_path = self._find_worktree_path_by_issue(issue_number)
        if worktree_path is None:
            raise WorktreeNotFoundError(issue_number)

        plans_path = worktree_path / ".plans" / str(issue_number)

        logger.info(
            "Initializing plans structure",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "plans_path": str(plans_path),
                }
            },
        )

        # Create directory structure (idempotent)
        plans_path.mkdir(parents=True, exist_ok=True)
        (plans_path / "specs").mkdir(exist_ok=True)
        (plans_path / "plans").mkdir(exist_ok=True)
        (plans_path / "reviews").mkdir(exist_ok=True)

        # Create README if not exists
        readme_path = plans_path / "README.md"
        if not readme_path.exists():
            title = feature_title or f"Feature #{issue_number}"
            readme_content = f"""# {title}

**Issue**: #{issue_number}
**Created**: {datetime.now(UTC).isoformat()}
**Status**: In Progress

## Structure

- `specs/` - Feature specifications
- `plans/` - Implementation plans
- `reviews/` - Review artifacts
"""
            readme_path.write_text(readme_content)

        logger.info(
            "Plans structure initialized",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "plans_path": str(plans_path),
                }
            },
        )

        return PlansFolder(
            issue_number=issue_number,
            worktree_path=worktree_path,
            has_specs=True,
            has_plans=True,
            has_reviews=True,
            has_readme=True,
        )

    def get_plans(self, issue_number: int) -> PlansFolder | None:
        """
        Get PlansFolder if .plans/{issue}/ exists.

        Args:
            issue_number: Issue number to look up

        Returns:
            PlansFolder if exists, None otherwise
        """
        worktree_path = self._find_worktree_path_by_issue(issue_number)
        if worktree_path is None:
            return None

        plans_path = worktree_path / ".plans" / str(issue_number)
        if not plans_path.exists():
            return None

        # Check what exists
        has_specs = (plans_path / "specs").is_dir()
        has_plans = (plans_path / "plans").is_dir()
        has_reviews = (plans_path / "reviews").is_dir()
        has_readme = (plans_path / "README.md").is_file()

        return PlansFolder(
            issue_number=issue_number,
            worktree_path=worktree_path,
            has_specs=has_specs,
            has_plans=has_plans,
            has_reviews=has_reviews,
            has_readme=has_readme,
        )

    # =========================================================================
    # US3: Commit and Push
    # =========================================================================

    def _has_changes(self, worktree_path: Path) -> bool:
        """
        Check if worktree has uncommitted changes.

        Args:
            worktree_path: Path to worktree

        Returns:
            True if there are uncommitted changes
        """
        result = self.git.run_command(
            ["status", "--porcelain"],
            cwd=worktree_path,
            check=False,
        )
        return bool(result.stdout.strip())

    def commit_and_push(
        self,
        issue_number: int,
        message: str,
        push: bool = True,
    ) -> CommitResult:
        """
        Stage, commit, and optionally push changes in worktree.

        Args:
            issue_number: Issue number of worktree
            message: Commit message
            push: Whether to push after commit

        Returns:
            CommitResult with commit SHA and push status

        Raises:
            WorktreeNotFoundError: If no worktree for issue number
        """
        worktree_path = self._find_worktree_path_by_issue(issue_number)
        if worktree_path is None:
            raise WorktreeNotFoundError(issue_number)

        logger.info(
            "Committing changes",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "message": message,
                    "push": push,
                }
            },
        )

        # Check if there are changes
        if not self._has_changes(worktree_path):
            logger.info(
                "Nothing to commit",
                extra={"context": {"issue_number": issue_number}},
            )
            return CommitResult(
                commit_sha=None,
                pushed=False,
                nothing_to_commit=True,
                push_error=None,
            )

        # Stage all changes
        self.git.run_command(["add", "-A"], cwd=worktree_path)

        # Commit
        self.git.run_command(
            ["commit", "-m", message],
            cwd=worktree_path,
        )

        # Get commit SHA
        result = self.git.run_command(
            ["rev-parse", "HEAD"],
            cwd=worktree_path,
        )
        commit_sha = result.stdout.strip()

        logger.info(
            "Committed changes",
            extra={
                "context": {
                    "commit_sha": commit_sha,
                    "message": message,
                }
            },
        )

        # Push if requested
        pushed = False
        push_error = None
        if push:
            try:
                pushed = self.push(issue_number)
            except Exception as e:
                push_error = str(e)
                logger.warning(
                    "Push failed",
                    extra={
                        "context": {
                            "issue_number": issue_number,
                            "error": push_error,
                        }
                    },
                )

        return CommitResult(
            commit_sha=commit_sha,
            pushed=pushed,
            nothing_to_commit=False,
            push_error=push_error,
        )

    def push(self, issue_number: int) -> bool:
        """
        Push commits to remote.

        Args:
            issue_number: Issue number of worktree

        Returns:
            True if push succeeded, False otherwise

        Raises:
            WorktreeNotFoundError: If no worktree for issue number
        """
        worktree_path = self._find_worktree_path_by_issue(issue_number)
        if worktree_path is None:
            raise WorktreeNotFoundError(issue_number)

        logger.info(
            "Pushing to remote",
            extra={"context": {"issue_number": issue_number}},
        )

        # Get current branch
        result = self.git.run_command(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=worktree_path,
        )
        branch_name = result.stdout.strip()

        # Try to push
        push_result = self.git.run_command(
            ["push", "-u", "origin", branch_name],
            cwd=worktree_path,
            check=False,
        )

        if push_result.returncode != 0:
            logger.warning(
                "Push failed",
                extra={
                    "context": {
                        "issue_number": issue_number,
                        "branch": branch_name,
                        "error": push_result.stderr.strip(),
                    }
                },
            )
            return False

        logger.info(
            "Pushed to remote",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "branch": branch_name,
                }
            },
        )
        return True

    # =========================================================================
    # US4: Remove Worktree and Cleanup
    # =========================================================================

    def _check_uncommitted_changes(self, worktree_path: Path) -> bool:
        """
        Check if worktree has uncommitted changes.

        Args:
            worktree_path: Path to worktree

        Returns:
            True if there are uncommitted changes
        """
        return self._has_changes(worktree_path)

    def _get_branch_from_worktree(self, worktree_path: Path) -> str:
        """
        Get the branch name of a worktree.

        Args:
            worktree_path: Path to worktree

        Returns:
            Branch name
        """
        result = self.git.run_command(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=worktree_path,
        )
        return result.stdout.strip()

    def remove_worktree(
        self,
        issue_number: int,
        delete_branch: bool = False,
        delete_remote_branch: bool = False,
        force: bool = False,
    ) -> OperationResult:
        """
        Remove a worktree and optionally delete branches.

        Args:
            issue_number: Issue number of worktree
            delete_branch: Whether to delete local branch
            delete_remote_branch: Whether to delete remote branch
            force: Whether to force removal with uncommitted changes

        Returns:
            OperationResult with status and message

        Raises:
            WorktreeNotFoundError: If no worktree for issue number
            UncommittedChangesError: If uncommitted changes and not force
        """
        worktree_path = self._find_worktree_path_by_issue(issue_number)
        if worktree_path is None:
            raise WorktreeNotFoundError(issue_number)

        logger.info(
            "Removing worktree",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "worktree_path": str(worktree_path),
                    "delete_branch": delete_branch,
                    "delete_remote_branch": delete_remote_branch,
                    "force": force,
                }
            },
        )

        # Check for uncommitted changes
        if not force and self._check_uncommitted_changes(worktree_path):
            raise UncommittedChangesError(
                f"Worktree for issue #{issue_number} has uncommitted changes. "
                "Use force=True to remove anyway."
            )

        # Get branch name before removing worktree
        branch_name = self._get_branch_from_worktree(worktree_path)

        # Remove worktree
        remove_args = ["worktree", "remove"]
        if force:
            remove_args.append("--force")
        remove_args.append(str(worktree_path))

        self.git.run_command(remove_args)

        logger.info(
            "Worktree removed",
            extra={
                "context": {
                    "worktree_path": str(worktree_path),
                }
            },
        )

        # Delete local branch if requested
        branch_delete_error = None
        if delete_branch:
            try:
                self.git.run_command(["branch", "-D", branch_name])
                logger.info(
                    "Branch deleted",
                    extra={"context": {"branch_name": branch_name}},
                )
            except Exception as e:
                branch_delete_error = str(e)
                logger.warning(
                    "Branch delete failed",
                    extra={
                        "context": {
                            "branch_name": branch_name,
                            "error": branch_delete_error,
                        }
                    },
                )

        # Delete remote branch if requested
        remote_delete_error = None
        if delete_remote_branch:
            try:
                result = self.git.run_command(
                    ["push", "origin", "--delete", branch_name],
                    check=False,
                )
                if result.returncode == 0:
                    logger.info(
                        "Remote branch deleted",
                        extra={"context": {"branch_name": branch_name}},
                    )
                else:
                    remote_delete_error = result.stderr.strip()
            except Exception as e:
                remote_delete_error = str(e)
                logger.warning(
                    "Remote branch delete failed",
                    extra={
                        "context": {
                            "branch_name": branch_name,
                            "error": remote_delete_error,
                        }
                    },
                )

        # Determine result status
        if branch_delete_error or remote_delete_error:
            return OperationResult(
                status=OperationStatus.PARTIAL,
                message=f"Worktree removed but branch cleanup failed: "
                f"{branch_delete_error or remote_delete_error}",
                worktree=None,
                retry_possible=True,
            )

        return OperationResult(
            status=OperationStatus.SUCCESS,
            message=f"Worktree for issue #{issue_number} removed successfully",
            worktree=None,
            retry_possible=False,
        )

    # =========================================================================
    # Query Methods
    # =========================================================================

    def _run_git_command(self, args: list[str], **kwargs: Any) -> str:
        """
        Run a git command and return stdout.

        Helper for query methods that need command output.

        Args:
            args: Git command arguments
            **kwargs: Additional args passed to run_command

        Returns:
            Command stdout as string
        """
        result = self.git.run_command(args, **kwargs)
        return result.stdout

    def _parse_worktree_list(self, output: str) -> list[Worktree]:
        """
        Parse git worktree list --porcelain output.

        Format:
            worktree /path/to/worktree
            HEAD <sha>
            branch refs/heads/<name>

        Args:
            output: Raw porcelain output

        Returns:
            List of Worktree objects (excluding main repo)
        """
        worktrees: list[Worktree] = []
        current: dict[str, str] = {}

        for line in output.strip().split("\n"):
            if not line:
                # End of worktree block
                if current and current.get("worktree") != str(self.repo_path):
                    wt = self._create_worktree_from_parsed(current)
                    if wt:
                        worktrees.append(wt)
                current = {}
                continue

            if line.startswith("worktree "):
                current["worktree"] = line[9:]
            elif line.startswith("HEAD "):
                current["head"] = line[5:]
            elif line.startswith("branch "):
                current["branch"] = line[7:].replace("refs/heads/", "")

        # Handle last worktree if no trailing newline
        if current and current.get("worktree") != str(self.repo_path):
            wt = self._create_worktree_from_parsed(current)
            if wt:
                worktrees.append(wt)

        return worktrees

    def _create_worktree_from_parsed(self, data: dict[str, str]) -> Worktree | None:
        """
        Create Worktree from parsed data.

        Args:
            data: Dict with worktree, head, branch keys

        Returns:
            Worktree if valid feature worktree, None otherwise
        """
        path = Path(data.get("worktree", ""))
        branch_name = data.get("branch", "")

        # Skip if not a valid path or branch
        if not path or not branch_name:
            return None

        # Parse issue number and feature name from branch
        # Pattern: {issue_number}-{feature_name}
        match = re.match(r"^(\d+)-(.+)$", branch_name)
        if not match:
            return None

        issue_number = int(match.group(1))
        feature_name = match.group(2)

        # Check if worktree is clean
        is_clean = not self._check_uncommitted_changes(path)

        return Worktree(
            issue_number=issue_number,
            feature_name=feature_name,
            path=path,
            main_repo_path=self.repo_path,
            branch_name=branch_name,
            is_clean=is_clean,
            created_at=datetime.now(UTC),
        )

    def list_worktrees(self) -> list[Worktree]:
        """
        List all feature worktrees.

        Returns:
            List of Worktree objects (excluding main repository)
        """
        output = self._run_git_command(["worktree", "list", "--porcelain"])
        return self._parse_worktree_list(output)

    def get_worktree(self, issue_number: int) -> Worktree | None:
        """
        Get worktree by issue number.

        Args:
            issue_number: Issue number to find

        Returns:
            Worktree if found, None otherwise
        """
        worktrees = self.list_worktrees()
        for wt in worktrees:
            if wt.issue_number == issue_number:
                return wt
        return None

    def _parse_branch_info(self, output: str, branch_name: str) -> Branch | None:
        """
        Parse git branch -vv output for a specific branch.

        Format:
            * branch-name <sha> [remote/branch: ahead N, behind M] message

        Args:
            output: Raw branch -vv output
            branch_name: Branch to find

        Returns:
            Branch if found, None otherwise
        """
        for line in output.strip().split("\n"):
            if not line:
                continue

            # Strip leading * and whitespace
            clean_line = line.lstrip("* ").strip()
            if not clean_line:
                continue

            # Check if this is the branch we're looking for
            parts = clean_line.split()
            if not parts or parts[0] != branch_name:
                continue

            # Parse the line
            is_local = True
            remote = None
            remote_branch = None
            ahead = 0
            behind = 0
            is_remote = False

            # Look for tracking info [origin/branch: ahead N, behind M]
            tracking_match = re.search(r"\[([^/]+)/([^:\]]+)(?::\s*([^\]]+))?\]", line)
            if tracking_match:
                remote = tracking_match.group(1)
                remote_branch = tracking_match.group(2)
                is_remote = True

                # Parse ahead/behind
                if tracking_match.group(3):
                    tracking_info = tracking_match.group(3)
                    ahead_match = re.search(r"ahead\s+(\d+)", tracking_info)
                    behind_match = re.search(r"behind\s+(\d+)", tracking_info)
                    if ahead_match:
                        ahead = int(ahead_match.group(1))
                    if behind_match:
                        behind = int(behind_match.group(1))

            return Branch(
                name=branch_name,
                remote=remote,
                remote_branch=remote_branch,
                is_local=is_local,
                is_remote=is_remote,
                is_merged=self._is_branch_merged(branch_name),
                ahead=ahead,
                behind=behind,
            )

        return None

    def _is_branch_merged(self, branch_name: str) -> bool:
        """
        Check if branch is merged into main.

        Args:
            branch_name: Branch to check

        Returns:
            True if branch is merged into main
        """
        result = self.git.run_command(
            ["branch", "--merged", "main"],
            check=False,
        )
        merged_branches = result.stdout.strip().split("\n")
        return any(branch_name == b.strip().lstrip("* ") for b in merged_branches)

    def get_branch(self, branch_name: str) -> Branch | None:
        """
        Get branch info.

        Args:
            branch_name: Branch name to look up

        Returns:
            Branch if found, None otherwise
        """
        output = self._run_git_command(["branch", "-vv"])
        return self._parse_branch_info(output, branch_name)
