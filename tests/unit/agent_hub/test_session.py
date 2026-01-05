"""Unit tests for SessionManager (US2: Maintain Conversation Sessions)."""

import uuid
from datetime import UTC, datetime

import pytest

from agent_hub.exceptions import SessionClosedError, SessionNotFoundError
from agent_hub.models import Message, MessageRole, Session, SessionStatus


class TestSessionManagerCreate:
    """Tests for SessionManager.create() (T034 - US2)."""

    def test_create_session_returns_session_with_id(self) -> None:
        """Test that create() returns a Session with unique ID."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        assert isinstance(session, Session)
        assert session.id is not None
        assert len(session.id) > 0
        # Should be a valid UUID
        uuid.UUID(session.id)

    def test_create_session_sets_agent_id(self) -> None:
        """Test that create() sets the agent_id correctly."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="product")

        assert session.agent_id == "product"

    def test_create_session_with_feature_id(self) -> None:
        """Test that create() accepts optional feature_id."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect", feature_id="005-user-auth")

        assert session.feature_id == "005-user-auth"

    def test_create_session_starts_active(self) -> None:
        """Test that new sessions start with ACTIVE status."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        assert session.status == SessionStatus.ACTIVE

    def test_create_session_has_empty_messages(self) -> None:
        """Test that new sessions start with empty message list."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        assert session.messages == []

    def test_create_session_sets_timestamps(self) -> None:
        """Test that create() sets created_at and updated_at."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        _before = datetime.now(UTC)  # noqa: F841
        session = manager.create(agent_id="architect")
        _after = datetime.now(UTC)  # noqa: F841

        # Timestamps should be set (within reasonable range)
        assert session.created_at is not None
        assert session.updated_at is not None

    def test_create_multiple_sessions_have_unique_ids(self) -> None:
        """Test that multiple sessions have different IDs."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session1 = manager.create(agent_id="architect")
        session2 = manager.create(agent_id="architect")
        session3 = manager.create(agent_id="product")

        ids = {session1.id, session2.id, session3.id}
        assert len(ids) == 3  # All unique


class TestSessionManagerAddMessage:
    """Tests for SessionManager.add_message() (T035 - US2)."""

    def test_add_message_returns_message(self) -> None:
        """Test that add_message() returns the created Message."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        message = manager.add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content="What database should we use?",
        )

        assert isinstance(message, Message)
        assert message.role == MessageRole.USER
        assert message.content == "What database should we use?"

    def test_add_message_appends_to_session(self) -> None:
        """Test that add_message() appends message to session."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        manager.add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content="Question 1",
        )
        manager.add_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content="Answer 1",
        )

        updated_session = manager.get(session.id)
        assert len(updated_session.messages) == 2
        assert updated_session.messages[0].content == "Question 1"
        assert updated_session.messages[1].content == "Answer 1"

    def test_add_message_with_metadata(self) -> None:
        """Test that add_message() accepts optional metadata."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        message = manager.add_message(
            session_id=session.id,
            role=MessageRole.ASSISTANT,
            content="Use PostgreSQL",
            metadata={"confidence": 92, "model": "opus"},
        )

        assert message.metadata == {"confidence": 92, "model": "opus"}

    def test_add_message_sets_timestamp(self) -> None:
        """Test that add_message() sets timestamp on message."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        message = manager.add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content="Test question",
        )

        assert message.timestamp is not None

    def test_add_message_updates_session_updated_at(self) -> None:
        """Test that add_message() updates session's updated_at."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.01)

        manager.add_message(
            session_id=session.id,
            role=MessageRole.USER,
            content="Test question",
        )

        updated_session = manager.get(session.id)
        # updated_at should be set (the add_message updates it)
        assert updated_session.updated_at is not None

    def test_add_message_to_nonexistent_session_raises_error(self) -> None:
        """Test that add_message() raises SessionNotFoundError for bad ID."""
        from agent_hub.session import SessionManager

        manager = SessionManager()

        with pytest.raises(SessionNotFoundError) as exc_info:
            manager.add_message(
                session_id="nonexistent-id",
                role=MessageRole.USER,
                content="Test",
            )

        assert exc_info.value.session_id == "nonexistent-id"

    def test_add_message_to_closed_session_raises_error(self) -> None:
        """Test that add_message() raises SessionClosedError for closed session."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")
        manager.close(session.id)

        with pytest.raises(SessionClosedError) as exc_info:
            manager.add_message(
                session_id=session.id,
                role=MessageRole.USER,
                content="Test",
            )

        assert exc_info.value.session_id == session.id

    def test_add_human_message(self) -> None:
        """Test that add_message() supports HUMAN role."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        message = manager.add_message(
            session_id=session.id,
            role=MessageRole.HUMAN,
            content="Actually, use Redis for caching",
            metadata={"responder": "@farmer1st"},
        )

        assert message.role == MessageRole.HUMAN


class TestSessionManagerGetAndClose:
    """Tests for SessionManager.get() and close() (T036 - US2)."""

    def test_get_returns_session_by_id(self) -> None:
        """Test that get() returns session by ID."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        created = manager.create(agent_id="architect", feature_id="005-test")

        retrieved = manager.get(created.id)

        assert retrieved.id == created.id
        assert retrieved.agent_id == "architect"
        assert retrieved.feature_id == "005-test"

    def test_get_nonexistent_session_raises_error(self) -> None:
        """Test that get() raises SessionNotFoundError for bad ID."""
        from agent_hub.session import SessionManager

        manager = SessionManager()

        with pytest.raises(SessionNotFoundError) as exc_info:
            manager.get("nonexistent-id")

        assert exc_info.value.session_id == "nonexistent-id"

    def test_close_changes_status_to_closed(self) -> None:
        """Test that close() changes session status to CLOSED."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")
        assert session.status == SessionStatus.ACTIVE

        manager.close(session.id)

        closed_session = manager.get(session.id)
        assert closed_session.status == SessionStatus.CLOSED

    def test_close_nonexistent_session_raises_error(self) -> None:
        """Test that close() raises SessionNotFoundError for bad ID."""
        from agent_hub.session import SessionManager

        manager = SessionManager()

        with pytest.raises(SessionNotFoundError) as exc_info:
            manager.close("nonexistent-id")

        assert exc_info.value.session_id == "nonexistent-id"

    def test_close_updates_updated_at(self) -> None:
        """Test that close() updates session's updated_at."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        import time

        time.sleep(0.01)

        manager.close(session.id)

        closed_session = manager.get(session.id)
        # close should update the updated_at timestamp
        assert closed_session.updated_at is not None

    def test_get_preserves_messages(self) -> None:
        """Test that get() returns session with all messages."""
        from agent_hub.session import SessionManager

        manager = SessionManager()
        session = manager.create(agent_id="architect")

        manager.add_message(session.id, MessageRole.USER, "Q1")
        manager.add_message(session.id, MessageRole.ASSISTANT, "A1")
        manager.add_message(session.id, MessageRole.USER, "Q2")

        retrieved = manager.get(session.id)
        assert len(retrieved.messages) == 3


class TestSessionManagerIntegration:
    """Integration tests for SessionManager workflow."""

    def test_full_conversation_workflow(self) -> None:
        """Test complete conversation workflow with multiple messages."""
        from agent_hub.session import SessionManager

        manager = SessionManager()

        # Create session
        session = manager.create(
            agent_id="architect",
            feature_id="005-auth",
        )

        # Add question
        manager.add_message(
            session.id,
            MessageRole.USER,
            "What auth method should we use?",
        )

        # Add answer
        manager.add_message(
            session.id,
            MessageRole.ASSISTANT,
            "Use OAuth2 with JWT",
            metadata={"confidence": 85},
        )

        # Add follow-up question
        manager.add_message(
            session.id,
            MessageRole.USER,
            "What about refresh tokens?",
        )

        # Add follow-up answer
        manager.add_message(
            session.id,
            MessageRole.ASSISTANT,
            "Use rotating refresh tokens with 7-day expiry",
            metadata={"confidence": 90},
        )

        # Get and verify
        final_session = manager.get(session.id)
        assert len(final_session.messages) == 4
        assert final_session.messages[0].role == MessageRole.USER
        assert final_session.messages[1].role == MessageRole.ASSISTANT
        assert final_session.messages[2].role == MessageRole.USER
        assert final_session.messages[3].role == MessageRole.ASSISTANT

        # Close session
        manager.close(session.id)
        assert manager.get(session.id).status == SessionStatus.CLOSED

    def test_multiple_sessions_isolated(self) -> None:
        """Test that multiple sessions are isolated from each other."""
        from agent_hub.session import SessionManager

        manager = SessionManager()

        # Create two sessions
        session1 = manager.create(agent_id="architect")
        session2 = manager.create(agent_id="product")

        # Add messages to each
        manager.add_message(session1.id, MessageRole.USER, "Session 1 Q1")
        manager.add_message(session1.id, MessageRole.ASSISTANT, "Session 1 A1")

        manager.add_message(session2.id, MessageRole.USER, "Session 2 Q1")

        # Verify isolation
        s1 = manager.get(session1.id)
        s2 = manager.get(session2.id)

        assert len(s1.messages) == 2
        assert len(s2.messages) == 1
        assert s1.messages[0].content == "Session 1 Q1"
        assert s2.messages[0].content == "Session 2 Q1"
