"""Integration tests for escalation (KR-003)."""

import uuid

from knowledge_router.config import RoutingConfig
from knowledge_router.models import (
    Answer,
    Question,
    QuestionTarget,
)


class TestEscalationGitHubIntegration:
    """Integration tests for GitHub comment posting (T043)."""

    def test_format_escalation_for_github_comment(self) -> None:
        """Test formatting an escalation as a GitHub comment."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.models import EscalationRequest

        config = RoutingConfig(default_confidence_threshold=80)
        handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What encryption algorithm should we use for storing user passwords?",
            context="We're building a user authentication system for a mobile app.",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use bcrypt with a cost factor of 12 for password hashing.",
            rationale="bcrypt is designed for password hashing with configurable cost.",
            confidence=72,
            uncertainty_reasons=[
                "Cost factor may need tuning based on server capacity",
                "Should verify compliance requirements for password storage",
            ],
            model_used="sonnet",
            duration_seconds=2.8,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        comment = handler.format_github_comment(escalation)

        # Verify comment structure
        assert "## :warning: Low Confidence Answer - Human Review Required" in comment
        assert "**Topic:** `security`" in comment
        assert "**Confidence:** 72% (threshold: 80%)" in comment
        assert question.question in comment
        assert answer.answer in comment
        assert answer.rationale in comment
        assert "Cost factor may need tuning" in comment
        assert "/confirm" in comment
        assert "/correct" in comment
        assert "/context" in comment

    def test_format_escalation_without_uncertainty_reasons(self) -> None:
        """Test formatting an escalation with no uncertainty reasons."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.models import EscalationRequest

        config = RoutingConfig(default_confidence_threshold=80)
        handler = EscalationHandler(config)

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
            answer="Use Redis for distributed caching.",
            rationale="Redis is fast and supports various data structures.",
            confidence=75,
            # No uncertainty_reasons
            model_used="sonnet",
            duration_seconds=1.5,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        comment = handler.format_github_comment(escalation)

        # Should not have uncertainty section
        assert "**Uncertainty reasons:**" not in comment
        assert "**Confidence:** 75%" in comment

    def test_format_escalation_without_context(self) -> None:
        """Test formatting an escalation with no question context."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.models import EscalationRequest

        config = RoutingConfig(default_confidence_threshold=80)
        handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="database",
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which database should we use for this project?",
            # No context
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use PostgreSQL.",
            rationale="Reliable and feature-rich relational database.",
            confidence=70,
            model_used="opus",
            duration_seconds=2.0,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        comment = handler.format_github_comment(escalation)

        # Should not have context line if empty
        assert "**Context:**" not in comment
