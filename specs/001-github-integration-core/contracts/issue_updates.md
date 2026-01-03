# Contract: Issue Update and Close Operations

**Version**: 1.0.0
**Date**: 2026-01-02
**Purpose**: Define API for updating and closing GitHub issues (test cleanup)

## Overview

These operations are needed for test cleanup and issue lifecycle management.
They were not in the original spec but are required for proper test hygiene.

---

## update_issue

Update an existing issue's title, body, state, labels, or assignees.

**Signature**:
```python
def update_issue(
    self,
    issue_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    labels: Optional[list[str]] = None,
    assignees: Optional[list[str]] = None,
) -> Issue:
    """
    Update an existing issue.

    Args:
        issue_number: Issue number (must be positive)
        title: New title (1-256 chars, optional)
        body: New body (optional)
        state: New state ("open" or "closed", optional)
        labels: New labels list (replaces existing, optional)
        assignees: New assignees list (replaces existing, optional)

    Returns:
        Issue: Updated issue with new values

    Raises:
        ValueError: If issue_number <= 0 or state invalid
        ResourceNotFoundError: If issue doesn't exist
        ValidationError: If title too long/empty
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        # Close an issue
        issue = service.update_issue(42, state="closed")

        # Update title and body
        issue = service.update_issue(
            42,
            title="New title",
            body="Updated description"
        )
    """
```

**Contract Tests**:
- Update title only
- Update state only (open → closed)
- Update multiple fields at once
- Empty update (no fields) returns unchanged issue
- Invalid state raises ValueError
- Non-existent issue raises ResourceNotFoundError

---

## close_issue

Convenience method to close an issue.

**Signature**:
```python
def close_issue(self, issue_number: int) -> Issue:
    """
    Close an issue (convenience method).

    Args:
        issue_number: Issue number (must be positive)

    Returns:
        Issue: Closed issue with state="closed"

    Raises:
        ValueError: If issue_number <= 0
        ResourceNotFoundError: If issue doesn't exist
        AuthenticationError: If GitHub App auth fails
        RateLimitExceeded: If GitHub rate limit hit
        ServerError: If GitHub API returns 5xx after retries

    Example:
        issue = service.close_issue(42)
        assert issue.state == "closed"
    """
```

**Implementation Note**: This is a wrapper around `update_issue(issue_number, state="closed")`.

**Contract Tests**:
- Close open issue (state changes to "closed")
- Close already-closed issue (idempotent)
- Non-existent issue raises ResourceNotFoundError

---

## GitHub API Mapping

### PATCH /repos/{owner}/{repo}/issues/{issue_number}

Request body (all fields optional):
```json
{
  "title": "New title",
  "body": "New body",
  "state": "closed",
  "labels": ["label1", "label2"],
  "assignees": ["user1"]
}
```

Response: Updated issue object (same as GET /issues/{number})

---

## Test Cleanup Strategy

Use these methods for test cleanup with label-based filtering:

1. **Tag test issues** with `test:automated` label on creation
2. **Close after test** using `close_issue()` in fixture teardown
3. **Bulk cleanup** (if needed):
   ```bash
   gh issue list -R farmer1st/farmcode-tests \
     -L test:automated --state open --json number -q '.[].number' | \
     xargs -I {} gh issue close {} -R farmer1st/farmcode-tests
   ```

**Important**: Always filter by `--state open` AND `-L test:automated` to avoid processing all issues.
