"""Unit tests for RoutingConfig model."""

import pytest
from pydantic import ValidationError

from agent_hub.config import RoutingConfig
from agent_hub.models import AgentDefinition, AgentType, RoutingRule


class TestRoutingRule:
    """Tests for RoutingRule model."""

    def test_routing_rule_basic(self) -> None:
        """Test creating a basic routing rule."""
        rule = RoutingRule(
            topic="security",
            agent="architect",
        )
        assert rule.topic == "security"
        assert rule.agent == "architect"
        assert rule.confidence_threshold is None
        assert rule.model_override is None

    def test_routing_rule_with_threshold(self) -> None:
        """Test routing rule with confidence threshold override."""
        rule = RoutingRule(
            topic="security",
            agent="architect",
            confidence_threshold=95,
        )
        assert rule.confidence_threshold == 95

    def test_routing_rule_human_target(self) -> None:
        """Test routing rule targeting human."""
        rule = RoutingRule(
            topic="budget",
            agent="human",
        )
        assert rule.agent == "human"


class TestAgentDefinition:
    """Tests for AgentDefinition model."""

    def test_agent_definition_knowledge(self) -> None:
        """Test creating a knowledge agent definition."""
        agent = AgentDefinition(
            id="architect",
            name="@duc",
            agent_type=AgentType.KNOWLEDGE,
            topics=["authentication", "database", "architecture"],
            default_model="opus",
        )
        assert agent.id == "architect"
        assert agent.name == "@duc"
        assert agent.agent_type == AgentType.KNOWLEDGE
        assert len(agent.topics) == 3

    def test_agent_definition_execution(self) -> None:
        """Test creating an execution agent definition."""
        agent = AgentDefinition(
            id="dev",
            name="@dede",
            agent_type=AgentType.EXECUTION,
            scope=["src/"],
            default_model="sonnet",
        )
        assert agent.agent_type == AgentType.EXECUTION
        assert agent.scope == ["src/"]


class TestRoutingConfig:
    """Tests for RoutingConfig model."""

    def test_routing_config_defaults(self) -> None:
        """Test RoutingConfig with defaults."""
        config = RoutingConfig()
        assert config.default_confidence_threshold == 80
        assert config.default_timeout_seconds == 120
        assert config.default_model == "sonnet"

    def test_get_agent_for_topic_direct(self) -> None:
        """Test getting agent for a topic directly mapped."""
        config = RoutingConfig(
            agents={
                "architect": AgentDefinition(
                    id="architect",
                    name="@duc",
                    agent_type=AgentType.KNOWLEDGE,
                    topics=["authentication", "database"],
                ),
            }
        )
        agent = config.get_agent_for_topic("authentication")
        assert agent == "architect"

    def test_get_agent_for_topic_override(self) -> None:
        """Test that override takes precedence."""
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
                    agent="human",  # Override to human
                ),
            },
        )
        agent = config.get_agent_for_topic("security")
        assert agent == "human"

    def test_get_agent_for_topic_unknown(self) -> None:
        """Test that unknown topic defaults to human."""
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
        agent = config.get_agent_for_topic("unknown_topic")
        assert agent == "human"

    def test_get_threshold_for_topic_default(self) -> None:
        """Test getting default threshold when no override."""
        config = RoutingConfig(default_confidence_threshold=80)
        threshold = config.get_threshold_for_topic("authentication")
        assert threshold == 80

    def test_get_threshold_for_topic_override(self) -> None:
        """Test getting overridden threshold for topic."""
        config = RoutingConfig(
            default_confidence_threshold=80,
            overrides={
                "security": RoutingRule(
                    topic="security",
                    agent="architect",
                    confidence_threshold=95,
                ),
            },
        )
        threshold = config.get_threshold_for_topic("security")
        assert threshold == 95

    def test_routing_config_immutable(self) -> None:
        """Test that RoutingRule is immutable."""
        rule = RoutingRule(topic="test", agent="architect")
        with pytest.raises(ValidationError):
            rule.agent = "product"
