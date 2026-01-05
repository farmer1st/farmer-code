# Writing Tests

How to write tests for Farmer Code following TDD principles.

## TDD Workflow (NON-NEGOTIABLE)

1. **Write test first** (Red)
2. **Run test - should fail**
3. **Write minimal implementation** (Green)
4. **Run test - should pass**
5. **Refactor** (Clean)

## Test Structure

### Unit Test Template

```python
"""Unit tests for [component]."""
import pytest
from [module] import [Class]


class Test[ClassName]:
    """Test suite for [ClassName]."""

    def test_[behavior]_when_[condition](self):
        """[What should happen] when [condition]."""
        # Arrange
        instance = [Class](...)

        # Act
        result = instance.method(...)

        # Assert
        assert result == expected
```

### E2E Test Template

```python
"""E2E tests for [journey]."""
import pytest
from [module] import [Service]


@pytest.mark.e2e
@pytest.mark.journey("[DOMAIN]-[NNN]")
class Test[JourneyName]E2E:
    """E2E tests for [DOMAIN]-[NNN]: [Journey Name]."""

    def test_[step]_e2e(self):
        """Test [step description] end-to-end."""
        # Full integration test
        service = [Service](...)
        result = service.do_something(...)
        assert result.success
```

## Naming Conventions

### Test Files

```
tests/
├── unit/[module]/
│   └── test_[component].py      # test_validator.py
├── integration/[module]/
│   └── test_[feature].py        # test_dispatch.py
├── contract/[module]/
│   └── test_[schema]_schema.py  # test_question_schema.py
└── e2e/[module]/
    └── test_[journey].py        # test_route_question.py
```

### Test Functions

```python
# Pattern: test_[what]_[when/condition]
def test_answer_is_accepted_when_confidence_above_threshold():
    ...

def test_question_routes_to_architect_for_design_topic():
    ...

def test_escalation_created_when_confidence_below_threshold():
    ...
```

## Fixtures

### Module Fixtures

Create in `tests/[type]/[module]/conftest.py`:

```python
# tests/unit/knowledge_router/conftest.py
import pytest
from knowledge_router import Question, QuestionTarget


@pytest.fixture
def sample_question():
    """Create a sample question for testing."""
    return Question(
        id="q-test",
        topic="architecture",
        suggested_target=QuestionTarget.ARCHITECT,
        question="How should we structure the API?",
        feature_id="test-feature",
    )


@pytest.fixture
def high_confidence_answer(sample_question):
    """Create a high-confidence answer."""
    return Answer(
        question_id=sample_question.id,
        answered_by="@duc",
        answer="Use REST with resource-based URLs.",
        rationale="Standard pattern for this type of API.",
        confidence=90,
        model_used="opus",
        duration_seconds=2.5,
    )
```

### Global Fixtures

Create in `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
from pathlib import Path


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def mock_github():
    """Mock GitHub service."""
    from unittest.mock import Mock
    return Mock()
```

## Mocking

### Mock External Services

```python
from unittest.mock import Mock, patch


def test_dispatch_calls_subprocess(self):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = '{"answer": "Use OAuth2"}'
        mock_run.return_value.returncode = 0

        dispatcher = AgentDispatcher()
        handle = dispatcher.dispatch(config, question)

        mock_run.assert_called_once()
        assert handle.status == AgentStatus.COMPLETED
```

### Mock Dependencies

```python
def test_router_uses_config(self):
    mock_config = Mock(spec=RoutingConfig)
    mock_config.get_agent_for_topic.return_value = AgentDefinition(
        name="@duc", model="opus"
    )

    router = KnowledgeRouter(config=mock_config)
    handle = router.route_question(question)

    mock_config.get_agent_for_topic.assert_called_with("architecture")
```

## Testing Exceptions

```python
def test_raises_error_when_no_agent_available(self):
    config = RoutingConfig(agents=[])  # No agents

    with pytest.raises(RoutingError) as exc_info:
        router = KnowledgeRouter(config)
        router.route_question(question)

    assert "No agent available" in str(exc_info.value)
```

## Parametrized Tests

```python
@pytest.mark.parametrize("confidence,expected_outcome", [
    (90, ValidationOutcome.ACCEPTED),
    (80, ValidationOutcome.ACCEPTED),
    (79, ValidationOutcome.ESCALATE),
    (50, ValidationOutcome.ESCALATE),
])
def test_validation_outcomes(self, confidence, expected_outcome):
    answer = create_answer(confidence=confidence)
    result = validator.validate(answer)
    assert result.outcome == expected_outcome
```

## Journey Markers

E2E tests MUST have journey markers:

```python
@pytest.mark.e2e
@pytest.mark.journey("KR-001")
def test_route_question_to_architect_e2e():
    """Test KR-001: Route Question to Knowledge Agent.

    Steps tested:
    - Step 1: Create question with architecture topic
    - Step 2: Route to appropriate agent
    - Step 3: Verify agent received question
    """
    ...
```

## Test Documentation

Each test should have a docstring explaining:

```python
def test_escalation_includes_uncertainty_reasons(self):
    """Escalation request includes reasons for low confidence.

    Given:
        - Answer with 65% confidence
        - Uncertainty reasons: ["Missing context", "Ambiguous question"]

    When:
        - Validation triggers escalation

    Then:
        - EscalationRequest contains uncertainty_reasons list
        - GitHub comment format includes reasons
    """
    ...
```

## Common Patterns

### Testing File Operations

```python
def test_logs_written_to_file(self, tmp_path):
    log_path = tmp_path / "logs" / "qa"
    logger = QALogger(log_path)

    logger.log_exchange(entry)

    log_file = log_path / f"{entry.feature_id}.jsonl"
    assert log_file.exists()
    assert entry.id in log_file.read_text()
```

### Testing State Changes

```python
def test_state_transitions_correctly(self):
    machine = StateMachine()

    # Initial state
    assert machine.current_state == WorkflowState.IDLE

    # Transition
    machine.transition("phase_1_start")
    assert machine.current_state == WorkflowState.PHASE_1

    # Invalid transition
    with pytest.raises(InvalidStateTransition):
        machine.transition("approval_received")  # Can't skip to end
```

## Checklist

Before submitting PR, verify:

- [ ] Tests written BEFORE implementation
- [ ] All tests pass (`uv run pytest`)
- [ ] E2E tests have journey markers
- [ ] New code has 80%+ coverage
- [ ] Test names describe behavior
- [ ] Docstrings explain test purpose
