# Implementation Plan: Git Worktree Manager

**Branch**: `002-git-worktree-manager` | **Date**: 2026-01-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-git-worktree-manager/spec.md`

## Summary

Backend service for managing git branches and worktrees, enabling isolated development environments for each feature. The service wraps git CLI commands in a Python API, providing branch creation from main, worktree management in sibling directories, `.plans/` folder initialization, commit/push operations, and cleanup functionality. This is the second foundation piece for the orchestrator, building on the GitHub Integration Core.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: subprocess (stdlib), pathlib (stdlib), Pydantic v2 (validation)
**Storage**: N/A (operates on filesystem via git)
**Testing**: pytest with contract/integration/unit/e2e test layers
**Target Platform**: Linux/macOS (local development)
**Project Type**: Single project (backend service module)
**Performance Goals**: <30s for worktree creation on 1GB repo, <5s for local operations
**Constraints**: Git must be installed and in PATH, write access to repository required
**Scale/Scope**: Support 50+ concurrent worktrees

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Tests designed before implementation |
| II. Specification-Driven | ✅ PASS | spec.md complete with acceptance scenarios |
| III. Independent User Stories | ✅ PASS | 4 stories (2 P1, 2 P2), each independently testable |
| IV. Human Approval Gates | ✅ PASS | Gate 1 (spec) ready for approval |
| V. Parallel-First Execution | ✅ PASS | US1+US2 can run parallel, US3+US4 can run parallel |
| VI. Simplicity and YAGNI | ✅ PASS | Uses subprocess for git (simplest approach) |
| VII. Versioning | ✅ PASS | Feature branch created, conventional commits used |
| VIII. Technology Stack | ✅ PASS | Python 3.11+, pytest, ruff, mypy per constitution |
| IX. Thin Client Architecture | ✅ N/A | No frontend in this feature |
| X. Security-First | ✅ PASS | No secrets stored, uses existing git credentials |
| XI. Documentation | ✅ PASS | User journeys defined in spec |
| XII. CI/CD | ✅ PASS | Will follow existing CI pipeline |

**Gate Result**: ✅ PASSED - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/002-git-worktree-manager/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── worktree-service.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── github_integration/  # Feature 001 (existing)
│   ├── __init__.py
│   ├── auth.py
│   ├── client.py
│   ├── errors.py
│   ├── logger.py
│   ├── models.py
│   └── service.py
└── worktree_manager/    # Feature 002 (new)
    ├── __init__.py      # Public exports
    ├── errors.py        # Custom exceptions
    ├── models.py        # Pydantic models (Worktree, Branch, PlansFolder)
    ├── git_client.py    # Low-level git CLI wrapper
    └── service.py       # High-level WorktreeService

tests/
├── unit/
│   └── test_worktree_models.py
├── contract/
│   └── test_worktree_service.py
├── integration/
│   └── test_worktree_integration.py
└── e2e/
    └── test_worktree_e2e.py
```

**Structure Decision**: Single project structure following existing `github_integration` pattern. New module `worktree_manager` added to `src/` with same layered architecture (models, errors, client, service).

## Complexity Tracking

> No violations - simplest approach used throughout.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

---

## Phase 0: Research ✅ COMPLETE

**Output**: [research.md](./research.md)

Researched topics:
- Git worktree best practices and commands
- Subprocess patterns for git CLI wrapper
- Error handling patterns (custom exception hierarchy)
- Path handling for sibling directories
- Idempotency patterns (check-before-operate)
- Testing strategy with temporary git repositories

**Decision**: Use subprocess.run() with custom exceptions, stdlib only (no external git libraries).

---

## Phase 1: Design ✅ COMPLETE

**Outputs**:
- [data-model.md](./data-model.md) - Pydantic models (Worktree, Branch, PlansFolder)
- [contracts/worktree-service.md](./contracts/worktree-service.md) - Service API contract
- [quickstart.md](./quickstart.md) - Usage examples

### Post-Design Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Contract tests defined in worktree-service.md |
| II. Specification-Driven | ✅ PASS | All contracts derived from spec requirements |
| III. Independent User Stories | ✅ PASS | Each API method maps to one user story |
| IV. Human Approval Gates | ✅ PASS | Gate 2 (plan) ready for approval |
| V. Parallel-First Execution | ✅ PASS | US1+US2 implementable in parallel |
| VI. Simplicity and YAGNI | ✅ PASS | subprocess.run(), no external libraries |
| VII. Versioning | ✅ PASS | Conventional commits will be used |
| VIII. Technology Stack | ✅ PASS | Python 3.11+, Pydantic v2, pytest |
| IX. Thin Client Architecture | ✅ N/A | Backend service only |
| X. Security-First | ✅ PASS | No secrets, uses existing git credentials |
| XI. Documentation | ✅ PASS | Quickstart and contracts documented |
| XII. CI/CD | ✅ PASS | Will use existing CI pipeline with E2E tests |

**Gate Result**: ✅ PASSED - Ready for Phase 2 (tasks generation)

---

## Phase 2: Tasks

Run `/speckit.tasks` to generate task list from this plan.

---

## Next Steps

1. Run `/speckit.tasks` to generate tasks.md
2. Run `/speckit.implement` to execute tasks (TDD)
3. Create PR for review
