"""Shared fixtures for Agent Hub tests."""

import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set test database URL before importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def mock_agent_client() -> Generator[AsyncMock, None, None]:
    """Mock the AgentServiceClient for all tests.

    This prevents tests from making actual HTTP calls to agent services.
    """
    mock_response = {
        "success": True,
        "result": {"output": "Test answer from mocked agent."},
        "confidence": 85,
        "metadata": {},
    }

    with (
        patch("src.api.ask.AgentServiceClient") as mock_ask,
        patch("src.api.invoke.AgentServiceClient") as mock_invoke,
    ):
        # Setup mock for ask endpoint
        mock_agent_ask = AsyncMock()
        mock_agent_ask.invoke.return_value = mock_response
        mock_agent_ask.__aenter__.return_value = mock_agent_ask
        mock_agent_ask.__aexit__.return_value = None
        mock_ask.return_value = mock_agent_ask

        # Setup mock for invoke endpoint
        mock_agent_invoke = AsyncMock()
        mock_agent_invoke.invoke.return_value = mock_response
        mock_agent_invoke.__aenter__.return_value = mock_agent_invoke
        mock_agent_invoke.__aexit__.return_value = None
        mock_invoke.return_value = mock_agent_invoke

        yield mock_agent_ask


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio backend for tests."""
    return "asyncio"


@pytest.fixture
def test_db() -> Generator[Session, None, None]:
    """Create a test database session."""
    from src.db.models import Base

    # Create in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client for Agent Hub service.

    Note: This fixture will work once src/main.py is created.
    """
    from src.db.models import Base
    from src.db.session import engine
    from src.main import app

    # Initialize tables
    Base.metadata.create_all(bind=engine)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def sample_invoke_request() -> dict[str, Any]:
    """Sample invoke request for agent invocation."""
    return {
        "workflow_type": "specify",
        "context": {
            "feature_description": "Add user authentication",
        },
        "parameters": {},
    }


@pytest.fixture
def sample_ask_request() -> dict[str, Any]:
    """Sample ask request for expert consultation."""
    return {
        "question": "What authentication method should we use for the API?",
        "context": "Building a REST API for web and mobile clients",
        "feature_id": "008-services-architecture",
    }
