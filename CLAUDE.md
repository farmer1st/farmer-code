# Farmer Code Development Guidelines

## Architecture Overview

Farmer Code uses a **microservices architecture** with FastAPI services.

### Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Orchestrator | 8000 | Workflow state machine |
| Agent Hub | 8001 | Central agent coordination |
| Baron | 8002 | PM agent (specify, plan, tasks) |
| Duc | 8003 | Architecture expert |
| Marie | 8004 | Testing expert |

## Project Structure

```text
services/
  orchestrator/           # Workflow state machine (FastAPI)
    src/                  # Service source code
    tests/                # Service tests (unit, integration, contract, e2e)

  agent-hub/              # Agent routing & sessions (FastAPI)
    src/
    tests/

  agents/
    baron/                # PM agent
    duc/                  # Architecture expert
    marie/                # Testing expert

  shared/                 # Shared code and utilities
    src/
      contracts/          # API contracts and models
      github_integration/ # GitHub API client
      worktree_manager/   # Git worktree utilities
    tests/

  tests/                  # Cross-service tests
    e2e/                  # End-to-end tests
    integration/          # Integration tests
    contract/             # Contract tests

docs/                     # MkDocs documentation
```

## Commands

```bash
# Run all tests
uv run pytest

# Run tests for a specific service
uv run pytest services/orchestrator/tests/
uv run pytest services/agent-hub/tests/

# Run linting
uv run ruff check services/
uv run ruff format --check services/

# Run type checking
uv run mypy services/

# Auto-fix lint issues
uv run ruff check --fix services/
uv run ruff format services/

# Start services with Docker
docker-compose up

# Run individual service
cd services/orchestrator
uv run uvicorn src.main:app --port 8000 --reload
```

## Code Style

Python 3.11+: Follow standard conventions with Google-style docstrings

## Technologies

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, uv
- **Database**: SQLite (local), JSONL for audit logs
- **Testing**: pytest
- **Linting**: ruff, mypy

## Services Documentation

See `docs/services/` for detailed service documentation:
- [Orchestrator](docs/services/orchestrator.md) - Workflow management
- [Agent Hub](docs/services/agent-hub.md) - Agent coordination

## Development Workflow

1. Make changes in `services/` for new features
2. Run `docker-compose up` to test locally
3. Check health endpoints: `curl http://localhost:8000/health`
4. Run tests before committing

## Test Organization

Tests are organized within each service:
- **Unit tests**: `services/*/tests/unit/` - Test individual components
- **Integration tests**: `services/*/tests/integration/` - Test component interactions
- **Contract tests**: `services/*/tests/contract/` - Test API contracts
- **E2E tests**: `services/*/tests/e2e/` - End-to-end tests

Cross-service tests live in `services/tests/`.

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
