"""Workflow models for Orchestrator Service.

These models define the workflow lifecycle including types, statuses,
and request/response formats per data-model.md.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WorkflowType(str, Enum):
    """Type of SpecKit workflow to execute."""

    SPECIFY = "specify"
    PLAN = "plan"
    TASKS = "tasks"
    IMPLEMENT = "implement"


class WorkflowStatus(str, Enum):
    """Current status of a workflow."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateWorkflowRequest(BaseModel):
    """Request to create a new workflow."""

    workflow_type: WorkflowType = Field(
        ...,
        description="Type of SpecKit workflow to execute",
    )
    feature_description: str = Field(
        ...,
        min_length=10,
        description="Description of the feature to work on",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Additional context for the workflow",
    )


class WorkflowResponse(BaseModel):
    """Response containing workflow details."""

    id: UUID = Field(..., description="Workflow identifier")
    workflow_type: WorkflowType
    status: WorkflowStatus
    feature_id: str = Field(
        ...,
        pattern=r"^\d{3}-[a-z0-9-]+$",
        description="Feature ID in format NNN-name",
    )
    current_phase: str | None = Field(
        default=None,
        description="Current phase of execution",
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="Workflow output when complete",
    )
    error: str | None = Field(
        default=None,
        description="Error message if failed",
    )
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class AdvanceWorkflowRequest(BaseModel):
    """Request to advance workflow to next phase."""

    trigger: str = Field(
        ...,
        description="Trigger: agent_complete, human_approved, human_rejected",
    )
    phase_result: dict[str, Any] | None = Field(
        default=None,
        description="Output from the completed phase",
    )
