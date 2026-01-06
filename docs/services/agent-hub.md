# Agent Hub Service

The Agent Hub Service is the central coordination layer for all agent interactions.

## Overview

The Agent Hub is the **single entry point** for all agent invocations. It:

- Routes requests to appropriate agents based on topic
- Validates response confidence against thresholds
- Manages multi-turn conversation sessions
- Handles human escalation for low-confidence answers
- Logs all exchanges for audit

**Key Principle**: All agent invocations MUST go through Agent Hub. Direct agent calls are prohibited.

## Quick Start

### Running Locally

```bash
cd services/agent-hub

# Install dependencies
uv sync

# Run the service
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running with Docker

```bash
# Build image
docker build -t agent-hub:latest .

# Run container
docker run -p 8000:8000 agent-hub:latest
```

### API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Reference

### Direct Agent Invocation

```bash
curl -X POST http://localhost:8000/invoke/baron \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "specify",
    "context": {"feature_description": "User auth system"},
    "parameters": {"priority": "P1"}
  }'
```

### Ask Expert by Topic

```bash
curl -X POST http://localhost:8000/ask/architecture \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What authentication method should I use?",
    "context": "Building a multi-tenant SaaS",
    "feature_id": "008-auth"
  }'
```

### Session Management

```bash
# Create session
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "@baron", "feature_id": "008-auth"}'

# Get session with messages
curl http://localhost:8000/sessions/{session_id}

# Close session
curl -X DELETE http://localhost:8000/sessions/{session_id}
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              Agent Hub Service              │
├─────────────────────────────────────────────┤
│  API Layer (FastAPI)                        │
│  ├── /invoke/{agent}                        │
│  ├── /ask/{topic}                           │
│  ├── /sessions, /sessions/{id}              │
│  ├── /escalations/{id}                      │
│  └── /health                                │
├─────────────────────────────────────────────┤
│  Core Layer                                 │
│  ├── AgentRouter (topic → agent mapping)    │
│  ├── ConfidenceValidator                    │
│  ├── SessionManager                         │
│  └── EscalationManager                      │
├─────────────────────────────────────────────┤
│  Client Layer                               │
│  ├── AgentServiceClient                     │
│  └── GitHubClient (escalation comments)     │
├─────────────────────────────────────────────┤
│  Database Layer (SQLite)                    │
│  ├── sessions table                         │
│  ├── messages table                         │
│  └── escalations table                      │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Agent Services │
│  (Baron, etc.)  │
└─────────────────┘
```

## Topic Routing

| Topic | Agent | Confidence Threshold |
|-------|-------|---------------------|
| architecture | baron | 85% |
| security | charles | 90% |
| testing | marie | 80% |
| frontend | dali | 85% |
| devops | gustave | 85% |

## Session Management

Sessions enable multi-turn conversations with context preservation.

### Session Lifecycle

1. **Create**: `POST /sessions` - creates active session
2. **Exchange**: `POST /ask/{topic}` with `session_id` - adds messages
3. **Get**: `GET /sessions/{id}` - retrieves session with history
4. **Close**: `DELETE /sessions/{id}` - closes session (preserves history)

### Session States

| State | Description |
|-------|-------------|
| active | Session available for exchanges |
| closed | Manually closed, history preserved |
| expired | Inactive for > 1 hour |

### Context Preservation

When `session_id` is provided:
1. Previous messages retrieved from database
2. Conversation history included in agent context
3. New question and answer stored as messages

```python
# Agent receives context like:
{
    "question": "Should I use JWT?",
    "conversation_history": [
        {"role": "user", "content": "Building OAuth2 auth..."},
        {"role": "assistant", "content": "For OAuth2, consider..."}
    ]
}
```

## Confidence Validation

Responses below threshold trigger escalation:

```python
if confidence < threshold:
    # Create escalation record
    # Post to GitHub issue comment
    return {"status": "pending_human", "escalation_id": "..."}
```

## Human Escalation

When an agent response has low confidence, an escalation is created for human review.

### Escalation Endpoints

```bash
# Get escalation details
curl http://localhost:8000/escalations/{escalation_id}

# Submit human response
curl -X POST http://localhost:8000/escalations/{escalation_id} \
  -H "Content-Type: application/json" \
  -d '{
    "action": "confirm",
    "responder": "@jane"
  }'
```

### Human Actions

| Action | Description | Response Required |
|--------|-------------|-------------------|
| confirm | Accept the tentative answer | No |
| correct | Provide the correct answer | Yes |
| add_context | Add information for re-evaluation | Yes |

### Escalation States

| State | Description |
|-------|-------------|
| pending | Awaiting human review |
| resolved | Human has responded |
| expired | Expired without response |

### GitHub Integration

When configured with `GITHUB_TOKEN`, escalations are posted as GitHub comments:

```markdown
## Human Review Required

**Confidence:** 60%

### Question
Should we use microservices or monolith?

### Tentative Answer
Based on your context, I recommend...

### How to Respond
- `/confirm` - Accept the answer
- `/correct <answer>` - Provide correct answer
- `/context <info>` - Add more context
```

## Audit Logging

All agent invocations are automatically logged to JSONL format for audit purposes.

### Log Location

Default: `./logs/audit.jsonl` (configurable via `AUDIT_LOG_PATH`)

### Log Entry Format

Each line is a complete JSON object:

```json
{
  "id": "f5e6d7c8-...",
  "timestamp": "2025-01-03T12:34:56.789Z",
  "session_id": "a1b2c3d4-..." or null,
  "feature_id": "008-data-layer",
  "topic": "architecture",
  "question": "What pattern should I use?",
  "answer": "Use the repository pattern.",
  "confidence": 88,
  "status": "resolved",
  "escalation_id": null,
  "duration_ms": 245,
  "metadata": {"agent": "baron"}
}
```

### Log Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique entry identifier |
| `timestamp` | ISO 8601 | UTC timestamp |
| `session_id` | UUID/null | Session ID for multi-turn |
| `feature_id` | string | Feature being worked on |
| `topic` | string | Topic of the question |
| `question` | string | The question asked |
| `answer` | string | The answer provided |
| `confidence` | int (0-100) | Confidence level |
| `status` | string | "resolved" or "escalated" |
| `escalation_id` | UUID/null | Escalation ID if escalated |
| `duration_ms` | int | Response time in ms |
| `metadata` | object | Additional context |

### Querying Logs

```bash
# Filter by feature_id
cat logs/audit.jsonl | jq 'select(.feature_id == "008-auth")'

# Count by feature
cat logs/audit.jsonl | jq -s 'group_by(.feature_id) | map({feature: .[0].feature_id, count: length})'

# Find escalations
cat logs/audit.jsonl | jq 'select(.status == "escalated")'

# Average response time
cat logs/audit.jsonl | jq -s 'map(.duration_ms) | add / length'
```

### Success Criteria

- SC-007.1: 100% of invocations are logged
- SC-007.2: Logs are queryable by feature ID
- SC-007.3: Log format matches data-model.md AuditLog schema

## Database Schema

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
    message_metadata TEXT,  -- JSON
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
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | sqlite:///./data/agent-hub.db | Database connection |
| DEFAULT_CONFIDENCE_THRESHOLD | 85 | Default confidence threshold |
| SESSION_EXPIRY_HOURS | 1 | Session expiry time |
| BARON_URL | http://localhost:8002 | Baron service URL |
| GITHUB_TOKEN | - | GitHub API token for escalation comments |
| GITHUB_REPO | farmer1st/farmer-code | Repository for escalation comments |
| AUDIT_LOG_PATH | ./logs/audit.jsonl | Path to audit log file |

## Testing

```bash
cd services/agent-hub

# Run all tests
uv run pytest

# Run contract tests only
uv run pytest tests/contract/ -m contract

# Run integration tests only
uv run pytest tests/integration/ -m integration

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
services/agent-hub/
├── src/
│   ├── __init__.py           # Package metadata
│   ├── main.py               # FastAPI application
│   ├── api/
│   │   ├── health.py         # Health endpoint
│   │   ├── invoke.py         # /invoke/{agent} endpoint
│   │   ├── ask.py            # /ask/{topic} endpoint
│   │   ├── sessions.py       # /sessions endpoints
│   │   └── escalations.py    # /escalations endpoints
│   ├── core/
│   │   ├── router.py         # Topic → agent routing
│   │   ├── validator.py      # Confidence validation
│   │   ├── session_manager.py # Session lifecycle
│   │   └── escalation.py     # Escalation management
│   ├── clients/
│   │   ├── agents.py         # Agent service client
│   │   └── github.py         # GitHub API client
│   ├── logging/
│   │   └── audit.py          # JSONL audit logger
│   └── db/
│       ├── models.py         # SQLAlchemy models
│       └── session.py        # Database session
├── tests/
│   ├── conftest.py
│   ├── contract/             # API contract tests
│   └── integration/          # Integration tests
└── pyproject.toml
```

## Related Documentation

- [User Journey: SVC-002 Agent Consultation](../user-journeys/SVC-002-agent-consultation.md)
- [User Journey: SVC-003 Human Escalation](../user-journeys/SVC-003-human-escalation.md)
- [User Journey: SVC-004 Multi-Turn Session](../user-journeys/SVC-004-multi-turn-session.md)
- [User Journey: SVC-007 Audit Log Query](../user-journeys/SVC-007-audit-log-query.md)
- [API Contract](../../specs/008-services-architecture/contracts/agent-hub.yaml)
- [Orchestrator Service](./orchestrator.md)
