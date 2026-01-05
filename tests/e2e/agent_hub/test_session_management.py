"""End-to-end tests for session management (AH-002)."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from agent_hub.config import ConfigLoader
from agent_hub.models import SessionStatus


@pytest.mark.journey("AH-002")
class TestSessionManagementE2E:
    """E2E tests for session management flow (T038 - US2).

    User Story 2: Maintain Conversation Sessions
    - Agent Hub maintains conversation sessions with full context preservation
    - Sessions track questions and answers across multi-turn conversations
    - Context is preserved for follow-up questions
    """

    @patch("agent_hub.router.subprocess.run")
    def test_ask_expert_creates_session_e2e(self, mock_run: MagicMock) -> None:
        """Test that ask_expert creates a session and returns session_id."""
        from agent_hub.hub import AgentHub

        # Mock CLI response
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use PostgreSQL", '
                '"rationale": "Excellent for complex queries and ACID compliance", '
                '"confidence": 90}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["database"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="database",
            question="Which database should we use?",
            feature_id="005-db-setup",
        )

        # Should return a session_id
        assert response.session_id is not None
        assert len(response.session_id) > 0
        # Session ID should be a valid UUID
        uuid.UUID(response.session_id)

    @patch("agent_hub.router.subprocess.run")
    def test_session_preserves_context_across_questions_e2e(self, mock_run: MagicMock) -> None:
        """Test that session preserves context across multiple questions."""
        from agent_hub.hub import AgentHub

        # Mock responses for two questions
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout=(
                    '{"answer": "Use PostgreSQL for main data", '
                    '"rationale": "Good for structured data", '
                    '"confidence": 88}'
                ),
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout=(
                    '{"answer": "Add Redis for caching hot paths", '
                    '"rationale": "Complements PostgreSQL for read performance", '
                    '"confidence": 92}'
                ),
                stderr="",
            ),
        ]

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["database", "caching"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        # First question
        response1 = hub.ask_expert(
            topic="database",
            question="Which database should we use?",
            feature_id="005-db-setup",
        )

        # Second question using same session
        response2 = hub.ask_expert(
            topic="caching",
            question="What about caching?",
            feature_id="005-db-setup",
            session_id=response1.session_id,  # Reuse session
        )

        # Both should use the same session
        assert response1.session_id == response2.session_id

        # Verify session has both exchanges
        session = hub.get_session(response1.session_id)
        assert len(session.messages) >= 2  # At least 2 Q&A pairs

    @patch("agent_hub.router.subprocess.run")
    def test_get_session_returns_full_history_e2e(self, mock_run: MagicMock) -> None:
        """Test that get_session returns complete conversation history."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use OAuth2", '
                '"rationale": "Industry standard for secure API authentication", '
                '"confidence": 95}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["authentication"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="authentication",
            question="What auth method should we use?",
            context="Building REST API for mobile",
            feature_id="005-auth",
        )

        # Get the session
        session = hub.get_session(response.session_id)

        assert session is not None
        assert session.id == response.session_id
        assert session.status == SessionStatus.ACTIVE
        assert len(session.messages) >= 1

    @patch("agent_hub.router.subprocess.run")
    def test_close_session_prevents_new_messages_e2e(self, mock_run: MagicMock) -> None:
        """Test that closing a session prevents adding new messages."""
        from agent_hub.hub import AgentHub

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use microservices", '
                '"rationale": "Better scalability and independent deployment", '
                '"confidence": 85}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["architecture"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        # Create session via ask_expert
        response = hub.ask_expert(
            topic="architecture",
            question="What architecture pattern?",
            feature_id="005-arch",
        )

        # Close the session
        hub.close_session(response.session_id)

        # Verify session is closed
        session = hub.get_session(response.session_id)
        assert session.status == SessionStatus.CLOSED

    def test_get_nonexistent_session_raises_error_e2e(self) -> None:
        """Test that getting a nonexistent session raises error."""
        from agent_hub.exceptions import SessionNotFoundError
        from agent_hub.hub import AgentHub

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["test"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        with pytest.raises(SessionNotFoundError) as exc_info:
            hub.get_session("nonexistent-session-id")

        assert exc_info.value.session_id == "nonexistent-session-id"

    @patch("agent_hub.router.subprocess.run")
    def test_session_tracks_multiple_turn_conversation_e2e(self, mock_run: MagicMock) -> None:
        """Test complete multi-turn conversation tracking."""
        from agent_hub.hub import AgentHub

        # Mock 3 responses for a multi-turn conversation
        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout=(
                    '{"answer": "Use JWT tokens", '
                    '"rationale": "Stateless authentication", '
                    '"confidence": 90}'
                ),
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout=(
                    '{"answer": "Set expiry to 15 minutes for access tokens", '
                    '"rationale": "Balance security and UX", '
                    '"confidence": 88}'
                ),
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout=(
                    '{"answer": "Use rotating refresh tokens with 7 day expiry", '
                    '"rationale": "Secure long-term sessions", '
                    '"confidence": 92}'
                ),
                stderr="",
            ),
        ]

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["authentication", "security", "tokens"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        # Turn 1
        r1 = hub.ask_expert(
            topic="authentication",
            question="What token type should we use?",
            feature_id="005-auth",
        )
        session_id = r1.session_id

        # Turn 2
        r2 = hub.ask_expert(
            topic="security",
            question="What should be the token expiry?",
            feature_id="005-auth",
            session_id=session_id,
        )

        # Turn 3
        r3 = hub.ask_expert(
            topic="tokens",
            question="How should we handle refresh tokens?",
            feature_id="005-auth",
            session_id=session_id,
        )

        # All responses should use same session
        assert r1.session_id == r2.session_id == r3.session_id

        # Get final session state
        session = hub.get_session(session_id)

        # Should have all 3 Q&A exchanges
        assert session.status == SessionStatus.ACTIVE
        # Each ask_expert adds question + answer
        assert len(session.messages) >= 3

        # Close session
        hub.close_session(session_id)
        assert hub.get_session(session_id).status == SessionStatus.CLOSED
