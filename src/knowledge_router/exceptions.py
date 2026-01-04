"""Exception classes for Knowledge Router."""


class KnowledgeRouterError(Exception):
    """Base exception for Knowledge Router."""

    pass


class ConfigurationError(KnowledgeRouterError):
    """Invalid or missing configuration."""

    pass


class RoutingError(KnowledgeRouterError):
    """Error during question routing."""

    pass


class AgentDispatchError(KnowledgeRouterError):
    """Error dispatching agent via CLI."""

    pass


class AgentTimeoutError(AgentDispatchError):
    """Agent timed out."""

    pass


class AgentResponseError(KnowledgeRouterError):
    """Invalid response from agent."""

    pass


class ValidationError(KnowledgeRouterError):
    """Answer validation failed."""

    pass


class EscalationError(KnowledgeRouterError):
    """Error during human escalation."""

    pass


class ScopeViolationError(KnowledgeRouterError):
    """Execution agent attempted to access files outside scope."""

    def __init__(self, agent_id: str, path: str, allowed_scope: list[str]) -> None:
        self.agent_id = agent_id
        self.path = path
        self.allowed_scope = allowed_scope
        super().__init__(
            f"Agent '{agent_id}' attempted to access '{path}' "
            f"outside allowed scope: {allowed_scope}"
        )


class LoggingError(KnowledgeRouterError):
    """Error writing to Q&A log."""

    pass
