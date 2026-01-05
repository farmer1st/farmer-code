"""FastAPI application for Agent Hub service.

This is the main entry point for the Agent Hub service.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src import __service_name__, __version__
from src.api.ask import router as ask_router
from src.api.escalations import router as escalations_router
from src.api.health import router as health_router
from src.api.invoke import router as invoke_router
from src.api.sessions import router as sessions_router
from src.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application lifespan handler.

    Initializes database on startup.
    """
    # Initialize database tables
    init_db()
    yield


app = FastAPI(
    title="Agent Hub Service",
    description=(
        "The Agent Hub Service is the central coordination layer for all agent interactions. "
        "It routes requests to agent services, validates confidence, manages sessions, "
        "and handles human escalation via GitHub comments."
    ),
    version=__version__,
    lifespan=lifespan,
)

# Include routers
app.include_router(invoke_router, tags=["invoke"])
app.include_router(ask_router, tags=["ask"])
app.include_router(sessions_router, tags=["sessions"])
app.include_router(escalations_router, tags=["escalations"])
app.include_router(health_router, tags=["health"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with service info."""
    return {
        "service": __service_name__,
        "version": __version__,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
