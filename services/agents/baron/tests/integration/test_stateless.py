"""Integration tests for stateless agent invocation.

These tests verify Baron processes requests statelessly:
- All context passed in request
- No server-side session storage
- Independent requests produce independent results
"""


import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestStatelessInvocation:
    """Integration tests for stateless agent behavior."""

    async def test_invoke_processes_complete_context(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Baron processes all context passed in request."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {
                    "feature_description": "Add user authentication with OAuth2",
                    "requirements": [
                        "Support Google and GitHub OAuth",
                        "Store user sessions securely",
                    ],
                },
                "parameters": {
                    "priority": "P1",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Agent should use the provided context
        assert data["result"] is not None

    async def test_independent_requests_produce_independent_results(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Two independent requests don't share state."""
        # First request
        response1 = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {"feature_description": "Feature A"},
            },
        )

        # Second request with different context
        response2 = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {"feature_description": "Feature B"},
            },
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should succeed independently
        data1 = response1.json()
        data2 = response2.json()
        assert data1["success"] is True
        assert data2["success"] is True

    async def test_no_session_id_required(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Requests work without session_id (stateless)."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {"feature_description": "Stateless feature"},
                # No session_id - should work
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_result_contains_output(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Invoke result contains output from agent."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {"feature_description": "Test feature for output"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        # Result should have some output
        result = data["result"]
        assert result.get("output") is not None or result.get("data") is not None

    async def test_metadata_includes_timing(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Invoke metadata includes execution timing."""
        response = await test_client.post(
            "/invoke",
            json={
                "workflow_type": "specify",
                "context": {"feature_description": "Timing test"},
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "metadata" in data
        assert "duration_ms" in data["metadata"]
        assert data["metadata"]["duration_ms"] > 0

    async def test_all_workflow_types_supported(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Baron supports specify, plan, tasks, implement workflow types."""
        workflow_types = ["specify", "plan", "tasks", "implement"]

        for wf_type in workflow_types:
            response = await test_client.post(
                "/invoke",
                json={
                    "workflow_type": wf_type,
                    "context": {"feature_description": f"Test {wf_type}"},
                },
            )

            assert response.status_code == 200, f"Failed for {wf_type}"
            data = response.json()
            assert data["success"] is True, f"Failed for {wf_type}"
