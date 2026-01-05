"""GET /health endpoint for Agent Hub service.

This endpoint provides health check information per contracts/agent-hub.yaml.
"""

import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.core.router import get_router

router = APIRouter()

# Track service start time
_start_time = time.time()


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str = Field(..., description="healthy, degraded, or unhealthy")
    version: str
    uptime_seconds: int | None = None
    connected_agents: list[str] | None = None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Get Agent Hub health status.

    Returns:
        HealthResponse with status and connected agents
    """
    agent_router = get_router()
    uptime = int(time.time() - _start_time)

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        uptime_seconds=uptime,
        connected_agents=agent_router.available_agents,
    )
