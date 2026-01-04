"""End-to-end tests for escalation flow (KR-003)."""

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


@pytest.mark.journey("KR-003")
class TestEscalationFlowE2E:
    """E2E tests for the full escalation flow."""

    def test_low_confidence_triggers_escalation_e2e(self) -> None:
        """Test end-to-end: low confidence answer triggers escalation."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.validator import ConfidenceValidator

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

        # Step 1: Create question
        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What encryption algorithm should we use?",
            feature_id="005-user-auth",
        )

        # Step 2: Simulate low-confidence answer
        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use AES-256 for encryption.",
            rationale="Standard choice but uncertain about key management.",
            confidence=65,
            uncertainty_reasons=["Key management approach unclear"],
            model_used="sonnet",
            duration_seconds=2.5,
        )

        # Step 3: Validate and trigger escalation
        validation = validator.validate(answer, topic=question.topic)
        assert validation.outcome == ValidationOutcome.ESCALATE

        # Step 4: Create escalation request
        escalation = escalation_handler.create_escalation(question, validation)
        assert escalation.status == "pending"
        assert escalation.tentative_answer == answer
        assert escalation.threshold_used == 80

    def test_human_confirms_answer_e2e(self) -> None:
        """Test end-to-end: human confirms a low-confidence answer."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.models import EscalationRequest

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

        escalation_handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which OAuth2 flow should we use for our mobile app?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use Authorization Code with PKCE flow.",
            rationale="Recommended for mobile apps as it's more secure than implicit flow.",
            confidence=75,
            model_used="opus",
            duration_seconds=3.0,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        # Human confirms the answer
        human_response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.CONFIRM,
            responder="farmer1st",
            github_comment_id=12345,
        )

        result = escalation_handler.process_response(escalation, human_response)

        assert result.escalation_resolved is True
        assert result.action_taken == HumanAction.CONFIRM
        assert result.final_answer == answer

    def test_human_corrects_answer_e2e(self) -> None:
        """Test end-to-end: human provides a corrected answer."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.models import EscalationRequest

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["database"],
                    },
                },
            }
        )

        escalation_handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="database",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What database migration strategy should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use raw SQL migrations.",
            rationale="Simple and direct approach to database changes.",
            confidence=60,
            uncertainty_reasons=["Not sure about rollback support"],
            model_used="sonnet",
            duration_seconds=1.8,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        # Human corrects the answer
        human_response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.CORRECT,
            corrected_answer=(
                "Use Alembic for database migrations with version control and rollback support."
            ),
            responder="farmer1st",
            github_comment_id=12346,
        )

        result = escalation_handler.process_response(escalation, human_response)

        assert result.escalation_resolved is True
        assert result.action_taken == HumanAction.CORRECT
        assert result.final_answer.confidence == 100
        assert "Alembic" in result.final_answer.answer

    def test_human_adds_context_triggers_reroute_e2e(self) -> None:
        """Test end-to-end: human adds context and triggers re-routing."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.models import EscalationRequest

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

        escalation_handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="caching",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What caching strategy should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use Redis for caching.",
            rationale="Popular choice but need more context about usage patterns.",
            confidence=55,
            uncertainty_reasons=["Unknown cache size requirements", "Unclear data access patterns"],
            model_used="sonnet",
            duration_seconds=2.0,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        # Human adds context
        human_response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.ADD_CONTEXT,
            additional_context=(
                "We expect 10K concurrent users. Cache needs to handle "
                "session data and user preferences. Must survive pod restarts."
            ),
            responder="farmer1st",
            github_comment_id=12347,
        )

        result = escalation_handler.process_response(escalation, human_response)

        assert result.escalation_resolved is False
        assert result.action_taken == HumanAction.ADD_CONTEXT
        assert result.needs_reroute is True
        assert result.updated_question is not None
        assert "10K concurrent users" in result.updated_question.context
        assert "session data" in result.updated_question.context

    def test_topic_override_affects_escalation_threshold_e2e(self) -> None:
        """Test end-to-end: security topic with higher threshold triggers escalation."""
        from knowledge_router.escalation import EscalationHandler
        from knowledge_router.validator import ConfidenceValidator

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["security"],
                    },
                },
                "overrides": {
                    "security": {
                        "agent": "architect",
                        "confidence_threshold": 95,  # Higher threshold for security
                    },
                },
            }
        )

        validator = ConfidenceValidator(config)
        escalation_handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="How should we implement password reset?",
            feature_id="005-user-auth",
        )

        # 90% confidence - passes default 80% but fails security 95%
        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use time-limited tokens sent via email.",
            rationale="Standard approach with good security properties for password reset.",
            confidence=90,
            model_used="opus",
            duration_seconds=2.5,
        )

        validation = validator.validate(answer, topic="security")

        assert validation.outcome == ValidationOutcome.ESCALATE
        assert validation.threshold_used == 95

        escalation = escalation_handler.create_escalation(question, validation)
        assert escalation.threshold_used == 95
