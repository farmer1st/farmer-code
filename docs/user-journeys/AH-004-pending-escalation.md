# AH-004: Track Pending Escalations

**Actor**: Orchestration Agent (@baron PM Agent or similar)
**Goal**: Agents can check escalation status and receive resolved answers
**Preconditions**:
- AgentHub initialized with EscalationHandler
- Prior escalation created via ask_expert (AH-003)
- Human reviewer available to respond

**Priority**: P2 (Essential for complete escalation workflow)

## Overview

This journey covers tracking and resolving pending escalations. After a low-confidence answer triggers an escalation (AH-003), the calling agent can:
- Poll escalation status using check_escalation()
- Process human responses via add_human_response()
- Receive resolved answers or re-route instructions
- Access human feedback through session history

## Steps

### 1. Check Escalation Status

- **Action**: Agent calls check_escalation(escalation_id)
- **Expected outcome**: Returns EscalationRequest with current status
- **System behavior**:
  - Looks up escalation in internal storage
  - Returns pending, resolved, or expired status
  - Raises EscalationError if not found

### 2. Human Confirms Tentative Answer

- **Action**: Human reviewer confirms the agent's tentative answer
- **Expected outcome**: Escalation resolved with original answer
- **System behavior**:
  - add_human_response(action=CONFIRM) called
  - Escalation status set to "resolved"
  - EscalationResult.escalation_resolved = True
  - Original tentative answer becomes final

### 3. Human Corrects Answer

- **Action**: Human reviewer provides corrected answer
- **Expected outcome**: New answer with 100% confidence
- **System behavior**:
  - add_human_response(action=CORRECT, corrected_answer="...")
  - New Answer created with human as author
  - Confidence set to 100%
  - Escalation resolved

### 4. Human Adds Context (Needs Reroute)

- **Action**: Human provides additional context for re-query
- **Expected outcome**: Updated question ready for re-routing
- **System behavior**:
  - add_human_response(action=ADD_CONTEXT, additional_context="...")
  - EscalationResult.needs_reroute = True
  - Updated Question with appended context returned
  - Caller can re-invoke ask_expert with new context

### 5. Human Response Fed Back to Session

- **Action**: Human response automatically added to session
- **Expected outcome**: Session history includes human feedback
- **System behavior**:
  - Message with role=HUMAN added to session
  - Metadata includes responder, action, escalation_id
  - Context preserved for future queries

## Success Criteria

- check_escalation returns correct pending/resolved status
- CONFIRM action resolves with original answer
- CORRECT action creates new answer with 100% confidence
- ADD_CONTEXT sets needs_reroute flag
- Human messages appear in session history
- Non-existent escalation IDs raise EscalationError

## E2E Test Coverage

- **Test file**: `tests/e2e/agent_hub/test_escalation_flow.py`
- **Journey marker**: `@pytest.mark.journey("AH-004")`
- **Test class**: `TestPendingEscalationE2E`
- **Covered steps**: All 5 steps (100% coverage)
- **Test status**: Passing (6/6 tests)

### Test Implementation Details

```python
@pytest.mark.journey("AH-004")
class TestPendingEscalationE2E:
    def test_check_escalation_returns_status_e2e(self):
        """Check escalation returns pending status."""

    def test_add_human_response_confirms_and_resolves_e2e(self):
        """CONFIRM action resolves the escalation."""

    def test_add_human_response_corrects_answer_e2e(self):
        """CORRECT action creates new 100% confidence answer."""

    def test_add_human_response_adds_context_for_reroute_e2e(self):
        """ADD_CONTEXT sets needs_reroute flag."""

    def test_human_response_fed_back_to_session_e2e(self):
        """Human response appears in session history."""

    def test_full_escalation_workflow_e2e(self):
        """Complete workflow: create, check, resolve."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Escalation not found | EscalationError raised | `test_check_escalation_not_found_raises_error` (unit) |
| CONFIRM action | Resolves with original answer | `test_add_human_response_confirms_and_resolves_e2e` |
| CORRECT action | New answer at 100% confidence | `test_add_human_response_corrects_answer_e2e` |
| ADD_CONTEXT action | needs_reroute=True | `test_add_human_response_adds_context_for_reroute_e2e` |
| Session feedback | HUMAN message added | `test_human_response_fed_back_to_session_e2e` |

## Related Journeys

- **AH-001**: Route Question (routing after ADD_CONTEXT)
- **AH-002**: Session Management (human feedback in sessions)
- **AH-003**: Confidence Escalation (creates escalations tracked here)
- **AH-005**: Audit Trail Logging (logs escalation resolutions)

## API Reference

```python
# Check escalation status
escalation = hub.check_escalation(escalation_id)
print(f"Status: {escalation.status}")  # pending, resolved

# Human confirms the answer
result = hub.add_human_response(
    escalation_id=escalation_id,
    action=HumanAction.CONFIRM,
    responder="@farmer1st",
)
assert result.escalation_resolved is True

# Human corrects the answer
result = hub.add_human_response(
    escalation_id=escalation_id,
    action=HumanAction.CORRECT,
    corrected_answer="Use Argon2id for password hashing",
    responder="@farmer1st",
)
assert result.final_answer.confidence == 100

# Human adds context for re-query
result = hub.add_human_response(
    escalation_id=escalation_id,
    action=HumanAction.ADD_CONTEXT,
    additional_context="We need FIPS compliance",
    responder="@farmer1st",
)
if result.needs_reroute:
    # Re-query with updated context
    new_response = hub.ask_expert(
        topic=result.updated_question.topic,
        question=result.updated_question.question,
        context=result.updated_question.context,
        feature_id=result.updated_question.feature_id,
    )
```

### Session History After Human Response

```python
session = hub.get_session(session_id)
for msg in session.messages:
    if msg.role == MessageRole.HUMAN:
        print(f"Human ({msg.metadata['responder']}): {msg.content}")
        print(f"Action: {msg.metadata['action']}")
```

## Implementation References

- **Spec**: `specs/005-agent-hub-refactor/spec.md` (User Story 4)
- **Contract**: `specs/005-agent-hub-refactor/contracts/agent-hub-api.md`
- **Hub Code**: `src/agent_hub/hub.py` (lines 315-409)
- **Escalation Handler**: `src/agent_hub/escalation.py`
- **E2E Tests**: `tests/e2e/agent_hub/test_escalation_flow.py`
- **Unit Tests**: `tests/unit/agent_hub/test_hub.py`

## Notes

- Escalations are stored in `self._escalations` dict (in-memory for now)
- Future enhancement: persist to database for durability
- Human responses are fed back to the session that created the escalation
- NEEDS_REROUTE returns updated question with appended context
- Escalation status transitions: pending -> resolved (or expired)
- Human responder must match pattern `@?[a-z0-9][a-z0-9-]*$`
