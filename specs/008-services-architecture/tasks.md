# Tasks: Services Architecture Refactor

**Input**: Design documents from `/specs/008-services-architecture/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as this is a significant architectural change requiring TDD per constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Journey ID Convention

**Domain**: SVC (Services Architecture)

| User Story | Journey ID | Journey Name |
|------------|------------|--------------|
| US1 | SVC-001 | Orchestrator Workflow Execution |
| US2 | SVC-002 | Expert Agent Consultation |
| US3 | SVC-003 | Human Review Escalation |
| US4 | SVC-004 | Multi-Turn Session |
| US5 | SVC-005 | Stateless Agent Invocation |
| US6 | SVC-006 | Local Development Setup |
| US7 | SVC-007 | Audit Log Query |

---

## Phase 0: Documentation Cleanup (Pre-Implementation)

**Purpose**: Prepare documentation for services architecture transition

- [X] T001 Add deprecation banner to docs/modules/orchestrator.md: "DEPRECATED: See docs/services/orchestrator.md"
- [X] T002 [P] Add deprecation banner to docs/modules/agent-hub.md: "DEPRECATED: See docs/services/agent-hub.md"
- [X] T003 [P] Create docs/services/ directory structure with README.md placeholder
- [X] T004 Create docs/services/agents/ directory structure with README.md placeholder
- [X] T005 Add "Services Architecture (coming)" section to docs/architecture/system-overview.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T006 Create services/ directory structure per plan.md project structure
- [X] T007 Create services/shared/pyproject.toml with Pydantic v2, httpx dependencies
- [X] T008 [P] Create services/orchestrator/pyproject.toml with FastAPI, SQLAlchemy dependencies
- [X] T009 [P] Create services/agent-hub/pyproject.toml with FastAPI, SQLAlchemy dependencies
- [X] T010 [P] Create services/agents/baron/pyproject.toml with FastAPI, claude-code-sdk dependencies
- [X] T011 Configure ruff and mypy for services/ directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared contracts package that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Shared Models (services/shared/)

- [X] T012 Create services/shared/src/contracts/__init__.py with package exports
- [X] T013 [P] Create services/shared/src/contracts/models/workflow.py with WorkflowType, WorkflowStatus, CreateWorkflowRequest, WorkflowResponse per data-model.md
- [X] T014 [P] Create services/shared/src/contracts/models/session.py with SessionStatus, Session, Message, MessageRole per data-model.md
- [X] T015 [P] Create services/shared/src/contracts/models/escalation.py with EscalationStatus, HumanAction, Escalation per data-model.md
- [X] T016 [P] Create services/shared/src/contracts/models/agent.py with InvokeRequest, InvokeResponse per contracts/agent-service.yaml
- [X] T017 Create services/shared/src/contracts/models/__init__.py exporting all models

### Shared Clients (services/shared/)

- [X] T018 Create services/shared/src/contracts/clients/__init__.py with client exports
- [X] T019 [P] Create services/shared/src/contracts/clients/agent.py with AgentClient for generic agent invocation
- [X] T020 [P] Create services/shared/src/contracts/clients/agent_hub.py with AgentHubClient for hub communication
- [X] T021 [P] Create services/shared/src/contracts/clients/orchestrator.py with OrchestratorClient

### Shared Configuration

- [X] T022 Create services/shared/src/contracts/config.py with ServiceConfig base class and environment loading

**Checkpoint**: Shared contracts ready - user story implementation can now begin

---

## Phase 3: User Story 5 - Stateless Agent Services (Priority: P1) 🎯 MVP

**Goal**: Baron agent service receives requests with all context, processes via Claude SDK, returns complete response

**Journey ID**: SVC-005

**Independent Test**: Invoke Baron directly with a complete request, verify it returns a complete response without prior state

### Tests for User Story 5

> **NOTE: Write tests FIRST (TDD). E2E tests MUST have journey markers.**

- [X] T023 [P] [US5] Contract test for POST /invoke in services/agents/baron/tests/contract/test_invoke.py
- [X] T024 [P] [US5] Contract test for GET /health in services/agents/baron/tests/contract/test_health.py
- [X] T025 [P] [US5] Integration test for stateless invocation in services/agents/baron/tests/integration/test_stateless.py
- [X] T026 [US5] E2E test with `@pytest.mark.journey("SVC-005")` in tests/e2e/test_baron_stateless.py

### Implementation for User Story 5

- [X] T027 [P] [US5] Create services/agents/baron/src/__init__.py with package metadata
- [X] T028 [P] [US5] Create services/agents/baron/src/core/prompts.py with system prompts for specify, plan, tasks, implement workflows
- [X] T029 [US5] Create services/agents/baron/src/core/agent.py with SDK agent wrapper using claude-code-sdk (depends on T028)
- [X] T030 [US5] Create services/agents/baron/src/api/invoke.py with POST /invoke endpoint per contracts/agent-service.yaml
- [X] T031 [P] [US5] Create services/agents/baron/src/api/health.py with GET /health endpoint
- [X] T032 [US5] Create services/agents/baron/src/main.py FastAPI app mounting invoke and health routers
- [X] T033 [US5] Create services/agents/baron/Dockerfile for containerized deployment

### Documentation for User Story 5

- [X] T034 [US5] Create docs/user-journeys/SVC-005-stateless-agent.md with journey steps and test mapping

**Checkpoint**: User Story 5 is complete when:
- All tests pass (including E2E with SVC-005 marker)
- Baron can be invoked directly with stateless requests
- Documentation exists

---

## Phase 4: User Story 2 - Agent-to-Agent Communication (Priority: P1)

**Goal**: Agent Hub routes requests to appropriate agent, validates confidence, returns response

**Journey ID**: SVC-002

**Independent Test**: Have Baron ask an architecture question via Agent Hub, verify it routes to correct agent and returns answer

### Tests for User Story 2

> **NOTE: Write tests FIRST (TDD). E2E tests MUST have journey markers.**

- [X] T035 [P] [US2] Contract test for POST /invoke/{agent} in services/agent-hub/tests/contract/test_invoke.py
- [X] T036 [P] [US2] Contract test for POST /ask/{topic} in services/agent-hub/tests/contract/test_ask.py
- [X] T037 [P] [US2] Integration test for confidence validation in services/agent-hub/tests/integration/test_confidence.py
- [X] T038 [US2] E2E test with `@pytest.mark.journey("SVC-002")` in tests/e2e/test_agent_consultation.py

### Implementation for User Story 2

- [X] T039 [P] [US2] Create services/agent-hub/src/__init__.py with package metadata
- [X] T040 [P] [US2] Create services/agent-hub/src/core/router.py with agent routing logic (topic → agent mapping)
- [X] T041 [P] [US2] Create services/agent-hub/src/core/validator.py with confidence threshold validation
- [X] T042 [US2] Create services/agent-hub/src/clients/agents.py with HTTP client for agent service calls (depends on T019)
- [X] T043 [US2] Create services/agent-hub/src/api/invoke.py with POST /invoke/{agent} endpoint per contracts/agent-hub.yaml
- [X] T044 [US2] Create services/agent-hub/src/api/ask.py with POST /ask/{topic} endpoint per contracts/agent-hub.yaml (depends on T040, T041)
- [X] T045 [P] [US2] Create services/agent-hub/src/api/health.py with GET /health endpoint
- [X] T046 [US2] Create services/agent-hub/src/main.py FastAPI app mounting all routers

### Documentation for User Story 2

- [X] T047 [US2] Create docs/user-journeys/SVC-002-agent-consultation.md with journey steps and test mapping

**Checkpoint**: User Story 2 is complete when:
- All tests pass (including E2E with SVC-002 marker)
- Agent Hub routes to agents correctly
- Confidence validation works
- Documentation exists

---

## Phase 5: User Story 1 - Orchestrator Invokes Agent via Agent Hub (Priority: P1) 🎯 MVP

**Goal**: Orchestrator manages workflow state and invokes agents exclusively through Agent Hub

**Journey ID**: SVC-001

**Independent Test**: Trigger a SpecKit workflow, verify request flows Orchestrator → Agent Hub → Baron → response

### Tests for User Story 1

> **NOTE: Write tests FIRST (TDD). E2E tests MUST have journey markers.**

- [X] T048 [P] [US1] Contract test for POST /workflows in services/orchestrator/tests/contract/test_workflows.py
- [X] T049 [P] [US1] Contract test for GET /workflows/{id} in services/orchestrator/tests/contract/test_get_workflow.py
- [X] T050 [P] [US1] Contract test for POST /workflows/{id}/advance in services/orchestrator/tests/contract/test_advance.py
- [X] T051 [P] [US1] Integration test for workflow state machine in services/orchestrator/tests/integration/test_state_machine.py
- [X] T052 [US1] E2E test with `@pytest.mark.journey("SVC-001")` in tests/e2e/test_orchestrator_workflow.py

### Implementation for User Story 1

- [X] T053 [P] [US1] Create services/orchestrator/src/__init__.py with package metadata
- [X] T054 [P] [US1] Create services/orchestrator/src/db/models.py with SQLAlchemy Workflow, WorkflowHistory models per data-model.md
- [X] T055 [P] [US1] Create services/orchestrator/src/db/session.py with SQLite database session setup
- [X] T056 [US1] Create services/orchestrator/src/core/state_machine.py with workflow state management (depends on T054)
- [X] T057 [US1] Create services/orchestrator/src/core/phase_executor.py with phase execution logic calling Agent Hub (depends on T020)
- [X] T058 [US1] Create services/orchestrator/src/clients/agent_hub.py HTTP client wrapper using shared client (depends on T020)
- [X] T059 [US1] Create services/orchestrator/src/api/workflows.py with /workflows endpoints per contracts/orchestrator.yaml (depends on T056, T057)
- [X] T060 [P] [US1] Create services/orchestrator/src/api/health.py with GET /health endpoint
- [X] T061 [US1] Create services/orchestrator/src/main.py FastAPI app mounting all routers
- [X] T062 [US1] Create services/orchestrator/Dockerfile for containerized deployment

### Documentation for User Story 1

- [X] T063 [US1] Create docs/user-journeys/SVC-001-orchestrator-workflow.md with journey steps and test mapping
- [X] T064 [US1] Create docs/services/orchestrator.md with API reference, configuration, examples

**Checkpoint**: User Story 1 is complete when:
- All tests pass (including E2E with SVC-001 marker)
- Complete workflow flows from Orchestrator → Agent Hub → Baron → response
- Documentation exists

---

## Phase 6: User Story 4 - Session Management (Priority: P2)

**Goal**: Agent Hub maintains session state for multi-turn conversations with context preservation

**Journey ID**: SVC-004

**Independent Test**: Send follow-up question with session ID, verify context from previous question is included

### Tests for User Story 4

> **NOTE: Write tests FIRST (TDD). E2E tests MUST have journey markers.**

- [X] T065 [P] [US4] Contract test for POST /sessions in services/agent-hub/tests/contract/test_sessions_create.py
- [X] T066 [P] [US4] Contract test for GET /sessions/{id} in services/agent-hub/tests/contract/test_sessions_get.py
- [X] T067 [P] [US4] Contract test for DELETE /sessions/{id} in services/agent-hub/tests/contract/test_sessions_close.py
- [X] T068 [P] [US4] Integration test for context preservation in services/agent-hub/tests/integration/test_session_context.py
- [X] T069 [US4] E2E test with `@pytest.mark.journey("SVC-004")` in tests/e2e/test_multi_turn_session.py

### Implementation for User Story 4

- [X] T070 [P] [US4] Create services/agent-hub/src/db/models.py with SQLAlchemy Session, Message models per data-model.md
- [X] T071 [P] [US4] Create services/agent-hub/src/db/session.py with SQLite database session setup
- [X] T072 [US4] Create services/agent-hub/src/core/session_manager.py with session lifecycle management (depends on T070)
- [X] T073 [US4] Create services/agent-hub/src/api/sessions.py with /sessions endpoints per contracts/agent-hub.yaml (depends on T072)
- [X] T074 [US4] Update services/agent-hub/src/api/ask.py to include session context when session_id is provided
- [X] T075 [US4] Update services/agent-hub/src/main.py to mount sessions router

### Documentation for User Story 4

- [X] T076 [US4] Create docs/user-journeys/SVC-004-multi-turn-session.md with journey steps and test mapping
- [X] T077 [US4] Update docs/services/agent-hub.md with sessions section

**Checkpoint**: User Story 4 is complete when:
- All tests pass (including E2E with SVC-004 marker)
- Sessions preserve context across 5 consecutive exchanges (per SC-006)
- Documentation exists

---

## Phase 7: User Story 3 - Human Escalation (Priority: P2)

**Goal**: Low-confidence answers trigger GitHub comment escalation, humans respond via CONFIRM/CORRECT/ADD_CONTEXT

**Journey ID**: SVC-003

**Independent Test**: Trigger low-confidence response, verify GitHub comment is created, submit human response

### Tests for User Story 3

> **NOTE: Write tests FIRST (TDD). E2E tests MUST have journey markers.**

- [X] T078 [P] [US3] Contract test for GET /escalations/{id} in services/agent-hub/tests/contract/test_escalations_get.py
- [X] T079 [P] [US3] Contract test for POST /escalations/{id} in services/agent-hub/tests/contract/test_escalations_respond.py
- [X] T080 [P] [US3] Integration test for escalation creation on low confidence in services/agent-hub/tests/integration/test_escalation_create.py
- [X] T081 [P] [US3] Integration test for GitHub comment posting in services/agent-hub/tests/integration/test_github_escalation.py
- [X] T082 [US3] E2E test with `@pytest.mark.journey("SVC-003")` in tests/e2e/test_human_escalation.py

### Implementation for User Story 3

- [ ] T083 [P] [US3] Add Escalation model to services/agent-hub/src/db/models.py per data-model.md
- [ ] T084 [US3] Create services/agent-hub/src/core/escalation.py with escalation handling logic (depends on T083)
- [ ] T085 [US3] Create services/agent-hub/src/clients/github.py with GitHub API client for comment posting
- [ ] T086 [US3] Create services/agent-hub/src/api/escalations.py with /escalations endpoints per contracts/agent-hub.yaml (depends on T084, T085)
- [ ] T087 [US3] Update services/agent-hub/src/api/ask.py to create escalation when confidence below threshold
- [ ] T088 [US3] Update services/agent-hub/src/main.py to mount escalations router

### Documentation for User Story 3

- [ ] T089 [US3] Create docs/user-journeys/SVC-003-human-escalation.md with journey steps and test mapping
- [ ] T090 [US3] Update docs/services/agent-hub.md with escalation section

**Checkpoint**: User Story 3 is complete when:
- All tests pass (including E2E with SVC-003 marker)
- Escalations are created within 5 seconds of low confidence (per SC-005)
- Human responses are processed correctly
- Documentation exists

---

## Phase 8: User Story 6 - Docker Compose (Priority: P3)

**Goal**: Developer runs `docker-compose up` to start all services locally

**Journey ID**: SVC-006

**Independent Test**: Fresh clone, run `docker-compose up`, verify all services start and communicate

### Tests for User Story 6

> **NOTE: Write tests FIRST (TDD). E2E tests MUST have journey markers.**

- [ ] T091 [US6] E2E test with `@pytest.mark.journey("SVC-006")` in tests/e2e/test_docker_compose.py

### Implementation for User Story 6

- [ ] T092 [P] [US6] Create services/agent-hub/Dockerfile
- [ ] T093 [US6] Create docker-compose.yml with orchestrator, agent-hub, baron services and dependencies
- [ ] T094 [US6] Create .env.example with required environment variables
- [ ] T095 [US6] Create docker-compose.dev.yml with volume mounts for hot reload

### Documentation for User Story 6

- [ ] T096 [US6] Create docs/user-journeys/SVC-006-local-dev-setup.md with journey steps
- [ ] T097 [US6] Update docs/getting-started/quickstart.md with Docker Compose setup

**Checkpoint**: User Story 6 is complete when:
- All services start with single command within 60 seconds (per SC-001)
- Documentation exists

---

## Phase 9: User Story 7 - Audit Logging (Priority: P3)

**Goal**: All agent exchanges logged to JSONL with complete context

**Journey ID**: SVC-007

**Independent Test**: Trigger agent exchanges, verify log entries contain all required fields

### Tests for User Story 7

> **NOTE: Write tests FIRST (TDD). E2E tests MUST have journey markers.**

- [ ] T098 [P] [US7] Unit test for audit log format in services/agent-hub/tests/unit/test_audit_logger.py
- [ ] T099 [P] [US7] Integration test for log writing in services/agent-hub/tests/integration/test_audit_log.py
- [ ] T100 [US7] E2E test with `@pytest.mark.journey("SVC-007")` in tests/e2e/test_audit_logging.py

### Implementation for User Story 7

- [ ] T101 [P] [US7] Create services/agent-hub/src/logging/__init__.py
- [ ] T102 [US7] Create services/agent-hub/src/logging/audit.py with JSONL logger per data-model.md AuditLog schema
- [ ] T103 [US7] Update services/agent-hub/src/api/ask.py to log all exchanges via audit logger
- [ ] T104 [US7] Update services/agent-hub/src/api/invoke.py to log all invocations

### Documentation for User Story 7

- [ ] T105 [US7] Create docs/user-journeys/SVC-007-audit-log-query.md with journey steps
- [ ] T106 [US7] Update docs/services/agent-hub.md with audit logging section

**Checkpoint**: User Story 7 is complete when:
- 100% of invocations are logged (per SC-007)
- Logs are queryable by feature ID
- Documentation exists

---

## Phase 10: Additional Agents (P3)

**Purpose**: Add Duc and Marie agent services

- [ ] T107 [P] Create services/agents/duc/ with same structure as baron (api/, core/, tests/)
- [ ] T108 [P] Create services/agents/marie/ with same structure as baron (api/, core/, tests/)
- [ ] T109 Update services/agent-hub/src/core/router.py to include duc and marie routing
- [ ] T110 [P] Create services/agents/duc/Dockerfile
- [ ] T111 [P] Create services/agents/marie/Dockerfile
- [ ] T112 Update docker-compose.yml to include duc and marie services
- [ ] T113 [P] Create docs/services/agents/duc.md
- [ ] T114 [P] Create docs/services/agents/marie.md

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### User Journey Index Update

- [ ] T115 Update docs/user-journeys/JOURNEYS.md with all SVC-* journeys

### Documentation Finalization

**Module/Service Documentation**:
- [ ] T116 [P] Create services/orchestrator/README.md with quick start and API reference
- [ ] T117 [P] Create services/agent-hub/README.md with quick start and API reference
- [ ] T118 [P] Create services/agents/baron/README.md with quick start and API reference
- [ ] T119 Create docs/services/README.md with complete services overview

**Architecture Documentation**:
- [ ] T120 Update docs/architecture/system-overview.md with services architecture diagram
- [ ] T121 Create docs/architecture/services-communication.md (replaces module-interactions.md)

**Configuration Documentation**:
- [ ] T122 Update docs/configuration/environment-variables.md with all service env vars
- [ ] T123 Create docs/configuration/docker-compose.md with docker-compose guide

**Testing Documentation**:
- [ ] T124 Update docs/testing/running-tests.md with services test commands
- [ ] T125 Update docs/testing/writing-tests.md with services test patterns

### Quality & Validation

- [ ] T126 Run specs/008-services-architecture/quickstart.md validation
- [ ] T127 Run full E2E test suite to verify SC-002 (complete SpecKit workflow)
- [ ] T128 Performance test for SC-003 (<1s overhead) and SC-004 (10 concurrent workflows)

---

## Phase 12: Cleanup (Post-Implementation)

**Purpose**: Remove deprecated documentation

- [ ] T129 Delete docs/modules/orchestrator.md
- [ ] T130 [P] Delete docs/modules/agent-hub.md
- [ ] T131 [P] Delete docs/modules/README.md
- [ ] T132 Delete docs/architecture/module-interactions.md
- [ ] T133 Move docs/user-journeys/AH-*.md to docs/archive/
- [ ] T134 [P] Move docs/user-journeys/BRN-*.md to docs/archive/
- [ ] T135 [P] Move docs/user-journeys/ORC-*.md to docs/archive/ (except those still valid)
- [ ] T136 Verify all docs links are valid and no references to old src/orchestrator or src/agent_hub
- [ ] T137 Update project README.md with services architecture entry point

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Doc Cleanup)**: No dependencies - can start immediately
- **Phase 1 (Setup)**: No dependencies - can start immediately (parallel with Phase 0)
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - **BLOCKS all user stories**
- **Phases 3-5 (P1 Stories)**: All depend on Phase 2 completion
  - Phase 3 (US5) must complete before Phase 4 (US2) - Baron needed for Agent Hub testing
  - Phase 4 (US2) must complete before Phase 5 (US1) - Agent Hub needed for Orchestrator
- **Phases 6-7 (P2 Stories)**: Depend on Phase 4 (Agent Hub exists)
  - Can run in parallel with each other
- **Phases 8-9 (P3 Stories)**: Depend on Phases 3-5 (core services exist)
  - Can run in parallel with each other
- **Phase 10 (Additional Agents)**: Depends on Phase 3 (Baron pattern established)
- **Phase 11 (Polish)**: Depends on all desired user stories being complete
- **Phase 12 (Cleanup)**: Depends on Phase 11 (all docs created first)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- User journey doc MUST be created before story is marked complete

### Parallel Opportunities

Within Phase 2:
- T013, T014, T015, T016 (shared models) can run in parallel
- T019, T020, T021 (shared clients) can run in parallel

Within Phase 3 (US5):
- T023, T024, T025 (tests) can run in parallel
- T027, T028, T031 can run in parallel before T029, T030

Within Phase 4 (US2):
- T035, T036, T037 (tests) can run in parallel
- T039, T040, T041, T045 can run in parallel

Within Phases 6-7 (P2 Stories):
- Both phases can run in parallel (different parts of Agent Hub)

Within Phases 8-9 (P3 Stories):
- Both phases can run in parallel

Within Phase 10:
- Duc and Marie can be developed in parallel

---

## Task Count Summary

| Phase | Tasks | Parallel | Sequential |
|-------|-------|----------|------------|
| Phase 0: Doc Cleanup | 5 | 3 | 2 |
| Phase 1: Setup | 6 | 4 | 2 |
| Phase 2: Foundational | 11 | 8 | 3 |
| Phase 3: US5 (Baron) | 12 | 7 | 5 |
| Phase 4: US2 (Agent Hub routing) | 13 | 8 | 5 |
| Phase 5: US1 (Orchestrator) | 17 | 9 | 8 |
| Phase 6: US4 (Sessions) | 13 | 7 | 6 |
| Phase 7: US3 (Escalation) | 13 | 6 | 7 |
| Phase 8: US6 (Docker) | 6 | 1 | 5 |
| Phase 9: US7 (Audit) | 9 | 4 | 5 |
| Phase 10: Additional Agents | 8 | 6 | 2 |
| Phase 11: Polish | 13 | 4 | 9 |
| Phase 12: Cleanup | 9 | 5 | 4 |
| **Total** | **135** | **72** | **63** |

## MVP Scope

For minimum viable product, complete through Phase 5:
- Phase 0: Doc Cleanup (5 tasks)
- Phase 1: Setup (6 tasks)
- Phase 2: Foundational (11 tasks)
- Phase 3: US5 - Baron stateless agent (12 tasks)
- Phase 4: US2 - Agent Hub routing (13 tasks)
- Phase 5: US1 - Orchestrator workflow (17 tasks)

**MVP Total**: 64 tasks

This delivers:
- ✅ Complete SpecKit workflow via services (SC-002)
- ✅ Stateless agent invocation (US5)
- ✅ Agent-to-agent communication (US2)
- ✅ Orchestrator workflow management (US1)
- ✅ Foundation for P2/P3 features

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- User journey doc is part of each story's "definition of done"
- Documentation in docs/ is REQUIRED per Constitution Principle XI
