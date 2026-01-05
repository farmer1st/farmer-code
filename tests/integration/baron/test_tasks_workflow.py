"""Integration tests for Baron tasks workflow.

Tests dispatch Baron agent with real agent execution to verify
tasks.md is created with TDD ordering.

Journey: BRN-003 - Generate Task List
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.baron_dispatch import BaronDispatcher, DispatchError, ParseError
from orchestrator.baron_models import TasksRequest


@pytest.mark.journey("BRN-003")
@pytest.mark.integration
class TestTasksWorkflow:
    """Integration tests for the tasks workflow.

    These tests verify Baron can create valid tasks.md with
    TDD ordering (tests before implementation).
    """

    @pytest.fixture
    def mock_runner(self):
        """Create a mock runner that simulates successful agent execution."""
        runner = MagicMock()
        runner.execute.return_value = MagicMock(
            output="""
            Baron executing tasks workflow...

            Reading plan.md from specs/009-test-feature/plan.md...
            Plan loaded successfully.

            Reading spec.md...
            Found 2 user stories.

            Reading data-model.md...
            Reading contracts/...

            Loading constitution.md...
            TDD principle: tests before implementation

            Generating task list...
            - Phase 1: Setup (2 tasks)
            - Phase 2: Foundational (4 tasks)
            - Phase 3: US1 (8 tasks, 4 tests)
            - Phase 4: US2 (6 tasks, 3 tests)

            Writing tasks.md...

            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "tasks_path": "specs/009-test-feature/tasks.md",
                "task_count": 20,
                "test_count": 7,
                "duration_seconds": 48.5
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )
        return runner

    @pytest.fixture
    def dispatcher(self, mock_runner):
        """Create a BaronDispatcher with mocked runner."""
        with patch.object(BaronDispatcher, "_load_config", return_value={}):
            with patch.object(BaronDispatcher, "_load_system_prompt", return_value=""):
                return BaronDispatcher(runner=mock_runner)

    def test_dispatch_tasks_creates_task_list(self, dispatcher, mock_runner):
        """Test that Baron creates tasks.md with task counts."""
        request = TasksRequest(plan_path=Path("specs/009-test-feature/plan.md"))

        result = dispatcher.dispatch_tasks(request)

        assert result.success is True
        assert result.tasks_path == Path("specs/009-test-feature/tasks.md")
        assert result.task_count == 20
        assert result.test_count == 7
        assert result.duration_seconds > 0

    def test_dispatch_tasks_includes_plan_path(self, dispatcher, mock_runner):
        """Test that plan path is passed to agent in prompt."""
        request = TasksRequest(plan_path=Path("specs/010-auth-feature/plan.md"))

        dispatcher.dispatch_tasks(request)

        call_args = mock_runner.execute.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "010-auth-feature" in prompt
        assert "plan.md" in prompt

    def test_dispatch_tasks_verifies_tdd_ordering(self, dispatcher, mock_runner):
        """Test that tasks result includes test count for TDD verification."""
        request = TasksRequest(plan_path=Path("specs/009-test-feature/plan.md"))

        result = dispatcher.dispatch_tasks(request)

        assert result.success is True
        assert result.test_count > 0, "TDD requires test tasks"
        assert result.test_count <= result.task_count

    def test_dispatch_tasks_handles_plan_not_found(self, dispatcher, mock_runner):
        """Test handling when plan file is not found."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            Baron executing tasks workflow...
            ERROR: Plan file not found

            <!-- BARON_RESULT_START -->
            {
                "success": false,
                "error": "Plan file not found: specs/999-missing/plan.md",
                "duration_seconds": 2.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=1,
        )

        request = TasksRequest(plan_path=Path("specs/999-missing/plan.md"))

        result = dispatcher.dispatch_tasks(request)

        assert result.success is False
        assert "Plan file not found" in result.error

    def test_dispatch_tasks_handles_runner_exception(self, dispatcher, mock_runner):
        """Test handling of runner execution exception."""
        mock_runner.execute.side_effect = Exception("Agent timeout exceeded")

        request = TasksRequest(plan_path=Path("specs/009-test-feature/plan.md"))

        with pytest.raises(DispatchError) as exc_info:
            dispatcher.dispatch_tasks(request)

        assert "Agent timeout exceeded" in str(exc_info.value)

    def test_dispatch_tasks_handles_missing_markers(self, dispatcher, mock_runner):
        """Test handling of missing result markers in output."""
        mock_runner.execute.return_value = MagicMock(
            output="Baron executed but forgot to output result markers",
            exit_code=0,
        )

        request = TasksRequest(plan_path=Path("specs/009-test-feature/plan.md"))

        with pytest.raises(ParseError) as exc_info:
            dispatcher.dispatch_tasks(request)

        assert "Result markers not found" in str(exc_info.value)

    def test_dispatch_tasks_large_task_count(self, dispatcher, mock_runner):
        """Test handling of large task lists."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "tasks_path": "specs/009-test-feature/tasks.md",
                "task_count": 75,
                "test_count": 30,
                "duration_seconds": 120.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = TasksRequest(plan_path=Path("specs/009-test-feature/plan.md"))

        result = dispatcher.dispatch_tasks(request)

        assert result.success is True
        assert result.task_count == 75
        assert result.test_count == 30


@pytest.mark.journey("BRN-003")
@pytest.mark.integration
@pytest.mark.slow
class TestTasksWorkflowRealAgent:
    """Integration tests with real agent dispatch.

    These tests require Claude CLI to be available and
    are marked as slow since they involve actual agent execution.

    Skip these tests in CI by using: pytest -m "not slow"
    """

    @pytest.fixture
    def real_dispatcher(self):
        """Create a real BaronDispatcher.

        Skip if config files don't exist.
        """
        config_path = Path(".claude/agents/baron/config.yaml")
        if not config_path.exists():
            pytest.skip("Baron agent config not found")

        try:
            from orchestrator.agent_runner import ClaudeCLIRunner
        except ImportError:
            pytest.skip("ClaudeCLIRunner not available")

        runner = ClaudeCLIRunner()
        return BaronDispatcher(runner=runner)

    @pytest.mark.skip(reason="Requires real Claude CLI and Agent Hub - run manually")
    def test_real_agent_creates_tasks(self, real_dispatcher, tmp_path):
        """Test real agent dispatch creates tasks.md with TDD ordering.

        This test requires:
        1. Claude CLI installed and configured
        2. Agent Hub MCP server running
        3. Valid templates in .specify/templates/
        4. Existing plan.md to generate tasks from

        Run manually with:
            pytest tests/integration/baron/test_tasks_workflow.py -v
        """
        # Use existing test plan or create one
        plan_path = Path("specs/099-test-baron/plan.md")
        if not plan_path.exists():
            pytest.skip("Test plan not found - run plan workflow first")

        request = TasksRequest(plan_path=plan_path)

        result = real_dispatcher.dispatch_tasks(request)

        assert result.success is True
        assert result.tasks_path is not None
        assert Path(result.tasks_path).exists()

        # Verify TDD ordering in tasks
        tasks_content = Path(result.tasks_path).read_text()

        # Check for test sections before implementation sections
        assert "### Tests for" in tasks_content, "Missing test sections"

        # Verify task counts
        assert result.task_count > 0
        assert result.test_count > 0, "TDD requires test tasks"
