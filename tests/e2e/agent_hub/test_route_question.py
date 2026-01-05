"""End-to-end tests for question routing (KR-001, AH-001)."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from agent_hub.config import ConfigLoader
from agent_hub.models import Question, QuestionTarget, ResponseStatus


@pytest.mark.journey("KR-001")
class TestRouteQuestionE2E:
    """E2E tests for routing questions to knowledge agents."""

    @patch("agent_hub.router.subprocess.run")
    def test_route_question_to_architect_e2e(self, mock_run: MagicMock) -> None:
        """Test end-to-end routing of question to architect."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

        # Mock CLI response
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use OAuth2 with JWT", '
                '"rationale": "Industry standard for APIs", "confidence": 92}'
            ),
            stderr="",
        )

        # Load config from sample file
        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80, "model": "sonnet"},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["authentication", "database", "architecture"],
                        "model": "opus",
                    },
                },
            }
        )

        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What authentication method should we use for the API?",
            context="Building a REST API for mobile and web clients",
            feature_id="005-user-auth",
        )

        # Route the question
        handle = router.route_question(question)

        # Verify routing
        assert handle.agent_role == "architect"
        assert handle.agent_name == "@duc"
        mock_run.assert_called_once()

    @patch("agent_hub.router.subprocess.run")
    def test_route_question_with_override_e2e(self, mock_run: MagicMock) -> None:
        """Test routing with topic override goes to human."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

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
                        "agent": "human",
                        "confidence_threshold": 95,
                    },
                },
            }
        )

        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="How should we handle security for this sensitive data?",
            feature_id="005-user-auth",
        )

        # Route the question - should go to human, not dispatch
        handle = router.route_question(question)

        # Should not call CLI since it goes to human
        mock_run.assert_not_called()
        assert handle.agent_role == "human"


@pytest.mark.journey("AH-001")
class TestAskExpertE2E:
    """E2E tests for ask_expert flow (T028 - US1).

    User Story 1: Route Questions to Experts
    - Orchestration agents can route questions to domain experts via ask_expert
    - Returns HubResponse with answer, confidence, session_id
    """

    @patch("agent_hub.router.subprocess.run")
    def test_ask_expert_routes_and_returns_response_e2e(self, mock_run: MagicMock) -> None:
        """Test end-to-end ask_expert routing and response."""
        from agent_hub.hub import AgentHub

        # Mock CLI response from expert agent
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Use OAuth2 with JWT tokens", '
                '"rationale": "Industry standard for REST APIs with excellent security", '
                '"confidence": 92}'
            ),
            stderr="",
        )

        # Load config
        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80, "model": "sonnet"},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["authentication", "database", "architecture"],
                        "model": "opus",
                    },
                },
            }
        )

        hub = AgentHub(config)

        # Ask expert
        response = hub.ask_expert(
            topic="authentication",
            question="What authentication method should we use for the API?",
            context="Building a REST API for mobile and web clients",
            feature_id="005-user-auth",
        )

        # Verify response structure
        assert response.answer == "Use OAuth2 with JWT tokens"
        assert response.confidence == 92
        assert response.status == ResponseStatus.RESOLVED
        assert response.session_id is not None
        assert response.escalation_id is None  # High confidence, no escalation

        # Verify CLI was called
        mock_run.assert_called_once()

    @patch("agent_hub.router.subprocess.run")
    def test_ask_expert_low_confidence_triggers_escalation_e2e(self, mock_run: MagicMock) -> None:
        """Test that low confidence triggers escalation with PENDING_HUMAN status."""
        from agent_hub.hub import AgentHub

        # Mock CLI response with low confidence
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                '{"answer": "Maybe use encryption", '
                '"rationale": "Not sure about the requirements", '
                '"confidence": 55, '
                '"uncertainty_reasons": ["Missing security requirements"]}'
            ),
            stderr="",
        )

        config = ConfigLoader.load_from_dict(
            {
                "defaults": {"confidence_threshold": 80, "model": "sonnet"},
                "agents": {
                    "architect": {
                        "name": "@duc",
                        "topics": ["security"],
                    },
                },
            }
        )

        hub = AgentHub(config)

        response = hub.ask_expert(
            topic="security",
            question="How should we handle encryption?",
            feature_id="005-security",
        )

        # Low confidence should trigger escalation
        assert response.status == ResponseStatus.PENDING_HUMAN
        assert response.confidence == 55
        assert response.escalation_id is not None
        assert response.session_id is not None

    def test_ask_expert_unknown_topic_returns_error_e2e(self) -> None:
        """Test that unknown topic raises UnknownTopicError."""
        from agent_hub.exceptions import UnknownTopicError
        from agent_hub.hub import AgentHub

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

        hub = AgentHub(config)

        with pytest.raises(UnknownTopicError) as exc_info:
            hub.ask_expert(
                topic="unknown_topic",
                question="What about this unknown thing?",
                feature_id="005-test",
            )

        assert exc_info.value.topic == "unknown_topic"
        assert "authentication" in exc_info.value.available_topics
