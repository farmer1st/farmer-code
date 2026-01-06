"""Contract tests for POST /workflows endpoint.

Tests the create workflow API contract per contracts/orchestrator.yaml.
"""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.anyio
class TestCreateWorkflow:
    """Contract tests for POST /workflows endpoint."""

    async def test_create_workflow_success(
        self,
        test_client: AsyncClient,
        sample_create_workflow_request: dict[str, Any],
    ) -> None:
        """Test successful workflow creation.

        Contract: POST /workflows returns 201 with WorkflowResponse.
        """
        response = await test_client.post(
            "/workflows",
            json=sample_create_workflow_request,
        )

        assert response.status_code == 201
        data = response.json()

        # Required fields per contract
        assert "id" in data
        assert data["workflow_type"] == "specify"
        assert data["status"] in ["pending", "in_progress"]
        assert "feature_id" in data
        assert "created_at" in data

    async def test_create_workflow_all_types(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test workflow creation for all workflow types.

        Contract: workflow_type must be one of: specify, plan, tasks, implement.
        """
        workflow_types = ["specify", "plan", "tasks", "implement"]

        for wf_type in workflow_types:
            response = await test_client.post(
                "/workflows",
                json={
                    "workflow_type": wf_type,
                    "feature_description": f"Test feature for {wf_type} workflow",
                },
            )
            assert response.status_code == 201
            assert response.json()["workflow_type"] == wf_type

    async def test_create_workflow_invalid_type(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test workflow creation with invalid type.

        Contract: Invalid workflow_type returns 400 with ErrorResponse.
        """
        response = await test_client.post(
            "/workflows",
            json={
                "workflow_type": "invalid_type",
                "feature_description": "Test feature description",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

    async def test_create_workflow_missing_required_fields(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test workflow creation with missing required fields.

        Contract: Missing required fields return 400.
        """
        # Missing workflow_type
        response = await test_client.post(
            "/workflows",
            json={
                "feature_description": "Test feature description",
            },
        )
        assert response.status_code == 400 or response.status_code == 422

        # Missing feature_description
        response = await test_client.post(
            "/workflows",
            json={
                "workflow_type": "specify",
            },
        )
        assert response.status_code == 400 or response.status_code == 422

    async def test_create_workflow_short_description(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test workflow creation with too short description.

        Contract: feature_description minLength is 10.
        """
        response = await test_client.post(
            "/workflows",
            json={
                "workflow_type": "specify",
                "feature_description": "Short",  # Less than 10 chars
            },
        )
        assert response.status_code == 400 or response.status_code == 422

    async def test_create_workflow_with_context(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test workflow creation with optional context.

        Contract: context is optional object with additional properties.
        """
        response = await test_client.post(
            "/workflows",
            json={
                "workflow_type": "specify",
                "feature_description": "Add user authentication with OAuth2",
                "context": {
                    "priority": "P1",
                    "requester": "product-team",
                    "custom_field": "custom_value",
                },
            },
        )

        assert response.status_code == 201
        # Context should be accepted (additionalProperties: true)

    async def test_create_workflow_generates_feature_id(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that workflow creation generates a valid feature_id.

        Contract: feature_id must match pattern ^\\d{3}-[a-z0-9-]+$.
        """
        response = await test_client.post(
            "/workflows",
            json={
                "workflow_type": "specify",
                "feature_description": "Add user authentication with OAuth2",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Feature ID should match pattern (e.g., "009-user-auth")
        import re

        pattern = r"^\d{3}-[a-z0-9-]+$"
        assert re.match(pattern, data["feature_id"]), (
            f"feature_id '{data['feature_id']}' does not match pattern {pattern}"
        )

    async def test_create_workflow_returns_uuid(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that workflow creation returns valid UUID.

        Contract: id must be a valid UUID.
        """
        response = await test_client.post(
            "/workflows",
            json={
                "workflow_type": "specify",
                "feature_description": "Add user authentication with OAuth2",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Should be valid UUID
        from uuid import UUID

        try:
            UUID(data["id"])
        except ValueError:
            pytest.fail(f"id '{data['id']}' is not a valid UUID")

    async def test_create_workflow_timestamps(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that workflow creation includes proper timestamps.

        Contract: created_at is required, updated_at is optional,
        completed_at is nullable.
        """
        response = await test_client.post(
            "/workflows",
            json={
                "workflow_type": "specify",
                "feature_description": "Add user authentication with OAuth2",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # created_at is required
        assert "created_at" in data
        assert data["created_at"] is not None

        # completed_at should be null for new workflow
        assert data.get("completed_at") is None
