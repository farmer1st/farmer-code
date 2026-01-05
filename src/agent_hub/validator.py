"""Confidence validation for Knowledge Router.

This module handles validating agent answers against confidence thresholds
and determining whether answers should be accepted or escalated.
"""

from .config import RoutingConfig
from .models import Answer, AnswerValidationResult, ValidationOutcome


class ConfidenceValidator:
    """Validates agent answers against confidence thresholds."""

    def __init__(self, config: RoutingConfig) -> None:
        """Initialize the validator.

        Args:
            config: Routing configuration with thresholds.
        """
        self._config = config

    def validate(self, answer: Answer, topic: str) -> AnswerValidationResult:
        """Validate an answer's confidence against the threshold.

        Args:
            answer: The answer to validate.
            topic: The topic the answer is for (used for threshold lookup).

        Returns:
            AnswerValidationResult with outcome and threshold info.
        """
        threshold, source = self._get_threshold_for_topic(topic)

        if answer.confidence >= threshold:
            outcome = ValidationOutcome.ACCEPTED
        else:
            outcome = ValidationOutcome.ESCALATE

        return AnswerValidationResult(
            outcome=outcome,
            answer=answer,
            threshold_used=threshold,
            threshold_source=source,
        )

    def _get_threshold_for_topic(self, topic: str) -> tuple[int, str]:
        """Get the confidence threshold for a topic.

        Args:
            topic: The topic to look up.

        Returns:
            Tuple of (threshold, source) where source describes
            where the threshold came from.
        """
        # Check for topic-specific override
        if topic in self._config.overrides:
            override = self._config.overrides[topic]
            if override.confidence_threshold is not None:
                return override.confidence_threshold, "topic_override"

        # Use default threshold
        return self._config.default_confidence_threshold, "default"
