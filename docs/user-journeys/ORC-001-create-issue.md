# ORC-001: Create Issue for New Feature Request

**Actor**: Product Owner / Development Lead
**Goal**: Create a GitHub issue to track a new feature through the 8-phase SDLC workflow
**Preconditions**:
- GitHub App is installed on target repository
- User has repository access
- `.env` file configured with GitHub App credentials

**Priority**: P1 (Critical - Foundation for entire workflow)

## Steps

### 1. Initialize GitHubService
- **Action**: Instantiate `GitHubService` with App credentials
- **Expected outcome**: Service successfully authenticates with GitHub
- **System behavior**:
  - Validates PEM file exists and has correct permissions (600)
  - Generates JWT for GitHub App authentication
  - Fetches installation access token (cached for 1 hour)

### 2. Create Issue with Required Metadata
- **Action**: Call `create_issue()` with title, body, labels, and assignees
- **Expected outcome**: Issue is created on GitHub with:
  - Unique issue number
  - `state: "open"`
  - Initial label (e.g., `status:new`)
  - Assignment to architect agent (e.g., `@duc`)
- **System behavior**:
  - Validates input with Pydantic (title 1-256 chars, non-empty)
  - Makes POST /repos/{owner}/{repo}/issues API call
  - Handles rate limits and retries (3 attempts, 1s delay)
  - Returns fully populated `Issue` model

### 3. Verify Issue is Retrievable
- **Action**: Fetch issue by number using `get_issue(issue_number)`
- **Expected outcome**: Retrieved issue matches created issue
- **System behavior**:
  - Makes GET /repos/{owner}/{repo}/issues/{number} API call
  - Parses GitHub response into `Issue` model
  - Returns issue with all fields populated

### 4. Verify Issue Appears in Lists
- **Action**: Query issues using `list_issues()` with filters
- **Expected outcome**: Created issue appears in:
  - Open issues list (`state="open"`)
  - Label-filtered lists (`labels=["status:new"]`)
- **System behavior**:
  - Makes GET /repos/{owner}/{repo}/issues API call with query params
  - Handles eventual consistency (may require polling)
  - Returns list of matching issues

## Success Criteria

✅ **Issue Created**: Issue number > 0, state = "open"
✅ **Metadata Populated**: Title, body, labels, assignees all match input
✅ **Retrievable**: `get_issue()` returns identical data
✅ **Indexed**: Issue appears in filtered lists (with eventual consistency handling)
✅ **Persisted**: Issue visible in GitHub web UI
✅ **Logged**: Structured JSON logs capture operation with context

## E2E Test Coverage

- **Test file**: `tests/e2e/test_github_operations.py`
- **Journey marker**: `@pytest.mark.journey("ORC-001")`
- **Test method**: `TestFullIssueLifecycle::test_full_issue_lifecycle`
- **Covered steps**: All 4 steps (100% coverage)
- **Test status**: ✅ Passing (as of 2026-01-02)

### Test Implementation Details

```python
@pytest.mark.e2e
@pytest.mark.journey("ORC-001")
def test_full_issue_lifecycle(service, auto_cleanup_issue):
    """
    E2E test for ORC-001: Create Issue for New Feature Request

    Verifies:
    - Step 1: Service initialization (via fixture)
    - Step 2: Issue creation with metadata
    - Step 3: Issue retrieval by number
    - Step 4: Issue appears in lists (with polling for eventual consistency)
    """
    # Test implementation validates all success criteria
```

### Eventual Consistency Handling

GitHub API has eventual consistency for list/filter operations. The test uses polling helpers:
- `wait_for_issue_in_list()`: Polls until issue appears in list (10s timeout, 0.5s interval)
- Ensures test reliability despite GitHub's indexing delay

## Error Scenarios Tested

| Scenario | Expected Behavior | Test Location |
|----------|------------------|---------------|
| Empty title | `ValidationError` raised | `tests/contract/test_service_interface.py::test_create_issue_with_missing_required_field` |
| Title too long (>256 chars) | `ValidationError` raised | Same as above |
| Invalid credentials | `AuthenticationError` raised | `tests/unit/test_auth.py` (future) |
| Rate limit exceeded | `RateLimitExceeded` raised, retry after delay | `tests/unit/test_client.py` (future) |
| Network error | Retry 3 times with 1s delay | `tests/integration/test_service_integration.py` |

## Related Journeys

- **ORC-005**: Complete 8-Phase SDLC Workflow (includes this journey as Phase 1)
- **ORC-002**: Agent Provides Feedback via Comment (next step after issue creation)
- **ORC-003**: Progress Issue Through Workflow Phases (state transitions)

## Implementation References

- **Spec**: `specs/001-github-integration-core/spec.md` (User Story 1)
- **Contract**: `specs/001-github-integration-core/contracts/github_service.md`
- **Code**: `src/github_integration/service.py::create_issue()`
- **Tests**: `tests/e2e/test_github_operations.py::test_full_issue_lifecycle()`

## Notes

- This journey represents Phase 1 of the 8-phase SDLC workflow
- Labels used: `status:new` (initial state)
- Typical assignee: `@duc` (architecture agent)
- Average execution time: ~2 seconds (including GitHub API calls)
- Cleanup: Test issues tagged with `test:automated` are closed automatically
