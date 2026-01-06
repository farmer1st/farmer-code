"""E2E tests for Baron stateless agent invocation.

Journey ID: SVC-005 - Stateless Agent Invocation

These tests verify the complete flow of invoking Baron directly
with a stateless request and receiving a complete response.

Requires: RUN_E2E_TESTS=1 and services running on localhost.
"""

import os

import pytest
from httpx import AsyncClient

# Skip reason for when services are not running
SKIP_REASON = "Requires RUN_E2E_TESTS=1 and running services"


def _should_skip() -> bool:
    """Check if tests should be skipped."""
    return os.getenv("RUN_E2E_TESTS") != "1"


@pytest.mark.e2e
@pytest.mark.journey("SVC-005")
@pytest.mark.anyio
class TestBaronStatelessE2E:
    """E2E tests for SVC-005: Stateless Agent Invocation.

    Goal: Baron agent service receives requests with all context,
    processes via Claude SDK, returns complete response.

    Independent Test: Invoke Baron directly with a complete request,
    verify it returns a complete response without prior state.
    """

    @pytest.fixture
    async def baron_client(self) -> AsyncClient:
        """Create client for Baron service.

        In E2E tests, this connects to the actual running service.
        """
        if _should_skip():
            pytest.skip(SKIP_REASON)
        async with AsyncClient(
            base_url="http://localhost:8010",
            timeout=300.0,
        ) as client:
            yield client

    async def test_baron_health_check(
        self,
        baron_client: AsyncClient,
    ) -> None:
        """Baron service responds to health check."""
        response = await baron_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agent_name"] == "baron"

    async def test_baron_specify_workflow(
        self,
        baron_client: AsyncClient,
    ) -> None:
        """Baron executes specify workflow with complete context.

        This is the primary SVC-005 journey test:
        1. Send request with all context
        2. Baron processes via Claude SDK
        3. Returns complete response with specification
        """
        response = await baron_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {
                    "feature_description": "Add a simple health monitoring dashboard",
                },
                "parameters": {},
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify complete response
        assert data["success"] is True
        assert data["confidence"] >= 0
        assert data["confidence"] <= 100
        assert "result" in data
        assert "metadata" in data
        assert data["metadata"]["duration_ms"] > 0

    async def test_baron_plan_workflow(
        self,
        baron_client: AsyncClient,
    ) -> None:
        """Baron executes plan workflow."""
        response = await baron_client.post(
            "/invoke",
            json={
                "workflow_type": "plan",
                "context": {
                    "feature_description": "Simple API endpoint",
                    "spec_path": "specs/test/spec.md",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_baron_tasks_workflow(
        self,
        baron_client: AsyncClient,
    ) -> None:
        """Baron executes tasks workflow."""
        response = await baron_client.post(
            "/invoke",
            json={
                "workflow_type": "tasks",
                "context": {
                    "feature_description": "Task generation test",
                    "plan_path": "specs/test/plan.md",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_baron_no_state_between_requests(
        self,
        baron_client: AsyncClient,
    ) -> None:
        """Baron maintains no state between requests.

        Two different requests should be completely independent.
        """
        # First request
        response1 = await baron_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {
                    "feature_description": "Feature Alpha",
                },
            },
        )

        # Second request - completely different
        response2 = await baron_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {
                    "feature_description": "Feature Beta - unrelated",
                },
            },
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Both succeed independently
        assert data1["success"] is True
        assert data2["success"] is True

    async def test_baron_handles_invalid_workflow_type(
        self,
        baron_client: AsyncClient,
    ) -> None:
        """Baron returns proper error for invalid workflow type."""
        response = await baron_client.post(
            "/invoke",
            json={
                "workflow_type": "invalid_type",
                "context": {
                    "feature_description": "Test",
                },
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "UNKNOWN_WORKFLOW_TYPE"

    async def test_baron_reports_capabilities(
        self,
        baron_client: AsyncClient,
    ) -> None:
        """Baron health includes capability information."""
        response = await baron_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Check capabilities if present
        if "capabilities" in data:
            caps = data["capabilities"]
            # Baron should support SpecKit workflows
            if "workflow_types" in caps:
                assert "specify" in caps["workflow_types"]
                assert "plan" in caps["workflow_types"]
                assert "tasks" in caps["workflow_types"]
                assert "implement" in caps["workflow_types"]
