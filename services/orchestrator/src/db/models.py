"""SQLAlchemy models for Orchestrator service.

Defines Workflow and WorkflowHistory models per data-model.md.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class WorkflowType(str, Enum):
    """Workflow type enumeration."""

    SPECIFY = "specify"
    PLAN = "plan"
    TASKS = "tasks"
    IMPLEMENT = "implement"


class WorkflowStatus(str, Enum):
    """Workflow status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class Workflow(Base):
    """Workflow entity representing a SpecKit workflow execution."""

    __tablename__ = "workflows"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workflow_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default=WorkflowStatus.PENDING.value)
    feature_id = Column(String, nullable=False)
    feature_description = Column(Text, nullable=False)
    current_phase = Column(String, nullable=True)
    context = Column(Text, nullable=True)  # JSON string
    result = Column(Text, nullable=True)  # JSON string
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationship to history
    history = relationship(
        "WorkflowHistory",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

    def set_context(self, context: dict[str, Any] | None) -> None:
        """Set context as JSON string."""
        self.context = json.dumps(context) if context else None

    def get_context(self) -> dict[str, Any] | None:
        """Get context as dict."""
        return json.loads(self.context) if self.context else None

    def set_result(self, result: dict[str, Any] | None) -> None:
        """Set result as JSON string."""
        self.result = json.dumps(result) if result else None

    def get_result(self) -> dict[str, Any] | None:
        """Get result as dict."""
        return json.loads(self.result) if self.result else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response dict."""
        return {
            "id": self.id,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "feature_id": self.feature_id,
            "current_phase": self.current_phase,
            "result": self.get_result(),
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


class WorkflowHistory(Base):
    """Workflow history entry tracking state transitions."""

    __tablename__ = "workflow_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    from_status = Column(String, nullable=False)
    to_status = Column(String, nullable=False)
    trigger = Column(String, nullable=False)
    transition_metadata = Column(Text, nullable=True)  # JSON string (renamed from 'metadata' which is reserved)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to workflow
    workflow = relationship("Workflow", back_populates="history")

    def set_metadata(self, data: dict[str, Any] | None) -> None:
        """Set transition metadata as JSON string."""
        self.transition_metadata = json.dumps(data) if data else None

    def get_metadata(self) -> dict[str, Any] | None:
        """Get transition metadata as dict."""
        return json.loads(self.transition_metadata) if self.transition_metadata else None
