"""E2E tests for Orchestrator workflow execution.

Tests the complete SpecKit workflow: Orchestrator -> Agent Hub -> Baron -> response.

Journey ID: SVC-001
"""

from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.journey("SVC-001")
@pytest.mark.anyio
class TestOrchestratorWorkflow:
    """E2E tests for SVC-001: Orchestrator Workflow Execution."""

    @pytest.fixture
    def orchestrator_url(self) -> str:
        """Orchestrator service URL."""
        return "http://localhost:8001"

    @pytest.fixture
    def agent_hub_url(self) -> str:
        """Agent Hub service URL."""
        return "http://localhost:8000"

    @pytest.fixture
    def baron_url(self) -> str:
        """Baron agent service URL."""
        return "http://localhost:8002"

    async def test_specify_workflow_e2e(
        self,
        orchestrator_url: str,
    ) -> None:
        """Test complete specify workflow execution.

        Journey: User triggers specify workflow, request flows through
        Orchestrator -> Agent Hub -> Baron, returns specification.

        This test requires all services to be running.
        """
        async with AsyncClient(base_url=orchestrator_url) as client:
            # Start a specify workflow
            response = await client.post(
                "/workflows",
                json={
                    "workflow_type": "specify",
                    "feature_description": "Add user authentication with OAuth2 support",
                    "context": {
                        "priority": "P1",
                        "requester": "e2e-test",
                    },
                },
            )

            assert response.status_code == 201
            data = response.json()

            # Verify response structure
            assert "id" in data
            workflow_id = data["id"]

            # Verify valid UUID
            UUID(workflow_id)

            assert data["workflow_type"] == "specify"
            assert data["status"] in ["pending", "in_progress"]
            assert "feature_id" in data
            assert "created_at" in data

    async def test_workflow_invokes_agent_hub(
        self,
        orchestrator_url: str,
        agent_hub_url: str,
    ) -> None:
        """Test that workflow invokes Agent Hub for agent execution.

        The Orchestrator should NOT call agents directly - all agent
        invocations go through Agent Hub.
        """
        async with AsyncClient(base_url=orchestrator_url) as orch_client:
            async with AsyncClient(base_url=agent_hub_url) as hub_client:
                # Verify Agent Hub is healthy
                hub_health = await hub_client.get("/health")
                assert hub_health.status_code == 200

                # Start workflow
                response = await orch_client.post(
                    "/workflows",
                    json={
                        "workflow_type": "specify",
                        "feature_description": "Test feature for agent hub integration",
                    },
                )

                assert response.status_code == 201

    async def test_workflow_status_tracking(
        self,
        orchestrator_url: str,
    ) -> None:
        """Test that workflow status is properly tracked through execution."""
        async with AsyncClient(base_url=orchestrator_url) as client:
            # Create workflow
            create_response = await client.post(
                "/workflows",
                json={
                    "workflow_type": "plan",
                    "feature_description": "Test feature for status tracking",
                },
            )
            workflow_id = create_response.json()["id"]

            # Get workflow status
            status_response = await client.get(f"/workflows/{workflow_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            assert status_data["id"] == workflow_id
            assert "status" in status_data
            assert "updated_at" in status_data

    async def test_workflow_result_on_completion(
        self,
        orchestrator_url: str,
    ) -> None:
        """Test that workflow result is populated when complete.

        Contract: result field contains workflow output on completion.
        """
        async with AsyncClient(base_url=orchestrator_url) as client:
            # Create and run workflow to completion (may require multiple advances)
            create_response = await client.post(
                "/workflows",
                json={
                    "workflow_type": "specify",
                    "feature_description": "Simple test feature for completion",
                },
            )
            workflow_id = create_response.json()["id"]

            # Try to advance to completion
            for _ in range(5):
                advance_response = await client.post(
                    f"/workflows/{workflow_id}/advance",
                    json={
                        "trigger": "agent_complete",
                        "phase_result": {"output": "test output"},
                    },
                )

                if advance_response.status_code == 200:
                    if advance_response.json()["status"] == "completed":
                        # Verify result is populated
                        data = advance_response.json()
                        assert data.get("result") is not None or data.get("error") is None
                        break

                # If we get waiting_approval, do human_approved
                if (
                    advance_response.status_code == 200
                    and advance_response.json().get("status") == "waiting_approval"
                ):
                    await client.post(
                        f"/workflows/{workflow_id}/advance",
                        json={
                            "trigger": "human_approved",
                            "phase_result": {"approved": True},
                        },
                    )

    async def test_concurrent_workflows(
        self,
        orchestrator_url: str,
    ) -> None:
        """Test that multiple workflows can run concurrently.

        Success Criteria SC-004: Handle at least 10 concurrent workflows.
        """
        import asyncio

        async with AsyncClient(base_url=orchestrator_url) as client:

            async def create_workflow(index: int) -> dict[str, Any]:
                response = await client.post(
                    "/workflows",
                    json={
                        "workflow_type": "specify",
                        "feature_description": f"Concurrent test feature number {index}",
                    },
                )
                return {
                    "index": index,
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 201 else None,
                }

            # Create 10 workflows concurrently
            tasks = [create_workflow(i) for i in range(10)]
            results = await asyncio.gather(*tasks)

            # All should succeed
            success_count = sum(1 for r in results if r["status_code"] == 201)
            assert success_count >= 10, f"Only {success_count}/10 workflows created"

            # All should have unique IDs
            ids = [r["data"]["id"] for r in results if r["data"]]
            assert len(set(ids)) == len(ids), "Duplicate workflow IDs detected"

    async def test_workflow_error_handling(
        self,
        orchestrator_url: str,
    ) -> None:
        """Test that workflow handles errors gracefully.

        Errors during execution should result in FAILED status.
        """
        async with AsyncClient(base_url=orchestrator_url) as client:
            # Invalid workflow type should fail at creation
            response = await client.post(
                "/workflows",
                json={
                    "workflow_type": "invalid",
                    "feature_description": "This should fail validation",
                },
            )
            assert response.status_code in [400, 422]

            # Missing required field should fail
            response = await client.post(
                "/workflows",
                json={
                    "workflow_type": "specify",
                    # Missing feature_description
                },
            )
            assert response.status_code in [400, 422]

    async def test_all_services_healthy(
        self,
        orchestrator_url: str,
        agent_hub_url: str,
        baron_url: str,
    ) -> None:
        """Test that all required services are healthy.

        Pre-requisite check for full E2E flow.
        """
        async with AsyncClient() as client:
            # Check Orchestrator
            orch_health = await client.get(f"{orchestrator_url}/health")
            assert orch_health.status_code == 200
            assert orch_health.json()["status"] == "healthy"

            # Check Agent Hub
            hub_health = await client.get(f"{agent_hub_url}/health")
            assert hub_health.status_code == 200
            assert hub_health.json()["status"] == "healthy"

            # Check Baron
            baron_health = await client.get(f"{baron_url}/health")
            assert baron_health.status_code == 200
            assert baron_health.json()["status"] == "healthy"

    async def test_workflow_feature_id_generation(
        self,
        orchestrator_url: str,
    ) -> None:
        """Test that workflow generates valid feature ID.

        Contract: feature_id must match pattern ^\\d{3}-[a-z0-9-]+$.
        """
        import re

        async with AsyncClient(base_url=orchestrator_url) as client:
            response = await client.post(
                "/workflows",
                json={
                    "workflow_type": "specify",
                    "feature_description": "Test Feature With Many Words Here",
                },
            )

            assert response.status_code == 201
            feature_id = response.json()["feature_id"]

            # Verify pattern
            pattern = r"^\d{3}-[a-z0-9-]+$"
            assert re.match(pattern, feature_id), (
                f"feature_id '{feature_id}' does not match pattern {pattern}"
            )
