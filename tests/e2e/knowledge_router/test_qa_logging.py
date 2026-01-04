"""End-to-end tests for Q&A logging (KR-004)."""

import tempfile
import uuid

import pytest

from knowledge_router.config import ConfigLoader
from knowledge_router.models import (
    Answer,
    HumanAction,
    HumanResponse,
    Question,
    QuestionTarget,
    ValidationOutcome,
)


@pytest.mark.journey("KR-004")
class TestQALoggingE2E:
    """E2E tests for the Q&A logging flow."""

    def test_complete_qa_exchange_is_logged_e2e(self) -> None:
        """Test end-to-end: a complete Q&A exchange is logged."""
        from knowledge_router.logger import QALogger
        from knowledge_router.models import QALogEntry
        from knowledge_router.validator import ConfidenceValidator

        with tempfile.TemporaryDirectory() as tmpdir:
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
            logger = QALogger(log_dir=tmpdir)

            # Create a question
            question = Question(
                id=str(uuid.uuid4()),
                topic="authentication",
                suggested_target=QuestionTarget.ARCHITECT,
                question="Which authentication method should we use for our API?",
                feature_id="005-user-auth",
            )

            # Create an answer
            answer = Answer(
                question_id=question.id,
                answered_by="@duc",
                answer="Use OAuth2 with JWT tokens for API authentication.",
                rationale="Industry standard that provides flexibility and security.",
                confidence=92,
                model_used="opus",
                duration_seconds=3.5,
            )

            # Validate the answer
            validation = validator.validate(answer, topic=question.topic)
            assert validation.outcome == ValidationOutcome.ACCEPTED

            # Log the exchange
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

            logger.log_exchange(log_entry)

            # Retrieve and verify
            entries = logger.get_logs_for_feature("005-user-auth")
            assert len(entries) == 1
            assert entries[0]["question"]["topic"] == "authentication"
            assert entries[0]["validation_result"]["outcome"] == "accepted"

    def test_escalated_exchange_is_fully_logged_e2e(self) -> None:
        """Test end-to-end: an escalated exchange with human response is logged."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.logger import QALogger
        from knowledge_router.models import (
            QALogEntry,
        )
        from knowledge_router.validator import ConfidenceValidator

        with tempfile.TemporaryDirectory() as tmpdir:
            config = ConfigLoader.load_from_dict(
                {
                    "defaults": {"confidence_threshold": 80},
                    "agents": {
                        "architect": {
                            "name": "@duc",
                            "topics": ["security"],
                        },
                    },
                }
            )

            validator = ConfidenceValidator(config)
            escalation_handler = EscalationHandler(config)
            logger = QALogger(log_dir=tmpdir)

            # Create a question
            question = Question(
                id=str(uuid.uuid4()),
                topic="security",
                suggested_target=QuestionTarget.ARCHITECT,
                question="What encryption should we use for storing secrets?",
                feature_id="005-user-auth",
            )

            # Create a low-confidence answer
            tentative_answer = Answer(
                question_id=question.id,
                answered_by="@duc",
                answer="Use AES-256 for encryption.",
                rationale="Standard choice but need more context about key management.",
                confidence=70,
                uncertainty_reasons=["Key management approach unclear"],
                model_used="sonnet",
                duration_seconds=2.5,
            )

            # Validate - should escalate
            validation = validator.validate(tentative_answer, topic=question.topic)
            assert validation.outcome == ValidationOutcome.ESCALATE

            # Create escalation
            escalation = escalation_handler.create_escalation(question, validation)

            # Simulate human confirming the answer
            human_response = HumanResponse(
                escalation_id=escalation.id,
                action=HumanAction.CONFIRM,
                responder="farmer1st",
                github_comment_id=12345,
            )

            # Process the response
            result = escalation_handler.process_response(escalation, human_response)
            escalation.status = "resolved"

            # Log the complete exchange
            log_entry = QALogEntry(
                id=str(uuid.uuid4()),
                feature_id=question.feature_id,
                question=question,
                answer=tentative_answer,
                validation_result=validation,
                escalation=escalation,
                human_response=human_response,
                final_answer=result.final_answer,
                routing_decision="Routed to architect, escalated due to low confidence",
                total_duration_seconds=125.5,  # Includes human review time
            )

            logger.log_exchange(log_entry)

            # Retrieve and verify
            entries = logger.get_logs_for_feature("005-user-auth")
            assert len(entries) == 1
            assert entries[0]["escalation"] is not None
            assert entries[0]["escalation"]["status"] == "resolved"
            assert entries[0]["human_response"]["action"] == "confirm"

    def test_rerouted_exchange_chain_is_linked_e2e(self) -> None:
        """Test end-to-end: re-routed exchanges form a linked chain."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.logger import QALogger
        from knowledge_router.models import (
            QALogEntry,
        )
        from knowledge_router.validator import ConfidenceValidator

        with tempfile.TemporaryDirectory() as tmpdir:
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
            escalation_handler = EscalationHandler(config)
            logger = QALogger(log_dir=tmpdir)

            # First exchange - low confidence
            original_log_id = str(uuid.uuid4())

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
                answer="Use Redis for caching.",
                rationale="Popular choice but uncertain about specifics.",
                confidence=60,
                uncertainty_reasons=["Unknown data access patterns", "Scale unclear"],
                model_used="sonnet",
                duration_seconds=2.0,
            )

            validation1 = validator.validate(answer1, topic=question1.topic)
            assert validation1.outcome == ValidationOutcome.ESCALATE

            escalation = escalation_handler.create_escalation(question1, validation1)

            # Human adds context and requests re-route
            human_response1 = HumanResponse(
                escalation_id=escalation.id,
                action=HumanAction.ADD_CONTEXT,
                additional_context=(
                    "We expect 10K concurrent users with sub-100ms latency requirements."
                ),
                responder="farmer1st",
                github_comment_id=12345,
            )

            result1 = escalation_handler.process_response(escalation, human_response1)
            assert result1.needs_reroute is True

            # Log the first exchange
            log_entry1 = QALogEntry(
                id=original_log_id,
                feature_id=question1.feature_id,
                question=question1,
                answer=answer1,
                validation_result=validation1,
                escalation=escalation,
                human_response=human_response1,
                final_answer=answer1,
                routing_decision="Routed to architect, escalated, re-routing with context",
                total_duration_seconds=60.0,
            )

            logger.log_exchange(log_entry1)

            # Second exchange - with added context
            question2 = result1.updated_question

            answer2 = Answer(
                question_id=question2.id,
                answered_by="@duc",
                answer="Use Redis with read-through caching pattern and 5-minute TTL.",
                rationale="Optimal for 10K concurrent users with low latency requirements.",
                confidence=95,
                model_used="opus",
                duration_seconds=3.5,
            )

            validation2 = validator.validate(answer2, topic=question2.topic)
            assert validation2.outcome == ValidationOutcome.ACCEPTED

            # Log the second exchange
            log_entry2 = QALogEntry(
                id=str(uuid.uuid4()),
                feature_id=question2.feature_id,
                question=question2,
                answer=answer2,
                validation_result=validation2,
                final_answer=answer2,
                routing_decision="Re-routed to architect with additional context",
                total_duration_seconds=3.5,
                parent_id=original_log_id,
            )

            logger.log_exchange(log_entry2)

            # Verify the chain
            entries = logger.get_logs_for_feature("005-user-auth")
            assert len(entries) == 2

            # Get the chain starting from the second entry
            chain = logger.get_exchange_chain(log_entry2.id, "005-user-auth")
            assert len(chain) == 2
            assert chain[0]["id"] == original_log_id
            assert chain[1]["parent_id"] == original_log_id

    def test_multiple_features_logged_separately_e2e(self) -> None:
        """Test end-to-end: different features have separate log files."""
        from knowledge_router.logger import QALogger
        from knowledge_router.models import QALogEntry
        from knowledge_router.validator import ConfidenceValidator

        with tempfile.TemporaryDirectory() as tmpdir:
            config = ConfigLoader.load_from_dict(
                {
                    "defaults": {"confidence_threshold": 80},
                }
            )

            validator = ConfidenceValidator(config)
            logger = QALogger(log_dir=tmpdir)

            # Log exchanges for different features
            for feature_id in ["005-user-auth", "006-payments", "007-notifications"]:
                question = Question(
                    id=str(uuid.uuid4()),
                    topic="general",
                    suggested_target=QuestionTarget.ARCHITECT,
                    question=f"Question for feature {feature_id}?",
                    feature_id=feature_id,
                )

                answer = Answer(
                    question_id=question.id,
                    answered_by="@duc",
                    answer=f"Answer for {feature_id}.",
                    rationale=f"Rationale for feature {feature_id}.",
                    confidence=90,
                    model_used="opus",
                    duration_seconds=1.0,
                )

                validation = validator.validate(answer, topic=question.topic)

                log_entry = QALogEntry(
                    id=str(uuid.uuid4()),
                    feature_id=feature_id,
                    question=question,
                    answer=answer,
                    validation_result=validation,
                    final_answer=answer,
                    routing_decision=f"Routed for {feature_id}",
                    total_duration_seconds=1.0,
                )

                logger.log_exchange(log_entry)

            # Verify each feature has its own entries
            assert len(logger.get_logs_for_feature("005-user-auth")) == 1
            assert len(logger.get_logs_for_feature("006-payments")) == 1
            assert len(logger.get_logs_for_feature("007-notifications")) == 1
