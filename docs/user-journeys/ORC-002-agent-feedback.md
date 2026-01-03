# ORC-002: Agent Provides Feedback via Comment

**Actor**: AI Agent (e.g., @duc, @dede, @marie)
**Goal**: Provide feedback on issue progress through structured GitHub comments
**Preconditions**:
- Issue exists (created via ORC-001)
- Agent has completed assigned task
- GitHubService available

**Priority**: P2 (Important for workflow automation)
**Status**: 📋 Planned (not yet implemented)

## Steps

### 1. Agent Completes Task
- **Action**: Agent finishes architecture design, implementation, or review
- **Expected outcome**: Agent has feedback to share with team
- **System behavior**: Agent determines next steps in workflow

### 2. Post Comment with Signal
- **Action**: Call `add_comment(issue_number, body, mentions)` with structured content
- **Expected outcome**: Comment posted to GitHub issue
- **System behavior**:
  - Makes POST /repos/{owner}/{repo}/issues/{issue_number}/comments
  - Comment includes:
    - Status signal (✅ for completion, ❌ for blocking issue)
    - Summary of work completed
    - Mention of next agent (`@agent-name`)
    - Artifacts created (links to files)

### 3. Extract Comment Metadata
- **Action**: Parse comment for signals and mentions
- **Expected outcome**: System extracts:
  - Agent name
  - Status (approved/rejected/question)
  - Mentioned users
  - Linked artifacts
- **System behavior**:
  - Uses `Comment.contains_signal()` helper
  - Uses `Comment.extract_mentions()` helper
  - Updates workflow state based on signals

### 4. Notify Next Agent
- **Action**: GitHub mentions trigger notifications
- **Expected outcome**: Next agent receives notification
- **System behavior**: GitHub sends notification to mentioned user

## Success Criteria

✅ **Comment Posted**: Comment visible on issue
✅ **Signal Recognized**: System detects ✅ or ❌ status
✅ **Mentions Extracted**: All @mentions parsed correctly
✅ **Workflow Progresses**: Next agent notified and begins work
✅ **Audit Trail**: Complete comment history visible

## E2E Test Coverage

- **Test file**: `tests/e2e/test_agent_comments.py` (future)
- **Journey marker**: `@pytest.mark.journey("ORC-002")`
- **Test method**: Not yet implemented
- **Covered steps**: 0/4 (0% coverage)
- **Test status**: ⏳ Not implemented

## Implementation Status

**User Story 2** from `specs/001-github-integration-core/spec.md`:
- Add Comment: `add_comment(issue_number, body, mentions)` → Not implemented
- List Comments: `list_comments(issue_number)` → Not implemented
- Comment Model: `Comment` with `contains_signal()` and `extract_mentions()` → Model exists, methods not implemented

## Example Comment Structure

```markdown
✅ **Architecture specs complete**

Designed system with:
- 3 Pydantic models (Issue, Comment, Label)
- 5 service methods (create_issue, get_issue, list_issues, add_comment, list_comments)
- Contract tests for all operations

**Artifacts**:
- spec.md
- data-model.md
- contracts/github_service.md

Ready for implementation planning. @dede please review and create plan.md
```

## Related Journeys

- **ORC-001**: Create Issue (prerequisite - issue must exist)
- **ORC-003**: Progress Issue Through Workflow Phases (comments trigger state transitions)
- **ORC-005**: Complete SDLC Workflow (comments are Phase 3 communication)

## Implementation References

- **Spec**: `specs/001-github-integration-core/spec.md` (User Story 2)
- **Contract**: `specs/001-github-integration-core/contracts/github_service.md` (future)
- **Model**: `src/github_integration/models.py::Comment`
- **Service**: `src/github_integration/service.py::add_comment()` (future)

## Notes

- Comments use markdown formatting for rich content
- Signals (✅/❌) enable automated workflow detection
- Mentions (@agent-name) create GitHub notifications
- This journey is critical for Phase 3 (Implementation Plans) of ORC-005
