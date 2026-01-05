"""API endpoints for Baron agent service."""

from src.api.health import router as health_router
from src.api.invoke import router as invoke_router

__all__ = ["health_router", "invoke_router"]
