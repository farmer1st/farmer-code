"""Integration tests for Baron plan workflow.

Tests dispatch Baron agent with real agent execution to verify
plan.md and artifacts are created correctly.

Journey: BRN-002 - Generate Implementation Plan
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.baron_dispatch import BaronDispatcher, DispatchError, ParseError
from orchestrator.baron_models import PlanRequest


@pytest.mark.journey("BRN-002")
@pytest.mark.integration
class TestPlanWorkflow:
    """Integration tests for the plan workflow.

    These tests verify Baron can create valid plan.md with
    research.md, data-model.md, contracts/, and quickstart.md.
    """

    @pytest.fixture
    def mock_runner(self):
        """Create a mock runner that simulates successful agent execution."""
        runner = MagicMock()
        runner.execute.return_value = MagicMock(
            output="""
            Baron executing plan workflow...

            Reading spec.md from specs/009-test-feature/spec.md...
            Spec loaded successfully.

            Running setup-plan.sh...
            Plan directory prepared.

            Loading constitution.md...
            Phase 0: Generating research.md...
            Phase 1: Generating design artifacts...
            Filling plan.md...
            Updating agent context...

            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "plan_path": "specs/009-test-feature/plan.md",
                "research_path": "specs/009-test-feature/research.md",
                "data_model_path": "specs/009-test-feature/data-model.md",
                "contracts_dir": "specs/009-test-feature/contracts",
                "quickstart_path": "specs/009-test-feature/quickstart.md",
                "duration_seconds": 145.7
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

    def test_dispatch_plan_creates_all_artifacts(self, dispatcher, mock_runner):
        """Test that Baron creates plan.md with all required artifacts."""
        request = PlanRequest(spec_path=Path("specs/009-test-feature/spec.md"))

        result = dispatcher.dispatch_plan(request)

        assert result.success is True
        assert result.plan_path == Path("specs/009-test-feature/plan.md")
        assert result.research_path == Path("specs/009-test-feature/research.md")
        assert result.data_model_path == Path("specs/009-test-feature/data-model.md")
        assert result.contracts_dir == Path("specs/009-test-feature/contracts")
        assert result.quickstart_path == Path("specs/009-test-feature/quickstart.md")
        assert result.duration_seconds > 0

    def test_dispatch_plan_includes_spec_path(self, dispatcher, mock_runner):
        """Test that spec path is passed to agent in prompt."""
        request = PlanRequest(spec_path=Path("specs/010-auth-feature/spec.md"))

        dispatcher.dispatch_plan(request)

        call_args = mock_runner.execute.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "010-auth-feature" in prompt
        assert "spec.md" in prompt

    def test_dispatch_plan_with_force_research(self, dispatcher, mock_runner):
        """Test dispatching plan with force_research flag."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "plan_path": "specs/009-test-feature/plan.md",
                "research_path": "specs/009-test-feature/research.md",
                "duration_seconds": 180.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = PlanRequest(
            spec_path=Path("specs/009-test-feature/spec.md"),
            force_research=True,
        )

        result = dispatcher.dispatch_plan(request)

        assert result.success is True
        call_args = mock_runner.execute.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "Force Research: true" in prompt

    def test_dispatch_plan_handles_blocked_escalation(self, dispatcher, mock_runner):
        """Test handling when plan is blocked on human escalation."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            Baron executing plan workflow...
            Consulting @duc for architecture decision...
            Blocked waiting for response.

            <!-- BARON_RESULT_START -->
            {
                "success": false,
                "blocked_on_escalation": true,
                "error": "Waiting for @duc to approve data storage architecture",
                "duration_seconds": 45.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = PlanRequest(spec_path=Path("specs/009-test-feature/spec.md"))

        result = dispatcher.dispatch_plan(request)

        assert result.success is False
        assert result.blocked_on_escalation is True
        assert "Waiting for @duc" in result.error

    def test_dispatch_plan_handles_spec_not_found(self, dispatcher, mock_runner):
        """Test handling when spec file is not found."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            Baron executing plan workflow...
            ERROR: Spec file not found

            <!-- BARON_RESULT_START -->
            {
                "success": false,
                "error": "Spec file not found: specs/999-missing/spec.md",
                "duration_seconds": 2.5
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=1,
        )

        request = PlanRequest(spec_path=Path("specs/999-missing/spec.md"))

        result = dispatcher.dispatch_plan(request)

        assert result.success is False
        assert "Spec file not found" in result.error

    def test_dispatch_plan_handles_runner_exception(self, dispatcher, mock_runner):
        """Test handling of runner execution exception."""
        mock_runner.execute.side_effect = Exception("Agent timeout exceeded")

        request = PlanRequest(spec_path=Path("specs/009-test-feature/spec.md"))

        with pytest.raises(DispatchError) as exc_info:
            dispatcher.dispatch_plan(request)

        assert "Agent timeout exceeded" in str(exc_info.value)

    def test_dispatch_plan_handles_missing_markers(self, dispatcher, mock_runner):
        """Test handling of missing result markers in output."""
        mock_runner.execute.return_value = MagicMock(
            output="Baron executed but forgot to output result markers",
            exit_code=0,
        )

        request = PlanRequest(spec_path=Path("specs/009-test-feature/spec.md"))

        with pytest.raises(ParseError) as exc_info:
            dispatcher.dispatch_plan(request)

        assert "Result markers not found" in str(exc_info.value)


@pytest.mark.journey("BRN-002")
@pytest.mark.integration
@pytest.mark.slow
class TestPlanWorkflowRealAgent:
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
    def test_real_agent_creates_plan(self, real_dispatcher, tmp_path):
        """Test real agent dispatch creates plan.md with artifacts.

        This test requires:
        1. Claude CLI installed and configured
        2. Agent Hub MCP server running
        3. Valid templates in .specify/templates/
        4. Existing spec.md to plan from

        Run manually with:
            pytest tests/integration/baron/test_plan_workflow.py -v
        """
        # Use existing test spec or create one
        spec_path = Path("specs/099-test-baron/spec.md")
        if not spec_path.exists():
            pytest.skip("Test spec not found - run specify workflow first")

        request = PlanRequest(spec_path=spec_path)

        result = real_dispatcher.dispatch_plan(request)

        assert result.success is True
        assert result.plan_path is not None
        assert Path(result.plan_path).exists()

        # Verify plan has required sections
        plan_content = Path(result.plan_path).read_text()
        required_sections = [
            "## Technical Context",
            "## Constitution Check",
        ]
        for section in required_sections:
            assert section in plan_content, f"Missing required section: {section}"

        # Verify artifacts created
        if result.research_path:
            assert Path(result.research_path).exists()
        if result.data_model_path:
            assert Path(result.data_model_path).exists()
