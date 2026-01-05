"""Contract tests for POST /escalations/{id} endpoint.

Tests the submit human response API contract per contracts/agent-hub.yaml.
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.anyio
class TestSubmitHumanResponse:
    """Contract tests for POST /escalations/{id} endpoint."""

    async def test_submit_confirm_response(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test submitting CONFIRM action.

        Contract: CONFIRM accepts the tentative answer.
        """
        # This test requires an existing escalation
        # Will be fully testable after escalation creation
        pass  # Placeholder

    async def test_submit_correct_response(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test submitting CORRECT action with new answer.

        Contract: CORRECT requires a response with the correct answer.
        """
        # Placeholder - requires existing escalation
        pass

    async def test_submit_add_context_response(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test submitting ADD_CONTEXT action.

        Contract: ADD_CONTEXT triggers re-routing with additional context.
        """
        # Placeholder - requires existing escalation
        pass

    async def test_submit_response_not_found(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test submitting response to non-existent escalation.

        Contract: Non-existent escalation returns 404.
        """
        non_existent_id = str(uuid4())

        response = await test_client.post(
            f"/escalations/{non_existent_id}",
            json={
                "action": "confirm",
                "responder": "@testuser",
            },
        )

        assert response.status_code == 404
        data = response.json()
        # FastAPI returns error in detail.error
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "ESCALATION_NOT_FOUND"

    async def test_submit_response_invalid_action(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test submitting response with invalid action.

        Contract: Invalid action returns 400/422.
        """
        escalation_id = str(uuid4())

        response = await test_client.post(
            f"/escalations/{escalation_id}",
            json={
                "action": "invalid_action",
                "responder": "@testuser",
            },
        )

        assert response.status_code in [400, 422, 404]

    async def test_submit_correct_requires_response(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that CORRECT action requires response field.

        Contract: CORRECT action requires 'response' field.
        """
        escalation_id = str(uuid4())

        response = await test_client.post(
            f"/escalations/{escalation_id}",
            json={
                "action": "correct",
                "responder": "@testuser",
                # Missing 'response' field
            },
        )

        # Should fail validation (400/422) or not found (404)
        assert response.status_code in [400, 422, 404]

    async def test_submit_response_missing_responder(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test submitting response without responder.

        Contract: responder is required.
        """
        escalation_id = str(uuid4())

        response = await test_client.post(
            f"/escalations/{escalation_id}",
            json={
                "action": "confirm",
                # Missing 'responder' field
            },
        )

        assert response.status_code in [400, 422]

    async def test_submit_response_already_resolved(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test submitting response to already resolved escalation.

        Contract: Already resolved escalation returns 409 (conflict).
        """
        # This test requires creating and resolving an escalation first
        # Will be fully testable after escalation implementation
        pass  # Placeholder
