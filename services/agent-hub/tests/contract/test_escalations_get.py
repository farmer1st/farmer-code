"""Contract tests for GET /escalations/{id} endpoint.

Tests the get escalation API contract per contracts/agent-hub.yaml.
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.anyio
class TestGetEscalation:
    """Contract tests for GET /escalations/{id} endpoint."""

    async def test_get_escalation_success(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test successful escalation retrieval.

        Contract: GET /escalations/{id} returns 200 with EscalationResponse.

        Note: This test requires an escalation to exist. In practice,
        escalations are created automatically when confidence is low.
        """
        # First, we need to trigger an escalation by getting a low-confidence response
        # For now, we'll test the 404 case and mock the success case
        # The actual escalation creation will be tested in integration tests
        pass  # Placeholder - requires escalation creation first

    async def test_get_escalation_not_found(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test escalation retrieval with non-existent ID.

        Contract: Non-existent escalation returns 404 with ErrorResponse.
        """
        non_existent_id = str(uuid4())

        response = await test_client.get(f"/escalations/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        # FastAPI returns error in detail.error
        assert "detail" in data
        assert "error" in data["detail"]
        assert "code" in data["detail"]["error"]
        assert data["detail"]["error"]["code"] == "ESCALATION_NOT_FOUND"

    async def test_get_escalation_invalid_uuid(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test escalation retrieval with invalid UUID format.

        Contract: Invalid UUID returns 400/422.
        """
        response = await test_client.get("/escalations/not-a-uuid")

        assert response.status_code in [400, 422]

    async def test_get_escalation_response_format(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that escalation response has correct format.

        Contract: EscalationResponse has required fields:
        - id, status, question, tentative_answer, confidence, created_at
        """
        # This test verifies the response format when an escalation exists
        # Will be fully testable after escalation creation is implemented
        pass  # Placeholder

    async def test_get_escalation_includes_human_response(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that resolved escalation includes human response.

        Contract: Resolved escalation includes human_action, human_response.
        """
        # This test verifies human response fields are present
        # Will be fully testable after escalation response submission
        pass  # Placeholder
