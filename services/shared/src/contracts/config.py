"""Service configuration with environment loading."""

import os
from typing import Any

from pydantic import BaseModel, Field


class ServiceConfig(BaseModel):
    """Base configuration for all services.

    Loads configuration from environment variables with sensible defaults.

    Example:
        config = ServiceConfig.from_env()
        print(config.host, config.port)
    """

    # Server settings
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8000, description="Port to bind to")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Service URLs
    orchestrator_url: str = Field(
        default="http://localhost:8001",
        description="Orchestrator service URL",
    )
    agent_hub_url: str = Field(
        default="http://localhost:8002",
        description="Agent Hub service URL",
    )
    baron_url: str = Field(
        default="http://localhost:8010",
        description="Baron agent service URL",
    )

    # Database settings
    database_url: str = Field(
        default="sqlite:///./data/db.sqlite",
        description="Database connection URL",
    )

    # API settings
    api_timeout: float = Field(
        default=300.0,
        description="Default API timeout in seconds",
    )
    confidence_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Minimum confidence for auto-approval",
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Log level")
    log_dir: str = Field(default="./data/logs", description="Log directory")

    # Claude settings
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key for Claude",
    )

    @classmethod
    def from_env(cls, prefix: str = "") -> "ServiceConfig":
        """Load configuration from environment variables.

        Args:
            prefix: Optional prefix for environment variables (e.g., "ORCHESTRATOR_")

        Returns:
            ServiceConfig with values from environment

        Environment variables:
            - {PREFIX}HOST: Server host
            - {PREFIX}PORT: Server port
            - {PREFIX}DEBUG: Enable debug mode
            - {PREFIX}ORCHESTRATOR_URL: Orchestrator service URL
            - {PREFIX}AGENT_HUB_URL: Agent Hub service URL
            - {PREFIX}BARON_URL: Baron agent service URL
            - {PREFIX}DATABASE_URL: Database connection URL
            - {PREFIX}API_TIMEOUT: API timeout in seconds
            - {PREFIX}CONFIDENCE_THRESHOLD: Minimum confidence
            - {PREFIX}LOG_LEVEL: Log level
            - {PREFIX}LOG_DIR: Log directory
            - ANTHROPIC_API_KEY: Claude API key (no prefix)
        """

        def get_env(key: str, default: Any = None) -> Any:
            """Get environment variable with optional prefix."""
            prefixed_key = f"{prefix}{key}" if prefix else key
            return os.environ.get(prefixed_key, default)

        return cls(
            host=get_env("HOST", "0.0.0.0"),
            port=int(get_env("PORT", "8000")),
            debug=get_env("DEBUG", "false").lower() in ("true", "1", "yes"),
            orchestrator_url=get_env("ORCHESTRATOR_URL", "http://localhost:8001"),
            agent_hub_url=get_env("AGENT_HUB_URL", "http://localhost:8002"),
            baron_url=get_env("BARON_URL", "http://localhost:8010"),
            database_url=get_env("DATABASE_URL", "sqlite:///./data/db.sqlite"),
            api_timeout=float(get_env("API_TIMEOUT", "300.0")),
            confidence_threshold=int(get_env("CONFIDENCE_THRESHOLD", "80")),
            log_level=get_env("LOG_LEVEL", "INFO"),
            log_dir=get_env("LOG_DIR", "./data/logs"),
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )


class OrchestratorConfig(ServiceConfig):
    """Configuration specific to Orchestrator service."""

    @classmethod
    def from_env(cls) -> "OrchestratorConfig":
        """Load Orchestrator configuration from environment."""
        base = ServiceConfig.from_env("ORCHESTRATOR_")
        return cls(**base.model_dump())


class AgentHubConfig(ServiceConfig):
    """Configuration specific to Agent Hub service."""

    github_token: str | None = Field(
        default=None,
        description="GitHub token for escalation comments",
    )
    github_repo: str | None = Field(
        default=None,
        description="GitHub repo for escalation (owner/repo)",
    )

    @classmethod
    def from_env(cls) -> "AgentHubConfig":
        """Load Agent Hub configuration from environment."""
        base = ServiceConfig.from_env("AGENT_HUB_")
        return cls(
            **base.model_dump(),
            github_token=os.environ.get("GITHUB_TOKEN"),
            github_repo=os.environ.get("GITHUB_REPO"),
        )


class AgentConfig(ServiceConfig):
    """Configuration specific to Agent services (Baron, Duc, Marie)."""

    agent_name: str = Field(..., description="Agent identifier")
    allowed_tools: list[str] = Field(
        default_factory=lambda: ["Read", "Write", "Glob", "Grep", "Edit"],
        description="Claude Code tools the agent can use",
    )
    permission_mode: str = Field(
        default="acceptEdits",
        description="Claude Code permission mode",
    )

    @classmethod
    def from_env(cls, agent_name: str) -> "AgentConfig":
        """Load Agent configuration from environment.

        Args:
            agent_name: Agent identifier (baron, duc, marie)

        Returns:
            AgentConfig for the specified agent
        """
        prefix = f"{agent_name.upper()}_"
        base = ServiceConfig.from_env(prefix)

        # Parse allowed tools from comma-separated string
        tools_str = os.environ.get(f"{prefix}ALLOWED_TOOLS", "Read,Write,Glob,Grep,Edit")
        allowed_tools = [t.strip() for t in tools_str.split(",")]

        return cls(
            **base.model_dump(),
            agent_name=agent_name,
            allowed_tools=allowed_tools,
            permission_mode=os.environ.get(f"{prefix}PERMISSION_MODE", "acceptEdits"),
        )
