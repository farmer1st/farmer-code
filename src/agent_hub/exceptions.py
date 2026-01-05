"""Exception classes for Agent Hub."""


class KnowledgeRouterError(Exception):
    """Base exception for Agent Hub (legacy name for compatibility)."""

    pass


# Alias for new code
AgentHubError = KnowledgeRouterError


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


# =============================================================================
# Session Exceptions (T021-T023)
# =============================================================================


class SessionNotFoundError(KnowledgeRouterError):
    """Session with given ID does not exist (T021)."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session not found: {session_id}")


class SessionClosedError(KnowledgeRouterError):
    """Session is closed and cannot accept new messages (T022)."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Session is closed: {session_id}")


class UnknownTopicError(KnowledgeRouterError):
    """Topic is not configured in routing rules (T023)."""

    def __init__(self, topic: str, available_topics: list[str] | None = None) -> None:
        self.topic = topic
        self.available_topics = available_topics or []
        msg = f"Unknown topic: {topic}"
        if self.available_topics:
            msg += f". Available topics: {', '.join(self.available_topics)}"
        super().__init__(msg)
