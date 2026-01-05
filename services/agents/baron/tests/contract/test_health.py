"""Contract tests for GET /health endpoint.

These tests verify the health check API contract per contracts/agent-service.yaml.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
class TestHealthContract:
    """Contract tests for /health endpoint."""

    async def test_health_returns_200(
        self,
        test_client: AsyncClient,
    ) -> None:
        """GET /health returns 200."""
        response = await test_client.get("/health")

        assert response.status_code == 200

    async def test_health_response_contains_required_fields(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Response contains all required fields per contract."""
        response = await test_client.get("/health")
        data = response.json()

        # Required fields from agent-service.yaml HealthResponse
        assert "status" in data
        assert "version" in data
        assert "agent_name" in data

    async def test_health_status_is_valid_enum(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health status is one of: healthy, degraded, unhealthy."""
        response = await test_client.get("/health")
        data = response.json()

        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    async def test_health_agent_name_is_baron(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Agent name is 'baron' for Baron service."""
        response = await test_client.get("/health")
        data = response.json()

        assert data["agent_name"] == "baron"

    async def test_health_includes_optional_capabilities(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health response may include capabilities."""
        response = await test_client.get("/health")
        data = response.json()

        # capabilities is optional but should be valid if present
        if "capabilities" in data:
            capabilities = data["capabilities"]
            # Check expected capability fields
            if "workflow_types" in capabilities:
                assert isinstance(capabilities["workflow_types"], list)
            if "tools" in capabilities:
                assert isinstance(capabilities["tools"], list)
            if "mcp_servers" in capabilities:
                assert isinstance(capabilities["mcp_servers"], list)
            if "skills" in capabilities:
                assert isinstance(capabilities["skills"], list)

    async def test_health_includes_optional_uptime(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Health response may include uptime_seconds."""
        response = await test_client.get("/health")
        data = response.json()

        # uptime_seconds is optional but should be valid if present
        if "uptime_seconds" in data:
            assert isinstance(data["uptime_seconds"], int)
            assert data["uptime_seconds"] >= 0
