"""End-to-end tests for question routing (KR-001)."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from knowledge_router.config import ConfigLoader
from knowledge_router.models import Question, QuestionTarget


@pytest.mark.journey("KR-001")
class TestRouteQuestionE2E:
    """E2E tests for routing questions to knowledge agents."""

    @patch("knowledge_router.dispatcher.subprocess.run")
    def test_route_question_to_architect_e2e(self, mock_run: MagicMock) -> None:
        """Test end-to-end routing of question to architect."""
        from knowledge_router.router import KnowledgeRouterService

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

    @patch("knowledge_router.dispatcher.subprocess.run")
    def test_route_question_with_override_e2e(self, mock_run: MagicMock) -> None:
        """Test routing with topic override goes to human."""
        from knowledge_router.router import KnowledgeRouterService

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
