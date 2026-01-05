"""Unit tests for Answer model."""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from agent_hub.models import Answer


class TestAnswerModel:
    """Tests for Answer model validation and behavior."""

    def test_answer_creation_valid(self) -> None:
        """Test creating a valid Answer."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use OAuth2 with JWT tokens for authentication.",
            rationale="Industry standard for mobile/web APIs with good security.",
            confidence=92,
            model_used="opus",
            duration_seconds=3.5,
        )
        assert answer.confidence == 92
        assert answer.answered_by == "@duc"
        assert isinstance(answer.created_at, datetime)

    def test_answer_is_high_confidence(self) -> None:
        """Test is_high_confidence property for high confidence answer."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use PostgreSQL database.",
            rationale="Battle-tested, excellent for relational data.",
            confidence=85,
            model_used="opus",
            duration_seconds=2.0,
        )
        assert answer.is_high_confidence is True

    def test_answer_is_low_confidence(self) -> None:
        """Test is_high_confidence property for low confidence answer."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Maybe use Redis for caching?",
            rationale="Common choice but uncertain about requirements.",
            confidence=65,
            uncertainty_reasons=["No infrastructure details", "Unknown scale"],
            model_used="sonnet",
            duration_seconds=2.1,
        )
        assert answer.is_high_confidence is False

    def test_answer_at_threshold(self) -> None:
        """Test answer exactly at 80% threshold."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use REST API pattern.",
            rationale="Standard approach for this use case.",
            confidence=80,
            model_used="sonnet",
            duration_seconds=1.5,
        )
        assert answer.is_high_confidence is True

    def test_answer_with_uncertainty_reasons(self) -> None:
        """Test Answer with uncertainty reasons."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Consider using GraphQL.",
            rationale="Could be good for complex queries, but depends on team.",
            confidence=68,
            uncertainty_reasons=[
                "Unknown team experience with GraphQL",
                "No information about client requirements",
                "Not sure if caching is needed",
            ],
            model_used="sonnet",
            duration_seconds=2.5,
        )
        assert len(answer.uncertainty_reasons) == 3

    def test_answer_confidence_range_valid(self) -> None:
        """Test confidence at boundaries (0 and 100)."""
        # Test 0%
        answer_0 = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="I have no idea about this.",
            rationale="This is outside my knowledge area completely.",
            confidence=0,
            model_used="sonnet",
            duration_seconds=1.0,
        )
        assert answer_0.confidence == 0
        assert answer_0.is_high_confidence is False

        # Test 100%
        answer_100 = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Python is a programming language.",
            rationale="This is a well-known fact.",
            confidence=100,
            model_used="sonnet",
            duration_seconds=0.5,
        )
        assert answer_100.confidence == 100
        assert answer_100.is_high_confidence is True

    def test_answer_invalid_confidence_too_high(self) -> None:
        """Test that confidence > 100 raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Answer(
                question_id=str(uuid.uuid4()),
                answered_by="@duc",
                answer="Test answer.",
                rationale="Test rationale for this answer.",
                confidence=101,
                model_used="sonnet",
                duration_seconds=1.0,
            )
        assert "confidence" in str(exc_info.value).lower()

    def test_answer_invalid_confidence_negative(self) -> None:
        """Test that negative confidence raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Answer(
                question_id=str(uuid.uuid4()),
                answered_by="@duc",
                answer="Test answer.",
                rationale="Test rationale for this answer.",
                confidence=-1,
                model_used="sonnet",
                duration_seconds=1.0,
            )
        assert "confidence" in str(exc_info.value).lower()

    def test_answer_rationale_too_short(self) -> None:
        """Test that rationale must be at least 20 characters."""
        with pytest.raises(ValidationError) as exc_info:
            Answer(
                question_id=str(uuid.uuid4()),
                answered_by="@duc",
                answer="Use PostgreSQL.",
                rationale="Good choice.",  # Less than 20 chars
                confidence=90,
                model_used="sonnet",
                duration_seconds=1.0,
            )
        assert "rationale" in str(exc_info.value).lower()

    def test_answer_immutable(self) -> None:
        """Test that Answer is immutable (frozen)."""
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use PostgreSQL.",
            rationale="Reliable and well-supported database.",
            confidence=90,
            model_used="opus",
            duration_seconds=1.5,
        )
        with pytest.raises(ValidationError):
            answer.confidence = 50

    def test_answer_valid_model_used(self) -> None:
        """Test that model_used accepts valid model names."""
        for model in ["opus", "sonnet", "haiku"]:
            answer = Answer(
                question_id=str(uuid.uuid4()),
                answered_by="@duc",
                answer="Test answer content here.",
                rationale="This is a rationale with enough characters.",
                confidence=85,
                model_used=model,
                duration_seconds=1.0,
            )
            assert answer.model_used == model
