# Quickstart: Knowledge Router

**Feature**: 004-knowledge-router
**Date**: 2026-01-03

This guide validates the Knowledge Router implementation end-to-end.

## Prerequisites

1. **Claude CLI installed**:
   ```bash
   claude --version
   # Should output version info
   ```

2. **Python environment**:
   ```bash
   uv run python --version
   # Python 3.11+
   ```

3. **Feature dependencies installed**:
   ```bash
   uv pip install -e .
   ```

## Step 1: Configure Routing

Create or verify `config/routing.yaml`:

```yaml
defaults:
  confidence_threshold: 80
  timeout_seconds: 120
  model: sonnet

agents:
  architect:
    name: "@duc"
    topics:
      - authentication
      - api_design
      - database
    model: opus

  product:
    name: "@veuve"
    topics:
      - scope
      - priority

overrides:
  security:
    agent: architect
    confidence_threshold: 95
  budget:
    agent: human
```

## Step 2: Test Question Routing

```python
from knowledge_router import KnowledgeRouterService
from knowledge_router.models import Question

# Initialize service
router = KnowledgeRouterService.from_config("config/routing.yaml")

# Create a question
question = Question(
    id="test-001",
    topic="authentication",
    suggested_target="architect",
    question="What authentication method should we use?",
    context="Building a REST API for mobile and web clients",
    feature_id="005-user-auth",
)

# Route the question
handle = router.route_question(question)
print(f"Question routed to: {handle.agent_role}")
# Expected: architect
```

## Step 3: Test Confidence Validation

```python
from knowledge_router.models import Answer, AnswerValidationResult

# Simulate high-confidence answer
high_conf_answer = Answer(
    question_id="test-001",
    answered_by="@duc",
    answer="Use OAuth2 with JWT tokens",
    rationale="Industry standard for mobile/web APIs",
    confidence=92,
    model_used="opus",
    duration_seconds=3.5,
)

# Validate
result = router.submit_answer(high_conf_answer)
print(f"Outcome: {result.outcome}")
# Expected: ValidationOutcome.ACCEPTED

# Simulate low-confidence answer
low_conf_answer = Answer(
    question_id="test-002",
    answered_by="@duc",
    answer="Maybe use Redis?",
    rationale="Common choice but uncertain about requirements",
    confidence=65,
    uncertainty_reasons=["No infrastructure details", "Unknown scale"],
    model_used="sonnet",
    duration_seconds=2.1,
)

result = router.submit_answer(low_conf_answer)
print(f"Outcome: {result.outcome}")
# Expected: ValidationOutcome.ESCALATE
```

## Step 4: Test Human Escalation

```python
from knowledge_router.models import EscalationRequest, HumanResponse, HumanAction

# Create escalation from low-confidence answer
escalation = router.escalate_to_human(low_conf_answer, question)
print(f"Escalation ID: {escalation.id}")
print(f"GitHub comment would be posted to issue")

# Simulate human response
human_response = HumanResponse(
    escalation_id=escalation.id,
    action=HumanAction.CONFIRM,
    responder="octocat",
    github_comment_id=12345,
)

# Process response
final_answer = router.handle_human_response(escalation, human_response)
print(f"Final answer validated by: {final_answer.validated_by}")
# Expected: "human"
```

## Step 5: Test Q&A Logging

```python
# Retrieve log for feature
qa_log = router.get_qa_log("005-user-auth")
print(f"Total questions: {len(qa_log)}")

for entry in qa_log:
    print(f"  Q: {entry.question.topic} -> {entry.answer.confidence}% confidence")
```

## Step 6: Test Execution Dispatch

```python
from knowledge_router.models import ExecutionTask, TaskType

# Create a test task
task = ExecutionTask(
    id="T001",
    task_type=TaskType.TEST,
    title="Write auth tests",
    description="Create unit tests for OAuth2 authentication",
    acceptance_criteria=["Tests for login flow", "Tests for token refresh"],
    assigned_agent="qa",
    file_scope=["tests/"],
    feature_id="005-user-auth",
)

# Dispatch
handle = router.dispatch_task(task, "qa")
print(f"Task dispatched to: {handle.agent_name}")
# Expected: @marie
```

## Step 7: Generate Retro Report

```python
# After feature completion
retro = router.generate_retro("005-user-auth")

print(f"Total questions: {retro.total_questions}")
print(f"High confidence: {retro.high_confidence_count}")
print(f"Escalated: {retro.escalated_count}")
print(f"Average confidence: {retro.average_confidence:.1f}%")

for rec in retro.recommendations:
    print(f"  [{rec.priority}] {rec.category}: {rec.description}")
```

## Running the Full Test Suite

```bash
# Run all tests
uv run pytest tests/ -v

# Run only knowledge router tests
uv run pytest tests/unit/knowledge_router/ -v
uv run pytest tests/integration/knowledge_router/ -v

# Run with coverage
uv run pytest tests/ --cov=src/knowledge_router --cov-report=term-missing
```

## Expected E2E Flow

```
1. @baron generates question during /speckit.specify
2. Knowledge Router routes to @duc (topic: authentication)
3. @duc answers with 92% confidence
4. Router accepts (>= 80% threshold)
5. Answer returned to @baron
6. @baron writes to spec.md
7. All Q&A logged for retrospective
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Claude CLI not found | Install: `npm install -g @anthropic-ai/claude-code` |
| Low confidence on all questions | Check agent prompt template |
| Escalation not posting | Verify GitHub credentials in `.env` |
| Routing to wrong agent | Check `config/routing.yaml` topic mappings |

## Success Criteria

- [ ] Questions route to correct agent based on topic
- [ ] High-confidence answers (≥80%) are accepted
- [ ] Low-confidence answers (<80%) trigger escalation
- [ ] Human can confirm, correct, or add context
- [ ] All Q&A is logged without data loss
- [ ] Retro report identifies improvement opportunities
