# Research: Services Architecture Refactor

**Feature**: 008-services-architecture
**Date**: 2026-01-05
**Status**: Complete

## Research Summary

### 1. Current Architecture Analysis

**Decision**: Refactor from monolithic modules to independent services

**Rationale**: Current architecture has tight coupling at runtime:
- CLI subprocess for agent invocation (blocking, no async)
- File-based state persistence (not queryable, no transactions)
- Direct service dependencies (OrchestratorService imports GitHubService, WorktreeService)
- No HTTP layer exists

**Alternatives Considered**:
- Keep modules, add HTTP layer on top → Rejected: Still tightly coupled, harder to scale
- Full microservices with message queue → Rejected: Over-engineered for current scale
- Hybrid approach with shared process → Rejected: Doesn't achieve independent deployment

### 2. Agent Invocation Strategy

**Decision**: Use Claude Code SDK `query()` function for agent invocation

**Rationale**:
- SDK provides async/await support for concurrent agent dispatch
- Session management built into SDK (via session IDs)
- MCP servers, custom tools, and skills all work together in SDK
- `ClaudeAgentOptions` supports permission modes for unattended service execution

**Implementation Pattern**:
```python
from claude_code_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Generate specification for...",
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Glob", "Grep"],
        permission_mode="acceptEdits",
        mcp_servers={"agent_hub": agent_hub_server},
        setting_sources=["user", "project"]  # Enable skills
    )
):
    # Process streaming response
```

**Alternatives Considered**:
- Keep CLI subprocess → Rejected: Blocking, no proper timeout handling, no streaming
- Use MCP protocol only → Rejected: MCP is for tools, not agent orchestration
- Direct Claude API calls → Rejected: Loses Claude Code tooling (Read, Write, etc.)

### 3. Service Communication Pattern

**Decision**: REST APIs via FastAPI

**Rationale**:
- Aligns with constitution (FastAPI in technology stack)
- OpenAPI spec auto-generation
- Async support built-in
- Pydantic integration for request/response validation
- Same network deployment (latency not a concern)

**Service Endpoints**:
- Orchestrator: `/workflows`, `/workflows/{id}`, `/workflows/{id}/advance`
- Agent Hub: `/invoke/{agent}`, `/ask/{topic}`, `/escalations/{id}`, `/sessions`
- Agent Services: `/invoke`, `/health`

**Alternatives Considered**:
- gRPC → Rejected: Adds complexity, not needed for same-network deployment
- Message queue (RabbitMQ/Redis) → Rejected: Over-engineered for current scale
- WebSockets → Rejected: REST sufficient for request-response patterns

### 4. State Persistence Strategy

**Decision**: SQLite for local development, with abstraction for future Redis/PostgreSQL

**Rationale**:
- SQLite requires no external services (local-first per constitution)
- Transactions for multi-step operations
- Queryable (vs file-based JSON)
- Can swap to PostgreSQL for cloud deployment

**Persistence Needs**:
- Sessions: `sessions` table (id, agent_id, feature_id, status, created_at, updated_at)
- Escalations: `escalations` table (id, question_id, status, tentative_answer, human_response)
- Workflow State: `workflow_states` table (id, issue_number, current_state, history)
- Audit Logs: JSONL files (append-only, no need for database)

**Alternatives Considered**:
- Keep file-based JSON → Rejected: No transactions, race conditions, not queryable
- Redis only → Rejected: Requires external service for local dev
- In-memory only → Rejected: Loses state on restart

### 5. Agent Service Design

**Decision**: Stateless services with MCP + tools + skills support

**Rationale**:
- SDK confirmed to support all three simultaneously:
  - MCP servers: External tools via `mcp_servers` dict
  - Custom tools: In-process via `create_sdk_mcp_server()` + `@tool` decorator
  - Skills: Filesystem artifacts via `setting_sources=["user", "project"]`
- Stateless enables horizontal scaling
- All context passed in request

**Agent Service Pattern**:
```python
# Each agent service (Baron, Duc, Marie) follows this pattern
@app.post("/invoke")
async def invoke(request: InvokeRequest) -> InvokeResponse:
    options = ClaudeAgentOptions(
        allowed_tools=AGENT_ALLOWED_TOOLS,
        mcp_servers={"shared": shared_tools_server},
        setting_sources=["user", "project"],
        permission_mode="acceptEdits"
    )

    result = []
    async for message in query(prompt=build_prompt(request), options=options):
        result.append(message)

    return InvokeResponse(result=parse_result(result))
```

### 6. Docker Compose Configuration

**Decision**: Multi-service docker-compose with shared network

**Rationale**:
- Single command startup per success criteria
- Service isolation with shared networking
- Volume mounts for local development
- Easy to add new agent services

**Services**:
```yaml
services:
  orchestrator:
    build: ./services/orchestrator
    ports: ["8001:8000"]
    environment:
      - AGENT_HUB_URL=http://agent-hub:8000
    depends_on: [agent-hub]

  agent-hub:
    build: ./services/agent-hub
    ports: ["8002:8000"]
    environment:
      - BARON_URL=http://baron:8000
      - DUC_URL=http://duc:8000
    volumes:
      - ./data/sessions.db:/app/data/sessions.db

  baron:
    build: ./services/agents/baron
    ports: ["8010:8000"]
```

### 7. Migration Strategy

**Decision**: Incremental migration with parallel operation

**Rationale**:
- Preserve existing functionality during transition
- Tests continue to pass throughout migration
- Can rollback if issues arise

**Migration Phases**:
1. Create shared contracts package (models, schemas)
2. Build Agent Hub Service (wrap existing hub.py)
3. Build first Agent Service (Baron)
4. Build Orchestrator Service
5. Add remaining Agent Services
6. Deprecate old module imports

### 8. Shared Contracts Package

**Decision**: `packages/contracts/` with Pydantic models and OpenAPI schemas

**Rationale**:
- Single source of truth for API contracts
- Type safety across services
- OpenAPI generation from Pydantic models

**Package Structure**:
```
packages/contracts/
├── pyproject.toml
├── src/contracts/
│   ├── __init__.py
│   ├── models/           # Pydantic models
│   │   ├── agent.py      # AgentRequest, AgentResponse
│   │   ├── session.py    # Session, Message
│   │   ├── escalation.py # EscalationRequest, HumanAction
│   │   └── workflow.py   # WorkflowState, Phase
│   ├── schemas/          # OpenAPI schemas
│   │   ├── orchestrator.yaml
│   │   ├── agent_hub.yaml
│   │   └── agent.yaml
│   └── clients/          # Generated HTTP clients
│       ├── orchestrator.py
│       ├── agent_hub.py
│       └── agent.py
```

## Unresolved Questions

None - all technical decisions have been made based on:
- Claude Code SDK documentation (MCP + tools + skills confirmed)
- Constitution technology stack (FastAPI, SQLite, Docker)
- Spec requirements (REST APIs, non-blocking escalation, stateless agents)

## References

- Claude Code SDK documentation: query(), ClaudeAgentOptions, MCP servers
- Existing codebase: src/agent_hub/, src/orchestrator/
- Constitution v1.7.0: Technology Stack Standards, Thin Client Architecture
