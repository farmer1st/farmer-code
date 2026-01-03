# Quickstart: GitHub Integration Core

**Purpose**: End-to-end validation guide for testing the GitHub Integration service
**Audience**: Developers implementing or testing the service
**Prerequisites**: GitHub App configured, PEM file available, farmer1st/farmcode-tests repo accessible

---

## Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# .env (never commit this file!)
GITHUB_APP_PRIVATE_KEY_PATH=./keys/orchestrator.pem
```

Verify PEM file permissions:
```bash
chmod 600 ./keys/orchestrator.pem
ls -l ./keys/orchestrator.pem
# Should show: -rw------- (permissions 600)
```

### 2. Install Dependencies

Using uv (recommended):
```bash
uv pip install -e ".[dev]"
```

Or using pip:
```bash
pip install -e ".[dev]"
```

### 3. Verify GitHub App Configuration

Check that the GitHub App (ID: 2578431) is installed (Installation ID: 102211688) with these permissions:
- Issues: Read & Write
- Pull Requests: Read & Write
- Repository contents: Read

---

## Quick Validation (5 minutes)

### Test 1: Create an Issue

```python
from github_integration.service import GitHubService
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize service
service = GitHubService(
    app_id=2578431,
    installation_id=102211688,
    private_key_path=os.getenv("GITHUB_APP_PRIVATE_KEY_PATH"),
    repository="farmer1st/farmcode-tests"
)

# Create a test issue
issue = service.create_issue(
    title="[TEST] Quickstart validation",
    body="This is a test issue created by the quickstart guide.",
    labels=["test"]
)

print(f"✅ Created issue #{issue.number}")
print(f"   URL: {issue.url}")
print(f"   State: {issue.state}")
print(f"   Labels: {issue.labels}")
```

**Expected Output**:
```
✅ Created issue #X
   URL: https://github.com/farmer1st/farmcode-tests/issues/X
   State: open
   Labels: ['test']
```

**Verify**: Open the URL in your browser and confirm the issue exists on GitHub.

---

### Test 2: Post a Comment

```python
# Post a comment to the issue created above
comment = service.create_comment(
    issue_number=issue.number,
    body="✅ Comment posted successfully. @baron"
)

print(f"✅ Posted comment {comment.id}")
print(f"   Author: {comment.author}")
print(f"   URL: {comment.url}")
```

**Expected Output**:
```
✅ Posted comment 123456789
   Author: farmcode[bot]
   URL: https://github.com/farmer1st/farmcode-tests/issues/X#issuecomment-123456789
```

**Verify**: Refresh the issue URL and confirm the comment appears.

---

### Test 3: Add Labels

```python
# Add a new label (will auto-create if doesn't exist)
service.add_labels(issue.number, ["status:testing", "priority:p1"])

# Retrieve updated issue
updated_issue = service.get_issue(issue.number)

print(f"✅ Added labels")
print(f"   Current labels: {updated_issue.labels}")
```

**Expected Output**:
```
✅ Added labels
   Current labels: ['test', 'status:testing', 'priority:p1']
```

**Verify**: Refresh the issue and confirm all three labels are visible.

---

### Test 4: Polling Comments

```python
from datetime import datetime, timezone
import time

# Record current time
last_check = datetime.now(timezone.utc)

# Post another comment
service.create_comment(
    issue_number=issue.number,
    body="📝 Testing polling mechanism"
)

# Wait a moment
time.sleep(2)

# Poll for new comments
new_comments = service.get_comments_since(issue.number, last_check)

print(f"✅ Found {len(new_comments)} new comment(s)")
for comment in new_comments:
    print(f"   - {comment.author}: {comment.body[:50]}")
```

**Expected Output**:
```
✅ Found 1 new comment(s)
   - farmcode[bot]: 📝 Testing polling mechanism
```

---

### Test 5: List Issues

```python
# List all open issues with 'test' label
test_issues = service.list_issues(state="open", labels=["test"])

print(f"✅ Found {len(test_issues)} test issue(s)")
for issue in test_issues:
    print(f"   - #{issue.number}: {issue.title}")
```

**Expected Output**:
```
✅ Found X test issue(s)
   - #42: [TEST] Quickstart validation
   - #...
```

---

### Cleanup

```python
# Note: Currently, the service doesn't support closing issues
# This is intentionally out of scope per the spec (only create/read)
# For cleanup, manually close the test issue on GitHub or use gh CLI:

# gh issue close X -R farmer1st/farmcode-tests
```

---

## Full End-to-End Test (15 minutes)

This test validates all four user stories from the spec.

### User Story 1: Create and Track Workflow Issues

```python
# Create issue
issue = service.create_issue(
    title="[E2E TEST] Implement feature X",
    body="Full end-to-end test of GitHub Integration service",
    labels=["status:new"],
    assignees=[]
)
print(f"✅ P1: Created issue #{issue.number}")

# Retrieve issue
retrieved = service.get_issue(issue.number)
assert retrieved.number == issue.number
assert retrieved.title == issue.title
print(f"✅ P1: Retrieved issue #{issue.number}")

# List open issues
open_issues = service.list_issues(state="open")
assert any(i.number == issue.number for i in open_issues)
print(f"✅ P1: Listed {len(open_issues)} open issues")
```

---

### User Story 2: Facilitate Agent Communication

```python
from datetime import datetime, timezone
import time

# Post completion signal
service.create_comment(
    issue_number=issue.number,
    body="✅ Specs complete. @baron"
)
print(f"✅ P2: Posted completion signal")

# Retrieve all comments
all_comments = service.get_comments(issue.number)
assert len(all_comments) >= 1
print(f"✅ P2: Retrieved {len(all_comments)} comment(s)")

# Test incremental polling
last_check = datetime.now(timezone.utc)
time.sleep(1)

service.create_comment(
    issue_number=issue.number,
    body="❓ Question: Should we use GraphQL? @duc"
)

new_comments = service.get_comments_since(issue.number, last_check)
assert len(new_comments) == 1
assert "❓" in new_comments[0].body
print(f"✅ P2: Polling detected {len(new_comments)} new comment(s)")
```

---

### User Story 3: Track Workflow State

```python
# Add workflow labels
service.add_labels(issue.number, ["status:specs-ready"])
print(f"✅ P3: Added workflow label")

# Remove old label
service.remove_labels(issue.number, ["status:new"])
print(f"✅ P3: Removed old label")

# Verify label state
updated = service.get_issue(issue.number)
assert "status:specs-ready" in updated.labels
assert "status:new" not in updated.labels
print(f"✅ P3: Verified labels: {updated.labels}")

# Test auto-creation of non-existent label
service.add_labels(issue.number, ["auto-created-label"])
final = service.get_issue(issue.number)
assert "auto-created-label" in final.labels
print(f"✅ P3: Auto-created new label")
```

---

### User Story 4: Manage Code Review Process

**Note**: This requires a branch with commits. Create manually or use gh CLI:

```bash
# Create a test branch and commit
git checkout -b test-e2e-pr-123
echo "test" > test.txt
git add test.txt
git commit -m "Test commit"
git push origin test-e2e-pr-123
```

Then test PR creation:

```python
# Create pull request
pr = service.create_pull_request(
    title="[E2E TEST] Test PR",
    head="test-e2e-pr-123",
    base="main",
    body=f"Closes #{issue.number}\n\nTest PR for E2E validation"
)
print(f"✅ P4: Created PR #{pr.number}")
print(f"   Linked issues: {pr.linked_issues}")

# Retrieve PR
retrieved_pr = service.get_pull_request(pr.number)
assert retrieved_pr.number == pr.number
assert issue.number in retrieved_pr.linked_issues
print(f"✅ P4: Retrieved PR #{pr.number}")

# List open PRs
open_prs = service.list_pull_requests(state="open")
assert any(p.number == pr.number for p in open_prs)
print(f"✅ P4: Listed {len(open_prs)} open PR(s)")
```

---

## Error Handling Test

Validate that errors are handled correctly:

```python
from github_integration.errors import (
    ResourceNotFoundError,
    ValidationError,
    RateLimitExceeded
)

# Test 1: Resource not found
try:
    service.get_issue(999999)
    assert False, "Should have raised ResourceNotFoundError"
except ResourceNotFoundError as e:
    print(f"✅ ResourceNotFoundError: {e}")

# Test 2: Validation error
try:
    service.create_issue(title="")  # Empty title
    assert False, "Should have raised ValidationError"
except ValidationError as e:
    print(f"✅ ValidationError: {e}")

# Test 3: Invalid state filter
try:
    service.list_issues(state="invalid")
    assert False, "Should have raised ValueError"
except ValueError as e:
    print(f"✅ ValueError: {e}")
```

---

## Logging Validation

Check that structured JSON logs are output:

```python
import json
import sys
from io import StringIO

# Capture stdout
old_stdout = sys.stdout
sys.stdout = log_capture = StringIO()

# Perform operation
issue = service.create_issue(title="Log test")

# Restore stdout
sys.stdout = old_stdout
log_output = log_capture.getvalue()

# Parse JSON logs
for line in log_output.strip().split('\n'):
    if line:
        log_entry = json.loads(line)
        assert 'timestamp' in log_entry
        assert 'level' in log_entry
        assert 'message' in log_entry
        print(f"✅ Structured log: {log_entry['level']} - {log_entry['message']}")
```

---

## Performance Validation

Verify performance requirements from success criteria:

```python
import time

# SC-001: Issue create/retrieve < 2 seconds
start = time.time()
issue = service.create_issue(title="Performance test")
created_issue = service.get_issue(issue.number)
duration = time.time() - start
assert duration < 2.0, f"Too slow: {duration}s"
print(f"✅ SC-001: Issue create/retrieve in {duration:.2f}s")

# SC-003: Comment retrieval < 1 second (up to 100 comments)
# Note: Requires existing issue with comments
start = time.time()
comments = service.get_comments(issue.number)
duration = time.time() - start
assert duration < 1.0, f"Too slow: {duration}s"
print(f"✅ SC-003: Comment retrieval in {duration:.2f}s")

# SC-004: Polling detects comments within 10 seconds
# (Manual test - requires waiting for polling interval)
```

---

## Success Checklist

After running all tests, verify:

- [ ] ✅ Can create issues with title, body, labels
- [ ] ✅ Can retrieve issue by number
- [ ] ✅ Can list issues with filtering (state, labels)
- [ ] ✅ Can post comments with emoji (✅, ❓, 📝)
- [ ] ✅ Can retrieve all comments on an issue
- [ ] ✅ Can poll for new comments since timestamp
- [ ] ✅ Can add labels (auto-creates if missing)
- [ ] ✅ Can remove labels
- [ ] ✅ Can create pull requests
- [ ] ✅ Can retrieve PR details with linked issues
- [ ] ✅ Can list pull requests
- [ ] ✅ Errors are handled with meaningful messages
- [ ] ✅ Logs are structured JSON to stdout
- [ ] ✅ Performance meets success criteria (<2s, <1s)

---

## Troubleshooting

### Authentication Error

**Symptom**: `AuthenticationError: Failed to generate installation access token`

**Solutions**:
1. Check PEM file exists: `ls -l ./keys/orchestrator.pem`
2. Check PEM file permissions: `chmod 600 ./keys/orchestrator.pem`
3. Verify environment variable: `echo $GITHUB_APP_PRIVATE_KEY_PATH`
4. Confirm App ID and Installation ID are correct

### Rate Limit Error

**Symptom**: `RateLimitExceeded: GitHub rate limit exceeded. Wait 3600 seconds`

**Solutions**:
1. Wait for rate limit reset (check error message for seconds)
2. Use authenticated requests (they have higher limits - 5000/hour vs 60/hour)
3. Reduce test frequency
4. Check current rate limit: `curl -H "Authorization: token <token>" https://api.github.com/rate_limit`

### Resource Not Found

**Symptom**: `ResourceNotFoundError: Issue not found`

**Solutions**:
1. Verify issue number exists in repository
2. Check repository name is correct (farmer1st/farmcode-tests)
3. Confirm GitHub App has access to the repository

---

## Next Steps

After completing the quickstart:

1. **Read contracts**: Review `contracts/github_service.md` for full API details
2. **Run full test suite**: `pytest tests/`
3. **Review logging**: Check log output format matches specification
4. **Performance testing**: Run stress tests with 100+ issues/comments
5. **Integration with orchestrator**: Connect service to orchestrator workflow

