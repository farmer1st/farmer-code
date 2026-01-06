"""E2E tests for expert agent consultation.

Journey ID: SVC-002 - Expert Agent Consultation

These tests verify the complete flow of asking an expert question
through Agent Hub, routing to the correct agent, and receiving an answer.

Requires: RUN_E2E_TESTS=1 and services running on localhost.
"""

import os

import pytest
from httpx import AsyncClient

# Skip reason for when services are not running
SKIP_REASON = "Requires RUN_E2E_TESTS=1 and running services"


def _should_skip() -> bool:
    """Check if tests should be skipped."""
    return os.getenv("RUN_E2E_TESTS") != "1"


@pytest.mark.e2e
@pytest.mark.journey("SVC-002")
@pytest.mark.anyio
class TestAgentConsultationE2E:
    """E2E tests for SVC-002: Expert Agent Consultation.

    Goal: Agent Hub routes requests to appropriate agent, validates
    confidence, returns response.

    Independent Test: Have Baron ask an architecture question via Agent Hub,
    verify it routes to correct agent and returns answer.
    """

    @pytest.fixture
    async def hub_client(self) -> AsyncClient:
        """Create client for Agent Hub service.

        In E2E tests, this connects to the actual running service.
        """
        if _should_skip():
            pytest.skip(SKIP_REASON)
        async with AsyncClient(
            base_url="http://localhost:8002",
            timeout=300.0,
        ) as client:
            yield client

    async def test_agent_hub_health_check(
        self,
        hub_client: AsyncClient,
    ) -> None:
        """Agent Hub service responds to health check."""
        response = await hub_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_ask_architecture_question(
        self,
        hub_client: AsyncClient,
    ) -> None:
        """Ask architecture question through Agent Hub.

        This is the primary SVC-002 journey test:
        1. Send question to /ask/architecture
        2. Agent Hub routes to architecture expert
        3. Returns answer with confidence
        """
        response = await hub_client.post(
            "/ask/architecture",
            json={
                "question": "What authentication method should we use for a REST API?",
                "context": "Building a web application with mobile support",
                "feature_id": "008-services-architecture",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify complete response
        assert "answer" in data
        assert len(data["answer"]) > 0
        assert "confidence" in data
        assert 0 <= data["confidence"] <= 100
        assert "status" in data
        assert data["status"] in ["resolved", "pending_human", "needs_reroute"]
        assert "session_id" in data

    async def test_invoke_baron_through_hub(
        self,
        hub_client: AsyncClient,
    ) -> None:
        """Invoke Baron agent through Agent Hub."""
        response = await hub_client.post(
            "/invoke/baron",
            json={
                "workflow_type": "specify",
                "context": {
                    "feature_description": "Add a user profile page",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "result" in data
        assert "confidence" in data

    async def test_routing_to_different_topics(
        self,
        hub_client: AsyncClient,
    ) -> None:
        """Agent Hub routes different topics to appropriate experts."""
        topics_and_questions = [
            ("architecture", "How should we design the API structure?"),
            ("security", "What authentication method is most secure?"),
            ("testing", "What test coverage should we aim for?"),
        ]

        for topic, question in topics_and_questions:
            response = await hub_client.post(
                f"/ask/{topic}",
                json={
                    "question": question,
                    "feature_id": "008-services-architecture",
                },
            )

            # All should succeed (assuming topics are configured)
            assert response.status_code in [200, 404], f"Failed for topic: {topic}"

    async def test_high_confidence_is_resolved(
        self,
        hub_client: AsyncClient,
    ) -> None:
        """High confidence answers have resolved status."""
        response = await hub_client.post(
            "/ask/architecture",
            json={
                "question": "What is the standard REST API response format for errors?",
                "feature_id": "008-services-architecture",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Standard questions should get high confidence
        if data["confidence"] >= 80:
            assert data["status"] == "resolved"

    async def test_low_confidence_triggers_escalation(
        self,
        hub_client: AsyncClient,
    ) -> None:
        """Low confidence answers trigger escalation."""
        response = await hub_client.post(
            "/ask/security",
            json={
                "question": "Should we use encryption for this ambiguous edge case?",
                "context": "Requirements are unclear",
                "feature_id": "008-services-architecture",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # If confidence is low, should be pending human review
        if data["confidence"] < 80:
            assert data["status"] == "pending_human"
            assert "escalation_id" in data

    async def test_session_created_for_ask(
        self,
        hub_client: AsyncClient,
    ) -> None:
        """Ask creates a session for follow-up questions."""
        response = await hub_client.post(
            "/ask/architecture",
            json={
                "question": "What database should we use for this application?",
                "feature_id": "008-services-architecture",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Session should be created
        assert "session_id" in data
        assert data["session_id"] is not None

    async def test_connected_agents_in_health(
        self,
        hub_client: AsyncClient,
    ) -> None:
        """Health check shows connected agents."""
        response = await hub_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Should show connected agents
        if "connected_agents" in data:
            assert isinstance(data["connected_agents"], list)
            assert "baron" in data["connected_agents"]
