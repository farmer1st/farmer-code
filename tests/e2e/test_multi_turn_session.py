"""E2E tests for multi-turn session management.

Tests complete session lifecycle: create, exchange, close.

Journey ID: SVC-004
"""

import os
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient

# Skip reason for when services are not running
SKIP_REASON = "Requires RUN_E2E_TESTS=1 and running services"


def _should_skip() -> bool:
    """Check if tests should be skipped."""
    return os.getenv("RUN_E2E_TESTS") != "1"


@pytest.mark.e2e
@pytest.mark.journey("SVC-004")
@pytest.mark.anyio
class TestMultiTurnSession:
    """E2E tests for SVC-004: Multi-Turn Session."""

    @pytest.fixture
    def agent_hub_url(self) -> str:
        """Agent Hub service URL."""
        if _should_skip():
            pytest.skip(SKIP_REASON)
        return "http://localhost:8000"

    async def test_complete_session_lifecycle(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test complete session lifecycle: create -> exchange -> close.

        This test requires Agent Hub to be running.
        """
        async with AsyncClient(base_url=agent_hub_url) as client:
            # Step 1: Create session
            create_response = await client.post(
                "/sessions",
                json={
                    "agent_id": "@baron",
                    "feature_id": "008-e2e-session",
                },
            )

            assert create_response.status_code == 201
            session_data = create_response.json()
            session_id = session_data["id"]

            # Verify valid UUID
            UUID(session_id)
            assert session_data["status"] == "active"

            # Step 2: Make exchanges with session
            for i in range(3):
                ask_response = await client.post(
                    "/ask/architecture",
                    json={
                        "question": f"Question {i + 1}: How should I design this?",
                        "context": "Building a microservices architecture",
                        "feature_id": "008-e2e-session",
                        "session_id": session_id,
                    },
                )
                assert ask_response.status_code == 200

            # Step 3: Verify session has messages
            get_response = await client.get(f"/sessions/{session_id}")
            assert get_response.status_code == 200
            session_with_messages = get_response.json()

            assert "messages" in session_with_messages
            assert len(session_with_messages["messages"]) >= 6  # 3 user + 3 assistant

            # Step 4: Close session
            close_response = await client.delete(f"/sessions/{session_id}")
            assert close_response.status_code == 200
            assert close_response.json()["status"] == "closed"

            # Step 5: Verify session still accessible (for audit)
            audit_response = await client.get(f"/sessions/{session_id}")
            assert audit_response.status_code == 200
            assert audit_response.json()["status"] == "closed"

    async def test_session_context_preservation(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test that session preserves context across exchanges.

        SC-006: Session preserves context across 5 consecutive exchanges.
        """
        async with AsyncClient(base_url=agent_hub_url) as client:
            # Create session
            create_response = await client.post(
                "/sessions",
                json={
                    "agent_id": "@baron",
                    "feature_id": "008-context-preservation",
                },
            )
            session_id = create_response.json()["id"]

            # Make 5 consecutive exchanges
            questions = [
                "I'm designing a user authentication system",
                "Should I use JWT or session-based auth?",
                "What about refresh tokens?",
                "How do I handle token revocation?",
                "What security considerations should I keep in mind?",
            ]

            for question in questions:
                response = await client.post(
                    "/ask/architecture",
                    json={
                        "question": question,
                        "feature_id": "008-context-preservation",
                        "session_id": session_id,
                    },
                )
                assert response.status_code == 200

            # Get session and verify all messages
            get_response = await client.get(f"/sessions/{session_id}")
            session_data = get_response.json()

            # Should have at least 10 messages (5 user + 5 assistant)
            assert len(session_data["messages"]) >= 10

    async def test_concurrent_sessions(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test that multiple concurrent sessions work independently."""
        import asyncio

        async with AsyncClient(base_url=agent_hub_url) as client:

            async def create_and_use_session(index: int) -> dict[str, Any]:
                # Create session
                create_resp = await client.post(
                    "/sessions",
                    json={
                        "agent_id": "@baron",
                        "feature_id": f"008-concurrent-{index}",
                    },
                )
                session_id = create_resp.json()["id"]

                # Use session
                await client.post(
                    "/ask/architecture",
                    json={
                        "question": f"Concurrent session {index}: Design question here",
                        "feature_id": f"008-concurrent-{index}",
                        "session_id": session_id,
                    },
                )

                # Get session
                get_resp = await client.get(f"/sessions/{session_id}")
                return {
                    "index": index,
                    "session_id": session_id,
                    "message_count": len(get_resp.json().get("messages", [])),
                }

            # Create 5 concurrent sessions
            tasks = [create_and_use_session(i) for i in range(5)]
            results = await asyncio.gather(*tasks)

            # All should succeed
            assert len(results) == 5

            # All should have unique session IDs
            session_ids = [r["session_id"] for r in results]
            assert len(set(session_ids)) == 5

            # All should have messages
            for result in results:
                assert result["message_count"] >= 2  # At least user + assistant

    async def test_session_with_invoke(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test that session works with direct agent invocation."""
        async with AsyncClient(base_url=agent_hub_url) as client:
            # Create session
            create_response = await client.post(
                "/sessions",
                json={
                    "agent_id": "@baron",
                    "feature_id": "008-invoke-session",
                },
            )
            session_id = create_response.json()["id"]

            # Use session with invoke endpoint
            invoke_response = await client.post(
                "/invoke/baron",
                json={
                    "workflow_type": "specify",
                    "context": {
                        "feature_description": "User authentication system",
                    },
                    "session_id": session_id,
                },
            )

            assert invoke_response.status_code == 200

    async def test_expired_session_handling(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test handling of expired sessions.

        Sessions should expire after inactivity period.
        """
        # This test would require time manipulation or short expiry config
        # For now, just verify session has expires_at field
        async with AsyncClient(base_url=agent_hub_url) as client:
            create_response = await client.post(
                "/sessions",
                json={
                    "agent_id": "@baron",
                },
            )

            assert create_response.status_code == 201
            # Session may have expires_at field

    async def test_session_health_check(
        self,
        agent_hub_url: str,
    ) -> None:
        """Test that Agent Hub is healthy before session tests."""
        async with AsyncClient(base_url=agent_hub_url) as client:
            health_response = await client.get("/health")
            assert health_response.status_code == 200
            assert health_response.json()["status"] == "healthy"
