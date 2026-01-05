"""Escalation handling for Knowledge Router.

This module handles escalating low-confidence answers to humans,
processing human responses, and re-routing with additional context.
"""

import uuid
from dataclasses import dataclass

from .config import RoutingConfig
from .models import (
    Answer,
    AnswerValidationResult,
    EscalationRequest,
    HumanAction,
    HumanResponse,
    Question,
)


@dataclass
class EscalationResult:
    """Result of processing a human response to an escalation."""

    escalation_resolved: bool
    action_taken: HumanAction
    final_answer: Answer | None = None
    needs_reroute: bool = False
    updated_question: Question | None = None


class EscalationHandler:
    """Handles escalation of low-confidence answers to humans.

    Responsible for:
    - Creating escalation requests from failed validation results
    - Formatting escalations for GitHub comments
    - Processing human responses (confirm, correct, add_context)
    - Re-routing questions with additional context
    """

    def __init__(self, config: RoutingConfig) -> None:
        """Initialize the handler.

        Args:
            config: Routing configuration.
        """
        self._config = config

    def create_escalation(
        self,
        question: Question,
        validation: AnswerValidationResult,
    ) -> EscalationRequest:
        """Create an escalation request from a failed validation.

        Args:
            question: The original question.
            validation: The validation result (must have ESCALATE outcome).

        Returns:
            EscalationRequest ready to be posted to GitHub.
        """
        return EscalationRequest(
            id=str(uuid.uuid4()),
            question=question,
            tentative_answer=validation.answer,
            threshold_used=validation.threshold_used,
        )

    def process_response(
        self,
        escalation: EscalationRequest,
        response: HumanResponse,
    ) -> EscalationResult:
        """Process a human response to an escalation.

        Args:
            escalation: The original escalation request.
            response: The human's response.

        Returns:
            EscalationResult with final answer or re-route instructions.
        """
        if response.action == HumanAction.CONFIRM:
            return self._handle_confirm(escalation, response)
        elif response.action == HumanAction.CORRECT:
            return self._handle_correct(escalation, response)
        elif response.action == HumanAction.ADD_CONTEXT:
            return self._handle_add_context(escalation, response)
        else:
            raise ValueError(f"Unknown action: {response.action}")

    def _handle_confirm(
        self,
        escalation: EscalationRequest,
        response: HumanResponse,
    ) -> EscalationResult:
        """Handle CONFIRM action - accept the tentative answer."""
        return EscalationResult(
            escalation_resolved=True,
            action_taken=HumanAction.CONFIRM,
            final_answer=escalation.tentative_answer,
        )

    def _handle_correct(
        self,
        escalation: EscalationRequest,
        response: HumanResponse,
    ) -> EscalationResult:
        """Handle CORRECT action - replace with human-provided answer."""
        # Create new answer with human's correction and 100% confidence
        original_agent = escalation.tentative_answer.answered_by
        # Ensure responder has @ prefix but avoid double @@
        responder = response.responder
        if not responder.startswith("@"):
            responder = f"@{responder}"
        corrected_answer = Answer(
            question_id=escalation.question.id,
            answered_by=responder,
            answer=response.corrected_answer or escalation.tentative_answer.answer,
            rationale=(
                f"Human-corrected answer replacing original from {original_agent}. "
                "Human review required due to low confidence."
            ),
            confidence=100,  # Human-provided answers have full confidence
            model_used="human",
            duration_seconds=0.0,
        )

        return EscalationResult(
            escalation_resolved=True,
            action_taken=HumanAction.CORRECT,
            final_answer=corrected_answer,
        )

    def _handle_add_context(
        self,
        escalation: EscalationRequest,
        response: HumanResponse,
    ) -> EscalationResult:
        """Handle ADD_CONTEXT action - update question and prepare for re-route."""
        # Create updated question with additional context
        original = escalation.question
        new_context = original.context
        if new_context:
            new_context = (
                f"{new_context}\n\nAdditional context from human:\n{response.additional_context}"
            )
        else:
            new_context = f"Additional context from human:\n{response.additional_context}"

        # Need to create a new Question since it's frozen
        updated_question = Question(
            id=str(uuid.uuid4()),  # New question ID for the re-route
            topic=original.topic,
            suggested_target=original.suggested_target,
            question=original.question,
            context=new_context,
            options=original.options,
            feature_id=original.feature_id,
        )

        return EscalationResult(
            escalation_resolved=False,
            action_taken=HumanAction.ADD_CONTEXT,
            needs_reroute=True,
            updated_question=updated_question,
        )

    def format_github_comment(self, escalation: EscalationRequest) -> str:
        """Format an escalation for posting as a GitHub comment.

        Args:
            escalation: The escalation to format.

        Returns:
            Markdown-formatted comment text.
        """
        answer = escalation.tentative_answer
        question = escalation.question

        uncertainty_section = ""
        if answer.uncertainty_reasons:
            reasons = "\n".join(f"- {r}" for r in answer.uncertainty_reasons)
            uncertainty_section = f"\n\n**Uncertainty reasons:**\n{reasons}"

        return f"""## :warning: Low Confidence Answer - Human Review Required

**Topic:** `{question.topic}`
**Confidence:** {answer.confidence}% (threshold: {escalation.threshold_used}%)

### Question
{question.question}

{f"**Context:** {question.context}" if question.context else ""}

### Tentative Answer
{answer.answer}

**Rationale:** {answer.rationale}{uncertainty_section}

---

### Actions

Please respond with one of the following:
- `/confirm` - Accept this answer as-is
- `/correct <your answer>` - Provide the correct answer
- `/context <additional info>` - Add context and retry the question

**Answered by:** {answer.answered_by} ({answer.model_used})
"""
