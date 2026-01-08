"""Duc agent for architecture questions.

This module provides the core agent logic for Duc, the architecture expert.
"""

import time
from typing import Any
from uuid import UUID

from src.core.prompts import get_supported_topics, get_system_prompt


class AgentError(Exception):
    """Error during agent execution."""

    def __init__(
        self,
        message: str,
        code: str = "AGENT_EXECUTION_FAILED",
    ) -> None:
        super().__init__(message)
        self.code = code


class DucAgent:
    """Duc agent for architecture questions.

    This agent processes architecture questions and provides expert guidance.
    It is stateless - all context is passed in each request.

    Example:
        agent = DucAgent()
        result = await agent.invoke(
            topic="architecture",
            context={"question": "Should we use microservices?"}
        )
    """

    def __init__(self) -> None:
        """Initialize Duc agent."""
        self._start_time = time.time()

    @property
    def supported_topics(self) -> list[str]:
        """Get list of supported topics."""
        return get_supported_topics()

    async def invoke(
        self,
        topic: str,
        context: dict[str, Any],
        parameters: dict[str, Any] | None = None,
        session_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Invoke the agent with a question.

        Args:
            topic: Type of question (architecture, api_design, system_design)
            context: Context for the agent
            parameters: Additional parameters
            session_id: Optional session ID (for logging, not state)

        Returns:
            Dict with success, result, confidence, metadata

        Raises:
            AgentError: If topic is unknown or execution fails
        """
        if topic not in self.supported_topics:
            raise AgentError(
                f"Unknown topic: {topic}",
                code="UNKNOWN_TOPIC",
            )

        start_time = time.time()
        params = parameters or {}

        try:
            # Get system prompt for topic
            system_prompt = get_system_prompt(topic)

            # Build user prompt from context
            user_prompt = self._build_user_prompt(topic, context, params)

            # Execute (mock for now)
            result = await self._execute(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                topic=topic,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "result": result,
                "confidence": self._calculate_confidence(result),
                "metadata": {
                    "duration_ms": duration_ms,
                    "agent_name": "duc",
                    "topic": topic,
                },
            }

        except AgentError:
            raise
        except Exception as e:
            raise AgentError(f"Agent execution failed: {e}") from e

    def _build_user_prompt(
        self,
        topic: str,
        context: dict[str, Any],
        parameters: dict[str, Any],
    ) -> str:
        """Build user prompt from context and parameters."""
        parts = []

        if "question" in context:
            parts.append(f"## Question\n\n{context['question']}")

        if "additional_context" in context:
            parts.append(f"## Additional Context\n\n{context['additional_context']}")

        if "conversation_history" in context:
            history = context["conversation_history"]
            history_text = "\n".join(
                f"**{msg['role'].title()}**: {msg['content']}" for msg in history
            )
            parts.append(f"## Conversation History\n\n{history_text}")

        for key, value in context.items():
            if key not in ("question", "additional_context", "conversation_history"):
                parts.append(f"## {key.replace('_', ' ').title()}\n\n{value}")

        if parameters:
            params_text = "\n".join(f"- {k}: {v}" for k, v in parameters.items())
            parts.append(f"## Parameters\n\n{params_text}")

        return "\n\n".join(parts)

    async def _execute(
        self,
        system_prompt: str,
        user_prompt: str,
        topic: str,
    ) -> dict[str, Any]:
        """Execute the query (mock implementation)."""
        # Mock response for testing
        output = (
            f"# Architecture Guidance\n\n"
            f"Based on your {topic} question, here is my analysis:\n\n"
            f"{user_prompt[:200]}..."
        )
        return {
            "output": output,
            "answer": f"Architecture recommendation for {topic} topic.",
        }

    def _calculate_confidence(self, result: dict[str, Any]) -> int:
        """Calculate confidence score for result."""
        if result.get("uncertainty_reasons"):
            num_reasons = len(result["uncertainty_reasons"])
            return max(50, 90 - (num_reasons * 10))
        return 85

    def get_health(self) -> dict[str, Any]:
        """Get agent health status."""
        uptime = int(time.time() - self._start_time)

        return {
            "status": "healthy",
            "version": "0.1.0",
            "agent_name": "duc",
            "uptime_seconds": uptime,
            "capabilities": {
                "topics": self.supported_topics,
                "specialization": "architecture",
            },
        }
