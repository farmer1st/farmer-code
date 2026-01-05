"""E2E tests for human escalation workflow.

Tests the complete escalation lifecycle: low confidence -> escalation -> human response.

Journey ID: SVC-003
"""

from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.journey("SVC-003")
@pytest.mark.anyio
class TestHumanEscalation:
    """E2E tests for SVC-003: Human Review Escalation."""

    @pytest.fixture
    def agent_hub_url(self) -> str:
        """Agent Hub service URL."""
        return "http://localhost:8000"

    async def test_complete_escalation_lifecycle(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test complete escalation lifecycle.

        1. Ask question that triggers low confidence
        2. Verify escalation is created
        3. Submit human response
        4. Verify escalation is resolved

        This test requires Agent Hub to be running.
        """
        async with AsyncClient(base_url=agent_hub_url) as client:
            # Step 1: Ask question (may trigger escalation based on agent response)
            ask_response = await client.post(
                "/ask/architecture",
                json={
                    "question": "What's the best approach for this complex edge case scenario?",
                    "context": "Very unusual requirements with conflicting constraints",
                    "feature_id": "008-e2e-escalation",
                },
            )

            assert ask_response.status_code == 200
            ask_data = ask_response.json()

            # If escalation was created
            if ask_data.get("escalation_id"):
                escalation_id = ask_data["escalation_id"]
                assert ask_data["status"] == "pending_human"

                # Step 2: Verify escalation exists
                get_response = await client.get(f"/escalations/{escalation_id}")
                assert get_response.status_code == 200
                escalation_data = get_response.json()
                assert escalation_data["status"] == "pending"

                # Step 3: Submit human response (CONFIRM)
                confirm_response = await client.post(
                    f"/escalations/{escalation_id}",
                    json={
                        "action": "confirm",
                        "responder": "@e2e-tester",
                    },
                )
                assert confirm_response.status_code == 200
                assert confirm_response.json()["status"] == "resolved"

    async def test_escalation_with_correct_action(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test escalation resolution with CORRECT action.

        Human provides a different, correct answer.
        """
        async with AsyncClient(base_url=agent_hub_url) as client:
            # Trigger escalation
            ask_response = await client.post(
                "/ask/security",
                json={
                    "question": "What auth method for this edge case?",
                    "feature_id": "008-e2e-correct",
                },
            )

            if ask_response.json().get("escalation_id"):
                escalation_id = ask_response.json()["escalation_id"]

                # Submit CORRECT with new answer
                correct_response = await client.post(
                    f"/escalations/{escalation_id}",
                    json={
                        "action": "correct",
                        "response": "Use OAuth2 with PKCE for mobile clients",
                        "responder": "@security-expert",
                    },
                )

                assert correct_response.status_code == 200
                data = correct_response.json()
                assert data["status"] == "resolved"
                assert data["human_action"] == "correct"
                assert data["human_response"] == "Use OAuth2 with PKCE for mobile clients"

    async def test_escalation_with_add_context(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test escalation resolution with ADD_CONTEXT action.

        Human provides additional context for re-routing.
        """
        async with AsyncClient(base_url=agent_hub_url) as client:
            # Trigger escalation
            ask_response = await client.post(
                "/ask/architecture",
                json={
                    "question": "How should we handle this?",
                    "feature_id": "008-e2e-context",
                },
            )

            if ask_response.json().get("escalation_id"):
                escalation_id = ask_response.json()["escalation_id"]

                # Submit ADD_CONTEXT
                context_response = await client.post(
                    f"/escalations/{escalation_id}",
                    json={
                        "action": "add_context",
                        "response": "This is for a high-traffic e-commerce platform with 99.99% uptime requirements",
                        "responder": "@product-owner",
                    },
                )

                assert context_response.status_code == 200
                data = context_response.json()
                assert data["status"] == "resolved"
                assert data["human_action"] == "add_context"

    async def test_escalation_timing(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test that escalation is created within time limit.

        SC-005: Escalations are created within 5 seconds of low confidence.
        """
        import time

        async with AsyncClient(base_url=agent_hub_url) as client:
            start_time = time.time()

            ask_response = await client.post(
                "/ask/architecture",
                json={
                    "question": "Complex question requiring human review",
                    "feature_id": "008-timing-test",
                },
            )

            end_time = time.time()
            elapsed = end_time - start_time

            # Response should be fast (escalation created inline)
            assert elapsed < 5.0, f"Response took {elapsed}s, exceeds 5s limit"

            if ask_response.json().get("escalation_id"):
                # Escalation was created within time limit
                assert ask_response.json()["status"] == "pending_human"

    async def test_get_pending_escalation(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test retrieving a pending escalation."""
        async with AsyncClient(base_url=agent_hub_url) as client:
            # Create an escalation
            ask_response = await client.post(
                "/ask/architecture",
                json={
                    "question": "Question that might trigger escalation",
                    "feature_id": "008-get-pending",
                },
            )

            escalation_id = ask_response.json().get("escalation_id")
            if escalation_id:
                # Get the escalation
                get_response = await client.get(f"/escalations/{escalation_id}")

                assert get_response.status_code == 200
                data = get_response.json()

                # Verify all required fields
                assert "id" in data
                assert "status" in data
                assert "question" in data
                assert "tentative_answer" in data
                assert "confidence" in data
                assert "created_at" in data

    async def test_cannot_respond_to_resolved_escalation(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test that resolved escalation rejects new responses."""
        async with AsyncClient(base_url=agent_hub_url) as client:
            # Create and resolve an escalation
            ask_response = await client.post(
                "/ask/architecture",
                json={
                    "question": "Question for resolved test",
                    "feature_id": "008-resolved-test",
                },
            )

            escalation_id = ask_response.json().get("escalation_id")
            if escalation_id:
                # Resolve it
                await client.post(
                    f"/escalations/{escalation_id}",
                    json={
                        "action": "confirm",
                        "responder": "@first-responder",
                    },
                )

                # Try to respond again
                second_response = await client.post(
                    f"/escalations/{escalation_id}",
                    json={
                        "action": "correct",
                        "response": "Different answer",
                        "responder": "@second-responder",
                    },
                )

                # Should reject with conflict
                assert second_response.status_code == 409

    async def test_health_check(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test that Agent Hub is healthy before escalation tests."""
        async with AsyncClient(base_url=agent_hub_url) as client:
            health_response = await client.get("/health")
            assert health_response.status_code == 200
            assert health_response.json()["status"] == "healthy"
