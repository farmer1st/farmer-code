# KR-001: Route Question to Knowledge Agent

**Actor**: @baron (PM Agent running SpecKit)
**Goal**: Route a question to the appropriate knowledge agent based on topic and configuration
**Preconditions**:
- Routing configuration loaded from `config/routing.yaml`
- Knowledge agents defined (architect, product, etc.)
- Question has valid topic and suggested_target

**Priority**: P1 (Critical - Foundation for Knowledge Router)

## Steps

### 1. Create Question with Topic and Target
- **Action**: @baron creates a `Question` with topic, suggested_target, and context
- **Expected outcome**: Question is validated with Pydantic
- **System behavior**:
  - Validates topic is lowercase alphanumeric with underscores
  - Validates question text is 10-2000 characters
  - Validates feature_id matches pattern (e.g., `005-user-auth`)

### 2. Resolve Target Agent
- **Action**: Call `route_question()` on `KnowledgeRouterService`
- **Expected outcome**: Agent is resolved based on:
  1. If `suggested_target` is HUMAN, route to human
  2. Check topic overrides in config
  3. Check agent topic mappings
  4. Default to human if no match
- **System behavior**:
  - Priority: HUMAN target > topic override > agent mapping > default human
  - Returns agent ID (e.g., 'architect', 'product', 'human')

### 3. Dispatch to Agent (if not human)
- **Action**: `AgentDispatcher` spawns Claude CLI with question prompt
- **Expected outcome**: Agent receives question as structured JSON prompt
- **System behavior**:
  - Builds prompt from template with question context
  - Spawns `claude --model {model} --print -p "{prompt}"`
  - Returns `AgentHandle` with status tracking

### 4. Return Handle for Tracking
- **Action**: Return `AgentHandle` to caller
- **Expected outcome**: Handle contains agent info and status
- **System behavior**:
  - Handle includes: id, agent_role, agent_name, status, question_id
  - Status starts as PENDING, updates to RUNNING, then COMPLETED/FAILED

## Success Criteria

- Question routed to correct agent based on topic
- Topic override takes precedence over agent mapping
- HUMAN suggested_target always routes to human
- Unknown topics default to human
- AgentHandle returned with correct metadata
- Question prompt includes all context

## E2E Test Coverage

- **Test file**: `tests/e2e/knowledge_router/test_route_question.py`
- **Journey marker**: `@pytest.mark.journey("KR-001")`
- **Test class**: `TestRouteQuestionE2E`
- **Covered steps**: All 4 steps (100% coverage)
- **Test status**: Passing

### Test Implementation Details

```python
@pytest.mark.journey("KR-001")
class TestRouteQuestionE2E:
    def test_route_question_to_architect_e2e(self):
        """Routes authentication topic to architect agent."""

    def test_route_question_with_override_e2e(self):
        """Topic override routes budget questions to human."""
```

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Unknown topic | Routes to human (default) | `test_router.py::test_unknown_topic_routes_to_human` |
| HUMAN suggested_target | Routes to human | `test_router.py::test_human_target_always_routes_to_human` |
| Topic override | Override takes precedence | `test_route_question.py::test_route_question_with_override_e2e` |
| Invalid question | `ValidationError` raised | `test_models_question.py` |

## Related Journeys

- **KR-002**: Validate Answer Confidence (next step after agent responds)
- **KR-003**: Escalate to Human (if answer confidence is low)
- **KR-004**: Log Q&A Exchange (logs all interactions)

## Implementation References

- **Spec**: `specs/004-knowledge-router/spec.md` (User Story 1)
- **Config**: `config/routing.yaml`
- **Code**: `src/knowledge_router/router.py::route_question()`
- **Dispatcher**: `src/knowledge_router/dispatcher.py::AgentDispatcher`
- **Tests**: `tests/e2e/knowledge_router/test_route_question.py`

## Notes

- Questions are immutable (frozen Pydantic models)
- Agent dispatch uses Claude CLI subprocess
- Human routing returns handle without subprocess spawn
- Topic matching is case-sensitive lowercase
