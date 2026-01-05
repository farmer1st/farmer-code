"""Health endpoint for Duc agent service."""

from fastapi import APIRouter

from src.core.agent import DucAgent

router = APIRouter()

# Shared agent instance for health checks
_agent = DucAgent()


@router.get("/health")
async def health() -> dict:
    """Health check endpoint.

    Returns:
        Health status of the agent
    """
    return _agent.get_health()
