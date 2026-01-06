"""Escalation models for Agent Hub Service.

These models define human escalation workflow for low-confidence answers
per data-model.md.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EscalationStatus(str, Enum):
    """Current status of an escalation."""

    PENDING = "pending"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class HumanAction(str, Enum):
    """Action taken by human reviewer."""

    CONFIRM = "confirm"  # Accept tentative answer
    CORRECT = "correct"  # Provide different answer
    ADD_CONTEXT = "add_context"  # Need more context, re-route


class Escalation(BaseModel):
    """Human review request for low-confidence answers."""

    id: UUID = Field(..., description="Escalation identifier")
    session_id: UUID | None = Field(
        default=None,
        description="Associated session if multi-turn",
    )
    question_id: str = Field(..., description="Unique question identifier")
    topic: str = Field(..., description="Topic for routing")
    question: str = Field(..., description="The original question")
    tentative_answer: str = Field(..., description="Agent's tentative answer")
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence level (0-100)",
    )
    uncertainty_reasons: list[str] | None = Field(
        default=None,
        description="Reasons for low confidence",
    )
    status: EscalationStatus = Field(
        default=EscalationStatus.PENDING,
        description="Current escalation status",
    )
    human_action: HumanAction | None = Field(
        default=None,
        description="Action taken by human reviewer",
    )
    human_response: str | None = Field(
        default=None,
        description="Response from human reviewer",
    )
    human_responder: str | None = Field(
        default=None,
        description="Identifier of the human responder",
    )
    github_comment_id: int | None = Field(
        default=None,
        description="GitHub comment ID if posted",
    )
    created_at: datetime
    resolved_at: datetime | None = None
    updated_at: datetime


class EscalationResponse(BaseModel):
    """Response containing escalation details."""

    id: UUID
    status: EscalationStatus
    question: str
    tentative_answer: str
    confidence: int
    human_action: HumanAction | None = None
    human_response: str | None = None
    human_responder: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class SubmitHumanResponseRequest(BaseModel):
    """Request to submit human response to escalation."""

    action: HumanAction = Field(..., description="Action to take")
    response: str | None = Field(
        default=None,
        description="Required for 'correct', optional for 'add_context'",
    )
    responder: str = Field(..., description="Identifier of the responder")


class AskExpertRequest(BaseModel):
    """Request to ask an expert by topic."""

    question: str = Field(
        ...,
        min_length=10,
        description="Question to ask the expert",
    )
    context: str | None = Field(
        default=None,
        description="Additional context for the question",
    )
    feature_id: str = Field(..., description="Feature ID for logging")
    session_id: UUID | None = Field(
        default=None,
        description="Session ID for multi-turn conversations",
    )


class AskExpertResponse(BaseModel):
    """Response from expert consultation."""

    answer: str
    rationale: str | None = None
    confidence: int = Field(..., ge=0, le=100)
    uncertainty_reasons: list[str] | None = None
    status: str = Field(
        ...,
        description="resolved, pending_human, or needs_reroute",
    )
    session_id: UUID
    escalation_id: UUID | None = None
