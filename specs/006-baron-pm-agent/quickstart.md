# Quickstart: Baron PM Agent

**Purpose**: End-to-end validation guide for testing Baron PM Agent
**Audience**: Developers implementing or testing the Baron module
**Prerequisites**: Claude CLI installed, repository cloned, Agent Hub available

---

## Architecture Overview

Baron is a **Claude Agent SDK agent**, NOT a Python library. Testing involves:
1. **Agent configuration files** in `.claude/agents/baron/`
2. **BaronDispatcher class** in `src/orchestrator/baron_dispatch.py`
3. **Agent execution** via Claude CLI with MCP

---

## Setup

### 1. Environment

```bash
# Verify Claude CLI is installed
claude --version

# Verify repository structure
ls .specify/templates/
# Should show: spec-template.md, plan-template.md, tasks-template.md

# Verify constitution exists
cat .specify/memory/constitution.md | head -5

# Verify Agent Hub is available
python -c "from agent_hub import MCPServer; print('OK')"
```

### 2. Dependencies

```bash
# Install from repo root
uv pip install -e .

# Verify orchestrator with baron dispatch
python -c "from orchestrator.baron_dispatch import BaronDispatcher; print('OK')"
```

---

## Test 1: Agent Configuration Validation

Test that Baron's agent configuration files are valid.

```python
import yaml
from pathlib import Path

# Load and validate config
config_path = Path(".claude/agents/baron/config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

# Check required fields
assert "name" in config, "Missing name"
assert "model" in config, "Missing model"
assert "tools" in config, "Missing tools"
assert "Read" in config["tools"], "Missing Read tool"
assert "Write" in config["tools"], "Missing Write tool"

# Check system prompt exists
system_prompt = Path(".claude/agents/baron/system-prompt.md")
assert system_prompt.exists(), "Missing system prompt"

print("✅ Agent configuration valid")
```

---

## Test 2: Dispatch Specify Workflow

Test that BaronDispatcher can trigger a specify workflow.

```python
from orchestrator import ClaudeCLIRunner
from orchestrator.baron_dispatch import BaronDispatcher
from orchestrator.models.baron_models import SpecifyRequest

# Initialize dispatcher
runner = ClaudeCLIRunner()
dispatcher = BaronDispatcher(runner)

# Dispatch specify workflow
result = dispatcher.dispatch_specify(
    SpecifyRequest(
        feature_description="Add a health check endpoint that returns service status"
    )
)

print(f"✅ Success: {result.success}")
print(f"   Spec path: {result.spec_path}")
print(f"   Feature ID: {result.feature_id}")
print(f"   Branch: {result.branch_name}")
print(f"   Duration: {result.duration_seconds:.1f}s")
```

**Expected Output**:
```
✅ Success: True
   Spec path: specs/009-health-check-endpoint/spec.md
   Feature ID: 009-health-check-endpoint
   Branch: 009-health-check-endpoint
   Duration: 45.2s
```

**Verify**: Check that `specs/009-health-check-endpoint/spec.md` exists and contains all mandatory sections.

---

## Test 3: Dispatch Plan Workflow

Test that BaronDispatcher can trigger a plan workflow.

```python
from orchestrator.models.baron_models import PlanRequest
from pathlib import Path

# Use the spec from Test 2
result = dispatcher.dispatch_plan(
    PlanRequest(spec_path=Path("specs/009-health-check-endpoint/spec.md"))
)

print(f"✅ Success: {result.success}")
print(f"   Plan path: {result.plan_path}")
print(f"   Research path: {result.research_path}")
print(f"   Data model path: {result.data_model_path}")
print(f"   Contracts dir: {result.contracts_dir}")
print(f"   Quickstart path: {result.quickstart_path}")
print(f"   Duration: {result.duration_seconds:.1f}s")
```

**Expected Output**:
```
✅ Success: True
   Plan path: specs/009-health-check-endpoint/plan.md
   Research path: specs/009-health-check-endpoint/research.md
   Data model path: specs/009-health-check-endpoint/data-model.md
   Contracts dir: specs/009-health-check-endpoint/contracts
   Quickstart path: specs/009-health-check-endpoint/quickstart.md
   Duration: 120.5s
```

**Verify**: Check that all artifacts exist and plan.md has Constitution Check section filled.

---

## Test 4: Dispatch Tasks Workflow

Test that BaronDispatcher can trigger a tasks workflow.

```python
from orchestrator.models.baron_models import TasksRequest

# Use the plan from Test 3
result = dispatcher.dispatch_tasks(
    TasksRequest(plan_path=Path("specs/009-health-check-endpoint/plan.md"))
)

print(f"✅ Success: {result.success}")
print(f"   Tasks path: {result.tasks_path}")
print(f"   Total tasks: {result.task_count}")
print(f"   Test tasks: {result.test_count}")
print(f"   Duration: {result.duration_seconds:.1f}s")
```

**Expected Output**:
```
✅ Success: True
   Tasks path: specs/009-health-check-endpoint/tasks.md
   Total tasks: 25
   Test tasks: 12
   Duration: 60.3s
```

**Verify**: Check that tasks.md has TDD tasks (test before implementation) and correct ordering.

---

## Test 5: Agent Hub Integration

Test that Baron can consult experts via Agent Hub MCP.

```bash
# Start Agent Hub MCP server in background
python -m agent_hub.mcp_server &
AGENT_HUB_PID=$!

# Run a complex feature that requires consultation
python -c "
from orchestrator import ClaudeCLIRunner
from orchestrator.baron_dispatch import BaronDispatcher
from orchestrator.models.baron_models import SpecifyRequest

runner = ClaudeCLIRunner()
dispatcher = BaronDispatcher(runner)

result = dispatcher.dispatch_specify(
    SpecifyRequest(
        feature_description='Implement distributed caching with Redis cluster support, automatic failover, and cache invalidation strategies'
    )
)

print(f'Success: {result.success}')
# Check spec.md for expert consultation notes
"

# Cleanup
kill $AGENT_HUB_PID
```

---

## Test 6: State Persistence and Resumption

Test that Baron persists state for interrupted workflows.

```python
from pathlib import Path
import json

# Check state file exists after workflow
state_path = Path("specs/009-health-check-endpoint/.baron-state.json")

if state_path.exists():
    with open(state_path) as f:
        state = json.load(f)

    print(f"Workflow ID: {state['workflow_id']}")
    print(f"Current phase: {state['current_phase']}")
    print(f"Completed phases: {state['completed_phases']}")
    print("✅ State persistence working")
else:
    print("ℹ️  State file not found (workflow may have completed)")
```

---

## Test 7: Error Handling

Test error scenarios.

```python
from orchestrator.models.baron_models import SpecifyRequest, PlanRequest
from orchestrator.baron_dispatch import DispatchError, ParseError
from pathlib import Path

# Test 1: Invalid description (too short)
try:
    dispatcher.dispatch_specify(SpecifyRequest(feature_description="Add"))
except Exception as e:
    print(f"✅ Caught validation error: {type(e).__name__}")

# Test 2: Missing spec file
try:
    dispatcher.dispatch_plan(PlanRequest(spec_path=Path("nonexistent.md")))
except Exception as e:
    print(f"✅ Caught file error: {type(e).__name__}")
```

---

## Unit Tests (Mocked)

For unit tests, mock the ClaudeCLIRunner:

```python
import pytest
from unittest.mock import Mock, MagicMock
from orchestrator.baron_dispatch import BaronDispatcher
from orchestrator.models.baron_models import SpecifyRequest

@pytest.fixture
def mock_runner():
    runner = Mock()
    runner.execute.return_value = MagicMock(
        output="""
        Baron executing specify workflow...

        <!-- BARON_RESULT_START -->
        {
            "success": true,
            "spec_path": "specs/009-test/spec.md",
            "feature_id": "009-test",
            "branch_name": "009-test",
            "duration_seconds": 10.5
        }
        <!-- BARON_RESULT_END -->
        """
    )
    return runner

def test_dispatch_specify_success(mock_runner):
    dispatcher = BaronDispatcher(mock_runner)
    result = dispatcher.dispatch_specify(
        SpecifyRequest(feature_description="Add test feature")
    )

    assert result.success is True
    assert result.feature_id == "009-test"
    mock_runner.execute.assert_called_once()
```

---

## Cleanup

After testing, clean up test artifacts:

```bash
# Remove test feature directories (if created for testing)
rm -rf specs/009-health-check-endpoint
rm -rf specs/010-distributed-caching
```

---

## Troubleshooting

### Claude CLI Not Found

**Symptom**: `DispatchError: Claude CLI not found`

**Solutions**:
1. Install Claude CLI: `npm install -g @anthropic-ai/claude-code`
2. Verify path: `which claude`
3. Check PATH environment variable

### Agent Configuration Not Found

**Symptom**: `ConfigError: Agent config not found at .claude/agents/baron/config.yaml`

**Solutions**:
1. Verify agent config exists: `ls .claude/agents/baron/`
2. Create baron agent directory structure
3. Check you're in the repo root directory

### Agent Hub Timeout

**Symptom**: `TimeoutError` during expert consultation

**Solutions**:
1. Check Agent Hub is running: `python -m agent_hub.mcp_server`
2. Increase timeout in agent config
3. Check network connectivity

### Parse Error

**Symptom**: `ParseError: Result markers not found in output`

**Solutions**:
1. Check Baron's system prompt includes output format instructions
2. Review raw Claude CLI output for errors
3. Ensure Baron workflow completed successfully

---

## Next Steps

After completing the quickstart:

1. Run the full test suite: `uv run pytest tests/unit/orchestrator/test_baron_dispatch.py tests/integration/baron/ -v`
2. Try creating a real feature using Baron
3. Review the generated artifacts for quality
4. Integrate with the Workflow Orchestrator

