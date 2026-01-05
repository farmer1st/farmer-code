# Tasks: Agent Hub Refactor

**Input**: Design documents from `/specs/005-agent-hub-refactor/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: TDD approach - tests written first per Constitution Principle I.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Include exact file paths in descriptions

## Journey ID Convention

- **Domain**: AH (Agent Hub)
- Journey IDs: AH-001 through AH-005 (assigned in plan.md)

---

## Phase 1: Setup (Module Rename)

**Purpose**: Rename knowledge_router to agent_hub and update all references

- [X] T001 Rename src/knowledge_router/ to src/agent_hub/ using git mv
- [X] T002 [P] Rename tests/unit/knowledge_router/ to tests/unit/agent_hub/
- [X] T003 [P] Rename tests/integration/knowledge_router/ to tests/integration/agent_hub/
- [X] T004 [P] Rename tests/contract/knowledge_router/ to tests/contract/agent_hub/
- [X] T005 [P] Rename tests/e2e/knowledge_router/ to tests/e2e/agent_hub/
- [X] T006 Update all import statements in src/agent_hub/*.py from knowledge_router to agent_hub
- [X] T007 Update all import statements in tests/*/agent_hub/*.py from knowledge_router to agent_hub
- [X] T008 Rename dispatcher.py to router.py in src/agent_hub/
- [X] T009 Rename router.py to hub.py in src/agent_hub/
- [X] T010 Rename KnowledgeRouterService class to AgentHub in src/agent_hub/hub.py
- [X] T011 Rename AgentDispatcher class to AgentRouter in src/agent_hub/router.py
- [X] T012 Update __init__.py exports in src/agent_hub/__init__.py
- [X] T013 Run tests to verify rename doesn't break existing functionality

**Checkpoint**: All tests pass with new module names

---

## Phase 2: Foundational (New Models and Infrastructure)

**Purpose**: Add new models and session infrastructure required by all user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Add Session model to src/agent_hub/models.py with fields: id, agent_id, feature_id, messages, created_at, updated_at, status
- [X] T015 [P] Add Message model to src/agent_hub/models.py with fields: role, content, timestamp, metadata
- [X] T016 [P] Add MessageRole enum to src/agent_hub/models.py (USER, ASSISTANT, HUMAN)
- [X] T017 [P] Add SessionStatus enum to src/agent_hub/models.py (ACTIVE, CLOSED, EXPIRED)
- [X] T018 [P] Add HubResponse model to src/agent_hub/models.py with fields: answer, rationale, confidence, uncertainty_reasons, session_id, status, escalation_id
- [X] T019 [P] Add ResponseStatus enum to src/agent_hub/models.py (RESOLVED, PENDING_HUMAN, NEEDS_REROUTE)
- [X] T020 [P] Add EscalationStatus model to src/agent_hub/models.py with fields: escalation_id, status, action, corrected_answer, additional_context, resolved_at
- [X] T021 Add SessionNotFoundError to src/agent_hub/exceptions.py
- [X] T022 Add SessionClosedError to src/agent_hub/exceptions.py
- [X] T023 Add UnknownTopicError to src/agent_hub/exceptions.py
- [X] T024 Run tests to verify new models work correctly

**Checkpoint**: Foundation ready - all new models defined, user story implementation can begin

---

## Phase 3: User Story 1 - Route Questions to Experts (Priority: P1) 🎯 MVP

**Goal**: Orchestration agents can route questions to domain experts via ask_expert

**Journey ID**: AH-001

**Independent Test**: Send question with topic, verify correct agent receives it and returns answer

### Tests for User Story 1

> **NOTE**: Write tests FIRST (TDD). E2E tests MUST have journey markers.

- [X] T025 [P] [US1] Unit test for ask_expert routing logic in tests/unit/agent_hub/test_hub.py
- [X] T026 [P] [US1] Unit test for topic-to-agent mapping in tests/unit/agent_hub/test_router.py
- [X] T027 [P] [US1] Contract test for AgentHub.ask_expert() in tests/contract/agent_hub/test_hub_response_schema.py
- [X] T028 [US1] E2E test with `@pytest.mark.journey("AH-001")` in tests/e2e/agent_hub/test_route_question.py

### Implementation for User Story 1

- [X] T029 [US1] Implement ask_expert() method in src/agent_hub/hub.py
- [X] T030 [US1] Update AgentRouter to support new routing interface in src/agent_hub/router.py
- [X] T031 [US1] Add topic validation with UnknownTopicError in src/agent_hub/hub.py
- [X] T032 [US1] Return HubResponse with session_id from ask_expert in src/agent_hub/hub.py

### Documentation for User Story 1

- [X] T033 [US1] Create user journey doc in docs/user-journeys/AH-001-route-question.md

**Checkpoint**: User Story 1 complete when:
- All routing tests pass (including E2E with AH-001 marker)
- Questions route to correct agents by topic
- HubResponse returned with session_id

---

## Phase 4: User Story 2 - Maintain Conversation Sessions (Priority: P1)

**Goal**: Agent Hub maintains conversation sessions with full context preservation

**Journey ID**: AH-002

**Independent Test**: Send question, add feedback to session, verify context preserved

### Tests for User Story 2

> **NOTE**: Write tests FIRST (TDD). E2E tests MUST have journey markers.

- [X] T034 [P] [US2] Unit test for SessionManager.create() in tests/unit/agent_hub/test_session.py
- [X] T035 [P] [US2] Unit test for SessionManager.add_message() in tests/unit/agent_hub/test_session.py
- [X] T036 [P] [US2] Unit test for SessionManager.get() and close() in tests/unit/agent_hub/test_session.py
- [X] T037 [P] [US2] Unit test for session ID in ask_expert response in tests/unit/agent_hub/test_hub.py
- [X] T038 [US2] E2E test with `@pytest.mark.journey("AH-002")` in tests/e2e/agent_hub/test_session_management.py

### Implementation for User Story 2

- [X] T039 [US2] Create SessionManager class in src/agent_hub/session.py
- [X] T040 [US2] Implement create() method in SessionManager in src/agent_hub/session.py
- [X] T041 [US2] Implement get() method in SessionManager in src/agent_hub/session.py
- [X] T042 [US2] Implement add_message() method in SessionManager in src/agent_hub/session.py
- [X] T043 [US2] Implement close() method in SessionManager in src/agent_hub/session.py
- [X] T044 [US2] Integrate SessionManager into AgentHub in src/agent_hub/hub.py
- [X] T045 [US2] Add get_session() and close_session() methods to AgentHub in src/agent_hub/hub.py
- [X] T046 [US2] Update ask_expert to create/use sessions in src/agent_hub/hub.py
- [X] T047 [US2] Export SessionManager from src/agent_hub/__init__.py

### Documentation for User Story 2

- [X] T048 [US2] Create user journey doc in docs/user-journeys/AH-002-session-management.md

**Checkpoint**: User Story 2 complete when:
- All session tests pass (including E2E with AH-002 marker)
- Sessions created with unique IDs
- Message history preserved across calls

---

## Phase 5: User Story 3 - Validate Confidence and Escalate (Priority: P2)

**Goal**: Low-confidence answers trigger human escalation with pending status

**Journey ID**: AH-003

**Independent Test**: Provide low-confidence answer, verify escalation created and pending status returned

### Tests for User Story 3

> **NOTE**: Write tests FIRST (TDD). E2E tests MUST have journey markers.

- [X] T049 [P] [US3] Unit test for confidence validation in tests/unit/agent_hub/test_validator.py
- [X] T050 [P] [US3] Unit test for escalation creation on low confidence in tests/unit/agent_hub/test_hub.py
- [X] T051 [US3] E2E test with `@pytest.mark.journey("AH-003")` in tests/e2e/agent_hub/test_escalation_flow.py (update existing)

### Implementation for User Story 3

- [X] T052 [US3] Integrate ConfidenceValidator into ask_expert flow in src/agent_hub/hub.py
- [X] T053 [US3] Return PENDING_HUMAN status when escalation created in src/agent_hub/hub.py
- [X] T054 [US3] Add escalation_id to HubResponse when escalated in src/agent_hub/hub.py

### Documentation for User Story 3

- [X] T055 [US3] Create user journey doc in docs/user-journeys/AH-003-confidence-escalation.md

**Checkpoint**: User Story 3 complete when:
- Confidence validation works with topic thresholds
- Low confidence triggers escalation
- HubResponse shows PENDING_HUMAN status

---

## Phase 6: User Story 4 - Track Pending Escalations (Priority: P2)

**Goal**: Agents can check escalation status and receive resolved answers

**Journey ID**: AH-004

**Independent Test**: Create escalation, poll status, simulate human response, verify resolution

### Tests for User Story 4

> **NOTE**: Write tests FIRST (TDD). E2E tests MUST have journey markers.

- [X] T056 [P] [US4] Unit test for check_escalation() in tests/unit/agent_hub/test_hub.py
- [X] T057 [P] [US4] Unit test for add_human_response() in tests/unit/agent_hub/test_hub.py
- [X] T058 [US4] E2E test with `@pytest.mark.journey("AH-004")` in tests/e2e/agent_hub/test_escalation_flow.py (extend)

### Implementation for User Story 4

- [X] T059 [US4] Implement check_escalation() method in src/agent_hub/hub.py
- [X] T060 [US4] Implement add_human_response() method in src/agent_hub/hub.py
- [X] T061 [US4] Feed human response back to session in src/agent_hub/hub.py
- [X] T062 [US4] Handle NEEDS_REROUTE status with updated context in src/agent_hub/hub.py

### Documentation for User Story 4

- [X] T063 [US4] Create user journey doc in docs/user-journeys/AH-004-pending-escalation.md

**Checkpoint**: User Story 4 complete when:
- check_escalation returns correct status
- Human responses processed correctly
- NEEDS_REROUTE triggers re-query with context

---

## Phase 7: User Story 5 - Audit Trail Logging (Priority: P3)

**Goal**: All Q&A exchanges logged with full context for audit

**Journey ID**: AH-005

**Independent Test**: Route question, verify log entry created with correct content

### Tests for User Story 5

> **NOTE**: Write tests FIRST (TDD). E2E tests MUST have journey markers.

- [X] T064 [P] [US5] Unit test for logging integration in tests/unit/agent_hub/test_logger.py (update existing)
- [X] T065 [US5] E2E test with `@pytest.mark.journey("AH-005")` in tests/e2e/agent_hub/test_qa_logging.py (update existing)

### Implementation for User Story 5

- [X] T066 [US5] Integrate QALogger into AgentHub flow in src/agent_hub/hub.py
- [X] T067 [US5] Log session_id in Q&A log entries in src/agent_hub/hub.py
- [X] T068 [US5] Ensure escalation details included in logs in src/agent_hub/hub.py

### Documentation for User Story 5

- [X] T069 [US5] Create user journey doc in docs/user-journeys/AH-005-audit-logging.md

**Checkpoint**: User Story 5 complete when:
- All exchanges logged with session info
- Escalation details included in logs
- Logs queryable by feature_id

---

## Phase 8: MCP Server (Cross-Cutting)

**Purpose**: Expose Agent Hub functionality via MCP for SDK agents

- [X] T070 Create MCP server module in src/agent_hub/mcp_server.py
- [X] T071 Implement ask_expert MCP tool in src/agent_hub/mcp_server.py
- [X] T072 Implement check_escalation MCP tool in src/agent_hub/mcp_server.py
- [X] T073 Add MCP server entry point for `python -m agent_hub.mcp_server`
- [X] T074 Unit test for MCP tools in tests/unit/agent_hub/test_mcp_server.py

**Checkpoint**: MCP server runs and exposes tools correctly

---

## Phase 9: Polish & Documentation

**Purpose**: Final documentation and cleanup

### User Journey Index Update

- [X] T075 Update docs/user-journeys/JOURNEYS.md with AH-001 through AH-005

### Module Documentation

- [X] T076 Update src/agent_hub/README.md with new terminology and API
- [X] T077 Create docs/modules/agent-hub.md with extended documentation
- [X] T078 Create docs/architecture/agent-hub.md with architecture overview

### Infrastructure Documentation

- [X] T079 Verify docs/README.md includes Agent Hub
- [X] T080 Update CLAUDE.md with agent_hub module information

### Quality & Validation

- [X] T081 Remove any remaining "knowledge_router" references from codebase
- [X] T082 Run full test suite and verify 100% pass rate
- [X] T083 Run quickstart.md validation scenarios
- [X] T084 Run linting (ruff check) and fix any issues
- [X] T085 Run type checking (mypy) and fix any issues

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion
- **Phase 3-7 (User Stories)**: All depend on Phase 2 completion
- **Phase 8 (MCP)**: Depends on Phase 3-5 (needs core functionality)
- **Phase 9 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Route Questions)**: No dependencies on other stories - MVP
- **US2 (Sessions)**: No dependencies on other stories, integrates with US1
- **US3 (Confidence Escalation)**: Builds on US1 routing
- **US4 (Pending Escalation)**: Builds on US3 escalation
- **US5 (Audit Logging)**: Independent, uses existing logger

### Parallel Opportunities

After Phase 2 completes:
- US1 and US2 can run in parallel (both P1)
- US3 and US4 can run in parallel after US1 (both P2)
- US5 can run in parallel with US3/US4 (P3)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# All model tasks can run in parallel:
Task: T014 - Add Session model
Task: T015 - Add Message model
Task: T016 - Add MessageRole enum
Task: T017 - Add SessionStatus enum
Task: T018 - Add HubResponse model
Task: T019 - Add ResponseStatus enum
Task: T020 - Add EscalationStatus model
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (rename)
2. Complete Phase 2: Foundational (new models)
3. Complete Phase 3: User Story 1 (routing) ← Core MVP
4. Complete Phase 4: User Story 2 (sessions) ← Essential for Baron
5. **STOP and VALIDATE**: Test independently
6. Deploy/demo if ready

### Full Feature Delivery

1. Setup + Foundational → Foundation ready
2. US1 + US2 → Core functionality (MVP)
3. US3 + US4 → Escalation handling
4. US5 → Audit logging
5. MCP Server → SDK integration ready
6. Polish → Documentation complete

---

## Metrics

- **Total Tasks**: 85
- **Phase 1 (Setup)**: 13 tasks
- **Phase 2 (Foundational)**: 11 tasks
- **Phase 3-7 (User Stories)**: 45 tasks (9 per story avg)
- **Phase 8 (MCP)**: 5 tasks
- **Phase 9 (Polish)**: 11 tasks
- **Parallel Opportunities**: 35 tasks marked [P]
- **Test Tasks**: 18 tasks
- **Documentation Tasks**: 10 tasks

---

## Notes

- [P] tasks = different files, no dependencies
- [US#] label maps task to specific user story
- TDD: Write tests first, verify they fail, then implement
- Commit after each logical task group
- Journey docs are required for each user story
- Remove ALL "knowledge_router" references by end
