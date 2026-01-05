# Module Interactions

This document describes how Farmer Code modules interact with each other, including dependencies, interfaces, and data flow.

## Module Dependency Matrix

| Module | Depends On | Depended By |
|--------|------------|-------------|
| `github_integration` | (external: PyGithub) | `orchestrator`, `knowledge_router` |
| `worktree_manager` | (external: git) | `orchestrator` |
| `orchestrator` | `github_integration`, `worktree_manager` | (top-level) |
| `knowledge_router` | `github_integration` (optional) | `orchestrator` |

## Interaction Patterns

### 1. Orchestrator → GitHub Integration

The orchestrator uses GitHub Integration for all GitHub operations:

```python
# Issue creation during Phase 1
from github_integration import GitHubService

github = GitHubService.from_env()
issue = github.issues.create(
    title="Feature: Add authentication",
    body=spec_content,
    labels=["enhancement", "status:new"]
)

# Label sync during state transitions
github.issues.update_labels(
    issue_number=123,
    labels=["status:phase-2"]
)

# Comment posting for agent feedback
github.issues.add_comment(
    issue_number=123,
    body="Agent completed architecture review."
)
```

**Data Exchange**:
- Input: Issue metadata, comment content, label lists
- Output: Issue objects, comment objects, operation status

### 2. Orchestrator → Worktree Manager

The orchestrator uses Worktree Manager for isolated development environments:

```python
from worktree_manager import WorktreeService, CreateWorktreeRequest

worktree = WorktreeService(repo_path)

# Create feature worktree
result = worktree.create_worktree(
    CreateWorktreeRequest(
        branch_name="123-add-auth",
        worktree_path=Path("/worktrees/123-add-auth")
    )
)

# Initialize plans directory
worktree.init_plans(result.worktree_path)

# Cleanup after completion
worktree.delete_worktree(result.worktree_path)
```

**Data Exchange**:
- Input: Branch names, paths, commit messages
- Output: Worktree info, operation results

### 3. Orchestrator → Knowledge Router

The orchestrator routes questions to appropriate agents:

```python
from knowledge_router import KnowledgeRouter, Question, QuestionTarget

router = KnowledgeRouter(config_path)

# Route architecture question
question = Question(
    topic="authentication",
    suggested_target=QuestionTarget.ARCHITECT,
    question="Which auth method should we use?",
    feature_id="005-auth"
)

handle = router.route_question(question)
answer = router.submit_answer(handle, question)

if not answer.is_high_confidence:
    escalation = router.escalate_to_human(question, validation)
```

**Data Exchange**:
- Input: Questions with topic and target
- Output: Answers with confidence scores, escalation requests

### 4. Knowledge Router → GitHub Integration (Optional)

Knowledge Router can post escalation comments to GitHub:

```python
# Format escalation for GitHub
comment_body = router.format_escalation_comment(escalation)

# Post to issue (via orchestrator or directly)
github.issues.add_comment(
    issue_number=feature_issue_number,
    body=comment_body
)
```

## Data Flow Diagrams

### Phase 1 Execution

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant SM as StateMachine
    participant GI as GitHubIntegration
    participant WM as WorktreeManager

    O->>SM: transition(IDLE → PHASE_1)
    SM-->>O: StateTransition(success)

    O->>GI: create_issue(title, body, labels)
    GI-->>O: Issue(number=123)

    O->>WM: create_worktree("123-feature")
    WM-->>O: OperationResult(success)

    O->>WM: init_plans(worktree_path)
    WM-->>O: OperationResult(success)

    O->>GI: update_labels(["status:phase-1"])
    GI-->>O: success

    O->>SM: transition(PHASE_1 → PHASE_2)
    SM-->>O: StateTransition(success)
```

### Question Routing with Escalation

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant KR as KnowledgeRouter
    participant D as Dispatcher
    participant V as Validator
    participant E as EscalationHandler
    participant L as QALogger

    O->>KR: route_question(question)
    KR->>D: dispatch(agent_config, question)
    D-->>KR: AgentHandle

    KR->>D: parse_answer(handle)
    D-->>KR: Answer(confidence=65)

    KR->>V: validate(answer)
    V-->>KR: ValidationResult(ESCALATE)

    KR->>E: create_escalation(question, answer)
    E-->>KR: EscalationRequest

    Note over KR,E: Human reviews and responds

    KR->>E: process_response(escalation, response)
    E-->>KR: EscalationResult(final_answer)

    KR->>L: log_exchange(entry)
    L-->>KR: success

    KR-->>O: final_answer
```

## Interface Contracts

### GitHub Integration Interface

```python
class GitHubService:
    """GitHub API wrapper."""

    @classmethod
    def from_env(cls) -> GitHubService: ...

    @property
    def issues(self) -> IssueService: ...

    @property
    def comments(self) -> CommentService: ...

class IssueService:
    def create(self, title: str, body: str, labels: list[str]) -> Issue: ...
    def update(self, issue_number: int, **kwargs) -> Issue: ...
    def update_labels(self, issue_number: int, labels: list[str]) -> None: ...
    def add_comment(self, issue_number: int, body: str) -> Comment: ...
```

### Worktree Manager Interface

```python
class WorktreeService:
    """Git worktree management."""

    def __init__(self, repo_path: Path): ...

    def create_worktree(self, request: CreateWorktreeRequest) -> OperationResult: ...
    def delete_worktree(self, path: Path) -> OperationResult: ...
    def init_plans(self, worktree_path: Path) -> OperationResult: ...
    def commit_and_push(self, request: CommitRequest) -> OperationResult: ...
```

### Knowledge Router Interface

```python
class KnowledgeRouter:
    """Question routing and validation."""

    def __init__(self, config_path: Path): ...

    def route_question(self, question: Question) -> AgentHandle: ...
    def submit_answer(self, handle: AgentHandle, question: Question) -> Answer: ...
    def validate_answer(self, answer: Answer) -> AnswerValidationResult: ...
    def escalate_to_human(self, question: Question, validation: AnswerValidationResult) -> EscalationRequest: ...
    def handle_human_response(self, escalation: EscalationRequest, response: HumanResponse) -> EscalationResult: ...
```

## Error Propagation

Errors flow upward through the module hierarchy:

```
External System Error
    ↓
Module-Specific Error (e.g., AgentTimeoutError)
    ↓
Orchestrator catches and handles
    ↓
State machine may transition to error state
    ↓
User notified via GitHub comment or UI
```

### Error Types by Module

| Module | Error Types |
|--------|-------------|
| `github_integration` | `GitHubAPIError`, `IssueNotFoundError`, `AuthenticationError` |
| `worktree_manager` | `BranchExistsError`, `WorktreeExistsError`, `GitCommandError` |
| `orchestrator` | `InvalidStateTransition`, `PhaseExecutionError`, `PollTimeoutError` |
| `knowledge_router` | `RoutingError`, `AgentDispatchError`, `AgentTimeoutError`, `EscalationError` |

## Thread Safety

- **State Machine**: Single-threaded, file-locked during writes
- **GitHub Operations**: Thread-safe (PyGithub handles internally)
- **Git Operations**: Process-based isolation via subprocess
- **Q&A Logging**: Append-only, one writer per feature

## Configuration Sharing

Modules read configuration from:

1. **Environment Variables**: API keys, credentials (`python-dotenv`)
2. **YAML Files**: Routing rules, agent definitions (`config/routing.yaml`)
3. **JSON Files**: State persistence (`.plans/{issue}/state.json`)
