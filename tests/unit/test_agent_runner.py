"""Unit tests for the Agent Runner (User Story 3).

Tests cover:
- T043: AgentRunner protocol
- T044: ClaudeCLIRunner.is_available()
- T045: ClaudeCLIRunner.dispatch()
- T046: get_runner() factory
"""

from unittest.mock import MagicMock, patch

import pytest

from orchestrator import (
    AgentConfig,
    AgentNotAvailableError,
    AgentProvider,
    ExecutionMode,
)


class TestAgentRunnerProtocol:
    """T043: Unit tests for AgentRunner protocol."""

    def test_protocol_defines_dispatch(self):
        """AgentRunner protocol should define dispatch method."""
        from orchestrator.agent_runner import AgentRunner

        # Protocol should define these methods
        assert hasattr(AgentRunner, "dispatch")
        assert hasattr(AgentRunner, "is_available")
        assert hasattr(AgentRunner, "get_capabilities")

    def test_claude_cli_runner_implements_protocol(self):
        """ClaudeCLIRunner should implement AgentRunner protocol."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        runner = ClaudeCLIRunner()
        # Should have all protocol methods
        assert hasattr(runner, "dispatch")
        assert hasattr(runner, "is_available")
        assert hasattr(runner, "get_capabilities")


class TestClaudeCLIRunnerIsAvailable:
    """T044: Unit tests for ClaudeCLIRunner.is_available()."""

    def test_is_available_when_claude_installed(self):
        """Should return True when Claude CLI is installed."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            runner = ClaudeCLIRunner()
            assert runner.is_available() is True

    def test_is_not_available_when_claude_missing(self):
        """Should return False when Claude CLI is not installed."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("claude not found")
            runner = ClaudeCLIRunner()
            assert runner.is_available() is False

    def test_is_not_available_on_error(self):
        """Should return False on any error."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            runner = ClaudeCLIRunner()
            assert runner.is_available() is False


class TestClaudeCLIRunnerDispatch:
    """T045: Unit tests for ClaudeCLIRunner.dispatch()."""

    def test_dispatch_basic_config(self, tmp_path):
        """Should dispatch agent with basic configuration."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Agent output",
                stderr="",
            )

            runner = ClaudeCLIRunner()
            config = AgentConfig(
                provider=AgentProvider.CLAUDE,
                mode=ExecutionMode.CLI,
                model="sonnet",
                role="test",
                prompt="Do something",
            )

            result = runner.dispatch(config, {"worktree_path": tmp_path})

            assert result.success is True
            assert result.exit_code == 0
            mock_run.assert_called_once()

    def test_dispatch_with_skills(self, tmp_path):
        """Should include skills in CLI command."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            runner = ClaudeCLIRunner()
            config = AgentConfig(
                provider=AgentProvider.CLAUDE,
                mode=ExecutionMode.CLI,
                model="sonnet",
                role="@duc",
                skills=["/speckit.specify", "/speckit.plan"],
            )

            runner.dispatch(config, {"worktree_path": tmp_path})

            # Verify skills were added to command
            call_args = mock_run.call_args
            cmd = call_args.args[0] if call_args.args else call_args.kwargs.get("args", [])
            cmd_str = " ".join(cmd)
            assert "/speckit.specify" in cmd_str or "allowedTools" in cmd_str

    def test_dispatch_failure(self, tmp_path):
        """Should handle dispatch failure."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Error occurred",
            )

            runner = ClaudeCLIRunner()
            config = AgentConfig(
                provider=AgentProvider.CLAUDE,
                mode=ExecutionMode.CLI,
                model="sonnet",
                role="test",
                prompt="Do something",
            )

            result = runner.dispatch(config, {"worktree_path": tmp_path})

            assert result.success is False
            assert result.exit_code == 1

    def test_dispatch_timeout(self, tmp_path):
        """Should handle timeout."""
        import subprocess

        from orchestrator.agent_runner import ClaudeCLIRunner

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=10)

            runner = ClaudeCLIRunner()
            config = AgentConfig(
                provider=AgentProvider.CLAUDE,
                mode=ExecutionMode.CLI,
                model="sonnet",
                role="test",
                prompt="Do something",
                timeout_seconds=10,
            )

            result = runner.dispatch(config, {"worktree_path": tmp_path})

            assert result.success is False
            assert "timed out" in result.error_message.lower()

    def test_dispatch_records_duration(self, tmp_path):
        """Should record execution duration."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            runner = ClaudeCLIRunner()
            config = AgentConfig(
                provider=AgentProvider.CLAUDE,
                mode=ExecutionMode.CLI,
                model="sonnet",
                role="test",
                prompt="Do something",
            )

            result = runner.dispatch(config, {"worktree_path": tmp_path})

            assert result.duration_seconds is not None
            assert result.duration_seconds >= 0


class TestClaudeCLIRunnerCapabilities:
    """Additional tests for capabilities."""

    def test_get_capabilities(self):
        """Should return expected capabilities."""
        from orchestrator.agent_runner import ClaudeCLIRunner

        runner = ClaudeCLIRunner()
        caps = runner.get_capabilities()

        assert "skills" in caps
        assert "plugins" in caps
        assert "mcp" in caps
        assert "model_selection" in caps


class TestGetRunnerFactory:
    """T046: Unit tests for get_runner() factory."""

    def test_get_runner_returns_claude_cli(self):
        """Should return ClaudeCLIRunner for Claude CLI config."""
        from orchestrator.agent_runner import ClaudeCLIRunner, get_runner

        with patch.object(ClaudeCLIRunner, "is_available", return_value=True):
            config = AgentConfig(
                provider=AgentProvider.CLAUDE,
                mode=ExecutionMode.CLI,
                model="sonnet",
                role="test",
            )

            runner = get_runner(config)
            assert isinstance(runner, ClaudeCLIRunner)

    def test_get_runner_raises_when_unavailable(self):
        """Should raise AgentNotAvailableError when runner unavailable."""
        from orchestrator.agent_runner import ClaudeCLIRunner, get_runner

        with patch.object(ClaudeCLIRunner, "is_available", return_value=False):
            config = AgentConfig(
                provider=AgentProvider.CLAUDE,
                mode=ExecutionMode.CLI,
                model="sonnet",
                role="test",
            )

            with pytest.raises(AgentNotAvailableError) as exc_info:
                get_runner(config)

            assert "claude" in str(exc_info.value).lower()

    def test_get_runner_raises_for_sdk_mode(self):
        """Should raise AgentNotAvailableError for SDK mode (not implemented)."""
        from orchestrator.agent_runner import get_runner

        config = AgentConfig(
            provider=AgentProvider.CLAUDE,
            mode=ExecutionMode.SDK,
            model="sonnet",
            role="test",
        )

        with pytest.raises(AgentNotAvailableError) as exc_info:
            get_runner(config)

        assert "sdk" in str(exc_info.value).lower()

    def test_get_runner_raises_for_gemini(self):
        """Should raise AgentNotAvailableError for Gemini (not implemented)."""
        from orchestrator.agent_runner import get_runner

        config = AgentConfig(
            provider=AgentProvider.GEMINI,
            mode=ExecutionMode.CLI,
            model="pro",
            role="test",
        )

        with pytest.raises(AgentNotAvailableError) as exc_info:
            get_runner(config)

        assert "gemini" in str(exc_info.value).lower()
