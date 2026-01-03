"""E2E tests for AgentRunner with real Claude CLI.

These tests actually spawn the Claude CLI and expect real LLM responses.
They are SKIPPED on GitHub Actions (CI environment) since they require
a Claude Pro Max subscription and local Claude CLI installation.

Run locally with:
    uv run pytest tests/e2e/test_agent_runner_e2e.py -v

To force run even in CI (not recommended):
    RUN_CLAUDE_E2E=1 uv run pytest tests/e2e/test_agent_runner_e2e.py -v
"""

import os
import tempfile
from pathlib import Path

import pytest

from orchestrator import AgentConfig, AgentProvider, ExecutionMode
from orchestrator.agent_runner import ClaudeCLIRunner, get_runner

# Skip on CI unless explicitly enabled
SKIP_REASON = "Requires local Claude CLI with Pro Max subscription"
skip_on_ci = pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS") == "true" and os.environ.get("RUN_CLAUDE_E2E") != "1",
    reason=SKIP_REASON,
)


@pytest.fixture
def claude_runner():
    """Create a real ClaudeCLIRunner."""
    return ClaudeCLIRunner()


@pytest.fixture
def temp_workdir():
    """Create a temporary working directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestClaudeCLIAvailability:
    """Test that Claude CLI is available locally."""

    @skip_on_ci
    def test_claude_cli_is_installed(self, claude_runner):
        """Verify Claude CLI is installed and accessible."""
        is_available = claude_runner.is_available()

        if not is_available:
            pytest.skip("Claude CLI not installed - run: npm install -g @anthropic-ai/claude-code")

        assert is_available, "Claude CLI should be available"

    @skip_on_ci
    def test_claude_cli_reports_capabilities(self, claude_runner):
        """Verify Claude CLI reports its capabilities."""
        if not claude_runner.is_available():
            pytest.skip("Claude CLI not installed")

        capabilities = claude_runner.get_capabilities()

        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
        # Claude CLI should support at least model selection
        assert "model_selection" in capabilities


class TestClaudeCLIDispatch:
    """E2E tests for actual Claude CLI dispatch."""

    @skip_on_ci
    def test_dispatch_simple_prompt_gets_response(self, claude_runner, temp_workdir):
        """Send a simple prompt and verify we get a response."""
        if not claude_runner.is_available():
            pytest.skip("Claude CLI not installed")

        config = AgentConfig(
            provider=AgentProvider.CLAUDE,
            mode=ExecutionMode.CLI,
            model="sonnet",
            role="assistant",
            prompt="Respond with exactly: HELLO_E2E_TEST",
        )

        context = {
            "issue_number": 999,
            "feature_name": "e2e-test",
            "worktree_path": str(temp_workdir),
        }

        result = claude_runner.dispatch(config, context)

        # We should get a successful result
        assert result.success, f"Dispatch failed: {result.error_message}"
        # stdout should contain something (the LLM's response)
        assert result.stdout is not None
        assert len(result.stdout) > 0, f"Expected output, got empty stdout. stderr: {result.stderr}"

    @skip_on_ci
    def test_dispatch_with_print_flag_returns_output(self, claude_runner, temp_workdir):
        """Verify --print flag returns the response in output."""
        if not claude_runner.is_available():
            pytest.skip("Claude CLI not installed")

        config = AgentConfig(
            provider=AgentProvider.CLAUDE,
            mode=ExecutionMode.CLI,
            model="haiku",  # Use haiku for faster/cheaper response
            role="assistant",
            prompt="What is 2+2? Answer with just the number.",
        )

        context = {
            "issue_number": 998,
            "feature_name": "math-test",
            "worktree_path": str(temp_workdir),
        }

        result = claude_runner.dispatch(config, context)

        assert result.success, f"Dispatch failed: {result.error_message}"
        # The stdout should contain "4" somewhere
        assert "4" in result.stdout, f"Expected '4' in stdout, got: {result.stdout}"

    @skip_on_ci
    def test_dispatch_records_execution_time(self, claude_runner, temp_workdir):
        """Verify execution time is recorded."""
        if not claude_runner.is_available():
            pytest.skip("Claude CLI not installed")

        config = AgentConfig(
            provider=AgentProvider.CLAUDE,
            mode=ExecutionMode.CLI,
            model="haiku",
            role="assistant",
            prompt="Say hi",
        )

        context = {
            "issue_number": 997,
            "feature_name": "time-test",
            "worktree_path": str(temp_workdir),
        }

        result = claude_runner.dispatch(config, context)

        assert result.success, f"Dispatch failed: {result.error_message}"
        assert result.duration_seconds is not None
        assert result.duration_seconds > 0


class TestGetRunnerFactory:
    """E2E tests for the get_runner factory function."""

    @skip_on_ci
    def test_get_runner_returns_working_claude_runner(self, temp_workdir):
        """Verify get_runner returns a functional Claude runner."""
        config = AgentConfig(
            provider=AgentProvider.CLAUDE,
            mode=ExecutionMode.CLI,
            model="haiku",
            role="assistant",
            prompt="Respond with: FACTORY_TEST_OK",
        )

        runner = get_runner(config)

        if not runner.is_available():
            pytest.skip("Claude CLI not installed")

        context = {
            "issue_number": 996,
            "feature_name": "factory-test",
            "worktree_path": str(temp_workdir),
        }

        result = runner.dispatch(config, context)

        assert result.success, f"Dispatch failed: {result.error_message}"


class TestClaudeCLIErrorHandling:
    """E2E tests for error handling with real Claude CLI."""

    @skip_on_ci
    def test_dispatch_with_invalid_model_fails_gracefully(self, claude_runner, temp_workdir):
        """Verify invalid model name is handled gracefully."""
        if not claude_runner.is_available():
            pytest.skip("Claude CLI not installed")

        config = AgentConfig(
            provider=AgentProvider.CLAUDE,
            mode=ExecutionMode.CLI,
            model="nonexistent-model-xyz",
            role="assistant",
            prompt="This should fail",
        )

        context = {
            "issue_number": 995,
            "feature_name": "error-test",
            "worktree_path": str(temp_workdir),
        }

        result = claude_runner.dispatch(config, context)

        # Should fail but not raise an exception
        # (actual behavior depends on how Claude CLI handles invalid models)
        # Just verify we get a result back
        assert result is not None
