"""POST /ask/{topic} endpoint for Agent Hub.

This endpoint handles expert question routing per contracts/agent-hub.yaml.
"""

import time
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.clients.agents import AgentServiceClient, AgentServiceError
from src.core.escalation import EscalationManager
from src.core.router import UnknownTopicError, get_router
from src.core.session_manager import (
    SessionClosedError,
    SessionExpiredError,
    SessionManager,
    SessionNotFoundError,
)
from src.core.validator import validate_confidence
from src.db.session import get_db
from src.logging.audit import get_audit_logger

router = APIRouter()


class AskExpertRequest(BaseModel):
    """Request body for /ask/{topic} endpoint."""

    question: str = Field(
        ...,
        min_length=10,
        description="Question to ask the expert",
    )
    context: str | None = Field(
        default=None,
        description="Additional context for the question",
    )
    feature_id: str = Field(
        ...,
        description="Feature ID for logging",
    )
    session_id: UUID | None = Field(
        default=None,
        description="Session ID for multi-turn conversations",
    )


class AskExpertResponse(BaseModel):
    """Response from /ask/{topic} endpoint."""

    answer: str
    rationale: str | None = None
    confidence: int = Field(..., ge=0, le=100)
    uncertainty_reasons: list[str] | None = None
    status: str = Field(
        ...,
        description="resolved, pending_human, or needs_reroute",
    )
    session_id: UUID
    escalation_id: UUID | None = None


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: list[str] | None = None


class ErrorResponse(BaseModel):
    """Error response structure."""

    error: ErrorDetail


@router.post(
    "/ask/{topic}",
    response_model=AskExpertResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Unknown topic"},
    },
)
async def ask_expert(
    topic: str,
    request: AskExpertRequest,
    db: Session = Depends(get_db),
) -> AskExpertResponse:
    """Ask expert by topic.

    Routes a question to the appropriate expert agent based on topic.
    Validates confidence and creates escalation if below threshold.
    If session_id is provided, includes previous conversation context.

    Args:
        topic: Topic for routing (e.g., architecture, security)
        request: AskExpertRequest with question and context
        db: Database session

    Returns:
        AskExpertResponse with answer and confidence

    Raises:
        HTTPException: On validation or execution error
    """
    start_time = time.time()
    audit_logger = get_audit_logger()
    agent_router = get_router()
    session_manager = SessionManager(db)

    # Get agent for topic
    try:
        agent_info = agent_router.get_agent_for_topic(topic)
    except UnknownTopicError as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "UNKNOWN_TOPIC",
                    "message": str(e),
                    "details": [f"Available topics: {e.available_topics}"],
                }
            },
        ) from e

    agent_name = agent_info["agent"]
    agent_url = agent_info["url"]

    # Handle session
    session_id = request.session_id or uuid4()
    session_context: list[dict[str, str]] = []

    if request.session_id:
        # Validate existing session
        try:
            session_manager.validate_session_for_use(str(request.session_id))
            session_context = session_manager.get_session_context(str(request.session_id))
        except SessionNotFoundError as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "SESSION_NOT_FOUND",
                        "message": str(e),
                    }
                },
            ) from e
        except (SessionClosedError, SessionExpiredError) as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "SESSION_UNAVAILABLE",
                        "message": str(e),
                    }
                },
            ) from e

    # Build context for agent
    agent_context: dict[str, Any] = {
        "question": request.question,
        "topic": topic,
        "feature_id": request.feature_id,
    }
    if request.context:
        agent_context["additional_context"] = request.context
    if session_context:
        agent_context["conversation_history"] = session_context

    # Invoke agent
    try:
        async with AgentServiceClient(agent_url, agent_name=agent_name) as client:
            result = await client.invoke(
                workflow_type=topic,  # Use topic as workflow type
                context=agent_context,
                session_id=session_id,
            )

            confidence = result.get("confidence", 85)
            answer = _extract_answer(result)
            uncertainty_reasons = result.get("result", {}).get("uncertainty_reasons")

            # Record messages in session if session_id was provided
            if request.session_id:
                # Add user message
                session_manager.add_message(
                    session_id=str(request.session_id),
                    role="user",
                    content=request.question,
                    metadata={"topic": topic, "feature_id": request.feature_id},
                )
                # Add assistant message
                session_manager.add_message(
                    session_id=str(request.session_id),
                    role="assistant",
                    content=answer,
                    metadata={"confidence": confidence},
                )

            # Validate confidence
            validation = validate_confidence(confidence, topic)

            # Create escalation if confidence is below threshold
            escalation_id = None
            if not validation.is_valid:
                escalation_manager = EscalationManager(db)
                escalation = escalation_manager.create_escalation(
                    topic=topic,
                    question=request.question,
                    tentative_answer=answer,
                    confidence=confidence,
                    uncertainty_reasons=uncertainty_reasons,
                    session_id=str(session_id) if request.session_id else None,
                )
                escalation_id = UUID(escalation.id)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log the exchange
            audit_logger.log(
                feature_id=request.feature_id,
                topic=topic,
                question=request.question,
                answer=answer,
                confidence=confidence,
                status="escalated" if escalation_id else "resolved",
                duration_ms=duration_ms,
                session_id=session_id if request.session_id else None,
                escalation_id=escalation_id,
                metadata={"agent": agent_name},
            )

            return AskExpertResponse(
                answer=answer,
                rationale=None,  # Could be extracted from result
                confidence=confidence,
                uncertainty_reasons=uncertainty_reasons,
                status=validation.status,
                session_id=session_id,
                escalation_id=escalation_id,
            )

    except AgentServiceError as e:
        # If agent is unavailable, return a fallback response
        # In production, this might try a different agent or queue the request
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "AGENT_UNAVAILABLE",
                    "message": f"Agent {agent_name} is unavailable: {e}",
                }
            },
        ) from e


def _extract_answer(result: dict[str, Any]) -> str:
    """Extract answer from agent result.

    Args:
        result: Agent response dict

    Returns:
        Answer string
    """
    agent_result = result.get("result", {})

    # Try to get output
    if isinstance(agent_result, dict):
        if "output" in agent_result:
            return agent_result["output"]
        if "answer" in agent_result:
            return agent_result["answer"]

    # Fallback to stringifying result
    return str(agent_result) if agent_result else "No answer available"
