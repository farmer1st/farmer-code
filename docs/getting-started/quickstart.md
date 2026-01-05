# Quick Start

Get Farmer Code running in 5 minutes.

## TL;DR

```bash
git clone https://github.com/farmer1st/farmcode.git
cd farmcode
uv sync
uv run pytest tests/unit/  # Unit tests (no credentials needed)
```

## Step-by-Step

### 1. Clone & Install

```bash
git clone https://github.com/farmer1st/farmcode.git
cd farmcode
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
tests/unit/knowledge_router/test_models_question.py::TestQuestionModel PASSED
tests/unit/knowledge_router/test_validator.py::TestConfidenceValidator PASSED
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

## What's Next?

| Task | Guide |
|------|-------|
| Understand the codebase | [Architecture Overview](../architecture/README.md) |
| Contribute a feature | [Development Workflow](./development-workflow.md) |
| Explore modules | [Module Documentation](../modules/README.md) |
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
