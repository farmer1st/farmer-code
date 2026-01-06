"""E2E tests for audit logging.

Tests the complete audit logging journey.
"""

import json
import os
import sys
import tempfile

import pytest

# Add services/agent-hub to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "services", "agent-hub"))


@pytest.mark.journey("SVC-007")
@pytest.mark.e2e
@pytest.mark.anyio
class TestAuditLogging:
    """E2E tests for audit logging journey.

    Verifies that agent exchanges are logged with complete context.
    """

    async def test_full_exchange_is_logged(
        self,
    ) -> None:
        """Test complete Q&A exchange is logged to JSONL.

        Journey: User asks question → Agent responds → Log entry created
        Per SC-007: 100% of invocations are logged.
        """
        # This test verifies the full audit logging flow
        # In a real scenario, we would start the service and query it
        # For now, we test that the logging module works correctly

        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            logger = AuditLogger(log_path)

            # Simulate a complete exchange
            logger.log(
                feature_id="008-e2e-test",
                topic="architecture",
                question="What pattern should I use for the data layer?",
                answer="Use the repository pattern with SQLAlchemy ORM.",
                confidence=88,
                status="resolved",
                duration_ms=245,
                metadata={"agent": "baron", "model": "claude-3-opus"},
            )

            # Verify log entry
            with open(log_path) as f:
                entry = json.loads(f.readline())

            assert entry["feature_id"] == "008-e2e-test"
            assert entry["topic"] == "architecture"
            assert entry["question"] == "What pattern should I use for the data layer?"
            assert entry["answer"] == "Use the repository pattern with SQLAlchemy ORM."
            assert entry["confidence"] == 88
            assert entry["status"] == "resolved"
            assert entry["duration_ms"] == 245
            assert entry["metadata"]["agent"] == "baron"

    async def test_escalation_is_logged(
        self,
    ) -> None:
        """Test that escalated exchanges are logged with escalation_id."""
        from uuid import uuid4

        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            logger = AuditLogger(log_path)

            escalation_id = uuid4()

            # Simulate an escalated exchange
            logger.log(
                feature_id="008-escalation-e2e",
                topic="security",
                question="Is this authentication approach secure?",
                answer="I believe so, but human review is recommended.",
                confidence=65,
                status="escalated",
                duration_ms=180,
                escalation_id=escalation_id,
            )

            # Verify log entry
            with open(log_path) as f:
                entry = json.loads(f.readline())

            assert entry["status"] == "escalated"
            assert entry["escalation_id"] == str(escalation_id)
            assert entry["confidence"] == 65

    async def test_session_context_is_logged(
        self,
    ) -> None:
        """Test that session_id is logged for multi-turn conversations."""
        from uuid import uuid4

        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            logger = AuditLogger(log_path)

            session_id = uuid4()

            # Log multiple exchanges in same session
            for i in range(3):
                logger.log(
                    feature_id="008-session-e2e",
                    topic="architecture",
                    question=f"Question {i + 1} in session",
                    answer=f"Answer {i + 1}",
                    confidence=85 + i,
                    status="resolved",
                    duration_ms=100 + i * 10,
                    session_id=session_id,
                )

            # Verify all entries have same session_id
            with open(log_path) as f:
                entries = [json.loads(line) for line in f]

            assert len(entries) == 3
            for entry in entries:
                assert entry["session_id"] == str(session_id)

    async def test_logs_queryable_by_feature(
        self,
    ) -> None:
        """Test that logs can be filtered by feature_id.

        Per SC-007: Logs are queryable by feature ID.
        """
        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            logger = AuditLogger(log_path)

            # Log entries for different features
            features = ["008-auth", "009-payments", "008-auth", "010-dashboard"]
            for feature in features:
                logger.log(
                    feature_id=feature,
                    topic="test",
                    question=f"Question for {feature}",
                    answer="Answer",
                    confidence=85,
                    status="resolved",
                    duration_ms=100,
                )

            # Query by feature_id
            with open(log_path) as f:
                entries = [json.loads(line) for line in f]

            auth_entries = [e for e in entries if e["feature_id"] == "008-auth"]
            payments_entries = [e for e in entries if e["feature_id"] == "009-payments"]

            assert len(auth_entries) == 2
            assert len(payments_entries) == 1

    async def test_log_format_matches_schema(
        self,
    ) -> None:
        """Test that log entries match the data-model.md AuditLog schema."""
        from uuid import UUID, uuid4

        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")
            logger = AuditLogger(log_path)

            session_id = uuid4()
            escalation_id = uuid4()

            logger.log(
                feature_id="008-schema-test",
                topic="testing",
                question="Does the schema match?",
                answer="Yes, it does.",
                confidence=95,
                status="resolved",
                duration_ms=50,
                session_id=session_id,
                escalation_id=escalation_id,
                metadata={"key": "value"},
            )

            with open(log_path) as f:
                entry = json.loads(f.readline())

            # Verify all schema fields are present
            required_fields = [
                "id",
                "timestamp",
                "feature_id",
                "topic",
                "question",
                "answer",
                "confidence",
                "status",
                "duration_ms",
            ]

            for field in required_fields:
                assert field in entry, f"Missing required field: {field}"

            # Verify types
            UUID(entry["id"])  # Should be valid UUID
            assert isinstance(entry["confidence"], int)
            assert isinstance(entry["duration_ms"], int)
            assert entry["status"] in ["resolved", "escalated"]


@pytest.mark.journey("SVC-007")
@pytest.mark.e2e
@pytest.mark.anyio
class TestAuditLogFileManagement:
    """Tests for audit log file management."""

    async def test_log_directory_created_if_missing(
        self,
    ) -> None:
        """Test that log directory is created if it doesn't exist."""
        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "logs", "qa", "audit.jsonl")

            # Directory doesn't exist yet
            assert not os.path.exists(os.path.dirname(log_path))

            logger = AuditLogger(log_path)
            logger.log(
                feature_id="008-dir-test",
                topic="test",
                question="Q",
                answer="A",
                confidence=85,
                status="resolved",
                duration_ms=10,
            )

            # Directory should now exist
            assert os.path.exists(log_path)

    async def test_multiple_loggers_append_safely(
        self,
    ) -> None:
        """Test that multiple logger instances can append to same file."""
        from src.logging.audit import AuditLogger

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "audit.jsonl")

            # Create two logger instances
            logger1 = AuditLogger(log_path)
            logger2 = AuditLogger(log_path)

            # Both log entries
            logger1.log(
                feature_id="008-logger1",
                topic="test",
                question="From logger 1",
                answer="A",
                confidence=85,
                status="resolved",
                duration_ms=10,
            )

            logger2.log(
                feature_id="008-logger2",
                topic="test",
                question="From logger 2",
                answer="A",
                confidence=85,
                status="resolved",
                duration_ms=10,
            )

            # Both entries should be in file
            with open(log_path) as f:
                entries = [json.loads(line) for line in f]

            assert len(entries) == 2
            feature_ids = {e["feature_id"] for e in entries}
            assert "008-logger1" in feature_ids
            assert "008-logger2" in feature_ids
