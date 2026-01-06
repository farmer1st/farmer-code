"""Contract tests for POST /invoke/{agent} endpoint.

These tests verify the API contract per contracts/agent-hub.yaml.
"""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.contract
class TestInvokeAgentContract:
    """Contract tests for /invoke/{agent} endpoint."""

    async def test_invoke_agent_returns_200_with_valid_request(
        self,
        test_client: AsyncClient,
        sample_invoke_request: dict[str, Any],
    ) -> None:
        """POST /invoke/{agent} returns 200 with valid request."""
        response = await test_client.post(
            "/invoke/baron",
            json=sample_invoke_request,
        )

        assert response.status_code == 200

    async def test_invoke_agent_response_contains_required_fields(
        self,
        test_client: AsyncClient,
        sample_invoke_request: dict[str, Any],
    ) -> None:
        """Response contains all required fields per contract."""
        response = await test_client.post(
            "/invoke/baron",
            json=sample_invoke_request,
        )
        data = response.json()

        # Required fields from agent-hub.yaml InvokeResponse
        assert "success" in data
        assert "result" in data
        assert "confidence" in data

        # success is boolean
        assert isinstance(data["success"], bool)

        # confidence is 0-100
        assert isinstance(data["confidence"], int)
        assert 0 <= data["confidence"] <= 100

    async def test_invoke_agent_returns_404_for_unknown_agent(
        self,
        test_client: AsyncClient,
        sample_invoke_request: dict[str, Any],
    ) -> None:
        """POST /invoke/{agent} returns 404 for unknown agent."""
        response = await test_client.post(
            "/invoke/unknown_agent",
            json=sample_invoke_request,
        )

        assert response.status_code == 404

    async def test_invoke_agent_returns_400_for_missing_workflow_type(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke/{agent} returns 422 when workflow_type is missing (Pydantic validation)."""
        response = await test_client.post(
            "/invoke/baron",
            json={
                "context": {"feature_description": "test"},
            },
        )

        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422

    async def test_invoke_agent_returns_400_for_missing_context(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke/{agent} returns 422 when context is missing (Pydantic validation)."""
        response = await test_client.post(
            "/invoke/baron",
            json={
                "workflow_type": "specify",
            },
        )

        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422

    async def test_invoke_agent_error_response_format(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Error response follows contract format."""
        response = await test_client.post(
            "/invoke/unknown_agent",
            json={
                "workflow_type": "specify",
                "context": {"feature_description": "test"},
            },
        )

        assert response.status_code == 404
        data = response.json()

        # Error response format per agent-hub.yaml (FastAPI wraps in detail)
        assert "detail" in data
        assert "error" in data["detail"]
        assert "code" in data["detail"]["error"]
        assert "message" in data["detail"]["error"]

    async def test_invoke_agent_accepts_optional_session_id(
        self,
        test_client: AsyncClient,
        sample_invoke_request: dict[str, Any],
    ) -> None:
        """POST /invoke/{agent} accepts optional session_id."""
        request = {
            **sample_invoke_request,
            "session_id": "550e8400-e29b-41d4-a716-446655440000",
        }
        response = await test_client.post("/invoke/baron", json=request)

        assert response.status_code == 200
