# Baron Agent Service

Baron is the **Product Management (PM) Agent** for Farmer Code. It drives the speckit workflow for feature specification, planning, and task generation.

## Overview

Baron specializes in:
- Feature specification creation
- Implementation planning
- Task list generation
- Requirements clarification
- Stakeholder communication

## Quick Start

### Running Locally

```bash
cd services/agents/baron

# Install dependencies
uv sync

# Run the service
uv run uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

### Running with Docker

```bash
# Build image
docker build -t baron:latest .

# Run container
docker run -p 8002:8002 -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY baron:latest
```

### API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## API Reference

### Invoke Agent

```bash
curl -X POST http://localhost:8002/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "specification",
    "context": {
      "question": "Create a spec for user authentication"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "output": "# Feature Specification\n\n...",
    "answer": "I've created a specification..."
  },
  "confidence": 90,
  "metadata": {
    "duration_ms": 2500,
    "agent_name": "baron",
    "topic": "specification"
  }
}
```

### Supported Topics

| Topic | Description |
|-------|-------------|
| `specification` | Feature specification creation |
| `planning` | Implementation planning |
| `tasks` | Task list generation |

### Health Check

```bash
curl http://localhost:8002/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "agent_name": "baron",
  "uptime_seconds": 3600,
  "capabilities": {
    "topics": ["specification", "planning", "tasks"],
    "specialization": "product_management"
  }
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8002 | Service port |
| ANTHROPIC_API_KEY | - | Claude API key (required for LLM calls) |
| PYTHONUNBUFFERED | 1 | Enable unbuffered output |

## Response Format

Baron provides structured PM outputs:

1. **Analysis**: Understanding of the request
2. **Deliverable**: The specification, plan, or task list
3. **Rationale**: Why decisions were made
4. **Next Steps**: Recommended follow-up actions
5. **Questions**: Clarifications needed (if any)

## Testing

```bash
cd services/agents/baron

# Run all tests
uv run pytest

# Run contract tests only
uv run pytest tests/contract/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
services/agents/baron/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── health.py
│   │   └── invoke.py
│   ├── core/
│   │   ├── agent.py
│   │   └── prompts.py
│   └── tools/
│       └── speckit.py
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

- [Agent Hub Service](../../agent-hub/README.md)
- [Duc Agent](../duc/README.md)
- [Marie Agent](../marie/README.md)
- [Baron Documentation](../../../docs/services/agents/baron.md)
