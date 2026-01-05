# Contract: GitHubService Public Interface

**Version**: 1.0.0
**Date**: 2026-01-02
**Purpose**: Define the public programmatic interface for GitHub operations

## Overview

The `GitHubService` class is the main entry point for all GitHub operations. It provides a high-level, type-safe interface for the orchestrator to manage issues, comments, labels, and pull requests.

**Design Principles**:
- Synchronous interface (orchestrator calls directly)
- Type-safe with Pydantic models
- Meaningful exceptions for error handling
- Structured logging for all operations
- Retry logic built-in (3 attempts, 1s delay)

---

## Class Definition

### GitHubService

**Module**: `github_integration.service`
**Responsibility**: Coordinate GitHub operations with authentication and error handling

```python
class GitHubService:
    """
    Main service interface for GitHub operations.

    Handles GitHub App authentication, API calls, retry logic,
    and error handling for the Farmer Code orchestrator.
    """

    def __init__(
        self,
        app_id: int,
        installation_id: int,
        private_key_path: str,
        repository: str
    ):
        """
        Initialize GitHub service.

        Args:
            app_id: GitHub App ID (2578431)
            installation_id: GitHub App installation ID (102211688)
            private_key_path: Path to PEM file (from GITHUB_APP_PRIVATE_KEY_PATH env var)
            repository: Target repository in format "owner/repo" (farmer1st/farmcode-tests)

        Raises:
            FileNotFoundError: If PEM file doesn't exist
            PermissionError: If PEM file permissions != 600
            ValueError: If repository format invalid

        Example:
            service = GitHubService(
                app_id=2578431,
                installation_id=102211688,
                private_key_path=os.getenv("GITHUB_APP_PRIVATE_KEY_PATH"),
                repository="farmer1st/farmcode-tests"
            )
        """
```

---

## Issue Operations

### create_issue

Create a new GitHub issue.

**Signature**:
```python
def create_issue(
    self,
    title: str,
    body: Optional[str] = None,
    labels: list[str] = None,
    assignees: list[str] = None
) -> Issue:
    """
    Create a new issue in the configured repository.

    Args:
        title: Issue title (1-256 characters, required)
        body: Issue description in markdown (optional)
        labels: List of label names to apply (will auto-create if missing)
        assignees: List of usernames to assign (optional)

    Returns:
        Issue: Created issue with all metadata

    Raises:
        ValidationError: If title is empty or too long
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        issue = service.create_issue(
            title="Add user authentication",
            body="Implement OAuth2 flow",
            labels=["status:new", "priority:p1"],
            assignees=["duc"]
        )
        print(f"Created issue #{issue.number}")
    """
```

**Contract Tests**:
- Title validation (empty, too long)
- Label auto-creation (new labels created automatically)
- Assignee validation (invalid usernames raise error)
- Return value includes issue number, URL, timestamps

---

### get_issue

Retrieve issue details by number.

**Signature**:
```python
def get_issue(self, issue_number: int) -> Issue:
    """
    Get issue details by issue number.

    Args:
        issue_number: Issue number (must be positive integer)

    Returns:
        Issue: Issue with current state, labels, assignees, metadata

    Raises:
        ValueError: If issue_number <= 0
        ResourceNotFoundError: If issue doesn't exist
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        issue = service.get_issue(42)
        print(f"Issue state: {issue.state}")
        print(f"Labels: {', '.join(issue.labels)}")
    """
```

**Contract Tests**:
- Valid issue number returns Issue object
- Invalid issue number raises ResourceNotFoundError
- Returned issue has all required fields populated

---

### list_issues

List issues with optional filtering.

**Signature**:
```python
def list_issues(
    self,
    state: str = "open",
    labels: Optional[list[str]] = None
) -> list[Issue]:
    """
    List issues in the repository with optional filtering.

    Args:
        state: Filter by state ("open", "closed", or "all"), defaults to "open"
        labels: Filter by label names (AND logic - issue must have all), optional

    Returns:
        list[Issue]: List of matching issues (may be empty)

    Raises:
        ValueError: If state not in ["open", "closed", "all"]
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        open_issues = service.list_issues(state="open")
        print(f"Found {len(open_issues)} open issues")

        priority_issues = service.list_issues(
            state="open",
            labels=["priority:p1"]
        )
    """
```

**Contract Tests**:
- State filtering (open/closed/all)
- Label filtering (AND logic, empty if no matches)
- Empty list returned when no issues match
- Pagination handled transparently (returns all matching issues)

---

## Comment Operations

### create_comment

Post a comment to an issue.

**Signature**:
```python
def create_comment(self, issue_number: int, body: str) -> Comment:
    """
    Post a comment to an issue.

    Args:
        issue_number: Target issue number (must be positive)
        body: Comment text in markdown (may include emoji, @mentions)

    Returns:
        Comment: Created comment with ID, timestamp, URL

    Raises:
        ValueError: If body is empty or issue_number <= 0
        ResourceNotFoundError: If issue doesn't exist
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        comment = service.create_comment(
            issue_number=42,
            body="✅ Backend plan complete. @baron"
        )
        print(f"Posted comment: {comment.url}")
    """
```

**Contract Tests**:
- Empty body raises ValidationError
- Emoji preserved in body (✅, ❓, 📝)
- @mentions preserved
- Returns comment with ID and timestamp

---

### get_comments

Retrieve all comments on an issue.

**Signature**:
```python
def get_comments(self, issue_number: int) -> list[Comment]:
    """
    Get all comments on an issue in chronological order.

    Args:
        issue_number: Issue number (must be positive)

    Returns:
        list[Comment]: All comments sorted by creation time (oldest first)
                       Empty list if no comments

    Raises:
        ValueError: If issue_number <= 0
        ResourceNotFoundError: If issue doesn't exist
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        comments = service.get_comments(42)
        for comment in comments:
            if comment.contains_signal("✅"):
                print(f"Completion signal from {comment.author}")
    """
```

**Contract Tests**:
- Returns empty list when no comments
- Comments ordered chronologically (oldest first)
- All comment fields populated (id, author, body, timestamp)

---

### get_comments_since

Retrieve comments posted after a specific timestamp (for polling).

**Signature**:
```python
def get_comments_since(
    self,
    issue_number: int,
    since: datetime
) -> list[Comment]:
    """
    Get comments posted after a specific timestamp.

    Used for incremental polling - only fetch new comments since last check.

    Args:
        issue_number: Issue number (must be positive)
        since: Timestamp to filter from (UTC timezone required)

    Returns:
        list[Comment]: New comments posted after `since` timestamp
                       Empty list if no new comments

    Raises:
        ValueError: If issue_number <= 0 or since not timezone-aware
        ResourceNotFoundError: If issue doesn't exist
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        from datetime import datetime, timezone

        last_check = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
        new_comments = service.get_comments_since(42, last_check)
        print(f"Found {len(new_comments)} new comments")
    """
```

**Contract Tests**:
- Returns only comments after timestamp
- Returns empty list if no new comments
- Raises ValueError if timestamp not timezone-aware
- Handles edge case: comment created exactly at timestamp (included or excluded?)

---

## Label Operations

### add_labels

Add one or more labels to an issue.

**Signature**:
```python
def add_labels(self, issue_number: int, labels: list[str]) -> None:
    """
    Add labels to an issue. Auto-creates labels that don't exist.

    Args:
        issue_number: Target issue number (must be positive)
        labels: List of label names to add (non-empty)

    Raises:
        ValueError: If labels list is empty or issue_number <= 0
        ResourceNotFoundError: If issue doesn't exist
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Note:
        If a label doesn't exist in the repository, it will be created
        automatically with default color #EDEDED (light gray).

    Example:
        service.add_labels(42, ["status:specs-ready", "priority:p1"])
        # If "priority:p1" doesn't exist, it's created automatically
    """
```

**Contract Tests**:
- Multiple labels added in one call
- Non-existent labels auto-created with color EDEDED
- Empty labels list raises ValueError
- Idempotent: adding same label twice has no effect

---

### remove_labels

Remove one or more labels from an issue.

**Signature**:
```python
def remove_labels(self, issue_number: int, labels: list[str]) -> None:
    """
    Remove labels from an issue.

    Args:
        issue_number: Target issue number (must be positive)
        labels: List of label names to remove (non-empty)

    Raises:
        ValueError: If labels list is empty or issue_number <= 0
        ResourceNotFoundError: If issue doesn't exist
        ValidationError: If label not on issue (silently ignored)
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        service.remove_labels(42, ["status:new"])
    """
```

**Contract Tests**:
- Multiple labels removed in one call
- Removing non-existent label silently ignored (idempotent)
- Empty labels list raises ValueError

---

## Pull Request Operations

### create_pull_request

Create a pull request.

**Signature**:
```python
def create_pull_request(
    self,
    title: str,
    head: str,
    base: str = "main",
    body: Optional[str] = None
) -> PullRequest:
    """
    Create a pull request.

    Args:
        title: PR title (1-256 characters, required)
        head: Head branch name (e.g., "123-add-auth")
        base: Base branch name (defaults to "main")
        body: PR description in markdown (optional, may include "Closes #N")

    Returns:
        PullRequest: Created PR with number, URL, linked issues

    Raises:
        ValidationError: If title empty/too long or branch names invalid
        ResourceNotFoundError: If head or base branch doesn't exist
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Note:
        If body contains "Closes #123", the PR will be automatically linked
        to issue #123 by GitHub.

    Example:
        pr = service.create_pull_request(
            title="Add user authentication",
            head="123-add-auth",
            base="main",
            body="Closes #42\n\nImplements OAuth2 flow"
        )
        print(f"Created PR #{pr.number}")
        print(f"Linked to issues: {pr.linked_issues}")
    """
```

**Contract Tests**:
- Title validation (empty, too long)
- Branch validation (invalid characters)
- Auto-linking with "Closes #N" syntax
- Non-existent branch raises ResourceNotFoundError

---

### get_pull_request

Retrieve pull request details by number.

**Signature**:
```python
def get_pull_request(self, pr_number: int) -> PullRequest:
    """
    Get pull request details by PR number.

    Args:
        pr_number: PR number (must be positive integer)

    Returns:
        PullRequest: PR with state, branches, linked issues, merge status

    Raises:
        ValueError: If pr_number <= 0
        ResourceNotFoundError: If PR doesn't exist
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        pr = service.get_pull_request(15)
        print(f"PR state: {pr.state}, merged: {pr.merged}")
        print(f"Base: {pr.base_branch} ← Head: {pr.head_branch}")
    """
```

**Contract Tests**:
- Valid PR number returns PullRequest object
- Invalid PR number raises ResourceNotFoundError
- Merged PR has merged=True, state="closed"

---

### list_pull_requests

List pull requests with optional state filtering.

**Signature**:
```python
def list_pull_requests(self, state: str = "open") -> list[PullRequest]:
    """
    List pull requests in the repository.

    Args:
        state: Filter by state ("open", "closed", or "all"), defaults to "open"

    Returns:
        list[PullRequest]: List of matching PRs (may be empty)

    Raises:
        ValueError: If state not in ["open", "closed", "all"]
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        open_prs = service.list_pull_requests(state="open")
        print(f"Found {len(open_prs)} open PRs")
    """
```

**Contract Tests**:
- State filtering works correctly
- Empty list returned when no PRs match
- Pagination handled transparently

---

## Error Handling

All methods follow consistent error handling:

1. **Input Validation** (via Pydantic):
   - Raises `ValidationError` with specific field errors
   - Example: "title: String should have at least 1 characters"

2. **Retry Logic** (built-in):
   - Retries 3 times with 1-second delay for network/server errors
   - Logs each retry attempt at WARNING level
   - Raises `ServerError` after 3 failed attempts

3. **Rate Limiting**:
   - Detects rate limit via response headers
   - Raises `RateLimitExceeded` with wait_seconds attribute
   - Caller decides whether to wait or fail

4. **Authentication**:
   - Raises `AuthenticationError` if GitHub App auth fails
   - Logs full error with stack trace at ERROR level

5. **Resource Not Found**:
   - Raises `ResourceNotFoundError` for 404 responses
   - Includes resource type and identifier in error message

**Exception Hierarchy**:
```python
GitHubAPIError (base)
├── AuthenticationError
├── ResourceNotFoundError
├── ValidationError
├── RateLimitExceeded
└── ServerError
```

**Example Error Handling**:
```python
try:
    issue = service.create_issue(title="Test")
except ValidationError as e:
    print(f"Validation failed: {e}")
except RateLimitExceeded as e:
    print(f"Rate limited. Wait {e.wait_seconds}s")
    time.sleep(e.wait_seconds)
    # Retry
except ResourceNotFoundError:
    print("Issue not found")
except ServerError:
    print("GitHub API unavailable after retries")
```

---

## Logging

All operations log to stdout as structured JSON (per FR-017):

**INFO Level** (successful operations):
```json
{
  "timestamp": "2026-01-02T10:30:00.123Z",
  "level": "INFO",
  "message": "Created GitHub issue",
  "context": {
    "method": "create_issue",
    "issue_number": 42,
    "repository": "farmer1st/farmcode-tests",
    "duration_ms": 234
  }
}
```

**ERROR Level** (failures):
```json
{
  "timestamp": "2026-01-02T10:30:00.123Z",
  "level": "ERROR",
  "message": "GitHub API request failed",
  "context": {
    "method": "GET",
    "url": "/repos/farmer1st/farmcode-tests/issues/999",
    "status_code": 404,
    "error": "Not Found",
    "attempt": 1
  }
}
```

---

## Thread Safety

**Not thread-safe**. The service maintains internal state (auth token cache) that is not protected by locks. Orchestrator should use a single instance per thread or implement external synchronization.

---

## Performance Guarantees

Per success criteria (SC-001 to SC-007):

- Issue create/retrieve: <2 seconds (SC-001)
- Comment retrieval (100 comments): <1 second (SC-003)
- 95% success rate under normal GitHub availability (SC-005)
- 100% meaningful error messages (SC-007)

---

## Future Compatibility

Interface designed for stability:
- Methods return Pydantic models (backward compatible additions)
- Optional parameters have defaults (safe to add new params)
- Exceptions inherit from base GitHubAPIError (catch all via base)
- Versioning will use semantic versioning if breaking changes needed

