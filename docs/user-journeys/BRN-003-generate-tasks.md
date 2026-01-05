# BRN-003: Generate Task List

**Actor**: Developer / Tech Lead
**Goal**: Create an actionable, dependency-ordered task list from an implementation plan
**Preconditions**:
- Baron agent is configured in `.claude/agents/baron/`
- Claude CLI is installed and authenticated
- plan.md exists for the feature
- spec.md, data-model.md, and contracts/ exist
- `.specify/templates/tasks-template.md` exists
- `.specify/memory/constitution.md` is accessible

**Priority**: P1 (Critical - Required for implementation phase)

## Steps

### 1. Dispatch Baron with Plan Path
- **Action**: Call `BaronDispatcher.dispatch_tasks()` with `TasksRequest`
- **Expected outcome**: Baron agent is launched with the tasks workflow
- **System behavior**:
  - Builds dispatch prompt from `TasksRequest` including plan_path
  - Loads system prompt from `.claude/agents/baron/system-prompt.md`
  - Executes via `ClaudeCLIRunner`

### 2. Baron Reads Plan and Supporting Documents
- **Action**: Baron reads plan.md, spec.md, data-model.md, contracts/
- **Expected outcome**: Full context loaded for task generation
- **System behavior**:
  - Reads plan.md with technical context
  - Reads spec.md for user stories
  - Reads data-model.md for entity definitions
  - Reads contracts/ for API endpoints

### 3. Baron Loads Tasks Template
- **Action**: Baron reads `.specify/templates/tasks-template.md`
- **Expected outcome**: Template structure understood
- **System behavior**:
  - Parses template sections
  - Notes format requirements (IDs, markers)

### 4. Baron Loads Constitution
- **Action**: Baron reads `.specify/memory/constitution.md`
- **Expected outcome**: TDD requirements identified
- **System behavior**:
  - Reads Principle I: Test-First Development
  - Enforces tests before implementation ordering

### 5. Baron Extracts User Stories
- **Action**: Baron identifies user stories from spec.md
- **Expected outcome**: User stories mapped to journey IDs
- **System behavior**:
  - Lists all user stories with IDs
  - Maps to journey IDs from plan.md
  - Groups related functionality

### 6. Baron Generates Task List
- **Action**: Baron creates tasks organized by user story and phase
- **Expected outcome**: Complete task list with TDD ordering
- **System behavior**:
  - Creates setup tasks
  - Creates test tasks BEFORE implementation (TDD)
  - Creates implementation tasks
  - Creates integration test tasks
  - Creates documentation tasks

### 7. Baron Applies Parallel Markers
- **Action**: Baron marks tasks that can run in parallel
- **Expected outcome**: `[P]` markers on independent tasks
- **System behavior**:
  - Identifies tasks with no dependencies
  - Marks with `[P]` for parallel execution

### 8. Baron Adds Checkpoints
- **Action**: Baron adds phase boundaries and checkpoints
- **Expected outcome**: Clear phase structure with completion criteria
- **System behavior**:
  - Groups tasks into phases
  - Adds checkpoint markers
  - Notes dependencies between phases

### 9. Baron Returns Structured Result
- **Action**: Baron outputs JSON result between markers
- **Expected outcome**: `TasksResult` parsed with task counts
- **System behavior**:
  - Counts total tasks
  - Counts test tasks (for TDD verification)
  - Outputs duration

## Success Criteria

- **Tasks Created**: `tasks.md` exists with all required sections
- **TDD Ordering**: Test tasks appear before implementation tasks
- **User Stories Covered**: Every user story has associated tasks
- **Parallel Markers**: Independent tasks marked with `[P]`
- **Journey IDs**: Integration tests reference journey IDs
- **Documentation Tasks**: User journey docs included
- **Result Parseable**: JSON result can be parsed into `TasksResult`
- **Test Count Positive**: `test_count > 0` (TDD requirement)

## Integration Test Coverage

- **Test file**: `tests/integration/baron/test_tasks_workflow.py`
- **Journey marker**: `@pytest.mark.journey("BRN-003")`
- **Test class**: `TestTasksWorkflow`
- **Covered steps**: Steps 1, 2, 6, 9 (mocked runner)
- **Real agent test**: `TestTasksWorkflowRealAgent` (manual execution)

### Test Implementation Details

```python
@pytest.mark.journey("BRN-003")
@pytest.mark.integration
def test_dispatch_tasks_verifies_tdd_ordering(dispatcher, mock_runner):
    """
    Integration test for BRN-003: Generate Task List

    Verifies:
    - Step 6: Tasks generated with TDD ordering
    - Step 9: Result includes test_count for TDD verification
    """
    request = TasksRequest(plan_path=Path("specs/009-test-feature/plan.md"))
    result = dispatcher.dispatch_tasks(request)

    assert result.success is True
    assert result.test_count > 0, "TDD requires test tasks"
    assert result.test_count <= result.task_count
```

## Error Scenarios

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Plan not found | `success: false` with error | `tests/integration/baron/test_tasks_workflow.py` |
| CLI not available | `DispatchError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |
| Missing result markers | `ParseError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |
| Invalid JSON in result | `ParseError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |

## Related Journeys

- **BRN-001**: Create Feature Specification (prerequisite)
- **BRN-002**: Generate Implementation Plan (prerequisite)
- **BRN-006**: Constitution Compliance (TDD enforcement)

## Implementation References

- **Spec**: `specs/006-baron-pm-agent/spec.md` (User Story 3)
- **Plan**: `specs/006-baron-pm-agent/plan.md`
- **Agent Config**: `.claude/agents/baron/config.yaml`
- **System Prompt**: `.claude/agents/baron/system-prompt.md`
- **Workflow**: `.claude/agents/baron/workflows/tasks.md`
- **Example**: `.claude/agents/baron/examples/tasks-prompt.md`
- **Dispatcher**: `src/orchestrator/baron_dispatch.py::dispatch_tasks()`
- **Models**: `src/orchestrator/baron_models.py`
- **Unit Tests**: `tests/unit/orchestrator/test_baron_dispatch.py`
- **Integration Tests**: `tests/integration/baron/test_tasks_workflow.py`

## Notes

- This journey follows BRN-002 (plan generation)
- Final step before implementation begins
- TDD enforcement is non-negotiable per Constitution Principle I
- Test tasks must appear before implementation tasks
- `test_count` should be 30-50% of `task_count` for good TDD coverage
- Average execution time: 30-60 seconds
- Large features may have 50+ tasks
