# Running Tests

How to execute Farmer Code tests.

## Quick Reference

```bash
# All tests
uv run pytest

# By type
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/

# By module
uv run pytest tests/unit/agent_hub/
uv run pytest tests/e2e/agent_hub/

# By journey
uv run pytest -m journey
uv run pytest -m "journey('AH-001')"

# With coverage
uv run pytest --cov=src --cov-report=html
```

## Running All Tests

```bash
uv run pytest
```

Expected output:
```
tests/unit/... PASSED
tests/integration/... PASSED
tests/contract/... PASSED
tests/e2e/... PASSED

458 passed in 2.5s
```

## Running by Test Type

### Unit Tests (Fast, No Deps)

```bash
uv run pytest tests/unit/ -v
```

### Integration Tests (Mocked Deps)

```bash
uv run pytest tests/integration/ -v
```

### Contract Tests (Schema Validation)

```bash
uv run pytest tests/contract/ -v
```

### E2E Tests (Require Credentials)

```bash
# Requires .env with valid credentials
uv run pytest tests/e2e/ -v
```

## Running by Module

```bash
# Agent Hub
uv run pytest tests/unit/agent_hub/
uv run pytest tests/e2e/agent_hub/

# Orchestrator
uv run pytest tests/unit/orchestrator/
uv run pytest tests/unit/test_state_machine.py

# Worktree Manager
uv run pytest tests/unit/worktree_manager/
```

## Running Services Tests

Each service has its own test suite in `services/`:

```bash
# Agent Hub service tests
cd services/agent-hub
uv run pytest

# Agent Hub E2E tests (requires RUN_E2E_TESTS=1)
cd services/agent-hub
RUN_E2E_TESTS=1 uv run pytest tests/e2e/ -v

# Baron agent tests
cd services/agents/baron
uv run pytest

# Duc agent tests
cd services/agents/duc
uv run pytest

# Marie agent tests
cd services/agents/marie
uv run pytest
```

### Contract Tests

Each service has contract tests to verify API schemas:

```bash
# Run all contract tests for a service
cd services/agent-hub
uv run pytest tests/contract/ -v
```

## Running Journey Tests

```bash
# All journey tests
uv run pytest -m journey -v

# Specific journey
uv run pytest -m "journey('AH-001')" -v

# All AH journeys
uv run pytest -m "journey" tests/e2e/agent_hub/ -v
```

## Verbose Output

```bash
# Show test names
uv run pytest -v

# Show print statements
uv run pytest -s

# Show both
uv run pytest -vs
```

## Coverage

```bash
# Terminal report
uv run pytest --cov=src --cov-report=term-missing

# HTML report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html

# Specific module coverage
uv run pytest --cov=src/agent_hub tests/unit/agent_hub/
```

## Parallel Execution

```bash
# Run tests in parallel
uv run pytest -n auto

# Specific number of workers
uv run pytest -n 4
```

## Debugging Failures

```bash
# Stop on first failure
uv run pytest -x

# Show full tracebacks
uv run pytest --tb=long

# Enter debugger on failure
uv run pytest --pdb
```

## Filtering Tests

```bash
# By name pattern
uv run pytest -k "test_route"

# By marker
uv run pytest -m "not e2e"

# Combine filters
uv run pytest -k "test_validate" -m "not slow"
```

## Troubleshooting

### Tests Skip Due to Missing Credentials

```
SKIPPED [1] tests/e2e/...: Missing GITHUB_TOKEN
```

**Fix**: Create `.env` with credentials:

```bash
cp .env.example .env
# Edit .env with your tokens
```

### Module Not Found

```
ModuleNotFoundError: No module named 'agent_hub'
```

**Fix**: Use `uv run`:

```bash
uv run pytest  # Correct
pytest          # Wrong
```

### Slow Tests

```bash
# Skip slow tests
uv run pytest -m "not slow"

# Run only fast tests
uv run pytest tests/unit/ tests/contract/
```
