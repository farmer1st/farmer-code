"""FastAPI application for Duc agent service."""

from fastapi import FastAPI

from src.api.health import router as health_router
from src.api.invoke import router as invoke_router

app = FastAPI(
    title="Duc Agent Service",
    description="Architecture Expert Agent for Farmer Code",
    version="0.1.0",
)

# Mount routers
app.include_router(health_router, tags=["health"])
app.include_router(invoke_router, tags=["invoke"])
