"""Contract tests for GET /sessions/{id} endpoint.

Tests the get session API contract per contracts/agent-hub.yaml.
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.anyio
class TestGetSession:
    """Contract tests for GET /sessions/{id} endpoint."""

    async def test_get_session_success(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test successful session retrieval.

        Contract: GET /sessions/{id} returns 200 with SessionWithMessagesResponse.
        """
        # First create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron", "feature_id": "008-test"},
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["id"]

        # Then retrieve it
        response = await test_client.get(f"/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert data["id"] == session_id
        assert data["agent_id"] == "@baron"
        assert data["status"] == "active"
        assert "created_at" in data
        assert "messages" in data

    async def test_get_session_not_found(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test session retrieval with non-existent ID.

        Contract: Non-existent session returns 404 with ErrorResponse.
        """
        non_existent_id = str(uuid4())

        response = await test_client.get(f"/sessions/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        # FastAPI wraps errors in detail
        assert "detail" in data
        assert "error" in data["detail"]
        assert "code" in data["detail"]["error"]

    async def test_get_session_invalid_uuid(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test session retrieval with invalid UUID format.

        Contract: Invalid UUID returns 400/422.
        """
        response = await test_client.get("/sessions/not-a-uuid")

        assert response.status_code in [400, 422]

    async def test_get_session_includes_messages(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that session response includes messages array.

        Contract: SessionWithMessagesResponse includes messages array.
        """
        # Create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        session_id = create_response.json()["id"]

        # Get session
        response = await test_client.get(f"/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()

        # Messages should be an array (possibly empty)
        assert "messages" in data
        assert isinstance(data["messages"], list)

    async def test_get_session_messages_format(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that messages have correct format.

        Contract: Each message has id, role, content, created_at.
        """
        # Create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        session_id = create_response.json()["id"]

        # Use the session with an ask request to add messages
        await test_client.post(
            "/ask/architecture",
            json={
                "question": "What design pattern should I use for this service?",
                "feature_id": "008-test",
                "session_id": session_id,
            },
        )

        # Get session with messages
        response = await test_client.get(f"/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()

        # If there are messages, verify format
        if data["messages"]:
            message = data["messages"][0]
            assert "id" in message
            assert "role" in message
            assert message["role"] in ["user", "assistant", "human"]
            assert "content" in message
            assert "created_at" in message
