"""Contract tests for POST /invoke endpoint."""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestInvokeContract:
    """Contract tests for /invoke endpoint."""

    async def test_invoke_returns_200_with_valid_request(
        self,
        test_client: AsyncClient,
        sample_invoke_request: dict[str, Any],
    ) -> None:
        """POST /invoke returns 200 with valid request."""
        response = await test_client.post(
            "/invoke",
            json=sample_invoke_request,
        )

        assert response.status_code == 200

    async def test_invoke_response_contains_required_fields(
        self,
        test_client: AsyncClient,
        sample_invoke_request: dict[str, Any],
    ) -> None:
        """Response contains all required fields."""
        response = await test_client.post(
            "/invoke",
            json=sample_invoke_request,
        )
        data = response.json()

        assert "success" in data
        assert "result" in data
        assert "confidence" in data

        assert isinstance(data["success"], bool)
        assert isinstance(data["confidence"], int)
        assert 0 <= data["confidence"] <= 100

    async def test_invoke_returns_400_for_unknown_topic(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke returns 400 for unknown topic."""
        response = await test_client.post(
            "/invoke",
            json={
                "topic": "unknown_topic",
                "context": {"question": "Test question"},
            },
        )

        assert response.status_code == 400

    async def test_invoke_returns_422_for_missing_topic(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke returns 422 when topic is missing."""
        response = await test_client.post(
            "/invoke",
            json={
                "context": {"question": "Test question"},
            },
        )

        assert response.status_code == 422

    async def test_invoke_accepts_all_supported_topics(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /invoke accepts all supported topics."""
        topics = ["testing", "edge_cases", "qa_review"]

        for topic in topics:
            response = await test_client.post(
                "/invoke",
                json={
                    "topic": topic,
                    "context": {"question": f"Test question for {topic}"},
                },
            )

            assert response.status_code == 200, f"Failed for topic: {topic}"
