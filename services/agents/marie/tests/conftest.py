"""Shared fixtures for Marie agent tests."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio backend for tests."""
    return "asyncio"


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client for Marie agent service."""
    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def sample_invoke_request() -> dict[str, Any]:
    """Sample invoke request for testing question."""
    return {
        "topic": "testing",
        "context": {
            "question": "How should I test this API endpoint?",
        },
        "parameters": {},
    }
