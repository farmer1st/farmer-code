# Farmer Code

AI-orchestrated software development lifecycle (SDLC) automation system.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Verify services are running
curl http://localhost:8000/health  # Orchestrator
curl http://localhost:8001/health  # Agent Hub
curl http://localhost:8002/health  # Baron
curl http://localhost:8003/health  # Duc
curl http://localhost:8004/health  # Marie
```

### Local Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run a specific service
cd services/agent-hub
uv run uvicorn src.main:app --port 8001 --reload
```

## Services Architecture

| Service | Port | Description |
|---------|------|-------------|
| Orchestrator | 8000 | Workflow state machine |
| Agent Hub | 8001 | Agent routing, sessions, escalation |
| Baron | 8002 | PM Agent (specs, plans, tasks) |
| Duc | 8003 | Architecture Expert |
| Marie | 8004 | Testing Expert |

## Documentation

- [Full Documentation](./docs/README.md)
- [Services Architecture](./docs/services/README.md)
- [Getting Started](./docs/getting-started/README.md)
- [User Journeys](./docs/user-journeys/JOURNEYS.md)

## Project Structure

```
farmcode/
├── services/           # Microservices (Feature 008)
│   ├── orchestrator/   # Workflow state machine
│   ├── agent-hub/      # Agent routing & sessions
│   └── agents/         # Baron, Duc, Marie
├── src/                # Legacy modules
│   ├── orchestrator/
│   ├── agent_hub/
│   ├── github_integration/
│   └── worktree_manager/
├── docs/               # Documentation
├── specs/              # Feature specifications
└── tests/              # E2E tests
```

## License

Proprietary - Farmer1st
