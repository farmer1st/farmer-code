"""Unit tests for the State Machine (User Story 1).

Tests cover:
- T020: WorkflowState transitions
- T021: State persistence (save/load)
- T022: Invalid transition handling
- T023: State history tracking
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from orchestrator import (
    InvalidStateTransition,
    StateFileCorruptedError,
    WorkflowNotFoundError,
    WorkflowState,
)


class TestWorkflowStateTransitions:
    """T020: Unit tests for WorkflowState transitions."""

    def test_valid_transition_idle_to_phase_1(self, state_machine, tmp_plans_dir):
        """Test transition from IDLE to PHASE_1."""
        # Create initial state
        state = state_machine.create_state(
            issue_number=123,
            feature_name="test-feature",
        )
        assert state.current_state == WorkflowState.IDLE

        # Transition to PHASE_1
        result = state_machine.transition(123, "phase_1_start")
        assert result.to_state == WorkflowState.PHASE_1
        assert result.from_state == WorkflowState.IDLE
        assert result.trigger == "phase_1_start"

    def test_valid_transition_phase_1_to_phase_2(self, state_machine):
        """Test transition from PHASE_1 to PHASE_2."""
        state_machine.create_state(
            issue_number=123,
            feature_name="test-feature",
        )
        state_machine.transition(123, "phase_1_start")

        result = state_machine.transition(123, "phase_1_complete")
        assert result.to_state == WorkflowState.PHASE_2
        assert result.from_state == WorkflowState.PHASE_1

    def test_valid_transition_phase_2_to_gate_1(self, state_machine):
        """Test transition from PHASE_2 to GATE_1."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")
        state_machine.transition(123, "phase_1_complete")

        result = state_machine.transition(123, "phase_2_complete")
        assert result.to_state == WorkflowState.GATE_1
        assert result.from_state == WorkflowState.PHASE_2

    def test_valid_transition_gate_1_to_done(self, state_machine):
        """Test transition from GATE_1 to DONE."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")
        state_machine.transition(123, "phase_1_complete")
        state_machine.transition(123, "phase_2_complete")

        result = state_machine.transition(123, "approval_received")
        assert result.to_state == WorkflowState.DONE
        assert result.from_state == WorkflowState.GATE_1

    def test_full_workflow_transition(self, state_machine):
        """Test complete workflow from IDLE to DONE."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")

        # Progress through all states
        state_machine.transition(123, "phase_1_start")
        state_machine.transition(123, "phase_1_complete")
        state_machine.transition(123, "phase_2_complete")
        state_machine.transition(123, "approval_received")

        state = state_machine.get_state(123)
        assert state.current_state == WorkflowState.DONE


class TestStatePersistence:
    """T021: Unit tests for state persistence (save/load)."""

    def test_state_persists_after_transition(self, state_machine, tmp_plans_dir):
        """State should be saved to disk after each transition."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")

        # Verify state file exists
        state_file = tmp_plans_dir / "123" / "state.json"
        assert state_file.exists()

    def test_state_loads_from_disk(self, state_machine, tmp_plans_dir):
        """State should be loadable from persisted file."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")

        # Create a new state machine instance and load state
        from orchestrator.state_machine import StateMachine

        new_sm = StateMachine(tmp_plans_dir.parent)
        state = new_sm.get_state(123)

        assert state is not None
        assert state.current_state == WorkflowState.PHASE_1
        assert state.feature_name == "test-feature"

    def test_state_preserves_all_fields(self, state_machine):
        """All state fields should survive save/load cycle."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")

        # Update some fields
        state = state_machine.get_state(123)
        state.branch_name = "123-test-feature"
        state.worktree_path = Path("/tmp/worktree")
        state.phase1_steps = ["issue", "branch"]
        state_machine._save_state(state)

        # Reload and verify
        from orchestrator.state_machine import StateMachine

        new_sm = StateMachine(state_machine._plans_base.parent)
        loaded = new_sm.get_state(123)

        assert loaded.branch_name == "123-test-feature"
        assert loaded.phase1_steps == ["issue", "branch"]

    def test_state_file_location(self, state_machine, tmp_plans_dir):
        """State should be saved to .plans/{issue_number}/state.json."""
        state_machine.create_state(issue_number=456, feature_name="another-feature")

        expected_path = tmp_plans_dir / "456" / "state.json"
        assert expected_path.exists()


class TestInvalidTransitionHandling:
    """T022: Unit tests for invalid transition handling."""

    def test_backward_transition_rejected(self, state_machine):
        """Backward transitions should raise InvalidStateTransition."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")
        state_machine.transition(123, "phase_1_complete")

        # Try to go backwards
        with pytest.raises(InvalidStateTransition) as exc_info:
            state_machine.transition(123, "phase_1_start")

        assert "phase_2" in str(exc_info.value)
        assert exc_info.value.error_code == "INVALID_TRANSITION"

    def test_skip_state_rejected(self, state_machine):
        """Skipping states should raise InvalidStateTransition."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")

        # Try to skip from IDLE to PHASE_2
        with pytest.raises(InvalidStateTransition):
            state_machine.transition(123, "phase_1_complete")

    def test_transition_from_done_rejected(self, state_machine):
        """No transitions allowed from DONE state."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")
        state_machine.transition(123, "phase_1_complete")
        state_machine.transition(123, "phase_2_complete")
        state_machine.transition(123, "approval_received")

        # Try any transition from DONE
        with pytest.raises(InvalidStateTransition):
            state_machine.transition(123, "phase_1_start")

    def test_invalid_event_rejected(self, state_machine):
        """Invalid event names should raise InvalidStateTransition."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")

        with pytest.raises(InvalidStateTransition):
            state_machine.transition(123, "invalid_event")

    def test_transition_nonexistent_workflow(self, state_machine):
        """Transitioning nonexistent workflow raises WorkflowNotFoundError."""
        with pytest.raises(WorkflowNotFoundError):
            state_machine.transition(999, "phase_1_start")


class TestStateHistoryTracking:
    """T023: Unit tests for state history tracking."""

    def test_history_records_transitions(self, state_machine):
        """Each transition should be recorded in history."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")
        state_machine.transition(123, "phase_1_complete")

        state = state_machine.get_state(123)
        assert len(state.history) == 2

    def test_history_preserves_order(self, state_machine):
        """History should preserve chronological order."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")
        state_machine.transition(123, "phase_1_complete")
        state_machine.transition(123, "phase_2_complete")

        state = state_machine.get_state(123)

        assert state.history[0].trigger == "phase_1_start"
        assert state.history[1].trigger == "phase_1_complete"
        assert state.history[2].trigger == "phase_2_complete"

    def test_history_records_timestamps(self, state_machine):
        """Each history entry should have a timestamp."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        before = datetime.now(UTC)
        state_machine.transition(123, "phase_1_start")
        after = datetime.now(UTC)

        state = state_machine.get_state(123)
        transition = state.history[0]

        assert before <= transition.timestamp <= after

    def test_history_immutable(self, state_machine):
        """History entries should be immutable (frozen)."""
        state_machine.create_state(issue_number=123, feature_name="test-feature")
        state_machine.transition(123, "phase_1_start")

        state = state_machine.get_state(123)
        transition = state.history[0]

        from pydantic import ValidationError

        with pytest.raises(ValidationError):  # Frozen models raise ValidationError on mutation
            transition.trigger = "modified"


class TestCorruptedStateHandling:
    """Additional tests for edge cases."""

    def test_corrupted_state_file_raises_error(self, state_machine, tmp_plans_dir):
        """Corrupted state file should raise StateFileCorruptedError."""
        # Create a valid state
        state_machine.create_state(issue_number=123, feature_name="test-feature")

        # Corrupt the state file
        state_file = tmp_plans_dir / "123" / "state.json"
        state_file.write_text("invalid json {{{")

        # Loading should raise error
        with pytest.raises(StateFileCorruptedError):
            state_machine.get_state(123)

    def test_missing_state_returns_none(self, state_machine):
        """Missing state file should return None, not error."""
        result = state_machine.get_state(999)
        assert result is None


# Fixtures


@pytest.fixture
def tmp_plans_dir(tmp_path):
    """Create a temporary .plans directory."""
    plans_dir = tmp_path / ".plans"
    plans_dir.mkdir()
    return plans_dir


@pytest.fixture
def state_machine(tmp_plans_dir):
    """Create a StateMachine with temporary storage."""
    from orchestrator.state_machine import StateMachine

    return StateMachine(tmp_plans_dir.parent)
