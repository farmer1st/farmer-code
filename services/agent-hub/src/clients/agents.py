"""HTTP client for Agent Services.

This module provides HTTP client for communicating with agent services
(Baron, Duc, Marie, etc.).
"""

from typing import Any
from uuid import UUID

import httpx


class AgentServiceError(Exception):
    """Error communicating with agent service."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        code: str = "AGENT_ERROR",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class AgentServiceClient:
    """HTTP client for agent service communication.

    Example:
        async with AgentServiceClient("http://baron:8000") as client:
            response = await client.invoke(
                workflow_type="specify",
                context={"feature_description": "Add auth"}
            )
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 300.0,
        agent_name: str | None = None,
    ) -> None:
        """Initialize agent client.

        Args:
            base_url: Agent service URL (e.g., http://baron:8000)
            timeout: Request timeout in seconds
            agent_name: Optional agent name for logging
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.agent_name = agent_name or "unknown"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AgentServiceClient":
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

    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client, ensuring it's initialized."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client

    async def invoke(
        self,
        workflow_type: str,
        context: dict[str, Any],
        parameters: dict[str, Any] | None = None,
        session_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Invoke the agent with a request.

        Args:
            workflow_type: Type of workflow (e.g., specify, plan, tasks)
            context: Context for the agent
            parameters: Additional parameters
            session_id: Session ID for multi-turn conversations

        Returns:
            Response dict with success, result, confidence, metadata

        Raises:
            AgentServiceError: If request fails
        """
        request_data = {
            "workflow_type": workflow_type,
            "context": context,
            "parameters": parameters or {},
        }
        if session_id:
            request_data["session_id"] = str(session_id)

        try:
            response = await self.client.post("/invoke", json=request_data)

            if response.status_code >= 400:
                error_data = response.json()
                error = error_data.get("error", {})
                raise AgentServiceError(
                    error.get("message", f"Request failed: {response.status_code}"),
                    status_code=response.status_code,
                    code=error.get("code", "AGENT_ERROR"),
                )

            return response.json()

        except httpx.RequestError as e:
            raise AgentServiceError(f"Request failed: {e}") from e

    async def health(self) -> dict[str, Any]:
        """Check agent health.

        Returns:
            Health response dict

        Raises:
            AgentServiceError: If health check fails
        """
        try:
            response = await self.client.get("/health")

            if response.status_code >= 400:
                raise AgentServiceError(
                    f"Health check failed: {response.status_code}",
                    status_code=response.status_code,
                )

            return response.json()

        except httpx.RequestError as e:
            raise AgentServiceError(f"Health check failed: {e}") from e


# Agent client pool for reuse
_agent_clients: dict[str, AgentServiceClient] = {}


async def get_agent_client(
    agent_name: str,
    base_url: str,
) -> AgentServiceClient:
    """Get or create an agent client.

    Note: This creates a new client each time. In production,
    you'd want connection pooling.

    Args:
        agent_name: Agent name for identification
        base_url: Agent service URL

    Returns:
        AgentServiceClient instance
    """
    return AgentServiceClient(base_url, agent_name=agent_name)
