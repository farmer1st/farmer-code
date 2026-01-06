"""SQLAlchemy models for Agent Hub service.

Defines Session and Message models per data-model.md.
"""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class SessionStatus(str, Enum):
    """Session status enumeration."""

    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    HUMAN = "human"


class EscalationStatus(str, Enum):
    """Escalation status enumeration."""

    PENDING = "pending"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class HumanAction(str, Enum):
    """Human action enumeration."""

    CONFIRM = "confirm"
    CORRECT = "correct"
    ADD_CONTEXT = "add_context"


class Session(Base):
    """Session entity for multi-turn conversations."""

    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    agent_id = Column(String, nullable=False)
    feature_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default=SessionStatus.ACTIVE.value)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationship to messages
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize session with default expiry."""
        super().__init__(**kwargs)
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=1)

    def is_active(self) -> bool:
        """Check if session is active and not expired."""
        if self.status != SessionStatus.ACTIVE.value:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True

    def to_dict(self, include_messages: bool = False) -> dict[str, Any]:
        """Convert to API response dict."""
        result: dict[str, Any] = {
            "id": self.id,
            "agent_id": self.agent_id,
            "feature_id": self.feature_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            result["messages"] = [msg.to_dict() for msg in self.messages]
        return result


class Message(Base):
    """Message entity within a session."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to session
    session = relationship("Session", back_populates="messages")

    def set_metadata(self, metadata_dict: dict[str, Any] | None) -> None:
        """Set metadata as JSON string."""
        self.message_metadata = json.dumps(metadata_dict) if metadata_dict else None

    def get_metadata(self) -> dict[str, Any] | None:
        """Get metadata as dict."""
        return json.loads(self.message_metadata) if self.message_metadata else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response dict."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "metadata": self.get_metadata(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Escalation(Base):
    """Escalation entity for human review requests."""

    __tablename__ = "escalations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), nullable=True)
    question_id = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    tentative_answer = Column(Text, nullable=False)
    confidence = Column(Integer, nullable=False)
    uncertainty_reasons = Column(Text, nullable=True)  # JSON array
    status = Column(String, nullable=False, default=EscalationStatus.PENDING.value)
    human_action = Column(String, nullable=True)
    human_response = Column(Text, nullable=True)
    human_responder = Column(String, nullable=True)
    github_comment_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def set_uncertainty_reasons(self, reasons: list[str] | None) -> None:
        """Set uncertainty reasons as JSON string."""
        self.uncertainty_reasons = json.dumps(reasons) if reasons else None

    def get_uncertainty_reasons(self) -> list[str] | None:
        """Get uncertainty reasons as list."""
        return json.loads(self.uncertainty_reasons) if self.uncertainty_reasons else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response dict."""
        return {
            "id": self.id,
            "status": self.status,
            "question": self.question,
            "tentative_answer": self.tentative_answer,
            "confidence": self.confidence,
            "uncertainty_reasons": self.get_uncertainty_reasons(),
            "human_action": self.human_action,
            "human_response": self.human_response,
            "human_responder": self.human_responder,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
