"""FastAPI application for Orchestrator service.

This is the main entry point for the Orchestrator service.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src import __service_name__, __version__
from src.api.health import router as health_router
from src.api.workflows import router as workflows_router
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
    title="Orchestrator Service",
    description=(
        "The Orchestrator Service manages SpecKit workflow execution. "
        "It owns workflow definitions (specify, plan, tasks, implement) "
        "and manages state transitions. All agent invocations go through "
        "the Agent Hub Service."
    ),
    version=__version__,
    lifespan=lifespan,
)

# Include routers
app.include_router(workflows_router, tags=["workflows"])
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
        port=8001,  # Orchestrator runs on 8001
        reload=True,
    )
