"""Unit tests for ConfidenceValidator (KR-002)."""

import uuid

from agent_hub.config import RoutingConfig
from agent_hub.models import (
    Answer,
    RoutingRule,
    ValidationOutcome,
)


class TestConfidenceValidation:
    """Tests for confidence validation logic."""

    def test_accept_high_confidence_answer(self) -> None:
        """Test that high confidence answers (>= threshold) are accepted."""
        from agent_hub.validator import ConfidenceValidator

        config = RoutingConfig(default_confidence_threshold=80)
        validator = ConfidenceValidator(config)

        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use OAuth2 with JWT tokens.",
            rationale="Industry standard for mobile and web APIs.",
            confidence=92,
            model_used="opus",
            duration_seconds=3.5,
        )

        result = validator.validate(answer, topic="authentication")

        assert result.outcome == ValidationOutcome.ACCEPTED
        assert result.threshold_used == 80
        assert result.threshold_source == "default"

    def test_escalate_low_confidence_answer(self) -> None:
        """Test that low confidence answers (< threshold) are escalated."""
        from agent_hub.validator import ConfidenceValidator

        config = RoutingConfig(default_confidence_threshold=80)
        validator = ConfidenceValidator(config)

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

        result = validator.validate(answer, topic="caching")

        assert result.outcome == ValidationOutcome.ESCALATE
        assert result.threshold_used == 80

    def test_accept_at_threshold(self) -> None:
        """Test that answer exactly at threshold is accepted."""
        from agent_hub.validator import ConfidenceValidator

        config = RoutingConfig(default_confidence_threshold=80)
        validator = ConfidenceValidator(config)

        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use REST API pattern.",
            rationale="Standard approach for this use case.",
            confidence=80,  # Exactly at threshold
            model_used="sonnet",
            duration_seconds=1.5,
        )

        result = validator.validate(answer, topic="api_design")

        assert result.outcome == ValidationOutcome.ACCEPTED

    def test_escalate_one_below_threshold(self) -> None:
        """Test that answer one below threshold is escalated."""
        from agent_hub.validator import ConfidenceValidator

        config = RoutingConfig(default_confidence_threshold=80)
        validator = ConfidenceValidator(config)

        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Consider using GraphQL.",
            rationale="Could work but I'm not fully certain.",
            confidence=79,  # One below threshold
            model_used="sonnet",
            duration_seconds=1.5,
        )

        result = validator.validate(answer, topic="api_design")

        assert result.outcome == ValidationOutcome.ESCALATE


class TestTopicThresholdOverride:
    """Tests for topic-specific threshold overrides."""

    def test_topic_override_higher_threshold(self) -> None:
        """Test that topic override can set a higher threshold."""
        from agent_hub.validator import ConfidenceValidator

        config = RoutingConfig(
            default_confidence_threshold=80,
            overrides={
                "security": RoutingRule(
                    topic="security",
                    agent="architect",
                    confidence_threshold=95,  # Higher threshold for security
                ),
            },
        )
        validator = ConfidenceValidator(config)

        # 90% would pass default but fail security threshold
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use TLS 1.3 for encryption.",
            rationale="Modern standard, good security properties.",
            confidence=90,
            model_used="opus",
            duration_seconds=2.0,
        )

        result = validator.validate(answer, topic="security")

        assert result.outcome == ValidationOutcome.ESCALATE
        assert result.threshold_used == 95
        assert result.threshold_source == "topic_override"

    def test_topic_override_lower_threshold(self) -> None:
        """Test that topic override can set a lower threshold."""
        from agent_hub.validator import ConfidenceValidator

        config = RoutingConfig(
            default_confidence_threshold=80,
            overrides={
                "documentation": RoutingRule(
                    topic="documentation",
                    agent="product",
                    confidence_threshold=60,  # Lower threshold for docs
                ),
            },
        )
        validator = ConfidenceValidator(config)

        # 65% would fail default but pass documentation threshold
        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@veuve",
            answer="Add a README with basic instructions.",
            rationale="Standard practice for any project.",
            confidence=65,
            model_used="sonnet",
            duration_seconds=1.0,
        )

        result = validator.validate(answer, topic="documentation")

        assert result.outcome == ValidationOutcome.ACCEPTED
        assert result.threshold_used == 60
        assert result.threshold_source == "topic_override"

    def test_no_override_uses_default(self) -> None:
        """Test that topics without overrides use default threshold."""
        from agent_hub.validator import ConfidenceValidator

        config = RoutingConfig(
            default_confidence_threshold=80,
            overrides={
                "security": RoutingRule(
                    topic="security",
                    agent="architect",
                    confidence_threshold=95,
                ),
            },
        )
        validator = ConfidenceValidator(config)

        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@duc",
            answer="Use PostgreSQL for the database.",
            rationale="Reliable and well-supported choice.",
            confidence=85,
            model_used="opus",
            duration_seconds=1.5,
        )

        # database topic has no override, should use default 80%
        result = validator.validate(answer, topic="database")

        assert result.outcome == ValidationOutcome.ACCEPTED
        assert result.threshold_used == 80
        assert result.threshold_source == "default"

    def test_override_without_threshold_uses_default(self) -> None:
        """Test that override without confidence_threshold uses default."""
        from agent_hub.validator import ConfidenceValidator

        config = RoutingConfig(
            default_confidence_threshold=80,
            overrides={
                "budget": RoutingRule(
                    topic="budget",
                    agent="human",
                    # No confidence_threshold set
                ),
            },
        )
        validator = ConfidenceValidator(config)

        answer = Answer(
            question_id=str(uuid.uuid4()),
            answered_by="@veuve",
            answer="Budget is $50,000.",
            rationale="Based on typical project estimates.",
            confidence=75,
            model_used="sonnet",
            duration_seconds=1.0,
        )

        result = validator.validate(answer, topic="budget")

        assert result.outcome == ValidationOutcome.ESCALATE
        assert result.threshold_used == 80  # Uses default
        assert result.threshold_source == "default"
