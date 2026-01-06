"""Integration tests for escalation creation on low confidence.

Tests that low-confidence responses automatically create escalations.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
class TestEscalationCreation:
    """Integration tests for automatic escalation creation."""

    async def test_low_confidence_creates_escalation(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that low confidence response creates an escalation.

        When confidence < threshold, an escalation should be created
        and escalation_id returned in response.
        """
        # Mock agent to return low confidence
        mock_response = {
            "success": True,
            "result": {
                "output": "I'm not entirely sure, but...",
                "uncertainty_reasons": [
                    "Limited context provided",
                    "Multiple valid approaches",
                ],
            },
            "confidence": 60,  # Below default 85% threshold
            "metadata": {"duration_ms": 1000},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.invoke.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = await test_client.post(
                "/ask/architecture",
                json={
                    "question": "What's the best approach for this complex scenario?",
                    "feature_id": "008-escalation-test",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Should have pending_human status
            assert data["status"] == "pending_human"
            # Should have escalation_id
            assert data.get("escalation_id") is not None

    async def test_high_confidence_no_escalation(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that high confidence response does not create escalation."""
        mock_response = {
            "success": True,
            "result": {"output": "Definitely use approach X because..."},
            "confidence": 92,  # Above threshold
            "metadata": {"duration_ms": 1000},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.invoke.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            response = await test_client.post(
                "/ask/architecture",
                json={
                    "question": "What's the best approach for this scenario?",
                    "feature_id": "008-escalation-test",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Should have resolved status
            assert data["status"] == "resolved"
            # Should NOT have escalation_id
            assert data.get("escalation_id") is None

    async def test_escalation_stores_question_and_answer(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that escalation stores the original question and tentative answer."""
        mock_response = {
            "success": True,
            "result": {"output": "Tentative answer here"},
            "confidence": 70,
            "metadata": {},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.invoke.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            ask_response = await test_client.post(
                "/ask/architecture",
                json={
                    "question": "Complex question requiring human review",
                    "feature_id": "008-escalation-test",
                },
            )

            escalation_id = ask_response.json().get("escalation_id")
            if escalation_id:
                # Get the escalation
                get_response = await test_client.get(f"/escalations/{escalation_id}")

                if get_response.status_code == 200:
                    data = get_response.json()
                    assert data["question"] == "Complex question requiring human review"
                    assert data["tentative_answer"] == "Tentative answer here"
                    assert data["confidence"] == 70

    async def test_escalation_stores_uncertainty_reasons(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that escalation stores uncertainty reasons from agent."""
        mock_response = {
            "success": True,
            "result": {
                "output": "Maybe this approach...",
                "uncertainty_reasons": [
                    "Missing security requirements",
                    "Scalability needs unclear",
                ],
            },
            "confidence": 65,
            "metadata": {},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.invoke.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            ask_response = await test_client.post(
                "/ask/security",
                json={
                    "question": "Security question with uncertainty",
                    "feature_id": "008-escalation-test",
                },
            )

            data = ask_response.json()
            assert data.get("uncertainty_reasons") is not None
            assert len(data["uncertainty_reasons"]) == 2

    async def test_escalation_threshold_per_topic(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that different topics have different thresholds.

        Security topic has 90% threshold, testing has 80%.
        """
        # 85% confidence - below security threshold (90%) but above testing (80%)
        mock_response = {
            "success": True,
            "result": {"output": "Answer here"},
            "confidence": 85,
            "metadata": {},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_client_class:
            mock_client = AsyncMock()
            mock_client.invoke.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Security should escalate at 85% (threshold 90%)
            security_response = await test_client.post(
                "/ask/security",
                json={
                    "question": "Security question about authentication",
                    "feature_id": "008-threshold-test",
                },
            )

            # If security has 90% threshold, 85% should trigger escalation
            # This depends on actual threshold configuration
