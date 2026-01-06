# Module Documentation

Detailed documentation for Farmer Code library modules.

## Module Index

| Module | Purpose | Source | Spec |
|--------|---------|--------|------|
| [GitHub Integration](./github-integration.md) | GitHub API operations | [`src/github_integration/`](../../src/github_integration/) | [001](../../specs/001-github-integration-core/) |
| [Worktree Manager](./worktree-manager.md) | Git worktree management | [`src/worktree_manager/`](../../src/worktree_manager/) | [002](../../specs/002-git-worktree-manager/) |

> **Note**: Orchestrator and Agent Hub are now deployed as services. See [Services Documentation](../services/README.md).

## Module Organization

Each module follows this structure:

```
src/[module]/
├── __init__.py      # Public API exports
├── README.md        # Quick start and API reference
├── models.py        # Pydantic data models
├── service.py       # Main service class
├── exceptions.py    # Module-specific errors
└── ...              # Additional components
```

## Documentation Structure

Each module has two levels of documentation:

1. **Source README** (`src/[module]/README.md`)
   - Quick start guide
   - API reference
   - Usage examples
   - Error handling

2. **Extended Docs** (`docs/modules/[module-name].md`)
   - Architecture details
   - Integration guide
   - Advanced usage
   - Design decisions

## Quick Start

### Using a Module

```python
from github_integration import GitHubService

service = GitHubService(token="...")
repo = service.get_repository("owner/repo")
```

## Module Status

| Module | Status | Test Coverage |
|--------|--------|---------------|
| github_integration | Stable | 85% |
| worktree_manager | Stable | 88% |
