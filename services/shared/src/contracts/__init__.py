"""Shared contracts for Farmer Code services.

This package provides Pydantic models and HTTP clients for service-to-service
communication between Orchestrator, Agent Hub, and Agent Services.
"""

from contracts.models import (
    # Workflow models
    CreateWorkflowRequest,
    WorkflowResponse,
    WorkflowStatus,
    WorkflowType,
    # Session models
    Message,
    MessageRole,
    Session,
    SessionStatus,
    # Escalation models
    Escalation,
    EscalationStatus,
    HumanAction,
    # Agent models
    InvokeRequest,
    InvokeResponse,
)
from contracts.clients import (
    AgentClient,
    AgentHubClient,
    OrchestratorClient,
)
from contracts.config import ServiceConfig

__all__ = [
    # Workflow
    "WorkflowType",
    "WorkflowStatus",
    "CreateWorkflowRequest",
    "WorkflowResponse",
    # Session
    "SessionStatus",
    "Session",
    "Message",
    "MessageRole",
    # Escalation
    "EscalationStatus",
    "HumanAction",
    "Escalation",
    # Agent
    "InvokeRequest",
    "InvokeResponse",
    # Clients
    "AgentClient",
    "AgentHubClient",
    "OrchestratorClient",
    # Config
    "ServiceConfig",
]
