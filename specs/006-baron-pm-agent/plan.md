# Implementation Plan: Baron PM Agent

**Branch**: `006-baron-pm-agent` | **Date**: 2026-01-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-baron-pm-agent/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Baron is an autonomous PM agent that handles the planning phases of feature development. When triggered by the Workflow Orchestrator, Baron executes speckit workflows (specify → plan → tasks) autonomously, using the Agent Hub MCP tools to consult domain experts when clarification is needed.

**Key Architecture**: Baron is a **Claude Agent SDK agent** - NOT a Python library. Baron consists of:
1. **Agent system prompt** - Instructions and workflow definitions
2. **Tool configuration** - Access to Read, Write, Bash, and Agent Hub MCP
3. **Orchestrator dispatch** - ClaudeCLIRunner triggers Baron with context

Baron uses Claude's native capabilities to read templates from `.specify/templates/`, generate artifacts in `specs/{NNN-feature}/`, and handle async human escalations gracefully. Baron does NOT write implementation code - that is @dede's responsibility.

## Technical Context

**Agent Type**: Claude Agent SDK (dispatched via ClaudeCLIRunner)
**Agent Model**: claude-sonnet-4-20250514 (fast, capable)
**Primary Tools**: Read, Write, Bash, Agent Hub MCP (ask_expert, check_escalation)
**Storage**: File-based (specs/ directory structure, JSON state files via Write tool)
**Testing**: pytest with mock ClaudeCLIRunner, E2E with real agent dispatch
**Target Platform**: Mac/Linux/Windows (wherever Claude CLI is installed)
**Project Type**: Agent configuration + minimal Python dispatch code
**Performance Goals**: Complete full planning cycle (specify + plan + tasks) within 10 minutes for typical features
**Constraints**: Must use Agent Hub MCP for expert consultation, must follow speckit template structure
**Scale/Scope**: Single feature at a time, single repository (farmer1st/farmer-code-tests for testing)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development ✅

**Status**: PASS
**Evidence**: Feature spec includes 24 acceptance scenarios across 6 user stories. Plan will generate contract tests for all public interfaces before implementation. TDD workflow enforced in tasks phase.

### Principle II: Specification-Driven Development ✅

**Status**: PASS
**Evidence**: spec.md approved with quality checklist complete. This plan.md defines technical approach. tasks.md will define implementation sequence. All gates in place.

### Principle III: Independent User Stories ✅

**Status**: PASS
**Evidence**: Six user stories prioritized (P1-P2). P1 stories (specify, plan, tasks) are independently testable. MVP achievable with P1 stories alone.

### Principle IV: Human Approval Gates ✅

**Status**: PASS
**Evidence**: Four gates planned: Gate 1 (specs - complete), Gate 2 (plans - this document), Gate 3 (tests - tasks.md), Gate 4 (merge - code review).

### Principle V: Parallel-First Execution ✅

**Status**: PASS
**Evidence**: Baron's workflows are sequential by nature (specify → plan → tasks), but Baron handles async escalations in parallel. Within stories, tests can run in parallel.

### Principle VI: Simplicity and YAGNI ✅

**Status**: PASS
**Evidence**: Baron reuses existing speckit templates and Agent Hub infrastructure. No custom LLM integration - uses Claude Agent SDK. Simple file-based state persistence.

### Principle VII: Versioning and Change Control ✅

**Status**: PASS
**Evidence**: Feature tracked in branch 006-baron-pm-agent. All artifacts version-controlled. Semantic commits planned.

### Principle VIII: Technology Stack Standards ✅

**Status**: PASS
**Evidence**:
- Python 3.11+ ✅
- uv for package management ✅
- ruff for linting ✅
- pytest for testing ✅
- Pydantic v2 for validation ✅
- Claude Agent SDK for agent execution ✅

### Principle IX: Thin Client Architecture ✅

**Status**: PASS (N/A - no client)
**Evidence**: Baron is a backend agent consumed by the Workflow Orchestrator. All logic server-side by design.

### Principle X: Security-First Development ✅

**Status**: PASS
**Evidence**:
- No secrets in code ✅
- Uses existing Agent Hub authentication ✅
- Input validation via Pydantic ✅
- File operations within specs/ directory only ✅

### Principle XI: Documentation and User Journeys ✅

**Status**: PASS
**Evidence**: User journeys mapped below. E2E tests will be tagged with journey markers.

### Principle XII: Continuous Integration and Delivery ✅

**Status**: PASS
**Evidence**: All tests run in CI. E2E tests use farmer-code-tests repo.

**Re-check After Phase 1**: ✅ All principles remain satisfied after design phase.

## Project Structure

### Documentation (this feature)

```text
specs/006-baron-pm-agent/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── baron_dispatch.md    # Orchestrator dispatch interface
│   └── agent_config.md      # Agent configuration contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Agent Configuration (repository root)

```text
.claude/
└── agents/
    └── baron/
        ├── system-prompt.md     # Baron's system prompt and instructions
        ├── config.yaml          # Agent configuration (model, tools, MCP)
        ├── workflows/
        │   ├── specify.md       # Instructions for /speckit.specify workflow
        │   ├── plan.md          # Instructions for /speckit.plan workflow
        │   └── tasks.md         # Instructions for /speckit.tasks workflow
        └── examples/
            ├── specify-prompt.md    # Example dispatch prompt for specify
            ├── plan-prompt.md       # Example dispatch prompt for plan
            └── tasks-prompt.md      # Example dispatch prompt for tasks
```

### Orchestrator Integration (minimal Python)

```text
src/orchestrator/
├── baron_dispatch.py    # BaronDispatcher class (triggers Baron via ClaudeCLIRunner)
└── models/
    └── baron_models.py  # Pydantic models for dispatch requests/results
```

### Tests

```text
tests/
├── conftest.py                    # pytest fixtures
├── unit/
│   └── orchestrator/
│       └── test_baron_dispatch.py     # Dispatch logic tests (mocked CLI)
├── integration/
│   └── baron/
│       ├── test_specify_workflow.py   # Specify workflow with real agent
│       ├── test_plan_workflow.py      # Plan workflow with real agent
│       └── test_tasks_workflow.py     # Tasks workflow with real agent
└── e2e/
    └── baron/
        ├── test_full_cycle.py         # Full specify→plan→tasks cycle
        └── test_escalation_handling.py # Human escalation E2E tests
```

**Structure Decision**: Baron is a Claude Agent SDK agent, NOT a Python library. The agent's logic lives in system prompts and workflow instructions (`.claude/agents/baron/`). The only Python code is the `BaronDispatcher` class in the orchestrator module that triggers Baron via `ClaudeCLIRunner`. Baron uses Claude's native tool capabilities (Read, Write, Bash) plus Agent Hub MCP for expert consultation.

## User Journey Mapping (REQUIRED per Constitution Principle XI)

**Journey Domain**: BRN (Baron)

Map each user story to its corresponding user journey:

| User Story | Journey ID | Journey Name | Priority |
|------------|------------|--------------|----------|
| US1: Create Feature Specification | BRN-001 | Create Specification Autonomously | P1 |
| US2: Generate Implementation Plan | BRN-002 | Generate Implementation Plan | P1 |
| US3: Generate Task List | BRN-003 | Generate Task List | P1 |
| US4: Handle Async Human Escalation | BRN-004 | Handle Pending Escalations | P2 |
| US5: Consult Domain Experts | BRN-005 | Expert Consultation Flow | P2 |
| US6: Respect Constitution Principles | BRN-006 | Constitution Compliance | P2 |

**Journey Files to Create**:
- `docs/user-journeys/BRN-001-create-specification.md`
- `docs/user-journeys/BRN-002-generate-plan.md`
- `docs/user-journeys/BRN-003-generate-tasks.md`
- `docs/user-journeys/BRN-004-pending-escalations.md`
- `docs/user-journeys/BRN-005-expert-consultation.md`
- `docs/user-journeys/BRN-006-constitution-compliance.md`
- Update `docs/user-journeys/JOURNEYS.md`

**E2E Test Markers**:
- Each E2E test class should be marked with `@pytest.mark.journey("BRN-NNN")`

## Complexity Tracking

**No violations** - all constitutional principles satisfied. Baron reuses existing infrastructure (Agent Hub, speckit templates) without adding unnecessary complexity.

