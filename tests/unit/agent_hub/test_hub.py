"""Unit tests for AgentHub service (US1: Route Questions to Experts)."""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest

from agent_hub.config import RoutingConfig
from agent_hub.exceptions import UnknownTopicError
from agent_hub.hub import AgentHub
from agent_hub.models import (
    AgentDefinition,
    AgentHandle,
    AgentStatus,
    AgentType,
    Answer,
    HubResponse,
    ResponseStatus,
)


class TestAskExpert:
    """Tests for ask_expert routing logic (T025 - US1)."""

    def test_ask_expert_routes_to_correct_agent(self) -> None:
        """Test that ask_expert routes question to correct agent by topic."""
        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication", "database", "architecture"],
                ),
            }
        )
        hub = AgentHub(config)

        # Mock the router's dispatch and parse methods
        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Use OAuth2 with JWT",
                    rationale="Industry standard for REST APIs with good security",
                    confidence=92,
                    model_used="opus",
                    duration_seconds=2.5,
                )

                response = hub.ask_expert(
                    topic="authentication",
                    question="What authentication method should we use?",
                    feature_id="005-user-auth",
                )

                assert isinstance(response, HubResponse)
                assert response.answer == "Use OAuth2 with JWT"
                assert response.confidence == 92
                assert response.session_id  # Should have a session ID
                assert response.status == ResponseStatus.RESOLVED

    def test_ask_expert_returns_session_id(self) -> None:
        """Test that ask_expert returns a session_id for follow-ups."""
        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["database"],
                ),
            }
        )
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Use PostgreSQL",
                    rationale="Robust and well-supported database",
                    confidence=88,
                    model_used="opus",
                    duration_seconds=2.0,
                )

                response = hub.ask_expert(
                    topic="database",
                    question="Which database should we use?",
                    feature_id="005-db-setup",
                )

                assert response.session_id is not None
                assert len(response.session_id) > 0
                # Session ID should be a valid UUID
                uuid.UUID(response.session_id)

    def test_ask_expert_with_unknown_topic_raises_error(self) -> None:
        """Test that ask_expert raises UnknownTopicError for unknown topics."""
        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication"],
                ),
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

    def test_ask_expert_with_context(self) -> None:
        """Test that ask_expert passes context to agent."""
        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["architecture"],
                ),
            }
        )
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Use microservices",
                    rationale="Better scalability for high load scenarios",
                    confidence=85,
                    model_used="opus",
                    duration_seconds=3.0,
                )

                response = hub.ask_expert(
                    topic="architecture",
                    question="What architecture should we use?",
                    context="We expect 100k users and need horizontal scaling",
                    feature_id="005-arch",
                )

                assert response.answer == "Use microservices"
                # Verify context was passed to dispatch
                call_args = mock_dispatch.call_args
                assert "100k users" in call_args[0][0].context

    def test_ask_expert_with_low_confidence_returns_pending(self) -> None:
        """Test that low confidence answers return PENDING_HUMAN status."""
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
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Maybe use encryption",
                    rationale="Not sure about requirements here",
                    confidence=60,  # Below threshold
                    uncertainty_reasons=["Missing security requirements"],
                    model_used="opus",
                    duration_seconds=2.0,
                )

                response = hub.ask_expert(
                    topic="security",
                    question="How should we handle encryption?",
                    feature_id="005-security",
                )

                assert response.status == ResponseStatus.PENDING_HUMAN
                assert response.confidence == 60
                assert response.escalation_id is not None


class TestAskExpertTopicValidation:
    """Tests for topic validation in ask_expert (T031 - US1)."""

    def test_valid_topic_format_accepted(self) -> None:
        """Test that valid topic formats are accepted."""
        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["auth_v2", "database_design"],
                ),
            }
        )
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Use OAuth2",
                    rationale="Standard approach for API authentication",
                    confidence=90,
                    model_used="opus",
                    duration_seconds=2.0,
                )

                # Should not raise
                response = hub.ask_expert(
                    topic="auth_v2",
                    question="What auth approach for API v2?",
                    feature_id="005-auth",
                )
                assert response.status == ResponseStatus.RESOLVED

    def test_unknown_topic_includes_available_topics(self) -> None:
        """Test that UnknownTopicError includes list of available topics."""
        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication", "database"],
                ),
                "product": AgentDefinition(
                    id="product",
                    name="@veuve",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["scope", "priority"],
                ),
            }
        )
        hub = AgentHub(config)

        with pytest.raises(UnknownTopicError) as exc_info:
            hub.ask_expert(
                topic="unknown",
                question="What about this?",
                feature_id="005-test",
            )

        # Should include available topics in error
        available = exc_info.value.available_topics
        assert "authentication" in available
        assert "database" in available
        assert "scope" in available
        assert "priority" in available


class TestCheckEscalation:
    """Tests for check_escalation() method (T056 - US4)."""

    def test_check_escalation_returns_pending_escalation(self) -> None:
        """Test that check_escalation returns a pending escalation by ID."""
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
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Maybe use AES",
                    rationale="Not sure about requirements",
                    confidence=50,  # Low confidence
                    uncertainty_reasons=["Missing requirements"],
                    model_used="sonnet",
                    duration_seconds=1.5,
                )

                response = hub.ask_expert(
                    topic="security",
                    question="What encryption?",
                    feature_id="005-security",
                )

                # Verify escalation was created
                assert response.escalation_id is not None

                # Check the escalation
                escalation = hub.check_escalation(response.escalation_id)
                assert escalation is not None
                assert escalation.id == response.escalation_id
                assert escalation.status == "pending"

    def test_check_escalation_not_found_raises_error(self) -> None:
        """Test that check_escalation raises error for unknown ID."""
        from agent_hub.exceptions import EscalationError

        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["test"],
                ),
            },
        )
        hub = AgentHub(config)

        with pytest.raises(EscalationError) as exc_info:
            hub.check_escalation("nonexistent-escalation-id")

        assert "nonexistent-escalation-id" in str(exc_info.value)


class TestAddHumanResponse:
    """Tests for add_human_response() method (T057 - US4)."""

    def test_add_human_response_confirms_answer(self) -> None:
        """Test that add_human_response processes confirmation correctly."""
        from agent_hub.models import HumanAction

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
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Use PostgreSQL",
                    rationale="Good for complex queries",
                    confidence=65,
                    model_used="sonnet",
                    duration_seconds=1.5,
                )

                response = hub.ask_expert(
                    topic="database",
                    question="What database?",
                    feature_id="005-db",
                )

                # Add human confirmation
                result = hub.add_human_response(
                    escalation_id=response.escalation_id,
                    action=HumanAction.CONFIRM,
                    responder="@farmer1st",
                )

                assert result.escalation_resolved is True
                assert result.action_taken == HumanAction.CONFIRM
                assert result.final_answer is not None

                # Check escalation is now resolved
                escalation = hub.check_escalation(response.escalation_id)
                assert escalation.status == "resolved"

    def test_add_human_response_corrects_answer(self) -> None:
        """Test that add_human_response processes correction correctly."""
        from agent_hub.models import HumanAction

        config = RoutingConfig(
            default_confidence_threshold=80,
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["caching"],
                ),
            },
        )
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Use Memcached",
                    rationale="Simple caching solution",
                    confidence=55,
                    model_used="sonnet",
                    duration_seconds=1.5,
                )

                response = hub.ask_expert(
                    topic="caching",
                    question="What caching?",
                    feature_id="005-cache",
                )

                # Add human correction
                result = hub.add_human_response(
                    escalation_id=response.escalation_id,
                    action=HumanAction.CORRECT,
                    corrected_answer="Use Redis for better persistence and data structures",
                    responder="@farmer1st",
                )

                assert result.escalation_resolved is True
                assert result.action_taken == HumanAction.CORRECT
                assert "Redis" in result.final_answer.answer
                assert result.final_answer.confidence == 100  # Human-corrected

    def test_add_human_response_adds_context_needs_reroute(self) -> None:
        """Test that add_human_response handles ADD_CONTEXT with reroute."""
        from agent_hub.models import HumanAction

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
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Use microservices",
                    rationale="Need more context about scale",
                    confidence=45,
                    uncertainty_reasons=["Unknown scale requirements"],
                    model_used="sonnet",
                    duration_seconds=1.5,
                )

                response = hub.ask_expert(
                    topic="architecture",
                    question="What architecture?",
                    feature_id="005-arch",
                )

                # Add context - needs reroute
                result = hub.add_human_response(
                    escalation_id=response.escalation_id,
                    action=HumanAction.ADD_CONTEXT,
                    additional_context="We expect 100K concurrent users",
                    responder="@farmer1st",
                )

                assert result.escalation_resolved is False
                assert result.needs_reroute is True
                assert result.updated_question is not None
                assert "100K concurrent users" in result.updated_question.context

    def test_add_human_response_feeds_back_to_session(self) -> None:
        """Test that human response is added to session messages (T061)."""
        from agent_hub.models import HumanAction, MessageRole

        config = RoutingConfig(
            default_confidence_threshold=80,
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["testing"],
                ),
            },
        )
        hub = AgentHub(config)

        with patch.object(hub._router, "dispatch_question") as mock_dispatch:
            handle = AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="architect",
                agent_name="@duc",
                status=AgentStatus.COMPLETED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            mock_dispatch.return_value = handle

            with patch.object(hub._router, "parse_answer") as mock_parse:
                mock_parse.return_value = Answer(
                    question_id=str(uuid.uuid4()),
                    answered_by="@duc",
                    answer="Use pytest",
                    rationale="Standard Python testing framework",
                    confidence=60,
                    model_used="sonnet",
                    duration_seconds=1.5,
                )

                response = hub.ask_expert(
                    topic="testing",
                    question="What testing framework?",
                    feature_id="005-test",
                )

                # Add human confirmation
                hub.add_human_response(
                    escalation_id=response.escalation_id,
                    action=HumanAction.CONFIRM,
                    responder="@farmer1st",
                )

                # Check session has human message
                session = hub.get_session(response.session_id)
                human_messages = [m for m in session.messages if m.role == MessageRole.HUMAN]
                assert len(human_messages) >= 1
                assert human_messages[-1].metadata is not None
                assert human_messages[-1].metadata.get("responder") == "@farmer1st"

    def test_add_human_response_not_found_raises_error(self) -> None:
        """Test that add_human_response raises error for unknown escalation."""
        from agent_hub.exceptions import EscalationError
        from agent_hub.models import HumanAction

        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["test"],
                ),
            },
        )
        hub = AgentHub(config)

        with pytest.raises(EscalationError) as exc_info:
            hub.add_human_response(
                escalation_id="nonexistent-id",
                action=HumanAction.CONFIRM,
                responder="@farmer1st",
            )

        assert "nonexistent-id" in str(exc_info.value)
