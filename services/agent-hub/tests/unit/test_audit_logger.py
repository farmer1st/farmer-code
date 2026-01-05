"""Unit tests for audit logger.

Tests the audit log format and JSONL writing per data-model.md.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.mark.unit
class TestAuditLogFormat:
    """Unit tests for audit log entry format."""

    def test_audit_log_entry_has_required_fields(self) -> None:
        """Test that audit log entry contains all required fields.

        Per data-model.md AuditLog schema:
        - id, timestamp, session_id, feature_id, topic
        - question, answer, confidence, status
        - escalation_id, duration_ms, metadata
        """
        from src.logging.audit import AuditLogEntry

        entry = AuditLogEntry(
            feature_id="008-test",
            topic="architecture",
            question="What pattern should I use?",
            answer="Use the repository pattern.",
            confidence=85,
            status="resolved",
            duration_ms=150,
        )

        # Check required fields exist
        assert entry.id is not None
        assert entry.timestamp is not None
        assert entry.feature_id == "008-test"
        assert entry.topic == "architecture"
        assert entry.question == "What pattern should I use?"
        assert entry.answer == "Use the repository pattern."
        assert entry.confidence == 85
        assert entry.status == "resolved"
        assert entry.duration_ms == 150

    def test_audit_log_entry_optional_fields(self) -> None:
        """Test that optional fields are properly handled."""
        from src.logging.audit import AuditLogEntry

        session_id = uuid4()
        escalation_id = uuid4()

        entry = AuditLogEntry(
            feature_id="008-test",
            topic="security",
            question="Is this secure?",
            answer="Yes, with caveats.",
            confidence=60,
            status="escalated",
            duration_ms=200,
            session_id=session_id,
            escalation_id=escalation_id,
            metadata={"model": "claude-3"},
        )

        assert entry.session_id == session_id
        assert entry.escalation_id == escalation_id
        assert entry.metadata == {"model": "claude-3"}

    def test_audit_log_entry_to_json(self) -> None:
        """Test that audit log entry serializes to valid JSON."""
        from src.logging.audit import AuditLogEntry

        entry = AuditLogEntry(
            feature_id="008-test",
            topic="testing",
            question="How to test?",
            answer="Use pytest.",
            confidence=90,
            status="resolved",
            duration_ms=100,
        )

        json_str = entry.to_json()
        parsed = json.loads(json_str)

        assert parsed["feature_id"] == "008-test"
        assert parsed["topic"] == "testing"
        assert parsed["confidence"] == 90
        assert "id" in parsed
        assert "timestamp" in parsed

    def test_audit_log_entry_timestamp_is_utc(self) -> None:
        """Test that timestamp is in UTC ISO format."""
        from src.logging.audit import AuditLogEntry

        entry = AuditLogEntry(
            feature_id="008-test",
            topic="architecture",
            question="Test?",
            answer="Yes.",
            confidence=85,
            status="resolved",
            duration_ms=50,
        )

        json_str = entry.to_json()
        parsed = json.loads(json_str)

        # Timestamp should be parseable and in UTC
        timestamp = datetime.fromisoformat(parsed["timestamp"].replace("Z", "+00:00"))
        assert timestamp.tzinfo is not None

    def test_audit_log_entry_id_is_uuid(self) -> None:
        """Test that entry ID is a valid UUID string."""
        from uuid import UUID

        from src.logging.audit import AuditLogEntry

        entry = AuditLogEntry(
            feature_id="008-test",
            topic="architecture",
            question="Test?",
            answer="Yes.",
            confidence=85,
            status="resolved",
            duration_ms=50,
        )

        # Should not raise
        UUID(str(entry.id))

    def test_audit_log_status_values(self) -> None:
        """Test that status accepts valid values."""
        from src.logging.audit import AuditLogEntry

        # resolved status
        entry1 = AuditLogEntry(
            feature_id="008-test",
            topic="test",
            question="Q",
            answer="A",
            confidence=90,
            status="resolved",
            duration_ms=10,
        )
        assert entry1.status == "resolved"

        # escalated status
        entry2 = AuditLogEntry(
            feature_id="008-test",
            topic="test",
            question="Q",
            answer="A",
            confidence=50,
            status="escalated",
            duration_ms=10,
        )
        assert entry2.status == "escalated"


@pytest.mark.unit
class TestAuditLogger:
    """Unit tests for AuditLogger class."""

    def test_audit_logger_creates_log_file(self) -> None:
        """Test that audit logger creates the log file."""
        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            logger = AuditLogger(log_path)

            logger.log(
                feature_id="008-test",
                topic="test",
                question="Q",
                answer="A",
                confidence=85,
                status="resolved",
                duration_ms=10,
            )

            assert os.path.exists(log_path)

    def test_audit_logger_appends_entries(self) -> None:
        """Test that audit logger appends multiple entries."""
        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            logger = AuditLogger(log_path)

            # Log 3 entries
            for i in range(3):
                logger.log(
                    feature_id="008-test",
                    topic="test",
                    question=f"Question {i}",
                    answer=f"Answer {i}",
                    confidence=85,
                    status="resolved",
                    duration_ms=10,
                )

            # Read and verify
            with open(log_path) as f:
                lines = f.readlines()

            assert len(lines) == 3
            for i, line in enumerate(lines):
                entry = json.loads(line)
                assert entry["question"] == f"Question {i}"

    def test_audit_logger_writes_valid_jsonl(self) -> None:
        """Test that each line is valid JSON."""
        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            logger = AuditLogger(log_path)

            logger.log(
                feature_id="008-test",
                topic="test",
                question="Q",
                answer="A",
                confidence=85,
                status="resolved",
                duration_ms=10,
            )

            with open(log_path) as f:
                line = f.readline()
                # Should not raise
                entry = json.loads(line)
                assert entry["feature_id"] == "008-test"

    def test_audit_logger_creates_directory(self) -> None:
        """Test that audit logger creates parent directory if needed."""
        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "logs", "qa", "audit.jsonl")
            logger = AuditLogger(log_path)

            logger.log(
                feature_id="008-test",
                topic="test",
                question="Q",
                answer="A",
                confidence=85,
                status="resolved",
                duration_ms=10,
            )

            assert os.path.exists(log_path)

    def test_audit_logger_default_path(self) -> None:
        """Test that audit logger has sensible default path."""
        from src.logging.audit import get_audit_logger

        logger = get_audit_logger()
        assert logger.log_path is not None
        assert "audit" in logger.log_path.lower() or "log" in logger.log_path.lower()
