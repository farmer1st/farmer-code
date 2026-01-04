# KR-003: Escalate Low-Confidence Answer to Human

**Actor**: Knowledge Router Service / Human Reviewer
**Goal**: Package low-confidence answers for human review and process human responses
**Preconditions**:
- Answer validation returned ESCALATE outcome
- GitHub integration available for comment posting
- Human reviewer has repository access

**Priority**: P1 (Critical - Human-in-the-loop safety)

## Steps

### 1. Create Escalation Request
- **Action**: `EscalationHandler.create_escalation()` packages answer for review
- **Expected outcome**: `EscalationRequest` with question, answer, threshold
- **System behavior**:
  - Generates unique escalation ID
  - Captures original question and tentative answer
  - Records threshold that was not met
  - Status set to "pending"

### 2. Format GitHub Comment
- **Action**: `format_github_comment()` creates markdown for posting
- **Expected outcome**: Human-readable comment with all context
- **System behavior**:
  - Includes question, tentative answer, confidence score
  - Lists uncertainty reasons if present
  - Provides action instructions (/confirm, /correct, /context)
  - Shows answering agent and model used

### 3. Human Reviews and Responds
- **Action**: Human posts response comment with action
- **Expected outcome**: `HumanResponse` with chosen action
- **Actions available**:
  - `/confirm` - Accept the tentative answer as-is
  - `/correct <answer>` - Provide corrected answer
  - `/context <info>` - Add context and re-route to agent

### 4. Process Human Response
- **Action**: `EscalationHandler.process_response()` handles response
- **Expected outcome**: `EscalationResult` with final answer or re-route
- **System behavior**:
  - CONFIRM: Returns original answer as final
  - CORRECT: Creates new answer with 100% confidence
  - ADD_CONTEXT: Creates updated question for re-routing

## Success Criteria

- All low-confidence answers are escalated
- Human sees complete context (question, answer, rationale)
- All three response actions work correctly
- Re-routed questions include human-provided context
- Escalation status updated on resolution

## E2E Test Coverage

- **Test file**: `tests/e2e/knowledge_router/test_escalation_flow.py`
- **Journey marker**: `@pytest.mark.journey("KR-003")`
- **Test class**: `TestEscalationFlowE2E`
- **Covered steps**: All 4 steps (100% coverage)
- **Test status**: Passing

### Test Implementation Details

```python
@pytest.mark.journey("KR-003")
class TestEscalationFlowE2E:
    def test_low_confidence_triggers_escalation_e2e(self):
        """65% confidence triggers escalation."""

    def test_human_confirms_answer_e2e(self):
        """Human confirms tentative answer."""

    def test_human_corrects_answer_e2e(self):
        """Human provides corrected answer with 100% confidence."""

    def test_human_adds_context_triggers_reroute_e2e(self):
        """Human adds context, question is re-routed."""

    def test_topic_override_affects_escalation_threshold_e2e(self):
        """Security topic with 95% threshold escalates at 90%."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| CONFIRM without correction | Original answer accepted | `test_escalation.py::test_handler_process_confirm_response` |
| CORRECT without answer text | Uses original answer | `test_escalation.py::test_correct_response_without_corrected_answer` |
| ADD_CONTEXT | Re-route with updated question | `test_escalation.py::test_handler_process_add_context_response` |
| Invalid action | ValueError raised | `test_escalation.py` |

## Related Journeys

- **KR-001**: Route Question to Agent (initial routing)
- **KR-002**: Validate Answer Confidence (triggers escalation)
- **KR-004**: Log Q&A Exchange (logs escalation and response)

## Implementation References

- **Spec**: `specs/004-knowledge-router/spec.md` (User Story 3)
- **Code**: `src/knowledge_router/escalation.py::EscalationHandler`
- **Router**: `src/knowledge_router/router.py::escalate_to_human()`
- **Models**: `src/knowledge_router/models.py::EscalationRequest, HumanResponse`
- **Tests**: `tests/e2e/knowledge_router/test_escalation_flow.py`

## GitHub Comment Format

```markdown
## :warning: Low Confidence Answer - Human Review Required

**Topic:** `security`
**Confidence:** 65% (threshold: 80%)

### Question
What encryption algorithm should we use?

### Tentative Answer
Use AES-256 for encryption.

**Rationale:** Standard choice but need more context.

**Uncertainty reasons:**
- Key management approach unclear

---

### Actions

Please respond with one of the following:
- `/confirm` - Accept this answer as-is
- `/correct <your answer>` - Provide the correct answer
- `/context <additional info>` - Add context and retry

**Answered by:** @duc (sonnet)
```

## Notes

- Human-corrected answers get 100% confidence
- Re-routed questions get new ID but link to original
- Escalation timeout not yet implemented (P3)
- GitHub comment posting integration TBD
