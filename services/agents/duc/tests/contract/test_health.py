"""Contract tests for GET /health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestHealthContract:
    """Contract tests for /health endpoint."""

    async def test_health_returns_200(
        self,
        test_client: AsyncClient,
    ) -> None:
        """GET /health returns 200."""
        response = await test_client.get("/health")

        assert response.status_code == 200

    async def test_health_contains_required_fields(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health response contains required fields."""
        response = await test_client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "agent_name" in data

        assert data["status"] == "healthy"
        assert data["agent_name"] == "duc"

    async def test_health_includes_capabilities(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health response includes capabilities."""
        response = await test_client.get("/health")
        data = response.json()

        assert "capabilities" in data
        assert "topics" in data["capabilities"]
        assert "architecture" in data["capabilities"]["topics"]
