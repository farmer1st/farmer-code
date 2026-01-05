"""Agent Router for Agent Hub.

This module handles routing questions to agents via Claude CLI
and parsing their structured JSON responses.
"""

import json
import subprocess
import uuid
from datetime import datetime
from typing import Any

from .config import RoutingConfig
from .exceptions import AgentDispatchError, AgentResponseError, AgentTimeoutError
from .models import AgentHandle, AgentStatus, Answer, Question

# Default prompt template for knowledge agents
KNOWLEDGE_AGENT_PROMPT = """You are {agent_name}, the {agent_role} Agent.

Answer the following question. Your response MUST be valid JSON with this structure:
{{
  "answer": "your answer here",
  "rationale": "why you believe this is correct (at least 20 characters)",
  "confidence": 85,
  "uncertainty_reasons": ["reason 1", "reason 2"]
}}

Base your confidence on:
- 90-100: You have specific knowledge/documentation about this
- 70-89: You're making an informed inference based on patterns
- 50-69: You have general knowledge but significant uncertainty
- 0-49: You're guessing, recommend human input

If confidence < 100, include uncertainty_reasons explaining what you don't know.

Question: {question}

{context_section}
{options_section}
"""


class AgentRouter:
    """Routes questions to agents via Claude CLI."""

    def __init__(
        self,
        config: RoutingConfig,
        claude_path: str = "claude",
    ) -> None:
        """Initialize the router.

        Args:
            config: Routing configuration.
            claude_path: Path to Claude CLI executable.
        """
        self._config = config
        self._claude_path = claude_path

    def dispatch_question(
        self,
        question: Question,
        agent_id: str,
    ) -> AgentHandle:
        """Dispatch a question to an agent.

        Args:
            question: The question to ask.
            agent_id: Target agent ID.

        Returns:
            AgentHandle for tracking the dispatch.

        Raises:
            AgentDispatchError: If dispatch fails.
            AgentTimeoutError: If agent times out.
        """
        if agent_id not in self._config.agents:
            raise AgentDispatchError(f"Unknown agent: {agent_id}")

        agent = self._config.agents[agent_id]
        model = agent.default_model
        timeout = agent.default_timeout

        # Build prompt
        prompt = self._build_prompt(question, agent.name, agent_id)

        # Create handle
        handle = AgentHandle(
            id=str(uuid.uuid4()),
            agent_role=agent_id,
            agent_name=agent.name,
            status=AgentStatus.RUNNING,
            question_id=question.id,
        )

        # Build CLI command
        cmd = [
            self._claude_path,
            "--model",
            model,
            "--print",
            "-p",
            prompt,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                handle.status = AgentStatus.FAILED
                handle.completed_at = datetime.utcnow()
                raise AgentDispatchError(f"Agent {agent_id} failed: {result.stderr}")

            handle.status = AgentStatus.COMPLETED
            handle.completed_at = datetime.utcnow()

            # Store raw response for later parsing
            handle._raw_response = result.stdout  # type: ignore[attr-defined]

            return handle

        except subprocess.TimeoutExpired:
            handle.status = AgentStatus.TIMEOUT
            handle.completed_at = datetime.utcnow()
            raise AgentTimeoutError(f"Agent {agent_id} timed out after {timeout}s") from None

    def parse_answer(
        self,
        handle: AgentHandle,
        question: Question,
    ) -> Answer:
        """Parse the answer from a completed agent dispatch.

        Args:
            handle: Completed agent handle.
            question: Original question.

        Returns:
            Parsed Answer.

        Raises:
            AgentResponseError: If response cannot be parsed.
        """
        if handle.status != AgentStatus.COMPLETED:
            raise AgentResponseError(f"Cannot parse answer from agent with status {handle.status}")

        raw_response = getattr(handle, "_raw_response", None)
        if not raw_response:
            raise AgentResponseError("No response from agent")

        # Try to extract JSON from response
        try:
            data = self._extract_json(raw_response)
        except json.JSONDecodeError as e:
            raise AgentResponseError(f"Invalid JSON response: {e}") from e

        # Validate required fields
        required = ["answer", "rationale", "confidence"]
        for field in required:
            if field not in data:
                raise AgentResponseError(f"Missing required field: {field}")

        # Create Answer
        return Answer(
            question_id=question.id,
            answered_by=handle.agent_name,
            answer=data["answer"],
            rationale=data["rationale"],
            confidence=data["confidence"],
            uncertainty_reasons=data.get("uncertainty_reasons", []),
            model_used=self._config.get_model_for_agent(handle.agent_role),
            duration_seconds=(
                (handle.completed_at - handle.started_at).total_seconds()
                if handle.completed_at
                else 0.0
            ),
        )

    def _build_prompt(
        self,
        question: Question,
        agent_name: str,
        agent_role: str,
    ) -> str:
        """Build the prompt for the agent.

        Args:
            question: The question to ask.
            agent_name: Display name (e.g., '@duc').
            agent_role: Role name (e.g., 'architect').

        Returns:
            Formatted prompt string.
        """
        context_section = ""
        if question.context:
            context_section = f"Context: {question.context}"

        options_section = ""
        if question.options:
            options_section = "Options:\n" + "\n".join(f"  - {opt}" for opt in question.options)

        return KNOWLEDGE_AGENT_PROMPT.format(
            agent_name=agent_name,
            agent_role=agent_role.title(),
            question=question.question,
            context_section=context_section,
            options_section=options_section,
        )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from response text.

        Handles cases where JSON is wrapped in markdown code blocks.

        Args:
            text: Raw response text.

        Returns:
            Parsed JSON data.

        Raises:
            json.JSONDecodeError: If no valid JSON found.
        """
        # Try direct parse first
        try:
            result: dict[str, Any] = json.loads(text)
            return result
        except json.JSONDecodeError:
            pass

        # Try to find JSON in code blocks
        import re

        json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            result = json.loads(match.group(1))
            return result

        # Try to find raw JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
            return result

        raise json.JSONDecodeError("No JSON found in response", text, 0)
