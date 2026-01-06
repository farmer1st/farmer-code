"""
Git Worktree Manager

Service for managing git branches and worktrees, enabling isolated
development environments for each feature.

Public API:
- WorktreeService: Main service class
- Worktree, Branch, PlansFolder: Entity models
- CreateWorktreeRequest, CommitRequest, RemoveWorktreeRequest: Request models
- CommitResult, OperationResult, OperationStatus: Result models
- Exceptions: WorktreeError and subclasses
"""

# Exports: All public API
from .errors import (
    BranchExistsError,
    BranchNotFoundError,
    GitCommandError,
    GitNotFoundError,
    MainBranchNotFoundError,
    NotARepositoryError,
    PushError,
    UncommittedChangesError,
    WorktreeError,
    WorktreeExistsError,
    WorktreeNotFoundError,
)
from .models import (
    Branch,
    CommitRequest,
    CommitResult,
    CreateWorktreeRequest,
    OperationResult,
    OperationStatus,
    PlansFolder,
    RemoveWorktreeRequest,
    Worktree,
)
from .service import WorktreeService

__all__: list[str] = [
    # Service
    "WorktreeService",
    # Entity Models
    "Worktree",
    "Branch",
    "PlansFolder",
    # Request Models
    "CreateWorktreeRequest",
    "CommitRequest",
    "RemoveWorktreeRequest",
    # Result Models
    "CommitResult",
    "OperationStatus",
    "OperationResult",
    # Errors
    "WorktreeError",
    "GitNotFoundError",
    "NotARepositoryError",
    "GitCommandError",
    "MainBranchNotFoundError",
    "BranchExistsError",
    "BranchNotFoundError",
    "WorktreeExistsError",
    "WorktreeNotFoundError",
    "UncommittedChangesError",
    "PushError",
]
