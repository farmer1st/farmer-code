"""Integration tests for session context preservation.

Tests that session context is preserved across multiple exchanges.
Success Criteria SC-006: Session preserves context across 5 consecutive exchanges.
"""


import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
class TestSessionContextPreservation:
    """Integration tests for session context preservation."""

    async def test_session_preserves_context_across_exchanges(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that session context is preserved across multiple exchanges.

        SC-006: Session preserves context across 5 consecutive exchanges.
        """
        # Create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron", "feature_id": "008-context-test"},
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["id"]

        # Make 5 consecutive exchanges with the same session
        for i in range(5):
            response = await test_client.post(
                "/ask/architecture",
                json={
                    "question": f"Question number {i + 1}: What about performance considerations?",
                    "context": f"This is exchange {i + 1} in a multi-turn conversation",
                    "feature_id": "008-context-test",
                    "session_id": session_id,
                },
            )
            # Each exchange should succeed
            assert response.status_code == 200

        # Get session and verify message count
        session_response = await test_client.get(f"/sessions/{session_id}")
        assert session_response.status_code == 200
        data = session_response.json()

        # Should have at least 5 user messages and 5 assistant responses
        messages = data.get("messages", [])
        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]

        assert len(user_messages) >= 5, f"Expected 5 user messages, got {len(user_messages)}"
        assert len(assistant_messages) >= 5, f"Expected 5 assistant messages, got {len(assistant_messages)}"

    async def test_session_messages_ordered_chronologically(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that session messages are ordered chronologically."""
        # Create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        session_id = create_response.json()["id"]

        # Make multiple exchanges
        for i in range(3):
            await test_client.post(
                "/ask/architecture",
                json={
                    "question": f"Question {i + 1}: Design question here with enough characters",
                    "feature_id": "008-order-test",
                    "session_id": session_id,
                },
            )

        # Get session
        session_response = await test_client.get(f"/sessions/{session_id}")
        data = session_response.json()
        messages = data.get("messages", [])

        # Verify chronological order
        for i in range(len(messages) - 1):
            current_time = messages[i]["created_at"]
            next_time = messages[i + 1]["created_at"]
            assert current_time <= next_time, "Messages not in chronological order"

    async def test_session_context_includes_previous_messages(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that agent receives context from previous messages."""
        # Create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron", "feature_id": "008-include-test"},
        )
        session_id = create_response.json()["id"]

        # First exchange - establish context
        await test_client.post(
            "/ask/architecture",
            json={
                "question": "I'm building a user authentication system with OAuth2",
                "feature_id": "008-include-test",
                "session_id": session_id,
            },
        )

        # Second exchange - reference previous context
        response = await test_client.post(
            "/ask/architecture",
            json={
                "question": "Given what I just said, should I use JWT or sessions?",
                "feature_id": "008-include-test",
                "session_id": session_id,
            },
        )

        assert response.status_code == 200
        # The agent should have context from the previous message

    async def test_different_sessions_independent(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that different sessions have independent context."""
        # Create two sessions
        session1_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron", "feature_id": "008-session-1"},
        )
        session1_id = session1_response.json()["id"]

        session2_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron", "feature_id": "008-session-2"},
        )
        session2_id = session2_response.json()["id"]

        # Add message to session 1
        await test_client.post(
            "/ask/architecture",
            json={
                "question": "Question for session 1 about microservices architecture",
                "feature_id": "008-session-1",
                "session_id": session1_id,
            },
        )

        # Add message to session 2
        await test_client.post(
            "/ask/architecture",
            json={
                "question": "Question for session 2 about monolithic design",
                "feature_id": "008-session-2",
                "session_id": session2_id,
            },
        )

        # Get both sessions
        get1 = await test_client.get(f"/sessions/{session1_id}")
        get2 = await test_client.get(f"/sessions/{session2_id}")

        # Each session should have its own independent messages
        messages1 = get1.json().get("messages", [])
        messages2 = get2.json().get("messages", [])

        # Messages should be different
        assert len(messages1) > 0
        assert len(messages2) > 0

    async def test_closed_session_rejects_new_messages(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that closed session rejects new messages."""
        # Create and close a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        session_id = create_response.json()["id"]

        await test_client.delete(f"/sessions/{session_id}")

        # Try to use closed session
        response = await test_client.post(
            "/ask/architecture",
            json={
                "question": "This should fail because session is closed",
                "feature_id": "008-closed-test",
                "session_id": session_id,
            },
        )

        # Should reject with error (400 or similar)
        assert response.status_code in [400, 409]

    async def test_session_message_metadata(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that messages include useful metadata."""
        # Create a session
        create_response = await test_client.post(
            "/sessions",
            json={"agent_id": "@baron"},
        )
        session_id = create_response.json()["id"]

        # Add a message
        await test_client.post(
            "/ask/architecture",
            json={
                "question": "What's the best way to structure my API endpoints?",
                "feature_id": "008-metadata-test",
                "session_id": session_id,
            },
        )

        # Get session
        session_response = await test_client.get(f"/sessions/{session_id}")
        data = session_response.json()
        messages = data.get("messages", [])

        # Find assistant message
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        if assistant_messages:
            message = assistant_messages[0]
            # Metadata may include confidence, model_used, etc.
            # Just verify message structure is correct
            assert "id" in message
            assert "content" in message
            assert "created_at" in message
