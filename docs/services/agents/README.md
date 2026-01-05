# Agent Services

> **Status**: In Development (Feature 008)

This directory contains documentation for individual agent services.

## Overview

Agent services are stateless HTTP services that use the Claude Code SDK to process requests. Each agent has specialized capabilities and system prompts for its domain.

## Available Agents

| Agent | Port | Domain | Workflow Types |
|-------|------|--------|----------------|
| [Baron](./baron.md) | 8010 | SpecKit PM | specify, plan, tasks, implement |
| [Duc](./duc.md) | 8011 | Architecture | architecture, design, api |
| [Marie](./marie.md) | 8012 | Testing/QA | test, qa, edge_cases |

## Common API

All agent services implement the [Agent Service API](../../../specs/008-services-architecture/contracts/agent-service.yaml):

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/invoke` | POST | Process a request |
| `/health` | GET | Health check with capabilities |

### Request Format

```json
{
  "workflow_type": "specify",
  "context": {
    "feature_description": "Add user authentication"
  },
  "parameters": {
    "priority": "P1"
  }
}
```

### Response Format

```json
{
  "success": true,
  "result": {
    "output": "...",
    "files_created": ["specs/001-auth/spec.md"]
  },
  "confidence": 92,
  "metadata": {
    "duration_ms": 15234,
    "model_used": "claude-3-5-sonnet-20241022"
  }
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Service                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  FastAPI    │───▶│   Core      │───▶│ Claude SDK  │     │
│  │  Endpoints  │    │   Agent     │    │   Query     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                   │            │
│         ▼                  ▼                   ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Pydantic  │    │   System    │    │    Tools    │     │
│  │   Models    │    │   Prompts   │    │   & Skills  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Stateless Design

Agent services are stateless by design:

- **All context passed in request**: No server-side session storage
- **Horizontally scalable**: Multiple instances can run in parallel
- **Restartable**: No state lost on service restart
- **Testable**: Each request is independent

## Adding a New Agent

1. Create directory: `services/agents/{agent_name}/`
2. Copy structure from `baron/`
3. Customize `core/prompts.py` for agent domain
4. Update `docker-compose.yml` to include new service
5. Update Agent Hub routing configuration

## Related Documentation

- [Services Overview](../README.md)
- [Agent Hub](../agent-hub.md) - Routes requests to agents
- [Orchestrator](../orchestrator.md) - Invokes agents via Agent Hub
