"""Unit tests for BaronDispatcher.

Tests dispatch methods with mocked ClaudeCLIRunner.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from orchestrator.baron_dispatch import BaronDispatcher, DispatchError, ParseError
from orchestrator.baron_models import (
    PlanRequest,
    PlanResult,
    SpecifyRequest,
    SpecifyResult,
    TasksRequest,
    TasksResult,
)


@pytest.fixture
def mock_runner():
    """Create a mock ClaudeCLIRunner."""
    return Mock()


@pytest.fixture
def dispatcher(mock_runner):
    """Create a BaronDispatcher with mocked runner."""
    with patch.object(BaronDispatcher, "_load_config", return_value={}):
        with patch.object(BaronDispatcher, "_load_system_prompt", return_value=""):
            return BaronDispatcher(runner=mock_runner)


class TestSpecifyResultParsing:
    """Tests for parsing SpecifyResult from Baron output."""

    def test_parse_success_result(self, dispatcher):
        """Test parsing successful specify result."""
        output = """
        Baron executing specify workflow...
        Created feature directory and spec.

        <!-- BARON_RESULT_START -->
        {
            "success": true,
            "spec_path": "specs/009-test-feature/spec.md",
            "feature_id": "009-test-feature",
            "branch_name": "009-test-feature",
            "duration_seconds": 45.2
        }
        <!-- BARON_RESULT_END -->
        """
        result = dispatcher._parse_result(output, SpecifyResult)
        assert result.success is True
        assert result.feature_id == "009-test-feature"
        assert result.duration_seconds == 45.2

    def test_parse_failure_result(self, dispatcher):
        """Test parsing failed specify result."""
        output = """
        Baron executing specify workflow...
        Error: Template not found.

        <!-- BARON_RESULT_START -->
        {
            "success": false,
            "error": "Template not found: spec-template.md",
            "duration_seconds": 1.5
        }
        <!-- BARON_RESULT_END -->
        """
        result = dispatcher._parse_result(output, SpecifyResult)
        assert result.success is False
        assert "Template not found" in result.error

    def test_parse_missing_markers(self, dispatcher):
        """Test error when result markers are missing."""
        output = "Baron executed but no result markers"
        with pytest.raises(ParseError) as exc_info:
            dispatcher._parse_result(output, SpecifyResult)
        assert "Result markers not found" in str(exc_info.value)

    def test_parse_invalid_json(self, dispatcher):
        """Test error when JSON is invalid."""
        output = """
        <!-- BARON_RESULT_START -->
        {invalid json}
        <!-- BARON_RESULT_END -->
        """
        with pytest.raises(ParseError) as exc_info:
            dispatcher._parse_result(output, SpecifyResult)
        assert "Invalid JSON" in str(exc_info.value)


class TestDispatchSpecify:
    """Tests for dispatch_specify method."""

    def test_dispatch_specify_success(self, dispatcher, mock_runner):
        """Test successful specify dispatch."""
        mock_runner.execute.return_value = MagicMock(
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
            """,
            exit_code=0,
        )

        request = SpecifyRequest(feature_description="Add test feature for testing")
        result = dispatcher.dispatch_specify(request)

        assert result.success is True
        assert result.feature_id == "009-test"
        mock_runner.execute.assert_called_once()

    def test_dispatch_specify_runner_error(self, dispatcher, mock_runner):
        """Test handling of runner execution error."""
        mock_runner.execute.side_effect = Exception("CLI not found")

        request = SpecifyRequest(feature_description="Add test feature for testing")
        with pytest.raises(DispatchError) as exc_info:
            dispatcher.dispatch_specify(request)
        assert "CLI not found" in str(exc_info.value)

    def test_dispatch_specify_includes_description_in_prompt(
        self, dispatcher, mock_runner
    ):
        """Test that feature description is included in dispatch prompt."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {"success": true, "duration_seconds": 1.0}
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = SpecifyRequest(
            feature_description="Add OAuth2 authentication with Google provider"
        )
        dispatcher.dispatch_specify(request)

        call_args = mock_runner.execute.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "OAuth2 authentication" in prompt


class TestDispatchPlan:
    """Tests for dispatch_plan method."""

    def test_dispatch_plan_success(self, dispatcher, mock_runner):
        """Test successful plan dispatch."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "plan_path": "specs/009-test/plan.md",
                "research_path": "specs/009-test/research.md",
                "data_model_path": "specs/009-test/data-model.md",
                "duration_seconds": 120.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = PlanRequest(spec_path=Path("specs/009-test/spec.md"))
        result = dispatcher.dispatch_plan(request)

        assert result.success is True
        assert result.plan_path == Path("specs/009-test/plan.md")

    def test_dispatch_plan_with_force_research(self, dispatcher, mock_runner):
        """Test dispatch_plan with force_research flag."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {"success": true, "plan_path": "specs/009-test/plan.md", "duration_seconds": 60.0}
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = PlanRequest(
            spec_path=Path("specs/009-test/spec.md"),
            force_research=True,
        )
        dispatcher.dispatch_plan(request)

        call_args = mock_runner.execute.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "Force Research: true" in prompt

    def test_dispatch_plan_includes_spec_path_in_prompt(self, dispatcher, mock_runner):
        """Test that spec path is included in dispatch prompt."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {"success": true, "duration_seconds": 1.0}
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = PlanRequest(spec_path=Path("specs/010-auth-feature/spec.md"))
        dispatcher.dispatch_plan(request)

        call_args = mock_runner.execute.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "010-auth-feature" in prompt

    def test_dispatch_plan_runner_error(self, dispatcher, mock_runner):
        """Test handling of runner execution error."""
        mock_runner.execute.side_effect = Exception("Timeout exceeded")

        request = PlanRequest(spec_path=Path("specs/009-test/spec.md"))
        with pytest.raises(DispatchError) as exc_info:
            dispatcher.dispatch_plan(request)
        assert "Timeout exceeded" in str(exc_info.value)

    def test_dispatch_plan_blocked_on_escalation(self, dispatcher, mock_runner):
        """Test dispatch_plan when blocked on human escalation."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {
                "success": false,
                "blocked_on_escalation": true,
                "error": "Waiting for @duc to approve architecture",
                "duration_seconds": 45.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = PlanRequest(spec_path=Path("specs/009-test/spec.md"))
        result = dispatcher.dispatch_plan(request)

        assert result.success is False
        assert result.blocked_on_escalation is True
        assert "Waiting for @duc" in result.error


class TestDispatchTasks:
    """Tests for dispatch_tasks method."""

    def test_dispatch_tasks_success(self, dispatcher, mock_runner):
        """Test successful tasks dispatch."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "tasks_path": "specs/009-test/tasks.md",
                "task_count": 25,
                "test_count": 12,
                "duration_seconds": 60.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = TasksRequest(plan_path=Path("specs/009-test/plan.md"))
        result = dispatcher.dispatch_tasks(request)

        assert result.success is True
        assert result.task_count == 25
        assert result.test_count == 12

    def test_dispatch_tasks_includes_plan_path_in_prompt(self, dispatcher, mock_runner):
        """Test that plan path is included in dispatch prompt."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {"success": true, "duration_seconds": 1.0}
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = TasksRequest(plan_path=Path("specs/010-auth-feature/plan.md"))
        dispatcher.dispatch_tasks(request)

        call_args = mock_runner.execute.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "010-auth-feature" in prompt
        assert "plan.md" in prompt

    def test_dispatch_tasks_runner_error(self, dispatcher, mock_runner):
        """Test handling of runner execution error."""
        mock_runner.execute.side_effect = Exception("Agent crashed")

        request = TasksRequest(plan_path=Path("specs/009-test/plan.md"))
        with pytest.raises(DispatchError) as exc_info:
            dispatcher.dispatch_tasks(request)
        assert "Agent crashed" in str(exc_info.value)

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

    def test_dispatch_tasks_verifies_tdd_ordering(self, dispatcher, mock_runner):
        """Test that tasks result includes test count for TDD verification."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "tasks_path": "specs/009-test/tasks.md",
                "task_count": 30,
                "test_count": 15,
                "duration_seconds": 45.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = TasksRequest(plan_path=Path("specs/009-test/plan.md"))
        result = dispatcher.dispatch_tasks(request)

        assert result.success is True
        assert result.test_count > 0  # TDD requires test tasks
        assert result.test_count <= result.task_count


class TestPlanResultParsing:
    """Tests for parsing PlanResult from Baron output."""

    def test_parse_blocked_result(self, dispatcher):
        """Test parsing result when blocked on escalation."""
        output = """
        <!-- BARON_RESULT_START -->
        {
            "success": false,
            "blocked_on_escalation": true,
            "error": "Waiting for human approval",
            "duration_seconds": 30.0
        }
        <!-- BARON_RESULT_END -->
        """
        result = dispatcher._parse_result(output, PlanResult)
        assert result.success is False
        assert result.blocked_on_escalation is True


class TestTasksResultParsing:
    """Tests for parsing TasksResult from Baron output."""

    def test_parse_with_counts(self, dispatcher):
        """Test parsing tasks result with task counts."""
        output = """
        <!-- BARON_RESULT_START -->
        {
            "success": true,
            "tasks_path": "specs/009-test/tasks.md",
            "task_count": 45,
            "test_count": 20,
            "duration_seconds": 75.0
        }
        <!-- BARON_RESULT_END -->
        """
        result = dispatcher._parse_result(output, TasksResult)
        assert result.success is True
        assert result.task_count == 45
        assert result.test_count == 20
