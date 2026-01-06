"""Contract tests for POST /sessions endpoint.

Tests the create session API contract per contracts/agent-hub.yaml.
"""


import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.anyio
class TestCreateSession:
    """Contract tests for POST /sessions endpoint."""

    async def test_create_session_success(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test successful session creation.

        Contract: POST /sessions returns 201 with SessionResponse.
        """
        response = await test_client.post(
            "/sessions",
            json={
                "agent_id": "@baron",
                "feature_id": "008-test-feature",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Required fields per contract
        assert "id" in data
        assert data["agent_id"] == "@baron"
        assert data["status"] == "active"
        assert "created_at" in data

    async def test_create_session_minimal(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test session creation with minimal required fields.

        Contract: Only agent_id is required, feature_id is optional.
        """
        response = await test_client.post(
            "/sessions",
            json={
                "agent_id": "@duc",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["agent_id"] == "@duc"
        assert data.get("feature_id") is None

    async def test_create_session_missing_agent_id(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test session creation with missing agent_id.

        Contract: agent_id is required, missing returns 400/422.
        """
        response = await test_client.post(
            "/sessions",
            json={
                "feature_id": "008-test",
            },
        )

        assert response.status_code in [400, 422]

    async def test_create_session_returns_uuid(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that session creation returns valid UUID.

        Contract: id must be a valid UUID.
        """
        response = await test_client.post(
            "/sessions",
            json={
                "agent_id": "@baron",
            },
        )

        assert response.status_code == 201
        data = response.json()

        from uuid import UUID

        try:
            UUID(data["id"])
        except ValueError:
            pytest.fail(f"id '{data['id']}' is not a valid UUID")

    async def test_create_session_includes_timestamps(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that session includes proper timestamps.

        Contract: created_at and updated_at are included.
        """
        response = await test_client.post(
            "/sessions",
            json={
                "agent_id": "@baron",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert "created_at" in data
        assert data["created_at"] is not None

    async def test_create_multiple_sessions(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that multiple sessions can be created.

        Each session should have unique ID.
        """
        response1 = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        response2 = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )

        assert response1.status_code == 201
        assert response2.status_code == 201

        # IDs should be unique
        assert response1.json()["id"] != response2.json()["id"]
