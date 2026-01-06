"""Audit logger for Agent Hub service.

Logs all agent exchanges to JSONL format per data-model.md AuditLog schema.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class AuditLogEntry:
    """Audit log entry per data-model.md schema.

    Fields:
        id: Unique entry identifier
        timestamp: UTC timestamp
        session_id: Session UUID if multi-turn
        feature_id: Feature being worked on
        topic: Topic of the question
        question: The question asked
        answer: The answer provided
        confidence: Confidence level (0-100)
        status: resolved or escalated
        escalation_id: Escalation UUID if escalated
        duration_ms: Response time in milliseconds
        metadata: Additional context
    """

    feature_id: str
    topic: str
    question: str
    answer: str
    confidence: int
    status: str
    duration_ms: int
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    session_id: UUID | None = None
    escalation_id: UUID | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert entry to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "session_id": str(self.session_id) if self.session_id else None,
            "feature_id": self.feature_id,
            "topic": self.topic,
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "status": self.status,
            "escalation_id": str(self.escalation_id) if self.escalation_id else None,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata or {},
        }

    def to_json(self) -> str:
        """Convert entry to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """JSONL audit logger for agent exchanges.

    Appends log entries to a JSONL file. Each line is a complete
    JSON object representing one exchange.

    Example:
        logger = AuditLogger("/logs/audit.jsonl")
        logger.log(
            feature_id="008-auth",
            topic="architecture",
            question="How to implement auth?",
            answer="Use JWT tokens.",
            confidence=85,
            status="resolved",
            duration_ms=150,
        )
    """

    def __init__(self, log_path: str | None = None) -> None:
        """Initialize audit logger.

        Args:
            log_path: Path to JSONL log file. If None, uses default.
        """
        if log_path is None:
            log_path = os.environ.get(
                "AUDIT_LOG_PATH",
                "./logs/audit.jsonl",
            )
        self._log_path = log_path
        self._ensure_directory()

    @property
    def log_path(self) -> str:
        """Get the log file path."""
        return self._log_path

    def _ensure_directory(self) -> None:
        """Create log directory if it doesn't exist."""
        log_dir = os.path.dirname(self._log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def log(
        self,
        feature_id: str,
        topic: str,
        question: str,
        answer: str,
        confidence: int,
        status: str,
        duration_ms: int,
        session_id: UUID | None = None,
        escalation_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        """Log an exchange to the audit log.

        Args:
            feature_id: Feature being worked on
            topic: Topic of the question
            question: The question asked
            answer: The answer provided
            confidence: Confidence level (0-100)
            status: resolved or escalated
            duration_ms: Response time in milliseconds
            session_id: Session UUID if multi-turn
            escalation_id: Escalation UUID if escalated
            metadata: Additional context

        Returns:
            The created AuditLogEntry
        """
        entry = AuditLogEntry(
            feature_id=feature_id,
            topic=topic,
            question=question,
            answer=answer,
            confidence=confidence,
            status=status,
            duration_ms=duration_ms,
            session_id=session_id,
            escalation_id=escalation_id,
            metadata=metadata,
        )

        self._write_entry(entry)
        return entry

    def _write_entry(self, entry: AuditLogEntry) -> None:
        """Write entry to log file.

        Uses append mode to safely add entries.
        """
        with open(self._log_path, "a") as f:
            f.write(entry.to_json() + "\n")


# Module-level singleton
_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get the default audit logger instance.

    Returns a singleton instance of AuditLogger.
    """
    global _logger
    if _logger is None:
        _logger = AuditLogger()
    return _logger
