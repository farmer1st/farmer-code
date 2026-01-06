"""Escalation endpoints for Agent Hub service.

Implements GET /escalations/{id}, POST /escalations/{id}
per contracts/agent-hub.yaml.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.escalation import (
    EscalationAlreadyResolvedError,
    EscalationManager,
    EscalationNotFoundError,
    InvalidHumanActionError,
)
from src.db.session import get_db

router = APIRouter()


# Request/Response models


class EscalationResponse(BaseModel):
    """Response for escalation endpoints."""

    id: str
    status: str
    question: str
    tentative_answer: str
    confidence: int
    uncertainty_reasons: list[str] | None = None
    human_action: str | None = None
    human_response: str | None = None
    human_responder: str | None = None
    created_at: str
    resolved_at: str | None = None


class SubmitHumanResponseRequest(BaseModel):
    """Request body for POST /escalations/{id}."""

    action: str = Field(
        ...,
        description="Action: confirm, correct, or add_context",
    )
    response: str | None = Field(
        default=None,
        description="Response text (required for 'correct')",
    )
    responder: str = Field(
        ...,
        description="Human responder identifier (e.g., @username)",
    )


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: list[str] | None = None


class ErrorResponse(BaseModel):
    """Error response structure."""

    error: ErrorDetail


# Endpoints


@router.get(
    "/escalations/{escalation_id}",
    response_model=EscalationResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Escalation not found"},
    },
)
async def get_escalation(
    escalation_id: str,
    db: Session = Depends(get_db),
) -> EscalationResponse:
    """Get escalation by ID.

    Args:
        escalation_id: Escalation UUID
        db: Database session

    Returns:
        EscalationResponse with escalation details

    Raises:
        HTTPException: If escalation not found
    """
    # Validate UUID format
    try:
        UUID(escalation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_UUID",
                    "message": f"Invalid escalation ID format: {escalation_id}",
                }
            },
        ) from e

    manager = EscalationManager(db)

    try:
        escalation = manager.get_escalation(escalation_id)
        return EscalationResponse(**escalation.to_dict())

    except EscalationNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ESCALATION_NOT_FOUND",
                    "message": str(e),
                }
            },
        ) from e


@router.post(
    "/escalations/{escalation_id}",
    response_model=EscalationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Escalation not found"},
        409: {"model": ErrorResponse, "description": "Already resolved"},
    },
)
async def submit_human_response(
    escalation_id: str,
    request: SubmitHumanResponseRequest,
    db: Session = Depends(get_db),
) -> EscalationResponse:
    """Submit human response to an escalation.

    Args:
        escalation_id: Escalation UUID
        request: SubmitHumanResponseRequest with action and response
        db: Database session

    Returns:
        EscalationResponse with updated escalation

    Raises:
        HTTPException: On error
    """
    # Validate UUID format
    try:
        UUID(escalation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_UUID",
                    "message": f"Invalid escalation ID format: {escalation_id}",
                }
            },
        ) from e

    # Validate action
    valid_actions = ["confirm", "correct", "add_context"]
    if request.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_ACTION",
                    "message": f"Invalid action: {request.action}",
                    "details": [f"Valid actions: {valid_actions}"],
                }
            },
        )

    # Validate response for correct action
    if request.action == "correct" and not request.response:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "MISSING_RESPONSE",
                    "message": "Response is required for 'correct' action",
                }
            },
        )

    manager = EscalationManager(db)

    try:
        escalation = manager.submit_human_response(
            escalation_id=escalation_id,
            action=request.action,
            responder=request.responder,
            response=request.response,
        )
        return EscalationResponse(**escalation.to_dict())

    except EscalationNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ESCALATION_NOT_FOUND",
                    "message": str(e),
                }
            },
        ) from e

    except EscalationAlreadyResolvedError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "ALREADY_RESOLVED",
                    "message": str(e),
                }
            },
        ) from e

    except InvalidHumanActionError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_ACTION",
                    "message": str(e),
                }
            },
        ) from e
