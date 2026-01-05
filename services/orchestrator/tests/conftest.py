"""Shared fixtures for Orchestrator service tests."""

from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio backend for tests."""
    return "asyncio"


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client for Orchestrator service.

    Note: This fixture will work once src/main.py is created.
    For now, tests will fail with import error (expected in TDD).
    """
    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def sample_create_workflow_request() -> dict[str, Any]:
    """Sample create workflow request for tests."""
    return {
        "workflow_type": "specify",
        "feature_description": "Add user authentication with OAuth2",
        "context": {
            "priority": "P1",
        },
    }


@pytest.fixture
def sample_workflow_response() -> dict[str, Any]:
    """Sample workflow response for tests."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "workflow_type": "specify",
        "status": "pending",
        "feature_id": "009-user-auth",
        "current_phase": None,
        "result": None,
        "error": None,
        "created_at": "2026-01-05T12:00:00Z",
        "updated_at": "2026-01-05T12:00:00Z",
        "completed_at": None,
    }


@pytest.fixture
def sample_advance_request() -> dict[str, Any]:
    """Sample advance workflow request for tests."""
    return {
        "trigger": "human_approved",
        "phase_result": {
            "approved": True,
            "comments": "LGTM",
        },
    }
