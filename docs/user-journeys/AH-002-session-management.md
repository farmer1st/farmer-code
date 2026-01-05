# AH-002: Maintain Conversation Sessions

**Actor**: Orchestration Agent (@baron PM Agent or similar)
**Goal**: Maintain multi-turn conversation sessions with context preservation
**Preconditions**:
- AgentHub initialized with SessionManager
- Valid session created via ask_expert()
- Hub configuration loaded with agent definitions

**Priority**: P1 (Essential for multi-turn conversations)

## Overview

This journey covers session management for multi-turn conversations with expert agents. Sessions preserve conversation context across multiple questions, enabling follow-up questions and coherent dialogue:
- Sessions track all messages (questions and answers)
- Context is preserved for follow-up questions
- Sessions can be closed to prevent further messages
- Session state is queryable via get_session()

## Steps

### 1. Session Creation via ask_expert

- **Action**: Orchestration agent calls `hub.ask_expert()` (without session_id)
- **Expected outcome**: New session created automatically
- **System behavior**:
  - SessionManager.create() generates unique session ID
  - Session initialized with agent_id, feature_id, ACTIVE status
  - Session ID returned in HubResponse.session_id

### 2. Message Recording

- **Action**: Hub records question and answer in session
- **Expected outcome**: Messages preserved with metadata
- **System behavior**:
  - USER message added with question content
  - ASSISTANT message added with answer, confidence, rationale
  - Timestamps recorded for each message
  - Session updated_at refreshed

### 3. Follow-up Questions (Session Reuse)

- **Action**: Orchestration agent calls `hub.ask_expert(session_id=existing_id)`
- **Expected outcome**: Same session reused, context preserved
- **System behavior**:
  - SessionManager.exists() validates session_id
  - New messages appended to existing message history
  - Same session_id returned in HubResponse

### 4. Query Session State

- **Action**: Orchestration agent calls `hub.get_session(session_id)`
- **Expected outcome**: Full session with message history returned
- **System behavior**:
  - Returns Session object with all messages
  - Includes status, created_at, updated_at
  - Raises SessionNotFoundError if not found

### 5. Close Session

- **Action**: Orchestration agent calls `hub.close_session(session_id)`
- **Expected outcome**: Session marked as CLOSED
- **System behavior**:
  - Session status changed to SessionStatus.CLOSED
  - Subsequent add_message calls raise SessionClosedError
  - Session remains queryable via get_session()

## Success Criteria

- Sessions created with unique UUID identifiers
- Message history preserved across multiple ask_expert calls
- Session can be reused by passing session_id parameter
- get_session() returns complete conversation history
- close_session() prevents new messages
- SessionNotFoundError raised for invalid session IDs

## E2E Test Coverage

- **Test file**: `tests/e2e/agent_hub/test_session_management.py`
- **Journey marker**: `@pytest.mark.journey("AH-002")`
- **Test class**: `TestSessionManagementE2E`
- **Covered steps**: All 5 steps (100% coverage)
- **Test status**: Passing (6/6 tests)

### Test Implementation Details

```python
@pytest.mark.journey("AH-002")
class TestSessionManagementE2E:
    def test_ask_expert_creates_session_e2e(self):
        """ask_expert creates a session and returns session_id."""

    def test_session_preserves_context_across_questions_e2e(self):
        """Session preserves context across multiple questions."""

    def test_get_session_returns_full_history_e2e(self):
        """get_session returns complete conversation history."""

    def test_close_session_prevents_new_messages_e2e(self):
        """Closing a session changes status to CLOSED."""

    def test_get_nonexistent_session_raises_error_e2e(self):
        """Getting a nonexistent session raises SessionNotFoundError."""

    def test_session_tracks_multiple_turn_conversation_e2e(self):
        """Complete multi-turn conversation tracking."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Get nonexistent session | Raises `SessionNotFoundError` | `test_session_management.py::test_get_nonexistent_session_raises_error_e2e` |
| Add message to closed session | Raises `SessionClosedError` | `test_session.py::test_add_message_to_closed_session_raises_error` |
| Close nonexistent session | Raises `SessionNotFoundError` | `test_session.py::test_close_nonexistent_session_raises_error` |

## Related Journeys

- **AH-001**: Route Question (creates initial session)
- **AH-003**: Confidence Escalation (escalations linked to sessions)
- **AH-004**: Pending Escalation Tracking (human responses added to session)
- **AH-005**: Audit Logging (session_id included in logs)

## API Reference

```python
# First question creates session
response1 = hub.ask_expert(
    topic="database",
    question="Which database should we use?",
    feature_id="005-db-setup"
)
session_id = response1.session_id  # UUID

# Follow-up question reuses session
response2 = hub.ask_expert(
    topic="caching",
    question="What about caching?",
    session_id=session_id  # Reuse session
)
assert response1.session_id == response2.session_id

# Query session state
session = hub.get_session(session_id)
print(f"Messages: {len(session.messages)}")
for msg in session.messages:
    print(f"  [{msg.role}]: {msg.content[:50]}...")

# Close session when done
hub.close_session(session_id)
assert hub.get_session(session_id).status == SessionStatus.CLOSED
```

## Implementation References

- **Spec**: `specs/005-agent-hub-refactor/spec.md` (User Story 2)
- **Contract**: `specs/005-agent-hub-refactor/contracts/agent-hub-api.md`
- **Hub Code**: `src/agent_hub/hub.py::get_session()`, `close_session()`
- **SessionManager**: `src/agent_hub/session.py::SessionManager`
- **Models**: `src/agent_hub/models.py::Session`, `Message`, `MessageRole`
- **E2E Tests**: `tests/e2e/agent_hub/test_session_management.py`
- **Unit Tests**: `tests/unit/agent_hub/test_session.py`

## Notes

- Sessions use in-memory storage by default (can be extended for persistence)
- Session IDs are UUIDs generated via uuid.uuid4()
- Messages are appended, never modified
- Closed sessions remain queryable but cannot accept new messages
- MessageRole enum: USER, ASSISTANT, HUMAN (for human escalation responses)
