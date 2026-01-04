# Data Model: Knowledge Router

**Feature**: 004-knowledge-router
**Date**: 2026-01-03

## Overview

This document defines all Pydantic models for the Knowledge Router feature. Models are organized by domain: Core Q&A, Routing, Escalation, Logging, and Execution.

## Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Question   │────▶│   Answer    │────▶│ EscalationReq   │
│  (from      │     │  (from      │     │ (if confidence  │
│   @baron)   │     │   agent)    │     │  < threshold)   │
└─────────────┘     └─────────────┘     └────────┬────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │ HumanResponse   │
                                        │ (confirm/       │
                                        │  correct/add)   │
                                        └─────────────────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│RoutingConfig│────▶│RoutingRule │     │   QALogEntry    │
│ (YAML file) │     │ (per topic) │     │ (immutable log) │
└─────────────┘     └─────────────┘     └─────────────────┘
```

## Core Q&A Models

### Question

Structured query from @baron to a knowledge agent.

```python
class QuestionTarget(str, Enum):
    """Target agent type for a question."""
    ARCHITECT = "architect"
    PRODUCT = "product"
    HUMAN = "human"

class Question(BaseModel):
    """A structured question from @baron."""

    id: str = Field(description="Unique question ID (UUID)")
    topic: str = Field(description="Question topic for routing (e.g., 'authentication')")
    suggested_target: QuestionTarget = Field(description="@baron's suggested target agent")
    question: str = Field(description="The question text")
    context: str = Field(default="", description="Additional context for the question")
    options: list[str] | None = Field(default=None, description="Optional answer choices")
    feature_id: str = Field(description="Feature this question belongs to")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}
```

**Validation Rules**:
- `id`: UUID v4 format
- `topic`: non-empty, lowercase, alphanumeric with underscores
- `question`: min 10 characters

---

### Answer

Agent's response to a question with confidence score.

```python
class Answer(BaseModel):
    """An agent's answer to a question."""

    question_id: str = Field(description="Reference to the question")
    answered_by: str = Field(description="Agent role (e.g., 'architect', '@duc')")
    answer: str = Field(description="The answer content")
    rationale: str = Field(description="Why this answer is correct")
    confidence: int = Field(ge=0, le=100, description="Confidence percentage (0-100)")
    uncertainty_reasons: list[str] = Field(
        default_factory=list,
        description="Reasons for uncertainty (if confidence < 100)"
    )
    model_used: str = Field(description="Model that generated this answer")
    duration_seconds: float = Field(description="Time to generate answer")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}

    @property
    def is_high_confidence(self) -> bool:
        """Check if answer meets default threshold."""
        return self.confidence >= 80
```

**Validation Rules**:
- `confidence`: integer 0-100
- `rationale`: min 20 characters (must explain reasoning)

---

### AnswerValidationResult

Result of validating an answer against thresholds.

```python
class ValidationOutcome(str, Enum):
    """Outcome of answer validation."""
    ACCEPTED = "accepted"
    ESCALATE = "escalate"

class AnswerValidationResult(BaseModel):
    """Result of validating an answer's confidence."""

    outcome: ValidationOutcome
    answer: Answer
    threshold_used: int = Field(description="Confidence threshold that was applied")
    threshold_source: str = Field(
        description="Where threshold came from (default, topic_override, etc.)"
    )

    model_config = {"frozen": True}
```

---

## Routing Models

### RoutingRule

Configuration for routing a topic to an agent.

```python
class RoutingRule(BaseModel):
    """Rule for routing a topic to an agent."""

    topic: str = Field(description="Topic pattern (exact match or wildcard)")
    agent: str = Field(description="Target agent ID or 'human'")
    confidence_threshold: int | None = Field(
        default=None,
        description="Override default threshold for this topic"
    )
    model_override: str | None = Field(
        default=None,
        description="Use specific model for this topic"
    )
    priority: int = Field(default=0, description="Higher priority rules match first")

    model_config = {"frozen": True}
```

---

### AgentDefinition

Definition of a knowledge or execution agent.

```python
class AgentType(str, Enum):
    """Type of agent."""
    KNOWLEDGE = "knowledge"
    EXECUTION = "execution"

class AgentDefinition(BaseModel):
    """Definition of an agent."""

    id: str = Field(description="Agent identifier (e.g., 'architect')")
    name: str = Field(description="Display name (e.g., '@duc')")
    agent_type: AgentType
    topics: list[str] = Field(default_factory=list, description="Topics this agent handles")
    scope: list[str] = Field(
        default_factory=list,
        description="File paths agent can access (execution only)"
    )
    default_model: str = Field(default="sonnet")
    default_timeout: int = Field(default=120, description="Timeout in seconds")

    model_config = {"frozen": True}
```

---

### RoutingConfig

Complete routing configuration loaded from YAML.

```python
class RoutingConfig(BaseModel):
    """Complete routing configuration."""

    default_confidence_threshold: int = Field(default=80)
    default_timeout_seconds: int = Field(default=120)
    default_model: str = Field(default="sonnet")

    agents: dict[str, AgentDefinition] = Field(
        default_factory=dict,
        description="Agent definitions keyed by ID"
    )
    overrides: dict[str, RoutingRule] = Field(
        default_factory=dict,
        description="Topic-specific override rules"
    )

    def get_agent_for_topic(self, topic: str) -> str:
        """Resolve topic to agent ID."""
        # Check overrides first
        if topic in self.overrides:
            return self.overrides[topic].agent

        # Find agent by topic
        for agent_id, agent in self.agents.items():
            if topic in agent.topics:
                return agent_id

        # Default to human
        return "human"

    def get_threshold_for_topic(self, topic: str) -> int:
        """Get confidence threshold for topic."""
        if topic in self.overrides and self.overrides[topic].confidence_threshold:
            return self.overrides[topic].confidence_threshold
        return self.default_confidence_threshold
```

---

## Escalation Models

### EscalationRequest

Package for human escalation when confidence is low.

```python
class EscalationRequest(BaseModel):
    """Low-confidence answer packaged for human review."""

    id: str = Field(description="Escalation ID (UUID)")
    question: Question
    tentative_answer: Answer
    threshold_used: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    github_comment_id: int | None = Field(
        default=None,
        description="GitHub comment ID where escalation was posted"
    )
    status: str = Field(default="pending", description="pending, resolved, expired")

    model_config = {"frozen": False}  # Status can be updated
```

---

### HumanResponse

Human's response to an escalation.

```python
class HumanAction(str, Enum):
    """Actions a human can take on an escalation."""
    CONFIRM = "confirm"
    CORRECT = "correct"
    ADD_CONTEXT = "add_context"

class HumanResponse(BaseModel):
    """Human's response to an escalation."""

    escalation_id: str
    action: HumanAction
    corrected_answer: str | None = Field(
        default=None,
        description="New answer if action is CORRECT"
    )
    additional_context: str | None = Field(
        default=None,
        description="Context to add if action is ADD_CONTEXT"
    )
    responder: str = Field(description="GitHub username of responder")
    github_comment_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}
```

---

## Logging Models

### QALogEntry

Immutable record of a Q&A exchange.

```python
class QALogEntry(BaseModel):
    """Immutable log entry for a Q&A exchange."""

    id: str = Field(description="Log entry ID (UUID)")
    feature_id: str
    question: Question
    answer: Answer
    validation_result: AnswerValidationResult
    escalation: EscalationRequest | None = None
    human_response: HumanResponse | None = None
    final_answer: Answer = Field(description="Final answer after any human intervention")
    routing_decision: str = Field(description="Which agent was chosen and why")
    total_duration_seconds: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": True}
```

---

### RetroReport

Aggregated analysis of Q&A patterns.

```python
class ImprovementRecommendation(BaseModel):
    """A recommendation from retrospective analysis."""

    category: str = Field(description="Category: agent_knowledge, intake_template, threshold")
    description: str
    affected_topics: list[str]
    priority: str = Field(description="high, medium, low")

class RetroReport(BaseModel):
    """Retrospective analysis report."""

    feature_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Statistics
    total_questions: int
    high_confidence_count: int
    escalated_count: int
    average_confidence: float

    # Breakdown by agent
    questions_per_agent: dict[str, int]
    avg_confidence_per_agent: dict[str, float]

    # Escalation analysis
    escalation_topics: list[str] = Field(description="Topics that triggered escalations")
    human_actions: dict[str, int] = Field(
        description="Count of each HumanAction type"
    )
    context_patterns: list[str] = Field(
        description="Common context humans added"
    )

    # Recommendations
    recommendations: list[ImprovementRecommendation]

    model_config = {"frozen": True}
```

---

## Execution Models

### ExecutionTask

Task extracted from tasks.md for specialist agents.

```python
class TaskType(str, Enum):
    """Type of execution task."""
    TEST = "test"
    IMPLEMENTATION = "implementation"
    INFRASTRUCTURE = "infrastructure"
    REVIEW = "review"

class ExecutionTask(BaseModel):
    """Task for specialist execution agents."""

    id: str = Field(description="Task ID from tasks.md (e.g., 'T001')")
    task_type: TaskType
    title: str
    description: str
    acceptance_criteria: list[str]
    dependencies: list[str] = Field(
        default_factory=list,
        description="Task IDs this depends on"
    )
    dependency_outputs: dict[str, str] = Field(
        default_factory=dict,
        description="File paths from completed dependencies"
    )
    assigned_agent: str = Field(description="Agent role to execute")
    file_scope: list[str] = Field(description="Directories agent can write to")
    feature_id: str

    model_config = {"frozen": True}
```

---

### ExecutionResult

Result from executing a task.

```python
class ExecutionStatus(str, Enum):
    """Status of task execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SCOPE_VIOLATION = "scope_violation"

class ExecutionResult(BaseModel):
    """Result from executing a task."""

    task_id: str
    status: ExecutionStatus
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float
    error_message: str | None = None

    model_config = {"frozen": True}
```

---

## Handles and Status

### AgentHandle

Handle for tracking dispatched agents.

```python
class AgentStatus(str, Enum):
    """Status of a dispatched agent."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class AgentHandle(BaseModel):
    """Handle for a dispatched agent."""

    id: str = Field(description="Handle ID (UUID)")
    agent_role: str
    agent_name: str
    status: AgentStatus = AgentStatus.PENDING
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    pid: int | None = Field(default=None, description="Process ID if CLI-based")

    model_config = {"frozen": False}  # Status updates
```

---

## File Locations

| Model | Persisted To |
|-------|--------------|
| RoutingConfig | `config/routing.yaml` |
| QALogEntry | `logs/qa/{feature_id}.jsonl` |
| RetroReport | `logs/retro/{feature_id}.json` |
| EscalationRequest | `state/escalations/{id}.json` |
| OrchestratorState | `.plans/{issue}/state.json` (existing) |
