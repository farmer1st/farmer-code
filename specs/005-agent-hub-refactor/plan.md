# Implementation Plan: Agent Hub Refactor

**Branch**: `005-agent-hub-refactor` | **Date**: 2026-01-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-agent-hub-refactor/spec.md`

## Summary

Refactor the Knowledge Router module into the Agent Hub - a central coordination layer for all agent interactions. This involves renaming modules and classes, adding session management for multi-turn conversations, exposing functionality via MCP tools, and updating all documentation and tests.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Pydantic v2, subprocess (CLI runner), uuid, datetime, json
**Storage**: In-memory session storage (dict-based), JSON file logging
**Testing**: pytest with pytest-asyncio for async code
**Target Platform**: Local development (macOS/Linux)
**Project Type**: Single project (Python library/service)
**Performance Goals**: Route questions within 100ms (excluding agent response time)
**Constraints**: Backward compatibility with existing Knowledge Router tests
**Scale/Scope**: 5-10 concurrent sessions, single-user local development

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | PASS | Existing KR tests will be migrated, new session tests added first |
| II. Specification-Driven | PASS | Spec complete with user stories and requirements |
| III. Independent User Stories | PASS | Each story can be tested independently |
| IV. Human Approval Gates | PASS | Following standard gate process |
| V. Parallel-First Execution | PASS | Rename and new components can run in parallel |
| VI. Simplicity and YAGNI | PASS | In-memory sessions (no DB), simple dict-based storage |
| VII. Versioning | PASS | Using conventional commits |
| VIII. Technology Stack | PASS | Python 3.11+, Pydantic v2, pytest |
| IX. Thin Client Architecture | N/A | No frontend changes |
| X. Security-First | PASS | No secrets, input validation via Pydantic |
| XI. Documentation and User Journeys | PASS | Journey mapping below, docs will be updated |
| XII. Continuous Integration | PASS | All existing CI checks apply |

**Gate Status**: PASS - No violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/005-agent-hub-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── agent-hub-api.md # Service interface contract
└── tasks.md             # Phase 2 output (from /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── agent_hub/                    # NEW: Renamed from knowledge_router/
│   ├── __init__.py              # Updated exports
│   ├── hub.py                   # NEW: Main AgentHub class (was router.py)
│   ├── router.py                # Renamed from dispatcher.py
│   ├── session.py               # NEW: SessionManager
│   ├── models.py                # Extended with Session, HubResponse
│   ├── validator.py             # Unchanged logic
│   ├── escalation.py            # Unchanged logic
│   ├── logger.py                # Unchanged logic
│   ├── config.py                # Updated class names
│   ├── exceptions.py            # Unchanged
│   ├── prompts.py               # Unchanged
│   ├── mcp_server.py            # NEW: MCP server for tools
│   └── README.md                # Updated documentation
├── knowledge_router/             # REMOVED (renamed to agent_hub)
├── orchestrator/                 # Unchanged
├── worktree_manager/             # Unchanged
└── github_integration/           # Unchanged

tests/
├── unit/
│   └── agent_hub/               # Renamed from knowledge_router/
│       ├── test_hub.py          # Tests for AgentHub
│       ├── test_router.py       # Tests for routing (was test_dispatcher.py)
│       ├── test_session.py      # NEW: SessionManager tests
│       ├── test_models.py       # Extended model tests
│       ├── test_validator.py    # Unchanged
│       ├── test_escalation.py   # Unchanged
│       └── test_config.py       # Updated for new names
├── integration/
│   └── agent_hub/               # Renamed from knowledge_router/
│       └── test_full_flow.py    # Integration tests
├── contract/
│   └── agent_hub/               # Renamed from knowledge_router/
│       └── test_contracts.py    # Contract tests
└── e2e/
    └── agent_hub/               # Renamed from knowledge_router/
        ├── test_route_question.py
        ├── test_escalation_flow.py
        ├── test_qa_logging.py
        └── test_session_management.py  # NEW

docs/
├── architecture/
│   └── agent-hub.md             # NEW: Architecture documentation
└── user-journeys/
    ├── JOURNEYS.md              # Updated with AH journeys
    ├── AH-001-route-question.md
    ├── AH-002-session-management.md
    ├── AH-003-confidence-escalation.md
    ├── AH-004-pending-escalation.md
    └── AH-005-audit-logging.md
```

**Structure Decision**: Single project structure. This is a Python library/service module within the existing monorepo. No frontend or separate API service needed.

## User Journey Mapping (REQUIRED per Constitution Principle XI)

**Journey Domain**: AH (Agent Hub)

| User Story | Journey ID | Journey Name | Priority |
|------------|------------|--------------|----------|
| US1: Route Questions to Experts | AH-001 | Route Question to Expert | P1 |
| US2: Maintain Conversation Sessions | AH-002 | Session Management | P1 |
| US3: Validate Confidence and Escalate | AH-003 | Confidence Escalation | P2 |
| US4: Track Pending Escalations | AH-004 | Pending Escalation Check | P2 |
| US5: Audit Trail Logging | AH-005 | Audit Logging | P3 |

**Journey Files to Create**:
- `docs/user-journeys/AH-001-route-question.md`
- `docs/user-journeys/AH-002-session-management.md`
- `docs/user-journeys/AH-003-confidence-escalation.md`
- `docs/user-journeys/AH-004-pending-escalation.md`
- `docs/user-journeys/AH-005-audit-logging.md`
- Update `docs/user-journeys/JOURNEYS.md`

**E2E Test Markers**:
- `@pytest.mark.journey("AH-001")` for routing tests
- `@pytest.mark.journey("AH-002")` for session tests
- `@pytest.mark.journey("AH-003")` for escalation tests
- `@pytest.mark.journey("AH-004")` for pending check tests
- `@pytest.mark.journey("AH-005")` for logging tests

## Complexity Tracking

No violations to justify. The implementation follows YAGNI principles:
- In-memory sessions (no database)
- Simple dict-based storage
- MCP server follows existing patterns
