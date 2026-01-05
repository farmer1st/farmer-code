# Orchestrator Service

The Orchestrator Service manages SDLC workflow state and coordinates feature development phases.

## Overview

The Orchestrator provides:
- Workflow state management
- Phase transitions (IDLE -> PHASE_1 -> GATE_1 -> PHASE_2 -> DONE)
- Integration with Agent Hub for expert consultations
- Feature progress tracking

## Quick Start

### Running Locally

```bash
cd services/orchestrator

# Install dependencies
uv sync

# Run the service
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running with Docker

```bash
# Build image
docker build -t orchestrator:latest .

# Run container
docker run -p 8000:8000 orchestrator:latest
```

### API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Reference

### Start Workflow

```bash
curl -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{
    "feature_id": "008-services-architecture",
    "description": "Refactor to microservices"
  }'
```

### Get Workflow Status

```bash
curl http://localhost:8000/workflow/008-services-architecture
```

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "service": "orchestrator",
  "uptime_seconds": 3600
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8000 | Service port |
| DATABASE_URL | sqlite:///./data/orchestrator.db | Database connection |
| AGENT_HUB_URL | http://localhost:8001 | Agent Hub service URL |
| PYTHONUNBUFFERED | 1 | Enable unbuffered output |

## Workflow States

| State | Description |
|-------|-------------|
| IDLE | No active workflow |
| PHASE_1 | Specification and planning phase |
| GATE_1 | Review gate before implementation |
| PHASE_2 | Implementation phase |
| DONE | Workflow completed |

## Testing

```bash
cd services/orchestrator

# Run all tests
uv run pytest

# Run contract tests only
uv run pytest tests/contract/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
services/orchestrator/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── health.py
│   │   └── workflow.py
│   ├── core/
│   │   ├── state_machine.py
│   │   └── workflow.py
│   ├── db/
│   │   ├── models.py
│   │   └── repository.py
│   └── clients/
│       └── agent_hub.py
├── tests/
│   ├── conftest.py
│   ├── contract/
│   ├── unit/
│   └── integration/
├── Dockerfile
└── pyproject.toml
```

## Related Documentation

- [Agent Hub Service](../agent-hub/README.md)
- [Architecture Overview](../../docs/architecture/system-overview.md)
- [Services Documentation](../../docs/services/orchestrator.md)
