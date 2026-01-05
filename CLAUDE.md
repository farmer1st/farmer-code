# Farmer Code Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-03

## Active Technologies
- N/A (text changes only) + grep/sed for search and replace (007-farmer-code-rebrand)
- Python 3.11+ + Claude CLI (via subprocess), Agent Hub (MCP server), Pydantic v2 (006-baron-pm-agent)
- File-based (specs/ directory structure, JSON state files) (006-baron-pm-agent)
- Python 3.11+ + FastAPI, Claude Code SDK (claude-code-sdk), Pydantic v2, httpx, SQLAlchemy (008-services-architecture)
- SQLite (local), JSONL for audit logs (008-services-architecture)

- **001-github-integration-core**: Python 3.11+ + PyGithub, python-dotenv, python-jose
- **002-git-worktree-manager**: Python 3.11+ + subprocess (git commands), pathlib, Pydantic v2
- **003-orchestrator-state-machine**: Python 3.11+ + Pydantic v2, subprocess (Claude CLI), JSON state persistence
- **004-knowledge-router**: Python 3.11+ + Pydantic v2, subprocess (Claude CLI), YAML routing config, JSONL logging
- **005-agent-hub-refactor**: Python 3.11+ + Pydantic v2, subprocess (Claude CLI), MCP SDK (optional server), in-memory sessions, JSONL logging

## Project Structure

```text
src/
  github_integration/    # GitHub API client and service
  worktree_manager/      # Git worktree management
  orchestrator/          # SDLC workflow state machine
  agent_hub/             # Central coordination for agent interactions
tests/
  unit/                  # Unit tests
  integration/           # Integration tests
  contract/              # Contract tests
  e2e/                   # End-to-end tests
```

## Commands

```bash
# Run tests
uv run pytest

# Run linting (must pass BOTH for CI)
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Run type checking
uv run mypy src/ --strict

# Auto-fix lint issues
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

## Code Style

Python 3.11+: Follow standard conventions with Google-style docstrings

## Modules

### orchestrator

State machine orchestration for SDLC Phases 1-2. See `src/orchestrator/README.md` for details.

**Key exports**:
- `OrchestratorService` - Main facade
- `WorkflowState` - State enum (IDLE, PHASE_1, PHASE_2, GATE_1, DONE)
- `Phase1Request`, `Phase2Config` - Configuration models
- `AgentRunner`, `ClaudeCLIRunner` - Agent dispatch

**Usage**:
```python
from orchestrator import OrchestratorService, Phase1Request

orchestrator = OrchestratorService(repo_path, github_service, worktree_service)
result = orchestrator.execute_phase_1(Phase1Request(feature_description="..."))
```

### agent_hub

Central coordination layer for agent interactions. See `src/agent_hub/README.md` for details.

**Key exports**:
- `AgentHub` - Main facade for routing, sessions, validation
- `HubResponse`, `ResponseStatus` - Response with status
- `Session`, `Message`, `MessageRole` - Session management
- `EscalationRequest`, `HumanAction` - Human escalation
- `RoutingConfig`, `ConfigLoader` - Configuration
- MCP server via `python -m agent_hub.mcp_server`

**Usage**:
```python
from agent_hub import AgentHub, ConfigLoader

config = ConfigLoader.load_from_file("config/routing.yaml")
hub = AgentHub(config, log_dir="logs/qa")

response = hub.ask_expert(
    topic="architecture",
    question="What auth method should we use?",
    feature_id="005-auth"
)

if response.status.value == "resolved":
    print(response.answer)
else:
    # Low confidence - check escalation
    escalation = hub.check_escalation(response.escalation_id)
```

## Recent Changes
- 008-services-architecture: Added Python 3.11+ + FastAPI, Claude Code SDK (claude-code-sdk), Pydantic v2, httpx, SQLAlchemy
- 008-services-architecture: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]
- 006-baron-pm-agent: Added Python 3.11+ + Claude CLI (via subprocess), Agent Hub (MCP server), Pydantic v2

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
