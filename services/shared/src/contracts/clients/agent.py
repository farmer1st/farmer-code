"""HTTP client for Agent Services (Baron, Duc, Marie, etc.)."""

from typing import Any
from uuid import UUID

import httpx

from contracts.models.agent import (
    ErrorResponse,
    HealthResponse,
    InvokeRequest,
    InvokeResponse,
)


class AgentClientError(Exception):
    """Error communicating with agent service."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AgentClient:
    """HTTP client for generic agent service communication.

    Example:
        client = AgentClient("http://baron:8000")
        response = await client.invoke(
            workflow_type="specify",
            context={"feature_description": "Add OAuth2"}
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

    async def __aenter__(self) -> "AgentClient":
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
    ) -> InvokeResponse:
        """Invoke the agent with a request.

        Args:
            workflow_type: Type of workflow (e.g., specify, plan, tasks)
            context: Context for the agent
            parameters: Additional parameters
            session_id: Session ID for multi-turn conversations

        Returns:
            InvokeResponse from the agent

        Raises:
            AgentClientError: If request fails
        """
        request = InvokeRequest(
            workflow_type=workflow_type,
            context=context,
            parameters=parameters or {},
            session_id=session_id,
        )

        try:
            response = await self.client.post(
                "/invoke",
                json=request.model_dump(mode="json"),
            )

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise AgentClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return InvokeResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentClientError(f"Request failed: {e}") from e

    async def health(self) -> HealthResponse:
        """Check agent health.

        Returns:
            HealthResponse with agent status

        Raises:
            AgentClientError: If health check fails
        """
        try:
            response = await self.client.get("/health")

            if response.status_code >= 400:
                raise AgentClientError(
                    f"Health check failed: {response.status_code}",
                    status_code=response.status_code,
                )

            return HealthResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentClientError(f"Health check failed: {e}") from e
