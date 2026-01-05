# Tasks: Baron PM Agent

**Input**: Design documents from `/specs/006-baron-pm-agent/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Architecture**: Baron is a **Claude Agent SDK agent**, NOT a Python library. Tasks focus on:
1. Agent configuration files in `.claude/agents/baron/`
2. Minimal `BaronDispatcher` class in `src/orchestrator/`
3. Integration tests that dispatch real agents

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Journey ID Convention

**Journey Domain**: BRN (Baron)

| User Story | Journey ID | Journey Name |
|------------|------------|--------------|
| US1: Create Feature Specification | BRN-001 | Create Specification Autonomously |
| US2: Generate Implementation Plan | BRN-002 | Generate Implementation Plan |
| US3: Generate Task List | BRN-003 | Generate Task List |
| US4: Handle Async Human Escalation | BRN-004 | Handle Pending Escalations |
| US5: Consult Domain Experts | BRN-005 | Expert Consultation Flow |
| US6: Respect Constitution Principles | BRN-006 | Constitution Compliance |

---

## Phase 1: Setup (Agent Infrastructure)

**Purpose**: Create Baron agent directory structure and base configuration

- [X] T001 Create directory structure `.claude/agents/baron/`
- [X] T002 Create directory structure `.claude/agents/baron/workflows/`
- [X] T003 [P] Create directory structure `.claude/agents/baron/examples/`

---

## Phase 2: Foundational (Agent Configuration)

**Purpose**: Baron's core agent configuration files - MUST be complete before any workflow tests

**CRITICAL**: No workflow implementation can be tested until Baron's agent config exists

### Agent System Prompt

- [X] T004 Create Baron system prompt in `.claude/agents/baron/system-prompt.md`:
  - Define Baron's identity as PM agent
  - Specify tool access (Read, Write, Bash, Glob, Grep)
  - Specify Agent Hub MCP tools (ask_expert, check_escalation)
  - Define constitution compliance requirements
  - Define output format with result markers
  - Define error handling behavior

### Agent Configuration

- [X] T005 [P] Create Baron config in `.claude/agents/baron/config.yaml`:
  - Model: claude-sonnet-4-20250514
  - Tools: Read, Write, Bash, Glob, Grep
  - MCP servers: agent-hub
  - Timeout: 600 seconds
  - Output format with result markers

### Dispatch Models (Minimal Python)

- [X] T006 [P] Create BaronDispatcher request models in `src/orchestrator/baron_models.py`:
  - SpecifyRequest (feature_description, feature_number, short_name)
  - PlanRequest (spec_path, force_research)
  - TasksRequest (plan_path)

- [X] T007 [P] Create BaronDispatcher result models in `src/orchestrator/baron_models.py`:
  - SpecifyResult (success, spec_path, feature_id, branch_name, duration_seconds)
  - PlanResult (success, plan_path, research_path, data_model_path, contracts_dir, quickstart_path)
  - TasksResult (success, tasks_path, task_count, test_count, duration_seconds)

**Checkpoint**: Foundation ready - BaronDispatcher implementation can begin

---

## Phase 3: User Story 1 - Create Feature Specification (Priority: P1) MVP

**Goal**: Baron can autonomously create spec.md from a feature description

**Journey ID**: BRN-001

**Independent Test**: Dispatch Baron with feature description, verify spec.md is created with all mandatory sections

### Tests for User Story 1

> **NOTE: Write tests FIRST (TDD). Tests mock ClaudeCLIRunner for unit tests.**

- [X] T008 [P] [US1] Unit test for SpecifyRequest validation in `tests/unit/orchestrator/test_baron_models.py`
- [X] T009 [P] [US1] Unit test for SpecifyResult parsing in `tests/unit/orchestrator/test_baron_dispatch.py`
- [X] T010 [P] [US1] Unit test for dispatch_specify with mocked runner in `tests/unit/orchestrator/test_baron_dispatch.py`

### Implementation for User Story 1

- [X] T011 [US1] Create specify workflow instructions in `.claude/agents/baron/workflows/specify.md`:
  - Read feature description from dispatch prompt
  - Run create-new-feature.sh script
  - Load spec-template.md
  - Load constitution
  - Fill template sections
  - Create quality checklist
  - Output structured result

- [X] T012 [US1] Create specify example prompt in `.claude/agents/baron/examples/specify-prompt.md`:
  - Example dispatch prompt format
  - Expected output format

- [X] T013 [US1] Implement dispatch_specify() in `src/orchestrator/baron_dispatch.py`:
  - Build dispatch prompt from SpecifyRequest
  - Execute via ClaudeCLIRunner
  - Parse result between markers
  - Return SpecifyResult

### Integration Test for User Story 1

- [X] T014 [US1] Integration test with real agent dispatch in `tests/integration/baron/test_specify_workflow.py`:
  - Dispatch Baron with test feature description
  - Verify spec.md created
  - Verify all mandatory sections present
  - Mark with `@pytest.mark.journey("BRN-001")`

### Documentation for User Story 1

- [X] T015 [US1] Create user journey doc in `docs/user-journeys/BRN-001-create-specification.md`

**Checkpoint**: User Story 1 complete when Baron can create valid spec.md files

---

## Phase 4: User Story 2 - Generate Implementation Plan (Priority: P1) MVP

**Goal**: Baron can create plan.md and artifacts from spec.md

**Journey ID**: BRN-002

**Independent Test**: Provide spec.md, verify Baron creates plan.md with all required artifacts

### Tests for User Story 2

- [X] T016 [P] [US2] Unit test for PlanRequest validation in `tests/unit/orchestrator/test_baron_models.py`
- [X] T017 [P] [US2] Unit test for PlanResult parsing in `tests/unit/orchestrator/test_baron_dispatch.py`
- [X] T018 [P] [US2] Unit test for dispatch_plan with mocked runner in `tests/unit/orchestrator/test_baron_dispatch.py`

### Implementation for User Story 2

- [X] T019 [US2] Create plan workflow instructions in `.claude/agents/baron/workflows/plan.md`:
  - Read spec.md from dispatch prompt
  - Run setup-plan.sh script
  - Load plan-template.md and constitution
  - Phase 0: Generate research.md
  - Phase 1: Generate data-model.md, contracts/, quickstart.md
  - Fill constitution check section
  - Run update-agent-context.sh
  - Output structured result

- [X] T020 [US2] Create plan example prompt in `.claude/agents/baron/examples/plan-prompt.md`

- [X] T021 [US2] Implement dispatch_plan() in `src/orchestrator/baron_dispatch.py`:
  - Build dispatch prompt from PlanRequest
  - Execute via ClaudeCLIRunner
  - Parse result between markers
  - Return PlanResult

### Integration Test for User Story 2

- [X] T022 [US2] Integration test in `tests/integration/baron/test_plan_workflow.py`:
  - Create test spec.md
  - Dispatch Baron with spec path
  - Verify plan.md, research.md, data-model.md created
  - Mark with `@pytest.mark.journey("BRN-002")`

### Documentation for User Story 2

- [X] T023 [US2] Create user journey doc in `docs/user-journeys/BRN-002-generate-plan.md`

**Checkpoint**: User Story 2 complete when Baron can create valid plan.md with artifacts

---

## Phase 5: User Story 3 - Generate Task List (Priority: P1) MVP

**Goal**: Baron can create tasks.md from plan.md with TDD ordering

**Journey ID**: BRN-003

**Independent Test**: Provide plan.md, verify Baron creates tasks.md with tests before implementation

### Tests for User Story 3

- [X] T024 [P] [US3] Unit test for TasksRequest validation in `tests/unit/orchestrator/test_baron_models.py`
- [X] T025 [P] [US3] Unit test for TasksResult parsing in `tests/unit/orchestrator/test_baron_dispatch.py`
- [X] T026 [P] [US3] Unit test for dispatch_tasks with mocked runner in `tests/unit/orchestrator/test_baron_dispatch.py`

### Implementation for User Story 3

- [X] T027 [US3] Create tasks workflow instructions in `.claude/agents/baron/workflows/tasks.md`:
  - Read plan.md, spec.md, data-model.md, contracts/
  - Load tasks-template.md and constitution
  - Generate tasks organized by user story
  - Enforce TDD: test tasks before implementation
  - Include dependency ordering
  - Output structured result

- [X] T028 [US3] Create tasks example prompt in `.claude/agents/baron/examples/tasks-prompt.md`

- [X] T029 [US3] Implement dispatch_tasks() in `src/orchestrator/baron_dispatch.py`:
  - Build dispatch prompt from TasksRequest
  - Execute via ClaudeCLIRunner
  - Parse result between markers
  - Return TasksResult

### Integration Test for User Story 3

- [X] T030 [US3] Integration test in `tests/integration/baron/test_tasks_workflow.py`:
  - Create test plan.md
  - Dispatch Baron with plan path
  - Verify tasks.md created
  - Verify TDD ordering (tests before implementation)
  - Mark with `@pytest.mark.journey("BRN-003")`

### Documentation for User Story 3

- [X] T031 [US3] Create user journey doc in `docs/user-journeys/BRN-003-generate-tasks.md`

**Checkpoint**: User Story 3 complete when Baron can create valid TDD-ordered tasks.md

---

## Phase 6: User Story 4 - Handle Async Human Escalation (Priority: P2)

**Goal**: Baron continues non-blocked work when escalation is pending

**Journey ID**: BRN-004

**Independent Test**: Simulate pending escalation, verify Baron continues with other sections

### Tests for User Story 4

- [ ] T032 [P] [US4] Unit test for blocked workflow state handling in `tests/unit/orchestrator/test_baron_dispatch.py`
- [ ] T033 [P] [US4] Unit test for escalation check in dispatch in `tests/unit/orchestrator/test_baron_dispatch.py`

### Implementation for User Story 4

- [ ] T034 [US4] Update Baron system prompt for escalation handling in `.claude/agents/baron/system-prompt.md`:
  - Check for pending escalations via check_escalation MCP tool
  - Continue with non-blocked sections
  - Persist workflow state for resumption
  - Re-check escalation status periodically

- [ ] T035 [US4] Add state persistence instructions to system prompt:
  - Write state to specs/{feature}/.baron-state.json
  - Check for existing state on startup
  - Resume from checkpoint if state exists

### Integration Test for User Story 4

- [ ] T036 [US4] Integration test for escalation handling in `tests/integration/baron/test_escalation_handling.py`:
  - Mock Agent Hub to return pending status
  - Verify Baron continues with other sections
  - Verify state file created
  - Mark with `@pytest.mark.journey("BRN-004")`

### Documentation for User Story 4

- [ ] T037 [US4] Create user journey doc in `docs/user-journeys/BRN-004-pending-escalations.md`

**Checkpoint**: User Story 4 complete when Baron handles async escalations gracefully

---

## Phase 7: User Story 5 - Consult Domain Experts (Priority: P2)

**Goal**: Baron consults correct experts via Agent Hub for specialized knowledge

**Journey ID**: BRN-005

**Independent Test**: Trigger expert consultation, verify correct expert is routed to

### Tests for User Story 5

- [ ] T038 [P] [US5] Unit test for expert topic routing in Baron prompts (verify prompts contain correct topic)

### Implementation for User Story 5

- [ ] T039 [US5] Update Baron system prompt for expert consultation in `.claude/agents/baron/system-prompt.md`:
  - Architecture questions → ask_expert with topic "architecture" (routes to @duc)
  - Product questions → ask_expert with topic "product" (routes to @veuve)
  - Testing questions → ask_expert with topic "testing" (routes to @marie)
  - Session management for multi-turn conversations

### Integration Test for User Story 5

- [ ] T040 [US5] Integration test for expert consultation in `tests/integration/baron/test_expert_consultation.py`:
  - Provide complex feature requiring expert input
  - Verify ask_expert called with correct topic
  - Verify answer incorporated into artifact
  - Mark with `@pytest.mark.journey("BRN-005")`

### Documentation for User Story 5

- [ ] T041 [US5] Create user journey doc in `docs/user-journeys/BRN-005-expert-consultation.md`

**Checkpoint**: User Story 5 complete when Baron correctly routes to domain experts

---

## Phase 8: User Story 6 - Respect Constitution Principles (Priority: P2)

**Goal**: Baron enforces constitution principles during all planning

**Journey ID**: BRN-006

**Independent Test**: Verify generated artifacts reference and comply with constitution

### Tests for User Story 6

- [ ] T042 [P] [US6] Unit test for constitution loading in Baron prompts

### Implementation for User Story 6

- [ ] T043 [US6] Update Baron system prompt for constitution enforcement:
  - Read constitution at workflow start
  - Principle I: TDD - test tasks before implementation
  - Principle VI: YAGNI - no unnecessary complexity
  - Principle XI: User journey mapping in plan.md
  - Fill Constitution Check section in plan.md

- [ ] T044 [US6] Update workflow prompts to reference constitution:
  - Specify workflow: check if feature aligns with principles
  - Plan workflow: fill constitution check section
  - Tasks workflow: enforce TDD ordering

### Integration Test for User Story 6

- [ ] T045 [US6] Integration test for constitution compliance in `tests/integration/baron/test_constitution_compliance.py`:
  - Verify plan.md has constitution check section filled
  - Verify tasks.md has test tasks before implementation
  - Mark with `@pytest.mark.journey("BRN-006")`

### Documentation for User Story 6

- [ ] T046 [US6] Create user journey doc in `docs/user-journeys/BRN-006-constitution-compliance.md`

**Checkpoint**: User Story 6 complete when Baron enforces constitution principles

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final integration and documentation

### BaronDispatcher Complete Class

- [ ] T047 Implement BaronDispatcher.__init__() with runner and config loading
- [ ] T048 Implement _load_system_prompt() to read from agent config
- [ ] T049 Implement _parse_result() to extract JSON between markers
- [ ] T050 Add error handling for DispatchError, ParseError, TimeoutError

### E2E Tests

- [ ] T051 E2E test for full cycle in `tests/e2e/baron/test_full_cycle.py`:
  - dispatch_specify → dispatch_plan → dispatch_tasks
  - Verify all artifacts created
  - Verify constitution compliance
  - Mark with `@pytest.mark.journey("BRN-001,BRN-002,BRN-003")`

### User Journey Index Update

- [X] T052 Update `docs/user-journeys/JOURNEYS.md` with all BRN journeys

### Module Documentation

- [X] T053 [P] Create `.claude/agents/baron/README.md` with:
  - Baron overview
  - Agent configuration reference
  - Workflow instructions

- [X] T054 [P] Update `src/orchestrator/README.md` with BaronDispatcher usage

### Quality & Validation

- [X] T055 Run quickstart.md validation steps
- [X] T056 Code cleanup and linting pass
- [X] T057 Run full test suite: `uv run pytest tests/unit/orchestrator/test_baron*.py tests/integration/baron/ -v`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1, US2, US3 (P1) should be done first
  - US4, US5, US6 (P2) can run in parallel after P1 stories
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational - No dependencies on other stories
- **US2 (P1)**: Can start after Foundational - May reference US1 examples but independently testable
- **US3 (P1)**: Can start after Foundational - May reference US1/US2 examples but independently testable
- **US4 (P2)**: Can start after Foundational - Independent of other stories
- **US5 (P2)**: Can start after Foundational - Independent of other stories
- **US6 (P2)**: Can start after Foundational - Applies to all workflows

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- System prompt updates before dispatcher implementation
- Workflow instructions before integration tests
- **User journey doc MUST be created before story is marked complete**

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- All tests for a user story marked [P] can run in parallel
- P2 user stories can run in parallel with each other

---

## Parallel Example: Foundational Phase

```bash
# Launch all foundational tasks in parallel:
Task: "Create Baron config in .claude/agents/baron/config.yaml"
Task: "Create BaronDispatcher request models in src/orchestrator/models/baron_models.py"
Task: "Create BaronDispatcher result models in src/orchestrator/models/baron_models.py"
```

---

## Notes

- Baron is an AGENT, not a Python library - most logic is in prompts
- Python code is MINIMAL - only BaronDispatcher and models
- Tests mock ClaudeCLIRunner for unit tests
- Integration tests dispatch real agent (slower, more comprehensive)
- TDD enforced: test tasks before implementation tasks
- User journey docs are REQUIRED per Constitution Principle XI

## Documentation Checklist

Before marking feature complete, verify:

- [X] `.claude/agents/baron/README.md` exists with configuration reference
- [X] `src/orchestrator/README.md` updated with BaronDispatcher usage
- [X] `docs/user-journeys/` has journey doc for P1 user stories (BRN-001 through BRN-003)
- [X] `docs/user-journeys/JOURNEYS.md` updated with all BRN journeys
- [X] All integration tests pass with journey markers (66 passed, 3 skipped)

