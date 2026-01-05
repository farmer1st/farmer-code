"""Workflow endpoints for Orchestrator service.

Implements POST /workflows, GET /workflows/{id}, POST /workflows/{id}/advance
per contracts/orchestrator.yaml.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.core.state_machine import (
    InvalidStateTransitionError,
    WorkflowNotFoundError,
    WorkflowStateMachine,
)
from src.db.models import WorkflowStatus, WorkflowType
from src.db.session import get_db

router = APIRouter()


# Request/Response models


class CreateWorkflowRequest(BaseModel):
    """Request body for POST /workflows."""

    workflow_type: str = Field(
        ...,
        description="Type of workflow: specify, plan, tasks, implement",
    )
    feature_description: str = Field(
        ...,
        min_length=10,
        description="Description of the feature",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Additional context for the workflow",
    )


class WorkflowResponse(BaseModel):
    """Response for workflow endpoints."""

    id: str
    workflow_type: str
    status: str
    feature_id: str
    current_phase: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str
    updated_at: str | None = None
    completed_at: str | None = None


class AdvanceWorkflowRequest(BaseModel):
    """Request body for POST /workflows/{id}/advance."""

    trigger: str = Field(
        ...,
        description="Trigger: agent_complete, human_approved, human_rejected",
    )
    phase_result: dict[str, Any] | None = Field(
        default=None,
        description="Result from completed phase",
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


@router.post(
    "/workflows",
    response_model=WorkflowResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def create_workflow(
    request: CreateWorkflowRequest,
    db: Session = Depends(get_db),
) -> WorkflowResponse:
    """Create and start a new workflow.

    Args:
        request: CreateWorkflowRequest with workflow_type and feature_description
        db: Database session

    Returns:
        WorkflowResponse with created workflow

    Raises:
        HTTPException: On validation error
    """
    # Validate workflow type
    valid_types = [wt.value for wt in WorkflowType]
    if request.workflow_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_WORKFLOW_TYPE",
                    "message": f"Invalid workflow type: {request.workflow_type}",
                    "details": [f"Valid types: {valid_types}"],
                }
            },
        )

    state_machine = WorkflowStateMachine(db)

    try:
        workflow = state_machine.create_workflow(
            workflow_type=request.workflow_type,
            feature_description=request.feature_description,
            context=request.context,
        )

        return WorkflowResponse(**workflow.to_dict())

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                }
            },
        ) from e


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Workflow not found"},
    },
)
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
) -> WorkflowResponse:
    """Get workflow by ID.

    Args:
        workflow_id: Workflow UUID
        db: Database session

    Returns:
        WorkflowResponse with workflow details

    Raises:
        HTTPException: If workflow not found
    """
    # Validate UUID format
    try:
        UUID(workflow_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_UUID",
                    "message": f"Invalid workflow ID format: {workflow_id}",
                }
            },
        ) from e

    state_machine = WorkflowStateMachine(db)

    try:
        workflow = state_machine.get_workflow(workflow_id)
        return WorkflowResponse(**workflow.to_dict())

    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "WORKFLOW_NOT_FOUND",
                    "message": str(e),
                }
            },
        ) from e


@router.post(
    "/workflows/{workflow_id}/advance",
    response_model=WorkflowResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid state transition"},
        404: {"model": ErrorResponse, "description": "Workflow not found"},
    },
)
async def advance_workflow(
    workflow_id: str,
    request: AdvanceWorkflowRequest,
    db: Session = Depends(get_db),
) -> WorkflowResponse:
    """Advance workflow to next state.

    Args:
        workflow_id: Workflow UUID
        request: AdvanceWorkflowRequest with trigger and optional phase_result
        db: Database session

    Returns:
        WorkflowResponse with updated workflow

    Raises:
        HTTPException: On error
    """
    # Validate UUID format
    try:
        UUID(workflow_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_UUID",
                    "message": f"Invalid workflow ID format: {workflow_id}",
                }
            },
        ) from e

    # Validate trigger
    valid_triggers = ["agent_complete", "human_approved", "human_rejected"]
    if request.trigger not in valid_triggers:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_TRIGGER",
                    "message": f"Invalid trigger: {request.trigger}",
                    "details": [f"Valid triggers: {valid_triggers}"],
                }
            },
        )

    state_machine = WorkflowStateMachine(db)

    try:
        workflow = state_machine.advance_workflow(
            workflow_id=workflow_id,
            trigger=request.trigger,
            phase_result=request.phase_result,
        )

        return WorkflowResponse(**workflow.to_dict())

    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "WORKFLOW_NOT_FOUND",
                    "message": str(e),
                }
            },
        ) from e

    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_STATE_TRANSITION",
                    "message": str(e),
                    "details": [
                        f"From: {e.from_status}",
                        f"Trigger: {e.trigger}",
                    ],
                }
            },
        ) from e
