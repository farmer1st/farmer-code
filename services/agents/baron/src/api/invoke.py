"""POST /invoke endpoint for Baron agent service.

This endpoint handles workflow invocation requests per contracts/agent-service.yaml.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.agent import AgentError, BaronAgent

router = APIRouter()

# Singleton agent instance
_agent: BaronAgent | None = None


def get_agent() -> BaronAgent:
    """Get or create the Baron agent instance."""
    global _agent
    if _agent is None:
        _agent = BaronAgent()
    return _agent


class InvokeRequest(BaseModel):
    """Request body for /invoke endpoint."""

    workflow_type: str = Field(
        ...,
        description="Type of workflow (specify, plan, tasks, implement)",
    )
    context: dict[str, Any] = Field(
        ...,
        description="Context for the agent",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters",
    )
    session_id: UUID | None = Field(
        default=None,
        description="Optional session ID",
    )


class InvokeMetadata(BaseModel):
    """Metadata about the invocation."""

    duration_ms: int
    model_used: str
    tools_used: list[str] | None = None
    tokens_used: int | None = None


class InvokeResult(BaseModel):
    """Result from agent processing."""

    output: str | None = None
    files_created: list[str] | None = None
    files_read: list[str] | None = None
    uncertainty_reasons: list[str] | None = None
    data: dict[str, Any] | None = None


class InvokeResponse(BaseModel):
    """Response from /invoke endpoint."""

    success: bool
    result: InvokeResult
    confidence: int = Field(..., ge=0, le=100)
    metadata: InvokeMetadata
    error: str | None = None
    escalation_id: UUID | None = None


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: list[str] | None = None


class ErrorResponse(BaseModel):
    """Error response structure."""

    error: ErrorDetail


@router.post(
    "/invoke",
    response_model=InvokeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Agent execution failed"},
        504: {"model": ErrorResponse, "description": "Agent timeout"},
    },
)
async def invoke(request: InvokeRequest) -> InvokeResponse:
    """Invoke the Baron agent with a workflow request.

    Args:
        request: InvokeRequest with workflow_type, context, parameters

    Returns:
        InvokeResponse with result and metadata

    Raises:
        HTTPException: On validation or execution error
    """
    agent = get_agent()

    # Validate workflow type
    if request.workflow_type not in agent.supported_workflows:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "UNKNOWN_WORKFLOW_TYPE",
                    "message": f"Unknown workflow type: {request.workflow_type}",
                    "details": [f"Valid types: {agent.supported_workflows}"],
                }
            },
        )

    # Validate context
    if not request.context:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Context is required",
                }
            },
        )

    try:
        result = await agent.invoke(
            workflow_type=request.workflow_type,
            context=request.context,
            parameters=request.parameters,
            session_id=request.session_id,
        )

        return InvokeResponse(
            success=result["success"],
            result=InvokeResult(**result["result"]),
            confidence=result["confidence"],
            metadata=InvokeMetadata(**result["metadata"]),
        )

    except AgentError as e:
        raise HTTPException(
            status_code=400 if e.code == "UNKNOWN_WORKFLOW_TYPE" else 500,
            detail={
                "error": {
                    "code": e.code,
                    "message": str(e),
                }
            },
        ) from e
