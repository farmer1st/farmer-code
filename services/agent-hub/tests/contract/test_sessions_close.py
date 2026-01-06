"""Contract tests for DELETE /sessions/{id} endpoint.

Tests the close session API contract per contracts/agent-hub.yaml.
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.anyio
class TestCloseSession:
    """Contract tests for DELETE /sessions/{id} endpoint."""

    async def test_close_session_success(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test successful session closure.

        Contract: DELETE /sessions/{id} returns 200 with SessionResponse.
        """
        # First create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["id"]

        # Close the session
        response = await test_client.delete(f"/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == session_id
        assert data["status"] == "closed"

    async def test_close_session_not_found(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test session closure with non-existent ID.

        Contract: Non-existent session returns 404 with ErrorResponse.
        """
        non_existent_id = str(uuid4())

        response = await test_client.delete(f"/sessions/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        # FastAPI wraps errors in detail
        assert "detail" in data
        assert "error" in data["detail"]
        assert "code" in data["detail"]["error"]

    async def test_close_session_invalid_uuid(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test session closure with invalid UUID format.

        Contract: Invalid UUID returns 400/422.
        """
        response = await test_client.delete("/sessions/not-a-uuid")

        assert response.status_code in [400, 422]

    async def test_close_session_preserves_history(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that closing session preserves message history.

        Contract: Session history preserved for audit after closure.
        """
        # Create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        session_id = create_response.json()["id"]

        # Close the session
        close_response = await test_client.delete(f"/sessions/{session_id}")
        assert close_response.status_code == 200

        # Session should still be retrievable (for audit)
        get_response = await test_client.get(f"/sessions/{session_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "closed"

    async def test_close_already_closed_session(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test closing an already closed session.

        Should be idempotent or return appropriate error.
        """
        # Create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        session_id = create_response.json()["id"]

        # Close the session twice
        await test_client.delete(f"/sessions/{session_id}")
        response = await test_client.delete(f"/sessions/{session_id}")

        # Should either succeed (idempotent) or return 409 (conflict)
        assert response.status_code in [200, 409]
