# Testing Guide

How to run and write tests for FarmCode.

## Contents

| Document | Description |
|----------|-------------|
| [Running Tests](./running-tests.md) | How to execute tests |
| [Writing Tests](./writing-tests.md) | How to write new tests |

## Test Organization

```
tests/
├── unit/                    # Unit tests (no external deps)
│   └── [module]/           # Tests per module
├── integration/             # Integration tests (mocked externals)
│   └── [module]/
├── contract/                # Contract/schema tests
│   └── [module]/
└── e2e/                     # End-to-end tests (real externals)
    └── [module]/
```

## Quick Start

```bash
# Run all tests
uv run pytest

# Run specific test type
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/contract/
uv run pytest tests/e2e/

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run journey tests
uv run pytest -m journey
```

## Test Types

### Unit Tests

Test individual functions/classes in isolation.

```python
# tests/unit/knowledge_router/test_validator.py
def test_high_confidence_is_accepted():
    validator = ConfidenceValidator(default_threshold=80)
    result = validator.validate(answer_with_confidence(85))
    assert result.outcome == ValidationOutcome.ACCEPTED
```

**Characteristics**:
- No external dependencies
- Fast execution
- Test single units of code

### Integration Tests

Test module interactions with mocked externals.

```python
# tests/integration/knowledge_router/test_dispatch.py
def test_agent_dispatch_with_mock_cli(mock_subprocess):
    mock_subprocess.return_value.stdout = '{"answer": "Use OAuth2"}'
    dispatcher = AgentDispatcher()
    handle = dispatcher.dispatch(config, question)
    assert handle.status == AgentStatus.COMPLETED
```

**Characteristics**:
- Mock external systems (GitHub, Git, Claude)
- Test module integration points
- Medium execution time

### Contract Tests

Validate data schemas and API contracts.

```python
# tests/contract/knowledge_router/test_question_schema.py
def test_question_schema_matches_contract():
    with open("specs/.../contracts/question.json") as f:
        schema = json.load(f)

    question = Question(...)
    validate(question.model_dump(), schema)  # Should not raise
```

**Characteristics**:
- Verify JSON schemas
- Check API contracts
- Prevent breaking changes

### E2E Tests

Test full user journeys with real systems.

```python
# tests/e2e/knowledge_router/test_route_question.py
@pytest.mark.e2e
@pytest.mark.journey("KR-001")
def test_route_question_to_architect_e2e():
    """Test KR-001: Route Question to Knowledge Agent."""
    router = KnowledgeRouter(config_path)
    question = Question(topic="architecture", ...)

    handle = router.route_question(question)

    assert handle.agent_name == "@duc"
    assert handle.status == AgentStatus.DISPATCHED
```

**Characteristics**:
- Use real external systems
- Test complete workflows
- Require credentials
- Tagged with journey markers

## Journey Markers

E2E tests MUST be tagged with journey markers:

```python
@pytest.mark.e2e
@pytest.mark.journey("KR-001")
def test_something_e2e():
    ...
```

Run journey tests:

```bash
# All journey tests
uv run pytest -m journey

# Specific journey
uv run pytest -m "journey and KR-001"
```

## Coverage Requirements

- New code: 80% minimum coverage
- Critical paths: 100% coverage
- Journey tests: 100% for MVP journeys

Check coverage:

```bash
uv run pytest --cov=src --cov-report=term-missing
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Test Configuration

Configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
markers = [
    "e2e: End-to-end tests",
    "journey(id): User journey marker",
]
```

## Fixtures

Common fixtures are in `conftest.py`:

```python
# tests/conftest.py
@pytest.fixture
def mock_github_service():
    return Mock(spec=GitHubService)

@pytest.fixture
def sample_question():
    return Question(
        id="q-001",
        topic="architecture",
        ...
    )
```

## Related Documentation

- [Development Workflow](../getting-started/development-workflow.md)
- [User Journeys](../user-journeys/JOURNEYS.md)
- [Constitution - TDD](../../.specify/memory/constitution.md)
