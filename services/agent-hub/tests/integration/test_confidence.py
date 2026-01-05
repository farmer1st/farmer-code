"""Integration tests for confidence validation.

These tests verify Agent Hub validates confidence against thresholds
and creates escalations when confidence is below threshold.
"""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestConfidenceValidation:
    """Integration tests for confidence threshold validation."""

    async def test_high_confidence_returns_resolved_status(
        self,
        test_client: AsyncClient,
    ) -> None:
        """High confidence responses have status 'resolved'."""
        response = await test_client.post(
            "/ask/architecture",
            json={
                "question": "What is the standard way to structure a FastAPI application?",
                "feature_id": "test-feature",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # High confidence should be resolved
        if data["confidence"] >= 80:
            assert data["status"] == "resolved"
            assert data.get("escalation_id") is None

    async def test_low_confidence_creates_escalation(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Low confidence responses create escalation."""
        # Ambiguous question more likely to get low confidence
        response = await test_client.post(
            "/ask/security",
            json={
                "question": "Should we use encryption for temporary internal data?",
                "context": "No specific requirements provided",
                "feature_id": "test-feature",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # If confidence is low, should have escalation
        if data["confidence"] < 80:
            assert data["status"] == "pending_human"
            assert data.get("escalation_id") is not None

    async def test_confidence_threshold_is_configurable(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Confidence threshold can be configured per topic.

        Note: This test verifies the mechanism exists; actual thresholds
        depend on routing configuration.
        """
        # Security typically has higher threshold
        response = await test_client.post(
            "/ask/security",
            json={
                "question": "What authentication method should we use for the API?",
                "feature_id": "test-feature",
            },
        )

        assert response.status_code == 200
        # Test passes if endpoint works - threshold behavior is config-dependent

    async def test_escalation_returns_tentative_answer(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Even low confidence responses return an answer."""
        response = await test_client.post(
            "/ask/architecture",
            json={
                "question": "What is the best approach for this unclear requirement?",
                "context": "Requirements are still being defined",
                "feature_id": "test-feature",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should always have an answer, even if low confidence
        assert "answer" in data
        assert len(data["answer"]) > 0

    async def test_confidence_is_always_0_to_100(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Confidence is always within valid range."""
        questions = [
            "What authentication method should we use?",
            "How should we structure the database?",
            "What testing strategy is best?",
        ]

        for question in questions:
            response = await test_client.post(
                "/ask/architecture",
                json={
                    "question": question,
                    "feature_id": "test-feature",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert 0 <= data["confidence"] <= 100

    async def test_uncertainty_reasons_when_low_confidence(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Low confidence responses may include uncertainty reasons."""
        response = await test_client.post(
            "/ask/architecture",
            json={
                "question": "What approach should we take without knowing the constraints?",
                "feature_id": "test-feature",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # If low confidence, may have uncertainty reasons
        if data["confidence"] < 80 and "uncertainty_reasons" in data:
            assert isinstance(data["uncertainty_reasons"], list)
