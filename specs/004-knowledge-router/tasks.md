# Tasks: Knowledge Router

**Input**: Design documents from `/specs/004-knowledge-router/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included per constitution (Test-First Development is NON-NEGOTIABLE)

**Organization**: Tasks are grouped by user story (KR-001 through KR-008) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (KR-001, KR-002, etc.)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module structure

- [X] T001 Create module directory structure: `src/knowledge_router/` with `__init__.py`
- [X] T002 [P] Create test directory structure: `tests/unit/knowledge_router/`, `tests/integration/knowledge_router/`, `tests/contract/knowledge_router/`, `tests/e2e/knowledge_router/`
- [X] T003 [P] Create config directory: `config/` with sample `routing.yaml`
- [X] T004 [P] Create log directory structure: `logs/qa/`, `logs/retro/`, `state/escalations/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and shared infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundation

- [X] T005 [P] Unit tests for Question model in `tests/unit/knowledge_router/test_models_question.py`
- [X] T006 [P] Unit tests for Answer model in `tests/unit/knowledge_router/test_models_answer.py`
- [X] T007 [P] Unit tests for RoutingConfig model in `tests/unit/knowledge_router/test_models_routing.py`
- [X] T008 [P] Contract tests for Question JSON schema in `tests/contract/knowledge_router/test_question_schema.py`
- [X] T009 [P] Contract tests for Answer JSON schema in `tests/contract/knowledge_router/test_answer_schema.py`
- [X] T010 [P] Contract tests for RoutingConfig JSON schema in `tests/contract/knowledge_router/test_routing_config_schema.py`

### Implementation for Foundation

- [X] T011 Implement core enums (QuestionTarget, ValidationOutcome, HumanAction, AgentStatus, TaskType, ExecutionStatus) in `src/knowledge_router/models.py`
- [X] T012 [P] Implement Question model with validation in `src/knowledge_router/models.py`
- [X] T013 [P] Implement Answer model with `is_high_confidence` property in `src/knowledge_router/models.py`
- [X] T014 [P] Implement AnswerValidationResult model in `src/knowledge_router/models.py`
- [X] T015 [P] Implement RoutingRule and AgentDefinition models in `src/knowledge_router/models.py`
- [X] T016 Implement RoutingConfig with `get_agent_for_topic()` and `get_threshold_for_topic()` in `src/knowledge_router/config.py`
- [X] T017 Implement config loader (YAML parsing) in `src/knowledge_router/config.py`
- [X] T018 [P] Create base exception classes in `src/knowledge_router/exceptions.py`
- [X] T019 Export public API from `src/knowledge_router/__init__.py`

**Checkpoint**: Foundation ready - all models validated, config loading works

---

## Phase 3: User Story 1 - Route Questions to Knowledge Agents (Priority: P1) 🎯 MVP

**Goal**: @baron can route questions to knowledge agents based on topic and configuration

**Journey ID**: KR-001

**Independent Test**: Submit a question with target "architect", verify it reaches @duc

### Tests for KR-001

- [X] T020 [P] [KR-001] Unit test for topic-to-agent routing in `tests/unit/knowledge_router/test_router.py`
- [X] T021 [P] [KR-001] Unit test for routing override logic in `tests/unit/knowledge_router/test_router.py`
- [X] T022 [P] [KR-001] Integration test for agent dispatch via CLI in `tests/integration/knowledge_router/test_dispatch.py`
- [X] T023 [P] [KR-001] E2E test `@pytest.mark.journey("KR-001")` in `tests/e2e/knowledge_router/test_route_question.py`

### Implementation for KR-001

- [X] T024 [KR-001] Implement AgentHandle model in `src/knowledge_router/models.py`
- [X] T025 [KR-001] Implement AgentDispatcher for Claude CLI spawning in `src/knowledge_router/dispatcher.py`
- [X] T026 [KR-001] Extend existing `ClaudeCLIRunner` (from orchestrator) for structured JSON prompts in `src/knowledge_router/dispatcher.py`
- [X] T027 [KR-001] Implement `route_question()` method in `src/knowledge_router/router.py`
- [X] T028 [KR-001] Implement topic matching logic (exact + override precedence) in `src/knowledge_router/router.py`
- [X] T029 [KR-001] Add prompt templates for knowledge agent questions in `src/knowledge_router/prompts.py`

**Checkpoint**: Questions route to correct agent, agent spawns and receives JSON prompt

---

## Phase 4: User Story 2 - Receive and Validate Agent Answers (Priority: P1) 🎯 MVP

**Goal**: Agent answers are validated against confidence thresholds

**Journey ID**: KR-002

**Independent Test**: Submit answer with 65% confidence, verify it triggers escalation

### Tests for KR-002

- [X] T030 [P] [KR-002] Unit test for confidence validation (accept >= threshold) in `tests/unit/knowledge_router/test_validator.py`
- [X] T031 [P] [KR-002] Unit test for confidence validation (escalate < threshold) in `tests/unit/knowledge_router/test_validator.py`
- [X] T032 [P] [KR-002] Unit test for topic-specific threshold override in `tests/unit/knowledge_router/test_validator.py`
- [X] T033 [P] [KR-002] E2E test `@pytest.mark.journey("KR-002")` in `tests/e2e/knowledge_router/test_confidence_gate.py`

### Implementation for KR-002

- [X] T034 [KR-002] Implement ConfidenceValidator class in `src/knowledge_router/validator.py`
- [X] T035 [KR-002] Implement `validate_answer()` returning AnswerValidationResult in `src/knowledge_router/validator.py`
- [X] T036 [KR-002] Implement threshold lookup (topic override > default) in `src/knowledge_router/validator.py`
- [X] T037 [KR-002] Implement `submit_answer()` method in `src/knowledge_router/router.py`
- [X] T038 [KR-002] Parse structured JSON response from agent stdout in `src/knowledge_router/dispatcher.py`

**Checkpoint**: High-confidence answers accepted, low-confidence flagged for escalation

---

## Phase 5: User Story 3 - Escalate Low-Confidence Answers to Human (Priority: P1) 🎯 MVP

**Goal**: Low-confidence answers are packaged and escalated to human for review

**Journey ID**: KR-003

**Independent Test**: Trigger escalation, verify human sees all context, each response option works

### Tests for KR-003

- [X] T039 [P] [KR-003] Unit test for EscalationRequest creation in `tests/unit/knowledge_router/test_escalation.py`
- [X] T040 [P] [KR-003] Unit test for HumanResponse handling (confirm) in `tests/unit/knowledge_router/test_escalation.py`
- [X] T041 [P] [KR-003] Unit test for HumanResponse handling (correct) in `tests/unit/knowledge_router/test_escalation.py`
- [X] T042 [P] [KR-003] Unit test for HumanResponse handling (add_context) in `tests/unit/knowledge_router/test_escalation.py`
- [X] T043 [P] [KR-003] Integration test for GitHub comment posting in `tests/integration/knowledge_router/test_escalation.py`

### Implementation for KR-003

- [X] T044 [KR-003] Implement EscalationRequest model in `src/knowledge_router/models.py`
- [X] T045 [KR-003] Implement HumanResponse model in `src/knowledge_router/models.py`
- [X] T046 [KR-003] Implement EscalationHandler class in `src/knowledge_router/escalation.py`
- [X] T047 [KR-003] Implement `escalate_to_human()` method in `src/knowledge_router/router.py`
- [X] T048 [KR-003] Implement GitHub comment formatting for escalations in `src/knowledge_router/escalation.py`
- [X] T049 [KR-003] Implement `handle_human_response()` method in `src/knowledge_router/router.py`
- [X] T050 [KR-003] Implement re-route logic for add_context action in `src/knowledge_router/escalation.py`

**Checkpoint**: Human escalation works end-to-end (post comment, receive response, update answer)

---

## Phase 6: User Story 4 - Log All Q&A for Retrospectives (Priority: P1) 🎯 MVP

**Goal**: Every Q&A exchange is logged immutably for retrospective analysis

**Journey ID**: KR-004

**Independent Test**: Complete a feature workflow, retrieve Q&A log, verify all interactions captured

### Tests for KR-004

- [X] T051 [P] [KR-004] Unit test for QALogEntry creation in `tests/unit/knowledge_router/test_logger.py`
- [X] T052 [P] [KR-004] Unit test for log file append (JSONL format) in `tests/unit/knowledge_router/test_logger.py`
- [X] T053 [P] [KR-004] Unit test for log retrieval by feature_id in `tests/unit/knowledge_router/test_logger.py`
- [X] T054 [P] [KR-004] Unit test for linking related exchanges in `tests/unit/knowledge_router/test_logger.py`

### Implementation for KR-004

- [X] T055 [KR-004] Implement QALogEntry model in `src/knowledge_router/models.py`
- [X] T056 [KR-004] Implement QALogger class in `src/knowledge_router/logger.py`
- [X] T057 [KR-004] Implement `log_exchange()` for JSONL file append in `src/knowledge_router/logger.py`
- [X] T058 [KR-004] Implement `get_qa_log()` method in `src/knowledge_router/logger.py` (as `get_logs_for_feature()`)
- [X] T059 [KR-004] Implement exchange linking (parent_id for re-routes) in `src/knowledge_router/logger.py`
- [X] T060 [KR-004] E2E tests validate logging hooks work end-to-end in `tests/e2e/knowledge_router/test_qa_logging.py`

**Checkpoint**: All Q&A logged with no data loss, retrievable by feature_id

---

## Phase 7: User Story 5 - Dispatch Execution Tasks to Specialists (Priority: P2)

**Goal**: Execution tasks from tasks.md are dispatched to specialist agents with scoped access

**Journey ID**: KR-005

**Independent Test**: Dispatch task to @dede, verify they receive only task context and can only modify `src/`

### Tests for KR-005

- [ ] T061 [P] [KR-005] Unit test for ExecutionTask model in `tests/unit/knowledge_router/test_models_execution.py`
- [ ] T062 [P] [KR-005] Unit test for scope enforcement (allowed paths) in `tests/unit/knowledge_router/test_dispatcher.py`
- [ ] T063 [P] [KR-005] Unit test for scope violation detection in `tests/unit/knowledge_router/test_dispatcher.py`
- [ ] T064 [P] [KR-005] Integration test for execution agent dispatch in `tests/integration/knowledge_router/test_execution_dispatch.py`

### Implementation for KR-005

- [ ] T065 [KR-005] Implement ExecutionTask model in `src/knowledge_router/models.py`
- [ ] T066 [KR-005] Implement ExecutionResult model in `src/knowledge_router/models.py`
- [ ] T067 [KR-005] Implement ExecutionAgentDefinition in `src/knowledge_router/config.py`
- [ ] T068 [KR-005] Implement scope enforcement in `src/knowledge_router/dispatcher.py`
- [ ] T069 [KR-005] Implement `dispatch_task()` method in `src/knowledge_router/router.py`
- [ ] T070 [KR-005] Add execution agent prompts (task context only) in `src/knowledge_router/prompts.py`
- [ ] T071 [KR-005] Implement scope validation on agent file changes in `src/knowledge_router/dispatcher.py`

**Checkpoint**: Execution tasks dispatch correctly, scope violations blocked and logged

---

## Phase 8: User Story 6 - Configure Routing Rules (Priority: P2)

**Goal**: Administrators can configure routing rules via YAML

**Journey ID**: KR-006

**Independent Test**: Modify routing config, verify questions route according to new rules

### Tests for KR-006

- [ ] T072 [P] [KR-006] Unit test for YAML config parsing in `tests/unit/knowledge_router/test_config.py`
- [ ] T073 [P] [KR-006] Unit test for topic-to-agent mapping in `tests/unit/knowledge_router/test_config.py`
- [ ] T074 [P] [KR-006] Unit test for model selection per agent in `tests/unit/knowledge_router/test_config.py`
- [ ] T075 [P] [KR-006] Unit test for timeout configuration in `tests/unit/knowledge_router/test_config.py`

### Implementation for KR-006

- [ ] T076 [KR-006] Implement `configure_routing()` method in `src/knowledge_router/router.py`
- [ ] T077 [KR-006] Implement config validation (agent exists, valid thresholds) in `src/knowledge_router/config.py`
- [ ] T078 [KR-006] Implement runtime config reload in `src/knowledge_router/config.py`
- [ ] T079 [KR-006] Create sample `config/routing.yaml` with all options documented

**Checkpoint**: Routing fully configurable via YAML, invalid config rejected with clear errors

---

## Phase 9: User Story 7 - Generate Retrospective Report (Priority: P2)

**Goal**: Generate analysis report from Q&A logs with improvement recommendations

**Journey ID**: KR-007

**Independent Test**: Complete feature with varied confidence levels, generate report, verify insights

### Tests for KR-007

- [ ] T080 [P] [KR-007] Unit test for RetroReport model in `tests/unit/knowledge_router/test_retro.py`
- [ ] T081 [P] [KR-007] Unit test for confidence statistics calculation in `tests/unit/knowledge_router/test_retro.py`
- [ ] T082 [P] [KR-007] Unit test for escalation pattern detection in `tests/unit/knowledge_router/test_retro.py`
- [ ] T083 [P] [KR-007] Unit test for recommendation generation in `tests/unit/knowledge_router/test_retro.py`

### Implementation for KR-007

- [ ] T084 [KR-007] Implement ImprovementRecommendation model in `src/knowledge_router/models.py`
- [ ] T085 [KR-007] Implement RetroReport model in `src/knowledge_router/models.py`
- [ ] T086 [KR-007] Implement RetroGenerator class in `src/knowledge_router/retro.py`
- [ ] T087 [KR-007] Implement `generate_retro()` method in `src/knowledge_router/router.py`
- [ ] T088 [KR-007] Implement statistics aggregation (avg confidence, escalation rate) in `src/knowledge_router/retro.py`
- [ ] T089 [KR-007] Implement pattern detection (low-confidence topics, common context adds) in `src/knowledge_router/retro.py`
- [ ] T090 [KR-007] Implement recommendation engine in `src/knowledge_router/retro.py`

**Checkpoint**: Retro reports generated with actionable recommendations

---

## Phase 10: User Story 8 - Handle Agent Unavailability (Priority: P3)

**Goal**: Graceful degradation when knowledge agents timeout or fail

**Journey ID**: KR-008

**Independent Test**: Simulate agent timeout, verify graceful escalation to human

### Tests for KR-008

- [ ] T091 [P] [KR-008] Unit test for agent timeout detection in `tests/unit/knowledge_router/test_dispatcher.py`
- [ ] T092 [P] [KR-008] Unit test for fallback agent routing in `tests/unit/knowledge_router/test_router.py`
- [ ] T093 [P] [KR-008] Unit test for error escalation to human in `tests/unit/knowledge_router/test_escalation.py`

### Implementation for KR-008

- [ ] T094 [KR-008] Implement timeout handling in `src/knowledge_router/dispatcher.py`
- [ ] T095 [KR-008] Implement fallback agent configuration in `src/knowledge_router/config.py`
- [ ] T096 [KR-008] Implement `get_agent_status()` method in `src/knowledge_router/router.py`
- [ ] T097 [KR-008] Implement graceful escalation with "unavailable" note in `src/knowledge_router/escalation.py`
- [ ] T098 [KR-008] Add retry logic with configurable attempts in `src/knowledge_router/dispatcher.py`

**Checkpoint**: Agent failures handled gracefully, never block the workflow

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and integration

### User Journey Documentation (REQUIRED per Constitution Principle XI)

- [X] T099 [P] Create `docs/user-journeys/KR-001-route-question.md`
- [X] T100 [P] Create `docs/user-journeys/KR-002-validate-confidence.md`
- [X] T101 [P] Create `docs/user-journeys/KR-003-escalate-human.md`
- [X] T102 [P] Create `docs/user-journeys/KR-004-log-qa.md`
- [ ] T103 [P] Create `docs/user-journeys/KR-005-dispatch-task.md` (P2 - not implemented)
- [ ] T104 [P] Create `docs/user-journeys/KR-006-configure-routing.md` (P2 - not implemented)
- [ ] T105 [P] Create `docs/user-journeys/KR-007-generate-retro.md` (P2 - not implemented)
- [ ] T106 [P] Create `docs/user-journeys/KR-008-handle-timeout.md` (P3 - not implemented)
- [X] T107 Update `docs/user-journeys/JOURNEYS.md` with KR journeys
- [X] T108 Add `@pytest.mark.journey("KR-XXX")` markers to all E2E tests

### Module Documentation

- [ ] T109 Create module README in `src/knowledge_router/README.md`
- [ ] T110 [P] Add docstrings to all public methods
- [ ] T111 [P] Update root CLAUDE.md with knowledge_router module info

### Quality & Validation

- [ ] T112 Run `uv run ruff check src/knowledge_router/`
- [ ] T113 Run `uv run mypy src/knowledge_router/`
- [ ] T114 Run full test suite: `uv run pytest tests/ -v`
- [ ] T115 Run quickstart.md validation end-to-end
- [ ] T116 Security review: no secrets in code, inputs validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phases 3-10)**: All depend on Foundational completion
  - P1 stories (KR-001 to KR-004): Core MVP, complete first
  - P2 stories (KR-005 to KR-007): Enhanced features, after P1
  - P3 stories (KR-008): Robustness, after P2
- **Polish (Phase 11)**: Depends on all stories complete

### User Story Dependencies

| Story | Depends On | Can Run In Parallel With |
|-------|------------|--------------------------|
| KR-001 (Route Questions) | Foundation | - |
| KR-002 (Validate Answers) | KR-001 | - |
| KR-003 (Human Escalation) | KR-002 | - |
| KR-004 (Q&A Logging) | Foundation | KR-001, KR-002, KR-003 |
| KR-005 (Dispatch Tasks) | Foundation | KR-001-004 |
| KR-006 (Configure Routing) | KR-001 | KR-002-005 |
| KR-007 (Retro Report) | KR-004 | KR-005, KR-006 |
| KR-008 (Agent Unavailable) | KR-001, KR-003 | KR-004-007 |

### Critical Path (MVP)

```
Foundation → KR-001 → KR-002 → KR-003 → KR-004
                                         ↓
                                   MVP COMPLETE
```

### Parallel Opportunities

- All [P] tasks within a phase can run in parallel
- KR-004 (logging) can proceed in parallel with KR-001-003 once foundation done
- KR-005-008 can run in parallel after core P1 stories complete

---

## Summary

| Phase | Tasks | Priority | Estimated Effort |
|-------|-------|----------|------------------|
| Setup | T001-T004 | - | Low |
| Foundation | T005-T019 | - | Medium |
| KR-001: Route Questions | T020-T029 | P1 | Medium |
| KR-002: Validate Answers | T030-T038 | P1 | Medium |
| KR-003: Human Escalation | T039-T050 | P1 | High |
| KR-004: Q&A Logging | T051-T060 | P1 | Medium |
| KR-005: Dispatch Tasks | T061-T071 | P2 | High |
| KR-006: Configure Routing | T072-T079 | P2 | Low |
| KR-007: Retro Report | T080-T090 | P2 | Medium |
| KR-008: Agent Unavailable | T091-T098 | P3 | Low |
| Polish | T099-T116 | - | Medium |

**Total Tasks**: 116
**MVP Tasks (P1)**: T001-T060 (60 tasks)
**Full Feature**: T001-T116 (116 tasks)
