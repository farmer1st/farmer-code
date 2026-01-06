"""Shared fixtures for Baron agent tests."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

# Import will work once main.py is created
# from src.main import app


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio backend for tests."""
    return "asyncio"


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client for Baron service.

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
def sample_invoke_request() -> dict[str, Any]:
    """Sample invoke request for tests."""
    return {
        "workflow_type": "specify",
        "context": {
            "feature_description": "Add user authentication with OAuth2",
        },
        "parameters": {
            "priority": "P1",
        },
    }


@pytest.fixture
def sample_invoke_response() -> dict[str, Any]:
    """Sample invoke response for tests."""
    return {
        "success": True,
        "result": {
            "output": "# Feature Specification...",
            "files_created": ["specs/001-auth/spec.md"],
        },
        "confidence": 92,
        "metadata": {
            "duration_ms": 15234,
            "model_used": "claude-3-5-sonnet-20241022",
        },
    }
