# Services Architecture

> **Status**: Implemented (Feature 008)

This directory contains documentation for the Farmer Code services architecture.

## Overview

The services architecture refactors Farmer Code from a module-based Python architecture to independent services communicating via REST APIs.

## Services

| Service | Port | Description |
|---------|------|-------------|
| [Orchestrator](./orchestrator.md) | 8000 | Workflow state machine and phase execution |
| [Agent Hub](./agent-hub.md) | 8001 | Agent routing, session management, escalation |
| [Baron](./agents/baron.md) | 8002 | SpecKit workflow agent (specify, plan, tasks, implement) |
| [Duc](./agents/duc.md) | 8003 | Architecture and design expert |
| [Marie](./agents/marie.md) | 8004 | Testing and QA expert |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Orchestrator  │────▶│   Agent Hub     │────▶│  Agent Services │
│   (workflows)   │     │  (routing)      │     │ (Baron/Duc/...)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   ┌─────────┐            ┌─────────┐            ┌─────────┐
   │ SQLite  │            │ SQLite  │            │Claude SDK│
   └─────────┘            └─────────┘            └─────────┘
```

## Quick Start

```bash
# Start all services
docker-compose up -d

# Verify health
curl http://localhost:8000/health  # Orchestrator
curl http://localhost:8001/health  # Agent Hub
curl http://localhost:8002/health  # Baron
curl http://localhost:8003/health  # Duc
curl http://localhost:8004/health  # Marie
```

## Related Documentation

- [System Overview](../architecture/system-overview.md)
- [Services Communication](../architecture/services-communication.md)
- [Environment Variables](../configuration/environment-variables.md)
- [Docker Compose Guide](../configuration/docker-compose.md)

## User Journeys

| Journey | Description |
|---------|-------------|
| [SVC-001](../user-journeys/SVC-001-orchestrator-workflow.md) | Orchestrator Workflow Execution |
| [SVC-002](../user-journeys/SVC-002-agent-consultation.md) | Expert Agent Consultation |
| [SVC-003](../user-journeys/SVC-003-human-escalation.md) | Human Review Escalation |
| [SVC-004](../user-journeys/SVC-004-multi-turn-session.md) | Multi-Turn Session |
| [SVC-005](../user-journeys/SVC-005-stateless-agent.md) | Stateless Agent Invocation |
| [SVC-006](../user-journeys/SVC-006-local-dev-setup.md) | Local Development Setup |
| [SVC-007](../user-journeys/SVC-007-audit-log-query.md) | Audit Log Query |
