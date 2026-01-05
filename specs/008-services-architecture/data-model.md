# Data Model: Services Architecture Refactor

**Feature**: 008-services-architecture
**Date**: 2026-01-05

## Overview

This document defines the data models for the services architecture. Models are shared across services via the `packages/contracts/` package.

## Core Entities

### 1. Workflow (Orchestrator Service)

Represents a SpecKit workflow execution (specify, plan, tasks, implement).

```
Workflow
├── id: UUID (primary key)
├── workflow_type: WorkflowType (SPECIFY, PLAN, TASKS, IMPLEMENT)
├── status: WorkflowStatus (PENDING, IN_PROGRESS, WAITING_APPROVAL, COMPLETED, FAILED)
├── feature_id: str (e.g., "008-services-architecture")
├── feature_description: str
├── current_phase: str (e.g., "phase_1", "phase_2")
├── context: JSON (workflow-specific context data)
├── result: JSON (workflow output, null until complete)
├── error: str | null (error message if failed)
├── created_at: datetime
├── updated_at: datetime
└── completed_at: datetime | null
```

**Relationships**:
- One Workflow → Many WorkflowHistory entries

### 2. WorkflowHistory (Orchestrator Service)

Tracks state transitions for audit.

```
WorkflowHistory
├── id: UUID (primary key)
├── workflow_id: UUID (foreign key → Workflow)
├── from_status: WorkflowStatus
├── to_status: WorkflowStatus
├── trigger: str (e.g., "agent_complete", "human_approved")
├── metadata: JSON (additional context)
└── created_at: datetime
```

### 3. Session (Agent Hub Service)

Maintains conversation context for multi-turn agent interactions.

```
Session
├── id: UUID (primary key)
├── agent_id: str (e.g., "@duc", "@baron")
├── feature_id: str | null
├── status: SessionStatus (ACTIVE, CLOSED, EXPIRED)
├── created_at: datetime
├── updated_at: datetime
└── expires_at: datetime | null
```

**Relationships**:
- One Session → Many Messages

### 4. Message (Agent Hub Service)

Individual message within a session.

```
Message
├── id: UUID (primary key)
├── session_id: UUID (foreign key → Session)
├── role: MessageRole (USER, ASSISTANT, HUMAN)
├── content: str
├── metadata: JSON (confidence, model_used, duration_ms, etc.)
└── created_at: datetime
```

### 5. Escalation (Agent Hub Service)

Tracks human review requests for low-confidence answers.

```
Escalation
├── id: UUID (primary key)
├── session_id: UUID | null (foreign key → Session)
├── question_id: str
├── topic: str
├── question: str
├── tentative_answer: str
├── confidence: int (0-100)
├── uncertainty_reasons: JSON (list of strings)
├── status: EscalationStatus (PENDING, RESOLVED, EXPIRED)
├── human_action: HumanAction | null (CONFIRM, CORRECT, ADD_CONTEXT)
├── human_response: str | null
├── human_responder: str | null
├── github_comment_id: int | null
├── created_at: datetime
├── resolved_at: datetime | null
└── updated_at: datetime
```

### 6. AuditLog (Agent Hub Service)

Append-only log entry for Q&A exchanges.

```
AuditLog (JSONL file, not database table)
├── id: UUID
├── timestamp: datetime
├── session_id: UUID | null
├── feature_id: str
├── topic: str
├── question: str
├── answer: str
├── confidence: int
├── status: str (resolved, escalated)
├── escalation_id: UUID | null
├── duration_ms: int
└── metadata: JSON
```

## Enumerations

### WorkflowType
```
SPECIFY   = "specify"
PLAN      = "plan"
TASKS     = "tasks"
IMPLEMENT = "implement"
```

### WorkflowStatus
```
PENDING          = "pending"
IN_PROGRESS      = "in_progress"
WAITING_APPROVAL = "waiting_approval"
COMPLETED        = "completed"
FAILED           = "failed"
```

### SessionStatus
```
ACTIVE  = "active"
CLOSED  = "closed"
EXPIRED = "expired"
```

### MessageRole
```
USER      = "user"
ASSISTANT = "assistant"
HUMAN     = "human"
```

### EscalationStatus
```
PENDING  = "pending"
RESOLVED = "resolved"
EXPIRED  = "expired"
```

### HumanAction
```
CONFIRM     = "confirm"      # Accept tentative answer
CORRECT     = "correct"      # Provide different answer
ADD_CONTEXT = "add_context"  # Need more context, re-route
```

## API Request/Response Models

### Agent Invocation

```
InvokeRequest
├── workflow_type: str (for Baron: "specify", "plan", "tasks")
├── context: dict (workflow-specific context)
├── parameters: dict (additional parameters)
└── session_id: UUID | null (for multi-turn conversations)

InvokeResponse
├── success: bool
├── result: dict (agent output)
├── confidence: int (0-100)
├── metadata: dict (duration_ms, model_used, etc.)
└── error: str | null
```

### Agent Hub Ask Expert

```
AskExpertRequest
├── topic: str (e.g., "architecture", "security")
├── question: str
├── context: str | null
├── feature_id: str
└── session_id: UUID | null

AskExpertResponse
├── answer: str
├── rationale: str
├── confidence: int (0-100)
├── uncertainty_reasons: list[str]
├── status: str (resolved, pending_human, needs_reroute)
├── session_id: UUID
└── escalation_id: UUID | null
```

### Escalation

```
EscalationResponse
├── id: UUID
├── status: EscalationStatus
├── question: str
├── tentative_answer: str
├── confidence: int
├── human_action: HumanAction | null
├── human_response: str | null
└── created_at: datetime

SubmitHumanResponseRequest
├── action: HumanAction
├── response: str | null (required for CORRECT, optional for ADD_CONTEXT)
└── responder: str (GitHub username or identifier)
```

### Workflow

```
CreateWorkflowRequest
├── workflow_type: WorkflowType
├── feature_description: str
└── context: dict | null

WorkflowResponse
├── id: UUID
├── workflow_type: WorkflowType
├── status: WorkflowStatus
├── current_phase: str
├── result: dict | null
└── created_at: datetime

AdvanceWorkflowRequest
├── phase_result: dict (output from completed phase)
└── trigger: str (e.g., "agent_complete", "human_approved")
```

## State Transitions

### Workflow State Machine

```
PENDING → IN_PROGRESS (workflow started)
    │
    ├── Agent processing...
    │
    └── IN_PROGRESS → WAITING_APPROVAL (agent complete, gate reached)
                │
                ├── Human approves
                │
                └── WAITING_APPROVAL → IN_PROGRESS (next phase)
                                    or
                    WAITING_APPROVAL → COMPLETED (all phases done)

Any state → FAILED (error occurred)
```

### Session State Machine

```
ACTIVE (created)
    │
    ├── add_message() [stays ACTIVE]
    │
    ├── close_session() → CLOSED
    │
    └── timeout reached → EXPIRED
```

### Escalation State Machine

```
PENDING (created, low confidence)
    │
    ├── human_response(CONFIRM) → RESOLVED
    │
    ├── human_response(CORRECT) → RESOLVED
    │
    ├── human_response(ADD_CONTEXT) → RESOLVED (with needs_reroute flag)
    │
    └── timeout (7 days) → EXPIRED
```

## Database Schema

### SQLite Tables (Agent Hub Service)

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    feature_id TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL
);

CREATE TABLE escalations (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    question_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    question TEXT NOT NULL,
    tentative_answer TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    uncertainty_reasons TEXT,  -- JSON array
    status TEXT NOT NULL DEFAULT 'pending',
    human_action TEXT,
    human_response TEXT,
    human_responder TEXT,
    github_comment_id INTEGER,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_feature_id ON sessions(feature_id);
CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_escalations_status ON escalations(status);
```

### SQLite Tables (Orchestrator Service)

```sql
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    feature_id TEXT NOT NULL,
    feature_description TEXT NOT NULL,
    current_phase TEXT,
    context TEXT,  -- JSON
    result TEXT,   -- JSON
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE workflow_history (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    trigger TEXT NOT NULL,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL
);

CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_feature_id ON workflows(feature_id);
CREATE INDEX idx_workflow_history_workflow_id ON workflow_history(workflow_id);
```

## Validation Rules

### Session
- `agent_id` must be a known agent (from routing config)
- `status` must be valid enum value
- `expires_at` calculated as `created_at + 1 hour` if not provided

### Message
- `session_id` must reference existing session
- `role` must be valid enum value
- `content` cannot be empty

### Escalation
- `confidence` must be 0-100
- `human_action` required when transitioning to RESOLVED
- `human_response` required when `human_action` is CORRECT

### Workflow
- `workflow_type` must be valid enum value
- `feature_id` must follow pattern `\d{3}-[a-z0-9-]+`
- `feature_description` cannot be empty
