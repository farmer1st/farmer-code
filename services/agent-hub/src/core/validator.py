"""Confidence validation for Agent Hub.

This module handles validation of agent response confidence
against configured thresholds.
"""

from typing import Any
from uuid import UUID, uuid4


class ValidationResult:
    """Result of confidence validation."""

    def __init__(
        self,
        is_valid: bool,
        confidence: int,
        threshold: int,
        escalation_id: UUID | None = None,
    ) -> None:
        self.is_valid = is_valid
        self.confidence = confidence
        self.threshold = threshold
        self.escalation_id = escalation_id

    @property
    def status(self) -> str:
        """Get status string for response."""
        return "resolved" if self.is_valid else "pending_human"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "threshold": self.threshold,
            "status": self.status,
            "escalation_id": str(self.escalation_id) if self.escalation_id else None,
        }


class ConfidenceValidator:
    """Validates confidence against thresholds.

    Example:
        validator = ConfidenceValidator(default_threshold=80)
        result = validator.validate(confidence=75, topic="security")
        if not result.is_valid:
            print(f"Escalation needed: {result.escalation_id}")
    """

    def __init__(
        self,
        default_threshold: int = 80,
        topic_thresholds: dict[str, int] | None = None,
    ) -> None:
        """Initialize validator.

        Args:
            default_threshold: Default confidence threshold (0-100)
            topic_thresholds: Optional per-topic threshold overrides
        """
        self.default_threshold = default_threshold
        self.topic_thresholds = topic_thresholds or {}

    def get_threshold(self, topic: str | None = None) -> int:
        """Get threshold for a topic.

        Args:
            topic: Optional topic for topic-specific threshold

        Returns:
            Confidence threshold (0-100)
        """
        if topic and topic in self.topic_thresholds:
            return self.topic_thresholds[topic]
        return self.default_threshold

    def validate(
        self,
        confidence: int,
        topic: str | None = None,
        create_escalation: bool = True,
    ) -> ValidationResult:
        """Validate confidence against threshold.

        Args:
            confidence: Confidence score (0-100)
            topic: Optional topic for topic-specific threshold
            create_escalation: Whether to create escalation ID if validation fails

        Returns:
            ValidationResult with is_valid, threshold, and optional escalation_id
        """
        threshold = self.get_threshold(topic)
        is_valid = confidence >= threshold

        escalation_id = None
        if not is_valid and create_escalation:
            escalation_id = uuid4()

        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            threshold=threshold,
            escalation_id=escalation_id,
        )


# Module-level convenience functions
_validator: ConfidenceValidator | None = None


def get_validator() -> ConfidenceValidator:
    """Get or create the default validator instance."""
    global _validator
    if _validator is None:
        _validator = ConfidenceValidator(
            default_threshold=80,
            topic_thresholds={
                "security": 95,  # Higher threshold for security
                "compliance": 95,
            },
        )
    return _validator


def validate_confidence(
    confidence: int,
    topic: str | None = None,
) -> ValidationResult:
    """Validate confidence using the default validator.

    Args:
        confidence: Confidence score (0-100)
        topic: Optional topic for topic-specific threshold

    Returns:
        ValidationResult
    """
    return get_validator().validate(confidence, topic)
