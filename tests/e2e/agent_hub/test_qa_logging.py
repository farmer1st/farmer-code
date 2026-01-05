"""End-to-end tests for Q&A logging (KR-004)."""

import tempfile
import uuid

import pytest

from agent_hub.config import ConfigLoader
from agent_hub.models import (
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
        from agent_hub.logger import QALogger
        from agent_hub.models import QALogEntry
        from agent_hub.validator import ConfidenceValidator

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
        from agent_hub.escalation import EscalationHandler
        from agent_hub.logger import QALogger
        from agent_hub.models import (
            QALogEntry,
        )
        from agent_hub.validator import ConfidenceValidator

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
        from agent_hub.escalation import EscalationHandler
        from agent_hub.logger import QALogger
        from agent_hub.models import (
            QALogEntry,
        )
        from agent_hub.validator import ConfidenceValidator

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
        from agent_hub.logger import QALogger
        from agent_hub.models import QALogEntry
        from agent_hub.validator import ConfidenceValidator

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


@pytest.mark.journey("AH-005")
class TestAgentHubAuditLoggingE2E:
    """E2E tests for AgentHub audit trail logging (T065 - US5)."""

    def test_ask_expert_logs_exchange_automatically_e2e(self) -> None:
        """Test that ask_expert automatically logs the Q&A exchange."""
        from unittest.mock import patch

        from agent_hub.config import AgentDefinition, AgentType, RoutingConfig
        from agent_hub.hub import AgentHub
        from agent_hub.models import AgentHandle, AgentStatus, Answer

        with tempfile.TemporaryDirectory() as tmpdir:
            config = RoutingConfig(
                default_confidence_threshold=80,
                agents={
                    "architect": AgentDefinition(
                        id="architect",
                        name="@duc",
                        agent_type=AgentType.KNOWLEDGE,
                        topics=["authentication"],
                    ),
                },
            )

            hub = AgentHub(config, log_dir=tmpdir)

            with patch.object(hub._router, "dispatch_question") as mock_dispatch:
                handle = AgentHandle(
                    id=str(uuid.uuid4()),
                    agent_role="architect",
                    agent_name="@duc",
                    status=AgentStatus.COMPLETED,
                )
                mock_dispatch.return_value = handle

                with patch.object(hub._router, "parse_answer") as mock_parse:
                    mock_parse.return_value = Answer(
                        question_id=str(uuid.uuid4()),
                        answered_by="@duc",
                        answer="Use OAuth2 with JWT tokens",
                        rationale="Industry standard for secure API authentication",
                        confidence=92,
                        model_used="opus",
                        duration_seconds=3.5,
                    )

                    response = hub.ask_expert(
                        topic="authentication",
                        question="Which auth method should we use?",
                        feature_id="005-user-auth",
                    )

            # Verify log was created
            logs = hub.get_logs_for_feature("005-user-auth")
            assert len(logs) == 1
            assert logs[0]["session_id"] == response.session_id
            assert logs[0]["question"]["topic"] == "authentication"
            assert logs[0]["validation_result"]["outcome"] == "accepted"

    def test_ask_expert_logs_escalation_details_e2e(self) -> None:
        """Test that escalated exchanges include escalation details in log."""
        from unittest.mock import patch

        from agent_hub.config import AgentDefinition, AgentType, RoutingConfig
        from agent_hub.hub import AgentHub
        from agent_hub.models import AgentHandle, AgentStatus, Answer, ResponseStatus

        with tempfile.TemporaryDirectory() as tmpdir:
            config = RoutingConfig(
                default_confidence_threshold=80,
                agents={
                    "architect": AgentDefinition(
                        id="architect",
                        name="@duc",
                        agent_type=AgentType.KNOWLEDGE,
                        topics=["security"],
                    ),
                },
            )

            hub = AgentHub(config, log_dir=tmpdir)

            with patch.object(hub._router, "dispatch_question") as mock_dispatch:
                handle = AgentHandle(
                    id=str(uuid.uuid4()),
                    agent_role="architect",
                    agent_name="@duc",
                    status=AgentStatus.COMPLETED,
                )
                mock_dispatch.return_value = handle

                with patch.object(hub._router, "parse_answer") as mock_parse:
                    mock_parse.return_value = Answer(
                        question_id=str(uuid.uuid4()),
                        answered_by="@duc",
                        answer="Use AES-256 for encryption",
                        rationale="Standard but need more context for key management",
                        confidence=60,  # Low confidence - will escalate
                        uncertainty_reasons=["Key management approach unclear"],
                        model_used="sonnet",
                        duration_seconds=2.5,
                    )

                    response = hub.ask_expert(
                        topic="security",
                        question="What encryption should we use?",
                        feature_id="005-security",
                    )

            assert response.status == ResponseStatus.PENDING_HUMAN
            assert response.escalation_id is not None

            # Verify log includes escalation
            logs = hub.get_logs_for_feature("005-security")
            assert len(logs) == 1
            assert logs[0]["escalation"] is not None
            assert logs[0]["escalation"]["id"] == response.escalation_id
            assert logs[0]["escalation"]["status"] == "pending"

    def test_ask_expert_logs_session_id_e2e(self) -> None:
        """Test that session_id is included in log entries."""
        from unittest.mock import patch

        from agent_hub.config import AgentDefinition, AgentType, RoutingConfig
        from agent_hub.hub import AgentHub
        from agent_hub.models import AgentHandle, AgentStatus, Answer

        with tempfile.TemporaryDirectory() as tmpdir:
            config = RoutingConfig(
                default_confidence_threshold=80,
                agents={
                    "architect": AgentDefinition(
                        id="architect",
                        name="@duc",
                        agent_type=AgentType.KNOWLEDGE,
                        topics=["database"],
                    ),
                },
            )

            hub = AgentHub(config, log_dir=tmpdir)

            with patch.object(hub._router, "dispatch_question") as mock_dispatch:
                handle = AgentHandle(
                    id=str(uuid.uuid4()),
                    agent_role="architect",
                    agent_name="@duc",
                    status=AgentStatus.COMPLETED,
                )
                mock_dispatch.return_value = handle

                with patch.object(hub._router, "parse_answer") as mock_parse:
                    mock_parse.return_value = Answer(
                        question_id=str(uuid.uuid4()),
                        answered_by="@duc",
                        answer="Use PostgreSQL",
                        rationale="Reliable and feature-rich RDBMS for production",
                        confidence=95,
                        model_used="opus",
                        duration_seconds=1.5,
                    )

                    response = hub.ask_expert(
                        topic="database",
                        question="Which database should we use?",
                        feature_id="005-db",
                    )

            # Verify session_id is in logs
            logs = hub.get_logs_for_feature("005-db")
            assert len(logs) == 1
            assert logs[0]["session_id"] == response.session_id
            assert logs[0]["session_id"] is not None

    def test_multiple_ask_expert_calls_all_logged_e2e(self) -> None:
        """Test that multiple ask_expert calls are all logged."""
        from unittest.mock import patch

        from agent_hub.config import AgentDefinition, AgentType, RoutingConfig
        from agent_hub.hub import AgentHub
        from agent_hub.models import AgentHandle, AgentStatus, Answer

        with tempfile.TemporaryDirectory() as tmpdir:
            config = RoutingConfig(
                default_confidence_threshold=80,
                agents={
                    "architect": AgentDefinition(
                        id="architect",
                        name="@duc",
                        agent_type=AgentType.KNOWLEDGE,
                        topics=["api_design"],
                    ),
                },
            )

            hub = AgentHub(config, log_dir=tmpdir)

            with patch.object(hub._router, "dispatch_question") as mock_dispatch:
                handle = AgentHandle(
                    id=str(uuid.uuid4()),
                    agent_role="architect",
                    agent_name="@duc",
                    status=AgentStatus.COMPLETED,
                )
                mock_dispatch.return_value = handle

                with patch.object(hub._router, "parse_answer") as mock_parse:
                    # Call ask_expert 3 times
                    for i in range(3):
                        mock_parse.return_value = Answer(
                            question_id=str(uuid.uuid4()),
                            answered_by="@duc",
                            answer=f"Answer {i}",
                            rationale=f"Rationale for answer {i} with explanation",
                            confidence=85 + i,
                            model_used="opus",
                            duration_seconds=1.0,
                        )

                        hub.ask_expert(
                            topic="api_design",
                            question=f"API design question number {i}?",
                            feature_id="005-api",
                        )

            # Verify all 3 exchanges are logged
            logs = hub.get_logs_for_feature("005-api")
            assert len(logs) == 3

    def test_ask_expert_logs_routing_decision_e2e(self) -> None:
        """Test that routing decision is captured in log."""
        from unittest.mock import patch

        from agent_hub.config import AgentDefinition, AgentType, RoutingConfig
        from agent_hub.hub import AgentHub
        from agent_hub.models import AgentHandle, AgentStatus, Answer

        with tempfile.TemporaryDirectory() as tmpdir:
            config = RoutingConfig(
                default_confidence_threshold=80,
                agents={
                    "architect": AgentDefinition(
                        id="architect",
                        name="@duc",
                        agent_type=AgentType.KNOWLEDGE,
                        topics=["architecture"],
                    ),
                },
            )

            hub = AgentHub(config, log_dir=tmpdir)

            with patch.object(hub._router, "dispatch_question") as mock_dispatch:
                handle = AgentHandle(
                    id=str(uuid.uuid4()),
                    agent_role="architect",
                    agent_name="@duc",
                    status=AgentStatus.COMPLETED,
                )
                mock_dispatch.return_value = handle

                with patch.object(hub._router, "parse_answer") as mock_parse:
                    mock_parse.return_value = Answer(
                        question_id=str(uuid.uuid4()),
                        answered_by="@duc",
                        answer="Use microservices pattern",
                        rationale="Good for scalability and team independence",
                        confidence=88,
                        model_used="opus",
                        duration_seconds=2.0,
                    )

                    hub.ask_expert(
                        topic="architecture",
                        question="What architecture pattern should we use?",
                        feature_id="005-arch",
                    )

            # Verify routing decision is in log
            logs = hub.get_logs_for_feature("005-arch")
            assert len(logs) == 1
            assert "routing_decision" in logs[0]
            assert "architect" in logs[0]["routing_decision"].lower()
