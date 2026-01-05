"""FastAPI application for Marie agent service."""

from fastapi import FastAPI

from src.api.health import router as health_router
from src.api.invoke import router as invoke_router

app = FastAPI(
    title="Marie Agent Service",
    description="Testing Expert Agent for Farmer Code",
    version="0.1.0",
)

# Mount routers
app.include_router(health_router, tags=["health"])
app.include_router(invoke_router, tags=["invoke"])
