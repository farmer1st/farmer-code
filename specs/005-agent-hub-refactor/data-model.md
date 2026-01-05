# Data Model: Agent Hub

**Feature**: 005-agent-hub-refactor
**Date**: 2026-01-05

## Entities

### Session

Represents a conversation with an expert agent, containing message history and metadata.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | str (UUID) | Unique session identifier | Required, UUID format |
| agent_id | str | Agent role (architect, product, qa) | Required, must be valid agent |
| feature_id | str | Feature this session relates to | Required |
| messages | list[Message] | Conversation history | Required, can be empty |
| created_at | datetime | Session creation time | Required, auto-set |
| updated_at | datetime | Last update time | Required, auto-updated |
| status | SessionStatus | Current session state | Required, default ACTIVE |

**State Transitions**:
```
ACTIVE → CLOSED (when session.close() called)
ACTIVE → EXPIRED (when session timeout reached)
```

### Message

A single message in a session conversation.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| role | MessageRole | Who sent the message | Required, enum |
| content | str | Message content | Required, non-empty |
| timestamp | datetime | When message was sent | Required, auto-set |
| metadata | dict | Additional context | Optional |

**MessageRole Enum**:
- `USER` - Question from the calling agent
- `ASSISTANT` - Answer from the expert agent
- `HUMAN` - Feedback from human during escalation

### HubResponse

Response from ask_expert containing answer, confidence, session_id, and status.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| answer | str | The expert's answer | Required when status=resolved |
| rationale | str | Why this answer | Required when status=resolved |
| confidence | int | 0-100 confidence score | Required, 0-100 |
| uncertainty_reasons | list[str] | Why not 100% confident | Optional |
| session_id | str | Session for follow-ups | Required |
| status | ResponseStatus | pending_human or resolved | Required |
| escalation_id | str | If escalated, the ID | Optional |

**ResponseStatus Enum**:
- `RESOLVED` - Answer ready, no escalation needed
- `PENDING_HUMAN` - Escalated, waiting for human
- `NEEDS_REROUTE` - Human added context, need to re-ask

### EscalationStatus

Status of a pending human escalation.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| escalation_id | str | Unique escalation ID | Required |
| status | str | pending, resolved, needs_reroute | Required |
| action | HumanAction | What human did | Optional, set when resolved |
| corrected_answer | str | If human corrected | Optional |
| additional_context | str | If human added context | Optional |
| resolved_at | datetime | When resolved | Optional |

## Entity Relationships

```
AgentHub
    │
    ├── SessionManager (1:1)
    │       │
    │       └── Session (1:N)
    │               │
    │               └── Message (1:N)
    │
    ├── AgentRouter (1:1)
    │       │
    │       └── routes to Expert Agents
    │
    ├── ConfidenceValidator (1:1)
    │
    ├── EscalationHandler (1:1)
    │       │
    │       └── EscalationRequest (1:N)
    │
    └── AuditLogger (1:1)
            │
            └── QALogEntry (1:N)
```

## Existing Entities (Unchanged)

These entities from Knowledge Router remain unchanged:

- **Question**: Input question with topic, context, options
- **Answer**: Expert agent response with confidence
- **ValidationResult**: Confidence validation outcome
- **EscalationRequest**: Full escalation with tentative answer
- **HumanResponse**: Human's action on escalation
- **QALogEntry**: Audit log entry
- **AgentConfig**: Agent configuration (topics, model, timeout)
- **RoutingConfig**: Full routing configuration
