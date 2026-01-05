# Orchestrator Module

State machine orchestration for SDLC Phases 1-2 workflow automation.

## Overview

The Orchestrator module provides automated workflow management for the SDLC process, handling:

- **State Machine**: Track workflow state through lifecycle phases (IDLE → PHASE_1 → PHASE_2 → GATE_1 → DONE)
- **Phase 1 Execution**: Create GitHub issue, branch, worktree, and .plans structure
- **Phase 2 Execution**: Dispatch AI agents and poll for completion signals
- **Label Synchronization**: Keep GitHub labels in sync with workflow state

## Quick Start

```python
from pathlib import Path
from github_integration import GitHubService
from worktree_manager import WorktreeService
from orchestrator import OrchestratorService, Phase1Request

# Initialize services
github = GitHubService.from_env()
worktree = WorktreeService(Path("."))
orchestrator = OrchestratorService(Path("."), github, worktree)

# Execute Phase 1
result = orchestrator.execute_phase_1(
    Phase1Request(
        feature_description="Add OAuth2 authentication",
        labels=["enhancement"],
    )
)

print(f"Success: {result.success}")
print(f"Artifacts: {result.artifacts_created}")
```

## Architecture

### Core Components

| Component | Purpose |
|-----------|---------|
| `OrchestratorService` | Main facade coordinating all operations |
| `StateMachine` | Manages state transitions and persistence |
| `PhaseExecutor` | Executes Phase 1 and Phase 2 steps |
| `SignalPoller` | Polls GitHub for completion signals |
| `LabelSync` | Synchronizes labels with workflow state |
| `AgentRunner` | Protocol for pluggable agent execution |

### State Flow

```
IDLE ──phase_1_start──► PHASE_1 ──phase_1_complete──► PHASE_2
                                                        │
                    DONE ◄──approval_received── GATE_1 ◄─phase_2_complete──
```

### Agent Runner Architecture

The module uses a pluggable runner architecture for AI agent dispatch:

```python
from orchestrator import AgentRunner, ClaudeCLIRunner, get_runner

# Direct instantiation
runner = ClaudeCLIRunner()
if runner.is_available():
    result = runner.dispatch(config, context)

# Factory function (recommended)
runner = get_runner(agent_config)  # Auto-selects based on provider
```

Supported providers:
- `AgentProvider.CLAUDE` - Claude CLI (`ClaudeCLIRunner`)
- `AgentProvider.GEMINI` - Gemini CLI (not yet implemented)
- `AgentProvider.CODEX` - Codex CLI (not yet implemented)

## API Reference

### OrchestratorService

```python
class OrchestratorService:
    def __init__(self, repo_path, github_service, worktree_service, agent_runner=None): ...
    def get_state(self, issue_number) -> OrchestratorState | None: ...
    def transition(self, issue_number, event) -> StateTransition: ...
    def execute_phase_1(self, request: Phase1Request) -> PhaseResult: ...
    def execute_phase_2(self, issue_number, config: Phase2Config) -> PhaseResult: ...
    def poll_for_signal(self, issue_number, signal_type, ...) -> PollResult: ...
    def sync_labels(self, issue_number) -> OperationResult: ...
```

### Models

| Model | Description |
|-------|-------------|
| `WorkflowState` | Enum: IDLE, PHASE_1, PHASE_2, GATE_1, DONE |
| `OrchestratorState` | Full workflow state for an issue |
| `Phase1Request` | Configuration for Phase 1 execution |
| `Phase2Config` | Configuration for Phase 2 (agent + polling) |
| `AgentConfig` | Agent configuration (provider, model, role, etc.) |
| `PhaseResult` | Result of phase execution |
| `PollResult` | Result of signal polling |

### Errors

| Error | When Raised |
|-------|-------------|
| `WorkflowNotFoundError` | No workflow exists for issue |
| `InvalidStateTransition` | Transition not allowed from current state |
| `IssueCreationError` | GitHub issue creation failed |
| `BranchCreationError` | Branch creation failed |
| `WorktreeCreationError` | Worktree creation failed |
| `AgentDispatchError` | Agent failed to dispatch |
| `AgentTimeoutError` | Agent execution timed out |
| `PollTimeoutError` | Signal polling timed out |

## State Persistence

Workflow state is persisted to JSON files:

```
.plans/{issue_number}/state.json
```

Example state file:
```json
{
  "issue_number": 123,
  "current_state": "phase_2",
  "feature_name": "oauth2-auth",
  "branch_name": "123-oauth2-auth",
  "worktree_path": "/path/to/worktree",
  "phase1_steps": ["issue", "branch", "worktree", "plans"],
  "phase2_agent_complete": false,
  "phase2_human_approved": false,
  "history": [...],
  "created_at": "2026-01-03T10:00:00Z",
  "updated_at": "2026-01-03T10:00:30Z"
}
```

## Signal Detection

The module polls for two types of signals in GitHub issue comments:

1. **Agent Complete**: Comment containing `✅` emoji
2. **Human Approval**: Comment containing "approved" (case-insensitive)

## Label Mapping

| State | GitHub Label |
|-------|--------------|
| IDLE | `status:new` |
| PHASE_1 | `status:phase-1` |
| PHASE_2 | `status:phase-2` |
| GATE_1 | `status:awaiting-approval` |
| DONE | `status:done` |

## Testing

```bash
# Run all orchestrator tests
uv run pytest tests/unit/test_state_machine.py tests/unit/test_phase_executor.py \
    tests/unit/test_agent_runner.py tests/unit/test_polling.py tests/unit/test_label_sync.py \
    tests/contract/test_orchestrator_contract.py tests/integration/test_orchestrator_integration.py -v

# Run with coverage
uv run pytest src/orchestrator/ --cov=src/orchestrator --cov-report=html
```

## BaronDispatcher

The module includes `BaronDispatcher` for dispatching the Baron PM agent:

```python
from orchestrator.baron_dispatch import BaronDispatcher
from orchestrator.baron_models import SpecifyRequest, PlanRequest, TasksRequest

# Create dispatcher
dispatcher = BaronDispatcher(runner=ClaudeCLIRunner())

# Dispatch specify workflow (create spec.md)
result = dispatcher.dispatch_specify(SpecifyRequest(
    feature_description="Add OAuth2 authentication"
))
print(f"Spec: {result.spec_path}")

# Dispatch plan workflow (create plan.md and artifacts)
result = dispatcher.dispatch_plan(PlanRequest(
    spec_path=Path("specs/008-auth/spec.md")
))
print(f"Plan: {result.plan_path}")

# Dispatch tasks workflow (create tasks.md)
result = dispatcher.dispatch_tasks(TasksRequest(
    plan_path=Path("specs/008-auth/plan.md")
))
print(f"Tasks: {result.tasks_path}, Count: {result.task_count}")
```

### Baron Models

| Model | Description |
|-------|-------------|
| `SpecifyRequest` | Request to create spec.md from description |
| `SpecifyResult` | Result with spec_path, feature_id, branch_name |
| `PlanRequest` | Request to create plan.md from spec.md |
| `PlanResult` | Result with plan_path, research_path, data_model_path |
| `TasksRequest` | Request to create tasks.md from plan.md |
| `TasksResult` | Result with tasks_path, task_count, test_count |

### Baron Errors

| Error | When Raised |
|-------|-------------|
| `DispatchError` | Agent execution failed |
| `ParseError` | Could not parse result markers |

See `.claude/agents/baron/README.md` for full Baron documentation.

## Dependencies

- `github_integration` - GitHub API operations
- `worktree_manager` - Git worktree management
- `pydantic` - Data validation and serialization
