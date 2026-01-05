# Agent Hub API Contract

**Feature**: 005-agent-hub-refactor
**Date**: 2026-01-05

## Service: AgentHub

The main facade for all agent coordination operations.

### Constructor

```python
def __init__(
    self,
    config: HubConfig,
    session_manager: SessionManager | None = None,
    router: AgentRouter | None = None,
) -> None:
    """Initialize the Agent Hub.

    Args:
        config: Hub configuration including agent definitions and thresholds.
        session_manager: Optional custom session manager (default: in-memory).
        router: Optional custom router (default: CLI-based).
    """
```

### Methods

#### ask_expert

```python
async def ask_expert(
    self,
    topic: str,
    question: str,
    context: str = "",
    session_id: str | None = None,
) -> HubResponse:
    """Route a question to the appropriate expert agent.

    Args:
        topic: Domain topic (e.g., "architecture", "product", "testing").
        question: The question to ask.
        context: Additional context for the question.
        session_id: Optional session ID for multi-turn conversations.

    Returns:
        HubResponse with answer, confidence, session_id, and status.

    Raises:
        UnknownTopicError: If topic is not configured.
        AgentDispatchError: If agent dispatch fails.
        AgentTimeoutError: If agent times out.

    Example:
        >>> hub = AgentHub(config)
        >>> response = await hub.ask_expert(
        ...     topic="architecture",
        ...     question="What caching strategy should we use?",
        ...     context="10K concurrent users expected"
        ... )
        >>> if response.status == ResponseStatus.RESOLVED:
        ...     print(response.answer)
        ... elif response.status == ResponseStatus.PENDING_HUMAN:
        ...     # Handle escalation
        ...     print(f"Waiting for human: {response.escalation_id}")
    """
```

#### check_escalation

```python
async def check_escalation(
    self,
    escalation_id: str,
) -> EscalationStatus:
    """Check the status of a pending human escalation.

    Args:
        escalation_id: The escalation ID from HubResponse.

    Returns:
        EscalationStatus with current status and resolution details.

    Raises:
        EscalationNotFoundError: If escalation_id is not found.

    Example:
        >>> status = await hub.check_escalation("abc-123")
        >>> if status.status == "resolved":
        ...     print(f"Human {status.action}: {status.corrected_answer or 'confirmed'}")
        ... elif status.status == "needs_reroute":
        ...     # Re-ask with additional context
        ...     response = await hub.ask_expert(
        ...         topic="architecture",
        ...         question=original_question,
        ...         context=status.additional_context,
        ...         session_id=session_id
        ...     )
    """
```

#### add_human_response

```python
async def add_human_response(
    self,
    escalation_id: str,
    response: HumanResponse,
) -> HubResponse:
    """Process a human response to an escalation.

    Args:
        escalation_id: The escalation ID.
        response: Human's response (confirm, correct, add_context).

    Returns:
        HubResponse with the final answer.

    Raises:
        EscalationNotFoundError: If escalation_id is not found.
        EscalationAlreadyResolvedError: If already resolved.

    Example:
        >>> human_response = HumanResponse(
        ...     escalation_id="abc-123",
        ...     action=HumanAction.CORRECT,
        ...     corrected_answer="Use Redis Cluster with read-through caching",
        ...     responder="farmer1st"
        ... )
        >>> result = await hub.add_human_response("abc-123", human_response)
        >>> print(result.answer)  # Human's corrected answer
        >>> print(result.confidence)  # 100 (human-verified)
    """
```

#### get_session

```python
def get_session(self, session_id: str) -> Session:
    """Retrieve a session by ID.

    Args:
        session_id: The session ID.

    Returns:
        Session with full conversation history.

    Raises:
        SessionNotFoundError: If session does not exist.
    """
```

#### close_session

```python
def close_session(self, session_id: str) -> None:
    """Close and archive a session.

    Args:
        session_id: The session ID to close.

    Raises:
        SessionNotFoundError: If session does not exist.
    """
```

## Service: SessionManager

Manages conversation sessions with expert agents.

### Methods

#### create

```python
def create(
    self,
    agent_id: str,
    feature_id: str = "",
) -> Session:
    """Create a new session.

    Args:
        agent_id: The agent role (e.g., "architect").
        feature_id: Optional feature ID for grouping.

    Returns:
        New Session with unique ID.
    """
```

#### get

```python
def get(self, session_id: str) -> Session | None:
    """Get session by ID.

    Args:
        session_id: The session ID.

    Returns:
        Session if found, None otherwise.
    """
```

#### add_message

```python
def add_message(
    self,
    session_id: str,
    role: MessageRole,
    content: str,
    metadata: dict | None = None,
) -> Message:
    """Add a message to a session.

    Args:
        session_id: The session ID.
        role: Message role (USER, ASSISTANT, HUMAN).
        content: Message content.
        metadata: Optional additional data.

    Returns:
        The created Message.

    Raises:
        SessionNotFoundError: If session does not exist.
        SessionClosedError: If session is closed.
    """
```

#### close

```python
def close(self, session_id: str) -> None:
    """Close a session.

    Args:
        session_id: The session ID.

    Raises:
        SessionNotFoundError: If session does not exist.
    """
```

## MCP Tools Contract

The Agent Hub exposes these tools via MCP server.

### ask_expert (MCP Tool)

```json
{
  "name": "ask_expert",
  "description": "Route a question to the appropriate expert agent based on topic.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "topic": {
        "type": "string",
        "description": "Domain topic (architecture, product, testing, etc.)"
      },
      "question": {
        "type": "string",
        "description": "The question to ask the expert"
      },
      "context": {
        "type": "string",
        "description": "Additional context for the question",
        "default": ""
      },
      "session_id": {
        "type": "string",
        "description": "Optional session ID for multi-turn conversations"
      }
    },
    "required": ["topic", "question"]
  }
}
```

### check_escalation (MCP Tool)

```json
{
  "name": "check_escalation",
  "description": "Check the status of a pending human escalation.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "escalation_id": {
        "type": "string",
        "description": "The escalation ID to check"
      }
    },
    "required": ["escalation_id"]
  }
}
```

## Error Responses

All errors follow the standard format:

```python
class AgentHubError(Exception):
    """Base error for Agent Hub."""
    code: str
    message: str
    details: dict

# Specific errors
class UnknownTopicError(AgentHubError):
    code = "UNKNOWN_TOPIC"
    # details includes: available_topics

class SessionNotFoundError(AgentHubError):
    code = "SESSION_NOT_FOUND"

class EscalationNotFoundError(AgentHubError):
    code = "ESCALATION_NOT_FOUND"

class AgentDispatchError(AgentHubError):
    code = "AGENT_DISPATCH_ERROR"

class AgentTimeoutError(AgentHubError):
    code = "AGENT_TIMEOUT"
```
