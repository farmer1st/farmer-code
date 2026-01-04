# KR-002: Validate Answer Confidence

**Actor**: Knowledge Router Service
**Goal**: Validate an agent's answer against confidence thresholds and determine if escalation is needed
**Preconditions**:
- Answer received from knowledge agent
- Routing configuration with confidence thresholds
- Threshold can be default (80%) or topic-specific override

**Priority**: P1 (Critical - Core validation logic)

## Steps

### 1. Receive Answer from Agent
- **Action**: Agent returns structured `Answer` with confidence score
- **Expected outcome**: Answer is parsed and validated
- **System behavior**:
  - Validates confidence is 0-100 integer
  - Validates rationale is 20+ characters
  - Validates model_used is valid (opus/sonnet/haiku/human)

### 2. Lookup Threshold for Topic
- **Action**: `ConfidenceValidator` looks up threshold
- **Expected outcome**: Returns threshold and source
- **System behavior**:
  - Check topic-specific override first
  - Fall back to default threshold (80%)
  - Return tuple: (threshold, source)

### 3. Compare Confidence to Threshold
- **Action**: Compare answer.confidence against threshold
- **Expected outcome**: Determine outcome (ACCEPTED or ESCALATE)
- **System behavior**:
  - If confidence >= threshold: ACCEPTED
  - If confidence < threshold: ESCALATE
  - Boundary: exactly at threshold is ACCEPTED

### 4. Return Validation Result
- **Action**: Return `AnswerValidationResult`
- **Expected outcome**: Result contains outcome, answer, threshold info
- **System behavior**:
  - Includes outcome enum (ACCEPTED/ESCALATE)
  - Includes original answer
  - Includes threshold_used and threshold_source

## Success Criteria

- High confidence answers (>= threshold) are ACCEPTED
- Low confidence answers (< threshold) are ESCALATE
- Topic overrides take precedence over default
- Boundary condition (exactly at threshold) is ACCEPTED
- Validation result contains complete context

## E2E Test Coverage

- **Test file**: `tests/e2e/knowledge_router/test_confidence_gate.py`
- **Journey marker**: `@pytest.mark.journey("KR-002")`
- **Test class**: `TestConfidenceGateE2E`
- **Covered steps**: All 4 steps (100% coverage)
- **Test status**: Passing

### Test Implementation Details

```python
@pytest.mark.journey("KR-002")
class TestConfidenceGateE2E:
    def test_high_confidence_answer_accepted_e2e(self):
        """92% confidence passes 80% threshold."""

    def test_low_confidence_answer_escalated_e2e(self):
        """65% confidence fails 80% threshold."""

    def test_topic_override_escalates_despite_high_confidence_e2e(self):
        """90% confidence fails 95% security threshold."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Confidence at threshold (80) | ACCEPTED | `test_validator.py::test_accept_at_threshold` |
| Confidence one below (79) | ESCALATE | `test_validator.py::test_escalate_one_below_threshold` |
| Security topic (95% threshold) | Higher bar | `test_confidence_gate.py::test_topic_override_escalates` |
| Override without threshold | Uses default | `test_validator.py::test_override_without_threshold_uses_default` |

## Related Journeys

- **KR-001**: Route Question to Agent (precedes this journey)
- **KR-003**: Escalate to Human (triggered by ESCALATE outcome)
- **KR-004**: Log Q&A Exchange (logs validation result)

## Implementation References

- **Spec**: `specs/004-knowledge-router/spec.md` (User Story 2)
- **Code**: `src/knowledge_router/validator.py::ConfidenceValidator`
- **Router**: `src/knowledge_router/router.py::submit_answer()`
- **Tests**: `tests/e2e/knowledge_router/test_confidence_gate.py`

## Threshold Configuration

```yaml
# config/routing.yaml
defaults:
  confidence_threshold: 80  # Default for all topics

overrides:
  security:
    agent: architect
    confidence_threshold: 95  # Higher for security topics
  documentation:
    agent: product
    confidence_threshold: 60  # Lower for docs
```

## Notes

- Confidence is self-reported by the agent (0-100)
- Agents should include `uncertainty_reasons` when confidence < 100
- Topic overrides allow risk-based threshold adjustment
- All validations are logged for retrospective analysis
