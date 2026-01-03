"""Unit tests for the Phase Executor (User Story 2).

Tests cover:
- T032: Phase 1 step execution
- T033: Resumable execution (skip completed steps)
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orchestrator import (
    Phase1Request,
    WorkflowState,
)


class TestPhase1StepExecution:
    """T032: Unit tests for Phase 1 step execution."""

    def test_create_issue_step(self, phase_executor, mock_github_service):
        """Test issue creation step."""
        mock_github_service.create_issue.return_value = MagicMock(
            number=123,
            title="Add user authentication",
        )

        result = phase_executor._create_issue(
            "Add user authentication feature",
            labels=["enhancement"],
        )

        assert result["number"] == 123
        mock_github_service.create_issue.assert_called_once()

    def test_create_branch_step(self, phase_executor, mock_github_service):
        """Test branch creation step."""
        mock_result = MagicMock()
        mock_result.name = "123-add-auth"
        mock_github_service.create_branch.return_value = mock_result

        result = phase_executor._create_branch(
            issue_number=123,
            feature_name="add-auth",
        )

        assert result["name"] == "123-add-auth"
        mock_github_service.create_branch.assert_called_once()

    def test_create_worktree_step(self, phase_executor, mock_worktree_service):
        """Test worktree creation step."""
        mock_worktree_service.create_worktree.return_value = MagicMock(
            path=Path("/tmp/repo-123-add-auth"),
            branch="123-add-auth",
        )

        result = phase_executor._create_worktree(
            issue_number=123,
            branch_name="123-add-auth",
        )

        assert "path" in result
        mock_worktree_service.create_worktree.assert_called_once()

    def test_initialize_plans_step(self, phase_executor, tmp_path):
        """Test .plans directory initialization step."""
        worktree_path = tmp_path / "worktree"
        worktree_path.mkdir()

        result = phase_executor._initialize_plans(
            issue_number=123,
            worktree_path=worktree_path,
        )

        plans_dir = worktree_path / ".plans" / "123"
        assert plans_dir.exists()
        assert (plans_dir / "state.json").exists() or result.get("initialized")

    def test_execute_phase_1_creates_all_artifacts(
        self,
        phase_executor,
        mock_github_service,
        mock_worktree_service,
        mock_state_machine,
        tmp_path,
    ):
        """Test execute_phase_1 creates issue, branch, worktree, and .plans."""
        issue_mock = MagicMock()
        issue_mock.number = 123
        issue_mock.title = "Add auth"
        mock_github_service.create_issue.return_value = issue_mock

        branch_mock = MagicMock()
        branch_mock.name = "123-add-auth"
        mock_github_service.create_branch.return_value = branch_mock

        worktree_mock = MagicMock()
        worktree_mock.path = tmp_path / "repo-123-add-auth"
        worktree_mock.branch = "123-add-auth"
        mock_worktree_service.create_worktree.return_value = worktree_mock
        # Create the directory so _initialize_plans works
        worktree_mock.path.mkdir(parents=True, exist_ok=True)

        request = Phase1Request(
            feature_description="Add user authentication",
            labels=["enhancement"],
        )

        result = phase_executor.execute_phase_1(request)

        assert result.success
        assert result.phase == "phase_1"
        assert len(result.steps_completed) == 4
        assert "issue" in result.steps_completed
        assert "branch" in result.steps_completed
        assert "worktree" in result.steps_completed
        assert "plans" in result.steps_completed


class TestResumableExecution:
    """T033: Unit tests for resumable execution (skip completed steps)."""

    def test_skip_completed_issue_step(
        self,
        phase_executor,
        mock_github_service,
        mock_state_machine,
    ):
        """Should skip issue creation if already completed."""
        # Setup: issue step already complete
        mock_state_machine.get_state.return_value = MagicMock(
            phase1_steps=["issue"],
            current_state=WorkflowState.PHASE_1,
        )

        request = Phase1Request(feature_description="Add auth")

        # When resuming, should not call create_issue
        with patch.object(phase_executor, "_create_issue") as mock_create:
            phase_executor._execute_phase_1_steps(
                request=request,
                state=mock_state_machine.get_state.return_value,
            )
            mock_create.assert_not_called()

    def test_resume_from_branch_step(
        self,
        phase_executor,
        mock_github_service,
        mock_worktree_service,
        mock_state_machine,
    ):
        """Should resume from branch step if issue completed."""
        mock_state_machine.get_state.return_value = MagicMock(
            phase1_steps=["issue"],
            issue_number=123,
            feature_name="add-auth",
            current_state=WorkflowState.PHASE_1,
        )
        mock_github_service.create_branch.return_value = MagicMock(name="123-add-auth")
        mock_worktree_service.create_worktree.return_value = MagicMock(
            path=Path("/tmp/worktree"),
            branch="123-add-auth",
        )

        request = Phase1Request(feature_description="Add auth")

        result = phase_executor._execute_phase_1_steps(
            request=request,
            state=mock_state_machine.get_state.return_value,
        )

        # Should have completed branch, worktree, and plans
        assert "branch" in result.steps_completed
        assert "issue" not in result.steps_completed  # Was skipped

    def test_resume_from_worktree_step(
        self,
        phase_executor,
        mock_worktree_service,
        mock_state_machine,
        tmp_path,
    ):
        """Should resume from worktree step if issue and branch completed."""
        mock_state_machine.get_state.return_value = MagicMock(
            phase1_steps=["issue", "branch"],
            issue_number=123,
            feature_name="add-auth",
            branch_name="123-add-auth",
            current_state=WorkflowState.PHASE_1,
        )
        mock_worktree_service.create_worktree.return_value = MagicMock(
            path=tmp_path / "worktree",
            branch="123-add-auth",
        )

        request = Phase1Request(feature_description="Add auth")

        result = phase_executor._execute_phase_1_steps(
            request=request,
            state=mock_state_machine.get_state.return_value,
        )

        # Should have completed worktree and plans
        assert "worktree" in result.steps_completed
        assert "plans" in result.steps_completed

    def test_already_complete_returns_success(
        self,
        phase_executor,
        mock_state_machine,
    ):
        """Phase already complete should return success with no new steps."""
        mock_state_machine.get_state.return_value = MagicMock(
            phase1_steps=["issue", "branch", "worktree", "plans"],
            current_state=WorkflowState.PHASE_2,
        )

        request = Phase1Request(feature_description="Add auth")

        result = phase_executor._execute_phase_1_steps(
            request=request,
            state=mock_state_machine.get_state.return_value,
        )

        assert result.success
        assert len(result.steps_completed) == 0  # Nothing new to do


class TestPhase1ErrorHandling:
    """Additional tests for error handling."""

    def test_issue_creation_failure(
        self,
        phase_executor,
        mock_github_service,
    ):
        """Should raise IssueCreationError on failure."""
        from orchestrator import IssueCreationError

        mock_github_service.create_issue.side_effect = Exception("API error")

        request = Phase1Request(feature_description="Add auth")

        with pytest.raises(IssueCreationError):
            phase_executor.execute_phase_1(request)

    def test_branch_creation_failure(
        self,
        phase_executor,
        mock_github_service,
    ):
        """Should raise BranchCreationError on failure."""
        from orchestrator import BranchCreationError

        issue_mock = MagicMock()
        issue_mock.number = 123
        issue_mock.title = "Test"
        mock_github_service.create_issue.return_value = issue_mock
        mock_github_service.create_branch.side_effect = Exception("Branch exists")

        request = Phase1Request(feature_description="Add auth")

        with pytest.raises(BranchCreationError):
            phase_executor.execute_phase_1(request)


# Fixtures


@pytest.fixture
def mock_github_service():
    """Create a mock GitHub service."""
    return MagicMock()


@pytest.fixture
def mock_worktree_service():
    """Create a mock worktree service."""
    return MagicMock()


@pytest.fixture
def mock_state_machine():
    """Create a mock state machine."""
    mock = MagicMock()
    state = MagicMock()
    state.issue_number = 123
    state.feature_name = "add-auth"
    state.current_state = WorkflowState.IDLE
    state.phase1_steps = []
    state.branch_name = None
    state.worktree_path = None

    # First call returns None (no state), subsequent calls return the state
    call_count = [0]

    def get_state_side_effect(issue_number):
        call_count[0] += 1
        if call_count[0] == 1:
            return None  # First call: no state exists
        return state

    mock.get_state.side_effect = get_state_side_effect
    mock.create_state.return_value = state
    return mock


@pytest.fixture
def phase_executor(mock_github_service, mock_worktree_service, mock_state_machine, tmp_path):
    """Create a PhaseExecutor with mocked dependencies."""
    from orchestrator.phase_executor import PhaseExecutor

    return PhaseExecutor(
        repo_path=tmp_path,
        github_service=mock_github_service,
        worktree_service=mock_worktree_service,
        state_machine=mock_state_machine,
    )
