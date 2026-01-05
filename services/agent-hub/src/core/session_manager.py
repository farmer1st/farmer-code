"""Session manager for Agent Hub service.

Manages session lifecycle: create, get, close, add messages.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session as DBSession

from src.db.models import Message, MessageRole, Session, SessionStatus


class SessionNotFoundError(Exception):
    """Raised when a session is not found."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session {session_id} not found")


class SessionClosedError(Exception):
    """Raised when trying to use a closed session."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session {session_id} is closed")


class SessionExpiredError(Exception):
    """Raised when trying to use an expired session."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session {session_id} has expired")


class SessionManager:
    """Manages session lifecycle."""

    def __init__(self, db: DBSession) -> None:
        """Initialize with database session."""
        self.db = db

    def create_session(
        self,
        agent_id: str,
        feature_id: str | None = None,
    ) -> Session:
        """Create a new session.

        Args:
            agent_id: Agent identifier (e.g., "@baron")
            feature_id: Optional feature ID for grouping

        Returns:
            Created session
        """
        session = Session(
            id=str(uuid4()),
            agent_id=agent_id,
            feature_id=feature_id,
            status=SessionStatus.ACTIVE.value,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session(self, session_id: str) -> Session:
        """Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session instance

        Raises:
            SessionNotFoundError: If session not found
        """
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise SessionNotFoundError(session_id)

        # Check if expired
        if session.status == SessionStatus.ACTIVE.value and not session.is_active():
            session.status = SessionStatus.EXPIRED.value
            self.db.commit()

        return session

    def close_session(self, session_id: str) -> Session:
        """Close a session.

        Args:
            session_id: Session UUID

        Returns:
            Closed session

        Raises:
            SessionNotFoundError: If session not found
        """
        session = self.get_session(session_id)
        session.status = SessionStatus.CLOSED.value
        session.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Add a message to a session.

        Args:
            session_id: Session UUID
            role: Message role (user, assistant, human)
            content: Message content
            metadata: Optional message metadata

        Returns:
            Created message

        Raises:
            SessionNotFoundError: If session not found
            SessionClosedError: If session is closed
            SessionExpiredError: If session is expired
        """
        session = self.get_session(session_id)

        # Check session state
        if session.status == SessionStatus.CLOSED.value:
            raise SessionClosedError(session_id)
        if session.status == SessionStatus.EXPIRED.value:
            raise SessionExpiredError(session_id)
        if not session.is_active():
            session.status = SessionStatus.EXPIRED.value
            self.db.commit()
            raise SessionExpiredError(session_id)

        # Create message
        message = Message(
            id=str(uuid4()),
            session_id=session_id,
            role=role,
            content=content,
        )
        if metadata:
            message.set_metadata(metadata)

        # Update session timestamp
        session.updated_at = datetime.utcnow()

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message

    def get_session_messages(self, session_id: str) -> list[Message]:
        """Get all messages for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of messages in chronological order

        Raises:
            SessionNotFoundError: If session not found
        """
        session = self.get_session(session_id)
        return list(session.messages)

    def get_session_context(self, session_id: str) -> list[dict[str, str]]:
        """Get session messages formatted as context for agent.

        Args:
            session_id: Session UUID

        Returns:
            List of message dicts with role and content
        """
        messages = self.get_session_messages(session_id)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def validate_session_for_use(self, session_id: str) -> Session:
        """Validate that session can be used.

        Args:
            session_id: Session UUID

        Returns:
            Active session

        Raises:
            SessionNotFoundError: If session not found
            SessionClosedError: If session is closed
            SessionExpiredError: If session is expired
        """
        session = self.get_session(session_id)

        if session.status == SessionStatus.CLOSED.value:
            raise SessionClosedError(session_id)
        if session.status == SessionStatus.EXPIRED.value or not session.is_active():
            raise SessionExpiredError(session_id)

        return session
