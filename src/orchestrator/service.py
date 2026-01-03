"""OrchestratorService - Main facade for orchestration operations.

This module provides the main service interface for the orchestrator,
coordinating state management, phase execution, signal polling, and
label synchronization.
"""

from pathlib import Path
from typing import Any

from orchestrator.agent_runner import AgentRunner, get_runner
from orchestrator.errors import WorkflowNotFoundError
from orchestrator.label_sync import LabelSync
from orchestrator.logger import logger
from orchestrator.models import (
    OperationResult,
    OrchestratorState,
    Phase1Request,
    Phase2Config,
    PhaseResult,
    PollResult,
    SignalType,
    StateTransition,
)
from orchestrator.phase_executor import PhaseExecutor
from orchestrator.polling import SignalPoller
from orchestrator.state_machine import StateMachine


class OrchestratorService:
    """Main facade for orchestrator operations.

    The OrchestratorService coordinates state management, phase execution,
    signal polling, and label synchronization. It provides a unified
    interface for workflow orchestration.

    Attributes:
        _repo_path: Path to the repository root.
        _github: GitHub service for API operations.
        _worktree: Worktree service for git operations.
        _state_machine: State machine for workflow state.
        _phase_executor: Executor for workflow phases.
        _signal_poller: Poller for completion signals.
        _label_sync: Label synchronization service.

    Example:
        >>> github = GitHubService.from_env()
        >>> worktree = WorktreeService(Path("."))
        >>> orchestrator = OrchestratorService(Path("."), github, worktree)
        >>> result = orchestrator.execute_phase_1(
        ...     Phase1Request(feature_description="Add auth")
        ... )
    """

    def __init__(
        self,
        repo_path: Path,
        github_service: Any,
        worktree_service: Any,
        agent_runner: AgentRunner | None = None,
    ) -> None:
        """Initialize the orchestrator service.

        Args:
            repo_path: Path to the main git repository.
            github_service: GitHub service for API operations.
            worktree_service: Worktree service for worktree operations.
            agent_runner: Agent runner (defaults to ClaudeCLIRunner).
        """
        self._repo_path = repo_path
        self._github = github_service
        self._worktree = worktree_service
        self._agent_runner = agent_runner

        # Initialize internal services
        self._state_machine = StateMachine(repo_path)
        self._phase_executor = PhaseExecutor(
            repo_path=repo_path,
            github_service=github_service,
            worktree_service=worktree_service,
            state_machine=self._state_machine,
        )
        self._signal_poller = SignalPoller(github_service)
        self._label_sync = LabelSync(github_service)

        logger.info(
            "OrchestratorService initialized",
            extra={"context": {"repo_path": str(repo_path)}},
        )

    # =========================================================================
    # State Management
    # =========================================================================

    def get_state(self, issue_number: int) -> OrchestratorState | None:
        """Get current workflow state for an issue.

        Args:
            issue_number: GitHub issue number.

        Returns:
            Current OrchestratorState or None if no workflow exists.
        """
        return self._state_machine.get_state(issue_number)

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
        result = self._state_machine.transition(issue_number, event)

        # Auto-sync labels on state transition
        state = self._state_machine.get_state(issue_number)
        if state:
            try:
                self._label_sync.sync_labels(issue_number, state.current_state)
            except Exception as e:
                logger.warning(
                    f"Label sync failed after transition: {e}",
                    extra={"context": {"issue_number": issue_number}},
                )

        return result

    # =========================================================================
    # Phase Execution
    # =========================================================================

    def execute_phase_1(self, request: Phase1Request) -> PhaseResult:
        """Execute Phase 1: Issue Setup.

        Creates GitHub issue, branch, worktree, and .plans structure.

        Args:
            request: Phase 1 configuration.

        Returns:
            PhaseResult with created artifacts.
        """
        result = self._phase_executor.execute_phase_1(request)

        # Sync labels after successful phase completion
        if result.success and result.artifacts_created:
            # Extract issue number from artifacts
            for artifact in result.artifacts_created:
                if artifact.startswith("issue#"):
                    try:
                        issue_number = int(artifact.replace("issue#", ""))
                        state = self.get_state(issue_number)
                        if state:
                            self._label_sync.sync_labels(issue_number, state.current_state)
                    except (ValueError, Exception) as e:
                        logger.warning(
                            f"Label sync failed after phase 1: {e}",
                            extra={"context": {"artifact": artifact}},
                        )

        return result

    def execute_phase_2(
        self,
        issue_number: int,
        config: Phase2Config,
    ) -> PhaseResult:
        """Execute Phase 2: Specification with Agent.

        Dispatches agent and polls for completion signals.

        Args:
            issue_number: GitHub issue number.
            config: Phase 2 configuration including agent config.

        Returns:
            PhaseResult indicating outcome.

        Raises:
            WorkflowNotFoundError: If no workflow for issue.
            InvalidStateError: If not in PHASE_2 state.
            AgentDispatchError: If agent fails to start.
            PollTimeoutError: If signals not received in time.
        """
        import time

        start_time = time.time()

        # Verify workflow exists and is in correct state
        state = self.get_state(issue_number)
        if state is None:
            raise WorkflowNotFoundError(f"No workflow found for issue {issue_number}")

        logger.info(
            f"Starting Phase 2 for issue {issue_number}",
            extra={
                "context": {
                    "issue_number": issue_number,
                    "current_state": state.current_state.value,
                }
            },
        )

        # Get agent runner
        runner = self._agent_runner or get_runner(config.agent_config)

        # Build context
        context = {
            "issue_number": issue_number,
            "feature_name": state.feature_name,
            "worktree_path": state.worktree_path,
        }

        # Dispatch agent
        agent_result = runner.dispatch(config.agent_config, context)
        if not agent_result.success:
            logger.error(
                f"Agent dispatch failed: {agent_result.error_message}",
                extra={"context": {"issue_number": issue_number}},
            )
            return PhaseResult(
                success=False,
                phase="phase_2",
                error=agent_result.error_message,
                duration_seconds=time.time() - start_time,
            )

        # Poll for agent completion
        agent_poll = self._signal_poller.poll_for_signal(
            issue_number=issue_number,
            signal_type=SignalType.AGENT_COMPLETE,
            timeout_seconds=config.poll_timeout_seconds,
            interval_seconds=config.poll_interval_seconds,
        )

        if agent_poll.detected:
            state.phase2_agent_complete = True
            self._state_machine._save_state(state)

            # Update label
            self._label_sync.sync_labels(issue_number, state.current_state)

        # Poll for human approval
        approval_poll = self._signal_poller.poll_for_signal(
            issue_number=issue_number,
            signal_type=SignalType.HUMAN_APPROVAL,
            timeout_seconds=config.poll_timeout_seconds,
            interval_seconds=config.poll_interval_seconds,
        )

        if approval_poll.detected:
            state.phase2_human_approved = True
            self._state_machine._save_state(state)

            # Transition to GATE_1 then DONE
            self._state_machine.transition(issue_number, "phase_2_complete")
            self._state_machine.transition(issue_number, "approval_received")

            # Sync final label
            state = self.get_state(issue_number)
            if state:
                self._label_sync.sync_labels(issue_number, state.current_state)

        duration = time.time() - start_time
        return PhaseResult(
            success=approval_poll.detected,
            phase="phase_2",
            steps_completed=["agent_dispatch", "agent_poll", "approval_poll"]
            if approval_poll.detected
            else ["agent_dispatch"],
            duration_seconds=duration,
        )

    # =========================================================================
    # Polling
    # =========================================================================

    def poll_for_signal(
        self,
        issue_number: int,
        signal_type: SignalType,
        timeout_seconds: int = 3600,
        interval_seconds: int = 30,
    ) -> PollResult:
        """Poll for a completion signal in issue comments.

        Args:
            issue_number: GitHub issue number.
            signal_type: Type of signal to poll for.
            timeout_seconds: Maximum time to poll (default 1 hour).
            interval_seconds: Time between polls (default 30s).

        Returns:
            PollResult with detection status.
        """
        return self._signal_poller.poll_for_signal(
            issue_number=issue_number,
            signal_type=signal_type,
            timeout_seconds=timeout_seconds,
            interval_seconds=interval_seconds,
        )

    # =========================================================================
    # Label Synchronization
    # =========================================================================

    def sync_labels(self, issue_number: int) -> OperationResult:
        """Synchronize GitHub labels with current state.

        Removes old status labels and applies current state label.

        Args:
            issue_number: GitHub issue number.

        Returns:
            OperationResult indicating success/failure.

        Raises:
            WorkflowNotFoundError: If no workflow for issue.
        """
        state = self.get_state(issue_number)
        if state is None:
            raise WorkflowNotFoundError(f"No workflow found for issue {issue_number}")

        return self._label_sync.sync_labels(issue_number, state.current_state)
