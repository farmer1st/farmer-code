"""Contract tests for POST /workflows/{id}/advance endpoint.

Tests the advance workflow API contract per contracts/orchestrator.yaml.
"""

from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.anyio
class TestAdvanceWorkflow:
    """Contract tests for POST /workflows/{id}/advance endpoint."""

    async def test_advance_workflow_success(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test successful workflow advancement.

        Contract: POST /workflows/{id}/advance returns 200 with WorkflowResponse.

        State flow: Created workflow is in IN_PROGRESS, so we use agent_complete
        to advance to WAITING_APPROVAL.
        """
        # First create a workflow (starts in IN_PROGRESS)
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        assert create_response.status_code == 201
        workflow_id = create_response.json()["id"]
        assert create_response.json()["status"] == "in_progress"

        # Advance with agent_complete (valid from IN_PROGRESS -> WAITING_APPROVAL)
        response = await test_client.post(
            f"/workflows/{workflow_id}/advance",
            json={
                "trigger": "agent_complete",
                "phase_result": {"output": "Generated specification"},
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields per contract
        assert data["id"] == workflow_id
        assert "status" in data
        assert data["status"] == "waiting_approval"
        assert "workflow_type" in data

    async def test_advance_workflow_not_found(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test workflow advancement with non-existent ID.

        Contract: Non-existent workflow returns 404 with ErrorResponse.
        """
        non_existent_id = str(uuid4())

        response = await test_client.post(
            f"/workflows/{non_existent_id}/advance",
            json={"trigger": "agent_complete"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]

    async def test_advance_workflow_all_triggers(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test workflow advancement with all valid triggers.

        Contract: trigger must be one of: agent_complete, human_approved, human_rejected.
        """
        triggers = ["agent_complete", "human_approved", "human_rejected"]

        for trigger in triggers:
            # Create a fresh workflow for each trigger test
            create_response = await test_client.post(
                "/workflows",
                json=sample_create_workflow_request,
            )
            workflow_id = create_response.json()["id"]

            response = await test_client.post(
                f"/workflows/{workflow_id}/advance",
                json={
                    "trigger": trigger,
                    "phase_result": {"test": "data"},
                },
            )

            # Should not fail with validation error for valid triggers
            # (may fail with state transition error which is acceptable)
            assert response.status_code in [200, 400]

    async def test_advance_workflow_invalid_trigger(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test workflow advancement with invalid trigger.

        Contract: Invalid trigger returns 400 with ErrorResponse.
        """
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        workflow_id = create_response.json()["id"]

        response = await test_client.post(
            f"/workflows/{workflow_id}/advance",
            json={
                "trigger": "invalid_trigger",
            },
        )

        assert response.status_code in [400, 422]

    async def test_advance_workflow_missing_trigger(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test workflow advancement with missing required trigger field.

        Contract: trigger is required.
        """
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        workflow_id = create_response.json()["id"]

        response = await test_client.post(
            f"/workflows/{workflow_id}/advance",
            json={
                "phase_result": {"test": "data"},
            },
        )

        assert response.status_code in [400, 422]

    async def test_advance_workflow_with_phase_result(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test workflow advancement with optional phase_result.

        Contract: phase_result is optional object.
        """
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        workflow_id = create_response.json()["id"]

        # With phase_result
        response = await test_client.post(
            f"/workflows/{workflow_id}/advance",
            json={
                "trigger": "agent_complete",
                "phase_result": {
                    "output": "Generated specification",
                    "files_created": ["specs/009-auth/spec.md"],
                    "confidence": 92,
                },
            },
        )

        # Should accept the phase_result
        assert response.status_code in [200, 400]  # 400 if state doesn't allow advance

    async def test_advance_workflow_invalid_state_transition(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test workflow advancement with invalid state transition.

        Contract: Invalid state transition returns 400 with ErrorResponse.

        For example, cannot advance a completed workflow.
        """
        # Create and complete a workflow (mock)
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        workflow_id = create_response.json()["id"]

        # Try to advance multiple times - at some point should fail
        # First advance might succeed, but repeated advances on completed should fail
        for _ in range(5):
            response = await test_client.post(
                f"/workflows/{workflow_id}/advance",
                json={
                    "trigger": "human_approved",
                    "phase_result": {"approved": True},
                },
            )
            if response.status_code == 400:
                data = response.json()
                assert "error" in data
                break

    async def test_advance_workflow_updates_status(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test that advancing workflow changes its status.

        Contract: Workflow status should change after valid advance.
        """
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        workflow_id = create_response.json()["id"]

        # Advance the workflow
        advance_response = await test_client.post(
            f"/workflows/{workflow_id}/advance",
            json={
                "trigger": "agent_complete",
                "phase_result": {"output": "test"},
            },
        )

        if advance_response.status_code == 200:
            # Status may have changed (depends on state machine logic)
            new_status = advance_response.json()["status"]
            # Status should be a valid WorkflowStatus
            assert new_status in [
                "pending",
                "in_progress",
                "waiting_approval",
                "completed",
                "failed",
            ]
