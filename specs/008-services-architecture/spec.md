# Feature Specification: Services Architecture Refactor

**Feature Branch**: `008-services-architecture`
**Created**: 2026-01-05
**Status**: Draft
**Input**: Refactor Farmer Code from a modular Python architecture to a services-based architecture with independent, deployable services communicating via REST APIs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Orchestrator Invokes Agent via Agent Hub (Priority: P1)

A developer triggers a SpecKit workflow (e.g., `/speckit.specify`). The Orchestrator Service receives the request, manages the workflow state, and invokes the Baron agent through the Agent Hub Service. Baron processes the request and returns a specification draft.

**Why this priority**: This is the core workflow that replaces the current module-based architecture. Without service-to-service communication working, no other functionality is possible.

**Independent Test**: Can be fully tested by triggering a SpecKit workflow and verifying that the request flows from Orchestrator → Agent Hub → Baron → back to user. Delivers value by proving the services architecture works end-to-end.

**Acceptance Scenarios**:

1. **Given** the Orchestrator, Agent Hub, and Baron services are running, **When** a developer triggers `/speckit.specify "Add user auth"`, **Then** the Orchestrator invokes Baron via Agent Hub and returns a specification draft.
2. **Given** a workflow is in progress, **When** the Baron agent completes its task, **Then** the Orchestrator receives the response and transitions to the next workflow state.
3. **Given** the Agent Hub receives a request for an agent, **When** the agent is available, **Then** it routes the request to the correct agent service and returns the response.

---

### User Story 2 - Agent-to-Agent Communication (Priority: P1)

During a complex task, one agent (e.g., Baron) needs expertise from another agent (e.g., Duc for architecture questions). Baron asks a question through the Agent Hub, which routes it to Duc, validates confidence, and returns the answer to Baron.

**Why this priority**: Agent collaboration is fundamental to the multi-agent system. Without this, agents cannot consult each other for specialized expertise.

**Independent Test**: Can be fully tested by having Baron ask an architecture question. Agent Hub routes to Duc, Duc responds, and Baron receives the answer to incorporate into its work.

**Acceptance Scenarios**:

1. **Given** Baron is working on a specification, **When** Baron asks an architecture question via Agent Hub, **Then** Agent Hub routes the question to Duc and returns Duc's answer to Baron.
2. **Given** an agent asks a question, **When** the response confidence is above the threshold, **Then** the answer is returned immediately without human escalation.
3. **Given** an agent asks a question, **When** the response confidence is below the threshold, **Then** the Agent Hub creates an escalation request and returns the tentative answer with an escalation flag.

---

### User Story 3 - Human Escalation via GitHub Comments (Priority: P2)

When an agent provides a low-confidence answer, the Agent Hub creates a GitHub comment requesting human review. The human responds via GitHub comment (CONFIRM, CORRECT, or ADD_CONTEXT). The system captures this feedback and incorporates it into the ongoing workflow.

**Why this priority**: Human-in-the-loop is essential for quality assurance, but the basic agent workflows must work first. The system continues with a best guess while flagging for review, making this non-blocking.

**Independent Test**: Can be fully tested by triggering a low-confidence response, verifying a GitHub comment is created, responding with CONFIRM/CORRECT, and verifying the feedback is captured.

**Acceptance Scenarios**:

1. **Given** an agent answer has low confidence, **When** Agent Hub creates an escalation, **Then** a GitHub comment is posted with the question, tentative answer, and response options.
2. **Given** an escalation is pending, **When** a human responds with CONFIRM via GitHub comment, **Then** the tentative answer is accepted and the escalation is marked resolved.
3. **Given** an escalation is pending, **When** a human responds with CORRECT and provides a new answer, **Then** the provided answer is used and the escalation is marked resolved with 100% confidence.
4. **Given** an escalation is pending, **When** a human responds with ADD_CONTEXT, **Then** the escalation is marked for re-routing with the additional context.

---

### User Story 4 - Session Management for Multi-Turn Conversations (Priority: P2)

An agent engages in a multi-turn conversation where context from previous exchanges is preserved. The Agent Hub maintains session state so that follow-up questions can reference earlier context.

**Why this priority**: Many agent interactions require context preservation. However, single-turn interactions work without sessions, so this builds on top of basic functionality.

**Independent Test**: Can be fully tested by having an agent ask a follow-up question that references context from a previous question in the same session.

**Acceptance Scenarios**:

1. **Given** an agent starts a new conversation, **When** the Agent Hub receives the first question, **Then** a new session is created with a unique identifier.
2. **Given** an active session exists, **When** a follow-up question is sent with the session ID, **Then** the Agent Hub includes previous conversation context when routing to the expert agent.
3. **Given** a session has been inactive for the timeout period, **When** a new request arrives, **Then** the session is marked as expired and a new session is created.
4. **Given** an agent explicitly closes a session, **When** the close request is processed, **Then** the session is marked as closed and the conversation history is preserved for audit.

---

### User Story 5 - Stateless Agent Services (Priority: P1)

Each agent service (Baron, Duc, Marie, etc.) runs as an independent, stateless service. The agent receives a request with all necessary context, performs its work using Claude SDK with MCP servers/tools/skills, and returns a result. No state is persisted within the agent service.

**Why this priority**: Stateless design is fundamental to the services architecture. It enables horizontal scaling, simpler deployment, and clearer service boundaries.

**Independent Test**: Can be fully tested by invoking an agent service directly with a complete request and verifying it returns a complete response without requiring prior invocations.

**Acceptance Scenarios**:

1. **Given** a Baron service is running, **When** an invoke request arrives with workflow type and context, **Then** Baron processes the request using Claude SDK and returns the result.
2. **Given** an agent service receives a request, **When** the request includes all necessary context, **Then** the agent does not need to query any external state to complete its task.
3. **Given** an agent needs to use external tools, **When** MCP servers are configured, **Then** the agent can invoke MCP tools, custom tools, and skills simultaneously.

---

### User Story 6 - Local Development with Docker Compose (Priority: P3)

A developer clones the repository and runs `docker-compose up` to start all services locally. The developer can then use the system for development and testing without cloud dependencies.

**Why this priority**: Developer experience is important but requires all services to exist first. This is an integration concern that comes after individual services work.

**Independent Test**: Can be fully tested by running `docker-compose up` on a fresh clone and verifying all services start and can communicate.

**Acceptance Scenarios**:

1. **Given** a developer has cloned the repository, **When** they run `docker-compose up`, **Then** all services (Orchestrator, Agent Hub, and available agents) start successfully.
2. **Given** all services are running via Docker Compose, **When** a developer triggers a workflow, **Then** the request is processed end-to-end within the local environment.
3. **Given** a developer modifies an agent service, **When** they rebuild and restart that service, **Then** only that service is affected and other services continue running.

---

### User Story 7 - Audit Logging for All Agent Exchanges (Priority: P3)

Every question-answer exchange between agents is logged with complete context including session information, confidence scores, and escalation status. Logs are stored in append-only format for audit and retrospective analysis.

**Why this priority**: Audit logging is essential for debugging and compliance but is not required for core functionality to work.

**Independent Test**: Can be fully tested by triggering agent exchanges and verifying log entries are created with all required fields.

**Acceptance Scenarios**:

1. **Given** an agent asks a question via Agent Hub, **When** the exchange completes, **Then** a log entry is written with question, answer, confidence, session ID, and timestamp.
2. **Given** an escalation occurs, **When** the escalation is resolved, **Then** the log entry includes escalation details and human response.
3. **Given** logs are stored, **When** a developer queries logs by feature ID, **Then** all exchanges for that feature are returned in chronological order.

---

### Edge Cases

- What happens when Agent Hub cannot reach an agent service? System should return a clear error and not hang indefinitely.
- What happens when an agent times out during processing? The request should fail gracefully with a timeout error.
- What happens when multiple agents request the same expert simultaneously? Agent Hub should handle concurrent requests without race conditions.
- What happens when GitHub is unavailable for escalation? The system should continue with the tentative answer and queue the escalation for retry.
- What happens when a session's storage backend is unavailable? The system should gracefully degrade to stateless operation with a warning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an Orchestrator Service that owns workflow definitions (specify, plan, tasks, implement) and manages state transitions.
- **FR-002**: System MUST provide an Agent Hub Service that routes all agent invocation requests to the appropriate agent service.
- **FR-003**: System MUST provide individual Agent Services (Baron, Duc, Marie, etc.) that are stateless and SDK-based.
- **FR-004**: Agent Services MUST support MCP servers, custom tools, and skills simultaneously.
- **FR-005**: System MUST route ALL agent invocations through the Agent Hub (single pattern, no direct agent-to-agent calls).
- **FR-006**: Agent Hub MUST validate response confidence against configurable thresholds.
- **FR-007**: Agent Hub MUST create escalation requests for low-confidence answers via GitHub comments.
- **FR-008**: Agent Hub MUST support session management for multi-turn conversations.
- **FR-009**: Agent Hub MUST log all Q&A exchanges to append-only storage with full context.
- **FR-010**: System MUST persist session and escalation state (locally via file-based storage or SQLite).
- **FR-011**: All services MUST communicate via REST APIs.
- **FR-012**: System MUST support local development via Docker Compose.
- **FR-013**: Human escalation MUST be non-blocking (continue with tentative answer, flag for review).
- **FR-014**: Escalation responses MUST support CONFIRM, CORRECT, and ADD_CONTEXT actions.
- **FR-015**: System MUST provide a shared contracts package for common models and API schemas.

### Key Entities

- **Service**: An independently deployable unit (Orchestrator, Agent Hub, or Agent) with its own API and lifecycle.
- **Session**: A conversation context maintained by Agent Hub, containing message history and metadata.
- **Escalation**: A pending human review request created when confidence is below threshold.
- **Workflow State**: The current phase of an Orchestrator workflow (IDLE, PHASE_1, PHASE_2, etc.).
- **Agent Response**: The result returned by an agent service, including answer, confidence, and metadata.

### Service Interface

**Service**: Orchestrator Service

| Method           | Purpose                | Inputs                                 | Outputs                             |
|------------------|------------------------|----------------------------------------|-------------------------------------|
| `POST /workflows` | Start a new workflow   | workflow_type, feature_description, context | workflow_id, status                 |
| `GET /workflows/{id}` | Get workflow status    | workflow_id                            | workflow_state, current_phase, result |
| `POST /workflows/{id}/advance` | Advance to next phase  | workflow_id, phase_result              | new_state, next_action              |

**Service**: Agent Hub Service

| Method                  | Purpose                 | Inputs                                    | Outputs                                |
|-------------------------|-------------------------|-------------------------------------------|----------------------------------------|
| `POST /invoke/{agent}`  | Invoke a specific agent | agent_name, request_payload, session_id   | agent_response, confidence, escalation_id |
| `POST /ask/{topic}`     | Ask expert by topic     | topic, question, feature_id, session_id   | response, status, escalation_id        |
| `GET /escalations/{id}` | Check escalation status | escalation_id                             | status, tentative_answer, human_response |
| `POST /escalations/{id}` | Submit human response   | escalation_id, action, response           | updated_status                         |
| `POST /sessions`        | Create new session      | agent_id, feature_id                      | session_id                             |
| `GET /sessions/{id}`    | Get session history     | session_id                                | messages, status                       |
| `DELETE /sessions/{id}` | Close session           | session_id                                | confirmation                           |

**Service**: Agent Service (per agent)

| Method        | Purpose         | Inputs                              | Outputs                         |
|---------------|-----------------|-------------------------------------|---------------------------------|
| `POST /invoke` | Process a request | workflow_type, context, parameters | result, confidence, metadata    |
| `GET /health` | Health check    | none                                | status, version                 |

**Error Conditions**:
- Agent not found: Return 404 with clear error message
- Agent timeout: Return 504 with timeout details
- Validation error: Return 400 with validation details
- Internal error: Return 500 with error ID for debugging

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All services can be started locally with a single command (`docker-compose up`) within 60 seconds.
- **SC-002**: A complete SpecKit workflow (specify → plan → tasks) completes successfully using the new services architecture.
- **SC-003**: Agent-to-agent communication via Agent Hub has less than 1 second overhead compared to direct invocation.
- **SC-004**: The system handles 10 concurrent workflow executions without degradation.
- **SC-005**: Human escalations are created within 5 seconds of detecting low confidence.
- **SC-006**: Session context is correctly preserved across 5 consecutive multi-turn exchanges.
- **SC-007**: 100% of agent invocations are logged with complete audit information.
- **SC-008**: No existing SpecKit functionality is broken during the transition (all existing tests pass).
- **SC-009**: Each service can be deployed and updated independently without affecting other running services.
- **SC-010**: Developer can add a new agent service by following documented patterns in under 30 minutes.

## Assumptions

- Claude Code SDK supports MCP servers, custom tools, and skills simultaneously (verified in pre-spec research).
- GitHub API is available for escalation comments (fallback to retry queue if unavailable).
- Local development will use Docker Compose; Kubernetes deployment is future scope.
- Initial persistence will use file-based storage or SQLite for simplicity; Redis is optional for distributed deployments.
- Services will run in the same network (localhost or same EKS cluster), so latency is not a primary concern.
- The existing test suite will be migrated to test the new services architecture.

## Out of Scope

- BFF (Backend for Frontend) implementation - future enhancement.
- Slack integration for escalations - will be added via GitHub Actions later.
- UI direct integration with Agent Hub - UI interacts via GitHub issues only.
- Kubernetes deployment configuration - Docker Compose only for this feature.
- Multi-hub federation for distributed deployments.
- Performance optimization beyond basic responsiveness requirements.
