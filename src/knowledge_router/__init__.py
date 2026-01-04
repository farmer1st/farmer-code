"""Knowledge Router - Question-answer orchestration for agent communication.

This module provides the Knowledge Router, which orchestrates a question-answer
protocol between @baron (the PM agent) and specialized knowledge/execution agents.

Key Features:
- Route questions to appropriate knowledge agents based on topic
- Validate answers against confidence thresholds (default 80%)
- Escalate low-confidence answers to humans
- Log all Q&A exchanges for retrospective analysis
- Dispatch execution tasks to specialist agents with scoped access
"""

__version__ = "0.1.0"

from .config import ConfigLoader, RoutingConfig
from .dispatcher import AgentDispatcher
from .exceptions import (
    AgentDispatchError,
    AgentResponseError,
    AgentTimeoutError,
    ConfigurationError,
    EscalationError,
    KnowledgeRouterError,
    LoggingError,
    RoutingError,
    ScopeViolationError,
    ValidationError,
)
from .models import (
    AgentDefinition,
    AgentHandle,
    AgentStatus,
    AgentType,
    Answer,
    AnswerValidationResult,
    ExecutionStatus,
    HumanAction,
    Question,
    QuestionTarget,
    RoutingRule,
    TaskType,
    ValidationOutcome,
)
from .router import KnowledgeRouterService

__all__ = [
    # Version
    "__version__",
    # Service
    "KnowledgeRouterService",
    # Config
    "ConfigLoader",
    "RoutingConfig",
    # Dispatcher
    "AgentDispatcher",
    # Models
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
    "KnowledgeRouterError",
    "ConfigurationError",
    "RoutingError",
    "AgentDispatchError",
    "AgentTimeoutError",
    "AgentResponseError",
    "ValidationError",
    "EscalationError",
    "ScopeViolationError",
    "LoggingError",
]
