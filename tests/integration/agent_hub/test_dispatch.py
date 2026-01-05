"""Integration tests for agent dispatch (KR-001)."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from agent_hub.config import RoutingConfig
from agent_hub.models import (
    AgentDefinition,
    AgentType,
    Question,
    QuestionTarget,
)


class TestAgentDispatch:
    """Tests for agent dispatch via CLI (KR-001)."""

    @patch("agent_hub.router.subprocess.run")
    def test_dispatch_calls_claude_cli(self, mock_run: MagicMock) -> None:
        """Test that dispatch calls Claude CLI with correct args."""
        from agent_hub.router import AgentRouter as AgentDispatcher

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"answer": "Use JWT", "rationale": "Standard approach", "confidence": 85}',
            stderr="",
        )

        config = RoutingConfig(
            default_model="sonnet",
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication"],
                    default_model="opus",
                ),
            },
        )
        dispatcher = AgentDispatcher(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What auth method should we use?",
            feature_id="005-user-auth",
        )

        handle = dispatcher.dispatch_question(question, "architect")

        assert handle is not None
        assert handle.agent_role == "architect"
        assert handle.agent_name == "@duc"
        mock_run.assert_called_once()

        # Verify CLI was called with model
        call_args = mock_run.call_args[0][0]
        assert "claude" in call_args[0] or call_args[0] == "claude"
        assert "--model" in call_args

    @patch("agent_hub.router.subprocess.run")
    def test_dispatch_uses_correct_model(self, mock_run: MagicMock) -> None:
        """Test that dispatch uses agent-specific model."""
        from agent_hub.router import AgentRouter as AgentDispatcher

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"answer": "Test", "rationale": "Rationale here", "confidence": 90}',
            stderr="",
        )

        config = RoutingConfig(
            default_model="sonnet",
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication"],
                    default_model="opus",  # Architect uses opus
                ),
            },
        )
        dispatcher = AgentDispatcher(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What auth method should we use?",
            feature_id="005-user-auth",
        )

        dispatcher.dispatch_question(question, "architect")

        call_args = mock_run.call_args[0][0]
        model_index = call_args.index("--model")
        assert call_args[model_index + 1] == "opus"

    @patch("agent_hub.router.subprocess.run")
    def test_dispatch_handles_cli_error(self, mock_run: MagicMock) -> None:
        """Test that dispatch handles CLI errors gracefully."""
        from agent_hub.exceptions import AgentDispatchError
        from agent_hub.router import AgentRouter as AgentDispatcher

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: something went wrong",
        )

        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication"],
                ),
            },
        )
        dispatcher = AgentDispatcher(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What auth method should we use?",
            feature_id="005-user-auth",
        )

        with pytest.raises(AgentDispatchError):
            dispatcher.dispatch_question(question, "architect")
