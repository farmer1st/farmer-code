"""Configuration management for Knowledge Router.

This module handles loading and managing routing configuration from YAML files.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .models import AgentDefinition, AgentType, RoutingRule


class ExecutionAgentDefinition(BaseModel):
    """Definition of an execution agent with scoped access."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Display name (e.g., '@marie')")
    scope: list[str] = Field(
        default_factory=list,
        description="Directories agent can write to",
    )
    model: str = Field(
        default="sonnet",
        description="Model for this agent",
    )


class RoutingConfig(BaseModel):
    """Complete routing configuration.

    Loaded from YAML file, defines agents, topics, thresholds, and overrides.
    """

    model_config = ConfigDict(frozen=False)  # Config can be updated at runtime

    default_confidence_threshold: int = Field(default=80)
    default_timeout_seconds: int = Field(default=120)
    default_model: str = Field(default="sonnet")

    agents: dict[str, AgentDefinition] = Field(
        default_factory=dict,
        description="Agent definitions keyed by ID",
    )
    overrides: dict[str, RoutingRule] = Field(
        default_factory=dict,
        description="Topic-specific override rules",
    )
    execution_agents: dict[str, ExecutionAgentDefinition] = Field(
        default_factory=dict,
        description="Execution agent definitions",
    )

    def get_agent_for_topic(self, topic: str) -> str:
        """Resolve topic to agent ID.

        Priority:
        1. Overrides (topic-specific rules)
        2. Agent topic mappings
        3. Default to human
        """
        # Check overrides first
        if topic in self.overrides:
            return self.overrides[topic].agent

        # Find agent by topic
        for agent_id, agent in self.agents.items():
            if topic in agent.topics:
                return agent_id

        # Default to human
        return "human"

    def get_threshold_for_topic(self, topic: str) -> int:
        """Get confidence threshold for topic.

        Priority:
        1. Override threshold (if set)
        2. Default threshold
        """
        if topic in self.overrides:
            override = self.overrides[topic]
            if override.confidence_threshold is not None:
                return override.confidence_threshold
        return self.default_confidence_threshold

    def get_model_for_agent(self, agent_id: str) -> str:
        """Get model to use for an agent."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            return agent.default_model
        if agent_id in self.execution_agents:
            return self.execution_agents[agent_id].model
        return self.default_model

    def get_timeout_for_agent(self, agent_id: str) -> int:
        """Get timeout for an agent."""
        if agent_id in self.agents:
            return self.agents[agent_id].default_timeout
        return self.default_timeout_seconds


class ConfigLoader:
    """Loads routing configuration from YAML files."""

    @staticmethod
    def load_from_file(path: str | Path) -> RoutingConfig:
        """Load routing configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            RoutingConfig instance.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If config is invalid.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path) as f:
            raw_config = yaml.safe_load(f)

        return ConfigLoader._parse_config(raw_config)

    @staticmethod
    def load_from_dict(data: dict[str, Any]) -> RoutingConfig:
        """Load routing configuration from a dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            RoutingConfig instance.
        """
        return ConfigLoader._parse_config(data)

    @staticmethod
    def _parse_config(raw: dict[str, Any]) -> RoutingConfig:
        """Parse raw config dict into RoutingConfig.

        Args:
            raw: Raw configuration dictionary.

        Returns:
            RoutingConfig instance.
        """
        defaults = raw.get("defaults", {})
        agents_raw = raw.get("agents", {})
        overrides_raw = raw.get("overrides", {})
        execution_agents_raw = raw.get("execution_agents", {})

        # Parse agents
        agents: dict[str, AgentDefinition] = {}
        for agent_id, agent_data in agents_raw.items():
            agents[agent_id] = AgentDefinition(
                id=agent_id,
                name=agent_data.get("name", f"@{agent_id}"),
                agent_type=AgentType.KNOWLEDGE,
                topics=agent_data.get("topics", []),
                default_model=agent_data.get("model", defaults.get("model", "sonnet")),
                default_timeout=agent_data.get(
                    "timeout_seconds", defaults.get("timeout_seconds", 120)
                ),
            )

        # Parse overrides
        overrides: dict[str, RoutingRule] = {}
        for topic, override_data in overrides_raw.items():
            overrides[topic] = RoutingRule(
                topic=topic,
                agent=override_data.get("agent", "human"),
                confidence_threshold=override_data.get("confidence_threshold"),
                model_override=override_data.get("model"),
            )

        # Parse execution agents
        execution_agents: dict[str, ExecutionAgentDefinition] = {}
        for agent_id, agent_data in execution_agents_raw.items():
            execution_agents[agent_id] = ExecutionAgentDefinition(
                name=agent_data.get("name", f"@{agent_id}"),
                scope=agent_data.get("scope", []),
                model=agent_data.get("model", defaults.get("model", "sonnet")),
            )

        return RoutingConfig(
            default_confidence_threshold=defaults.get("confidence_threshold", 80),
            default_timeout_seconds=defaults.get("timeout_seconds", 120),
            default_model=defaults.get("model", "sonnet"),
            agents=agents,
            overrides=overrides,
            execution_agents=execution_agents,
        )
