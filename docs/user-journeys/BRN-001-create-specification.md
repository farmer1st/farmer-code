# BRN-001: Create Feature Specification Autonomously

**Actor**: Developer / Product Owner
**Goal**: Create a complete feature specification (spec.md) from a natural language description
**Preconditions**:
- Baron agent is configured in `.claude/agents/baron/`
- Claude CLI is installed and authenticated
- `.specify/templates/spec-template.md` exists
- `.specify/memory/constitution.md` is accessible

**Priority**: P1 (Critical - Entry point for speckit workflow)

## Steps

### 1. Dispatch Baron with Feature Description
- **Action**: Call `BaronDispatcher.dispatch_specify()` with `SpecifyRequest`
- **Expected outcome**: Baron agent is launched with the specify workflow
- **System behavior**:
  - Builds dispatch prompt from `SpecifyRequest`
  - Loads system prompt from `.claude/agents/baron/system-prompt.md`
  - Executes via `ClaudeCLIRunner`

### 2. Baron Creates Feature Directory
- **Action**: Baron runs `.specify/scripts/bash/create-new-feature.sh`
- **Expected outcome**: Feature directory created with format `specs/NNN-short-name/`
- **System behavior**:
  - Determines next feature number (or uses provided number)
  - Creates branch with feature ID
  - Initializes spec.md from template

### 3. Baron Loads Templates and Constitution
- **Action**: Baron reads spec-template.md and constitution.md
- **Expected outcome**: Template structure and principles available for spec generation
- **System behavior**:
  - Reads `.specify/templates/spec-template.md`
  - Reads `.specify/memory/constitution.md`
  - Extracts mandatory sections and quality requirements

### 4. Baron Analyzes Feature Description
- **Action**: Baron parses natural language description to extract requirements
- **Expected outcome**: Key concepts identified (actors, actions, data, constraints)
- **System behavior**:
  - Identifies user roles and personas
  - Extracts functional requirements
  - Determines success criteria
  - Notes assumptions and dependencies

### 5. Baron Consults Experts (Optional)
- **Action**: Baron uses `ask_expert` MCP tool for clarification
- **Expected outcome**: Domain-specific questions answered by appropriate expert
- **System behavior**:
  - Routes architecture questions to @duc
  - Routes product questions to @veuve
  - Routes testing questions to @marie
  - Maximum 3 expert consultations per workflow

### 6. Baron Fills Template Sections
- **Action**: Baron populates all mandatory spec sections
- **Expected outcome**: Complete spec.md with all required sections
- **System behavior**:
  - Fills Summary, User Stories, Functional Requirements
  - Fills Success Criteria, Scope, Assumptions
  - Marks unclear items with `[NEEDS CLARIFICATION]`
  - Limits clarification markers to 3 maximum

### 7. Baron Creates Quality Checklist
- **Action**: Baron generates requirements checklist
- **Expected outcome**: Checklist file created at `specs/NNN-feature/checklists/requirements.md`
- **System behavior**:
  - Validates spec against quality criteria
  - Documents content quality checks
  - Tracks requirement completeness

### 8. Baron Returns Structured Result
- **Action**: Baron outputs JSON result between markers
- **Expected outcome**: `SpecifyResult` parsed with success status, paths, and metadata
- **System behavior**:
  - Outputs `<!-- BARON_RESULT_START -->` marker
  - Outputs JSON with success, spec_path, feature_id, branch_name, duration_seconds
  - Outputs `<!-- BARON_RESULT_END -->` marker

## Success Criteria

- **Spec Created**: `spec.md` exists in feature directory
- **Mandatory Sections Complete**: Summary, User Stories, Functional Requirements, Success Criteria all populated
- **Branch Created**: Git branch exists with feature ID format
- **Checklist Generated**: `checklists/requirements.md` exists
- **Result Parseable**: JSON result between markers can be parsed into `SpecifyResult`
- **Duration Tracked**: `duration_seconds` accurately reflects execution time

## Integration Test Coverage

- **Test file**: `tests/integration/baron/test_specify_workflow.py`
- **Journey marker**: `@pytest.mark.journey("BRN-001")`
- **Test class**: `TestSpecifyWorkflow`
- **Covered steps**: Steps 1, 6, 7, 8 (mocked runner)
- **Real agent test**: `TestSpecifyWorkflowRealAgent` (manual execution)

### Test Implementation Details

```python
@pytest.mark.journey("BRN-001")
@pytest.mark.integration
def test_dispatch_specify_creates_spec(dispatcher, mock_runner):
    """
    Integration test for BRN-001: Create Feature Specification

    Verifies:
    - Step 1: Dispatch with feature description
    - Step 8: Result parsing with spec path and feature ID
    """
    request = SpecifyRequest(
        feature_description="Add user authentication with OAuth2 support"
    )
    result = dispatcher.dispatch_specify(request)

    assert result.success is True
    assert result.spec_path is not None
```

## Error Scenarios

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Empty description | `ValidationError` raised | `tests/unit/orchestrator/test_baron_models.py` |
| Template not found | `success: false` with error message | `tests/integration/baron/test_specify_workflow.py` |
| CLI not available | `DispatchError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |
| Missing result markers | `ParseError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |
| Invalid JSON in result | `ParseError` raised | `tests/unit/orchestrator/test_baron_dispatch.py` |

## Related Journeys

- **BRN-002**: Generate Implementation Plan (next step after spec creation)
- **BRN-003**: Generate Task List (follows plan generation)
- **BRN-006**: Constitution Compliance (applies to all Baron workflows)

## Implementation References

- **Spec**: `specs/006-baron-pm-agent/spec.md` (User Story 1)
- **Plan**: `specs/006-baron-pm-agent/plan.md`
- **Agent Config**: `.claude/agents/baron/config.yaml`
- **System Prompt**: `.claude/agents/baron/system-prompt.md`
- **Workflow**: `.claude/agents/baron/workflows/specify.md`
- **Dispatcher**: `src/orchestrator/baron_dispatch.py::dispatch_specify()`
- **Models**: `src/orchestrator/baron_models.py`
- **Unit Tests**: `tests/unit/orchestrator/test_baron_dispatch.py`
- **Integration Tests**: `tests/integration/baron/test_specify_workflow.py`

## Notes

- This journey represents the entry point for the speckit workflow
- Baron is a Claude Agent SDK agent, not a Python library
- Most logic resides in prompts (`.claude/agents/baron/`)
- Python code is minimal (BaronDispatcher only)
- Expert consultation limited to 3 questions per workflow
- Clarification markers limited to 3 per spec
- Average execution time: 30-60 seconds (varies by feature complexity)
