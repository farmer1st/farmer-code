"""Escalation handler for Agent Hub service.

Manages escalation lifecycle: create, get, resolve.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session as DBSession

from src.db.models import Escalation, EscalationStatus, HumanAction


class EscalationNotFoundError(Exception):
    """Raised when an escalation is not found."""

    def __init__(self, escalation_id: str) -> None:
        self.escalation_id = escalation_id
        super().__init__(f"Escalation {escalation_id} not found")


class EscalationAlreadyResolvedError(Exception):
    """Raised when trying to respond to an already resolved escalation."""

    def __init__(self, escalation_id: str) -> None:
        self.escalation_id = escalation_id
        super().__init__(f"Escalation {escalation_id} is already resolved")


class InvalidHumanActionError(Exception):
    """Raised when an invalid human action is provided."""

    def __init__(self, action: str) -> None:
        self.action = action
        super().__init__(f"Invalid human action: {action}")


class EscalationManager:
    """Manages escalation lifecycle."""

    def __init__(self, db: DBSession) -> None:
        """Initialize with database session."""
        self.db = db

    def create_escalation(
        self,
        topic: str,
        question: str,
        tentative_answer: str,
        confidence: int,
        uncertainty_reasons: list[str] | None = None,
        session_id: str | None = None,
    ) -> Escalation:
        """Create a new escalation.

        Args:
            topic: Topic the question was about
            question: Original question
            tentative_answer: Agent's tentative answer
            confidence: Confidence level (0-100)
            uncertainty_reasons: Reasons for low confidence
            session_id: Optional session ID

        Returns:
            Created escalation
        """
        escalation = Escalation(
            id=str(uuid4()),
            question_id=str(uuid4()),
            topic=topic,
            question=question,
            tentative_answer=tentative_answer,
            confidence=confidence,
            session_id=session_id,
            status=EscalationStatus.PENDING.value,
        )
        escalation.set_uncertainty_reasons(uncertainty_reasons)

        self.db.add(escalation)
        self.db.commit()
        self.db.refresh(escalation)

        return escalation

    def get_escalation(self, escalation_id: str) -> Escalation:
        """Get escalation by ID.

        Args:
            escalation_id: Escalation UUID

        Returns:
            Escalation instance

        Raises:
            EscalationNotFoundError: If escalation not found
        """
        escalation = (
            self.db.query(Escalation).filter(Escalation.id == escalation_id).first()
        )
        if not escalation:
            raise EscalationNotFoundError(escalation_id)
        return escalation

    def submit_human_response(
        self,
        escalation_id: str,
        action: str,
        responder: str,
        response: str | None = None,
    ) -> Escalation:
        """Submit human response to an escalation.

        Args:
            escalation_id: Escalation UUID
            action: Human action (confirm, correct, add_context)
            responder: Human responder identifier
            response: Optional response text (required for correct)

        Returns:
            Updated escalation

        Raises:
            EscalationNotFoundError: If escalation not found
            EscalationAlreadyResolvedError: If already resolved
            InvalidHumanActionError: If action is invalid
        """
        escalation = self.get_escalation(escalation_id)

        # Check if already resolved
        if escalation.status == EscalationStatus.RESOLVED.value:
            raise EscalationAlreadyResolvedError(escalation_id)

        # Validate action
        valid_actions = [a.value for a in HumanAction]
        if action not in valid_actions:
            raise InvalidHumanActionError(action)

        # Validate response for correct action
        if action == HumanAction.CORRECT.value and not response:
            raise ValueError("Response is required for 'correct' action")

        # Update escalation
        escalation.human_action = action
        escalation.human_response = response
        escalation.human_responder = responder
        escalation.status = EscalationStatus.RESOLVED.value
        escalation.resolved_at = datetime.utcnow()
        escalation.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(escalation)

        return escalation

    def should_escalate(self, confidence: int, topic: str | None = None) -> bool:
        """Determine if a response should be escalated.

        Args:
            confidence: Confidence level (0-100)
            topic: Optional topic for topic-specific thresholds

        Returns:
            True if should escalate
        """
        # Topic-specific thresholds
        thresholds = {
            "security": 90,
            "architecture": 85,
            "testing": 80,
            "default": 85,
        }

        threshold = thresholds.get(topic, thresholds["default"]) if topic else thresholds["default"]
        return confidence < threshold
