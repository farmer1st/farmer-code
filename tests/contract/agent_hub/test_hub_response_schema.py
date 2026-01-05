"""Contract tests for HubResponse JSON schema (T027 - US1)."""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate

from agent_hub.models import HubResponse, ResponseStatus

# Load the JSON schema
SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "specs"
    / "005-agent-hub-refactor"
    / "contracts"
    / "hub_response.json"
)


@pytest.fixture
def hub_response_schema() -> dict:
    """Load the HubResponse JSON schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class TestHubResponseSchemaContract:
    """Contract tests to ensure Pydantic model matches JSON schema (T027)."""

    def test_resolved_response_matches_schema(self, hub_response_schema: dict) -> None:
        """Test that a RESOLVED HubResponse matches the JSON schema."""
        response = HubResponse(
            answer="Use OAuth2 with JWT tokens for authentication.",
            rationale="Industry standard for mobile/web APIs.",
            confidence=92,
            session_id="abc-123-def-456",
            status=ResponseStatus.RESOLVED,
        )
        response_dict = response.model_dump(mode="json")
        validate(instance=response_dict, schema=hub_response_schema)

    def test_pending_human_response_matches_schema(self, hub_response_schema: dict) -> None:
        """Test that a PENDING_HUMAN HubResponse with escalation_id matches schema."""
        response = HubResponse(
            answer="Consider using encryption.",
            rationale="Not sure about requirements.",
            confidence=60,
            uncertainty_reasons=[
                "Missing security requirements",
                "No compliance info provided",
            ],
            session_id="session-123",
            status=ResponseStatus.PENDING_HUMAN,
            escalation_id="escalation-456",
        )
        response_dict = response.model_dump(mode="json")
        validate(instance=response_dict, schema=hub_response_schema)

    def test_needs_reroute_response_matches_schema(self, hub_response_schema: dict) -> None:
        """Test that NEEDS_REROUTE response matches schema."""
        response = HubResponse(
            answer="",  # No answer yet, need to re-ask
            rationale="Human added context, need to re-query agent",
            confidence=0,
            session_id="session-789",
            status=ResponseStatus.NEEDS_REROUTE,
        )
        response_dict = response.model_dump(mode="json")
        validate(instance=response_dict, schema=hub_response_schema)

    def test_response_with_empty_uncertainty_reasons(self, hub_response_schema: dict) -> None:
        """Test that response with empty uncertainty_reasons is valid."""
        response = HubResponse(
            answer="Use PostgreSQL for the database.",
            rationale="Excellent for complex queries and data integrity.",
            confidence=100,
            uncertainty_reasons=[],  # Empty is valid
            session_id="session-aaa",
            status=ResponseStatus.RESOLVED,
        )
        response_dict = response.model_dump(mode="json")
        validate(instance=response_dict, schema=hub_response_schema)

    def test_confidence_boundaries_valid_in_schema(self, hub_response_schema: dict) -> None:
        """Test confidence at 0 and 100 are valid."""
        for confidence in [0, 100]:
            response = HubResponse(
                answer="Test answer.",
                rationale="Test rationale.",
                confidence=confidence,
                session_id="session-boundary",
                status=ResponseStatus.RESOLVED,
            )
            response_dict = response.model_dump(mode="json")
            validate(instance=response_dict, schema=hub_response_schema)

    def test_invalid_confidence_rejected_by_schema(self, hub_response_schema: dict) -> None:
        """Test that schema rejects invalid confidence values."""
        invalid_data = {
            "answer": "Test answer.",
            "rationale": "Test rationale.",
            "confidence": 150,  # Invalid: > 100
            "session_id": "session-invalid",
            "status": "resolved",
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_data, schema=hub_response_schema)

    def test_invalid_status_rejected_by_schema(self, hub_response_schema: dict) -> None:
        """Test that schema rejects invalid status values."""
        invalid_data = {
            "answer": "Test answer.",
            "rationale": "Test rationale.",
            "confidence": 80,
            "session_id": "session-invalid",
            "status": "invalid_status",  # Not in enum
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_data, schema=hub_response_schema)

    def test_missing_required_field_rejected_by_schema(self, hub_response_schema: dict) -> None:
        """Test that schema rejects missing required fields."""
        invalid_data = {
            "answer": "Test answer.",
            # Missing: rationale, confidence, session_id, status
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_data, schema=hub_response_schema)

    def test_all_status_values_valid_in_schema(self, hub_response_schema: dict) -> None:
        """Test all valid status values are accepted."""
        for status in [
            ResponseStatus.RESOLVED,
            ResponseStatus.PENDING_HUMAN,
            ResponseStatus.NEEDS_REROUTE,
        ]:
            response = HubResponse(
                answer="Test answer.",
                rationale="Test rationale.",
                confidence=85,
                session_id="session-status",
                status=status,
            )
            response_dict = response.model_dump(mode="json")
            validate(instance=response_dict, schema=hub_response_schema)
