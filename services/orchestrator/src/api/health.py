"""GET /health endpoint for Orchestrator service.

This endpoint provides health check information per contracts/orchestrator.yaml.
"""

import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src import __version__

router = APIRouter()

# Track service start time
_start_time = time.time()


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str = Field(..., description="healthy, degraded, or unhealthy")
    version: str
    uptime_seconds: int | None = None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Get Orchestrator health status.

    Returns:
        HealthResponse with status and uptime
    """
    uptime = int(time.time() - _start_time)

    return HealthResponse(
        status="healthy",
        version=__version__,
        uptime_seconds=uptime,
    )
