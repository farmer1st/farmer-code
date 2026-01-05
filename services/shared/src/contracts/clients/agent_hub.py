"""HTTP client for Agent Hub Service."""

from typing import Any
from uuid import UUID

import httpx

from contracts.models.agent import ErrorResponse, InvokeRequest, InvokeResponse
from contracts.models.escalation import (
    AskExpertRequest,
    AskExpertResponse,
    EscalationResponse,
    HumanAction,
    SubmitHumanResponseRequest,
)
from contracts.models.session import (
    CreateSessionRequest,
    SessionResponse,
    SessionWithMessagesResponse,
)


class AgentHubClientError(Exception):
    """Error communicating with Agent Hub service."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AgentHubClient:
    """HTTP client for Agent Hub service communication.

    Example:
        client = AgentHubClient("http://agent-hub:8000")
        response = await client.ask_expert(
            topic="architecture",
            question="Which auth method?",
            feature_id="008-services"
        )
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 300.0,
    ) -> None:
        """Initialize Agent Hub client.

        Args:
            base_url: Agent Hub service URL (e.g., http://agent-hub:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
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

    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client, ensuring it's initialized."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client

    # Invoke endpoints

    async def invoke_agent(
        self,
        agent: str,
        workflow_type: str,
        context: dict[str, Any],
        parameters: dict[str, Any] | None = None,
        session_id: UUID | None = None,
    ) -> InvokeResponse:
        """Invoke a specific agent.

        Args:
            agent: Agent name (e.g., baron, duc, marie)
            workflow_type: Type of workflow
            context: Context for the agent
            parameters: Additional parameters
            session_id: Session ID for multi-turn conversations

        Returns:
            InvokeResponse from the agent

        Raises:
            AgentHubClientError: If request fails
        """
        request = InvokeRequest(
            workflow_type=workflow_type,
            context=context,
            parameters=parameters or {},
            session_id=session_id,
        )

        try:
            response = await self.client.post(
                f"/invoke/{agent}",
                json=request.model_dump(mode="json"),
            )

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise AgentHubClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return InvokeResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentHubClientError(f"Request failed: {e}") from e

    # Ask endpoints

    async def ask_expert(
        self,
        topic: str,
        question: str,
        feature_id: str,
        context: str | None = None,
        session_id: UUID | None = None,
    ) -> AskExpertResponse:
        """Ask expert by topic.

        Args:
            topic: Topic for routing (e.g., architecture, security)
            question: Question to ask
            feature_id: Feature ID for logging
            context: Additional context
            session_id: Session ID for multi-turn conversations

        Returns:
            AskExpertResponse with answer and confidence

        Raises:
            AgentHubClientError: If request fails
        """
        request = AskExpertRequest(
            question=question,
            context=context,
            feature_id=feature_id,
            session_id=session_id,
        )

        try:
            response = await self.client.post(
                f"/ask/{topic}",
                json=request.model_dump(mode="json"),
            )

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise AgentHubClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return AskExpertResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentHubClientError(f"Request failed: {e}") from e

    # Session endpoints

    async def create_session(
        self,
        agent_id: str,
        feature_id: str | None = None,
    ) -> SessionResponse:
        """Create a new session.

        Args:
            agent_id: Agent identifier (e.g., @duc)
            feature_id: Feature ID for grouping

        Returns:
            SessionResponse with session details

        Raises:
            AgentHubClientError: If request fails
        """
        request = CreateSessionRequest(
            agent_id=agent_id,
            feature_id=feature_id,
        )

        try:
            response = await self.client.post(
                "/sessions",
                json=request.model_dump(mode="json"),
            )

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise AgentHubClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return SessionResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentHubClientError(f"Request failed: {e}") from e

    async def get_session(
        self,
        session_id: UUID,
    ) -> SessionWithMessagesResponse:
        """Get session with message history.

        Args:
            session_id: Session identifier

        Returns:
            SessionWithMessagesResponse with messages

        Raises:
            AgentHubClientError: If request fails
        """
        try:
            response = await self.client.get(f"/sessions/{session_id}")

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise AgentHubClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return SessionWithMessagesResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentHubClientError(f"Request failed: {e}") from e

    async def close_session(
        self,
        session_id: UUID,
    ) -> SessionResponse:
        """Close a session.

        Args:
            session_id: Session identifier

        Returns:
            SessionResponse with updated status

        Raises:
            AgentHubClientError: If request fails
        """
        try:
            response = await self.client.delete(f"/sessions/{session_id}")

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise AgentHubClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return SessionResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentHubClientError(f"Request failed: {e}") from e

    # Escalation endpoints

    async def get_escalation(
        self,
        escalation_id: UUID,
    ) -> EscalationResponse:
        """Get escalation status.

        Args:
            escalation_id: Escalation identifier

        Returns:
            EscalationResponse with status

        Raises:
            AgentHubClientError: If request fails
        """
        try:
            response = await self.client.get(f"/escalations/{escalation_id}")

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise AgentHubClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return EscalationResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentHubClientError(f"Request failed: {e}") from e

    async def submit_human_response(
        self,
        escalation_id: UUID,
        action: HumanAction,
        responder: str,
        response_text: str | None = None,
    ) -> EscalationResponse:
        """Submit human response to escalation.

        Args:
            escalation_id: Escalation identifier
            action: Action to take (confirm, correct, add_context)
            responder: Identifier of the responder
            response_text: Response text (required for correct)

        Returns:
            EscalationResponse with updated status

        Raises:
            AgentHubClientError: If request fails
        """
        request = SubmitHumanResponseRequest(
            action=action,
            response=response_text,
            responder=responder,
        )

        try:
            response = await self.client.post(
                f"/escalations/{escalation_id}",
                json=request.model_dump(mode="json"),
            )

            if response.status_code >= 400:
                error = ErrorResponse.model_validate(response.json())
                raise AgentHubClientError(
                    f"{error.error.code}: {error.error.message}",
                    status_code=response.status_code,
                )

            return EscalationResponse.model_validate(response.json())

        except httpx.RequestError as e:
            raise AgentHubClientError(f"Request failed: {e}") from e
