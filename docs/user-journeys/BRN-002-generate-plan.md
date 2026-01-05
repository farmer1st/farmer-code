# BRN-002: Generate Implementation Plan

**Actor**: Developer / Architect
**Goal**: Create a complete implementation plan with design artifacts from a feature specification
**Preconditions**:
- Baron agent is configured in `.claude/agents/baron/`
- Claude CLI is installed and authenticated
- spec.md exists for the feature
- `.specify/templates/plan-template.md` exists
- `.specify/memory/constitution.md` is accessible

**Priority**: P1 (Critical - Required before task generation)

## Steps

### 1. Dispatch Baron with Spec Path
- **Action**: Call `BaronDispatcher.dispatch_plan()` with `PlanRequest`
- **Expected outcome**: Baron agent is launched with the plan workflow
- **System behavior**:
  - Builds dispatch prompt from `PlanRequest` including spec_path
  - Loads system prompt from `.claude/agents/baron/system-prompt.md`
  - Executes via `ClaudeCLIRunner`

### 2. Baron Reads Specification
- **Action**: Baron reads spec.md from the provided path
- **Expected outcome**: Full spec loaded with requirements and success criteria
- **System behavior**:
  - Reads spec.md file
  - Extracts summary, user stories, functional requirements
  - Identifies assumptions and constraints

### 3. Baron Runs Setup Script
- **Action**: Baron executes `.specify/scripts/bash/setup-plan.sh --json`
- **Expected outcome**: Plan directory prepared with template
- **System behavior**:
  - Creates plan.md from template
  - Sets up artifact directories
  - Returns JSON with paths

### 4. Baron Loads Constitution
- **Action**: Baron reads `.specify/memory/constitution.md`
- **Expected outcome**: Constitution principles loaded for compliance checking
- **System behavior**:
  - Reads constitution document
  - Identifies applicable principles (TDD, YAGNI, User Journeys)
  - Prepares constitution check section

### 5. Phase 0: Research
- **Action**: Baron generates research.md to resolve unknowns
- **Expected outcome**: All technology decisions documented with rationale
- **System behavior**:
  - Identifies unknowns from spec (technology, architecture)
  - Consults experts via `ask_expert` MCP tool (max 3 questions)
  - Documents decisions, rationale, and alternatives

### 6. Phase 1: Design Artifacts
- **Action**: Baron generates data-model.md, contracts/, quickstart.md
- **Expected outcome**: Complete design documentation
- **System behavior**:
  - Creates data-model.md with entities and relationships
  - Creates OpenAPI/GraphQL schemas in contracts/
  - Creates quickstart.md with development setup

### 7. Baron Fills Plan Template
- **Action**: Baron completes plan.md with all sections
- **Expected outcome**: Complete implementation plan
- **System behavior**:
  - Fills Technical Context section
  - Fills Constitution Check section
  - Fills User Journey Mapping (REQUIRED per Principle XI)
  - Documents architecture decisions

### 8. Baron Updates Agent Context
- **Action**: Baron runs `.specify/scripts/bash/update-agent-context.sh claude`
- **Expected outcome**: Agent context updated with new technologies
- **System behavior**:
  - Updates `.claude/CLAUDE.md` with technology stack
  - Preserves manual additions

### 9. Baron Returns Structured Result
- **Action**: Baron outputs JSON result between markers
- **Expected outcome**: `PlanResult` parsed with success status, paths, and metadata
- **System behavior**:
  - Outputs `<!-- BARON_RESULT_START -->` marker
  - Outputs JSON with plan_path, research_path, data_model_path, contracts_dir, quickstart_path
  - Outputs `<!-- BARON_RESULT_END -->` marker

## Success Criteria

- **Plan Created**: `plan.md` exists with all required sections
- **Research Complete**: `research.md` documents all technology decisions
- **Data Model Defined**: `data-model.md` defines entities and relationships
- **Contracts Generated**: `contracts/` contains API schemas
- **Quickstart Written**: `quickstart.md` provides development setup
- **Constitution Checked**: Constitution check section is filled
- **User Journeys Mapped**: Each user story has a journey ID
- **Result Parseable**: JSON result can be parsed into `PlanResult`

## Integration Test Coverage

- **Test file**: `tests/integration/baron/test_plan_workflow.py`
- **Journey marker**: `@pytest.mark.journey("BRN-002")`
- **Test class**: `TestPlanWorkflow`
- **Covered steps**: Steps 1, 2, 6, 9 (mocked runner)
- **Real agent test**: `TestPlanWorkflowRealAgent` (manual execution)

### Test Implementation Details

```python
@pytest.mark.journey("BRN-002")
@pytest.mark.integration
def test_dispatch_plan_creates_all_artifacts(dispatcher, mock_runner):
    """
    Integration test for BRN-002: Generate Implementation Plan

    Verifies:
    - Step 1: Dispatch with spec path
    - Step 9: Result parsing with all artifact paths
    """
    request = PlanRequest(spec_path=Path("specs/009-test-feature/spec.md"))
    result = dispatcher.dispatch_plan(request)

    assert result.success is True
    assert result.plan_path is not None
    assert result.research_path is not None
```

## Error Scenarios

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Spec not found | `success: false` with error | `tests/integration/baron/test_plan_workflow.py` |
| CLI not available | `DispatchError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |
| Blocked on escalation | `blocked_on_escalation: true` | `tests/integration/baron/test_plan_workflow.py` |
| Missing result markers | `ParseError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |
| Invalid JSON in result | `ParseError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |

## Related Journeys

- **BRN-001**: Create Feature Specification (prerequisite)
- **BRN-003**: Generate Task List (next step)
- **BRN-004**: Handle Pending Escalations (when blocked)
- **BRN-005**: Expert Consultation Flow (during research phase)
- **BRN-006**: Constitution Compliance (applied throughout)

## Implementation References

- **Spec**: `specs/006-baron-pm-agent/spec.md` (User Story 2)
- **Plan**: `specs/006-baron-pm-agent/plan.md`
- **Agent Config**: `.claude/agents/baron/config.yaml`
- **System Prompt**: `.claude/agents/baron/system-prompt.md`
- **Workflow**: `.claude/agents/baron/workflows/plan.md`
- **Example**: `.claude/agents/baron/examples/plan-prompt.md`
- **Dispatcher**: `src/orchestrator/baron_dispatch.py::dispatch_plan()`
- **Models**: `src/orchestrator/baron_models.py`
- **Unit Tests**: `tests/unit/orchestrator/test_baron_dispatch.py`
- **Integration Tests**: `tests/integration/baron/test_plan_workflow.py`

## Notes

- This journey follows BRN-001 (specification creation)
- Creates multiple design artifacts in Phase 1
- May block on expert consultation (async escalation)
- Constitution check is mandatory per Principle XI
- User journey mapping required for each user story
- Average execution time: 2-5 minutes (varies by complexity)
- Force research flag regenerates research.md even if it exists
