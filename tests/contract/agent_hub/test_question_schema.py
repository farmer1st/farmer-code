"""Contract tests for Question JSON schema."""

import json
import uuid
from pathlib import Path

import pytest
from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate

from agent_hub.models import Question, QuestionTarget

# Load the JSON schema
SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "specs"
    / "004-knowledge-router"
    / "contracts"
    / "question.json"
)


@pytest.fixture
def question_schema() -> dict:
    """Load the Question JSON schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


class TestQuestionSchemaContract:
    """Contract tests to ensure Pydantic model matches JSON schema."""

    def test_valid_question_matches_schema(self, question_schema: dict) -> None:
        """Test that a valid Question model output matches the JSON schema."""
        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What authentication method should we use for the API?",
            context="Building a REST API for mobile and web clients",
            feature_id="005-user-auth",
        )
        # Convert to dict and validate against schema
        question_dict = question.model_dump(mode="json")
        validate(instance=question_dict, schema=question_schema)

    def test_question_with_options_matches_schema(self, question_schema: dict) -> None:
        """Test Question with options matches schema."""
        question = Question(
            id=str(uuid.uuid4()),
            topic="database",
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which database should we use?",
            options=["PostgreSQL", "MySQL", "MongoDB"],
            feature_id="005-user-auth",
        )
        question_dict = question.model_dump(mode="json")
        validate(instance=question_dict, schema=question_schema)

    def test_minimal_question_matches_schema(self, question_schema: dict) -> None:
        """Test minimal valid Question matches schema."""
        question = Question(
            id=str(uuid.uuid4()),
            topic="test_topic",
            suggested_target=QuestionTarget.HUMAN,
            question="What is the timeline for this project?",
            feature_id="001-test",
        )
        question_dict = question.model_dump(mode="json")
        validate(instance=question_dict, schema=question_schema)

    def test_invalid_topic_format_rejected_by_schema(self, question_schema: dict) -> None:
        """Test that schema rejects invalid topic format."""
        invalid_data = {
            "id": str(uuid.uuid4()),
            "topic": "INVALID TOPIC!",  # Invalid: uppercase and special chars
            "suggested_target": "architect",
            "question": "What should we do?",
            "feature_id": "005-test",
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_data, schema=question_schema)

    def test_missing_required_field_rejected_by_schema(self, question_schema: dict) -> None:
        """Test that schema rejects missing required fields."""
        invalid_data = {
            "id": str(uuid.uuid4()),
            "topic": "authentication",
            # Missing: suggested_target, question, feature_id
        }
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=invalid_data, schema=question_schema)

    def test_all_targets_valid_in_schema(self, question_schema: dict) -> None:
        """Test all QuestionTarget values are valid in schema."""
        for target in QuestionTarget:
            question = Question(
                id=str(uuid.uuid4()),
                topic="test",
                suggested_target=target,
                question="This is a test question here",
                feature_id="001-test",
            )
            question_dict = question.model_dump(mode="json")
            validate(instance=question_dict, schema=question_schema)
