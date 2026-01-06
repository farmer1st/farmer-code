"""POST /invoke endpoint for Duc agent service."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.agent import AgentError, DucAgent

router = APIRouter()


class InvokeRequest(BaseModel):
    """Request body for /invoke endpoint."""

    topic: str = Field(
        ...,
        description="Topic type (architecture, api_design, system_design)",
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
        description="Optional session ID for logging",
    )


class InvokeMetadata(BaseModel):
    """Metadata about the invocation."""

    duration_ms: int | None = None
    agent_name: str | None = None
    topic: str | None = None


class InvokeResult(BaseModel):
    """Result from agent processing."""

    output: str | None = None
    answer: str | None = None


class InvokeResponse(BaseModel):
    """Response from /invoke endpoint."""

    success: bool
    result: InvokeResult | dict[str, Any]
    confidence: int = Field(..., ge=0, le=100)
    metadata: InvokeMetadata | dict[str, Any] | None = None
    error: str | None = None


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response structure."""

    error: ErrorDetail


@router.post(
    "/invoke",
    response_model=InvokeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def invoke_agent(request: InvokeRequest) -> InvokeResponse:
    """Invoke Duc agent with a topic request.

    Args:
        request: InvokeRequest with topic, context, parameters

    Returns:
        InvokeResponse with result and metadata

    Raises:
        HTTPException: On validation or execution error
    """
    agent = DucAgent()

    try:
        result = await agent.invoke(
            topic=request.topic,
            context=request.context,
            parameters=request.parameters,
            session_id=request.session_id,
        )

        return InvokeResponse(
            success=result["success"],
            result=result["result"],
            confidence=result["confidence"],
            metadata=result.get("metadata"),
        )

    except AgentError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": e.code,
                    "message": str(e),
                }
            },
        ) from e
