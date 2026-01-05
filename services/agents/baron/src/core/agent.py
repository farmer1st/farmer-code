"""Baron agent wrapper using Claude Code SDK.

This module provides the core agent logic for Baron, wrapping the
Claude Code SDK to process workflow requests.
"""

import time
from typing import Any
from uuid import UUID

from src.core.prompts import get_supported_workflow_types, get_system_prompt


class AgentError(Exception):
    """Error during agent execution."""

    def __init__(
        self,
        message: str,
        code: str = "AGENT_EXECUTION_FAILED",
    ) -> None:
        super().__init__(message)
        self.code = code


class BaronAgent:
    """Baron agent for SpecKit workflows.

    This agent processes workflow requests using the Claude Code SDK.
    It is stateless - all context is passed in each request.

    Example:
        agent = BaronAgent()
        result = await agent.invoke(
            workflow_type="specify",
            context={"feature_description": "Add auth"}
        )
    """

    def __init__(self) -> None:
        """Initialize Baron agent."""
        self._start_time = time.time()

    @property
    def supported_workflows(self) -> list[str]:
        """Get list of supported workflow types."""
        return get_supported_workflow_types()

    async def invoke(
        self,
        workflow_type: str,
        context: dict[str, Any],
        parameters: dict[str, Any] | None = None,
        session_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Invoke the agent with a workflow request.

        Args:
            workflow_type: Type of workflow (specify, plan, tasks, implement)
            context: Context for the agent
            parameters: Additional parameters
            session_id: Optional session ID (for logging, not state)

        Returns:
            Dict with success, result, confidence, metadata

        Raises:
            AgentError: If workflow type is unknown or execution fails
        """
        if workflow_type not in self.supported_workflows:
            raise AgentError(
                f"Unknown workflow type: {workflow_type}",
                code="UNKNOWN_WORKFLOW_TYPE",
            )

        start_time = time.time()
        params = parameters or {}

        try:
            # Get system prompt for workflow
            system_prompt = get_system_prompt(workflow_type)

            # Build user prompt from context
            user_prompt = self._build_user_prompt(workflow_type, context, params)

            # Execute via Claude Code SDK
            result = await self._execute_with_sdk(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                workflow_type=workflow_type,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "result": result,
                "confidence": self._calculate_confidence(result),
                "metadata": {
                    "duration_ms": duration_ms,
                    "model_used": "claude-3-5-sonnet-20241022",
                    "workflow_type": workflow_type,
                },
            }

        except AgentError:
            raise
        except Exception as e:
            raise AgentError(f"Agent execution failed: {e}") from e

    def _build_user_prompt(
        self,
        workflow_type: str,
        context: dict[str, Any],
        parameters: dict[str, Any],
    ) -> str:
        """Build user prompt from context and parameters.

        Args:
            workflow_type: Type of workflow
            context: Context dict
            parameters: Parameters dict

        Returns:
            Formatted user prompt
        """
        parts = []

        # Add feature description if present
        if "feature_description" in context:
            parts.append(f"## Feature Description\n\n{context['feature_description']}")

        # Add requirements if present
        if "requirements" in context:
            reqs = context["requirements"]
            if isinstance(reqs, list):
                reqs_text = "\n".join(f"- {r}" for r in reqs)
            else:
                reqs_text = str(reqs)
            parts.append(f"## Requirements\n\n{reqs_text}")

        # Add spec/plan paths if present
        if "spec_path" in context:
            parts.append(f"## Specification Path\n\n{context['spec_path']}")

        if "plan_path" in context:
            parts.append(f"## Plan Path\n\n{context['plan_path']}")

        # Add any additional context
        for key, value in context.items():
            if key not in ("feature_description", "requirements", "spec_path", "plan_path"):
                parts.append(f"## {key.replace('_', ' ').title()}\n\n{value}")

        # Add parameters if any
        if parameters:
            params_text = "\n".join(f"- {k}: {v}" for k, v in parameters.items())
            parts.append(f"## Parameters\n\n{params_text}")

        return "\n\n".join(parts)

    async def _execute_with_sdk(
        self,
        system_prompt: str,
        user_prompt: str,
        workflow_type: str,
    ) -> dict[str, Any]:
        """Execute workflow using Claude Code SDK.

        This is a placeholder that will be replaced with actual SDK integration.
        For now, it returns a mock response for testing.

        Args:
            system_prompt: System prompt for the agent
            user_prompt: User prompt with context
            workflow_type: Type of workflow

        Returns:
            Result dict with output and metadata
        """
        # TODO: Replace with actual Claude Code SDK integration
        # For now, return a mock response for testing
        #
        # Real implementation would be:
        # from claude_code_sdk import query, ClaudeAgentOptions
        #
        # result = []
        # async for message in query(
        #     prompt=user_prompt,
        #     options=ClaudeAgentOptions(
        #         system_prompt=system_prompt,
        #         allowed_tools=["Read", "Write", "Glob", "Grep", "Edit"],
        #         permission_mode="acceptEdits",
        #     )
        # ):
        #     result.append(message)
        #
        # return self._parse_sdk_result(result)

        return {
            "output": f"# {workflow_type.title()} Output\n\nProcessed workflow: {workflow_type}\n\n{user_prompt[:200]}...",
            "files_created": [],
            "files_read": [],
        }

    def _calculate_confidence(self, result: dict[str, Any]) -> int:
        """Calculate confidence score for result.

        Args:
            result: Result dict from execution

        Returns:
            Confidence score 0-100
        """
        # Simple heuristic for now
        # Real implementation would analyze result quality
        if result.get("uncertainty_reasons"):
            # Lower confidence if there are uncertainty reasons
            num_reasons = len(result["uncertainty_reasons"])
            return max(50, 90 - (num_reasons * 10))

        # Default high confidence for successful execution
        return 85

    def get_health(self) -> dict[str, Any]:
        """Get agent health status.

        Returns:
            Health status dict
        """
        uptime = int(time.time() - self._start_time)

        return {
            "status": "healthy",
            "version": "0.1.0",
            "agent_name": "baron",
            "uptime_seconds": uptime,
            "capabilities": {
                "workflow_types": self.supported_workflows,
                "tools": ["Read", "Write", "Glob", "Grep", "Edit"],
                "mcp_servers": [],
                "skills": ["speckit.specify", "speckit.plan", "speckit.tasks", "speckit.implement"],
            },
        }
