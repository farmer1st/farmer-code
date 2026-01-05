# Research: Agent Hub Refactor

**Feature**: 005-agent-hub-refactor
**Date**: 2026-01-05

## Research Questions

### R1: Module Renaming Strategy

**Question**: What is the best approach for renaming the module while maintaining backward compatibility during transition?

**Decision**: Direct rename with git mv

**Rationale**:
- Git mv preserves file history
- All imports updated in a single commit
- No need for backward compatibility shims (internal module)
- Cleaner than creating aliases

**Alternatives Considered**:
- Deprecation period with both modules: Rejected - unnecessary complexity for internal module
- Symbolic links: Rejected - doesn't work well with Python imports
- Import aliases in __init__.py: Rejected - adds maintenance burden

### R2: Session Storage Approach

**Question**: How should session state be stored for multi-turn conversations?

**Decision**: In-memory dictionary with UUID keys

**Rationale**:
- Simple and fast for local development
- No external dependencies
- Sufficient for single-user, 5-10 concurrent sessions
- Easy to replace with persistent storage later if needed

**Alternatives Considered**:
- SQLite: Rejected - overkill for local development, adds complexity
- Redis: Rejected - external dependency, not needed for single-user
- File-based JSON: Rejected - slower, file locking issues

**Implementation**:
```python
class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self, agent_id: str, feature_id: str) -> Session:
        session = Session(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            feature_id=feature_id,
            messages=[],
            created_at=datetime.utcnow(),
        )
        self._sessions[session.id] = session
        return session
```

### R3: MCP Server Implementation

**Question**: How should the Agent Hub expose tools via MCP?

**Decision**: Standalone MCP server module using mcp-python library

**Rationale**:
- Follows MCP protocol standards
- Can be started independently or embedded
- Clean separation between Hub logic and MCP transport

**Alternatives Considered**:
- FastAPI endpoints: Rejected - MCP is the standard for Claude tools
- Direct function calls: Rejected - doesn't work with Agent SDK

**Implementation Pattern**:
```python
# mcp_server.py
from mcp import Server, Tool

server = Server("agent-hub")

@server.tool()
async def ask_expert(
    topic: str,
    question: str,
    context: str = "",
    session_id: str | None = None,
) -> dict:
    """Route question to appropriate expert agent."""
    hub = get_hub()
    response = await hub.ask_expert(topic, question, context, session_id)
    return response.model_dump()
```

### R4: Class Renaming Mapping

**Question**: What is the complete mapping of old to new class/module names?

**Decision**: Clear 1:1 mapping with improved naming

| Old | New | Notes |
|-----|-----|-------|
| `knowledge_router/` | `agent_hub/` | Module directory |
| `router.py` | `hub.py` | Main service file |
| `KnowledgeRouterService` | `AgentHub` | Main class |
| `dispatcher.py` | `router.py` | Agent routing logic |
| `AgentDispatcher` | `AgentRouter` | Routing class |

### R5: Test Migration Approach

**Question**: How should existing tests be migrated?

**Decision**: Rename directories and update imports in a single commit

**Rationale**:
- Atomic change reduces confusion
- Git history preserved with git mv
- CI validates all tests pass after migration

**Steps**:
1. `git mv tests/unit/knowledge_router tests/unit/agent_hub`
2. `git mv tests/integration/knowledge_router tests/integration/agent_hub`
3. `git mv tests/contract/knowledge_router tests/contract/agent_hub`
4. `git mv tests/e2e/knowledge_router tests/e2e/agent_hub`
5. Find/replace imports in all test files
6. Run full test suite to validate

## Dependencies Research

### Claude Agent SDK MCP Integration

**Finding**: The Claude Agent SDK supports MCP servers via the `mcp_servers` configuration option.

```python
from claude_code_sdk import query, ClaudeCodeOptions

async for event in query(
    prompt="...",
    options=ClaudeCodeOptions(
        mcp_servers={
            "agent-hub": {
                "command": "python",
                "args": ["-m", "agent_hub.mcp_server"]
            }
        }
    )
):
    ...
```

**Action**: MCP server will be implemented as a standalone module that can be run as `python -m agent_hub.mcp_server`

## Conclusion

All research questions resolved. No NEEDS CLARIFICATION items remaining.

**Ready for Phase 1: Design & Contracts**
