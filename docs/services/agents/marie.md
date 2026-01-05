# Marie Agent Service

Marie is the **Testing Expert** agent for Farmer Code. It provides guidance on test strategy, edge case identification, and QA best practices.

## Overview

Marie specializes in:
- Test strategy and planning
- Test case generation
- Edge case identification
- TDD guidance
- QA review and assessment

## Quick Start

### Running Locally

```bash
cd services/agents/marie

# Install dependencies
uv sync

# Run the service
uv run uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
```

### Running with Docker

```bash
# Build image
docker build -t marie:latest .

# Run container
docker run -p 8004:8004 marie:latest
```

### API Documentation

Once running, visit:
- OpenAPI docs: http://localhost:8004/docs
- ReDoc: http://localhost:8004/redoc

## API Reference

### Invoke Agent

```bash
curl -X POST http://localhost:8004/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "testing",
    "context": {
      "question": "How should I test this API endpoint?"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "result": {
    "output": "# Testing Guidance\n\n...",
    "answer": "Based on your requirements..."
  },
  "confidence": 85,
  "metadata": {
    "duration_ms": 150,
    "agent_name": "marie",
    "topic": "testing"
  }
}
```

### Supported Topics

| Topic | Description |
|-------|-------------|
| `testing` | General testing strategy |
| `edge_cases` | Edge case identification |
| `qa_review` | QA review and assessment |

### Health Check

```bash
curl http://localhost:8004/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "agent_name": "marie",
  "uptime_seconds": 3600,
  "capabilities": {
    "topics": ["testing", "edge_cases", "qa_review"],
    "specialization": "testing"
  }
}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8004 | Service port |
| PYTHONUNBUFFERED | 1 | Enable unbuffered output |

## Response Format

Marie provides structured testing guidance:

1. **Analysis**: Assessment of testing requirements
2. **Strategy**: Recommended testing approach
3. **Test Cases**: Specific tests to write
4. **Edge Cases**: Important edge cases to cover
5. **Tools**: Recommended testing tools

## Testing

```bash
cd services/agents/marie

# Run all tests
uv run pytest

# Run contract tests only
uv run pytest tests/contract/ -v

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
services/agents/marie/
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
- [Duc Agent](./duc.md)
