"""Session Manager for Agent Hub.

This module provides session management for multi-turn conversations
with expert agents. Sessions maintain conversation history and context.
"""

from datetime import UTC, datetime
from typing import Any

from .exceptions import SessionClosedError, SessionNotFoundError
from .models import Message, MessageRole, Session, SessionStatus


class SessionManager:
    """Manages conversation sessions with expert agents.

    Provides CRUD operations for sessions and message management.
    Uses in-memory storage by default (can be extended for persistence).
    """

    def __init__(self) -> None:
        """Initialize the session manager with empty session store."""
        self._sessions: dict[str, Session] = {}

    def create(
        self,
        agent_id: str,
        feature_id: str = "",
    ) -> Session:
        """Create a new session.

        Args:
            agent_id: The agent role (e.g., "architect", "product").
            feature_id: Optional feature ID for grouping.

        Returns:
            New Session with unique ID.
        """
        session = Session(
            agent_id=agent_id,
            feature_id=feature_id,
        )
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session:
        """Get session by ID.

        Args:
            session_id: The session ID.

        Returns:
            Session if found.

        Raises:
            SessionNotFoundError: If session does not exist.
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        return self._sessions[session_id]

    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Add a message to a session.

        Args:
            session_id: The session ID.
            role: Message role (USER, ASSISTANT, HUMAN).
            content: Message content.
            metadata: Optional additional data (e.g., confidence, model).

        Returns:
            The created Message.

        Raises:
            SessionNotFoundError: If session does not exist.
            SessionClosedError: If session is closed.
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)

        session = self._sessions[session_id]

        if session.status == SessionStatus.CLOSED:
            raise SessionClosedError(session_id)

        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(UTC),
            metadata=metadata,
        )

        session.messages.append(message)
        session.updated_at = datetime.now(UTC)

        return message

    def close(self, session_id: str) -> None:
        """Close a session.

        Closed sessions cannot accept new messages.

        Args:
            session_id: The session ID.

        Raises:
            SessionNotFoundError: If session does not exist.
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)

        session = self._sessions[session_id]
        session.status = SessionStatus.CLOSED
        session.updated_at = datetime.now(UTC)

    def exists(self, session_id: str) -> bool:
        """Check if a session exists.

        Args:
            session_id: The session ID.

        Returns:
            True if session exists, False otherwise.
        """
        return session_id in self._sessions

    def list_active(self) -> list[Session]:
        """List all active sessions.

        Returns:
            List of sessions with ACTIVE status.
        """
        return [s for s in self._sessions.values() if s.status == SessionStatus.ACTIVE]

    def get_by_feature(self, feature_id: str) -> list[Session]:
        """Get all sessions for a feature.

        Args:
            feature_id: The feature ID to filter by.

        Returns:
            List of sessions matching the feature ID.
        """
        return [s for s in self._sessions.values() if s.feature_id == feature_id]
