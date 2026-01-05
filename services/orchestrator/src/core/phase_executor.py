"""Phase executor for Orchestrator service.

Executes workflow phases by invoking agents via Agent Hub.
"""

from typing import Any
from uuid import UUID

from src.clients.agent_hub import AgentHubClient, AgentHubError
from src.db.models import Workflow, WorkflowType


class PhaseExecutionError(Exception):
    """Error during phase execution."""

    def __init__(
        self,
        message: str,
        phase: str,
        workflow_id: str,
    ) -> None:
        self.message = message
        self.phase = phase
        self.workflow_id = workflow_id
        super().__init__(f"Phase {phase} failed for workflow {workflow_id}: {message}")


# Mapping of workflow types to agents
WORKFLOW_AGENT_MAP: dict[str, str] = {
    WorkflowType.SPECIFY.value: "baron",
    WorkflowType.PLAN.value: "baron",
    WorkflowType.TASKS.value: "baron",
    WorkflowType.IMPLEMENT.value: "baron",
}


class PhaseExecutor:
    """Executes workflow phases via Agent Hub."""

    def __init__(self, agent_hub_url: str | None = None) -> None:
        """Initialize phase executor.

        Args:
            agent_hub_url: Optional Agent Hub URL (defaults to env var)
        """
        self.agent_hub_url = agent_hub_url

    async def execute_phase(
        self,
        workflow: Workflow,
        session_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Execute the current phase of a workflow.

        Args:
            workflow: Workflow to execute
            session_id: Optional session ID for multi-turn

        Returns:
            Phase result dict

        Raises:
            PhaseExecutionError: If phase execution fails
        """
        # Determine which agent to use
        agent = WORKFLOW_AGENT_MAP.get(workflow.workflow_type, "baron")

        # Build context for agent
        context = self._build_context(workflow)

        try:
            async with AgentHubClient(self.agent_hub_url) as client:
                result = await client.invoke_agent(
                    agent=agent,
                    workflow_type=workflow.workflow_type,
                    context=context,
                    session_id=session_id,
                )

                return {
                    "success": result.get("success", True),
                    "output": result.get("result", {}),
                    "confidence": result.get("confidence", 85),
                    "metadata": result.get("metadata", {}),
                }

        except AgentHubError as e:
            raise PhaseExecutionError(
                message=str(e),
                phase=workflow.current_phase or "unknown",
                workflow_id=workflow.id,
            ) from e

    def _build_context(self, workflow: Workflow) -> dict[str, Any]:
        """Build context dict for agent invocation.

        Args:
            workflow: Workflow instance

        Returns:
            Context dict for agent
        """
        context: dict[str, Any] = {
            "feature_id": workflow.feature_id,
            "feature_description": workflow.feature_description,
            "phase": workflow.current_phase,
        }

        # Include workflow context if present
        workflow_context = workflow.get_context()
        if workflow_context:
            context["additional_context"] = workflow_context

        # Include previous result if available
        result = workflow.get_result()
        if result:
            context["previous_result"] = result

        return context

    async def validate_phase_prerequisites(
        self,
        workflow: Workflow,
    ) -> tuple[bool, str | None]:
        """Validate that prerequisites for phase execution are met.

        Args:
            workflow: Workflow to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check workflow is in correct state
        if workflow.status != "in_progress":
            return (
                False,
                f"Workflow is not in_progress (current: {workflow.status})",
            )

        # Check agent hub is available
        try:
            async with AgentHubClient(self.agent_hub_url) as client:
                health = await client.health_check()
                if health.get("status") != "healthy":
                    return (False, "Agent Hub is not healthy")
        except AgentHubError as e:
            return (False, f"Cannot reach Agent Hub: {e}")

        return (True, None)
