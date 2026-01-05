# Feature Specification: Agent Hub Refactor

**Feature Branch**: `005-agent-hub-refactor`
**Created**: 2026-01-05
**Status**: Draft
**Input**: Refactor Knowledge Router to Agent Hub - central coordination layer for all agent interactions

## Overview

This is a refactoring feature that evolves the Knowledge Router module into the Agent Hub - a more comprehensive central coordination layer for all agent interactions. The Agent Hub expands beyond simple question routing to include conversation session management, making it suitable for complex multi-turn agent interactions with human feedback loops.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Route Questions to Experts (Priority: P1)

An orchestration agent (Baron or @dede) needs to ask a domain expert a question during workflow execution. The Agent Hub routes the question to the appropriate expert agent based on topic and returns the answer.

**Why this priority**: This is the core functionality - without routing, no agent coordination is possible. This existed in Knowledge Router and must continue to work.

**Independent Test**: Can be fully tested by sending a question with a topic and verifying it reaches the correct expert agent and returns an answer.

**Acceptance Scenarios**:

1. **Given** a question with topic "architecture", **When** the agent calls `ask_expert`, **Then** the question is routed to @duc (Architect agent)
2. **Given** a question with topic "product", **When** the agent calls `ask_expert`, **Then** the question is routed to @veuve (Product agent)
3. **Given** a question with topic "testing", **When** the agent calls `ask_expert`, **Then** the question is routed to @marie (QA agent)

---

### User Story 2 - Maintain Conversation Sessions (Priority: P1)

When a question requires back-and-forth clarification or human feedback, the Agent Hub maintains conversation session state so that the expert agent has full context of prior exchanges.

**Why this priority**: Session management is critical for the async escalation flow where human feedback must be fed back to the same agent with context preserved.

**Independent Test**: Can be tested by sending a question, receiving a response, adding human feedback, and verifying the agent receives the full conversation history.

**Acceptance Scenarios**:

1. **Given** a new question, **When** routed to an expert, **Then** a new session is created with a unique session ID
2. **Given** an existing session ID, **When** human feedback is added, **Then** the feedback is appended to the session history
3. **Given** a session with prior exchanges, **When** the agent is queried again, **Then** it receives the full conversation context
4. **Given** a session, **When** the escalation is resolved, **Then** the session can be closed and archived

---

### User Story 3 - Validate Confidence and Escalate (Priority: P2)

When an expert agent returns a low-confidence answer, the Agent Hub validates against topic-specific thresholds and initiates human escalation if needed.

**Why this priority**: Confidence validation ensures answer quality. This existed in Knowledge Router and must continue to work with the new architecture.

**Independent Test**: Can be tested by providing answers with various confidence levels and verifying escalation triggers appropriately.

**Acceptance Scenarios**:

1. **Given** an answer with confidence above threshold, **When** validated, **Then** the answer is returned directly
2. **Given** an answer with confidence below threshold, **When** validated, **Then** an escalation is created and pending status returned
3. **Given** a topic with custom threshold (e.g., security=95%), **When** answer has 90% confidence, **Then** escalation is triggered despite exceeding default 80%

---

### User Story 4 - Track Pending Escalations (Priority: P2)

Orchestration agents can check the status of pending human escalations and receive the resolved answer when the human responds.

**Why this priority**: Enables async workflow where agents can continue other work while waiting for human input.

**Independent Test**: Can be tested by creating an escalation, polling for status, simulating human response, and verifying resolution.

**Acceptance Scenarios**:

1. **Given** a pending escalation, **When** `check_escalation` is called, **Then** status "pending" is returned
2. **Given** an escalation where human confirmed, **When** `check_escalation` is called, **Then** status "resolved" with original answer is returned
3. **Given** an escalation where human corrected, **When** `check_escalation` is called, **Then** status "resolved" with corrected answer (100% confidence) is returned
4. **Given** an escalation where human added context, **When** `check_escalation` is called, **Then** status "needs_reroute" with updated question context is returned

---

### User Story 5 - Audit Trail Logging (Priority: P3)

All Q&A exchanges through the Agent Hub are logged with full context for audit and debugging purposes.

**Why this priority**: Important for transparency and debugging but not blocking for core functionality.

**Independent Test**: Can be tested by routing questions and verifying log entries are created with correct content.

**Acceptance Scenarios**:

1. **Given** a Q&A exchange, **When** completed, **Then** a log entry is created with question, answer, agent, confidence, and duration
2. **Given** an escalated exchange, **When** resolved, **Then** the log entry includes escalation details and human response
3. **Given** a feature ID, **When** logs are queried, **Then** all exchanges for that feature are returned chronologically

---

### Edge Cases

- What happens when an unknown topic is provided? Route to default agent or return error with available topics
- How does system handle when no agent is configured for a topic? Return clear error listing available topics
- What happens when a session expires or is not found? Create new session with warning log
- How does system handle concurrent requests to the same session? Queue requests or reject with conflict error
- What happens when human escalation times out? Configurable timeout with notification to orchestrator

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST route questions to appropriate expert agents based on topic configuration
- **FR-002**: System MUST create and maintain conversation sessions with unique identifiers
- **FR-003**: System MUST preserve full conversation history within a session
- **FR-004**: System MUST validate answer confidence against topic-specific thresholds
- **FR-005**: System MUST create escalations for low-confidence answers
- **FR-006**: System MUST track escalation status (pending, resolved, needs_reroute)
- **FR-007**: System MUST feed human responses back into the appropriate session
- **FR-008**: System MUST log all Q&A exchanges with full context
- **FR-009**: System MUST expose functionality via MCP tools (ask_expert, check_escalation)
- **FR-010**: System MUST maintain backward compatibility with existing Knowledge Router functionality

### Key Entities

- **AgentHub**: Central coordinator that manages routing, sessions, validation, and escalation
- **Session**: Represents a conversation with an expert agent, containing message history and metadata
- **HubResponse**: Response from ask_expert containing answer, confidence, session_id, and status
- **EscalationStatus**: Status of a pending human escalation (pending, resolved, needs_reroute)

### Service Interface

**Service**: AgentHub

| Method                 | Purpose                                  | Inputs                               | Outputs          |
|------------------------|------------------------------------------|--------------------------------------|------------------|
| `ask_expert()`         | Route question to appropriate expert     | topic, question, context, session_id | HubResponse      |
| `check_escalation()`   | Check status of pending human escalation | escalation_id                        | EscalationStatus |
| `add_human_response()` | Process human response to escalation     | escalation_id, response              | HubResponse      |
| `get_session()`        | Retrieve session by ID                   | session_id                           | Session          |
| `close_session()`      | Close and archive a session              | session_id                           | None             |

**Error Conditions**:
- Unknown topic: Returns error listing available topics
- Session not found: Creates new session with warning or returns error
- Agent dispatch failure: Returns error with agent details
- Escalation not found: Returns error with escalation ID

## Refactoring Scope

### Module Rename

| Before                        | After                    |
|-------------------------------|--------------------------|
| `src/knowledge_router/`       | `src/agent_hub/`         |
| `knowledge_router.router`     | `agent_hub.hub`          |
| `KnowledgeRouterService`      | `AgentHub`               |
| `knowledge_router.dispatcher` | `agent_hub.router`       |
| `knowledge_router.models`     | `agent_hub.models`       |
| `knowledge_router.validator`  | `agent_hub.validator`    |
| `knowledge_router.escalation` | `agent_hub.escalation`   |
| `knowledge_router.logger`     | `agent_hub.logger`       |
| `knowledge_router.config`     | `agent_hub.config`       |
| `knowledge_router.exceptions` | `agent_hub.exceptions`   |

### New Components

| Component       | Purpose                                          |
|-----------------|--------------------------------------------------|
| `session.py`    | SessionManager for conversation state management |
| `mcp_server.py` | MCP server exposing Agent Hub tools              |

### Documentation Updates

- Update all module docstrings to reflect Agent Hub terminology
- Update README.md in src/agent_hub/
- Create/update docs/architecture/agent-hub.md
- Create user journey documentation
- Update CLAUDE.md with new module information

### Test Updates

- Rename test directories: `tests/*/knowledge_router/` to `tests/*/agent_hub/`
- Update all import statements in tests
- Add new tests for SessionManager
- Ensure all existing tests pass after refactoring

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All existing Knowledge Router tests pass after refactoring (100% test pass rate)
- **SC-002**: New session management functionality has greater than 90% test coverage
- **SC-003**: Questions are routed to correct agents within 100ms (excluding agent response time)
- **SC-004**: Session state is preserved across multiple exchanges without data loss
- **SC-005**: Documentation is complete with no references to "Knowledge Router" remaining
- **SC-006**: Zero breaking changes to external interfaces (MCP tools work identically)

## Assumptions

- The existing Knowledge Router implementation is stable and well-tested
- Session data can be stored in memory for local development (persistence can be added later)
- MCP server implementation follows the patterns established in the codebase
- Agent configurations remain compatible with new architecture

## Dependencies

- Feature 004 (Knowledge Router) must be complete and merged
- Claude Agent SDK documentation for MCP server implementation
