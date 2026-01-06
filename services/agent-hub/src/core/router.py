"""Agent routing logic for Agent Hub.

This module handles routing questions to the appropriate agent based on topic.
"""

from typing import Any


class UnknownTopicError(Exception):
    """Raised when a topic is not configured."""

    def __init__(self, topic: str, available_topics: list[str]) -> None:
        self.topic = topic
        self.available_topics = available_topics
        super().__init__(f"Unknown topic: {topic}. Available: {available_topics}")


class UnknownAgentError(Exception):
    """Raised when an agent is not configured."""

    def __init__(self, agent: str, available_agents: list[str]) -> None:
        self.agent = agent
        self.available_agents = available_agents
        super().__init__(f"Unknown agent: {agent}. Available: {available_agents}")


# Default routing configuration
# In production, this would be loaded from config file
DEFAULT_ROUTING_CONFIG: dict[str, dict[str, Any]] = {
    "topics": {
        "architecture": {
            "agent": "duc",
            "model": "opus",
            "confidence_threshold": 80,
        },
        "security": {
            "agent": "charles",
            "model": "opus",
            "confidence_threshold": 95,  # Higher threshold for security
        },
        "testing": {
            "agent": "marie",
            "model": "sonnet",
            "confidence_threshold": 80,
        },
        "frontend": {
            "agent": "dali",
            "model": "sonnet",
            "confidence_threshold": 80,
        },
        "backend": {
            "agent": "dede",
            "model": "sonnet",
            "confidence_threshold": 80,
        },
        "devops": {
            "agent": "gustave",
            "model": "sonnet",
            "confidence_threshold": 80,
        },
    },
    "agents": {
        "baron": {
            "url": "http://localhost:8002",
            "workflows": ["specify", "plan", "tasks", "implement"],
        },
        "duc": {
            "url": "http://localhost:8003",
            "workflows": ["architecture", "api_design", "system_design"],
        },
        "marie": {
            "url": "http://localhost:8004",
            "workflows": ["testing", "edge_cases", "qa_review"],
        },
        # Placeholder agents - will be routed to baron for now
        "charles": {"url": "http://localhost:8002", "workflows": ["security"]},
        "dali": {"url": "http://localhost:8002", "workflows": ["frontend"]},
        "dede": {"url": "http://localhost:8002", "workflows": ["backend"]},
        "gustave": {"url": "http://localhost:8002", "workflows": ["devops"]},
    },
    "defaults": {
        "confidence_threshold": 80,
        "timeout_seconds": 300,
    },
}


class AgentRouter:
    """Routes requests to appropriate agents based on topic.

    Example:
        router = AgentRouter()
        agent_info = router.get_agent_for_topic("architecture")
        print(agent_info["agent"])  # "duc"
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize router with configuration.

        Args:
            config: Routing configuration. Uses DEFAULT_ROUTING_CONFIG if not provided.
        """
        self.config = config or DEFAULT_ROUTING_CONFIG

    @property
    def available_topics(self) -> list[str]:
        """Get list of available topics."""
        return list(self.config.get("topics", {}).keys())

    @property
    def available_agents(self) -> list[str]:
        """Get list of available agents."""
        return list(self.config.get("agents", {}).keys())

    def get_agent_for_topic(self, topic: str) -> dict[str, Any]:
        """Get agent configuration for a topic.

        Args:
            topic: Topic to route (e.g., "architecture", "security")

        Returns:
            Dict with agent, model, confidence_threshold, url

        Raises:
            UnknownTopicError: If topic is not configured
        """
        topics = self.config.get("topics", {})
        if topic not in topics:
            raise UnknownTopicError(topic, self.available_topics)

        topic_config = topics[topic]
        agent_name = topic_config["agent"]
        agent_config = self.config.get("agents", {}).get(agent_name, {})

        return {
            "agent": agent_name,
            "model": topic_config.get("model", "sonnet"),
            "confidence_threshold": topic_config.get(
                "confidence_threshold",
                self.config.get("defaults", {}).get("confidence_threshold", 80),
            ),
            "url": agent_config.get("url", f"http://{agent_name}:8000"),
        }

    def get_agent_config(self, agent: str) -> dict[str, Any]:
        """Get configuration for a specific agent.

        Args:
            agent: Agent name (e.g., "baron", "duc")

        Returns:
            Dict with url, workflows

        Raises:
            UnknownAgentError: If agent is not configured
        """
        agents = self.config.get("agents", {})
        if agent not in agents:
            raise UnknownAgentError(agent, self.available_agents)

        return agents[agent]

    def get_default_threshold(self) -> int:
        """Get default confidence threshold."""
        return self.config.get("defaults", {}).get("confidence_threshold", 80)


# Module-level convenience functions
_router: AgentRouter | None = None


def get_router() -> AgentRouter:
    """Get or create the default router instance."""
    global _router
    if _router is None:
        _router = AgentRouter()
    return _router


def get_agent_for_topic(topic: str) -> dict[str, Any]:
    """Get agent for a topic using the default router.

    Args:
        topic: Topic to route

    Returns:
        Agent configuration dict
    """
    return get_router().get_agent_for_topic(topic)
