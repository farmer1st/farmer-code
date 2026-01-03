"""Agent Runner module for dispatching AI agents.

This module provides the AgentRunner protocol and implementations for
executing AI agents via different methods (CLI, SDK).
"""

import subprocess
import time
from pathlib import Path
from typing import Any, Protocol

from orchestrator.errors import (
    AgentDispatchError,
    AgentNotAvailableError,
)
from orchestrator.logger import logger
from orchestrator.models import (
    AgentConfig,
    AgentProvider,
    AgentResult,
    ExecutionMode,
)


class AgentRunner(Protocol):
    """Protocol for AI agent execution.

    Implementations handle the specifics of invoking an AI agent,
    whether via CLI, SDK, or other mechanisms.
    """

    def dispatch(
        self,
        config: AgentConfig,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute an AI agent with the given configuration.

        Args:
            config: Complete agent configuration.
            context: Additional context (issue details, paths, etc.).

        Returns:
            AgentResult with execution outcome.

        Raises:
            AgentDispatchError: If agent fails to start.
            AgentExecutionError: If agent fails during execution.
            AgentTimeoutError: If execution exceeds timeout.
        """
        ...

    def is_available(self) -> bool:
        """Check if this runner is available on the system.

        Returns:
            True if the runner can be used, False otherwise.
        """
        ...

    def get_capabilities(self) -> list[str]:
        """List capabilities this runner supports.

        Returns:
            List of capability strings (e.g., ["skills", "plugins", "mcp"]).
        """
        ...


class ClaudeCLIRunner:
    """Runs Claude agents via the Claude CLI.

    This implementation invokes the Claude CLI (claude command) to
    execute agents with the specified configuration.

    Attributes:
        _claude_path: Path to the claude executable.
    """

    def __init__(self, claude_path: str = "claude") -> None:
        """Initialize the Claude CLI runner.

        Args:
            claude_path: Path to claude executable (default: "claude").
        """
        self._claude_path = claude_path

    def is_available(self) -> bool:
        """Check if Claude CLI is installed and accessible.

        Returns:
            True if `claude --version` succeeds.
        """
        try:
            result = subprocess.run(
                [self._claude_path, "--version"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            return False

    def get_capabilities(self) -> list[str]:
        """List Claude CLI capabilities.

        Returns:
            ["skills", "plugins", "mcp", "model_selection"]
        """
        return ["skills", "plugins", "mcp", "model_selection"]

    def dispatch(
        self,
        config: AgentConfig,
        context: dict[str, Any],
    ) -> AgentResult:
        """Execute Claude CLI with the given configuration.

        Args:
            config: Agent configuration.
            context: Additional context dict with keys:
                - issue_number: int (optional)
                - issue_title: str (optional)
                - issue_body: str (optional)
                - worktree_path: Path (required)
                - repo_path: Path (optional)

        Returns:
            AgentResult with execution outcome.

        Raises:
            AgentDispatchError: If claude CLI is not available.
        """
        start_time = time.time()

        # Build CLI command
        cmd = self._build_command(config, context)

        # Set working directory
        work_dir = context.get("worktree_path") or config.work_dir
        if work_dir:
            work_dir = Path(work_dir)

        logger.info(
            "Dispatching Claude agent",
            extra={
                "context": {
                    "model": config.model,
                    "role": config.role,
                    "work_dir": str(work_dir) if work_dir else None,
                }
            },
        )

        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=config.timeout_seconds,
            )

            duration = time.time() - start_time

            return AgentResult(
                success=result.returncode == 0,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_seconds=duration,
                error_message=result.stderr if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return AgentResult(
                success=False,
                duration_seconds=duration,
                error_message=f"Agent execution timed out after {config.timeout_seconds}s",
            )

        except FileNotFoundError as e:
            raise AgentDispatchError(f"Claude CLI not found at '{self._claude_path}': {e}") from e

        except Exception as e:
            duration = time.time() - start_time
            return AgentResult(
                success=False,
                duration_seconds=duration,
                error_message=str(e),
            )

    def _build_command(
        self,
        config: AgentConfig,
        context: dict[str, Any],
    ) -> list[str]:
        """Build the CLI command from configuration.

        Args:
            config: Agent configuration.
            context: Additional context.

        Returns:
            List of command arguments.
        """
        cmd = [self._claude_path, "--model", config.model, "--print"]

        # Add prompt
        if config.prompt:
            cmd.extend(["-p", config.prompt])

        # Add skills (allowedTools)
        for skill in config.skills:
            cmd.extend(["--allowedTools", skill])

        # Add plugins
        for plugin in config.plugins:
            cmd.extend(["--plugin", plugin])

        # Add MCP servers
        for mcp in config.mcp_servers:
            cmd.extend(["--mcp", mcp])

        return cmd


def get_runner(config: AgentConfig) -> AgentRunner:
    """Get appropriate runner for the configuration.

    Args:
        config: Agent configuration.

    Returns:
        AgentRunner instance.

    Raises:
        AgentNotAvailableError: If no runner available for config.
    """
    if config.provider == AgentProvider.CLAUDE:
        if config.mode == ExecutionMode.CLI:
            runner = ClaudeCLIRunner()
            if not runner.is_available():
                raise AgentNotAvailableError(
                    "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
                )
            return runner
        else:
            raise AgentNotAvailableError("Claude SDK mode not yet implemented")
    elif config.provider == AgentProvider.GEMINI:
        raise AgentNotAvailableError("Provider gemini not yet implemented")
    elif config.provider == AgentProvider.CODEX:
        raise AgentNotAvailableError("Provider codex not yet implemented")
    else:
        raise AgentNotAvailableError(f"Unknown provider: {config.provider}")
