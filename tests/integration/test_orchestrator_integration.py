"""Integration tests for the Orchestrator (User Stories 2 & 4).

Tests cover:
- T031: Integration test for execute_phase_1()
- T059: Integration test for execute_phase_2()
"""

from unittest.mock import MagicMock

import pytest

from orchestrator import (
    Phase1Request,
    WorkflowState,
)


class TestPhase1Integration:
    """T031: Integration tests for execute_phase_1()."""

    @pytest.mark.integration
    def test_phase_1_creates_complete_workflow(
        self,
        orchestrator_service,
        mock_github,
        mock_worktree,
        tmp_path,
    ):
        """Integration test: Phase 1 creates issue, branch, worktree, .plans."""
        # Setup mocks
        issue_mock = MagicMock()
        issue_mock.number = 123
        issue_mock.title = "Add user authentication"
        issue_mock.html_url = "https://github.com/org/repo/issues/123"
        mock_github.create_issue.return_value = issue_mock

        branch_mock = MagicMock()
        branch_mock.name = "123-add-auth"
        branch_mock.sha = "abc123"
        mock_github.create_branch.return_value = branch_mock

        worktree_mock = MagicMock()
        worktree_mock.path = tmp_path / "worktree-123"
        worktree_mock.branch = "123-add-auth"
        worktree_mock.issue_number = 123
        mock_worktree.create_worktree.return_value = worktree_mock

        # Execute Phase 1
        request = Phase1Request(
            feature_description="Add user authentication with OAuth2",
            labels=["enhancement", "security"],
        )
        result = orchestrator_service.execute_phase_1(request)

        # Verify result
        assert result.success
        assert result.phase == "phase_1"
        assert "issue" in result.steps_completed
        assert "branch" in result.steps_completed
        assert "worktree" in result.steps_completed
        assert "plans" in result.steps_completed
        assert any("issue#123" in a for a in result.artifacts_created)

    @pytest.mark.integration
    def test_phase_1_updates_state(
        self,
        orchestrator_service,
        mock_github,
        mock_worktree,
        tmp_path,
    ):
        """Integration test: Phase 1 correctly updates workflow state."""
        issue_mock = MagicMock()
        issue_mock.number = 123
        mock_github.create_issue.return_value = issue_mock

        branch_mock = MagicMock()
        branch_mock.name = "123-add-auth"
        mock_github.create_branch.return_value = branch_mock

        worktree_mock = MagicMock()
        worktree_mock.path = tmp_path / "worktree"
        worktree_mock.branch = "123-add-auth"
        mock_worktree.create_worktree.return_value = worktree_mock

        request = Phase1Request(feature_description="Add feature")
        orchestrator_service.execute_phase_1(request)

        # Verify state was updated
        state = orchestrator_service.get_state(123)
        assert state is not None
        assert state.current_state == WorkflowState.PHASE_2
        assert state.phase1_steps == ["issue", "branch", "worktree", "plans"]

    @pytest.mark.integration
    def test_phase_1_handles_partial_failure(
        self,
        orchestrator_service,
        mock_github,
        mock_worktree,
        tmp_path,
    ):
        """Integration test: Phase 1 can resume after partial failure."""
        from orchestrator import BranchCreationError

        # First attempt: fail at branch creation
        issue_mock = MagicMock()
        issue_mock.number = 123
        mock_github.create_issue.return_value = issue_mock
        mock_github.create_branch.side_effect = Exception("Rate limited")

        request = Phase1Request(feature_description="Add feature")

        with pytest.raises(BranchCreationError):
            orchestrator_service.execute_phase_1(request)

        # Reset and retry
        mock_github.create_branch.side_effect = None
        branch_mock = MagicMock()
        branch_mock.name = "123-add-feature"
        mock_github.create_branch.return_value = branch_mock

        worktree_mock = MagicMock()
        worktree_mock.path = tmp_path / "worktree"
        worktree_mock.branch = "123-add-feature"
        mock_worktree.create_worktree.return_value = worktree_mock

        # Should resume from branch step
        result = orchestrator_service.execute_phase_1(request)
        assert result.success


class TestPhase2Integration:
    """T059: Integration tests for execute_phase_2() (placeholder for Phase 6)."""

    @pytest.mark.integration
    def test_phase_2_dispatches_agent(self):
        """Integration test: Phase 2 dispatches agent correctly."""
        # This test will be fully implemented in Phase 6
        pytest.skip("Phase 2 implementation in Phase 6")


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
