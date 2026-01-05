# AH-005: Audit Trail Logging

**Actor**: Orchestration Agent (@baron PM Agent or similar)
**Goal**: All Q&A exchanges logged with full context for audit
**Preconditions**:
- AgentHub initialized with log_dir parameter
- QALogger enabled for the hub instance

**Priority**: P3 (Essential for retrospectives and knowledge improvement)

## Overview

This journey covers automatic audit trail logging of all Q&A exchanges. When ask_expert is called, the AgentHub automatically:
- Creates a QALogEntry with full exchange details
- Includes session_id for conversation context
- Captures escalation details when applicable
- Writes logs to feature-specific JSONL files
- Supports retrieval by feature_id

## Steps

### 1. Enable Logging on AgentHub

- **Action**: Initialize AgentHub with log_dir parameter
- **Expected outcome**: QALogger created for specified directory
- **System behavior**:
  - `log_dir` creates QALogger instance
  - Directory created if it doesn't exist
  - Each feature gets its own JSONL file

### 2. Ask Expert Logs Exchange

- **Action**: Call ask_expert() with any question
- **Expected outcome**: Exchange automatically logged
- **System behavior**:
  - QALogEntry created with question, answer, validation
  - Routing decision captured
  - Duration tracked
  - Log appended to feature JSONL file

### 3. Session ID Captured in Logs

- **Action**: Exchange occurs within a session
- **Expected outcome**: session_id included in log entry
- **System behavior**:
  - Log entry includes session_id field
  - Enables correlation of multi-turn conversations
  - Session history traceable via logs

### 4. Escalation Details Logged

- **Action**: Low-confidence answer triggers escalation
- **Expected outcome**: Escalation details included in log
- **System behavior**:
  - EscalationRequest attached to log entry
  - Escalation status recorded (pending)
  - Threshold that triggered escalation captured

### 5. Retrieve Logs by Feature

- **Action**: Call get_logs_for_feature(feature_id)
- **Expected outcome**: All exchanges for feature returned
- **System behavior**:
  - Reads feature's JSONL log file
  - Returns list of log entries as dicts
  - Empty list if no logs exist

## Success Criteria

- All ask_expert calls create log entries
- Log entries include session_id
- Escalation details captured when applicable
- Routing decision recorded
- Logs retrievable by feature_id
- Logging disabled when log_dir is None

## E2E Test Coverage

- **Test file**: `tests/e2e/agent_hub/test_qa_logging.py`
- **Journey marker**: `@pytest.mark.journey("AH-005")`
- **Test class**: `TestAgentHubAuditLoggingE2E`
- **Covered steps**: All 5 steps (100% coverage)
- **Test status**: Passing (5/5 tests)

### Test Implementation Details

```python
@pytest.mark.journey("AH-005")
class TestAgentHubAuditLoggingE2E:
    def test_ask_expert_logs_exchange_automatically_e2e(self):
        """Exchanges are automatically logged."""

    def test_ask_expert_logs_escalation_details_e2e(self):
        """Escalation details included in logs."""

    def test_ask_expert_logs_session_id_e2e(self):
        """Session ID captured in log entries."""

    def test_multiple_ask_expert_calls_all_logged_e2e(self):
        """Multiple exchanges all logged."""

    def test_ask_expert_logs_routing_decision_e2e(self):
        """Routing decision recorded in logs."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Logging enabled | All exchanges logged | `test_ask_expert_logs_exchange_automatically_e2e` |
| Escalation occurs | Escalation in log | `test_ask_expert_logs_escalation_details_e2e` |
| Session context | session_id in log | `test_ask_expert_logs_session_id_e2e` |
| Multiple calls | All calls logged | `test_multiple_ask_expert_calls_all_logged_e2e` |
| Routing tracked | Decision recorded | `test_ask_expert_logs_routing_decision_e2e` |

## Related Journeys

- **AH-001**: Route Question (routing decision logged)
- **AH-002**: Session Management (session_id in logs)
- **AH-003**: Confidence Escalation (escalation details logged)
- **AH-004**: Track Pending Escalations (escalation status logged)
- **KR-004**: Log Q&A Exchange (underlying logger)

## API Reference

```python
# Enable logging when creating AgentHub
hub = AgentHub(config, log_dir="/path/to/logs")

# Ask expert - exchange automatically logged
response = hub.ask_expert(
    topic="architecture",
    question="What pattern should we use?",
    feature_id="005-arch",
)

# Retrieve logs for a feature
logs = hub.get_logs_for_feature("005-arch")
for log in logs:
    print(f"Question: {log['question']['question']}")
    print(f"Session: {log['session_id']}")
    print(f"Confidence: {log['answer']['confidence']}%")
    if log['escalation']:
        print(f"Escalated: {log['escalation']['id']}")
```

### Log Entry Structure

```python
{
    "id": "uuid",
    "feature_id": "005-arch",
    "question": {...},           # Full Question object
    "answer": {...},             # Full Answer object
    "validation_result": {...},  # Outcome, threshold
    "escalation": {...} | None,  # If escalated
    "final_answer": {...},       # Final answer used
    "routing_decision": "Routed to architect (@duc) based on topic 'architecture'",
    "total_duration_seconds": 3.5,
    "session_id": "uuid",        # Session context (T067)
    "created_at": "2026-01-05T..."
}
```

## Implementation References

- **Spec**: `specs/005-agent-hub-refactor/spec.md` (User Story 5)
- **Hub Code**: `src/agent_hub/hub.py` (lines 465-514)
- **Logger**: `src/agent_hub/logger.py`
- **Models**: `src/agent_hub/models.py::QALogEntry`
- **E2E Tests**: `tests/e2e/agent_hub/test_qa_logging.py`
- **Unit Tests**: `tests/unit/agent_hub/test_logger.py`

## Notes

- Logs stored as JSONL (one JSON object per line)
- Each feature gets its own log file: `{feature_id}.jsonl`
- Logging is optional - pass `log_dir=None` to disable
- session_id enables correlation with session history
- Escalation details preserved for retrospective analysis
- Logs are append-only for audit trail integrity
