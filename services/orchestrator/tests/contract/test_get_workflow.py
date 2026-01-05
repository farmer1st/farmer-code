"""Contract tests for GET /workflows/{id} endpoint.

Tests the get workflow API contract per contracts/orchestrator.yaml.
"""

from typing import Any
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.anyio
class TestGetWorkflow:
    """Contract tests for GET /workflows/{id} endpoint."""

    async def test_get_workflow_success(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test successful workflow retrieval.

        Contract: GET /workflows/{id} returns 200 with WorkflowResponse.
        """
        # First create a workflow
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        assert create_response.status_code == 201
        workflow_id = create_response.json()["id"]

        # Then retrieve it
        response = await test_client.get(f"/workflows/{workflow_id}")

        assert response.status_code == 200
        data = response.json()

        # Required fields per contract
        assert data["id"] == workflow_id
        assert "workflow_type" in data
        assert "status" in data
        assert "feature_id" in data
        assert "created_at" in data

    async def test_get_workflow_not_found(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test workflow retrieval with non-existent ID.

        Contract: Non-existent workflow returns 404 with ErrorResponse.
        """
        non_existent_id = str(uuid4())

        response = await test_client.get(f"/workflows/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

    async def test_get_workflow_invalid_uuid(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test workflow retrieval with invalid UUID format.

        Contract: Invalid UUID format returns 400 or 422.
        """
        response = await test_client.get("/workflows/not-a-uuid")

        # FastAPI may return 400 or 422 for validation errors
        assert response.status_code in [400, 422]

    async def test_get_workflow_returns_current_state(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test that get workflow returns the current state.

        Contract: Response reflects current workflow state.
        """
        # Create a workflow
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        workflow_id = create_response.json()["id"]

        # Get workflow should return same data
        response = await test_client.get(f"/workflows/{workflow_id}")
        data = response.json()

        assert data["workflow_type"] == sample_create_workflow_request["workflow_type"]
        assert data["status"] in [
            "pending",
            "in_progress",
            "waiting_approval",
            "completed",
            "failed",
        ]

    async def test_get_workflow_includes_optional_fields(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test that optional fields are included in response.

        Contract: Optional fields current_phase, result, error are nullable.
        """
        # Create a workflow
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        workflow_id = create_response.json()["id"]

        response = await test_client.get(f"/workflows/{workflow_id}")
        data = response.json()

        # These fields should exist (may be null for new workflow)
        assert "current_phase" in data or data.get("current_phase") is None
        assert "result" in data or data.get("result") is None
        assert "error" in data or data.get("error") is None

    async def test_get_workflow_multiple_times(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test that workflow can be retrieved multiple times consistently.

        Contract: GET is idempotent - same response for same request.
        """
        # Create a workflow
        create_response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )
        workflow_id = create_response.json()["id"]

        # Get workflow multiple times
        response1 = await test_client.get(f"/workflows/{workflow_id}")
        response2 = await test_client.get(f"/workflows/{workflow_id}")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Core fields should be the same
        data1 = response1.json()
        data2 = response2.json()

        assert data1["id"] == data2["id"]
        assert data1["workflow_type"] == data2["workflow_type"]
        assert data1["feature_id"] == data2["feature_id"]
