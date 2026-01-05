"""Agent Hub Service.

Central coordination layer for all agent interactions.
Routes questions to expert agents, manages sessions, validates confidence,
and handles human escalations.
"""

import uuid
from typing import Any

from .config import RoutingConfig
from .escalation import EscalationHandler, EscalationResult
from .exceptions import EscalationError, RoutingError, UnknownTopicError
from .logger import QALogger
from .models import (
    AgentHandle,
    AgentStatus,
    Answer,
    AnswerValidationResult,
    EscalationRequest,
    HubResponse,
    HumanAction,
    HumanResponse,
    MessageRole,
    QALogEntry,
    Question,
    QuestionTarget,
    ResponseStatus,
    Session,
    ValidationOutcome,
)
from .router import AgentRouter
from .session import SessionManager
from .validator import ConfidenceValidator


class AgentHub:
    """Central coordination layer for agent interactions.

    Routes questions to expert agents, manages conversation sessions,
    validates confidence, and handles human escalations.
    """

    def __init__(
        self,
        config: RoutingConfig,
        router: AgentRouter | None = None,
        validator: ConfidenceValidator | None = None,
        session_manager: SessionManager | None = None,
        log_dir: str | None = None,
    ) -> None:
        """Initialize the Agent Hub.

        Args:
            config: Hub configuration including agent definitions and thresholds.
            router: Agent router (creates default if not provided).
            validator: Confidence validator (creates default if not provided).
            session_manager: Session manager (creates default if not provided).
            log_dir: Directory for Q&A logs (T066). If None, logging is disabled.
        """
        self._config = config
        self._router = router or AgentRouter(config)
        self._validator = validator or ConfidenceValidator(config)
        self._escalation_handler = EscalationHandler(config)
        self._session_manager = session_manager or SessionManager()
        self._escalations: dict[str, EscalationRequest] = {}  # Escalation storage
        self._logger = QALogger(log_dir) if log_dir else None  # T066: QA Logger

    def ask_expert(
        self,
        topic: str,
        question: str,
        context: str = "",
        feature_id: str = "",
        session_id: str | None = None,
    ) -> HubResponse:
        """Route a question to the appropriate expert agent.

        Args:
            topic: Domain topic (e.g., "architecture", "product", "testing").
            question: The question to ask.
            context: Additional context for the question.
            feature_id: Feature ID for grouping questions.
            session_id: Optional session ID for multi-turn conversations.

        Returns:
            HubResponse with answer, confidence, session_id, and status.

        Raises:
            UnknownTopicError: If topic is not configured.
            AgentDispatchError: If agent dispatch fails.
            AgentTimeoutError: If agent times out.
        """
        # T031: Validate topic
        if not self._config.is_known_topic(topic):
            available_topics = self._config.get_all_topics()
            raise UnknownTopicError(topic, available_topics)

        # Create or reuse session (T044-T046: Use SessionManager)
        if session_id and self._session_manager.exists(session_id):
            current_session_id = session_id
        else:
            # Resolve agent for topic to set agent_id on session
            agent_id = self._config.get_agent_for_topic(topic)
            session = self._session_manager.create(
                agent_id=agent_id,
                feature_id=feature_id or "000-default",
            )
            current_session_id = session.id

        # Build Question object
        q = Question(
            id=str(uuid.uuid4()),
            topic=topic,
            suggested_target=QuestionTarget.ARCHITECT,  # Default, routing handles actual target
            question=question,
            context=context,
            feature_id=feature_id or "000-default",
        )

        # Route to agent
        agent_id = self._resolve_agent_for_question(q)

        # If routing to human directly, return pending response
        if agent_id == "human":
            escalation_id = str(uuid.uuid4())
            return HubResponse(
                answer="",
                rationale="Question requires direct human input",
                confidence=0,
                uncertainty_reasons=["Question routed directly to human"],
                session_id=current_session_id,
                status=ResponseStatus.PENDING_HUMAN,
                escalation_id=escalation_id,
            )

        # Dispatch to agent
        handle = self._router.dispatch_question(q, agent_id)

        # Parse the answer
        answer = self._router.parse_answer(handle, q)

        # Validate confidence
        validation = self._validator.validate(answer, topic)

        # Store messages in session (T044: Use SessionManager)
        self._session_manager.add_message(
            session_id=current_session_id,
            role=MessageRole.USER,
            content=question,
            metadata={"context": context} if context else None,
        )
        self._session_manager.add_message(
            session_id=current_session_id,
            role=MessageRole.ASSISTANT,
            content=answer.answer,
            metadata={
                "confidence": answer.confidence,
                "rationale": answer.rationale,
            },
        )

        # Build routing decision string
        agent_name = self._config.get_agent_name(agent_id)
        routing_decision = f"Routed to {agent_id} ({agent_name}) based on topic '{topic}'"

        # If low confidence, create escalation
        if validation.outcome == ValidationOutcome.ESCALATE:
            escalation = self._escalation_handler.create_escalation(q, validation)
            self._escalations[escalation.id] = escalation

            # T066-T068: Log the escalated exchange
            self._log_exchange(
                question=q,
                answer=answer,
                validation=validation,
                session_id=current_session_id,
                routing_decision=routing_decision + ", escalated due to low confidence",
                escalation=escalation,
            )

            return HubResponse(
                answer=answer.answer,
                rationale=answer.rationale,
                confidence=answer.confidence,
                uncertainty_reasons=answer.uncertainty_reasons,
                session_id=current_session_id,
                status=ResponseStatus.PENDING_HUMAN,
                escalation_id=escalation.id,
            )

        # T066-T068: Log the resolved exchange
        self._log_exchange(
            question=q,
            answer=answer,
            validation=validation,
            session_id=current_session_id,
            routing_decision=routing_decision,
        )

        # High confidence - return resolved
        return HubResponse(
            answer=answer.answer,
            rationale=answer.rationale,
            confidence=answer.confidence,
            uncertainty_reasons=answer.uncertainty_reasons,
            session_id=current_session_id,
            status=ResponseStatus.RESOLVED,
            escalation_id=None,
        )

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
        return self._router.dispatch_question(question, agent_id)

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

    def get_session(self, session_id: str) -> Session:
        """Get a session by ID (T045).

        Args:
            session_id: The session ID.

        Returns:
            Session if found.

        Raises:
            SessionNotFoundError: If session does not exist.
        """
        return self._session_manager.get(session_id)

    def close_session(self, session_id: str) -> None:
        """Close a session (T045).

        Closed sessions cannot accept new messages.

        Args:
            session_id: The session ID.

        Raises:
            SessionNotFoundError: If session does not exist.
        """
        self._session_manager.close(session_id)

    def check_escalation(self, escalation_id: str) -> EscalationRequest:
        """Get an escalation by ID (T059).

        Args:
            escalation_id: The escalation ID.

        Returns:
            EscalationRequest if found.

        Raises:
            EscalationError: If escalation does not exist.
        """
        if escalation_id not in self._escalations:
            raise EscalationError(f"Escalation not found: {escalation_id}")
        return self._escalations[escalation_id]

    def add_human_response(
        self,
        escalation_id: str,
        action: HumanAction,
        responder: str,
        corrected_answer: str | None = None,
        additional_context: str | None = None,
        github_comment_id: int = 0,
    ) -> EscalationResult:
        """Add a human response to an escalation (T060).

        Processes the human's response and feeds it back to the session (T061).
        Handles NEEDS_REROUTE status for re-querying with context (T062).

        Args:
            escalation_id: The escalation ID.
            action: What action the human took (CONFIRM, CORRECT, ADD_CONTEXT).
            responder: GitHub username of the responder.
            corrected_answer: The corrected answer if action is CORRECT.
            additional_context: Additional context if action is ADD_CONTEXT.
            github_comment_id: GitHub comment ID where response was posted.

        Returns:
            EscalationResult with resolution details.

        Raises:
            EscalationError: If escalation does not exist.
        """
        # T059: Look up escalation
        escalation = self.check_escalation(escalation_id)

        # Create HumanResponse
        human_response = HumanResponse(
            escalation_id=escalation_id,
            action=action,
            corrected_answer=corrected_answer,
            additional_context=additional_context,
            responder=responder,
            github_comment_id=github_comment_id,
        )

        # Process the response using existing handle_human_response
        result = self.handle_human_response(escalation, human_response)

        # T061: Feed human response back to session
        # Find the session associated with this escalation
        # The session was created during ask_expert, we need to find it
        # For now, we'll look through sessions to find one with this feature_id
        # Note: This could be improved by storing session_id in escalation
        for session_id in self._session_manager._sessions:
            session = self._session_manager._sessions[session_id]
            if session.feature_id == escalation.question.feature_id:
                # Add human message to session
                content = ""
                if action == HumanAction.CONFIRM:
                    content = "Confirmed the tentative answer"
                elif action == HumanAction.CORRECT:
                    content = f"Corrected answer: {corrected_answer}"
                elif action == HumanAction.ADD_CONTEXT:
                    content = f"Added context: {additional_context}"

                self._session_manager.add_message(
                    session_id=session_id,
                    role=MessageRole.HUMAN,
                    content=content,
                    metadata={
                        "responder": responder,
                        "action": action.value,
                        "escalation_id": escalation_id,
                    },
                )
                break

        # T062: Handle NEEDS_REROUTE status
        # The result.needs_reroute flag is already set by handle_human_response
        # Caller can check result.needs_reroute and result.updated_question
        # to trigger a new ask_expert call with the updated context

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
    def from_config(cls, config_path: str) -> "AgentHub":
        """Create an Agent Hub from a config file.

        Args:
            config_path: Path to the YAML config file.

        Returns:
            Configured AgentHub instance.
        """
        from .config import ConfigLoader

        config = ConfigLoader.load_from_file(config_path)
        return cls(config)

    def _log_exchange(
        self,
        question: Question,
        answer: Answer,
        validation: AnswerValidationResult,
        session_id: str,
        routing_decision: str,
        escalation: EscalationRequest | None = None,
    ) -> None:
        """Log a Q&A exchange (T066).

        Args:
            question: The question that was asked.
            answer: The answer received.
            validation: The validation result.
            session_id: The session ID for this exchange.
            routing_decision: Description of how the question was routed.
            escalation: Escalation request if applicable (T068).
        """
        if not self._logger:
            return

        log_entry = QALogEntry(
            id=str(uuid.uuid4()),
            feature_id=question.feature_id,
            question=question,
            answer=answer,
            validation_result=validation,
            escalation=escalation,
            final_answer=answer,
            routing_decision=routing_decision,
            total_duration_seconds=answer.duration_seconds,
            session_id=session_id,  # T067: Include session_id
        )

        self._logger.log_exchange(log_entry)

    def get_logs_for_feature(self, feature_id: str) -> list[dict[str, Any]]:
        """Get all Q&A logs for a feature (T066).

        Args:
            feature_id: The feature ID to retrieve logs for.

        Returns:
            List of log entries as dictionaries.
        """
        if not self._logger:
            return []
        return self._logger.get_logs_for_feature(feature_id)
