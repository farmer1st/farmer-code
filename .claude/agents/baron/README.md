# Baron PM Agent

Baron is a Claude Agent SDK agent that acts as a Product Manager for the speckit workflow. It autonomously creates feature specifications, implementation plans, and task lists.

## Overview

Baron is **not** a Python library - it's a Claude agent with prompts and configuration files. The minimal Python code in `src/orchestrator/baron_dispatch.py` only handles dispatch and result parsing.

## Directory Structure

```
.claude/agents/baron/
├── README.md              # This file
├── config.yaml            # Agent configuration
├── system-prompt.md       # Baron's identity and instructions
├── workflows/
│   ├── specify.md         # Specify workflow instructions
│   ├── plan.md            # Plan workflow instructions
│   └── tasks.md           # Tasks workflow instructions
└── examples/
    ├── specify-prompt.md  # Example dispatch prompts
    ├── plan-prompt.md
    └── tasks-prompt.md
```

## Agent Configuration

### config.yaml

```yaml
name: baron
model: claude-sonnet-4-20250514
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
mcp_servers:
  - agent-hub
timeout_seconds: 600
output_format:
  result_start: "<!-- BARON_RESULT_START -->"
  result_end: "<!-- BARON_RESULT_END -->"
```

### Key Settings

- **Model**: Claude Sonnet 4 for balanced performance/cost
- **Timeout**: 10 minutes per workflow
- **MCP Servers**: agent-hub for expert consultation
- **Result Markers**: HTML comments for reliable parsing

## Workflows

### 1. Specify Workflow

Creates `spec.md` from a natural language feature description.

**Input**: Feature description string
**Output**: spec.md with all mandatory sections

```bash
# Dispatch via BaronDispatcher
dispatcher.dispatch_specify(SpecifyRequest(
    feature_description="Add user authentication with OAuth2"
))
```

### 2. Plan Workflow

Creates `plan.md` and design artifacts from `spec.md`.

**Input**: Path to spec.md
**Output**: plan.md, research.md, data-model.md, contracts/, quickstart.md

```bash
dispatcher.dispatch_plan(PlanRequest(
    spec_path=Path("specs/008-auth/spec.md")
))
```

### 3. Tasks Workflow

Creates `tasks.md` with TDD-ordered task list from `plan.md`.

**Input**: Path to plan.md
**Output**: tasks.md with test tasks before implementation

```bash
dispatcher.dispatch_tasks(TasksRequest(
    plan_path=Path("specs/008-auth/plan.md")
))
```

## System Prompt

The system prompt in `system-prompt.md` defines:

1. **Identity**: Baron as PM agent
2. **Tools**: Available tools and when to use them
3. **MCP Tools**: ask_expert, check_escalation
4. **Constitution**: Required compliance with principles
5. **Output Format**: Structured JSON between markers
6. **Error Handling**: How to report failures

## Expert Consultation

Baron can consult domain experts via Agent Hub MCP:

```json
{
  "tool": "ask_expert",
  "topic": "architecture",
  "question": "Should we use WebSockets or SSE?",
  "context": "Feature requires real-time updates"
}
```

Topics route to experts:
- `architecture` → @duc
- `product` → @veuve
- `testing` → @marie

## Result Format

All workflows output JSON between markers:

```json
<!-- BARON_RESULT_START -->
{
  "success": true,
  "spec_path": "specs/008-auth/spec.md",
  "feature_id": "008-auth",
  "branch_name": "008-auth",
  "duration_seconds": 45.2
}
<!-- BARON_RESULT_END -->
```

## Python Integration

### BaronDispatcher

```python
from orchestrator.baron_dispatch import BaronDispatcher
from orchestrator.baron_models import SpecifyRequest

# Create dispatcher
dispatcher = BaronDispatcher(runner=ClaudeCLIRunner())

# Dispatch specify workflow
result = dispatcher.dispatch_specify(SpecifyRequest(
    feature_description="Add OAuth2 authentication"
))

print(f"Spec created: {result.spec_path}")
```

### Models

- `SpecifyRequest` / `SpecifyResult`
- `PlanRequest` / `PlanResult`
- `TasksRequest` / `TasksResult`

### Exceptions

- `DispatchError`: Agent execution failed
- `ParseError`: Could not parse result

## Testing

```bash
# Unit tests (mock runner)
pytest tests/unit/orchestrator/test_baron_models.py
pytest tests/unit/orchestrator/test_baron_dispatch.py

# Integration tests (mock runner)
pytest tests/integration/baron/ -v

# Real agent tests (manual)
pytest tests/integration/baron/ -m slow -v
```

## User Journeys

| Journey | Description | Status |
|---------|-------------|--------|
| BRN-001 | Create Specification | ✅ Implemented |
| BRN-002 | Generate Plan | ✅ Implemented |
| BRN-003 | Generate Tasks | ✅ Implemented |
| BRN-004 | Handle Escalations | 📋 Planned |
| BRN-005 | Expert Consultation | 📋 Planned |
| BRN-006 | Constitution Compliance | 📋 Planned |

## Related Documentation

- [Spec](../../specs/006-baron-pm-agent/spec.md)
- [Plan](../../specs/006-baron-pm-agent/plan.md)
- [Tasks](../../specs/006-baron-pm-agent/tasks.md)
- [Dispatcher Code](../../src/orchestrator/baron_dispatch.py)
- [Models Code](../../src/orchestrator/baron_models.py)
