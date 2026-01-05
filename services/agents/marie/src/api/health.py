"""Health endpoint for Marie agent service."""

from fastapi import APIRouter

from src.core.agent import MarieAgent

router = APIRouter()

# Shared agent instance for health checks
_agent = MarieAgent()


@router.get("/health")
async def health() -> dict:
    """Health check endpoint.

    Returns:
        Health status of the agent
    """
    return _agent.get_health()
