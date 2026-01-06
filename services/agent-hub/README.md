# Agent Hub Service

The Agent Hub Service provides central coordination for agent interactions, session management, and expert routing.

## Overview

The Agent Hub provides:
- Expert agent routing based on topic
- Session management for multi-turn conversations
- Human escalation when confidence is low
- Audit logging for all interactions

## Quick Start

### Running Locally

```bash
cd services/agent-hub

# Install dependencies
uv sync

# Run the service
uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

### Running with Docker

```bash
# Build image
docker build -t agent-hub:latest .

# Run container
docker run -p 8001:8001 agent-hub:latest
```

### API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## API Reference

### Ask Expert

Route a question to the appropriate expert agent:

```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "architecture",
    "question": "Should we use microservices?",
    "feature_id": "008-services"
  }'
```

**Response:**
```json
{
  "answer": "Based on your requirements...",
  "confidence": 85,
  "status": "resolved",
  "session_id": "sess_abc123",
  "escalation_id": null
}
```

### Invoke Agent Directly

Invoke a specific agent without routing:

```bash
curl -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "baron",
    "topic": "specification",
    "context": {
      "question": "Generate a feature spec"
    }
  }'
```

### Session Management

```bash
# Create session
curl -X POST http://localhost:8001/sessions \
  -H "Content-Type: application/json" \
  -d '{"feature_id": "008-services"}'

# Get session
curl http://localhost:8001/sessions/{session_id}

# Add message to session
curl -X POST http://localhost:8001/sessions/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "Follow-up question"}'
```

### Escalation Management

```bash
# Get pending escalations
curl http://localhost:8001/escalations

# Resolve escalation
curl -X POST http://localhost:8001/escalations/{escalation_id}/resolve \
  -H "Content-Type: application/json" \
  -d '{"resolution": "Use JWT for auth", "resolved_by": "human"}'
```

### Health Check

```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "service": "agent-hub",
  "uptime_seconds": 3600,
  "agents": {
    "baron": "healthy",
    "duc": "healthy",
    "marie": "healthy"
  }
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8001 | Service port |
| DATABASE_URL | sqlite:///./data/agent-hub.db | Database connection |
| BARON_URL | http://localhost:8002 | Baron agent URL |
| DUC_URL | http://localhost:8003 | Duc agent URL |
| MARIE_URL | http://localhost:8004 | Marie agent URL |
| CONFIDENCE_THRESHOLD | 70 | Minimum confidence for auto-resolution |
| PYTHONUNBUFFERED | 1 | Enable unbuffered output |

## Agent Routing

| Topic | Agent | Description |
|-------|-------|-------------|
| specification, planning, tasks | Baron | PM workflows |
| architecture, api_design, system_design | Duc | Architecture guidance |
| testing, edge_cases, qa_review | Marie | Testing expertise |

## Testing

```bash
cd services/agent-hub

# Run all tests
uv run pytest

# Run contract tests only
uv run pytest tests/contract/ -v

# Run E2E tests
RUN_E2E_TESTS=1 uv run pytest tests/e2e/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
services/agent-hub/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── health.py
│   │   ├── ask.py
│   │   ├── invoke.py
│   │   ├── sessions.py
│   │   └── escalations.py
│   ├── core/
│   │   ├── router.py
│   │   └── session.py
│   ├── db/
│   │   ├── models.py
│   │   └── repository.py
│   ├── clients/
│   │   └── agent.py
│   └── logging/
│       └── audit.py
├── tests/
│   ├── conftest.py
│   ├── contract/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── Dockerfile
└── pyproject.toml
```

## Related Documentation

- [Orchestrator Service](../orchestrator/README.md)
- [Baron Agent](../agents/baron/README.md)
- [Duc Agent](../agents/duc/README.md)
- [Marie Agent](../agents/marie/README.md)
- [Services Documentation](../../docs/services/agent-hub.md)
