# Data Model: Git Worktree Manager

**Feature**: 002-git-worktree-manager
**Date**: 2026-01-03
**Status**: Complete

## Overview

This feature manages git worktrees and branches for isolated development. All entities are Pydantic models with frozen=True (immutable) following the pattern established in github_integration.

## Entities

### Worktree

Represents a git worktree linked to a specific branch and issue.

```python
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

class Worktree(BaseModel):
    """Represents a git worktree with associated metadata."""

    model_config = ConfigDict(frozen=True)

    # Identity
    issue_number: int = Field(..., description="Associated issue number", gt=0)
    feature_name: str = Field(..., description="Feature short name (slug)", min_length=1, max_length=100)

    # Paths
    path: Path = Field(..., description="Absolute path to worktree directory")
    main_repo_path: Path = Field(..., description="Absolute path to main repository")

    # Branch info
    branch_name: str = Field(..., description="Branch name (e.g., '123-add-auth')")

    # State
    is_clean: bool = Field(True, description="True if no uncommitted changes")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")

    @property
    def plans_path(self) -> Path:
        """Get path to .plans/{issue_number}/ directory."""
        return self.path / ".plans" / str(self.issue_number)
```

**Validation Rules**:
- `issue_number` must be positive integer
- `feature_name` must be 1-100 chars, lowercase with hyphens
- `path` must be absolute (enforced at runtime)
- `branch_name` follows pattern `{issue_number}-{feature_name}`

**State Transitions**:
- `is_clean`: True → False (on file changes), False → True (after commit)

---

### Branch

Represents a git branch with tracking and merge status.

```python
class Branch(BaseModel):
    """Represents a git branch with remote tracking info."""

    model_config = ConfigDict(frozen=True)

    # Identity
    name: str = Field(..., description="Branch name", min_length=1, max_length=256)

    # Tracking
    remote: str | None = Field(None, description="Remote name (e.g., 'origin')")
    remote_branch: str | None = Field(None, description="Remote branch name if tracking")

    # Status
    is_local: bool = Field(True, description="True if branch exists locally")
    is_remote: bool = Field(False, description="True if branch exists on remote")
    is_merged: bool = Field(False, description="True if merged into main")
    ahead: int = Field(0, description="Commits ahead of remote", ge=0)
    behind: int = Field(0, description="Commits behind remote", ge=0)

    @property
    def is_tracking(self) -> bool:
        """Check if branch tracks a remote branch."""
        return self.remote is not None and self.remote_branch is not None

    @property
    def is_synced(self) -> bool:
        """Check if local and remote are in sync."""
        return self.ahead == 0 and self.behind == 0
```

**Validation Rules**:
- `name` must not contain spaces or special chars (git restriction)
- `ahead`/`behind` must be non-negative

---

### PlansFolder

Represents the `.plans/{issue_number}/` directory structure.

```python
class PlansFolder(BaseModel):
    """Represents the .plans/{issue_number}/ structure."""

    model_config = ConfigDict(frozen=True)

    # Identity
    issue_number: int = Field(..., description="Associated issue number", gt=0)
    worktree_path: Path = Field(..., description="Path to parent worktree")

    # Contents
    has_specs: bool = Field(False, description="True if specs/ subdirectory exists")
    has_plans: bool = Field(False, description="True if plans/ subdirectory exists")
    has_reviews: bool = Field(False, description="True if reviews/ subdirectory exists")
    has_readme: bool = Field(False, description="True if README.md exists")

    @property
    def path(self) -> Path:
        """Get full path to .plans/{issue_number}/."""
        return self.worktree_path / ".plans" / str(self.issue_number)

    @property
    def is_complete(self) -> bool:
        """Check if all required subdirectories exist."""
        return all([self.has_specs, self.has_plans, self.has_reviews, self.has_readme])
```

**Directory Structure**:
```
.plans/
└── {issue_number}/
    ├── README.md       # Feature metadata
    ├── specs/          # Specifications
    ├── plans/          # Implementation plans
    └── reviews/        # Review artifacts
```

---

## Request Models

### CreateWorktreeRequest

```python
class CreateWorktreeRequest(BaseModel):
    """Request to create a new worktree."""

    issue_number: int = Field(..., description="Issue number", gt=0)
    feature_name: str = Field(
        ...,
        description="Feature short name",
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$"
    )

    @property
    def branch_name(self) -> str:
        """Generate branch name from issue and feature."""
        return f"{self.issue_number}-{self.feature_name}"
```

### CommitRequest

```python
class CommitRequest(BaseModel):
    """Request to commit and push changes."""

    message: str = Field(..., description="Commit message", min_length=1, max_length=500)
    push: bool = Field(True, description="Whether to push after commit")
```

### RemoveWorktreeRequest

```python
class RemoveWorktreeRequest(BaseModel):
    """Request to remove a worktree."""

    issue_number: int = Field(..., description="Issue number", gt=0)
    delete_branch: bool = Field(False, description="Delete local branch after removal")
    delete_remote_branch: bool = Field(False, description="Delete remote branch after removal")
    force: bool = Field(False, description="Force removal even with uncommitted changes")
```

---

## Result Models

### OperationResult

```python
from enum import Enum

class OperationStatus(str, Enum):
    """Status of a worktree operation."""
    SUCCESS = "success"
    PARTIAL = "partial"  # Some operations succeeded, some failed
    FAILED = "failed"

class OperationResult(BaseModel):
    """Result of a worktree operation."""

    model_config = ConfigDict(frozen=True)

    status: OperationStatus = Field(..., description="Operation outcome")
    message: str = Field(..., description="Human-readable result message")
    worktree: Worktree | None = Field(None, description="Worktree if operation created/affected one")
    retry_possible: bool = Field(False, description="True if failed operation can be retried")
```

### CommitResult

```python
class CommitResult(BaseModel):
    """Result of a commit operation."""

    model_config = ConfigDict(frozen=True)

    commit_sha: str | None = Field(None, description="SHA of created commit")
    pushed: bool = Field(False, description="True if push succeeded")
    nothing_to_commit: bool = Field(False, description="True if working tree was clean")
    push_error: str | None = Field(None, description="Push error message if push failed")
```

---

## Relationships

```
Worktree 1:1 Branch       # Each worktree has exactly one branch
Worktree 1:1 PlansFolder  # Each worktree has exactly one .plans/{issue} folder
Branch N:1 Remote         # Many branches can track same remote
```

## Storage

This feature has no persistent storage. All data comes from:
- Git CLI commands (`git worktree list`, `git branch -v`, etc.)
- Filesystem inspection (pathlib.Path operations)

State is computed fresh on each operation, not cached.
