# Duc Agent Service

Duc is the **Architecture Expert** agent for Farmer Code. It provides guidance on system architecture, API design, and technical decisions.

## Overview

Duc specializes in:
- System architecture design and patterns
- API design and REST/GraphQL decisions
- Technology stack recommendations
- Scalability and performance guidance
- Design trade-off analysis

## Quick Start

### Running Locally

```bash
cd services/agents/duc

# Install dependencies
uv sync

# Run the service
uv run uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
```

### Running with Docker

```bash
# Build image
docker build -t duc:latest .

# Run container
docker run -p 8003:8003 duc:latest
```

### API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

## API Reference

### Invoke Agent

```bash
curl -X POST http://localhost:8003/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "architecture",
    "context": {
      "question": "Should we use microservices or monolith?"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "output": "# Architecture Guidance\n\n...",
    "answer": "Based on your requirements..."
  },
  "confidence": 85,
  "metadata": {
    "duration_ms": 150,
    "agent_name": "duc",
    "topic": "architecture"
  }
}
```

### Supported Topics

| Topic | Description |
|-------|-------------|
| `architecture` | General architecture questions |
| `api_design` | API design and contracts |
| `system_design` | Distributed systems, scaling |

### Health Check

```bash
curl http://localhost:8003/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "agent_name": "duc",
  "uptime_seconds": 3600,
  "capabilities": {
    "topics": ["architecture", "api_design", "system_design"],
    "specialization": "architecture"
  }
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8003 | Service port |
| PYTHONUNBUFFERED | 1 | Enable unbuffered output |

## Response Format

Duc provides structured architecture guidance:

1. **Analysis**: Assessment of the current situation
2. **Recommendation**: Suggested approach
3. **Rationale**: Why this is the best choice
4. **Trade-offs**: Pros and cons
5. **Next Steps**: Concrete actions

## Testing

```bash
cd services/agents/duc

# Run all tests
uv run pytest

# Run contract tests only
uv run pytest tests/contract/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
services/agents/duc/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── health.py
│   │   └── invoke.py
│   └── core/
│       ├── agent.py
│       └── prompts.py
├── tests/
│   ├── conftest.py
│   ├── contract/
│   │   ├── test_health.py
│   │   └── test_invoke.py
│   └── integration/
├── Dockerfile
└── pyproject.toml
```

## Related Documentation

- [Agent Hub Service](../agent-hub.md)
- [Baron Agent](./baron.md)
- [Marie Agent](./marie.md)
