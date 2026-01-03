# Quickstart: Git Worktree Manager

**Feature**: 002-git-worktree-manager
**Date**: 2026-01-03

## Overview

The Git Worktree Manager provides isolated development environments for each feature by managing git worktrees in sibling directories.

## Quick Usage

### 1. Create a Worktree for New Feature

```python
from worktree_manager import WorktreeService

# Initialize service with main repository path
service = WorktreeService("/path/to/farmcode")

# Create worktree for issue #123
worktree = service.create_worktree(
    issue_number=123,
    feature_name="add-user-auth",
)

print(f"Worktree created at: {worktree.path}")
# Output: Worktree created at: /path/to/farmcode-123-add-user-auth

print(f"Branch: {worktree.branch_name}")
# Output: Branch: 123-add-user-auth
```

### 2. Initialize Plans Structure

```python
# Initialize .plans/123/ structure
plans = service.init_plans(issue_number=123)

print(f"Plans folder: {plans.path}")
# Output: Plans folder: /path/to/farmcode-123-add-user-auth/.plans/123

# Check structure is complete
print(f"Ready: {plans.is_complete}")
# Output: Ready: True
```

### 3. Commit and Push Changes

```python
# After making changes in the worktree...
result = service.commit_and_push(
    issue_number=123,
    message="feat: add user authentication model",
)

if result.pushed:
    print(f"Committed and pushed: {result.commit_sha}")
elif result.nothing_to_commit:
    print("No changes to commit")
else:
    print(f"Commit OK, push failed: {result.push_error}")
```

### 4. Cleanup After Merge

```python
# Remove worktree and branches after feature is merged
result = service.remove_worktree(
    issue_number=123,
    delete_branch=True,
    delete_remote_branch=True,
)

print(result.message)
# Output: Worktree removed and branches deleted
```

## Common Patterns

### Check if Worktree Exists

```python
worktree = service.get_worktree(issue_number=123)
if worktree:
    print(f"Working in: {worktree.path}")
else:
    print("Need to create worktree first")
```

### List All Worktrees

```python
for wt in service.list_worktrees():
    status = "clean" if wt.is_clean else "dirty"
    print(f"Issue #{wt.issue_number}: {wt.branch_name} [{status}]")
```

### Resume Work on Existing Branch

```python
# Checkout existing remote branch
worktree = service.create_worktree_from_existing(
    issue_number=123,
    feature_name="add-user-auth",
)
```

### Force Cleanup Dirty Worktree

```python
# Be careful - discards uncommitted changes!
result = service.remove_worktree(
    issue_number=123,
    force=True,
)
```

## Error Handling

```python
from worktree_manager import (
    WorktreeService,
    WorktreeExistsError,
    WorktreeNotFoundError,
    UncommittedChangesError,
    GitNotFoundError,
)

try:
    service = WorktreeService("/path/to/repo")
except GitNotFoundError:
    print("Git is not installed or not in PATH")

try:
    service.create_worktree(123, "feature")
except WorktreeExistsError:
    print("Worktree already exists for issue #123")

try:
    service.remove_worktree(123)
except UncommittedChangesError:
    print("Cannot remove - uncommitted changes exist")
    print("Use force=True to override")
```

## Integration with GitHub Service

```python
from github_integration import GitHubService
from worktree_manager import WorktreeService

# Setup services
github = GitHubService(...)
worktree = WorktreeService("/path/to/farmcode")

# Get issue and create worktree
issue = github.get_issue(123)
wt = worktree.create_worktree(
    issue_number=issue.number,
    feature_name="add-auth",  # Derived from issue title
)

# Initialize plans
worktree.init_plans(issue.number, feature_title=issue.title)

# ... do work ...

# Commit with reference to issue
worktree.commit_and_push(
    issue_number=123,
    message=f"feat: implement {issue.title.lower()}",
)
```

## Requirements

- Git installed and in PATH
- Write access to repository
- Main branch exists (`main`)
- Sufficient disk space for worktrees
