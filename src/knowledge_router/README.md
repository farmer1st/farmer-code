# Knowledge Router Module

Question routing, validation, and escalation for AI agent Q&A protocol.

## Overview

The Knowledge Router module provides intelligent question routing and answer validation:

- **Question Routing**: Route questions to appropriate knowledge agents based on topic
- **Answer Validation**: Validate agent answers against configurable confidence thresholds
- **Human Escalation**: Package low-confidence answers for human review
- **Q&A Logging**: Immutable logging of all exchanges for retrospective analysis

## Quick Start

```python
from pathlib import Path
from knowledge_router import (
    KnowledgeRouter,
    Question,
    QuestionTarget,
    HumanAction,
    HumanResponse,
)

# Initialize router
router = KnowledgeRouter(Path("config/routing.yaml"))

# Create and route a question
question = Question(
    id="q-001",
    topic="authentication",
    suggested_target=QuestionTarget.ARCHITECT,
    question="Which auth method should we use for the API?",
    feature_id="005-user-auth",
)

# Route to agent
handle = router.route_question(question)

# Submit answer and validate
answer = router.submit_answer(handle, question)

if answer.is_high_confidence:
    print(f"Accepted: {answer.answer}")
else:
    # Escalate to human
    escalation = router.escalate_to_human(question, validation_result)

    # Human responds
    response = HumanResponse(
        escalation_id=escalation.id,
        responder="reviewer",
        action=HumanAction.CONFIRM,
    )
    result = router.handle_human_response(escalation, response)
```

## Architecture

### Core Components

| Component | Purpose |
|-----------|---------|
| `KnowledgeRouter` | Main facade coordinating routing and validation |
| `AgentDispatcher` | Spawns Claude CLI agents and parses responses |
| `ConfidenceValidator` | Validates answers against thresholds |
| `EscalationHandler` | Manages human review workflow |
| `QALogger` | Logs all Q&A exchanges to JSONL |
| `RoutingConfig` | Loads and manages routing configuration |

### Q&A Flow

```
Question ──route──► Agent ──answer──► Validator
                                          │
              ┌───accepted───────────────►│
              │                            │
         [Accept]◄──high confidence────────┤
              │                            │
         [Escalate]◄──low confidence───────┘
              │
              ▼
    Human Review ──► CONFIRM / CORRECT / ADD_CONTEXT
              │
              ▼
         Final Answer ──► QALogger
```

## API Reference

### KnowledgeRouter

```python
class KnowledgeRouter:
    def __init__(self, config_path: Path): ...
    def route_question(self, question: Question) -> AgentHandle: ...
    def submit_answer(self, handle: AgentHandle, question: Question) -> Answer: ...
    def validate_answer(self, answer: Answer) -> AnswerValidationResult: ...
    def escalate_to_human(self, question, validation) -> EscalationRequest: ...
    def handle_human_response(self, escalation, response) -> EscalationResult: ...
```

### Models

| Model | Description |
|-------|-------------|
| `Question` | Question with topic, target, and context |
| `Answer` | Agent response with confidence score |
| `AnswerValidationResult` | Validation outcome (ACCEPTED/ESCALATE) |
| `EscalationRequest` | Package for human review |
| `HumanResponse` | Human's response with action |
| `QALogEntry` | Complete Q&A exchange record |

### Enums

| Enum | Values |
|------|--------|
| `QuestionTarget` | ARCHITECT, DEVOPS, SECURITY, FRONTEND, BACKEND, QA |
| `ValidationOutcome` | ACCEPTED, ESCALATE |
| `HumanAction` | CONFIRM, CORRECT, ADD_CONTEXT |

### Errors

| Error | When Raised |
|-------|-------------|
| `RoutingError` | No agent available for topic |
| `AgentDispatchError` | Agent failed to start |
| `AgentTimeoutError` | Agent execution timed out |
| `AgentResponseError` | Invalid response from agent |
| `EscalationError` | Escalation processing failed |

## Configuration

Configuration is managed via YAML:

```yaml
# config/routing.yaml
default_threshold: 80

agents:
  - target: architect
    name: "@duc"
    model: opus
    topics: [architecture, design, patterns]
  - target: devops
    name: "@gustave"
    model: sonnet
    topics: [deployment, ci, infrastructure]

topic_overrides:
  security:
    threshold: 95  # Higher bar for security questions
```

### Threshold Precedence

1. Topic-specific override (e.g., security: 95%)
2. Default threshold (80%)

## Human Escalation

When an answer falls below the confidence threshold:

1. `EscalationRequest` is created with full context
2. GitHub comment is formatted with question, answer, and rationale
3. Human responds with one of three actions:

| Action | Effect |
|--------|--------|
| `/confirm` | Accept the tentative answer as-is |
| `/correct <answer>` | Replace with human-provided answer (100% confidence) |
| `/context <info>` | Add context and re-route to agent |

## Q&A Logging

All exchanges are logged to JSONL files:

```
logs/qa/{feature_id}.jsonl
```

Each line is a complete `QALogEntry`:
- Question details
- Agent's answer
- Validation result
- Escalation and human response (if any)
- Final answer
- Timing information

### Retrieving Logs

```python
from knowledge_router import QALogger

logger = QALogger(Path("logs/qa"))

# Get all logs for a feature
logs = logger.get_logs_for_feature("005-user-auth")

# Get an exchange chain (for re-routed questions)
chain = logger.get_exchange_chain(entry_id, "005-user-auth")
```

## Testing

```bash
# Run all knowledge router tests
uv run pytest tests/unit/knowledge_router/ tests/integration/knowledge_router/ \
    tests/contract/knowledge_router/ tests/e2e/knowledge_router/ -v

# Run journey tests only
uv run pytest -m "journey" tests/e2e/knowledge_router/ -v

# Run specific journey
uv run pytest -m "journey('KR-001')" -v
```

## User Journeys

| Journey | Description | Status |
|---------|-------------|--------|
| [KR-001](../../docs/user-journeys/KR-001-route-question.md) | Route Question to Agent | Implemented |
| [KR-002](../../docs/user-journeys/KR-002-validate-confidence.md) | Validate Answer Confidence | Implemented |
| [KR-003](../../docs/user-journeys/KR-003-escalate-human.md) | Escalate to Human | Implemented |
| [KR-004](../../docs/user-journeys/KR-004-log-qa.md) | Log Q&A Exchange | Implemented |
| KR-005 | Dispatch Execution Tasks | Planned (P2) |
| KR-006 | Configure Routing | Planned (P2) |
| KR-007 | Generate Retrospective | Planned (P2) |
| KR-008 | Handle Agent Unavailable | Planned (P3) |

## Dependencies

- `subprocess` - Claude CLI spawning
- `pydantic` - Data validation and serialization
- `PyYAML` - Configuration parsing
