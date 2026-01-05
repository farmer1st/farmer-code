# Data Model: Baron PM Agent

**Feature**: 006-baron-pm-agent
**Date**: 2026-01-05
**Purpose**: Define models for Baron agent dispatch and configuration

---

## Architecture Overview

Baron is a **Claude Agent SDK agent**, NOT a Python library. This means:

1. **Agent logic** lives in system prompts and workflow instructions
2. **Python code** is MINIMAL - only the `BaronDispatcher` class
3. **Data models** support dispatch interface and result parsing

---

## Dispatch Models (Python - src/orchestrator/models/baron_models.py)

These are the only Pydantic models in the codebase - used by `BaronDispatcher`.

### 1. SpecifyRequest

Input for dispatching Baron to run specify workflow.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `feature_description` | str | Yes | Natural language feature description |
| `feature_number` | int | None | No | Explicit feature number (auto if None) |
| `short_name` | str | None | No | Branch short name (auto if None) |

**Validation**:
- `feature_description` must be at least 10 characters
- `feature_number` must be positive if provided
- `short_name` must match pattern `^[a-z0-9-]+$` if provided

---

### 2. PlanRequest

Input for dispatching Baron to run plan workflow.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `spec_path` | Path | Yes | Path to spec.md file |
| `force_research` | bool | No | Force re-run of research phase (default: False) |

---

### 3. TasksRequest

Input for dispatching Baron to run tasks workflow.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_path` | Path | Yes | Path to plan.md file |

---

### 4. SpecifyResult

Output parsed from Baron's specify workflow response.

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether workflow completed |
| `spec_path` | Path | None | Path to created spec.md |
| `feature_id` | str | None | Feature directory name (e.g., "008-oauth2-auth") |
| `branch_name` | str | None | Git branch name |
| `error` | str | None | Error message if failed |
| `duration_seconds` | float | Time taken |

---

### 5. PlanResult

Output parsed from Baron's plan workflow response.

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether workflow completed |
| `plan_path` | Path | None | Path to created plan.md |
| `research_path` | Path | None | Path to research.md |
| `data_model_path` | Path | None | Path to data-model.md |
| `contracts_dir` | Path | None | Path to contracts/ directory |
| `quickstart_path` | Path | None | Path to quickstart.md |
| `error` | str | None | Error message if failed |
| `blocked_on_escalation` | bool | Whether waiting for human input |
| `duration_seconds` | float | Time taken |

---

### 6. TasksResult

Output parsed from Baron's tasks workflow response.

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Whether workflow completed |
| `tasks_path` | Path | None | Path to created tasks.md |
| `task_count` | int | Number of tasks generated |
| `test_count` | int | Number of test tasks (TDD) |
| `error` | str | None | Error message if failed |
| `duration_seconds` | float | Time taken |

---

## Agent Configuration Schema (.claude/agents/baron/config.yaml)

This YAML file configures Baron's agent settings. NOT a Pydantic model - just a schema definition.

```yaml
# Baron PM Agent Configuration
name: baron-pm
description: Autonomous PM agent for speckit workflows

# Model settings
model: claude-sonnet-4-20250514
max_tokens: 16000
temperature: 0.3  # Low for consistent output

# Tool access
tools:
  - Read      # Read templates, specs, constitution
  - Write     # Write artifacts, state files
  - Bash      # Run speckit bash scripts
  - Glob      # Find files
  - Grep      # Search codebase

# MCP servers
mcp_servers:
  - name: agent-hub
    command: python -m agent_hub.mcp_server

# Execution settings
timeout_seconds: 600  # 10 minutes for full cycle
retry_on_timeout: false

# Output parsing
output_format: structured_json
result_markers:
  start: "<!-- BARON_RESULT_START -->"
  end: "<!-- BARON_RESULT_END -->"
```

---

## State File Schema (specs/{feature}/.baron-state.json)

This JSON file is written by Baron (via Write tool) for workflow persistence.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BaronWorkflowState",
  "type": "object",
  "required": ["workflow_id", "feature_id", "current_phase", "created_at", "updated_at"],
  "properties": {
    "workflow_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique workflow identifier"
    },
    "feature_id": {
      "type": "string",
      "pattern": "^[0-9]{3}-[a-z0-9-]+$",
      "description": "Feature directory name"
    },
    "feature_description": {
      "type": "string",
      "minLength": 10,
      "description": "Original feature description"
    },
    "current_phase": {
      "type": "string",
      "enum": ["specify", "plan_research", "plan_design", "tasks", "complete", "blocked"],
      "description": "Current execution phase"
    },
    "completed_phases": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Phases finished successfully"
    },
    "blocked_on": {
      "type": ["string", "null"],
      "description": "Escalation ID if blocked"
    },
    "expert_questions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "topic": {"type": "string"},
          "question": {"type": "string"},
          "answer": {"type": ["string", "null"]},
          "session_id": {"type": "string"}
        }
      },
      "description": "Expert consultations made"
    },
    "artifacts_created": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Paths to created files"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

---

## Key Differences from Library Approach

| Aspect | Library Approach (WRONG) | Agent Approach (CORRECT) |
|--------|-------------------------|-------------------------|
| Workflow logic | Python methods (`run_specify()`) | Agent prompt instructions |
| Template loading | Python `template_loader.py` | Agent uses Read tool |
| State management | Python `state.py` class | Agent uses Write tool |
| Expert consultation | Python MCP client wrapper | Agent uses MCP tools directly |
| Models count | 12+ Pydantic models | 6 dispatch models only |
| Code location | `src/baron/` module | `src/orchestrator/baron_dispatch.py` |

---

## Result Parsing

Baron outputs structured results that `BaronDispatcher` parses:

```
<!-- BARON_RESULT_START -->
{
  "success": true,
  "spec_path": "specs/008-oauth2-auth/spec.md",
  "feature_id": "008-oauth2-auth",
  "branch_name": "008-oauth2-auth",
  "duration_seconds": 45.2
}
<!-- BARON_RESULT_END -->
```

The dispatcher extracts JSON between markers and validates with Pydantic models.

