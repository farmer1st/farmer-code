# Quick Start

Get Farmer Code running in 5 minutes.

## TL;DR

```bash
git clone https://github.com/farmer1st/farmer-code.git
cd farmer-code
uv sync
uv run pytest tests/unit/  # Unit tests (no credentials needed)
```

## Step-by-Step

### 1. Clone & Install

```bash
git clone https://github.com/farmer1st/farmer-code.git
cd farmer-code
uv sync
```

### 2. Verify Installation

```bash
# Should show Python 3.11+
uv run python --version

# Should list installed packages
uv pip list | grep pydantic
```

### 3. Run Unit Tests

Unit tests don't require external credentials:

```bash
uv run pytest tests/unit/ -v
```

Expected output:
```
tests/unit/agent_hub/test_models.py::TestQuestionModel PASSED
tests/unit/agent_hub/test_validator.py::TestConfidenceValidator PASSED
...
458 passed in 2.5s
```

### 4. (Optional) Full Test Suite

For full tests, configure `.env`:

```bash
cp .env.example .env
# Edit .env with your credentials
uv run pytest
```

## Running with Docker Compose

Start all services with a single command:

```bash
# Copy environment template
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Start all services
docker-compose up

# Or for development with hot reload
docker-compose -f docker-compose.dev.yml up
```

Services will be available at:
- Orchestrator: http://localhost:8000
- Agent Hub: http://localhost:8001
- Baron Agent: http://localhost:8002

Verify services are running:
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

For more details, see [Local Development Setup](../user-journeys/SVC-006-local-dev-setup.md).

## What's Next?

| Task | Guide |
|------|-------|
| Understand the codebase | [Architecture Overview](../architecture/README.md) |
| Contribute a feature | [Development Workflow](./development-workflow.md) |
| Run services locally | [Docker Compose Guide](../user-journeys/SVC-006-local-dev-setup.md) |
| Explore services | [Services Documentation](../services/README.md) |
| Run journey tests | [Testing Guide](../testing/README.md) |

## Quick Reference

```bash
# Tests
uv run pytest                    # All tests
uv run pytest tests/unit/        # Unit only
uv run pytest -m journey         # Journey tests

# Quality
uv run ruff check .              # Lint
uv run mypy src/                 # Types

# Coverage
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```
