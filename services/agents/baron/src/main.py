"""FastAPI application for Baron agent service.

This is the main entry point for the Baron agent service.
"""

from fastapi import FastAPI

from src import __version__
from src.api.health import router as health_router
from src.api.invoke import router as invoke_router

app = FastAPI(
    title="Baron Agent Service",
    description=(
        "Baron is a stateless agent service for SpecKit workflows. "
        "It handles specify, plan, tasks, and implement workflows using the Claude Code SDK."
    ),
    version=__version__,
)

# Include routers
app.include_router(invoke_router, tags=["invoke"])
app.include_router(health_router, tags=["health"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with service info."""
    return {
        "service": "baron",
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
