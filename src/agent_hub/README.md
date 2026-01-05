# Agent Hub Module

Central coordination layer for all agent interactions.

## Overview

The Agent Hub module provides intelligent question routing and answer validation:

- **Question Routing**: Route questions to appropriate expert agents based on topic
- **Session Management**: Maintain conversation context across multi-turn interactions
- **Answer Validation**: Validate agent answers against configurable confidence thresholds
- **Human Escalation**: Package low-confidence answers for human review
- **Audit Logging**: Immutable logging of all exchanges for retrospective analysis
- **MCP Server**: Expose functionality via Model Context Protocol for SDK agents

## Quick Start

```python
from agent_hub import AgentHub, RoutingConfig, ConfigLoader

# Initialize hub from config
config = ConfigLoader.load_from_file("config/routing.yaml")
hub = AgentHub(config, log_dir="logs/qa")

# Ask an expert
response = hub.ask_expert(
    topic="architecture",
    question="Which auth method should we use for the API?",
    context="Building microservices with 10K concurrent users",
    feature_id="005-user-auth",
)

if response.status.value == "resolved":
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence}%")
else:
    # Low confidence - escalated to human
    print(f"Pending human review: {response.escalation_id}")

# Multi-turn conversation
follow_up = hub.ask_expert(
    topic="architecture",
    question="What about rate limiting?",
    session_id=response.session_id,  # Continue conversation
)
```

## Architecture

### Core Components

| Component | Purpose |
|-----------|---------|
| `AgentHub` | Main facade coordinating routing, sessions, and validation |
| `AgentRouter` | Spawns Claude CLI agents and parses responses |
| `SessionManager` | Manages conversation sessions with context preservation |
| `ConfidenceValidator` | Validates answers against thresholds |
| `EscalationHandler` | Manages human review workflow |
| `QALogger` | Logs all Q&A exchanges to JSONL |
| `RoutingConfig` | Loads and manages routing configuration |

### Q&A Flow

```
Question ──ask_expert──► Agent ──answer──► Validator
                                              │
              ┌───resolved───────────────────►│
              │                                │
         [RESOLVED]◄──high confidence──────────┤
              │                                │
         [PENDING_HUMAN]◄──low confidence──────┘
              │
              ▼
    Human Review ──► CONFIRM / CORRECT / ADD_CONTEXT
              │
              ▼
         Final Answer ──► QALogger
```

## API Reference

### AgentHub

```python
class AgentHub:
    def __init__(
        self,
        config: RoutingConfig,
        router: AgentRouter | None = None,
        validator: ConfidenceValidator | None = None,
        session_manager: SessionManager | None = None,
        log_dir: str | None = None,
    ): ...

    def ask_expert(
        self,
        topic: str,
        question: str,
        context: str = "",
        feature_id: str = "",
        session_id: str | None = None,
    ) -> HubResponse: ...

    def check_escalation(self, escalation_id: str) -> EscalationRequest: ...

    def add_human_response(
        self,
        escalation_id: str,
        action: HumanAction,
        responder: str,
        corrected_answer: str | None = None,
        additional_context: str | None = None,
    ) -> EscalationResult: ...

    def get_session(self, session_id: str) -> Session: ...
    def close_session(self, session_id: str) -> None: ...
    def get_logs_for_feature(self, feature_id: str) -> list[dict]: ...
```

### Models

| Model | Description |
|-------|-------------|
| `HubResponse` | Response with answer, confidence, session_id, status |
| `Session` | Conversation session with message history |
| `Message` | Individual message in a session |
| `Question` | Question with topic, target, and context |
| `Answer` | Agent response with confidence score |
| `EscalationRequest` | Package for human review |
| `EscalationResult` | Human response resolution |
| `QALogEntry` | Complete Q&A exchange record |

### Enums

| Enum | Values |
|------|--------|
| `ResponseStatus` | RESOLVED, PENDING_HUMAN, NEEDS_REROUTE |
| `MessageRole` | USER, ASSISTANT, HUMAN |
| `SessionStatus` | ACTIVE, CLOSED, EXPIRED |
| `HumanAction` | CONFIRM, CORRECT, ADD_CONTEXT |
| `ValidationOutcome` | ACCEPTED, ESCALATE |

### Errors

| Error | When Raised |
|-------|-------------|
| `UnknownTopicError` | Topic not configured |
| `SessionNotFoundError` | Session does not exist |
| `SessionClosedError` | Session already closed |
| `EscalationError` | Escalation not found or invalid |
| `AgentDispatchError` | Agent failed to start |
| `AgentTimeoutError` | Agent execution timed out |

## Configuration

Configuration is managed via YAML:

```yaml
# config/routing.yaml
defaults:
  confidence_threshold: 80
  timeout_seconds: 120
  model: sonnet

agents:
  architect:
    name: "@duc"
    model: opus
    topics: [architecture, design, patterns]
  devops:
    name: "@gustave"
    topics: [deployment, ci, infrastructure]

overrides:
  security:
    agent: architect
    confidence_threshold: 95  # Higher bar for security
```

### Threshold Precedence

1. Topic-specific override (e.g., security: 95%)
2. Default threshold (80%)

## Session Management

Sessions maintain conversation context across multiple ask_expert calls:

```python
# First question creates a session
response1 = hub.ask_expert(
    topic="architecture",
    question="How should we structure the API?",
    feature_id="005-api"
)

# Follow-up uses the same session
response2 = hub.ask_expert(
    topic="architecture",
    question="What about authentication?",
    session_id=response1.session_id,  # Preserves context
)

# Get full conversation history
session = hub.get_session(response1.session_id)
for msg in session.messages:
    print(f"{msg.role.value}: {msg.content}")

# Close when done
hub.close_session(response1.session_id)
```

## Human Escalation

When an answer falls below the confidence threshold:

1. `ask_expert` returns `PENDING_HUMAN` status with `escalation_id`
2. Check escalation status with `check_escalation(escalation_id)`
3. Process human response with `add_human_response()`

| Action | Effect |
|--------|--------|
| `CONFIRM` | Accept the tentative answer as-is |
| `CORRECT` | Replace with human-provided answer (100% confidence) |
| `ADD_CONTEXT` | Add context and re-route to agent |

```python
# Check escalation status
escalation = hub.check_escalation(response.escalation_id)
print(f"Status: {escalation.status}")

# Process human response
result = hub.add_human_response(
    escalation_id=response.escalation_id,
    action=HumanAction.CORRECT,
    responder="farmer1st",
    corrected_answer="Use OAuth2 with PKCE for public clients",
)
```

## MCP Server

The Agent Hub can be exposed as an MCP server for Claude Agent SDK integration:

```bash
# Run as MCP server
python -m agent_hub.mcp_server
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `ask_expert` | Route question to appropriate expert |
| `check_escalation` | Check pending escalation status |

### Claude Agent SDK Integration

```python
from claude_code_sdk import query, ClaudeCodeOptions

async for event in query(
    prompt="Ask the architecture expert about caching",
    options=ClaudeCodeOptions(
        mcp_servers={
            "agent-hub": {
                "command": "python",
                "args": ["-m", "agent_hub.mcp_server"]
            }
        }
    )
):
    ...
```

## Audit Logging

All exchanges are logged to JSONL files when `log_dir` is provided:

```
logs/qa/{feature_id}.jsonl
```

Each line is a complete `QALogEntry`:
- Question details with session_id
- Agent's answer with confidence
- Validation result
- Escalation details (if any)
- Routing decision
- Timing information

### Retrieving Logs

```python
# Get all logs for a feature
logs = hub.get_logs_for_feature("005-user-auth")
for log in logs:
    print(f"Q: {log['question']['question']}")
    print(f"A: {log['answer']['answer']}")
    print(f"Session: {log['session_id']}")
```

## Testing

```bash
# Run all agent hub tests
uv run pytest tests/unit/agent_hub/ tests/integration/agent_hub/ \
    tests/contract/agent_hub/ tests/e2e/agent_hub/ -v

# Run journey tests only
uv run pytest -m "journey" tests/e2e/agent_hub/ -v

# Run specific journey
uv run pytest -m "journey('AH-001')" -v
```

## User Journeys

| Journey | Description | Status |
|---------|-------------|--------|
| [AH-001](../../docs/user-journeys/AH-001-route-question.md) | Route Question to Expert | Implemented |
| [AH-002](../../docs/user-journeys/AH-002-session-management.md) | Maintain Conversation Sessions | Implemented |
| [AH-003](../../docs/user-journeys/AH-003-confidence-escalation.md) | Validate Confidence and Escalate | Implemented |
| [AH-004](../../docs/user-journeys/AH-004-pending-escalation.md) | Track Pending Escalations | Implemented |
| [AH-005](../../docs/user-journeys/AH-005-audit-logging.md) | Audit Trail Logging | Implemented |

## Dependencies

- `subprocess` - Claude CLI spawning
- `pydantic` - Data validation and serialization
- `PyYAML` - Configuration parsing
- `mcp` - Model Context Protocol SDK
