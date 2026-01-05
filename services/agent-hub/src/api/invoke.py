"""POST /invoke/{agent} endpoint for Agent Hub.

This endpoint handles direct agent invocation per contracts/agent-hub.yaml.
"""

import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.clients.agents import AgentServiceClient, AgentServiceError
from src.core.router import UnknownAgentError, get_router
from src.logging.audit import get_audit_logger

router = APIRouter()


class InvokeRequest(BaseModel):
    """Request body for /invoke/{agent} endpoint."""

    workflow_type: str = Field(
        ...,
        description="Type of workflow (e.g., specify, plan, tasks)",
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

    duration_ms: int | None = None
    model_used: str | None = None


class InvokeResult(BaseModel):
    """Result from agent processing."""

    output: str | None = None
    files_created: list[str] | None = None
    files_read: list[str] | None = None
    uncertainty_reasons: list[str] | None = None
    data: dict[str, Any] | None = None


class InvokeResponse(BaseModel):
    """Response from /invoke/{agent} endpoint."""

    success: bool
    result: InvokeResult | dict[str, Any]
    confidence: int = Field(..., ge=0, le=100)
    metadata: InvokeMetadata | dict[str, Any] | None = None
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
    "/invoke/{agent}",
    response_model=InvokeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Agent not found"},
        504: {"model": ErrorResponse, "description": "Agent timeout"},
    },
)
async def invoke_agent(agent: str, request: InvokeRequest) -> InvokeResponse:
    """Invoke a specific agent with a workflow request.

    Args:
        agent: Agent name (e.g., baron, duc, marie)
        request: InvokeRequest with workflow_type, context, parameters

    Returns:
        InvokeResponse with result and metadata

    Raises:
        HTTPException: On validation or execution error
    """
    start_time = time.time()
    audit_logger = get_audit_logger()
    agent_router = get_router()

    # Validate agent exists
    try:
        agent_config = agent_router.get_agent_config(agent)
    except UnknownAgentError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "AGENT_NOT_FOUND",
                    "message": str(e),
                    "details": [f"Available agents: {e.available_agents}"],
                }
            },
        ) from e

    # Validate request
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

    # Invoke agent service
    agent_url = agent_config.get("url", f"http://{agent}:8000")

    try:
        async with AgentServiceClient(agent_url, agent_name=agent) as client:
            result = await client.invoke(
                workflow_type=request.workflow_type,
                context=request.context,
                parameters=request.parameters,
                session_id=request.session_id,
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            confidence = result.get("confidence", 85)

            # Extract output for logging
            result_data = result.get("result", {})
            output = (
                result_data.get("output", str(result_data))
                if isinstance(result_data, dict)
                else str(result_data)
            )

            # Log the invocation
            audit_logger.log(
                feature_id=request.context.get("feature_id", "unknown"),
                topic=f"{agent}/{request.workflow_type}",
                question=f"Invoke {request.workflow_type}",
                answer=output[:500] if len(output) > 500 else output,
                confidence=confidence,
                status="resolved",
                duration_ms=duration_ms,
                session_id=request.session_id,
                metadata={"agent": agent, "workflow_type": request.workflow_type},
            )

            return InvokeResponse(
                success=result.get("success", True),
                result=result_data,
                confidence=confidence,
                metadata=result.get("metadata"),
            )

    except AgentServiceError as e:
        if e.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": e.code,
                        "message": str(e),
                    }
                },
            ) from e

        raise HTTPException(
            status_code=504 if "timeout" in str(e).lower() else 500,
            detail={
                "error": {
                    "code": "AGENT_INVOCATION_FAILED",
                    "message": str(e),
                }
            },
        ) from e
