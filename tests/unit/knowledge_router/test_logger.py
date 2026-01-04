"""Unit tests for Q&A logging (KR-004)."""

import json
import tempfile
import uuid
from pathlib import Path

from knowledge_router.models import (
    Answer,
    AnswerValidationResult,
    Question,
    QuestionTarget,
    ValidationOutcome,
)


class TestQALogEntryCreation:
    """Tests for QALogEntry creation (T051)."""

    def test_create_qa_log_entry_for_accepted_answer(self) -> None:
        """Test creating a QALogEntry for an accepted answer."""
        from knowledge_router.models import QALogEntry

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which auth method should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use OAuth2 with JWT tokens.",
            rationale="Industry standard for secure authentication.",
            confidence=92,
            model_used="opus",
            duration_seconds=3.5,
        )

        validation = AnswerValidationResult(
            outcome=ValidationOutcome.ACCEPTED,
            answer=answer,
            threshold_used=80,
            threshold_source="default",
        )

        log_entry = QALogEntry(
            id=str(uuid.uuid4()),
            feature_id=question.feature_id,
            question=question,
            answer=answer,
            validation_result=validation,
            final_answer=answer,
            routing_decision="Routed to architect (@duc) based on topic 'authentication'",
            total_duration_seconds=3.5,
        )

        assert log_entry.feature_id == "005-user-auth"
        assert log_entry.question == question
        assert log_entry.answer == answer
        assert log_entry.validation_result.outcome == ValidationOutcome.ACCEPTED
        assert log_entry.escalation is None
        assert log_entry.human_response is None
        assert log_entry.final_answer == answer

    def test_create_qa_log_entry_with_escalation(self) -> None:
        """Test creating a QALogEntry that includes escalation info."""
        from knowledge_router.models import (
            EscalationRequest,
            HumanAction,
            HumanResponse,
            QALogEntry,
        )

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What encryption should we use?",
            feature_id="005-user-auth",
        )

        tentative_answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use AES-256 for encryption.",
            rationale="Standard choice but need more context.",
            confidence=65,
            model_used="sonnet",
            duration_seconds=2.0,
        )

        validation = AnswerValidationResult(
            outcome=ValidationOutcome.ESCALATE,
            answer=tentative_answer,
            threshold_used=80,
            threshold_source="default",
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=tentative_answer,
            threshold_used=80,
            github_comment_id=12345,
            status="resolved",
        )

        human_response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.CONFIRM,
            responder="farmer1st",
            github_comment_id=12346,
        )

        # Final answer is the confirmed tentative answer
        final_answer = tentative_answer

        log_entry = QALogEntry(
            id=str(uuid.uuid4()),
            feature_id=question.feature_id,
            question=question,
            answer=tentative_answer,
            validation_result=validation,
            escalation=escalation,
            human_response=human_response,
            final_answer=final_answer,
            routing_decision="Routed to architect (@duc) based on topic 'security'",
            total_duration_seconds=125.5,  # Includes human review time
        )

        assert log_entry.escalation == escalation
        assert log_entry.human_response == human_response
        assert log_entry.human_response.action == HumanAction.CONFIRM

    def test_qa_log_entry_with_parent_id_for_reroute(self) -> None:
        """Test creating a QALogEntry with parent_id for re-routed questions."""
        from knowledge_router.models import QALogEntry

        original_log_id = str(uuid.uuid4())

        question = Question(
            id=str(uuid.uuid4()),
            topic="caching",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What caching strategy?",
            context="Additional context: We need sub-100ms latency.",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use Redis with read-through caching pattern.",
            rationale="Optimal for low-latency requirements with caching layer.",
            confidence=90,
            model_used="opus",
            duration_seconds=2.5,
        )

        validation = AnswerValidationResult(
            outcome=ValidationOutcome.ACCEPTED,
            answer=answer,
            threshold_used=80,
            threshold_source="default",
        )

        log_entry = QALogEntry(
            id=str(uuid.uuid4()),
            feature_id=question.feature_id,
            question=question,
            answer=answer,
            validation_result=validation,
            final_answer=answer,
            routing_decision="Re-routed to architect with additional context",
            total_duration_seconds=2.5,
            parent_id=original_log_id,
        )

        assert log_entry.parent_id == original_log_id


class TestQALogFileAppend:
    """Tests for JSONL file append (T052)."""

    def test_log_exchange_appends_to_jsonl(self) -> None:
        """Test that log_exchange appends entries to JSONL file."""
        from knowledge_router.logger import QALogger
        from knowledge_router.models import QALogEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = QALogger(log_dir=tmpdir)

            question = Question(
                id=str(uuid.uuid4()),
                topic="database",
                suggested_target=QuestionTarget.ARCHITECT,
                question="Which database should we use?",
                feature_id="005-user-auth",
            )

            answer = Answer(
                question_id=question.id,
                answered_by="@duc",
                answer="Use PostgreSQL.",
                rationale="Reliable and feature-rich RDBMS.",
                confidence=95,
                model_used="opus",
                duration_seconds=1.5,
            )

            validation = AnswerValidationResult(
                outcome=ValidationOutcome.ACCEPTED,
                answer=answer,
                threshold_used=80,
                threshold_source="default",
            )

            log_entry = QALogEntry(
                id=str(uuid.uuid4()),
                feature_id=question.feature_id,
                question=question,
                answer=answer,
                validation_result=validation,
                final_answer=answer,
                routing_decision="Routed to architect",
                total_duration_seconds=1.5,
            )

            logger.log_exchange(log_entry)

            # Verify file exists
            log_path = Path(tmpdir) / "005-user-auth.jsonl"
            assert log_path.exists()

            # Verify content
            with open(log_path) as f:
                lines = f.readlines()
                assert len(lines) == 1
                data = json.loads(lines[0])
                assert data["feature_id"] == "005-user-auth"
                assert data["question"]["topic"] == "database"

    def test_log_exchange_appends_multiple_entries(self) -> None:
        """Test that multiple log entries are appended."""
        from knowledge_router.logger import QALogger
        from knowledge_router.models import QALogEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = QALogger(log_dir=tmpdir)

            for i in range(3):
                question = Question(
                    id=str(uuid.uuid4()),
                    topic=f"topic_{i}",
                    suggested_target=QuestionTarget.ARCHITECT,
                    question=f"Question number {i} for testing?",
                    feature_id="005-user-auth",
                )

                answer = Answer(
                    question_id=question.id,
                    answered_by="@duc",
                    answer=f"Answer {i}.",
                    rationale=f"Rationale for answer {i}.",
                    confidence=90 + i,
                    model_used="sonnet",
                    duration_seconds=1.0 + i,
                )

                validation = AnswerValidationResult(
                    outcome=ValidationOutcome.ACCEPTED,
                    answer=answer,
                    threshold_used=80,
                    threshold_source="default",
                )

                log_entry = QALogEntry(
                    id=str(uuid.uuid4()),
                    feature_id=question.feature_id,
                    question=question,
                    answer=answer,
                    validation_result=validation,
                    final_answer=answer,
                    routing_decision=f"Routed for question {i}",
                    total_duration_seconds=1.0 + i,
                )

                logger.log_exchange(log_entry)

            # Verify 3 entries
            log_path = Path(tmpdir) / "005-user-auth.jsonl"
            with open(log_path) as f:
                lines = f.readlines()
                assert len(lines) == 3


class TestQALogRetrieval:
    """Tests for log retrieval by feature_id (T053)."""

    def test_get_log_by_feature_id(self) -> None:
        """Test retrieving log entries by feature_id."""
        from knowledge_router.logger import QALogger
        from knowledge_router.models import QALogEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = QALogger(log_dir=tmpdir)

            # Create entries for different features
            for feature_id in ["005-user-auth", "006-payments", "005-user-auth"]:
                question = Question(
                    id=str(uuid.uuid4()),
                    topic="authentication",
                    suggested_target=QuestionTarget.ARCHITECT,
                    question=f"Question for {feature_id}?",
                    feature_id=feature_id,
                )

                answer = Answer(
                    question_id=question.id,
                    answered_by="@duc",
                    answer="Answer.",
                    rationale="Rationale for this answer.",
                    confidence=90,
                    model_used="sonnet",
                    duration_seconds=1.0,
                )

                validation = AnswerValidationResult(
                    outcome=ValidationOutcome.ACCEPTED,
                    answer=answer,
                    threshold_used=80,
                    threshold_source="default",
                )

                log_entry = QALogEntry(
                    id=str(uuid.uuid4()),
                    feature_id=feature_id,
                    question=question,
                    answer=answer,
                    validation_result=validation,
                    final_answer=answer,
                    routing_decision="Routed",
                    total_duration_seconds=1.0,
                )

                logger.log_exchange(log_entry)

            # Retrieve logs for specific feature
            entries = logger.get_logs_for_feature("005-user-auth")
            assert len(entries) == 2

            entries = logger.get_logs_for_feature("006-payments")
            assert len(entries) == 1

    def test_get_log_for_nonexistent_feature(self) -> None:
        """Test retrieving logs for a feature with no entries."""
        from knowledge_router.logger import QALogger

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = QALogger(log_dir=tmpdir)
            entries = logger.get_logs_for_feature("999-nonexistent")
            assert entries == []


class TestExchangeLinking:
    """Tests for linking related exchanges (T054)."""

    def test_log_with_parent_id_creates_chain(self) -> None:
        """Test that parent_id links related exchanges."""
        from knowledge_router.logger import QALogger
        from knowledge_router.models import QALogEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = QALogger(log_dir=tmpdir)

            # Original exchange
            original_id = str(uuid.uuid4())
            question1 = Question(
                id=str(uuid.uuid4()),
                topic="caching",
                suggested_target=QuestionTarget.ARCHITECT,
                question="What caching strategy should we use?",
                feature_id="005-user-auth",
            )

            answer1 = Answer(
                question_id=question1.id,
                answered_by="@duc",
                answer="Use Redis.",
                rationale="Popular choice for caching needs.",
                confidence=60,
                model_used="sonnet",
                duration_seconds=2.0,
            )

            validation1 = AnswerValidationResult(
                outcome=ValidationOutcome.ESCALATE,
                answer=answer1,
                threshold_used=80,
                threshold_source="default",
            )

            entry1 = QALogEntry(
                id=original_id,
                feature_id=question1.feature_id,
                question=question1,
                answer=answer1,
                validation_result=validation1,
                final_answer=answer1,
                routing_decision="Routed to architect, escalated due to low confidence",
                total_duration_seconds=2.0,
            )

            logger.log_exchange(entry1)

            # Re-routed exchange with additional context
            question2 = Question(
                id=str(uuid.uuid4()),
                topic="caching",
                suggested_target=QuestionTarget.ARCHITECT,
                question="What caching strategy should we use?",
                context="Additional context: Need sub-100ms latency.",
                feature_id="005-user-auth",
            )

            answer2 = Answer(
                question_id=question2.id,
                answered_by="@duc",
                answer="Use Redis with read-through caching pattern.",
                rationale="Optimal for the latency requirements specified.",
                confidence=95,
                model_used="opus",
                duration_seconds=3.0,
            )

            validation2 = AnswerValidationResult(
                outcome=ValidationOutcome.ACCEPTED,
                answer=answer2,
                threshold_used=80,
                threshold_source="default",
            )

            entry2 = QALogEntry(
                id=str(uuid.uuid4()),
                feature_id=question2.feature_id,
                question=question2,
                answer=answer2,
                validation_result=validation2,
                final_answer=answer2,
                routing_decision="Re-routed with additional context",
                total_duration_seconds=3.0,
                parent_id=original_id,
            )

            logger.log_exchange(entry2)

            # Retrieve and verify chain
            entries = logger.get_logs_for_feature("005-user-auth")
            assert len(entries) == 2

            # Check the second entry links to the first
            rerouted_entry = [e for e in entries if e.get("parent_id")]
            assert len(rerouted_entry) == 1
            assert rerouted_entry[0]["parent_id"] == original_id

    def test_get_exchange_chain(self) -> None:
        """Test retrieving a complete exchange chain."""
        from knowledge_router.logger import QALogger
        from knowledge_router.models import QALogEntry

        with tempfile.TemporaryDirectory() as tmpdir:
            logger = QALogger(log_dir=tmpdir)

            # Create a chain: original -> reroute1 -> reroute2
            ids = [str(uuid.uuid4()) for _ in range(3)]

            for i, entry_id in enumerate(ids):
                question = Question(
                    id=str(uuid.uuid4()),
                    topic="caching",
                    suggested_target=QuestionTarget.ARCHITECT,
                    question=f"Caching question iteration {i}?",
                    feature_id="005-user-auth",
                )

                answer = Answer(
                    question_id=question.id,
                    answered_by="@duc",
                    answer=f"Answer iteration {i}.",
                    rationale=f"Rationale for iteration {i}.",
                    confidence=60 + (i * 15),  # 60, 75, 90
                    model_used="sonnet",
                    duration_seconds=1.0,
                )

                validation = AnswerValidationResult(
                    outcome=ValidationOutcome.ACCEPTED if i == 2 else ValidationOutcome.ESCALATE,
                    answer=answer,
                    threshold_used=80,
                    threshold_source="default",
                )

                entry = QALogEntry(
                    id=entry_id,
                    feature_id=question.feature_id,
                    question=question,
                    answer=answer,
                    validation_result=validation,
                    final_answer=answer,
                    routing_decision=f"Iteration {i}",
                    total_duration_seconds=1.0,
                    parent_id=ids[i - 1] if i > 0 else None,
                )

                logger.log_exchange(entry)

            # Get the chain for the last entry
            chain = logger.get_exchange_chain(ids[2], "005-user-auth")
            assert len(chain) == 3
            assert chain[0]["id"] == ids[0]  # Original
            assert chain[1]["id"] == ids[1]  # First reroute
            assert chain[2]["id"] == ids[2]  # Second reroute
