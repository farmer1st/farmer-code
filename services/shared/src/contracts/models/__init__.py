"""Shared Pydantic models for Farmer Code services."""

from contracts.models.agent import (
    ErrorDetail,
    ErrorResponse,
    HealthCapabilities,
    HealthResponse,
    InvokeMetadata,
    InvokeRequest,
    InvokeResponse,
    InvokeResult,
)
from contracts.models.escalation import (
    AskExpertRequest,
    AskExpertResponse,
    Escalation,
    EscalationResponse,
    EscalationStatus,
    HumanAction,
    SubmitHumanResponseRequest,
)
from contracts.models.session import (
    CreateSessionRequest,
    Message,
    MessageRole,
    Session,
    SessionResponse,
    SessionStatus,
    SessionWithMessagesResponse,
)
from contracts.models.workflow import (
    AdvanceWorkflowRequest,
    CreateWorkflowRequest,
    WorkflowResponse,
    WorkflowStatus,
    WorkflowType,
)

__all__ = [
    # Workflow
    "WorkflowType",
    "WorkflowStatus",
    "CreateWorkflowRequest",
    "WorkflowResponse",
    "AdvanceWorkflowRequest",
    # Session
    "SessionStatus",
    "MessageRole",
    "Message",
    "Session",
    "CreateSessionRequest",
    "SessionResponse",
    "SessionWithMessagesResponse",
    # Escalation
    "EscalationStatus",
    "HumanAction",
    "Escalation",
    "EscalationResponse",
    "SubmitHumanResponseRequest",
    "AskExpertRequest",
    "AskExpertResponse",
    # Agent
    "InvokeRequest",
    "InvokeResult",
    "InvokeMetadata",
    "InvokeResponse",
    "HealthCapabilities",
    "HealthResponse",
    "ErrorDetail",
    "ErrorResponse",
]
