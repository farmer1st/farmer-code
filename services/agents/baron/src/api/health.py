"""GET /health endpoint for Baron agent service.

This endpoint provides health check information per contracts/agent-service.yaml.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.invoke import get_agent

router = APIRouter()


class HealthCapabilities(BaseModel):
    """Agent capabilities."""

    workflow_types: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    mcp_servers: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str = Field(..., description="healthy, degraded, or unhealthy")
    version: str
    agent_name: str
    uptime_seconds: int | None = None
    capabilities: HealthCapabilities | None = None


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Get Baron agent health status.

    Returns:
        HealthResponse with status and capabilities
    """
    agent = get_agent()
    health_data = agent.get_health()

    return HealthResponse(
        status=health_data["status"],
        version=health_data["version"],
        agent_name=health_data["agent_name"],
        uptime_seconds=health_data.get("uptime_seconds"),
        capabilities=HealthCapabilities(**health_data.get("capabilities", {})),
    )
