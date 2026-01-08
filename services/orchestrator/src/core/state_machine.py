"""Workflow state machine for Orchestrator service.

Manages workflow state transitions per data-model.md state machine:

PENDING -> IN_PROGRESS (workflow started)
IN_PROGRESS -> WAITING_APPROVAL (agent complete, gate reached)
WAITING_APPROVAL -> IN_PROGRESS (human approved, next phase)
WAITING_APPROVAL -> COMPLETED (all phases done)
Any state -> FAILED (error occurred)
"""

import re
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from src.db.models import Workflow, WorkflowHistory, WorkflowStatus, WorkflowType


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        from_status: str,
        to_status: str,
        trigger: str,
    ) -> None:
        self.from_status = from_status
        self.to_status = to_status
        self.trigger = trigger
        super().__init__(f"Invalid transition from {from_status} to {to_status} via {trigger}")


class WorkflowNotFoundError(Exception):
    """Raised when a workflow is not found."""

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"Workflow {workflow_id} not found")


# Valid state transitions
VALID_TRANSITIONS: dict[str, dict[str, list[str]]] = {
    WorkflowStatus.PENDING.value: {
        "start": [WorkflowStatus.IN_PROGRESS.value],
    },
    WorkflowStatus.IN_PROGRESS.value: {
        "agent_complete": [WorkflowStatus.WAITING_APPROVAL.value],
        "error": [WorkflowStatus.FAILED.value],
    },
    WorkflowStatus.WAITING_APPROVAL.value: {
        "human_approved": [
            WorkflowStatus.IN_PROGRESS.value,  # Next phase
            WorkflowStatus.COMPLETED.value,  # If last phase
        ],
        "human_rejected": [
            WorkflowStatus.IN_PROGRESS.value,  # Rework
            WorkflowStatus.FAILED.value,  # Abort
        ],
        "error": [WorkflowStatus.FAILED.value],
    },
    # Terminal states - no transitions allowed
    WorkflowStatus.COMPLETED.value: {},
    WorkflowStatus.FAILED.value: {},
}


class WorkflowStateMachine:
    """Manages workflow state transitions."""

    def __init__(self, db: Session) -> None:
        """Initialize with database session."""
        self.db = db
        self._feature_counter = 0

    def create_workflow(
        self,
        workflow_type: str,
        feature_description: str,
        context: dict[str, Any] | None = None,
    ) -> Workflow:
        """Create a new workflow and start it.

        Args:
            workflow_type: Type of workflow (specify, plan, tasks, implement)
            feature_description: Description of the feature
            context: Optional additional context

        Returns:
            Created workflow
        """
        # Validate workflow type
        if workflow_type not in [wt.value for wt in WorkflowType]:
            raise ValueError(f"Invalid workflow type: {workflow_type}")

        # Generate feature ID from description
        feature_id = self._generate_feature_id(feature_description)

        # Create workflow
        workflow = Workflow(
            id=str(uuid4()),
            workflow_type=workflow_type,
            status=WorkflowStatus.PENDING.value,
            feature_id=feature_id,
            feature_description=feature_description,
            current_phase="phase_1",
        )
        workflow.set_context(context)

        self.db.add(workflow)

        # Immediately transition to in_progress
        self._transition(
            workflow,
            WorkflowStatus.IN_PROGRESS.value,
            "start",
        )

        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow UUID

        Returns:
            Workflow instance

        Raises:
            WorkflowNotFoundError: If workflow not found
        """
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)
        return workflow

    def advance_workflow(
        self,
        workflow_id: str,
        trigger: str,
        phase_result: dict[str, Any] | None = None,
    ) -> Workflow:
        """Advance workflow to next state.

        Args:
            workflow_id: Workflow UUID
            trigger: What triggered the transition (agent_complete, human_approved, human_rejected)
            phase_result: Optional result from completed phase

        Returns:
            Updated workflow

        Raises:
            WorkflowNotFoundError: If workflow not found
            InvalidStateTransitionError: If transition is not allowed
        """
        workflow = self.get_workflow(workflow_id)

        # Determine target state based on trigger
        target_status = self._determine_next_status(
            workflow.status,
            trigger,
            workflow.current_phase,
        )

        # Perform transition
        self._transition(workflow, target_status, trigger, phase_result)

        self.db.commit()
        self.db.refresh(workflow)

        return workflow

    def _transition(
        self,
        workflow: Workflow,
        to_status: str,
        trigger: str,
        phase_result: dict[str, Any] | None = None,
    ) -> None:
        """Perform state transition with history recording.

        Args:
            workflow: Workflow to transition
            to_status: Target status
            trigger: What triggered the transition
            phase_result: Optional result from phase
        """
        from_status = workflow.status

        # Validate transition
        if not self._is_valid_transition(from_status, to_status, trigger):
            raise InvalidStateTransitionError(from_status, to_status, trigger)

        # Record history
        history = WorkflowHistory(
            id=str(uuid4()),
            workflow_id=workflow.id,
            from_status=from_status,
            to_status=to_status,
            trigger=trigger,
        )
        history.set_metadata(phase_result)
        self.db.add(history)

        # Update workflow
        workflow.status = to_status
        workflow.updated_at = datetime.utcnow()

        # Update phase if moving to next phase
        if (
            from_status == WorkflowStatus.WAITING_APPROVAL.value
            and to_status == WorkflowStatus.IN_PROGRESS.value
        ):
            workflow.current_phase = self._get_next_phase(workflow.current_phase)

        # Mark completed
        if to_status == WorkflowStatus.COMPLETED.value:
            workflow.completed_at = datetime.utcnow()
            if phase_result:
                workflow.set_result(phase_result)

        # Mark failed
        if to_status == WorkflowStatus.FAILED.value:
            workflow.error = phase_result.get("error") if phase_result else "Unknown error"

    def _is_valid_transition(
        self,
        from_status: str,
        to_status: str,
        trigger: str,
    ) -> bool:
        """Check if transition is valid.

        Args:
            from_status: Current status
            to_status: Target status
            trigger: Transition trigger

        Returns:
            True if transition is valid
        """
        transitions = VALID_TRANSITIONS.get(from_status, {})
        allowed_targets = transitions.get(trigger, [])
        return to_status in allowed_targets

    def _determine_next_status(
        self,
        current_status: str,
        trigger: str,
        current_phase: str | None,
    ) -> str:
        """Determine the next status based on trigger and context.

        Args:
            current_status: Current workflow status
            trigger: What triggered the transition
            current_phase: Current phase of workflow

        Returns:
            Next status

        Raises:
            InvalidStateTransitionError: If trigger is not valid for current state
        """
        transitions = VALID_TRANSITIONS.get(current_status, {})
        allowed_targets = transitions.get(trigger, [])

        if not allowed_targets:
            raise InvalidStateTransitionError(current_status, "unknown", trigger)

        # For human_approved, check if this is the last phase
        if trigger == "human_approved":
            if self._is_last_phase(current_phase):
                return WorkflowStatus.COMPLETED.value
            return WorkflowStatus.IN_PROGRESS.value

        # For human_rejected, go back to in_progress for rework
        if trigger == "human_rejected":
            return WorkflowStatus.IN_PROGRESS.value

        # Default to first allowed target
        return allowed_targets[0]

    def _generate_feature_id(self, description: str) -> str:
        """Generate feature ID from description.

        Format: XXX-slug-from-description
        Example: "Add user authentication" -> "009-add-user-auth"
        """
        # Get next feature number
        max_num = self.db.query(Workflow).with_entities(Workflow.feature_id).all()
        existing_nums = []
        for (fid,) in max_num:
            if fid and fid[:3].isdigit():
                existing_nums.append(int(fid[:3]))

        next_num = max(existing_nums, default=0) + 1

        # Create slug from description
        slug = description.lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug)
        slug = slug[:30].rstrip("-")

        return f"{next_num:03d}-{slug}"

    def _get_next_phase(self, current_phase: str | None) -> str:
        """Get the next phase after current.

        Args:
            current_phase: Current phase (e.g., "phase_1")

        Returns:
            Next phase (e.g., "phase_2")
        """
        if not current_phase:
            return "phase_1"

        if current_phase.startswith("phase_"):
            num = int(current_phase.split("_")[1])
            return f"phase_{num + 1}"

        return "phase_1"

    def _is_last_phase(self, current_phase: str | None) -> bool:
        """Check if current phase is the last phase.

        For now, assume phase_2 is the last phase (specify workflow).
        More complex workflows would have more phases.
        """
        if not current_phase:
            return False

        # For simplicity, phase_2 is the last phase
        # In production, this would be workflow-type specific
        return current_phase == "phase_2"
