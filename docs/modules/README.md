# Module Documentation

Detailed documentation for each Farmer Code module.

## Module Index

| Module | Purpose | Source | Spec |
|--------|---------|--------|------|
| [GitHub Integration](./github-integration.md) | GitHub API operations | [`src/github_integration/`](../../src/github_integration/) | [001](../../specs/001-github-integration-core/) |
| [Worktree Manager](./worktree-manager.md) | Git worktree management | [`src/worktree_manager/`](../../src/worktree_manager/) | [002](../../specs/002-git-worktree-manager/) |
| [Orchestrator](./orchestrator.md) | SDLC workflow state machine | [`src/orchestrator/`](../../src/orchestrator/) | [003](../../specs/003-orchestrator-state-machine/) |
| [Agent Hub](./agent-hub.md) | Central agent coordination | [`src/agent_hub/`](../../src/agent_hub/) | [005](../../specs/005-agent-hub-refactor/) |

> **Note**: For the services-based architecture (Feature 008), see [Services Documentation](../services/README.md).

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
from [module] import MainService, Request

service = MainService(config)
result = service.operation(Request(...))
```

### Module Dependencies

```mermaid
graph LR
    GI[github_integration] --> ORC[orchestrator]
    WM[worktree_manager] --> ORC
    AH[agent_hub] --> ORC

    style ORC fill:#f9f
```

## Module Status

| Module | Status | Test Coverage | User Journeys |
|--------|--------|---------------|---------------|
| github_integration | Stable | 85% | ORC-001, ORC-002 |
| worktree_manager | Stable | 88% | WT-001 to WT-004 |
| orchestrator | Stable | 84% | ORC-005 |
| agent_hub | Stable | 84% | AH-001 to AH-005 |

## Adding a New Module

When adding a new module:

1. Create `src/[module]/` with standard structure
2. Add `src/[module]/README.md` with quick start
3. Add `docs/modules/[module-name].md` with extended docs
4. Update this index file
5. Update `docs/architecture/` if needed
