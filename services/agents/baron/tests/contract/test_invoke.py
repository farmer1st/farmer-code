"""Contract tests for POST /invoke endpoint.

These tests verify the API contract per contracts/agent-service.yaml.
"""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.contract
class TestInvokeContract:
    """Contract tests for /invoke endpoint."""

    async def test_invoke_returns_200_with_valid_request(
        self,
        test_client: AsyncClient,
        sample_invoke_request: dict[str, Any],
    ) -> None:
        """POST /invoke returns 200 with valid request."""
        response = await test_client.post("/invoke", json=sample_invoke_request)

        assert response.status_code == 200

    async def test_invoke_response_contains_required_fields(
        self,
        test_client: AsyncClient,
        sample_invoke_request: dict[str, Any],
    ) -> None:
        """Response contains all required fields per contract."""
        response = await test_client.post("/invoke", json=sample_invoke_request)
        data = response.json()

        # Required fields from agent-service.yaml InvokeResponse
        assert "success" in data
        assert "result" in data
        assert "confidence" in data
        assert "metadata" in data

        # success is boolean
        assert isinstance(data["success"], bool)

        # confidence is 0-100
        assert isinstance(data["confidence"], int)
        assert 0 <= data["confidence"] <= 100

        # metadata has required fields
        assert "duration_ms" in data["metadata"]
        assert "model_used" in data["metadata"]

    async def test_invoke_returns_400_for_missing_workflow_type(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke returns 400 when workflow_type is missing."""
        response = await test_client.post(
            "/invoke",
            json={
                "context": {"feature_description": "test"},
            },
        )

        assert response.status_code == 400

    async def test_invoke_returns_400_for_missing_context(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke returns 400 when context is missing."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
            },
        )

        assert response.status_code == 400

    async def test_invoke_returns_400_for_unknown_workflow_type(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke returns 400 for unknown workflow type."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "unknown_workflow",
                "context": {"feature_description": "test"},
            },
        )

        assert response.status_code == 400

    async def test_invoke_error_response_format(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Error response follows contract format."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                # Missing required context
            },
        )

        assert response.status_code == 400
        data = response.json()

        # Error response format per agent-service.yaml
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

    async def test_invoke_accepts_optional_parameters(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke accepts optional parameters field."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {"feature_description": "test feature"},
                "parameters": {"priority": "P1", "output_format": "markdown"},
            },
        )

        assert response.status_code == 200

    async def test_invoke_accepts_optional_session_id(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke accepts optional session_id field."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {"feature_description": "test feature"},
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
            },
        )

        assert response.status_code == 200
