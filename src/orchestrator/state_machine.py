"""State Machine for orchestrator workflow management.

This module provides the core state machine logic for tracking and transitioning
workflow states. States are persisted to .plans/{issue_number}/state.json.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from orchestrator.errors import (
    InvalidStateTransition,
    StateFileCorruptedError,
    WorkflowNotFoundError,
)
from orchestrator.logger import logger
from orchestrator.models import (
    OrchestratorState,
    StateTransition,
    WorkflowState,
)

# T024: State transition table
# Maps (current_state, event) -> next_state
TRANSITIONS: dict[tuple[WorkflowState, str], WorkflowState] = {
    (WorkflowState.IDLE, "phase_1_start"): WorkflowState.PHASE_1,
    (WorkflowState.PHASE_1, "phase_1_complete"): WorkflowState.PHASE_2,
    (WorkflowState.PHASE_2, "phase_2_complete"): WorkflowState.GATE_1,
    (WorkflowState.GATE_1, "approval_received"): WorkflowState.DONE,
}


class StateMachine:
    """Manages workflow state transitions and persistence.

    The StateMachine tracks workflow states for issues and ensures
    only valid forward transitions occur. State is persisted to
    .plans/{issue_number}/state.json.

    Attributes:
        _plans_base: Base path for .plans directory.

    Example:
        >>> sm = StateMachine(Path("/repo"))
        >>> state = sm.create_state(123, "add-auth")
        >>> sm.transition(123, "phase_1_start")
        StateTransition(from_state=IDLE, to_state=PHASE_1, ...)
    """

    def __init__(self, repo_path: Path) -> None:
        """Initialize the state machine.

        Args:
            repo_path: Path to the repository root. The .plans directory
                will be created at repo_path/.plans/.
        """
        self._plans_base = repo_path / ".plans"

    def _get_state_path(self, issue_number: int) -> Path:
        """Get the path to state file for an issue.

        Args:
            issue_number: GitHub issue number.

        Returns:
            Path to the state.json file.
        """
        return self._plans_base / str(issue_number) / "state.json"

    def get_state(self, issue_number: int) -> OrchestratorState | None:
        """Get current workflow state for an issue.

        Args:
            issue_number: GitHub issue number.

        Returns:
            Current OrchestratorState or None if no workflow exists.

        Raises:
            StateFileCorruptedError: If state file is malformed.
        """
        state_path = self._get_state_path(issue_number)
        if not state_path.exists():
            return None

        try:
            data = json.loads(state_path.read_text())
            # Convert worktree_path string back to Path if present
            if data.get("worktree_path"):
                data["worktree_path"] = Path(data["worktree_path"])
            return OrchestratorState.model_validate(data)
        except json.JSONDecodeError as e:
            logger.error(
                f"Corrupted state file for issue {issue_number}",
                extra={"context": {"issue_number": issue_number, "error": str(e)}},
            )
            raise StateFileCorruptedError(
                f"State file for issue {issue_number} is corrupted: {e}"
            ) from e
        except Exception as e:
            logger.error(
                f"Error loading state for issue {issue_number}",
                extra={"context": {"issue_number": issue_number, "error": str(e)}},
            )
            raise StateFileCorruptedError(
                f"Failed to load state for issue {issue_number}: {e}"
            ) from e

    def create_state(
        self,
        issue_number: int,
        feature_name: str,
    ) -> OrchestratorState:
        """Create a new workflow state for an issue.

        Args:
            issue_number: GitHub issue number.
            feature_name: Feature slug (kebab-case).

        Returns:
            Newly created OrchestratorState in IDLE state.
        """
        now = datetime.now(UTC)
        state = OrchestratorState(
            issue_number=issue_number,
            current_state=WorkflowState.IDLE,
            feature_name=feature_name,
            created_at=now,
            updated_at=now,
        )
        self._save_state(state)

        logger.info(
            f"Created workflow state for issue {issue_number}",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "feature_name": feature_name,
                    "state": state.current_state.value,
                }
            },
        )
        return state

    def transition(
        self,
        issue_number: int,
        event: str,
    ) -> StateTransition:
        """Transition workflow to next state.

        Args:
            issue_number: GitHub issue number.
            event: Event triggering the transition.

        Returns:
            StateTransition record of the change.

        Raises:
            WorkflowNotFoundError: If no workflow exists for issue.
            InvalidStateTransition: If transition not allowed.
        """
        state = self.get_state(issue_number)
        if state is None:
            raise WorkflowNotFoundError(f"No workflow found for issue {issue_number}")

        current_state = state.current_state
        transition_key = (current_state, event)

        if transition_key not in TRANSITIONS:
            # Check if it's an invalid event or invalid transition
            valid_events = [k[1] for k in TRANSITIONS.keys() if k[0] == current_state]
            if valid_events:
                raise InvalidStateTransition(
                    f"Cannot transition from {current_state.value} with event '{event}'. "
                    f"Valid events: {valid_events}"
                )
            else:
                raise InvalidStateTransition(
                    f"No transitions allowed from {current_state.value} (terminal state)"
                )

        next_state = TRANSITIONS[transition_key]
        now = datetime.now(UTC)

        # Create transition record
        transition = StateTransition(
            from_state=current_state,
            to_state=next_state,
            trigger=event,
            timestamp=now,
        )

        # Update state
        state.current_state = next_state
        state.updated_at = now
        state.history.append(transition)

        self._save_state(state)

        logger.info(
            f"Workflow transitioned for issue {issue_number}",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "from_state": current_state.value,
                    "to_state": next_state.value,
                    "event": event,
                }
            },
        )

        return transition

    def _save_state(self, state: OrchestratorState) -> None:
        """Save state to disk.

        Args:
            state: The OrchestratorState to persist.
        """
        state_path = self._get_state_path(state.issue_number)
        state_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and handle Path serialization
        data = state.model_dump(mode="json")
        if state.worktree_path:
            data["worktree_path"] = str(state.worktree_path)

        state_path.write_text(json.dumps(data, indent=2, default=str))

    def _load_state(self, issue_number: int) -> OrchestratorState | None:
        """Load state from disk.

        This is an alias for get_state() for internal use.

        Args:
            issue_number: GitHub issue number.

        Returns:
            OrchestratorState or None if not found.
        """
        return self.get_state(issue_number)
