# KR-004: Log Q&A Exchange for Retrospectives

**Actor**: Knowledge Router Service
**Goal**: Immutably log all Q&A exchanges for retrospective analysis
**Preconditions**:
- Q&A exchange completed (accepted or escalated+resolved)
- Log directory exists (`logs/qa/`)
- Feature ID available for file naming

**Priority**: P1 (Critical - Audit trail and improvement data)

## Steps

### 1. Create QALogEntry
- **Action**: Assemble complete log entry with all exchange data
- **Expected outcome**: `QALogEntry` with question, answer, validation, escalation
- **System behavior**:
  - Captures original question
  - Captures agent's answer
  - Captures validation result (outcome, threshold)
  - Captures escalation and human response if applicable
  - Captures final answer (may differ from original)
  - Records routing decision explanation
  - Records total duration

### 2. Serialize to JSON
- **Action**: `QALogger._serialize_entry()` converts to JSON-safe dict
- **Expected outcome**: Complete JSON representation
- **System behavior**:
  - Uses Pydantic's `model_dump(mode="json")`
  - Handles datetime serialization
  - Handles nested models

### 3. Append to JSONL File
- **Action**: `QALogger.log_exchange()` appends to feature log
- **Expected outcome**: Entry appended to `logs/qa/{feature_id}.jsonl`
- **System behavior**:
  - Creates directory if needed
  - Opens file in append mode
  - Writes single JSON line
  - Each feature has its own log file

### 4. Support Chain Retrieval
- **Action**: `QALogger.get_exchange_chain()` for linked entries
- **Expected outcome**: Complete chain from original to final
- **System behavior**:
  - Uses `parent_id` to trace re-routed exchanges
  - Returns chronologically ordered list
  - Supports retrospective analysis

## Success Criteria

- Every Q&A exchange is logged immutably
- Logs are organized by feature_id
- Escalations and human responses are captured
- Re-routed exchanges are linked via parent_id
- Logs are retrievable by feature_id
- Exchange chains are reconstructable

## E2E Test Coverage

- **Test file**: `tests/e2e/knowledge_router/test_qa_logging.py`
- **Journey marker**: `@pytest.mark.journey("KR-004")`
- **Test class**: `TestQALoggingE2E`
- **Covered steps**: All 4 steps (100% coverage)
- **Test status**: Passing

### Test Implementation Details

```python
@pytest.mark.journey("KR-004")
class TestQALoggingE2E:
    def test_complete_qa_exchange_is_logged_e2e(self):
        """Complete Q&A exchange is logged to JSONL."""

    def test_escalated_exchange_is_fully_logged_e2e(self):
        """Escalated exchange with human response is logged."""

    def test_rerouted_exchange_chain_is_linked_e2e(self):
        """Re-routed exchanges form a linked chain."""

    def test_multiple_features_logged_separately_e2e(self):
        """Different features have separate log files."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Nonexistent feature log | Returns empty list | `test_logger.py::test_get_log_for_nonexistent_feature` |
| Multiple entries | All appended correctly | `test_logger.py::test_log_exchange_appends_multiple_entries` |
| Chain retrieval | Returns full chain | `test_logger.py::test_get_exchange_chain` |
| Missing parent | Chain ends at available entries | `test_logger.py` |

## Related Journeys

- **KR-001**: Route Question to Agent (logged)
- **KR-002**: Validate Answer Confidence (logged)
- **KR-003**: Escalate to Human (logged)
- **KR-007**: Generate Retrospective Report (consumes logs)

## Implementation References

- **Spec**: `specs/004-knowledge-router/spec.md` (User Story 4)
- **Code**: `src/knowledge_router/logger.py::QALogger`
- **Model**: `src/knowledge_router/models.py::QALogEntry`
- **Tests**: `tests/e2e/knowledge_router/test_qa_logging.py`

## Log Entry Structure

```json
{
  "id": "uuid",
  "feature_id": "005-user-auth",
  "question": {
    "id": "uuid",
    "topic": "authentication",
    "suggested_target": "architect",
    "question": "Which auth method?",
    "feature_id": "005-user-auth"
  },
  "answer": {
    "question_id": "uuid",
    "answered_by": "@duc",
    "answer": "Use OAuth2 with JWT.",
    "rationale": "Industry standard...",
    "confidence": 92,
    "model_used": "opus",
    "duration_seconds": 3.5
  },
  "validation_result": {
    "outcome": "accepted",
    "threshold_used": 80,
    "threshold_source": "default"
  },
  "escalation": null,
  "human_response": null,
  "final_answer": { ... },
  "routing_decision": "Routed to architect based on topic",
  "total_duration_seconds": 3.5,
  "parent_id": null,
  "created_at": "2026-01-03T12:00:00Z"
}
```

## File Organization

```
logs/
  qa/
    005-user-auth.jsonl     # All Q&A for feature 005
    006-payments.jsonl      # All Q&A for feature 006
    007-notifications.jsonl # All Q&A for feature 007
```

## Notes

- Logs are append-only (immutable)
- JSONL format allows line-by-line processing
- parent_id enables chain reconstruction for re-routes
- Logs support retrospective analysis and agent improvement
- Future: Compress old logs, retention policy
