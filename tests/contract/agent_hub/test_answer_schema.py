"""Contract tests for Answer JSON schema."""

import json
import uuid
from pathlib import Path

import pytest
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate

from agent_hub.models import Answer

# Load the JSON schema
SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "specs"
    / "004-knowledge-router"
    / "contracts"
    / "answer.json"
)


@pytest.fixture
def answer_schema() -> dict:
    """Load the Answer JSON schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class TestAnswerSchemaContract:
    """Contract tests to ensure Pydantic model matches JSON schema."""

    def test_valid_answer_matches_schema(self, answer_schema: dict) -> None:
        """Test that a valid Answer model output matches the JSON schema."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use OAuth2 with JWT tokens for authentication.",
            rationale="Industry standard for mobile/web APIs with excellent security properties.",
            confidence=92,
            model_used="opus",
            duration_seconds=3.5,
        )
        answer_dict = answer.model_dump(mode="json")
        validate(instance=answer_dict, schema=answer_schema)

    def test_answer_with_uncertainty_matches_schema(self, answer_schema: dict) -> None:
        """Test Answer with uncertainty reasons matches schema."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Consider using Redis for caching.",
            rationale="Common choice but I'm uncertain about infrastructure requirements.",
            confidence=65,
            uncertainty_reasons=[
                "No information about existing infrastructure",
                "Unknown scaling requirements",
            ],
            model_used="sonnet",
            duration_seconds=2.1,
        )
        answer_dict = answer.model_dump(mode="json")
        validate(instance=answer_dict, schema=answer_schema)

    def test_minimal_answer_matches_schema(self, answer_schema: dict) -> None:
        """Test minimal valid Answer matches schema."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="architect",
            answer="Use REST API.",
            rationale="Standard approach that works well for this use case.",
            confidence=85,
            model_used="sonnet",
            duration_seconds=1.0,
        )
        answer_dict = answer.model_dump(mode="json")
        validate(instance=answer_dict, schema=answer_schema)

    def test_confidence_boundaries_valid_in_schema(self, answer_schema: dict) -> None:
        """Test confidence at 0 and 100 are valid."""
        for confidence in [0, 100]:
            answer = Answer(
                question_id=str(uuid.uuid4()),
                answered_by="@duc",
                answer="Test answer content.",
                rationale="This is a rationale that is long enough.",
                confidence=confidence,
                model_used="sonnet",
                duration_seconds=1.0,
            )
            answer_dict = answer.model_dump(mode="json")
            validate(instance=answer_dict, schema=answer_schema)

    def test_invalid_confidence_rejected_by_schema(self, answer_schema: dict) -> None:
        """Test that schema rejects invalid confidence values."""
        invalid_data = {
            "question_id": str(uuid.uuid4()),
            "answered_by": "@duc",
            "answer": "Test answer.",
            "rationale": "This is a test rationale.",
            "confidence": 150,  # Invalid: > 100
            "model_used": "sonnet",
            "duration_seconds": 1.0,
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_data, schema=answer_schema)

    def test_missing_required_field_rejected_by_schema(self, answer_schema: dict) -> None:
        """Test that schema rejects missing required fields."""
        invalid_data = {
            "question_id": str(uuid.uuid4()),
            "answered_by": "@duc",
            # Missing: answer, rationale, confidence, model_used, duration_seconds
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_data, schema=answer_schema)

    def test_all_models_valid_in_schema(self, answer_schema: dict) -> None:
        """Test all valid model names are accepted."""
        for model in ["opus", "sonnet", "haiku"]:
            answer = Answer(
                question_id=str(uuid.uuid4()),
                answered_by="@duc",
                answer="Test answer content.",
                rationale="This is a rationale with enough characters.",
                confidence=85,
                model_used=model,
                duration_seconds=1.0,
            )
            answer_dict = answer.model_dump(mode="json")
            validate(instance=answer_dict, schema=answer_schema)

    def test_rationale_min_length_enforced_by_schema(self, answer_schema: dict) -> None:
        """Test that schema enforces rationale minimum length."""
        invalid_data = {
            "question_id": str(uuid.uuid4()),
            "answered_by": "@duc",
            "answer": "Use PostgreSQL.",
            "rationale": "Short.",  # Less than 20 chars
            "confidence": 90,
            "model_used": "sonnet",
            "duration_seconds": 1.0,
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_data, schema=answer_schema)
