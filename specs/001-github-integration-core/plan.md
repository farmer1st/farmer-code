# Implementation Plan: GitHub Integration Core

**Branch**: `001-github-integration-core` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-github-integration-core/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Backend service providing GitHub operations (issues, comments, labels, PRs) for the FarmCode orchestrator. Uses GitHub App authentication (App ID: 2578431, Installation ID: 102211688) with REST API polling (5-10 second intervals) for monitoring agent communications. Implements CRUD operations via programmatic interface, structured logging, and fixed retry logic for reliability. Local-first design runs on developer's machine without public endpoint.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PyGithub (GitHub API client), python-dotenv (secrets), python-jose (JWT for GitHub App auth)
**Storage**: N/A (stateless service, GitHub is source of truth)
**Testing**: pytest with pytest-asyncio
**Target Platform**: Mac/Linux/Windows (local developer machine)
**Project Type**: Single (backend service)
**Performance Goals**: <2s issue creation/retrieval, <1s comment retrieval (100 comments), 95% success rate
**Constraints**: 5-10 second polling interval, 3 retries with 1s delay, local-first (no public endpoint)
**Scale/Scope**: Single repository (farmer1st/farmcode-tests), single installation, bootstrap MVP

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development ✅

**Status**: PASS
**Evidence**: Feature spec includes 16 acceptance scenarios across 4 user stories. Plan will generate contract tests for all public interfaces before implementation. TDD workflow enforced in tasks phase.

### Principle II: Specification-Driven Development ✅

**Status**: PASS
**Evidence**: spec.md approved with clarifications, plan.md (this document) defines technical approach, tasks.md will define implementation sequence. All gates in place.

### Principle III: Independent User Stories ✅

**Status**: PASS
**Evidence**: Four user stories prioritized (P1-P4). P1 (issues) is independently deliverable and testable. MVP achievable with P1 alone.

### Principle IV: Human Approval Gates ✅

**Status**: PASS
**Evidence**: Four gates planned: Gate 1 (specs - complete), Gate 2 (plans - this document), Gate 3 (tests - tasks.md), Gate 4 (merge - code review).

### Principle V: Parallel-First Execution ✅

**Status**: PASS
**Evidence**: User stories P1-P4 can be implemented sequentially (foundation pattern not applicable for single service). Within stories, tests and models can be parallel.

### Principle VI: Simplicity and YAGNI ✅

**Status**: PASS
**Evidence**: No premature abstraction. Direct GitHub API client usage. Simple polling (not webhooks). Stateless design. No complexity violations.

### Principle VII: Versioning and Change Control ✅

**Status**: PASS
**Evidence**: Feature tracked in branch 001-github-integration-core. All artifacts version-controlled. Semantic commits planned.

### Principle VIII: Technology Stack Standards ✅

**Status**: PASS
**Evidence**:
- Python 3.11+ ✅
- uv for package management ✅
- ruff for linting ✅
- pytest for testing ✅
- FastAPI not needed (programmatic interface, not HTTP API) - justified as simpler
- Pydantic for validation ✅
- Structured JSON logging to stdout/stderr ✅

**Note**: This service provides a programmatic Python interface (not REST API), so FastAPI is not required. This simplification is justified by YAGNI - the orchestrator will import and call this service directly.

### Principle IX: Thin Client Architecture ✅

**Status**: PASS (N/A - no client)
**Evidence**: This is a backend service consumed by the orchestrator. All logic server-side by design.

### Principle X: Security-First Development ✅

**Status**: PASS
**Evidence**:
- GitHub App PEM file at ./keys/orchestrator.pem with chmod 600 ✅
- GITHUB_APP_PRIVATE_KEY_PATH environment variable ✅
- No secrets in code ✅
- Input validation via Pydantic ✅
- No raw SQL (no database) ✅
- Structured logging (no sensitive data logged) ✅

**Re-check After Phase 1**: ✅ All principles remain satisfied after design phase.

## Project Structure

### Documentation (this feature)

```text
specs/001-github-integration-core/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── github_service.md     # Public interface contract
│   └── data_models.md        # Pydantic model schemas
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── github_integration/
│   ├── __init__.py
│   ├── models.py          # Pydantic models (Issue, Comment, Label, PullRequest)
│   ├── auth.py            # GitHub App authentication
│   ├── client.py          # GitHub API client wrapper
│   ├── service.py         # Public service interface (main entry point)
│   ├── polling.py         # Comment polling mechanism
│   ├── errors.py          # Custom exceptions
│   └── logger.py          # Structured JSON logging

tests/
├── conftest.py           # pytest fixtures
├── contract/
│   ├── test_service_interface.py    # Public API contract tests
│   └── test_models.py                # Pydantic model validation tests
├── integration/
│   ├── test_github_operations.py    # Live GitHub API tests
│   └── test_polling.py               # Polling mechanism tests
└── unit/
    ├── test_auth.py                  # Authentication logic tests
    └── test_retry_logic.py           # Retry behavior tests
```

**Structure Decision**: Single project structure selected. This is a standalone Python package providing a programmatic interface to GitHub operations. No web frontend, no separate API service - just a library consumed by the orchestrator. Monorepo placement: this will live in `packages/github-integration/` when integrated into farmcode monorepo.

## Complexity Tracking

**No violations** - all constitutional principles satisfied with justified simplifications.

