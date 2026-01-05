"""Agent Hub - Central coordination layer for agent interactions.

The Agent Hub orchestrates all agent communication, routing questions to expert
agents, managing conversation sessions, validating confidence, and handling
human escalations.

Key Features:
- Route questions to appropriate expert agents based on topic
- Maintain conversation sessions with context preservation
- Validate answers against confidence thresholds (default 80%)
- Escalate low-confidence answers to humans
- Track pending escalations and process human responses
- Log all Q&A exchanges for audit and debugging
"""

__version__ = "0.1.0"

from .config import ConfigLoader, RoutingConfig
from .exceptions import (
    AgentDispatchError,
    AgentHubError,
    AgentResponseError,
    AgentTimeoutError,
    ConfigurationError,
    EscalationError,
    KnowledgeRouterError,
    LoggingError,
    RoutingError,
    ScopeViolationError,
    SessionClosedError,
    SessionNotFoundError,
    UnknownTopicError,
    ValidationError,
)
from .hub import AgentHub
from .models import (
    AgentDefinition,
    AgentHandle,
    AgentStatus,
    AgentType,
    Answer,
    AnswerValidationResult,
    EscalationStatus,
    ExecutionStatus,
    HubResponse,
    HumanAction,
    Message,
    MessageRole,
    Question,
    QuestionTarget,
    ResponseStatus,
    RoutingRule,
    Session,
    SessionStatus,
    TaskType,
    ValidationOutcome,
)
from .router import AgentRouter
from .session import SessionManager

# Backward compatibility aliases
KnowledgeRouterService = AgentHub
AgentDispatcher = AgentRouter

__all__ = [
    # Version
    "__version__",
    # Service
    "AgentHub",
    "KnowledgeRouterService",  # Backward compatibility
    # Config
    "ConfigLoader",
    "RoutingConfig",
    # Router
    "AgentRouter",
    "AgentDispatcher",  # Backward compatibility
    # Session Manager
    "SessionManager",
    # Session Models
    "Session",
    "SessionStatus",
    "Message",
    "MessageRole",
    # Hub Response Models
    "HubResponse",
    "ResponseStatus",
    "EscalationStatus",
    # Core Models
    "Question",
    "QuestionTarget",
    "Answer",
    "AnswerValidationResult",
    "ValidationOutcome",
    "RoutingRule",
    "AgentDefinition",
    "AgentType",
    "AgentHandle",
    "AgentStatus",
    "HumanAction",
    "TaskType",
    "ExecutionStatus",
    # Exceptions
    "AgentHubError",
    "KnowledgeRouterError",  # Backward compatibility
    "ConfigurationError",
    "RoutingError",
    "AgentDispatchError",
    "AgentTimeoutError",
    "AgentResponseError",
    "ValidationError",
    "EscalationError",
    "ScopeViolationError",
    "LoggingError",
    "SessionNotFoundError",
    "SessionClosedError",
    "UnknownTopicError",
]
