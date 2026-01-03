# Research: Git Worktree Manager

**Feature**: 002-git-worktree-manager
**Date**: 2026-01-03
**Status**: Complete

## Research Topics

### 1. Git Worktree Best Practices

**Decision**: Use `git worktree add` with explicit branch creation/checkout

**Rationale**:
- Git worktrees allow multiple working directories from a single repository
- Each worktree has its own index and working tree
- Worktrees share the object store (saves disk space)
- Worktrees can be in sibling directories (not nested)

**Key Commands**:
```bash
# Create worktree with new branch from main
git worktree add -b <branch> <path> main

# Create worktree with existing branch
git worktree add <path> <branch>

# List worktrees
git worktree list

# Remove worktree
git worktree remove <path>

# Prune stale worktree references
git worktree prune
```

**Alternatives Considered**:
- Multiple clones: Rejected - uses more disk space, harder to manage
- Git submodules: Rejected - different use case (external dependencies)

### 2. Subprocess Patterns for Git CLI

**Decision**: Use `subprocess.run()` with capture_output and check for errors

**Rationale**:
- Simplest approach per constitution (Principle VI)
- Direct mapping to git commands
- Full control over error handling
- No external dependencies beyond stdlib

**Pattern**:
```python
import subprocess
from pathlib import Path

def run_git_command(
    args: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run git command and return result."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,  # Handle errors ourselves
    )
    if check and result.returncode != 0:
        raise GitCommandError(
            command=args,
            returncode=result.returncode,
            stderr=result.stderr,
        )
    return result
```

**Alternatives Considered**:
- GitPython library: Rejected - adds external dependency, more complex API
- pygit2: Rejected - requires libgit2 C library, harder to install
- dulwich: Rejected - pure Python but limited worktree support

### 3. Error Handling Patterns

**Decision**: Custom exception hierarchy mirroring github_integration module

**Rationale**:
- Consistent with existing codebase patterns
- Clear error types for different failure modes
- Enables precise error handling by callers

**Exception Hierarchy**:
```python
WorktreeError (base)
├── GitNotFoundError          # git not in PATH
├── GitCommandError           # git command failed
├── BranchExistsError         # branch already exists
├── BranchNotFoundError       # branch doesn't exist
├── WorktreeExistsError       # worktree path already exists
├── WorktreeNotFoundError     # worktree not registered
├── UncommittedChangesError   # worktree has dirty state
├── PushError                 # push to remote failed
└── PermissionError           # filesystem permission issue
```

### 4. Path Handling for Sibling Directories

**Decision**: Use pathlib.Path with resolve() for absolute paths

**Rationale**:
- Sibling worktrees should be at `../{repo_name}-{issue_number}-{feature_name}/`
- Must handle spaces in paths (quote properly)
- Cross-platform compatibility (Windows/macOS/Linux)

**Pattern**:
```python
def get_worktree_path(
    repo_path: Path,
    issue_number: int,
    feature_name: str,
) -> Path:
    """Get sibling directory path for worktree."""
    repo_name = repo_path.name
    worktree_name = f"{repo_name}-{issue_number}-{feature_name}"
    return (repo_path.parent / worktree_name).resolve()
```

### 5. Idempotency Patterns

**Decision**: Check state before operations, return success if already in desired state

**Rationale**:
- FR-012 requires idempotent operations where possible
- Prevents errors on re-running same operation
- Enables safe retries

**Patterns**:
- `create_worktree()`: Check if worktree exists first, return existing if found
- `init_plans()`: Check if `.plans/` exists, skip if present
- `commit_and_push()`: Return early if nothing to commit

### 6. Testing with Real Git Operations

**Decision**: Use pytest fixtures with temporary git repositories

**Rationale**:
- Worktree operations need real git repos
- Can't mock git internals meaningfully
- Use farmer1st/farmcode-tests for E2E tests

**Fixture Pattern**:
```python
@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    """Create temporary git repository for testing."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, check=True)
    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repo")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
    return repo_path
```

## NEEDS CLARIFICATION Resolutions

All technical questions resolved through research. No remaining clarifications needed.

## Summary

| Topic | Decision | Confidence |
|-------|----------|------------|
| Git CLI approach | subprocess.run() | High |
| Dependencies | stdlib only (subprocess, pathlib) | High |
| Error handling | Custom exception hierarchy | High |
| Path handling | pathlib.Path with resolve() | High |
| Idempotency | Check-before-operate pattern | High |
| Testing | Real git repos in temp directories | High |
