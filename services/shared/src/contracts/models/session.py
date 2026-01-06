"""Session models for Agent Hub Service.

These models define session lifecycle for multi-turn agent conversations
per data-model.md.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Current status of a session."""

    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    HUMAN = "human"


class Message(BaseModel):
    """Individual message within a session."""

    id: UUID = Field(..., description="Message identifier")
    role: MessageRole = Field(..., description="Role of the sender")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata (confidence, model_used, duration_ms)",
    )
    created_at: datetime


class Session(BaseModel):
    """Conversation session for multi-turn interactions."""

    id: UUID = Field(..., description="Session identifier")
    agent_id: str = Field(..., description="Agent identifier (e.g., @duc, @baron)")
    feature_id: str | None = Field(
        default=None,
        description="Associated feature ID for grouping",
    )
    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE,
        description="Current session status",
    )
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = Field(
        default=None,
        description="When the session expires (default: created_at + 1 hour)",
    )


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    agent_id: str = Field(..., description="Agent identifier (e.g., @duc)")
    feature_id: str | None = Field(
        default=None,
        description="Feature ID for grouping",
    )


class SessionResponse(BaseModel):
    """Response containing session details."""

    id: UUID
    agent_id: str
    feature_id: str | None = None
    status: SessionStatus
    created_at: datetime
    updated_at: datetime


class SessionWithMessagesResponse(SessionResponse):
    """Session response including message history."""

    messages: list[Message] = Field(default_factory=list)
