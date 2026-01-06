# SVC-007: Audit Log Query

## User Story

**As a** developer or operator
**I want to** query audit logs by feature ID
**So that** I can review all Q&A exchanges for a specific feature

## Acceptance Criteria

- [ ] All agent invocations are logged to JSONL format
- [ ] Logs include: question, answer, confidence, status, duration_ms
- [ ] Logs are queryable by feature_id
- [ ] Session context is preserved for multi-turn conversations
- [ ] Escalation IDs are logged when escalation occurs

## Journey Flow

```
Developer queries logs → Filter by feature_id → Review Q&A exchanges
```

### Step 1: Invoke Agent (Automatically Logged)

When a user invokes the Agent Hub via `/ask/{topic}`:

```bash
curl -X POST http://localhost:8001/ask/architecture \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What pattern should I use for data access?",
    "feature_id": "008-data-layer"
  }'
```

Response:
```json
{
  "answer": "Use the repository pattern with SQLAlchemy ORM.",
  "confidence": 88,
  "status": "resolved",
  "session_id": "a1b2c3d4-..."
}
```

### Step 2: Log Entry Created

The exchange is automatically logged to `logs/audit.jsonl`:

```json
{
  "id": "f5e6d7c8-...",
  "timestamp": "2025-01-03T12:34:56.789Z",
  "session_id": null,
  "feature_id": "008-data-layer",
  "topic": "architecture",
  "question": "What pattern should I use for data access?",
  "answer": "Use the repository pattern with SQLAlchemy ORM.",
  "confidence": 88,
  "status": "resolved",
  "escalation_id": null,
  "duration_ms": 245,
  "metadata": {"agent": "baron"}
}
```

### Step 3: Query Logs by Feature

To review all exchanges for a feature:

```bash
# Using jq to filter by feature_id
cat logs/audit.jsonl | jq 'select(.feature_id == "008-data-layer")'

# Count exchanges per feature
cat logs/audit.jsonl | jq -s 'group_by(.feature_id) | map({feature: .[0].feature_id, count: length})'

# Find escalated exchanges
cat logs/audit.jsonl | jq 'select(.status == "escalated")'
```

## Log Entry Schema

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

## Configuration

The audit log path can be configured via environment variable:

```bash
export AUDIT_LOG_PATH=./logs/audit.jsonl
```

Default: `./logs/audit.jsonl`

## Success Criteria

- SC-007.1: 100% of invocations are logged
- SC-007.2: Logs are queryable by feature ID
- SC-007.3: Log format matches data-model.md AuditLog schema

## Related Tests

- `tests/e2e/test_audit_logging.py::TestAuditLogging`
- `services/agent-hub/tests/unit/test_audit_logger.py`
- `services/agent-hub/tests/integration/test_audit_log.py`
