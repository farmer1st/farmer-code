# AH-003: Validate Confidence and Escalate

**Actor**: Orchestration Agent (@baron PM Agent or similar)
**Goal**: Low-confidence answers trigger human escalation with pending status
**Preconditions**:
- AgentHub initialized with ConfidenceValidator and EscalationHandler
- Confidence thresholds configured (default 80%)
- Expert agent provides answer with confidence score

**Priority**: P2 (Essential for quality assurance)

## Overview

This journey covers confidence validation and human escalation within the ask_expert flow. When an expert agent provides a low-confidence answer, the Hub automatically:
- Validates the confidence against topic-specific thresholds
- Creates an escalation request for human review
- Returns PENDING_HUMAN status with escalation_id
- Preserves uncertainty reasons for human context

## Steps

### 1. Expert Agent Returns Answer

- **Action**: Expert agent provides answer via ask_expert()
- **Expected outcome**: Answer includes confidence score and optional uncertainty_reasons
- **System behavior**:
  - AgentRouter parses JSON response from CLI
  - Answer model validated with confidence 0-100

### 2. Validate Confidence Against Threshold

- **Action**: Hub validates confidence using ConfidenceValidator
- **Expected outcome**: Validation determines ACCEPTED or ESCALATE
- **System behavior**:
  - Checks for topic-specific threshold override
  - Falls back to default threshold (80%)
  - Returns AnswerValidationResult with outcome

### 3. Create Escalation (If Low Confidence)

- **Action**: Hub creates escalation request when confidence < threshold
- **Expected outcome**: EscalationRequest created with full context
- **System behavior**:
  - EscalationHandler.create_escalation() generates escalation
  - Includes original question, tentative answer, threshold used
  - Escalation stored for later retrieval

### 4. Return PENDING_HUMAN Response

- **Action**: Hub returns HubResponse with escalation details
- **Expected outcome**: Response indicates human review needed
- **System behavior**:
  - status = ResponseStatus.PENDING_HUMAN
  - escalation_id set for tracking
  - Original answer and uncertainty_reasons preserved

### 5. High Confidence Path (No Escalation)

- **Action**: Hub returns RESOLVED for high-confidence answers
- **Expected outcome**: Response ready for immediate use
- **System behavior**:
  - status = ResponseStatus.RESOLVED
  - escalation_id = None
  - Answer can be used directly

## Success Criteria

- Low confidence (< threshold) triggers PENDING_HUMAN status
- Escalation_id returned for tracking human review
- Topic-specific thresholds honored (e.g., security = 95%)
- High confidence answers return RESOLVED immediately
- Uncertainty reasons preserved in response

## E2E Test Coverage

- **Test file**: `tests/e2e/agent_hub/test_escalation_flow.py`
- **Journey marker**: `@pytest.mark.journey("AH-003")`
- **Test class**: `TestConfidenceEscalationE2E`
- **Covered steps**: All 5 steps (100% coverage)
- **Test status**: Passing (5/5 tests)

### Test Implementation Details

```python
@pytest.mark.journey("AH-003")
class TestConfidenceEscalationE2E:
    def test_ask_expert_low_confidence_creates_escalation_e2e(self):
        """Low confidence answer creates escalation with proper fields."""

    def test_ask_expert_topic_override_triggers_escalation_e2e(self):
        """Topic override threshold can trigger escalation."""

    def test_ask_expert_high_confidence_no_escalation_e2e(self):
        """High confidence answers don't create escalation."""

    def test_ask_expert_escalation_preserves_uncertainty_reasons_e2e(self):
        """Escalation response includes uncertainty reasons."""

    def test_ask_expert_escalation_with_session_context_e2e(self):
        """Escalation works correctly within session context."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Low confidence (< 80%) | PENDING_HUMAN status, escalation_id set | `test_ask_expert_low_confidence_creates_escalation_e2e` |
| Topic override threshold | 88% fails 95% security threshold | `test_ask_expert_topic_override_triggers_escalation_e2e` |
| High confidence (>= 80%) | RESOLVED status, no escalation | `test_ask_expert_high_confidence_no_escalation_e2e` |
| Multiple uncertainty reasons | All reasons preserved in response | `test_ask_expert_escalation_preserves_uncertainty_reasons_e2e` |

## Related Journeys

- **AH-001**: Route Question (prerequisite - routing to expert)
- **AH-002**: Session Management (session context preserved during escalation)
- **AH-004**: Track Pending Escalations (check escalation status)
- **KR-002**: Validate Answer Confidence (underlying validator)
- **KR-003**: Escalate to Human (escalation handler)

## API Reference

```python
# Low confidence triggers escalation
response = hub.ask_expert(
    topic="security",
    question="What encryption should we use?",
    feature_id="005-security"
)

if response.status == ResponseStatus.PENDING_HUMAN:
    print(f"Escalated: {response.escalation_id}")
    print(f"Confidence: {response.confidence}%")
    print(f"Reasons: {response.uncertainty_reasons}")
    # Human will review via check_escalation()
elif response.status == ResponseStatus.RESOLVED:
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence}%")
```

### Topic-Specific Thresholds

```python
# Config with topic override
config = ConfigLoader.load_from_dict({
    "defaults": {"confidence_threshold": 80},
    "agents": {
        "architect": {
            "name": "@duc",
            "topics": ["security", "compliance"],
        },
    },
    "overrides": {
        "security": {
            "agent": "architect",
            "confidence_threshold": 95,  # Higher for security
        },
    },
})

# 88% passes default but fails security threshold
response = hub.ask_expert(topic="security", ...)
# status = PENDING_HUMAN (88% < 95%)
```

## Implementation References

- **Spec**: `specs/005-agent-hub-refactor/spec.md` (User Story 3)
- **Contract**: `specs/005-agent-hub-refactor/contracts/agent-hub-api.md`
- **Hub Code**: `src/agent_hub/hub.py::ask_expert()` (lines 136-166)
- **Validator**: `src/agent_hub/validator.py::ConfidenceValidator`
- **Escalation**: `src/agent_hub/escalation.py::EscalationHandler`
- **E2E Tests**: `tests/e2e/agent_hub/test_escalation_flow.py`
- **Unit Tests**: `tests/unit/agent_hub/test_validator.py`

## Notes

- Default confidence threshold: 80%
- Topic overrides can set higher (security) or lower (documentation) thresholds
- Escalation preserves full context for human reviewer
- Uncertainty reasons help human understand agent's concerns
- Escalation stored in `self._escalations` dict for later retrieval
- Session messages still recorded even when escalated
