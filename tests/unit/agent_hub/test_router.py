"""Unit tests for KnowledgeRouterService."""

import uuid

from agent_hub.config import RoutingConfig
from agent_hub.models import (
    AgentDefinition,
    AgentType,
    Question,
    QuestionTarget,
    RoutingRule,
)


class TestRouteQuestion:
    """Tests for question routing logic (KR-001)."""

    def test_route_question_to_architect_by_topic(self) -> None:
        """Test routing question to architect based on topic."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

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
        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What authentication method should we use?",
            feature_id="005-user-auth",
        )

        agent_id = router._resolve_agent_for_question(question)
        assert agent_id == "architect"

    def test_route_question_to_product_by_topic(self) -> None:
        """Test routing question to product agent based on topic."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

        config = RoutingConfig(
            agents={
                "product": AgentDefinition(
                    id="product",
                    name="@veuve",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["scope", "priority", "features"],
                ),
            }
        )
        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="priority",
            suggested_target=QuestionTarget.PRODUCT,
            question="What is the priority of this feature?",
            feature_id="005-user-auth",
        )

        agent_id = router._resolve_agent_for_question(question)
        assert agent_id == "product"

    def test_route_question_unknown_topic_to_human(self) -> None:
        """Test that unknown topics route to human."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

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
        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="unknown_topic",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What should we do about this unknown thing?",
            feature_id="005-user-auth",
        )

        agent_id = router._resolve_agent_for_question(question)
        assert agent_id == "human"


class TestRoutingOverride:
    """Tests for routing override logic (KR-001)."""

    def test_override_takes_precedence(self) -> None:
        """Test that topic override takes precedence over agent topics."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication", "security"],
                ),
            },
            overrides={
                "security": RoutingRule(
                    topic="security",
                    agent="human",  # Override: security goes to human
                ),
            },
        )
        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="security",
            suggested_target=QuestionTarget.ARCHITECT,
            question="How should we handle security for this?",
            feature_id="005-user-auth",
        )

        agent_id = router._resolve_agent_for_question(question)
        assert agent_id == "human"

    def test_override_to_different_agent(self) -> None:
        """Test override routing to a different agent."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication"],
                ),
                "product": AgentDefinition(
                    id="product",
                    name="@veuve",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["scope"],
                ),
            },
            overrides={
                "authentication": RoutingRule(
                    topic="authentication",
                    agent="product",  # Override: auth goes to product
                ),
            },
        )
        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="authentication",
            suggested_target=QuestionTarget.ARCHITECT,
            question="What auth method should we use?",
            feature_id="005-user-auth",
        )

        agent_id = router._resolve_agent_for_question(question)
        assert agent_id == "product"

    def test_no_override_uses_agent_topics(self) -> None:
        """Test that without override, agent topics are used."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication", "database"],
                ),
            },
            overrides={
                "security": RoutingRule(topic="security", agent="human"),
            },
        )
        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="database",  # No override for this topic
            suggested_target=QuestionTarget.ARCHITECT,
            question="Which database should we use?",
            feature_id="005-user-auth",
        )

        agent_id = router._resolve_agent_for_question(question)
        assert agent_id == "architect"

    def test_suggested_target_human_goes_to_human(self) -> None:
        """Test that HUMAN suggested target always goes to human."""
        from agent_hub.hub import AgentHub as KnowledgeRouterService

        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["budget"],  # Even if topic matches
                ),
            }
        )
        router = KnowledgeRouterService(config)

        question = Question(
            id=str(uuid.uuid4()),
            topic="budget",
            suggested_target=QuestionTarget.HUMAN,
            question="What is the budget for this project?",
            feature_id="005-user-auth",
        )

        agent_id = router._resolve_agent_for_question(question)
        assert agent_id == "human"
