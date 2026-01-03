# Git Worktree Manager

Service for managing git branches and worktrees, enabling isolated development environments for each feature.

## Purpose

The Worktree Manager provides a programmatic interface for:
- Creating feature branches from main
- Setting up worktrees in sibling directories for isolated development
- Managing `.plans` folder structure for specifications
- Committing and pushing changes
- Cleaning up worktrees and branches when done

## Installation

```python
# From the project root
from worktree_manager import WorktreeService
```

## Quick Start

```python
from worktree_manager import WorktreeService, UncommittedChangesError

# Initialize for a repository
service = WorktreeService("/path/to/repo")

# Create a worktree for issue #42
worktree = service.create_worktree(
    issue_number=42,
    feature_name="user-auth"
)
# Creates: /path/to/repo-42-user-auth/ with branch 42-user-auth

# Initialize plans folder structure
plans = service.init_plans(worktree.path)
# Creates: .plans/spec.md, .plans/plan.md, .plans/tasks.md

# Commit changes
result = service.commit(
    worktree_path=worktree.path,
    message="feat: add authentication flow"
)

# Push to remote
service.push(worktree_path=worktree.path)

# Clean up when done
service.remove_worktree(worktree.path)
service.delete_branch("42-user-auth")
```

## Public API

| Method | Description | Returns |
|--------|-------------|---------|
| `create_worktree(issue_number, feature_name)` | Create branch and worktree | `Worktree` |
| `init_plans(worktree_path)` | Initialize .plans folder | `PlansFolder` |
| `commit(worktree_path, message)` | Commit all changes | `CommitResult` |
| `push(worktree_path, set_upstream)` | Push to remote | `OperationResult` |
| `remove_worktree(worktree_path, force)` | Remove worktree directory | `OperationResult` |
| `delete_branch(branch_name, force, delete_remote)` | Delete local/remote branch | `OperationResult` |
| `list_worktrees()` | List all worktrees | `list[Worktree]` |
| `get_worktree(worktree_path)` | Get specific worktree | `Worktree \| None` |
| `get_branch(branch_name)` | Get branch details | `Branch \| None` |

## Models

### Worktree
```python
Worktree(
    path: Path,           # Absolute path to worktree
    branch: str,          # Branch name
    commit: str,          # Current commit SHA
    is_main: bool = False # True if this is the main worktree
)
```

### PlansFolder
```python
PlansFolder(
    path: Path,           # Path to .plans directory
    spec_path: Path,      # Path to spec.md
    plan_path: Path,      # Path to plan.md
    tasks_path: Path      # Path to tasks.md
)
```

### CommitResult
```python
CommitResult(
    commit_sha: str,      # SHA of created commit
    message: str,         # Commit message used
    files_changed: int    # Number of files in commit
)
```

### OperationResult
```python
OperationResult(
    status: OperationStatus,  # SUCCESS or FAILURE
    message: str,             # Human-readable message
    details: dict | None      # Additional context
)
```

## Error Handling

All errors inherit from `WorktreeError`:

| Error | When Raised |
|-------|-------------|
| `GitNotFoundError` | Git is not installed or not in PATH |
| `NotARepositoryError` | Path is not a git repository |
| `GitCommandError` | Git command failed unexpectedly |
| `MainBranchNotFoundError` | Main branch doesn't exist |
| `BranchExistsError` | Branch already exists locally |
| `BranchNotFoundError` | Branch doesn't exist |
| `WorktreeExistsError` | Worktree directory already exists |
| `WorktreeNotFoundError` | Worktree not found |
| `UncommittedChangesError` | Worktree has uncommitted changes |
| `PushError` | Push to remote failed |

Example error handling:
```python
from worktree_manager import (
    WorktreeService,
    BranchExistsError,
    WorktreeExistsError,
)

try:
    worktree = service.create_worktree(42, "feature")
except BranchExistsError:
    print("Branch already exists - checking out existing branch")
except WorktreeExistsError:
    print("Worktree already exists at that path")
```

## Contracts

For detailed interface specifications, see:
- [`specs/002-git-worktree-manager/contracts/`](../../specs/002-git-worktree-manager/contracts/)

## Requirements

- Python 3.11+
- Git installed and in PATH
- Repository must have a `main` branch
