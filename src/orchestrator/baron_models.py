"""Pydantic models for Baron PM Agent dispatch and results.

Baron is a Claude Agent SDK agent. These models are used by BaronDispatcher
to build dispatch prompts and parse agent output.
"""

import re
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class SpecifyRequest(BaseModel):
    """Request to dispatch Baron for the specify workflow.

    Creates a feature specification (spec.md) from a natural language description.
    """

    feature_description: str = Field(
        ...,
        min_length=10,
        description="Natural language description of the feature",
    )
    feature_number: int | None = Field(
        default=None,
        gt=0,
        description="Explicit feature number (auto-generated if None)",
    )
    short_name: str | None = Field(
        default=None,
        description="Short name for branch (auto-generated if None)",
    )

    @field_validator("short_name")
    @classmethod
    def validate_short_name(cls, v: str | None) -> str | None:
        """Validate short_name matches expected pattern."""
        if v is not None and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("short_name must match pattern ^[a-z0-9-]+$")
        return v


class SpecifyResult(BaseModel):
    """Result from Baron's specify workflow.

    Parsed from Baron's structured output between result markers.
    """

    success: bool = Field(..., description="Whether workflow completed successfully")
    spec_path: Path | None = Field(default=None, description="Path to created spec.md")
    feature_id: str | None = Field(
        default=None, description="Feature directory name (e.g., '008-oauth2-auth')"
    )
    branch_name: str | None = Field(default=None, description="Git branch name")
    error: str | None = Field(default=None, description="Error message if failed")
    duration_seconds: float = Field(default=0.0, ge=0, description="Time taken in seconds")


class PlanRequest(BaseModel):
    """Request to dispatch Baron for the plan workflow.

    Creates implementation plan and design artifacts from spec.md.
    """

    spec_path: Path = Field(..., description="Path to spec.md file")
    force_research: bool = Field(default=False, description="Force re-run of research phase")


class PlanResult(BaseModel):
    """Result from Baron's plan workflow.

    Parsed from Baron's structured output between result markers.
    """

    success: bool = Field(..., description="Whether workflow completed successfully")
    plan_path: Path | None = Field(default=None, description="Path to created plan.md")
    research_path: Path | None = Field(default=None, description="Path to research.md")
    data_model_path: Path | None = Field(default=None, description="Path to data-model.md")
    contracts_dir: Path | None = Field(default=None, description="Path to contracts/ directory")
    quickstart_path: Path | None = Field(default=None, description="Path to quickstart.md")
    error: str | None = Field(default=None, description="Error message if failed")
    blocked_on_escalation: bool = Field(
        default=False, description="Whether waiting for human input"
    )
    duration_seconds: float = Field(default=0.0, ge=0, description="Time taken in seconds")


class TasksRequest(BaseModel):
    """Request to dispatch Baron for the tasks workflow.

    Creates task list (tasks.md) from plan.md with TDD ordering.
    """

    plan_path: Path = Field(..., description="Path to plan.md file")


class TasksResult(BaseModel):
    """Result from Baron's tasks workflow.

    Parsed from Baron's structured output between result markers.
    """

    success: bool = Field(..., description="Whether workflow completed successfully")
    tasks_path: Path | None = Field(default=None, description="Path to created tasks.md")
    task_count: int = Field(default=0, ge=0, description="Number of tasks generated")
    test_count: int = Field(default=0, ge=0, description="Number of test tasks (TDD)")
    error: str | None = Field(default=None, description="Error message if failed")
    duration_seconds: float = Field(default=0.0, ge=0, description="Time taken in seconds")
