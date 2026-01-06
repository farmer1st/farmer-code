"""Session endpoints for Agent Hub service.

Implements POST /sessions, GET /sessions/{id}, DELETE /sessions/{id}
per contracts/agent-hub.yaml.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.session_manager import (
    SessionManager,
    SessionNotFoundError,
)
from src.db.session import get_db

router = APIRouter()


# Request/Response models


class CreateSessionRequest(BaseModel):
    """Request body for POST /sessions."""

    agent_id: str = Field(
        ...,
        description="Agent identifier (e.g., @baron)",
    )
    feature_id: str | None = Field(
        default=None,
        description="Optional feature ID for grouping",
    )


class MessageResponse(BaseModel):
    """Message in session response."""

    id: str
    role: str
    content: str
    metadata: dict[str, Any] | None = None
    created_at: str


class SessionResponse(BaseModel):
    """Response for session endpoints."""

    id: str
    agent_id: str
    feature_id: str | None = None
    status: str
    created_at: str
    updated_at: str | None = None


class SessionWithMessagesResponse(SessionResponse):
    """Session response including messages."""

    messages: list[MessageResponse] = []


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: list[str] | None = None


class ErrorResponse(BaseModel):
    """Error response structure."""

    error: ErrorDetail


# Endpoints


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=201,
)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Create a new session for multi-turn conversations.

    Args:
        request: CreateSessionRequest with agent_id and optional feature_id
        db: Database session

    Returns:
        SessionResponse with created session
    """
    manager = SessionManager(db)

    session = manager.create_session(
        agent_id=request.agent_id,
        feature_id=request.feature_id,
    )

    return SessionResponse(**session.to_dict())


@router.get(
    "/sessions/{session_id}",
    response_model=SessionWithMessagesResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionWithMessagesResponse:
    """Get session with message history.

    Args:
        session_id: Session UUID
        db: Database session

    Returns:
        SessionWithMessagesResponse with session and messages

    Raises:
        HTTPException: If session not found
    """
    # Validate UUID format
    try:
        UUID(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_UUID",
                    "message": f"Invalid session ID format: {session_id}",
                }
            },
        ) from e

    manager = SessionManager(db)

    try:
        session = manager.get_session(session_id)
        session_dict = session.to_dict(include_messages=True)

        # Convert messages to response format
        messages = [
            MessageResponse(**msg) for msg in session_dict.get("messages", [])
        ]

        return SessionWithMessagesResponse(
            id=session_dict["id"],
            agent_id=session_dict["agent_id"],
            feature_id=session_dict["feature_id"],
            status=session_dict["status"],
            created_at=session_dict["created_at"],
            updated_at=session_dict["updated_at"],
            messages=messages,
        )

    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": str(e),
                }
            },
        ) from e


@router.delete(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def close_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionResponse:
    """Close a session, preserving history for audit.

    Args:
        session_id: Session UUID
        db: Database session

    Returns:
        SessionResponse with closed session

    Raises:
        HTTPException: If session not found
    """
    # Validate UUID format
    try:
        UUID(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_UUID",
                    "message": f"Invalid session ID format: {session_id}",
                }
            },
        ) from e

    manager = SessionManager(db)

    try:
        session = manager.close_session(session_id)
        return SessionResponse(**session.to_dict())

    except SessionNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "SESSION_NOT_FOUND",
                    "message": str(e),
                }
            },
        ) from e
