# Implementation Plan: Knowledge Router

**Branch**: `004-knowledge-router` | **Date**: 2026-01-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-knowledge-router/spec.md`

## Summary

The Knowledge Router orchestrates a question-answer protocol between @baron (the PM agent running SpecKit) and specialized agents. It routes questions from @baron to knowledge agents (@duc, @veuve), validates answers against confidence thresholds (default 80%), escalates low-confidence answers to humans, and logs all Q&A for retrospective improvement. The system also dispatches execution tasks to specialists (@marie, @dede, @gustave, @degaulle) with scoped repository access.

**Key Technical Approach**:
- JSON-based question-answer protocol for agent communication
- Confidence-based routing with topic-specific threshold overrides
- GitHub comments for human escalation and status updates
- Immutable Q&A logging for retrospective analysis
- Process-based agent spawning via Claude CLI

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: Pydantic v2 (data models), subprocess (CLI spawning), python-dotenv (config)
**Storage**: JSON files for Q&A logs and routing config; SQLite for structured data (future)
**Testing**: pytest with pytest-asyncio
**Target Platform**: Local CLI (macOS/Linux)
**Project Type**: Single project (Python library + CLI)
**Performance Goals**: Question routing < 100ms, agent spawn < 3s
**Constraints**: Support 5+ concurrent agent interactions, no data loss in Q&A logs
**Scale/Scope**: Single user, 10-50 questions per feature workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ PASS | Tests designed before implementation |
| II. Specification-Driven | ✅ PASS | Full spec.md completed |
| III. Independent User Stories | ✅ PASS | 8 stories with clear priorities (P1-P3) |
| IV. Human Approval Gates | ✅ PASS | Confidence threshold + human escalation built-in |
| V. Parallel-First Execution | ✅ PASS | Knowledge agents can answer concurrently |
| VI. Simplicity/YAGNI | ✅ PASS | JSON files first, DB later if needed |
| VII. Versioning | ✅ PASS | Conventional commits, semantic versioning |
| VIII. Technology Stack | ✅ PASS | Python 3.11+, Pydantic v2, pytest |
| IX. Thin Client | ✅ PASS | No frontend, pure backend logic |
| X. Security-First | ✅ PASS | Config via .env, no secrets in code |
| XI. Documentation | ✅ PASS | User journeys mapped below |
| XII. CI/CD | ✅ PASS | Will add to existing CI workflow |

**Gate Status**: ✅ PASS - Ready for Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/004-knowledge-router/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── question.json    # Question schema
│   ├── answer.json      # Answer schema
│   └── routing.json     # Routing config schema
├── checklists/
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── knowledge_router/        # NEW: This feature
│   ├── __init__.py
│   ├── models.py            # Pydantic models (Question, Answer, etc.)
│   ├── router.py            # KnowledgeRouterService
│   ├── dispatcher.py        # Agent dispatch (spawn Claude CLI)
│   ├── validator.py         # Confidence validation
│   ├── escalation.py        # Human escalation handler
│   ├── logger.py            # Q&A logging
│   ├── retro.py             # Retrospective report generation
│   └── config.py            # Routing rules, thresholds
├── orchestrator/            # EXISTING: Feature 003
├── worktree_manager/        # EXISTING: Feature 002
└── github_integration/      # EXISTING: Feature 001

tests/
├── unit/
│   └── knowledge_router/
│       ├── test_models.py
│       ├── test_router.py
│       ├── test_validator.py
│       └── test_logger.py
├── integration/
│   └── knowledge_router/
│       ├── test_dispatch.py
│       └── test_escalation.py
├── contract/
│   └── knowledge_router/
│       ├── test_question_schema.py
│       └── test_answer_schema.py
└── e2e/
    └── knowledge_router/
        ├── test_route_question.py
        └── test_confidence_gate.py
```

**Structure Decision**: Single project layout (Option 1). This feature adds a new module `knowledge_router/` alongside existing modules. No frontend, pure Python backend service.

## User Journey Mapping (REQUIRED per Constitution Principle XI)

**Journey Domain**: KR (Knowledge Router)

| User Story | Journey ID | Journey Name | Priority |
|------------|------------|--------------|----------|
| US1: Route Questions to Knowledge Agents | KR-001 | Route Question to Agent | P1 |
| US2: Receive and Validate Agent Answers | KR-002 | Validate Answer Confidence | P1 |
| US3: Escalate Low-Confidence Answers | KR-003 | Escalate to Human | P1 |
| US4: Log All Q&A for Retrospectives | KR-004 | Log Q&A Exchange | P1 |
| US5: Dispatch Execution Tasks | KR-005 | Dispatch Execution Task | P2 |
| US6: Configure Routing Rules | KR-006 | Configure Routing | P2 |
| US7: Generate Retrospective Report | KR-007 | Generate Retro Report | P2 |
| US8: Handle Agent Unavailability | KR-008 | Handle Agent Timeout | P3 |

**Journey Files to Create**:
- `docs/user-journeys/KR-001-route-question.md`
- `docs/user-journeys/KR-002-validate-confidence.md`
- `docs/user-journeys/KR-003-escalate-human.md`
- `docs/user-journeys/KR-004-log-qa.md`
- `docs/user-journeys/KR-005-dispatch-task.md`
- `docs/user-journeys/KR-006-configure-routing.md`
- `docs/user-journeys/KR-007-generate-retro.md`
- `docs/user-journeys/KR-008-handle-timeout.md`
- Update `docs/user-journeys/JOURNEYS.md`

**E2E Test Markers**:
- Each E2E test class should be marked with `@pytest.mark.journey("KR-NNN")`

## Complexity Tracking

> No violations - complexity justified within constitution bounds.

| Item | Justification |
|------|---------------|
| JSON file logging (not DB) | YAGNI - start simple, migrate to SQLite if scale requires |
| No async initially | Single-user CLI, sync is sufficient for MVP |
| Process-based CLI spawn | Constitution requires Claude CLI, subprocess is standard approach |

## Phase 0: Research Required

The following areas need research before detailed design:

1. **Claude CLI spawning patterns** - How to spawn Claude CLI with custom prompts and capture structured output
2. **Confidence score implementation** - How agents should calculate and report confidence (0-100%)
3. **GitHub comment format** - Structure for human escalation comments
4. **Routing config schema** - Best format for topic-to-agent mapping

## Phase 1: Design Artifacts

Will generate after Phase 0 research:
- `research.md` - Consolidated research findings
- `data-model.md` - Entity definitions (Question, Answer, etc.)
- `contracts/` - JSON schemas for all entities
- `quickstart.md` - End-to-end validation guide
