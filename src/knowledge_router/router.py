"""Knowledge Router Service.

Main orchestration service for routing questions to agents,
validating answers, and handling escalations.
"""

import uuid

from .config import RoutingConfig
from .dispatcher import AgentDispatcher
from .escalation import EscalationHandler, EscalationResult
from .exceptions import RoutingError
from .models import (
    AgentHandle,
    AgentStatus,
    Answer,
    AnswerValidationResult,
    EscalationRequest,
    HumanResponse,
    Question,
    QuestionTarget,
    ValidationOutcome,
)
from .validator import ConfidenceValidator


class KnowledgeRouterService:
    """Main service for knowledge routing.

    Orchestrates the question-answer protocol between @baron
    and specialized knowledge agents.
    """

    def __init__(
        self,
        config: RoutingConfig,
        dispatcher: AgentDispatcher | None = None,
        validator: ConfidenceValidator | None = None,
    ) -> None:
        """Initialize the router service.

        Args:
            config: Routing configuration.
            dispatcher: Agent dispatcher (creates default if not provided).
            validator: Confidence validator (creates default if not provided).
        """
        self._config = config
        self._dispatcher = dispatcher or AgentDispatcher(config)
        self._validator = validator or ConfidenceValidator(config)
        self._escalation_handler = EscalationHandler(config)

    def route_question(self, question: Question) -> AgentHandle:
        """Route a question to the appropriate agent.

        Args:
            question: The question to route.

        Returns:
            AgentHandle for tracking the dispatch.

        Raises:
            RoutingError: If routing fails.
        """
        # Resolve target agent
        agent_id = self._resolve_agent_for_question(question)

        # If routing to human, return a handle without dispatch
        if agent_id == "human":
            return AgentHandle(
                id=str(uuid.uuid4()),
                agent_role="human",
                agent_name="human",
                status=AgentStatus.PENDING,
                question_id=question.id,
            )

        # Dispatch to agent
        return self._dispatcher.dispatch_question(question, agent_id)

    def _resolve_agent_for_question(self, question: Question) -> str:
        """Resolve which agent should handle a question.

        Priority:
        1. If suggested_target is HUMAN, always route to human
        2. Topic overrides (from config)
        3. Agent topic mappings (from config)
        4. Default to human if no match

        Args:
            question: The question to route.

        Returns:
            Agent ID (e.g., 'architect', 'product', 'human').
        """
        # HUMAN suggested target always goes to human
        if question.suggested_target == QuestionTarget.HUMAN:
            return "human"

        # Use config to resolve agent
        return self._config.get_agent_for_topic(question.topic)

    def submit_answer(self, answer: Answer, topic: str) -> AnswerValidationResult:
        """Submit an answer for validation.

        Args:
            answer: The answer to validate.
            topic: The topic the answer is for (used for threshold lookup).

        Returns:
            AnswerValidationResult with outcome and threshold info.
        """
        return self._validator.validate(answer, topic)

    def escalate_to_human(
        self,
        question: Question,
        validation: AnswerValidationResult,
    ) -> EscalationRequest:
        """Escalate a low-confidence answer to human review.

        Args:
            question: The original question.
            validation: The validation result (should have ESCALATE outcome).

        Returns:
            EscalationRequest for tracking the escalation.

        Raises:
            RoutingError: If validation outcome is not ESCALATE.
        """
        if validation.outcome != ValidationOutcome.ESCALATE:
            raise RoutingError(f"Cannot escalate answer with outcome {validation.outcome}")

        return self._escalation_handler.create_escalation(question, validation)

    def handle_human_response(
        self,
        escalation: EscalationRequest,
        response: HumanResponse,
    ) -> EscalationResult:
        """Handle a human's response to an escalation.

        Args:
            escalation: The original escalation request.
            response: The human's response.

        Returns:
            EscalationResult with final answer or re-route instructions.
        """
        result = self._escalation_handler.process_response(escalation, response)

        # Update escalation status
        if result.escalation_resolved:
            escalation.status = "resolved"

        return result

    def format_escalation_comment(self, escalation: EscalationRequest) -> str:
        """Format an escalation as a GitHub comment.

        Args:
            escalation: The escalation to format.

        Returns:
            Markdown-formatted comment text.
        """
        return self._escalation_handler.format_github_comment(escalation)

    @classmethod
    def from_config(cls, config_path: str) -> "KnowledgeRouterService":
        """Create a router service from a config file.

        Args:
            config_path: Path to the YAML config file.

        Returns:
            Configured KnowledgeRouterService instance.
        """
        from .config import ConfigLoader

        config = ConfigLoader.load_from_file(config_path)
        return cls(config)
