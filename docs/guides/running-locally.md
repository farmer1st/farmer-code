# Running Locally

Run all Farmer Code services on your local machine.

## Prerequisites

- Docker and Docker Compose
- `.env` file with required variables (copy from `.env.example`)

## Quick Start

### 1. Copy Environment File

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Start All Services

```bash
docker-compose up
```

This starts:
- Orchestrator on http://localhost:8000
- Agent Hub on http://localhost:8001
- Baron on http://localhost:8002
- Duc on http://localhost:8003
- Marie on http://localhost:8004

### 3. Verify Services

```bash
# Check all health endpoints
curl http://localhost:8000/health  # Orchestrator
curl http://localhost:8001/health  # Agent Hub
curl http://localhost:8002/health  # Baron
```

## Development Mode

For development with hot-reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

This mounts local source directories so changes are reflected immediately.

## Running Individual Services

To run services outside Docker:

```bash
# Terminal 1: Orchestrator
cd services/orchestrator
uv run uvicorn src.main:app --port 8000 --reload

# Terminal 2: Agent Hub
cd services/agent-hub
uv run uvicorn src.main:app --port 8001 --reload

# Terminal 3: Baron
cd services/agents/baron
uv run uvicorn src.main:app --port 8002 --reload
```

## Troubleshooting

### Port Already in Use

```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Services Can't Connect

Ensure all services are on the same Docker network:

```bash
docker network ls
docker-compose down && docker-compose up
```

## Next Steps

- [Testing Guide](testing.md) - Run the test suite
- [Adding an Agent](adding-an-agent.md) - Create a new agent
