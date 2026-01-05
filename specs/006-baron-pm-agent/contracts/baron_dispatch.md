# Contract: Baron Dispatch Interface

**Version**: 1.0.0
**Date**: 2026-01-05
**Purpose**: Define the interface for dispatching Baron agent from the Orchestrator

---

## Overview

Baron is a Claude Agent SDK agent. The only Python code is `BaronDispatcher` in `src/orchestrator/baron_dispatch.py`. This contract defines that dispatch interface.

---

## Class: BaronDispatcher

**Module**: `src/orchestrator/baron_dispatch.py`
**Responsibility**: Build prompts and dispatch Baron via ClaudeCLIRunner

```python
class BaronDispatcher:
    """
    Dispatches Baron agent for speckit workflows.

    Baron is a Claude agent - this class just triggers it and parses results.
    """

    def __init__(
        self,
        runner: ClaudeCLIRunner,
        agent_config_path: Path = Path(".claude/agents/baron/config.yaml"),
    ):
        """
        Initialize dispatcher.

        Args:
            runner: ClaudeCLIRunner instance for executing agents.
            agent_config_path: Path to Baron's agent configuration.
        """
```

---

## Operations

### dispatch_specify()

Dispatch Baron to create a feature specification.

```python
def dispatch_specify(self, request: SpecifyRequest) -> SpecifyResult:
    """
    Dispatch Baron to run specify workflow.

    Args:
        request: SpecifyRequest with feature_description.

    Returns:
        SpecifyResult parsed from Baron's output.

    Raises:
        DispatchError: If Claude CLI execution fails.
        ParseError: If Baron's output cannot be parsed.
        TimeoutError: If Baron exceeds timeout.

    Example:
        >>> dispatcher = BaronDispatcher(runner)
        >>> result = dispatcher.dispatch_specify(
        ...     SpecifyRequest(feature_description="Add OAuth2 authentication")
        ... )
        >>> print(result.spec_path)
        specs/008-oauth2-auth/spec.md
    """
```

**Dispatch Prompt Template**:
```markdown
Execute the SPECIFY workflow for this feature:

Feature Description: {feature_description}
Feature Number: {feature_number or "auto"}
Short Name: {short_name or "auto"}

Instructions:
1. Run create-new-feature.sh to set up branch and directory
2. Read spec-template.md from .specify/templates/
3. Read constitution from .specify/memory/constitution.md
4. Fill template with feature requirements
5. Consult experts via Agent Hub if needed (max 3 questions)
6. Write spec.md to the feature directory
7. Create quality checklist
8. Output structured result

Output your result in this format:
<!-- BARON_RESULT_START -->
{json with success, spec_path, feature_id, branch_name, duration_seconds}
<!-- BARON_RESULT_END -->
```

---

### dispatch_plan()

Dispatch Baron to generate an implementation plan.

```python
def dispatch_plan(self, request: PlanRequest) -> PlanResult:
    """
    Dispatch Baron to run plan workflow.

    Args:
        request: PlanRequest with spec_path.

    Returns:
        PlanResult parsed from Baron's output.

    Raises:
        DispatchError: If Claude CLI execution fails.
        ParseError: If Baron's output cannot be parsed.
        TimeoutError: If Baron exceeds timeout.
    """
```

**Dispatch Prompt Template**:
```markdown
Execute the PLAN workflow for this specification:

Spec Path: {spec_path}
Force Research: {force_research}

Instructions:
1. Read the spec.md file
2. Read constitution from .specify/memory/constitution.md
3. Read plan-template.md from .specify/templates/
4. Phase 0: Generate research.md (resolve unknowns)
5. Phase 1: Generate data-model.md, contracts/, quickstart.md
6. Fill plan.md with technical context
7. Consult experts via Agent Hub for architecture decisions
8. Output structured result

Output your result in this format:
<!-- BARON_RESULT_START -->
{json with success, plan_path, research_path, etc.}
<!-- BARON_RESULT_END -->
```

---

### dispatch_tasks()

Dispatch Baron to generate a task list.

```python
def dispatch_tasks(self, request: TasksRequest) -> TasksResult:
    """
    Dispatch Baron to run tasks workflow.

    Args:
        request: TasksRequest with plan_path.

    Returns:
        TasksResult parsed from Baron's output.

    Raises:
        DispatchError: If Claude CLI execution fails.
        ParseError: If Baron's output cannot be parsed.
        TimeoutError: If Baron exceeds timeout.
    """
```

**Dispatch Prompt Template**:
```markdown
Execute the TASKS workflow for this plan:

Plan Path: {plan_path}

Instructions:
1. Read plan.md, spec.md, data-model.md, contracts/
2. Read tasks-template.md from .specify/templates/
3. Read constitution for TDD requirements
4. Generate ordered task list (test tasks before implementation)
5. Write tasks.md to the feature directory
6. Output structured result

Output your result in this format:
<!-- BARON_RESULT_START -->
{json with success, tasks_path, task_count, test_count, duration_seconds}
<!-- BARON_RESULT_END -->
```

---

## CLI Execution

BaronDispatcher uses ClaudeCLIRunner to execute Baron:

```python
def _dispatch(self, prompt: str, workflow: str) -> str:
    """Execute Baron via Claude CLI."""
    config = self._load_agent_config()

    result = self.runner.execute(
        prompt=prompt,
        system_prompt=self._load_system_prompt(),
        model=config.get("model", "sonnet"),
        tools=config.get("tools", []),
        mcp_servers=config.get("mcp_servers", []),
        timeout=config.get("timeout_seconds", 600),
    )

    return result.output
```

---

## Result Parsing

Baron outputs structured JSON between markers:

```python
def _parse_result(self, output: str, result_class: Type[T]) -> T:
    """Parse Baron's output into a result model."""
    start = output.find("<!-- BARON_RESULT_START -->")
    end = output.find("<!-- BARON_RESULT_END -->")

    if start == -1 or end == -1:
        raise ParseError("Result markers not found in output")

    json_str = output[start + len("<!-- BARON_RESULT_START -->"):end].strip()
    data = json.loads(json_str)
    return result_class.model_validate(data)
```

---

## Error Handling

| Error | When Raised | Recovery |
|-------|-------------|----------|
| `DispatchError` | Claude CLI returns non-zero exit | Log, check CLI installation |
| `ParseError` | Result markers missing or invalid JSON | Log raw output, manual review |
| `TimeoutError` | Baron exceeds configured timeout | Check state file for resumption |
| `AgentHubError` | MCP server unavailable | Retry or proceed without consultation |

---

## Thread Safety

BaronDispatcher is NOT thread-safe. Each workflow dispatch should be serialized.

