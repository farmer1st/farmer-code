"""Contract tests for POST /ask/{topic} endpoint.

These tests verify the API contract per contracts/agent-hub.yaml.
"""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.contract
class TestAskExpertContract:
    """Contract tests for /ask/{topic} endpoint."""

    async def test_ask_expert_returns_200_with_valid_request(
        self,
        test_client: AsyncClient,
        sample_ask_request: dict[str, Any],
    ) -> None:
        """POST /ask/{topic} returns 200 with valid request."""
        response = await test_client.post(
            "/ask/architecture",
            json=sample_ask_request,
        )

        assert response.status_code == 200

    async def test_ask_expert_response_contains_required_fields(
        self,
        test_client: AsyncClient,
        sample_ask_request: dict[str, Any],
    ) -> None:
        """Response contains all required fields per contract."""
        response = await test_client.post(
            "/ask/architecture",
            json=sample_ask_request,
        )
        data = response.json()

        # Required fields from agent-hub.yaml AskExpertResponse
        assert "answer" in data
        assert "confidence" in data
        assert "status" in data
        assert "session_id" in data

        # confidence is 0-100
        assert isinstance(data["confidence"], int)
        assert 0 <= data["confidence"] <= 100

        # status is valid enum
        assert data["status"] in ["resolved", "pending_human", "needs_reroute"]

    async def test_ask_expert_returns_404_for_unknown_topic(
        self,
        test_client: AsyncClient,
        sample_ask_request: dict[str, Any],
    ) -> None:
        """POST /ask/{topic} returns 404 for unknown topic."""
        response = await test_client.post(
            "/ask/unknown_topic",
            json=sample_ask_request,
        )

        assert response.status_code == 404

    async def test_ask_expert_returns_400_for_missing_question(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /ask/{topic} returns 422 when question is missing (Pydantic validation)."""
        response = await test_client.post(
            "/ask/architecture",
            json={
                "feature_id": "test-feature",
            },
        )

        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422

    async def test_ask_expert_returns_400_for_short_question(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /ask/{topic} returns 422 when question is too short (Pydantic validation)."""
        response = await test_client.post(
            "/ask/architecture",
            json={
                "question": "Why?",  # Too short (< 10 chars)
                "feature_id": "test-feature",
            },
        )

        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422

    async def test_ask_expert_returns_400_for_missing_feature_id(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /ask/{topic} returns 422 when feature_id is missing (Pydantic validation)."""
        response = await test_client.post(
            "/ask/architecture",
            json={
                "question": "What authentication method should we use?",
            },
        )

        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422

    async def test_ask_expert_accepts_optional_context(
        self,
        test_client: AsyncClient,
    ) -> None:
        """POST /ask/{topic} accepts optional context."""
        response = await test_client.post(
            "/ask/architecture",
            json={
                "question": "What authentication method should we use?",
                "context": "Building a REST API",
                "feature_id": "test-feature",
            },
        )

        assert response.status_code == 200

    async def test_ask_expert_accepts_optional_session_id(
        self,
        test_client: AsyncClient,
        sample_ask_request: dict[str, Any],
    ) -> None:
        """POST /ask/{topic} accepts optional session_id."""
        # First create a session
        session_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron", "feature_id": "test-feature"},
        )
        assert session_response.status_code == 201
        session_id = session_response.json()["id"]

        # Now use the session_id in the ask request
        request = {
            **sample_ask_request,
            "session_id": session_id,
        }
        response = await test_client.post("/ask/architecture", json=request)

        assert response.status_code == 200

    async def test_ask_expert_low_confidence_includes_escalation_id(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Low confidence response includes escalation_id."""
        # This test may need mocking to force low confidence
        response = await test_client.post(
            "/ask/security",
            json={
                "question": "Should we use encryption for this edge case?",
                "feature_id": "test-feature",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # If confidence is low, escalation_id should be present
        if data["confidence"] < 80:
            assert data["status"] == "pending_human"
            assert data.get("escalation_id") is not None
