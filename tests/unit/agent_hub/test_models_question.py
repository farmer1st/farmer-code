"""Unit tests for Question model."""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from agent_hub.models import Question, QuestionTarget


class TestQuestionModel:
    """Tests for Question model validation and behavior."""

    def test_question_creation_valid(self) -> None:
        """Test creating a valid Question."""
        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What authentication method should we use?",
            feature_id="005-user-auth",
        )
        assert question.topic == "authentication"
        assert question.suggested_target == QuestionTarget.ARCHITECT
        assert isinstance(question.created_at, datetime)

    def test_question_with_context(self) -> None:
        """Test Question with optional context."""
        question = Question(
            id=str(uuid.uuid4()),
            topic="database",
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which database should we use for user data?",
            context="Building a REST API for mobile and web clients",
            feature_id="005-user-auth",
        )
        assert question.context == "Building a REST API for mobile and web clients"

    def test_question_with_options(self) -> None:
        """Test Question with answer choices."""
        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which auth method?",
            options=["OAuth2", "JWT", "Session-based", "API Keys"],
            feature_id="005-user-auth",
        )
        assert len(question.options) == 4
        assert "OAuth2" in question.options

    def test_question_invalid_topic_format(self) -> None:
        """Test that invalid topic format raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=str(uuid.uuid4()),
                topic="Invalid Topic!",  # Contains uppercase and special char
                suggested_target=QuestionTarget.ARCHITECT,
                question="What should we do?",
                feature_id="005-test",
            )
        assert "topic" in str(exc_info.value)

    def test_question_too_short(self) -> None:
        """Test that question text must be at least 10 characters."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=str(uuid.uuid4()),
                topic="test",
                suggested_target=QuestionTarget.ARCHITECT,
                question="Short?",  # Less than 10 chars
                feature_id="005-test",
            )
        assert "question" in str(exc_info.value).lower()

    def test_question_immutable(self) -> None:
        """Test that Question is immutable (frozen)."""
        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What authentication method?",
            feature_id="005-test",
        )
        with pytest.raises(ValidationError):
            question.topic = "database"

    def test_question_targets(self) -> None:
        """Test all valid question targets."""
        for target in QuestionTarget:
            question = Question(
                id=str(uuid.uuid4()),
                topic="test_topic",
                suggested_target=target,
                question="This is a test question for validation",
                feature_id="005-test",
            )
            assert question.suggested_target == target

    def test_question_invalid_feature_id(self) -> None:
        """Test that feature_id must match pattern NNN-name."""
        with pytest.raises(ValidationError) as exc_info:
            Question(
                id=str(uuid.uuid4()),
                topic="test",
                suggested_target=QuestionTarget.ARCHITECT,
                question="What should we do here?",
                feature_id="invalid-format",  # Missing number prefix
            )
        assert "feature_id" in str(exc_info.value)
