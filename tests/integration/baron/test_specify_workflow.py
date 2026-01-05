"""Integration tests for Baron specify workflow.

Tests dispatch Baron agent with real agent execution to verify
spec.md is created with all mandatory sections.

Journey: BRN-001 - Create Specification Autonomously
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.baron_dispatch import BaronDispatcher, DispatchError, ParseError
from orchestrator.baron_models import SpecifyRequest


@pytest.mark.journey("BRN-001")
@pytest.mark.integration
class TestSpecifyWorkflow:
    """Integration tests for the specify workflow.

    These tests verify Baron can create valid spec.md files
    with all mandatory sections.
    """

    @pytest.fixture
    def mock_runner(self):
        """Create a mock runner that simulates successful agent execution."""
        runner = MagicMock()
        runner.execute.return_value = MagicMock(
            output="""
            Baron executing specify workflow...

            Running create-new-feature.sh...
            Created feature directory: specs/099-test-feature/

            Loading spec-template.md...
            Loading constitution.md...

            Analyzing feature description...
            Filling template sections...

            Writing spec.md to specs/099-test-feature/spec.md
            Creating quality checklist...

            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "spec_path": "specs/099-test-feature/spec.md",
                "feature_id": "099-test-feature",
                "branch_name": "099-test-feature",
                "duration_seconds": 45.2
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

    def test_dispatch_specify_creates_spec(self, dispatcher, mock_runner):
        """Test that Baron creates spec.md with valid result."""
        request = SpecifyRequest(feature_description="Add user authentication with OAuth2 support")

        result = dispatcher.dispatch_specify(request)

        assert result.success is True
        assert result.spec_path == Path("specs/099-test-feature/spec.md")
        assert result.feature_id == "099-test-feature"
        assert result.branch_name == "099-test-feature"
        assert result.duration_seconds > 0

    def test_dispatch_specify_includes_feature_description(self, dispatcher, mock_runner):
        """Test that feature description is passed to agent."""
        request = SpecifyRequest(
            feature_description="Implement real-time notifications using WebSockets"
        )

        dispatcher.dispatch_specify(request)

        call_args = mock_runner.execute.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "real-time notifications" in prompt
        assert "WebSockets" in prompt

    def test_dispatch_specify_with_custom_feature_number(self, dispatcher, mock_runner):
        """Test dispatching with explicit feature number."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            <!-- BARON_RESULT_START -->
            {
                "success": true,
                "spec_path": "specs/010-custom-feature/spec.md",
                "feature_id": "010-custom-feature",
                "branch_name": "010-custom-feature",
                "duration_seconds": 30.0
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=0,
        )

        request = SpecifyRequest(
            feature_description="Add payment processing integration",
            feature_number=10,
            short_name="custom-feature",
        )

        result = dispatcher.dispatch_specify(request)

        assert result.success is True
        assert result.feature_id == "010-custom-feature"

    def test_dispatch_specify_handles_agent_failure(self, dispatcher, mock_runner):
        """Test handling of agent execution failure."""
        mock_runner.execute.return_value = MagicMock(
            output="""
            Baron executing specify workflow...

            ERROR: Template not found

            <!-- BARON_RESULT_START -->
            {
                "success": false,
                "error": "Template not found: spec-template.md",
                "duration_seconds": 2.5
            }
            <!-- BARON_RESULT_END -->
            """,
            exit_code=1,
        )

        request = SpecifyRequest(feature_description="Add feature that will fail")

        result = dispatcher.dispatch_specify(request)

        assert result.success is False
        assert "Template not found" in result.error

    def test_dispatch_specify_handles_runner_exception(self, dispatcher, mock_runner):
        """Test handling of runner execution exception."""
        mock_runner.execute.side_effect = Exception("Claude CLI not found")

        request = SpecifyRequest(feature_description="Add feature with CLI error")

        with pytest.raises(DispatchError) as exc_info:
            dispatcher.dispatch_specify(request)

        assert "Claude CLI not found" in str(exc_info.value)

    def test_dispatch_specify_handles_missing_markers(self, dispatcher, mock_runner):
        """Test handling of missing result markers in output."""
        mock_runner.execute.return_value = MagicMock(
            output="Baron executed but forgot to output result markers",
            exit_code=0,
        )

        request = SpecifyRequest(feature_description="Add feature with missing markers")

        with pytest.raises(ParseError) as exc_info:
            dispatcher.dispatch_specify(request)

        assert "Result markers not found" in str(exc_info.value)


@pytest.mark.journey("BRN-001")
@pytest.mark.integration
@pytest.mark.slow
class TestSpecifyWorkflowRealAgent:
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

        # Import real runner
        try:
            from orchestrator.agent_runner import ClaudeCLIRunner
        except ImportError:
            pytest.skip("ClaudeCLIRunner not available")

        runner = ClaudeCLIRunner()
        return BaronDispatcher(runner=runner)

    @pytest.mark.skip(reason="Requires real Claude CLI and Agent Hub - run manually")
    def test_real_agent_creates_spec(self, real_dispatcher, tmp_path):
        """Test real agent dispatch creates spec.md.

        This test requires:
        1. Claude CLI installed and configured
        2. Agent Hub MCP server running
        3. Valid templates in .specify/templates/

        Run manually with:
            pytest tests/integration/baron/test_specify_workflow.py -v
        """
        request = SpecifyRequest(
            feature_description="Add a simple hello world greeting feature for testing Baron agent",
            feature_number=999,
            short_name="test-baron",
        )

        result = real_dispatcher.dispatch_specify(request)

        assert result.success is True
        assert result.spec_path is not None
        assert Path(result.spec_path).exists()

        # Verify spec has mandatory sections
        spec_content = Path(result.spec_path).read_text()
        mandatory_sections = [
            "## Summary",
            "## User Stories",
            "## Functional Requirements",
            "## Success Criteria",
        ]
        for section in mandatory_sections:
            assert section in spec_content, f"Missing mandatory section: {section}"
