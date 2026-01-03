# API Contract: WorktreeService

**Feature**: 002-git-worktree-manager
**Date**: 2026-01-03
**Status**: Complete

## Overview

The `WorktreeService` provides a high-level Python API for managing git worktrees, branches, and the `.plans/` folder structure. This is a local service (not HTTP/REST) designed for orchestrator integration.

## Service Interface

```python
class WorktreeService:
    """
    High-level service for git worktree operations.

    All methods are synchronous and operate on the local filesystem.
    Uses git CLI internally via subprocess.
    """

    def __init__(self, repo_path: str | Path) -> None:
        """
        Initialize service for a git repository.

        Args:
            repo_path: Path to the git repository root

        Raises:
            GitNotFoundError: If git is not installed or not in PATH
            NotARepositoryError: If repo_path is not a git repository
            PermissionError: If no write access to repository
        """
```

---

## US1: Create Branch and Worktree

### create_worktree

```python
def create_worktree(
    self,
    issue_number: int,
    feature_name: str,
) -> Worktree:
    """
    Create a new branch and worktree for a feature.

    Creates branch '{issue_number}-{feature_name}' from main branch
    and checks it out in sibling directory.

    Args:
        issue_number: GitHub issue number (positive integer)
        feature_name: Feature slug (lowercase, hyphenated, 1-100 chars)

    Returns:
        Worktree: Created worktree with path and branch info

    Raises:
        ValueError: If issue_number <= 0 or feature_name invalid
        WorktreeExistsError: If worktree directory already exists
        MainBranchNotFoundError: If 'main' branch doesn't exist
        GitCommandError: If git command fails

    Idempotency:
        If worktree already exists for this issue/feature, raises
        WorktreeExistsError. Does NOT return existing worktree.

    Side Effects:
        - Creates branch '{issue_number}-{feature_name}' from main
        - Creates directory '../{repo_name}-{issue_number}-{feature_name}/'
        - Registers worktree in git

    Example:
        >>> service = WorktreeService("/path/to/farmcode")
        >>> wt = service.create_worktree(123, "add-auth")
        >>> print(wt.path)
        /path/to/farmcode-123-add-auth
        >>> print(wt.branch_name)
        123-add-auth
    """
```

### create_worktree_from_existing

```python
def create_worktree_from_existing(
    self,
    issue_number: int,
    feature_name: str,
    branch_name: str | None = None,
) -> Worktree:
    """
    Create worktree from existing remote branch.

    Fetches and checks out existing branch into new worktree.
    If branch_name not provided, uses '{issue_number}-{feature_name}'.

    Args:
        issue_number: GitHub issue number
        feature_name: Feature slug
        branch_name: Optional explicit branch name to checkout

    Returns:
        Worktree: Created worktree

    Raises:
        ValueError: If inputs invalid
        WorktreeExistsError: If worktree directory exists
        BranchNotFoundError: If remote branch doesn't exist
        GitCommandError: If git command fails
    """
```

---

## US2: Initialize Plans Structure

### init_plans

```python
def init_plans(
    self,
    issue_number: int,
    feature_title: str | None = None,
) -> PlansFolder:
    """
    Initialize .plans/{issue_number}/ structure in worktree.

    Creates directory structure and README.md with feature metadata.

    Args:
        issue_number: GitHub issue number (must have matching worktree)
        feature_title: Optional title for README.md (defaults to branch name)

    Returns:
        PlansFolder: Initialized folder with all subdirectories

    Raises:
        ValueError: If issue_number <= 0
        WorktreeNotFoundError: If no worktree exists for this issue
        PermissionError: If no write access to worktree

    Idempotency:
        If .plans/{issue_number}/ already exists, returns existing
        PlansFolder without modification. Safe to call multiple times.

    Created Structure:
        .plans/
        └── {issue_number}/
            ├── README.md       # Feature metadata
            ├── specs/          # Empty directory
            ├── plans/          # Empty directory
            └── reviews/        # Empty directory

    README.md Contents:
        # Feature: {feature_title or branch_name}

        **Issue**: #{issue_number}
        **Created**: {date}
        **Status**: In Progress

        ## Artifacts

        - `specs/` - Feature specifications
        - `plans/` - Implementation plans
        - `reviews/` - Review documents
    """
```

### get_plans

```python
def get_plans(
    self,
    issue_number: int,
) -> PlansFolder | None:
    """
    Get PlansFolder for an issue if it exists.

    Args:
        issue_number: GitHub issue number

    Returns:
        PlansFolder if exists, None otherwise

    Raises:
        ValueError: If issue_number <= 0
    """
```

---

## US3: Commit and Push Changes

### commit_and_push

```python
def commit_and_push(
    self,
    issue_number: int,
    message: str,
    push: bool = True,
) -> CommitResult:
    """
    Stage, commit, and optionally push all changes in worktree.

    Args:
        issue_number: GitHub issue number (must have matching worktree)
        message: Commit message (1-500 chars)
        push: Whether to push to remote (default True)

    Returns:
        CommitResult with commit SHA and push status

    Raises:
        ValueError: If issue_number <= 0 or message empty/too long
        WorktreeNotFoundError: If no worktree for this issue
        GitCommandError: If commit fails

    Partial Failure:
        If commit succeeds but push fails (network error), returns
        CommitResult with pushed=False and push_error message.
        Commit is NOT rolled back. Caller can retry push.

    Nothing to Commit:
        If working tree is clean, returns CommitResult with
        nothing_to_commit=True and no commit_sha.

    Example:
        >>> result = service.commit_and_push(123, "Add user model")
        >>> print(result.commit_sha)
        abc123def456...
        >>> print(result.pushed)
        True

        >>> result = service.commit_and_push(123, "No changes")
        >>> print(result.nothing_to_commit)
        True
    """
```

### push

```python
def push(
    self,
    issue_number: int,
) -> bool:
    """
    Push commits to remote for worktree.

    Args:
        issue_number: GitHub issue number

    Returns:
        True if push succeeded

    Raises:
        ValueError: If issue_number <= 0
        WorktreeNotFoundError: If no worktree for this issue
        PushError: If push fails (network, permissions, etc.)
    """
```

---

## US4: Remove Worktree and Cleanup

### remove_worktree

```python
def remove_worktree(
    self,
    issue_number: int,
    delete_branch: bool = False,
    delete_remote_branch: bool = False,
    force: bool = False,
) -> OperationResult:
    """
    Remove worktree and optionally delete branches.

    Args:
        issue_number: GitHub issue number
        delete_branch: Also delete local branch (default False)
        delete_remote_branch: Also delete remote branch (default False)
        force: Force removal even with uncommitted changes (default False)

    Returns:
        OperationResult with status and message

    Raises:
        ValueError: If issue_number <= 0
        WorktreeNotFoundError: If no worktree for this issue
        UncommittedChangesError: If uncommitted changes and force=False

    Partial Failure:
        If worktree removal succeeds but branch deletion fails,
        returns OperationResult with status=PARTIAL.

    Safety:
        - Checks for uncommitted changes before removal
        - Requires force=True to delete dirty worktree
        - delete_remote_branch only works if branch is merged

    Example:
        >>> result = service.remove_worktree(123, delete_branch=True)
        >>> print(result.status)
        OperationStatus.SUCCESS
        >>> print(result.message)
        "Worktree removed and local branch deleted"
    """
```

---

## Query Methods

### list_worktrees

```python
def list_worktrees(self) -> list[Worktree]:
    """
    List all worktrees managed by this repository.

    Returns:
        List of Worktree objects (may be empty)

    Note:
        Only returns worktrees in sibling directories following
        the naming convention. Does not return the main worktree.
    """
```

### get_worktree

```python
def get_worktree(
    self,
    issue_number: int,
) -> Worktree | None:
    """
    Get worktree for specific issue.

    Args:
        issue_number: GitHub issue number

    Returns:
        Worktree if exists, None otherwise
    """
```

### get_branch

```python
def get_branch(
    self,
    name: str,
) -> Branch | None:
    """
    Get branch info by name.

    Args:
        name: Branch name

    Returns:
        Branch with tracking and merge status, or None if not found
    """
```

---

## Error Handling

All methods raise specific exceptions for error conditions:

| Exception | When Raised |
|-----------|-------------|
| `GitNotFoundError` | git not installed or not in PATH |
| `NotARepositoryError` | Path is not a git repository |
| `MainBranchNotFoundError` | Main branch doesn't exist |
| `BranchExistsError` | Trying to create existing branch |
| `BranchNotFoundError` | Branch doesn't exist |
| `WorktreeExistsError` | Worktree path already exists |
| `WorktreeNotFoundError` | No worktree for issue number |
| `UncommittedChangesError` | Dirty working tree blocks operation |
| `PushError` | Push to remote failed |
| `GitCommandError` | Generic git command failure |

---

## Performance Expectations

| Operation | Target | Notes |
|-----------|--------|-------|
| create_worktree | <30s | For repos up to 1GB |
| init_plans | <1s | Filesystem only |
| commit_and_push | <10s | Depends on changes and network |
| remove_worktree | <5s | Filesystem only |
| list_worktrees | <1s | git worktree list |
| get_worktree | <1s | Single lookup |

---

## Thread Safety

This service is NOT thread-safe. Git operations should be serialized at the caller level if concurrent access is needed.

---

## Test Repository

E2E tests use `farmer1st/farmcode-tests` repository for real git operations.
