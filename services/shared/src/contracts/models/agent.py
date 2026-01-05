"""Agent models for Agent Services.

These models define the request/response format for agent invocation
per contracts/agent-service.yaml.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    """Request to invoke an agent."""

    workflow_type: str = Field(
        ...,
        description="Type of workflow or task (e.g., specify, plan, tasks, implement)",
    )
    context: dict[str, Any] = Field(
        ...,
        description="Context for the agent (varies by workflow_type)",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for customization",
    )
    session_id: UUID | None = Field(
        default=None,
        description="Session ID for multi-turn conversations",
    )


class InvokeMetadata(BaseModel):
    """Metadata about the agent invocation."""

    duration_ms: int = Field(..., description="Execution time in milliseconds")
    model_used: str = Field(..., description="Claude model used")
    tools_used: list[str] | None = Field(
        default=None,
        description="Tools invoked during execution",
    )
    tokens_used: int | None = Field(
        default=None,
        description="Approximate tokens consumed",
    )


class InvokeResult(BaseModel):
    """Result from agent processing."""

    output: str | None = Field(
        default=None,
        description="Primary text output",
    )
    files_created: list[str] | None = Field(
        default=None,
        description="List of files created/modified",
    )
    files_read: list[str] | None = Field(
        default=None,
        description="List of files read",
    )
    uncertainty_reasons: list[str] | None = Field(
        default=None,
        description="Reasons for low confidence (if applicable)",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional structured output",
    )


class InvokeResponse(BaseModel):
    """Response from agent invocation."""

    success: bool = Field(..., description="Whether invocation completed successfully")
    result: InvokeResult = Field(..., description="Agent output")
    confidence: int = Field(..., ge=0, le=100, description="Confidence level (0-100)")
    metadata: InvokeMetadata = Field(..., description="Execution metadata")
    error: str | None = Field(
        default=None,
        description="Error message if success is false",
    )
    escalation_id: UUID | None = Field(
        default=None,
        description="Escalation ID if low confidence triggered escalation",
    )


class HealthCapabilities(BaseModel):
    """Agent capabilities reported in health check."""

    workflow_types: list[str] = Field(
        default_factory=list,
        description="Supported workflow types",
    )
    tools: list[str] = Field(
        default_factory=list,
        description="Available Claude Code tools",
    )
    mcp_servers: list[str] = Field(
        default_factory=list,
        description="Connected MCP servers",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Available skills",
    )


class HealthResponse(BaseModel):
    """Health check response for agent services."""

    status: str = Field(..., description="healthy, degraded, or unhealthy")
    version: str = Field(..., description="Service version")
    agent_name: str = Field(..., description="Agent identifier (baron, duc, marie)")
    uptime_seconds: int | None = Field(
        default=None,
        description="Time since service started",
    )
    capabilities: HealthCapabilities | None = Field(
        default=None,
        description="Agent capabilities",
    )


class ErrorDetail(BaseModel):
    """Error response structure."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: list[str] | None = Field(
        default=None,
        description="Additional error details",
    )


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    error: ErrorDetail
