"""
Pydantic Models for Git Worktree Manager.

Immutable (frozen) models for worktrees, branches, and request/response types.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    pass  # For forward references


# =============================================================================
# US1: Worktree, Branch, CreateWorktreeRequest
# =============================================================================


class Worktree(BaseModel):
    """
    Represents a git worktree with associated metadata.

    Each worktree is linked to a specific issue number and feature branch.
    The worktree directory is created as a sibling to the main repository.
    """

    model_config = ConfigDict(frozen=True)

    # Identity
    issue_number: int = Field(..., description="Associated issue number", gt=0)
    feature_name: str = Field(
        ..., description="Feature short name (slug)", min_length=1, max_length=100
    )

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


class Branch(BaseModel):
    """
    Represents a git branch with remote tracking info.

    Tracks whether the branch exists locally, remotely, and its sync status.
    """

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


class CreateWorktreeRequest(BaseModel):
    """
    Request to create a new worktree.

    Validates issue_number and feature_name, provides computed branch_name.
    """

    issue_number: int = Field(..., description="Issue number", gt=0)
    feature_name: str = Field(
        ...,
        description="Feature short name",
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$",
    )

    @property
    def branch_name(self) -> str:
        """Generate branch name from issue and feature."""
        return f"{self.issue_number}-{self.feature_name}"


# =============================================================================
# US2: PlansFolder
# =============================================================================


class PlansFolder(BaseModel):
    """
    Represents the .plans/{issue_number}/ structure.

    Contains subdirectories for specs, plans, and reviews, plus a README.
    """

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


# =============================================================================
# US3: CommitRequest and CommitResult
# =============================================================================


class CommitRequest(BaseModel):
    """
    Request to commit and push changes.

    Used for staging, committing, and optionally pushing changes.
    """

    message: str = Field(..., description="Commit message", min_length=1, max_length=500)
    push: bool = Field(True, description="Whether to push after commit")


class CommitResult(BaseModel):
    """
    Result of a commit operation.

    Captures commit SHA, push status, and any errors.
    """

    model_config = ConfigDict(frozen=True)

    commit_sha: str | None = Field(None, description="SHA of created commit")
    pushed: bool = Field(False, description="True if push succeeded")
    nothing_to_commit: bool = Field(False, description="True if working tree was clean")
    push_error: str | None = Field(None, description="Push error message if push failed")


# =============================================================================
# US4: OperationStatus, OperationResult, RemoveWorktreeRequest
# =============================================================================


class OperationStatus(str, Enum):
    """Status of a worktree operation."""

    SUCCESS = "success"
    PARTIAL = "partial"  # Some operations succeeded, some failed
    FAILED = "failed"


class OperationResult(BaseModel):
    """
    Result of a worktree operation.

    Used for remove and other operations that may partially succeed.
    """

    model_config = ConfigDict(frozen=True)

    status: OperationStatus = Field(..., description="Operation outcome")
    message: str = Field(..., description="Human-readable result message")
    worktree: "Worktree | None" = Field(
        None, description="Worktree if operation created/affected one"
    )
    retry_possible: bool = Field(False, description="True if failed operation can be retried")


class RemoveWorktreeRequest(BaseModel):
    """
    Request to remove a worktree.

    Controls branch deletion and force options.
    """

    issue_number: int = Field(..., description="Issue number", gt=0)
    delete_branch: bool = Field(False, description="Delete local branch after removal")
    delete_remote_branch: bool = Field(False, description="Delete remote branch after removal")
    force: bool = Field(False, description="Force removal even with uncommitted changes")


# Rebuild forward references
OperationResult.model_rebuild()
