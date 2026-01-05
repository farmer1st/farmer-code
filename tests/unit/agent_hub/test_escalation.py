"""Unit tests for escalation handling (KR-003)."""

import uuid

from agent_hub.config import RoutingConfig
from agent_hub.models import (
    Answer,
    AnswerValidationResult,
    Question,
    QuestionTarget,
    ValidationOutcome,
)


class TestEscalationRequestCreation:
    """Tests for EscalationRequest creation (T039)."""

    def test_create_escalation_request_from_low_confidence_answer(self) -> None:
        """Test creating an EscalationRequest from a low-confidence answer."""
        from agent_hub.models import EscalationRequest

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What encryption algorithm should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Consider using AES-256 for encryption.",
            rationale="Common choice but need more context about requirements.",
            confidence=65,
            uncertainty_reasons=["Unknown data sensitivity", "Performance requirements unclear"],
            model_used="sonnet",
            duration_seconds=2.5,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        assert escalation.question == question
        assert escalation.tentative_answer == answer
        assert escalation.threshold_used == 80
        assert escalation.status == "pending"
        assert escalation.github_comment_id is None

    def test_escalation_request_status_can_be_updated(self) -> None:
        """Test that escalation status can be updated (mutable field)."""
        from agent_hub.models import EscalationRequest

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What auth method to use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use OAuth2",
            rationale="Standard approach for web applications.",
            confidence=70,
            model_used="sonnet",
            duration_seconds=1.5,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        # Status should be mutable
        escalation.status = "resolved"
        escalation.github_comment_id = 12345

        assert escalation.status == "resolved"
        assert escalation.github_comment_id == 12345


class TestHumanResponseConfirm:
    """Tests for HumanResponse with CONFIRM action (T040)."""

    def test_human_confirms_tentative_answer(self) -> None:
        """Test human confirms the tentative answer is acceptable."""
        from agent_hub.models import HumanAction, HumanResponse

        response = HumanResponse(
            escalation_id=str(uuid.uuid4()),
            action=HumanAction.CONFIRM,
            responder="farmer1st",
            github_comment_id=67890,
        )

        assert response.action == HumanAction.CONFIRM
        assert response.corrected_answer is None
        assert response.additional_context is None

    def test_confirm_response_has_required_fields(self) -> None:
        """Test that CONFIRM response requires escalation_id and responder."""
        from agent_hub.models import HumanAction, HumanResponse

        response = HumanResponse(
            escalation_id="esc-123",
            action=HumanAction.CONFIRM,
            responder="farmer1st",
            github_comment_id=11111,
        )

        assert response.escalation_id == "esc-123"
        assert response.responder == "farmer1st"


class TestHumanResponseCorrect:
    """Tests for HumanResponse with CORRECT action (T041)."""

    def test_human_provides_corrected_answer(self) -> None:
        """Test human provides a corrected answer."""
        from agent_hub.models import HumanAction, HumanResponse

        response = HumanResponse(
            escalation_id=str(uuid.uuid4()),
            action=HumanAction.CORRECT,
            corrected_answer="Use AES-256-GCM for authenticated encryption.",
            responder="farmer1st",
            github_comment_id=77777,
        )

        assert response.action == HumanAction.CORRECT
        assert response.corrected_answer == "Use AES-256-GCM for authenticated encryption."
        assert response.additional_context is None

    def test_correct_response_without_corrected_answer_is_valid(self) -> None:
        """Test that CORRECT action without corrected_answer is technically valid.

        Note: Business logic should validate this, not the model.
        """
        from agent_hub.models import HumanAction, HumanResponse

        # This is allowed by the model, but handler should validate
        response = HumanResponse(
            escalation_id=str(uuid.uuid4()),
            action=HumanAction.CORRECT,
            responder="farmer1st",
            github_comment_id=88888,
        )

        assert response.action == HumanAction.CORRECT
        assert response.corrected_answer is None


class TestHumanResponseAddContext:
    """Tests for HumanResponse with ADD_CONTEXT action (T042)."""

    def test_human_adds_context_for_retry(self) -> None:
        """Test human adds context and requests re-routing."""
        from agent_hub.models import HumanAction, HumanResponse

        response = HumanResponse(
            escalation_id=str(uuid.uuid4()),
            action=HumanAction.ADD_CONTEXT,
            additional_context="Data is highly sensitive PII. Must comply with GDPR.",
            responder="farmer1st",
            github_comment_id=99999,
        )

        assert response.action == HumanAction.ADD_CONTEXT
        assert response.additional_context == "Data is highly sensitive PII. Must comply with GDPR."
        assert response.corrected_answer is None

    def test_add_context_response_preserves_metadata(self) -> None:
        """Test that ADD_CONTEXT response preserves all metadata."""
        from agent_hub.models import HumanAction, HumanResponse

        escalation_id = str(uuid.uuid4())
        response = HumanResponse(
            escalation_id=escalation_id,
            action=HumanAction.ADD_CONTEXT,
            additional_context="Performance is critical - need sub-millisecond latency.",
            responder="security-lead",
            github_comment_id=12121,
        )

        assert response.escalation_id == escalation_id
        assert response.responder == "security-lead"
        assert response.github_comment_id == 12121


class TestEscalationHandler:
    """Tests for EscalationHandler class."""

    def test_create_escalation_from_validation_result(self) -> None:
        """Test creating an escalation from a failed validation result."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.models import EscalationRequest

        config = RoutingConfig(default_confidence_threshold=80)
        handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What encryption should we use?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use AES-256",
            rationale="Standard encryption algorithm.",
            confidence=70,
            model_used="sonnet",
            duration_seconds=2.0,
        )

        validation = AnswerValidationResult(
            outcome=ValidationOutcome.ESCALATE,
            answer=answer,
            threshold_used=80,
            threshold_source="default",
        )

        escalation = handler.create_escalation(question, validation)

        assert isinstance(escalation, EscalationRequest)
        assert escalation.question == question
        assert escalation.tentative_answer == answer
        assert escalation.threshold_used == 80
        assert escalation.status == "pending"

    def test_handler_process_confirm_response(self) -> None:
        """Test processing a CONFIRM response."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.models import EscalationRequest, HumanAction, HumanResponse

        config = RoutingConfig(default_confidence_threshold=80)
        handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which auth method?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use OAuth2 with PKCE",
            rationale="Secure flow for SPAs.",
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

        response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.CONFIRM,
            responder="farmer1st",
            github_comment_id=12345,
        )

        result = handler.process_response(escalation, response)

        assert result.final_answer == answer
        assert result.escalation_resolved is True
        assert result.action_taken == HumanAction.CONFIRM

    def test_handler_process_correct_response(self) -> None:
        """Test processing a CORRECT response."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.models import EscalationRequest, HumanAction, HumanResponse

        config = RoutingConfig(default_confidence_threshold=80)
        handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="caching",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What caching strategy?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use Redis for caching",
            rationale="Popular choice but uncertain about scale.",
            confidence=60,
            model_used="sonnet",
            duration_seconds=2.0,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.CORRECT,
            corrected_answer="Use Redis with a 5-minute TTL for session data only.",
            responder="farmer1st",
            github_comment_id=22222,
        )

        result = handler.process_response(escalation, response)

        assert result.escalation_resolved is True
        assert result.action_taken == HumanAction.CORRECT
        # Final answer should have 100% confidence since human corrected it
        assert result.final_answer.confidence == 100
        assert result.final_answer.answer == "Use Redis with a 5-minute TTL for session data only."

    def test_handler_process_add_context_response(self) -> None:
        """Test processing an ADD_CONTEXT response."""
        from agent_hub.escalation import EscalationHandler
        from agent_hub.models import EscalationRequest, HumanAction, HumanResponse

        config = RoutingConfig(default_confidence_threshold=80)
        handler = EscalationHandler(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What encryption?",
            feature_id="005-user-auth",
        )

        answer = Answer(
            question_id=question.id,
            answered_by="@duc",
            answer="Use AES-256",
            rationale="Standard choice for encryption but need more context.",
            confidence=65,
            model_used="sonnet",
            duration_seconds=1.5,
        )

        escalation = EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=answer,
            threshold_used=80,
        )

        response = HumanResponse(
            escalation_id=escalation.id,
            action=HumanAction.ADD_CONTEXT,
            additional_context="Data is PII, must comply with GDPR.",
            responder="farmer1st",
            github_comment_id=33333,
        )

        result = handler.process_response(escalation, response)

        assert result.escalation_resolved is False
        assert result.action_taken == HumanAction.ADD_CONTEXT
        assert result.needs_reroute is True
        assert result.updated_question is not None
        assert "Data is PII, must comply with GDPR." in result.updated_question.context
