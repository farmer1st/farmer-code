"""Unit tests for Label Synchronization (User Story 5).

Tests cover:
- T068: Label mapping
- T069: sync_labels()
- T070: Label sync error handling
"""

from unittest.mock import MagicMock

import pytest

from orchestrator import WorkflowState


class TestLabelMapping:
    """T068: Unit tests for label mapping."""

    def test_state_to_label_mapping(self):
        """Each state should map to a status label."""
        from orchestrator.label_sync import STATE_LABEL_MAP

        expected = {
            WorkflowState.IDLE: "status:new",
            WorkflowState.PHASE_1: "status:phase-1",
            WorkflowState.PHASE_2: "status:phase-2",
            WorkflowState.GATE_1: "status:awaiting-approval",
            WorkflowState.DONE: "status:done",
        }

        for state, label in expected.items():
            assert STATE_LABEL_MAP[state] == label, f"State {state} should map to {label}"

    def test_all_states_have_labels(self):
        """All workflow states should have a label mapping."""
        from orchestrator.label_sync import STATE_LABEL_MAP

        for state in WorkflowState:
            assert state in STATE_LABEL_MAP, f"State {state} missing from label map"

    def test_status_labels_have_prefix(self):
        """All status labels should have 'status:' prefix."""
        from orchestrator.label_sync import STATE_LABEL_MAP

        for label in STATE_LABEL_MAP.values():
            assert label.startswith("status:"), f"Label {label} missing 'status:' prefix"


class TestSyncLabels:
    """T069: Unit tests for sync_labels()."""

    def test_sync_labels_adds_current_state_label(self, label_sync, mock_github):
        """Should add label for current state."""
        result = label_sync.sync_labels(
            issue_number=123,
            current_state=WorkflowState.PHASE_2,
        )

        assert result.status.value == "success"
        mock_github.add_label.assert_called()

    def test_sync_labels_removes_old_status_labels(self, label_sync, mock_github):
        """Should remove old status labels before adding new one."""
        # Setup: issue has old status labels
        mock_label = MagicMock()
        mock_label.name = "status:phase-1"
        mock_github.get_issue_labels.return_value = [mock_label]

        label_sync.sync_labels(
            issue_number=123,
            current_state=WorkflowState.PHASE_2,
        )

        # Should remove old label
        mock_github.remove_label.assert_called_once_with(123, "status:phase-1")
        # Should add new label
        mock_github.add_label.assert_called_once_with(123, "status:phase-2")

    def test_sync_labels_preserves_non_status_labels(self, label_sync, mock_github):
        """Should not remove non-status labels."""
        # Create mock labels with proper name attributes
        label1 = MagicMock()
        label1.name = "enhancement"
        label2 = MagicMock()
        label2.name = "priority:high"
        label3 = MagicMock()
        label3.name = "status:phase-1"

        mock_github.get_issue_labels.return_value = [label1, label2, label3]

        label_sync.sync_labels(
            issue_number=123,
            current_state=WorkflowState.PHASE_2,
        )

        # Should only remove status label
        mock_github.remove_label.assert_called_once_with(123, "status:phase-1")

    def test_sync_labels_returns_success(self, label_sync, mock_github):
        """Should return success result."""
        result = label_sync.sync_labels(
            issue_number=123,
            current_state=WorkflowState.DONE,
        )

        assert result.status.value == "success"


class TestLabelSyncErrorHandling:
    """T070: Unit tests for label sync error handling."""

    def test_handles_add_label_error(self, label_sync, mock_github):
        """Should handle error when adding label fails."""
        mock_github.add_label.side_effect = Exception("API error")

        result = label_sync.sync_labels(
            issue_number=123,
            current_state=WorkflowState.PHASE_2,
        )

        # Should return failure but not raise
        assert result.status.value == "failure"

    def test_handles_remove_label_error(self, label_sync, mock_github):
        """Should handle error when removing label fails."""
        mock_label = MagicMock()
        mock_label.name = "status:phase-1"
        mock_github.get_issue_labels.return_value = [mock_label]
        mock_github.remove_label.side_effect = Exception("API error")

        label_sync.sync_labels(
            issue_number=123,
            current_state=WorkflowState.PHASE_2,
        )

        # Should continue and try to add new label
        mock_github.add_label.assert_called_once()

    def test_handles_get_labels_error(self, label_sync, mock_github):
        """Should handle error when getting labels fails."""
        mock_github.get_issue_labels.side_effect = Exception("API error")

        label_sync.sync_labels(
            issue_number=123,
            current_state=WorkflowState.PHASE_2,
        )

        # Should still try to add new label
        mock_github.add_label.assert_called()


# Fixtures


@pytest.fixture
def mock_github():
    """Create a mock GitHub service."""
    mock = MagicMock()
    mock.get_issue_labels.return_value = []
    return mock


@pytest.fixture
def label_sync(mock_github):
    """Create a LabelSync with mocked GitHub service."""
    from orchestrator.label_sync import LabelSync

    return LabelSync(github_service=mock_github)
