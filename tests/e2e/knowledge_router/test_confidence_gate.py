"""End-to-end tests for confidence gating (KR-002)."""

import uuid

import pytest

from knowledge_router.config import ConfigLoader
from knowledge_router.models import (
    Answer,
    Question,
    QuestionTarget,
    ValidationOutcome,
)


@pytest.mark.journey("KR-002")
class TestConfidenceGateE2E:
    """E2E tests for confidence-based answer validation."""

    def test_high_confidence_answer_accepted_e2e(self) -> None:
        """Test end-to-end: high confidence answer is accepted."""
        from knowledge_router.validator import ConfidenceValidator

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["authentication"],
                    },
                },
            }
        )

        validator = ConfidenceValidator(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What authentication method should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use OAuth2 with JWT tokens for authentication.",
            rationale="Industry standard for mobile and web APIs.",
            confidence=92,
            model_used="opus",
            duration_seconds=3.5,
        )

        result = validator.validate(answer, topic=question.topic)

        assert result.outcome == ValidationOutcome.ACCEPTED
        assert result.answer == answer

    def test_low_confidence_answer_escalated_e2e(self) -> None:
        """Test end-to-end: low confidence answer triggers escalation."""
        from knowledge_router.validator import ConfidenceValidator

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["caching"],
                    },
                },
            }
        )

        validator = ConfidenceValidator(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="caching",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What caching strategy should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Maybe use Redis for caching?",
            rationale="Common choice but uncertain about requirements.",
            confidence=65,
            uncertainty_reasons=["No infrastructure details", "Unknown scale"],
            model_used="sonnet",
            duration_seconds=2.1,
        )

        result = validator.validate(answer, topic=question.topic)

        assert result.outcome == ValidationOutcome.ESCALATE
        assert result.answer == answer
        assert len(answer.uncertainty_reasons) == 2

    def test_topic_override_escalates_despite_high_confidence_e2e(self) -> None:
        """Test end-to-end: security topic with higher threshold."""
        from knowledge_router.validator import ConfidenceValidator

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["security"],
                    },
                },
                "overrides": {
                    "security": {
                        "agent": "architect",
                        "confidence_threshold": 95,
                    },
                },
            }
        )

        validator = ConfidenceValidator(config)

        # 90% confidence - passes default 80% but fails security 95%
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use TLS 1.3 for encryption.",
            rationale="Modern standard with good security properties.",
            confidence=90,
            model_used="opus",
            duration_seconds=2.0,
        )

        result = validator.validate(answer, topic="security")

        assert result.outcome == ValidationOutcome.ESCALATE
        assert result.threshold_used == 95
        assert result.threshold_source == "topic_override"
