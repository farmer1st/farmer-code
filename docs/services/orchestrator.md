# Orchestrator Service

The Orchestrator Service manages SpecKit workflow execution, owning workflow definitions and state transitions.

## Overview

The Orchestrator is the entry point for executing SpecKit workflows. It:

- Accepts workflow requests (specify, plan, tasks, implement)
- Manages workflow state machine transitions
- Invokes agents exclusively via Agent Hub (never directly)
- Persists workflow state in SQLite
- Records state transition history for audit

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

### Create Workflow

```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "specify",
    "feature_description": "Add user authentication with OAuth2",
    "context": {"priority": "P1"}
  }'
```

### Get Workflow

```bash
curl http://localhost:8000/workflows/{workflow_id}
```

### Advance Workflow

```bash
curl -X POST http://localhost:8000/workflows/{workflow_id}/advance \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "human_approved",
    "phase_result": {"approved": true}
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              Orchestrator Service            │
├─────────────────────────────────────────────┤
│  API Layer (FastAPI)                        │
│  ├── /workflows                             │
│  ├── /workflows/{id}                        │
│  ├── /workflows/{id}/advance                │
│  └── /health                                │
├─────────────────────────────────────────────┤
│  Core Layer                                 │
│  ├── WorkflowStateMachine                   │
│  └── PhaseExecutor                          │
├─────────────────────────────────────────────┤
│  Client Layer                               │
│  └── AgentHubClient                         │
├─────────────────────────────────────────────┤
│  Database Layer (SQLite)                    │
│  ├── workflows table                        │
│  └── workflow_history table                 │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Agent Hub     │
└─────────────────┘
```

## Workflow Types

| Type | Description | Phases |
|------|-------------|--------|
| specify | Generate feature specification | 2 |
| plan | Create implementation plan | 2 |
| tasks | Generate task breakdown | 2 |
| implement | Execute implementation | 2 |

## State Machine

### States

| State | Description |
|-------|-------------|
| pending | Workflow created, not started |
| in_progress | Agent is executing current phase |
| waiting_approval | Phase complete, awaiting human review |
| completed | All phases complete |
| failed | Error occurred |

### Transitions

| From | Trigger | To |
|------|---------|-----|
| pending | start | in_progress |
| in_progress | agent_complete | waiting_approval |
| in_progress | error | failed |
| waiting_approval | human_approved | in_progress (next phase) or completed |
| waiting_approval | human_rejected | in_progress (rework) or failed |

## Database Schema

```sql
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    workflow_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    feature_id TEXT NOT NULL,
    feature_description TEXT NOT NULL,
    current_phase TEXT,
    context TEXT,  -- JSON
    result TEXT,   -- JSON
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE workflow_history (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    trigger TEXT NOT NULL,
    metadata TEXT,  -- JSON
    created_at TEXT NOT NULL
);
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | sqlite:///./data/orchestrator.db | Database connection |
| AGENT_HUB_URL | http://localhost:8001 | Agent Hub service URL |

## Testing

```bash
cd services/orchestrator

# Run all tests
uv run pytest

# Run contract tests only
uv run pytest tests/contract/ -m contract

# Run integration tests only
uv run pytest tests/integration/ -m integration

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
services/orchestrator/
├── src/
│   ├── __init__.py           # Package metadata
│   ├── main.py               # FastAPI application
│   ├── api/
│   │   ├── health.py         # Health endpoint
│   │   └── workflows.py      # Workflow endpoints
│   ├── core/
│   │   ├── state_machine.py  # Workflow state management
│   │   └── phase_executor.py # Phase execution logic
│   ├── clients/
│   │   └── agent_hub.py      # Agent Hub client
│   └── db/
│       ├── models.py         # SQLAlchemy models
│       └── session.py        # Database session
├── tests/
│   ├── conftest.py
│   ├── contract/             # API contract tests
│   ├── integration/          # Integration tests
│   └── unit/                 # Unit tests
├── Dockerfile
└── pyproject.toml
```

## Related Documentation

- [User Journey: SVC-001](../user-journeys/SVC-001-orchestrator-workflow.md)
- [Agent Hub Service](./agent-hub.md)
- [API Contracts](../reference/api-contracts.md)
