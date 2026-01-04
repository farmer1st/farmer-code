# farmcode Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-03

## Active Technologies

- **001-github-integration-core**: Python 3.11+ + PyGithub, python-dotenv, python-jose
- **002-git-worktree-manager**: Python 3.11+ + subprocess, pathlib, Pydantic v2
- **003-orchestrator-state-machine**: Python 3.11+ + Pydantic v2, subprocess (CLI runner), JSON state persistence
- **004-knowledge-router**: Python 3.11+ + Pydantic v2, subprocess (CLI spawning), YAML routing config, JSONL logging

## Project Structure

```text
src/
  github_integration/    # GitHub API client and service
  worktree_manager/      # Git worktree management
  orchestrator/          # SDLC workflow state machine
  knowledge_router/      # AI agent Q&A routing and validation
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

### knowledge_router

AI agent Q&A routing and validation. See `src/knowledge_router/README.md` for details.

**Key exports**:
- `KnowledgeRouter` - Main facade for routing and validation
- `Question`, `Answer` - Core Q&A models
- `AnswerValidationResult`, `ValidationOutcome` - Validation results
- `EscalationRequest`, `HumanResponse`, `HumanAction` - Human escalation
- `QALogger`, `QALogEntry` - Q&A logging
- `RoutingConfig` - Configuration management

**Usage**:
```python
from knowledge_router import KnowledgeRouter, Question, QuestionTarget

router = KnowledgeRouter(config_path)
question = Question(topic="auth", suggested_target=QuestionTarget.ARCHITECT, ...)
handle = router.route_question(question)
answer = router.submit_answer(handle, question)
```

## Recent Changes

- 004-knowledge-router: Q&A routing, validation, escalation, and logging (MVP complete)
- 003-orchestrator-state-machine: State machine with phases 1-2, agent dispatch, label sync
- 002-git-worktree-manager: Git worktree management
- 001-github-integration-core: GitHub API integration

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
