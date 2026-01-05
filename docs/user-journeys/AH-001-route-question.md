# AH-001: Route Question to Expert Agent

**Actor**: Orchestration Agent (@baron PM Agent or similar)
**Goal**: Route a question to the appropriate expert agent via `ask_expert()` and receive a structured HubResponse
**Preconditions**:
- Hub configuration loaded with agent definitions and topics
- Expert agents defined (architect, product, etc.)
- Valid topic configured in routing config

**Priority**: P1 (MVP - Foundation for Agent Hub)

## Overview

This journey represents the core ask_expert flow of the Agent Hub. Unlike the legacy `route_question()` API, `ask_expert()` provides a higher-level interface that:
- Returns a structured `HubResponse` with answer, confidence, and session_id
- Automatically validates confidence and escalates when needed
- Creates sessions for multi-turn conversations
- Validates topics and provides helpful error messages

## Steps

### 1. Call ask_expert with Topic and Question
- **Action**: Orchestration agent calls `hub.ask_expert(topic, question, context, feature_id)`
- **Expected outcome**: Request is validated and processed
- **System behavior**:
  - Validates topic is configured (raises `UnknownTopicError` if not)
  - Creates new session or reuses existing session_id
  - Builds Question object with validated parameters

### 2. Route to Expert Agent
- **Action**: Hub resolves which agent handles the topic
- **Expected outcome**: Correct agent is selected based on:
  1. Topic overrides in config (highest priority)
  2. Agent topic mappings
  3. Default to human if no match
- **System behavior**:
  - Uses `RoutingConfig.get_agent_for_topic()` for resolution
  - If routing directly to human, returns PENDING_HUMAN immediately

### 3. Dispatch and Get Answer
- **Action**: Hub dispatches question to expert agent via CLI
- **Expected outcome**: Agent provides structured JSON answer
- **System behavior**:
  - AgentRouter spawns `claude --model {model} --print -p "{prompt}"`
  - Parses answer with rationale, confidence, uncertainty_reasons
  - Records response duration

### 4. Validate Confidence
- **Action**: Hub validates answer confidence against threshold
- **Expected outcome**: Determines if answer is acceptable or needs escalation
- **System behavior**:
  - Default threshold: 80%
  - Topic-specific thresholds from overrides
  - If below threshold, creates escalation

### 5. Return HubResponse
- **Action**: Hub returns structured response to caller
- **Expected outcome**: HubResponse with all relevant fields
- **System behavior**:
  - Status: RESOLVED (high confidence) or PENDING_HUMAN (escalated)
  - Includes session_id for follow-up questions
  - Includes escalation_id if escalated

## Success Criteria

- Question routed to correct agent based on topic
- HubResponse returned with answer, confidence, session_id
- Low confidence answers trigger PENDING_HUMAN status
- Unknown topics raise UnknownTopicError with available topics list
- Session created for conversation tracking

## E2E Test Coverage

- **Test file**: `tests/e2e/agent_hub/test_route_question.py`
- **Journey marker**: `@pytest.mark.journey("AH-001")`
- **Test class**: `TestAskExpertE2E`
- **Covered steps**: All 5 steps (100% coverage)
- **Test status**: Passing

### Test Implementation Details

```python
@pytest.mark.journey("AH-001")
class TestAskExpertE2E:
    def test_ask_expert_routes_and_returns_response_e2e(self):
        """Routes authentication topic to architect and returns HubResponse."""

    def test_ask_expert_low_confidence_triggers_escalation_e2e(self):
        """Low confidence answer triggers PENDING_HUMAN status."""

    def test_ask_expert_unknown_topic_returns_error_e2e(self):
        """Unknown topic raises UnknownTopicError."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Unknown topic | Raises `UnknownTopicError` with available topics | `test_hub.py::test_unknown_topic_includes_available_topics` |
| Low confidence | Returns PENDING_HUMAN with escalation_id | `test_route_question.py::test_ask_expert_low_confidence_triggers_escalation_e2e` |
| Agent dispatch failure | Raises `AgentDispatchError` | `test_router.py` |
| Agent timeout | Raises `AgentTimeoutError` | `test_router.py` |

## Related Journeys

- **AH-002**: Session Management (multi-turn conversations)
- **AH-003**: Confidence Escalation (low confidence handling)
- **AH-004**: Pending Escalation Tracking (check escalation status)
- **AH-005**: Audit Logging (Q&A exchange logging)
- **KR-001**: Route Question (legacy lower-level API)

## API Reference

```python
# Basic usage
response = hub.ask_expert(
    topic="authentication",
    question="What auth method should we use for the API?",
    context="Building REST API for mobile clients",
    feature_id="005-user-auth"
)

# Check response status
if response.status == ResponseStatus.RESOLVED:
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence}%")
elif response.status == ResponseStatus.PENDING_HUMAN:
    print(f"Escalated: {response.escalation_id}")
    # Poll check_escalation() for resolution
```

## Implementation References

- **Spec**: `specs/005-agent-hub-refactor/spec.md` (User Story 1)
- **Contract**: `specs/005-agent-hub-refactor/contracts/agent-hub-api.md`
- **Code**: `src/agent_hub/hub.py::ask_expert()`
- **Router**: `src/agent_hub/router.py::AgentRouter`
- **Tests**: `tests/e2e/agent_hub/test_route_question.py`
- **Unit Tests**: `tests/unit/agent_hub/test_hub.py`

## Notes

- Questions are built internally from topic, question, context parameters
- Session IDs are UUIDs generated automatically
- Topic validation happens before routing
- Confidence validation uses ConfidenceValidator from Phase 2 (KR-002)
- Escalation uses EscalationHandler from Phase 3 (KR-003)
