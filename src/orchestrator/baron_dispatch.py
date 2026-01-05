"""BaronDispatcher - Dispatch Baron PM Agent for speckit workflows.

Baron is a Claude Agent SDK agent. This module provides the BaronDispatcher class
that builds dispatch prompts and parses Baron's structured output.
"""

import json
import time
from pathlib import Path
from typing import Any, Protocol, TypeVar

import yaml

from orchestrator.baron_models import (
    PlanRequest,
    PlanResult,
    SpecifyRequest,
    SpecifyResult,
    TasksRequest,
    TasksResult,
)

T = TypeVar("T", SpecifyResult, PlanResult, TasksResult)


class ExecuteResult(Protocol):
    """Protocol for execute result with output attribute."""

    output: str


class BaronRunner(Protocol):
    """Protocol for runners that support Baron's execute interface."""

    def execute(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        tools: list[str],
        timeout: int,
    ) -> ExecuteResult:
        """Execute an agent with the given parameters."""
        ...


class DispatchError(Exception):
    """Error during Baron dispatch execution."""

    pass


class ParseError(Exception):
    """Error parsing Baron's output."""

    pass


class BaronDispatcher:
    """Dispatches Baron agent for speckit workflows.

    Baron is a Claude agent - this class builds prompts, triggers execution
    via BaronRunner, and parses structured results.
    """

    RESULT_START_MARKER = "<!-- BARON_RESULT_START -->"
    RESULT_END_MARKER = "<!-- BARON_RESULT_END -->"

    def __init__(
        self,
        runner: BaronRunner,
        agent_config_path: Path | None = None,
    ):
        """Initialize dispatcher.

        Args:
            runner: ClaudeCLIRunner instance for executing agents.
            agent_config_path: Path to Baron's agent configuration.
                Defaults to .claude/agents/baron/config.yaml
        """
        self.runner = runner
        self.config_path = agent_config_path or Path(".claude/agents/baron/config.yaml")
        self._config = self._load_config()
        self._system_prompt = self._load_system_prompt()

    def _load_config(self) -> dict[str, Any]:
        """Load Baron agent configuration from YAML."""
        if not self.config_path.exists():
            return {}
        with open(self.config_path) as f:
            return yaml.safe_load(f) or {}

    def _load_system_prompt(self) -> str:
        """Load Baron's system prompt from markdown file."""
        prompt_path = Path(".claude/agents/baron/system-prompt.md")
        if not prompt_path.exists():
            return ""
        return prompt_path.read_text()

    def dispatch_specify(self, request: SpecifyRequest) -> SpecifyResult:
        """Dispatch Baron to run specify workflow.

        Args:
            request: SpecifyRequest with feature_description.

        Returns:
            SpecifyResult parsed from Baron's output.

        Raises:
            DispatchError: If Claude CLI execution fails.
            ParseError: If Baron's output cannot be parsed.
        """
        prompt = self._build_specify_prompt(request)
        start_time = time.time()

        try:
            result = self.runner.execute(
                prompt=prompt,
                system_prompt=self._system_prompt,
                model=self._config.get("model", "sonnet"),
                tools=self._config.get("tools", []),
                timeout=self._config.get("timeout_seconds", 600),
            )
            output = result.output
        except Exception as e:
            raise DispatchError(f"Failed to dispatch Baron: {e}") from e

        parsed = self._parse_result(output, SpecifyResult)

        # Ensure duration is set
        if parsed.duration_seconds == 0:
            parsed.duration_seconds = time.time() - start_time

        return parsed

    def dispatch_plan(self, request: PlanRequest) -> PlanResult:
        """Dispatch Baron to run plan workflow.

        Args:
            request: PlanRequest with spec_path.

        Returns:
            PlanResult parsed from Baron's output.

        Raises:
            DispatchError: If Claude CLI execution fails.
            ParseError: If Baron's output cannot be parsed.
        """
        prompt = self._build_plan_prompt(request)
        start_time = time.time()

        try:
            result = self.runner.execute(
                prompt=prompt,
                system_prompt=self._system_prompt,
                model=self._config.get("model", "sonnet"),
                tools=self._config.get("tools", []),
                timeout=self._config.get("timeout_seconds", 600),
            )
            output = result.output
        except Exception as e:
            raise DispatchError(f"Failed to dispatch Baron: {e}") from e

        parsed = self._parse_result(output, PlanResult)

        if parsed.duration_seconds == 0:
            parsed.duration_seconds = time.time() - start_time

        return parsed

    def dispatch_tasks(self, request: TasksRequest) -> TasksResult:
        """Dispatch Baron to run tasks workflow.

        Args:
            request: TasksRequest with plan_path.

        Returns:
            TasksResult parsed from Baron's output.

        Raises:
            DispatchError: If Claude CLI execution fails.
            ParseError: If Baron's output cannot be parsed.
        """
        prompt = self._build_tasks_prompt(request)
        start_time = time.time()

        try:
            result = self.runner.execute(
                prompt=prompt,
                system_prompt=self._system_prompt,
                model=self._config.get("model", "sonnet"),
                tools=self._config.get("tools", []),
                timeout=self._config.get("timeout_seconds", 600),
            )
            output = result.output
        except Exception as e:
            raise DispatchError(f"Failed to dispatch Baron: {e}") from e

        parsed = self._parse_result(output, TasksResult)

        if parsed.duration_seconds == 0:
            parsed.duration_seconds = time.time() - start_time

        return parsed

    def _build_specify_prompt(self, request: SpecifyRequest) -> str:
        """Build dispatch prompt for specify workflow."""
        feature_number = request.feature_number or "auto"
        short_name = request.short_name or "auto"

        return f"""Execute the SPECIFY workflow for this feature:

## Feature Description

{request.feature_description}

## Configuration

- Feature Number: {feature_number}
- Short Name: {short_name}

## Instructions

Follow the specify workflow in `.claude/agents/baron/workflows/specify.md`:

1. Run create-new-feature.sh to set up branch and directory
2. Read spec-template.md from .specify/templates/
3. Read constitution from .specify/memory/constitution.md
4. Analyze the feature description
5. Consult experts via Agent Hub if needed (max 3 questions)
6. Fill all mandatory template sections
7. Write spec.md to the feature directory
8. Create quality checklist in checklists/requirements.md

## Output Format

Output your result in this format:

<!-- BARON_RESULT_START -->
{{
  "success": true,
  "spec_path": "specs/NNN-feature/spec.md",
  "feature_id": "NNN-feature",
  "branch_name": "NNN-feature",
  "duration_seconds": 45.2
}}
<!-- BARON_RESULT_END -->
"""

    def _build_plan_prompt(self, request: PlanRequest) -> str:
        """Build dispatch prompt for plan workflow."""
        force_research = "true" if request.force_research else "false"

        return f"""Execute the PLAN workflow for this specification:

## Specification Path

{request.spec_path}

## Configuration

- Force Research: {force_research}

## Instructions

Follow the plan workflow in `.claude/agents/baron/workflows/plan.md`:

1. Read the spec.md file
2. Read constitution from .specify/memory/constitution.md
3. Run setup-plan.sh to prepare artifacts
4. Phase 0: Generate research.md (resolve unknowns)
5. Phase 1: Generate data-model.md, contracts/, quickstart.md
6. Fill plan.md with technical context
7. Consult experts via Agent Hub for architecture decisions

## Output Format

Output your result in this format:

<!-- BARON_RESULT_START -->
{{
  "success": true,
  "plan_path": "specs/NNN-feature/plan.md",
  "research_path": "specs/NNN-feature/research.md",
  "data_model_path": "specs/NNN-feature/data-model.md",
  "contracts_dir": "specs/NNN-feature/contracts",
  "quickstart_path": "specs/NNN-feature/quickstart.md",
  "duration_seconds": 120.0
}}
<!-- BARON_RESULT_END -->
"""

    def _build_tasks_prompt(self, request: TasksRequest) -> str:
        """Build dispatch prompt for tasks workflow."""
        return f"""Execute the TASKS workflow for this plan:

## Plan Path

{request.plan_path}

## Instructions

Follow the tasks workflow in `.claude/agents/baron/workflows/tasks.md`:

1. Read plan.md, spec.md, data-model.md, contracts/
2. Read tasks-template.md from .specify/templates/
3. Read constitution for TDD requirements
4. Generate ordered task list (test tasks before implementation)
5. Write tasks.md to the feature directory

## Output Format

Output your result in this format:

<!-- BARON_RESULT_START -->
{{
  "success": true,
  "tasks_path": "specs/NNN-feature/tasks.md",
  "task_count": 25,
  "test_count": 12,
  "duration_seconds": 60.0
}}
<!-- BARON_RESULT_END -->
"""

    def _parse_result(self, output: str, result_class: type[T]) -> T:
        """Parse Baron's output into a result model.

        Args:
            output: Raw output from Baron execution.
            result_class: Pydantic model class to parse into.

        Returns:
            Parsed result model.

        Raises:
            ParseError: If markers not found or JSON invalid.
        """
        start_idx = output.find(self.RESULT_START_MARKER)
        end_idx = output.find(self.RESULT_END_MARKER)

        if start_idx == -1 or end_idx == -1:
            raise ParseError(
                f"Result markers not found in output. "
                f"Expected {self.RESULT_START_MARKER} and {self.RESULT_END_MARKER}"
            )

        json_str = output[start_idx + len(self.RESULT_START_MARKER) : end_idx].strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ParseError(f"Invalid JSON in result: {e}") from e

        return result_class.model_validate(data)
