"""Contract tests for OrchestratorService (Phase 8).

Tests cover:
- T077: Contract test for OrchestratorService
"""

from unittest.mock import MagicMock

import pytest

from orchestrator import (
    Phase1Request,
)


class TestOrchestratorServiceContract:
    """T077: Contract tests for OrchestratorService."""

    @pytest.mark.contract
    def test_service_has_get_state_method(self, orchestrator_service):
        """Service should have get_state method."""
        assert hasattr(orchestrator_service, "get_state")
        assert callable(orchestrator_service.get_state)

    @pytest.mark.contract
    def test_service_has_transition_method(self, orchestrator_service):
        """Service should have transition method."""
        assert hasattr(orchestrator_service, "transition")
        assert callable(orchestrator_service.transition)

    @pytest.mark.contract
    def test_service_has_execute_phase_1_method(self, orchestrator_service):
        """Service should have execute_phase_1 method."""
        assert hasattr(orchestrator_service, "execute_phase_1")
        assert callable(orchestrator_service.execute_phase_1)

    @pytest.mark.contract
    def test_service_has_execute_phase_2_method(self, orchestrator_service):
        """Service should have execute_phase_2 method."""
        assert hasattr(orchestrator_service, "execute_phase_2")
        assert callable(orchestrator_service.execute_phase_2)

    @pytest.mark.contract
    def test_service_has_poll_for_signal_method(self, orchestrator_service):
        """Service should have poll_for_signal method."""
        assert hasattr(orchestrator_service, "poll_for_signal")
        assert callable(orchestrator_service.poll_for_signal)

    @pytest.mark.contract
    def test_service_has_sync_labels_method(self, orchestrator_service):
        """Service should have sync_labels method."""
        assert hasattr(orchestrator_service, "sync_labels")
        assert callable(orchestrator_service.sync_labels)

    @pytest.mark.contract
    def test_get_state_returns_none_for_unknown_issue(self, orchestrator_service):
        """get_state should return None for unknown issue."""
        result = orchestrator_service.get_state(99999)
        assert result is None

    @pytest.mark.contract
    def test_execute_phase_1_returns_phase_result(
        self,
        orchestrator_service,
        mock_github,
        mock_worktree,
        tmp_path,
    ):
        """execute_phase_1 should return PhaseResult."""
        # Setup mocks
        issue_mock = MagicMock()
        issue_mock.number = 123
        issue_mock.title = "Test"
        mock_github.create_issue.return_value = issue_mock

        branch_mock = MagicMock()
        branch_mock.name = "123-test"
        mock_github.create_branch.return_value = branch_mock

        worktree_mock = MagicMock()
        worktree_mock.path = tmp_path / "worktree"
        worktree_mock.branch = "123-test"
        mock_worktree.create_worktree.return_value = worktree_mock
        worktree_mock.path.mkdir(parents=True, exist_ok=True)

        request = Phase1Request(feature_description="Test feature")
        result = orchestrator_service.execute_phase_1(request)

        assert result.success
        assert result.phase == "phase_1"

    @pytest.mark.contract
    def test_sync_labels_returns_operation_result(
        self,
        orchestrator_service,
        mock_github,
        tmp_path,
    ):
        """sync_labels should return OperationResult."""
        # Create state first
        from orchestrator.state_machine import StateMachine

        sm = StateMachine(tmp_path)
        sm.create_state(123, "test")

        # Setup mock
        mock_github.get_issue_labels.return_value = []

        result = orchestrator_service.sync_labels(123)
        assert hasattr(result, "status")


# Fixtures


@pytest.fixture
def mock_github():
    """Create a mock GitHub service."""
    return MagicMock()


@pytest.fixture
def mock_worktree():
    """Create a mock worktree service."""
    return MagicMock()


@pytest.fixture
def orchestrator_service(mock_github, mock_worktree, tmp_path):
    """Create an OrchestratorService with mocked dependencies."""
    from orchestrator.service import OrchestratorService

    return OrchestratorService(
        repo_path=tmp_path,
        github_service=mock_github,
        worktree_service=mock_worktree,
    )
