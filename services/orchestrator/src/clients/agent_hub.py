"""Agent Hub client for Orchestrator service.

All agent invocations go through Agent Hub, never directly to agents.
"""

import os
from typing import Any
from uuid import UUID

import httpx


class AgentHubError(Exception):
    """Error from Agent Hub service."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class AgentHubClient:
    """HTTP client for Agent Hub service."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        """Initialize Agent Hub client.

        Args:
            base_url: Agent Hub service URL (default from env)
            timeout: Request timeout in seconds (default 5 minutes)
        """
        self.base_url = base_url or os.environ.get(
            "AGENT_HUB_URL",
            "http://localhost:8000",
        )
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AgentHubClient":
        """Enter async context."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def invoke_agent(
        self,
        agent: str,
        workflow_type: str,
        context: dict[str, Any],
        parameters: dict[str, Any] | None = None,
        session_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Invoke a specific agent via Agent Hub.

        Args:
            agent: Agent name (e.g., "baron", "duc")
            workflow_type: Type of workflow
            context: Context for the agent
            parameters: Optional additional parameters
            session_id: Optional session ID

        Returns:
            Agent response dict

        Raises:
            AgentHubError: On invocation failure
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        request_data: dict[str, Any] = {
            "workflow_type": workflow_type,
            "context": context,
            "parameters": parameters or {},
        }
        if session_id:
            request_data["session_id"] = str(session_id)

        try:
            response = await self._client.post(
                f"/invoke/{agent}",
                json=request_data,
            )

            if response.status_code == 200:
                return response.json()

            # Handle error responses
            error_data = response.json()
            error = error_data.get("error", {})
            raise AgentHubError(
                message=error.get("message", "Unknown error"),
                status_code=response.status_code,
                code=error.get("code"),
            )

        except httpx.RequestError as e:
            raise AgentHubError(
                message=f"Failed to connect to Agent Hub: {e}",
                code="CONNECTION_ERROR",
            ) from e

    async def ask_expert(
        self,
        topic: str,
        question: str,
        feature_id: str,
        context: str | None = None,
        session_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Ask an expert via Agent Hub.

        Args:
            topic: Topic for routing (e.g., "architecture", "security")
            question: Question to ask
            feature_id: Feature ID for logging
            context: Optional additional context
            session_id: Optional session ID

        Returns:
            Expert response dict

        Raises:
            AgentHubError: On request failure
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        request_data: dict[str, Any] = {
            "question": question,
            "feature_id": feature_id,
        }
        if context:
            request_data["context"] = context
        if session_id:
            request_data["session_id"] = str(session_id)

        try:
            response = await self._client.post(
                f"/ask/{topic}",
                json=request_data,
            )

            if response.status_code == 200:
                return response.json()

            error_data = response.json()
            error = error_data.get("error", {})
            raise AgentHubError(
                message=error.get("message", "Unknown error"),
                status_code=response.status_code,
                code=error.get("code"),
            )

        except httpx.RequestError as e:
            raise AgentHubError(
                message=f"Failed to connect to Agent Hub: {e}",
                code="CONNECTION_ERROR",
            ) from e

    async def health_check(self) -> dict[str, Any]:
        """Check Agent Hub health.

        Returns:
            Health status dict

        Raises:
            AgentHubError: If health check fails
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        try:
            response = await self._client.get("/health")
            return response.json()
        except httpx.RequestError as e:
            raise AgentHubError(
                message=f"Health check failed: {e}",
                code="HEALTH_CHECK_FAILED",
            ) from e
