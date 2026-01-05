"""API endpoints for Agent Hub service."""

from src.api.ask import router as ask_router
from src.api.health import router as health_router
from src.api.invoke import router as invoke_router

__all__ = ["ask_router", "health_router", "invoke_router"]
