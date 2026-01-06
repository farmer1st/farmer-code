# Adding an Agent

Create a new agent service and integrate it with Agent Hub.

## Overview

Agents are stateless services that process requests using Claude SDK. Each agent has:

- A domain expertise (e.g., architecture, testing, security)
- One or more workflow types it supports
- A health endpoint for discovery

## Step 1: Create Service Structure

```bash
mkdir -p services/agents/your-agent/{src/{api,core},tests/{unit,integration,contract}}
```

Directory structure:
```
services/agents/your-agent/
├── Dockerfile
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── invoke.py
│   └── core/
│       ├── __init__.py
│       ├── agent.py
│       └── prompts.py
└── tests/
```

## Step 2: Implement the Agent

### main.py

```python
from fastapi import FastAPI
from src.api.health import router as health_router
from src.api.invoke import router as invoke_router

app = FastAPI(title="Your Agent")
app.include_router(health_router)
app.include_router(invoke_router)
```

### api/health.py

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent_name": "your-agent",
        "capabilities": {
            "workflow_types": ["your-workflow"]
        }
    }
```

### api/invoke.py

```python
from fastapi import APIRouter
from pydantic import BaseModel
from src.core.agent import YourAgent

router = APIRouter()

class InvokeRequest(BaseModel):
    workflow_type: str
    context: dict

@router.post("/invoke")
async def invoke(request: InvokeRequest):
    agent = YourAgent()
    result = await agent.process(request.workflow_type, request.context)
    return result
```

### core/agent.py

```python
import anthropic

class YourAgent:
    def __init__(self):
        self.client = anthropic.Anthropic()

    async def process(self, workflow_type: str, context: dict):
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": str(context)}]
        )
        return {
            "success": True,
            "result": response.content[0].text,
            "confidence": 85
        }
```

## Step 3: Add to Docker Compose

In `docker-compose.yml`:

```yaml
your-agent:
  build:
    context: ./services/agents/your-agent
  ports:
    - "8005:8005"  # Next available port after Marie (8004)
  environment:
    - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
```

## Step 4: Register with Agent Hub

Add to Agent Hub's agent configuration:

```python
AGENTS = {
    "your-agent": {
        "url": "http://your-agent:8005",
        "capabilities": ["your-workflow"]
    }
}
```

## Step 5: Test

```bash
# Unit tests
cd services/agents/your-agent
uv run pytest tests/

# Integration test
curl -X POST http://localhost:8005/invoke \
  -H "Content-Type: application/json" \
  -d '{"workflow_type": "your-workflow", "context": {}}'
```

## Next Steps

- See [Baron](../services/agents/baron.md) for a complete example
- Read [Testing Guide](testing.md) for test patterns
