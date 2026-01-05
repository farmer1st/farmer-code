"""HTTP client for Orchestrator Service."""

from typing import Any
from uuid import UUID

import httpx

from contracts.models.agent import ErrorResponse
from contracts.models.workflow import (
    AdvanceWorkflowRequest,
    CreateWorkflowRequest,
    WorkflowResponse,
    WorkflowType,
)


class OrchestratorClientError(Exception):
    """Error communicating with Orchestrator service."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OrchestratorClient:
    """HTTP client for Orchestrator service communication.

    Example:
        client = OrchestratorClient("http://orchestrator:8000")
        workflow = await client.create_workflow(
            workflow_type=WorkflowType.SPECIFY,
            feature_description="Add OAuth2 authentication"
        )
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 300.0,
    ) -> None:
        """Initialize Orchestrator client.

        Args:
            base_url: Orchestrator service URL (e.g., http://orchestrator:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OrchestratorClient":
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

    async def create_workflow(
        self,
        workflow_type: WorkflowType,
        feature_description: str,
        context: dict[str, Any] | None = None,
    ) -> WorkflowResponse:
        """Create and start a new workflow.

        Args:
            workflow_type: Type of workflow (specify, plan, tasks, implement)
            feature_description: Description of the feature
            context: Additional context for the workflow

        Returns:
            WorkflowResponse with workflow details

        Raises:
            OrchestratorClientError: If request fails
        """
        request = CreateWorkflowRequest(
            workflow_type=workflow_type,
            feature_description=feature_description,
            context=context,
        )

        try:
            response = await self.client.post(
                "/workflows",
                json=request.model_dump(mode="json"),
            )

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise OrchestratorClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return WorkflowResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise OrchestratorClientError(f"Request failed: {e}") from e

    async def get_workflow(
        self,
        workflow_id: UUID,
    ) -> WorkflowResponse:
        """Get workflow status.

        Args:
            workflow_id: Workflow identifier

        Returns:
            WorkflowResponse with current status

        Raises:
            OrchestratorClientError: If request fails
        """
        try:
            response = await self.client.get(f"/workflows/{workflow_id}")

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise OrchestratorClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return WorkflowResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise OrchestratorClientError(f"Request failed: {e}") from e

    async def advance_workflow(
        self,
        workflow_id: UUID,
        trigger: str,
        phase_result: dict[str, Any] | None = None,
    ) -> WorkflowResponse:
        """Advance workflow to next phase.

        Args:
            workflow_id: Workflow identifier
            trigger: What triggered the advancement (agent_complete, human_approved)
            phase_result: Output from the completed phase

        Returns:
            WorkflowResponse with updated status

        Raises:
            OrchestratorClientError: If request fails
        """
        request = AdvanceWorkflowRequest(
            trigger=trigger,
            phase_result=phase_result,
        )

        try:
            response = await self.client.post(
                f"/workflows/{workflow_id}/advance",
                json=request.model_dump(mode="json"),
            )

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise OrchestratorClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return WorkflowResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise OrchestratorClientError(f"Request failed: {e}") from e

    async def health(self) -> dict[str, Any]:
        """Check orchestrator health.

        Returns:
            Health response dict

        Raises:
            OrchestratorClientError: If health check fails
        """
        try:
            response = await self.client.get("/health")

            if response.status_code >= 400:
                raise OrchestratorClientError(
                    f"Health check failed: {response.status_code}",
                    status_code=response.status_code,
                )

            return response.json()  # type: ignore[no-any-return]

        except httpx.RequestError as e:
            raise OrchestratorClientError(f"Health check failed: {e}") from e
