# Research: GitHub Integration Core

**Phase**: 0 (Outline & Research)
**Date**: 2026-01-02
**Purpose**: Resolve technical unknowns and establish best practices before design phase

## Overview

This document captures research decisions for implementing a GitHub integration service using GitHub App authentication, REST API operations, and polling-based monitoring.

---

## Research Topics

### 1. GitHub App Authentication

**Decision**: Use PyJWT for JWT generation + requests library for GitHub API calls

**Rationale**:
- GitHub Apps require JWT authentication signed with private key (PEM file)
- Workflow: Generate JWT → Exchange for installation access token → Use token for API calls
- PyJWT is lightweight, well-maintained, and handles RS256 signing required by GitHub
- Installation access tokens expire after 1 hour, so caching with refresh is needed
- PyGithub library doesn't support GitHub App auth well (designed for PATs)

**Alternatives Considered**:
- **PyGithub**: Popular but limited GitHub App support, designed for PAT auth
- **ghapi**: Lightweight but manual auth handling required, less documentation
- **github3.py**: Good GitHub App support but heavier dependency, more complex API
- **Direct requests**: Feasible but reinventing the wheel for API pagination, rate limits

**Implementation Approach**:
- Use PyJWT to generate JWT from PEM file
- POST to /app/installations/{id}/access_tokens to get installation token
- Cache token with expiration tracking (refresh 5 min before expiry)
- Use requests library with installation token for all GitHub API calls
- Implement custom client wrapper for consistent error handling and retry logic

**References**:
- [GitHub Apps Authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

---

### 2. GitHub REST API Client Strategy

**Decision**: Build custom lightweight wrapper around requests library

**Rationale**:
- Full control over retry logic (3 retries, 1s delay - spec requirement)
- Custom error handling and logging (structured JSON)
- No need for full-featured GitHub library (only need issues, comments, labels, PRs)
- Easier to test with mocked responses
- No dependency on external library's GitHub App auth implementation
- Can optimize for our specific use case (polling comments, creating issues)

**Alternatives Considered**:
- **PyGithub**: Feature-rich but heavy, poor GitHub App support, opinionated retry logic
- **ghapi**: Fast but less mature, documentation gaps
- **github3.py**: Complete but overkill for our needs, steep learning curve

**Implementation Approach**:
- GitHubClient class wraps requests with auth token injection
- Methods: create_issue, get_issue, list_issues, create_comment, get_comments, add_label, remove_label, create_pr, get_pr
- Built-in pagination handling (follow 'next' links)
- Rate limit header inspection (X-RateLimit-Remaining, X-RateLimit-Reset)
- Fixed retry: 3 attempts, 1s delay, only for 5xx and network errors
- Structured logging for all requests (method, url, status, duration)

**API Endpoints Used**:
```
POST   /repos/{owner}/{repo}/issues
GET    /repos/{owner}/{repo}/issues/{number}
GET    /repos/{owner}/{repo}/issues
POST   /repos/{owner}/{repo}/issues/{number}/comments
GET    /repos/{owner}/{repo}/issues/{number}/comments
POST   /repos/{owner}/{repo}/issues/{number}/labels
DELETE /repos/{owner}/{repo}/issues/{number}/labels/{name}
POST   /repos/{owner}/{repo}/pulls
GET    /repos/{owner}/{repo}/pulls/{number}
GET    /repos/{owner}/{repo}/pulls
```

**References**:
- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [Rate Limiting](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)

---

### 3. Polling Mechanism Design

**Decision**: Simple interval-based polling with timestamp tracking

**Rationale**:
- Spec requires 5-10 second polling interval
- Comments endpoint supports `since` parameter (ISO 8601 timestamp)
- Track last_checked_at per issue to avoid re-processing old comments
- No need for complex change detection - timestamp filtering is sufficient
- Orchestrator will manage polling loop (not this service's responsibility)

**Alternatives Considered**:
- **Event-driven polling**: More complex, no benefit without webhooks
- **Long polling**: GitHub API doesn't support, would require custom server
- **ETag caching**: Reduces bandwidth but adds complexity, not needed for MVP

**Implementation Approach**:
- Service provides `get_comments_since(issue_number, since_timestamp)` method
- Caller (orchestrator) tracks last poll time per issue
- Returns only new comments posted after `since` timestamp
- If no new comments, returns empty list (not an error)
- Polling frequency controlled by caller (5-10s recommended)

**Example Usage**:
```python
last_check = datetime.now(timezone.utc)
while True:
    new_comments = service.get_comments_since(issue_num, last_check)
    for comment in new_comments:
        process_agent_signal(comment)
    last_check = datetime.now(timezone.utc)
    time.sleep(10)  # 10 second interval
```

**References**:
- [List issue comments API](https://docs.github.com/en/rest/issues/comments#list-issue-comments)

---

### 4. Error Handling and Retry Strategy

**Decision**: Fixed retry with exponential circuit breaker for rate limits

**Rationale**:
- Spec requires 3 retries with 1-second delay for transient errors
- GitHub rate limits need special handling (don't retry immediately)
- Network errors (timeouts, connection refused) should retry
- 4xx errors (validation, not found) should NOT retry
- 5xx errors (server errors) should retry
- Meaningful error messages required per spec

**Error Categories**:
1. **Retriable** (3 attempts, 1s delay):
   - Network errors (ConnectionError, Timeout)
   - 500, 502, 503, 504 (server errors)

2. **Non-retriable** (fail immediately):
   - 400 Bad Request (validation error - return details)
   - 401 Unauthorized (auth failure - check token)
   - 403 Forbidden (permission denied)
   - 404 Not Found (resource doesn't exist)
   - 422 Unprocessable Entity (validation error)

3. **Rate Limit** (403 with X-RateLimit-Remaining: 0):
   - Calculate wait time from X-RateLimit-Reset header
   - Raise RateLimitExceeded with wait_seconds
   - Caller decides whether to wait or fail

**Custom Exceptions**:
```python
class GitHubAPIError(Exception): pass
class AuthenticationError(GitHubAPIError): pass
class ResourceNotFoundError(GitHubAPIError): pass
class ValidationError(GitHubAPIError): pass
class RateLimitExceeded(GitHubAPIError): pass
class ServerError(GitHubAPIError): pass
```

**Logging on Errors**:
- ERROR level: Full exception with stack trace
- Include: method, url, status_code, response_body (if not sensitive), attempt_number
- Structured JSON format per constitution

**References**:
- [GitHub API Error Responses](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api)

---

### 5. Structured Logging Implementation

**Decision**: Python logging module with JSON formatter to stdout

**Rationale**:
- Spec requires structured JSON logging to stdout/stderr
- Standard library (no extra dependency)
- Supports multiple log levels (DEBUG, INFO, WARNING, ERROR)
- Easy to integrate with log aggregators (Datadog, CloudWatch) in future
- 12-factor app compliant

**Log Format**:
```json
{
  "timestamp": "2026-01-02T10:30:00.123Z",
  "level": "INFO",
  "message": "GitHub API request completed",
  "context": {
    "method": "POST",
    "url": "/repos/farmer1st/farmcode-tests/issues",
    "status_code": 201,
    "duration_ms": 234,
    "issue_number": 42
  }
}
```

**Log Levels**:
- **DEBUG**: API request/response details (dev only)
- **INFO**: Successful operations (issue created, comments retrieved)
- **WARNING**: Retries, deprecated features, slow operations (>1s)
- **ERROR**: Failures requiring attention (auth errors, server errors)

**What NOT to Log**:
- ❌ PEM file contents
- ❌ JWT tokens or installation tokens
- ❌ Full issue/comment bodies (may contain sensitive data)
- ✅ Issue numbers, labels, authors, timestamps
- ✅ HTTP status codes, error messages, retry counts

**Implementation**:
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, 'context'):
            log_obj['context'] = record.context
        return json.dumps(log_obj)

logger = logging.getLogger('github_integration')
handler = logging.StreamHandler()  # stdout
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

**References**:
- [Python logging](https://docs.python.org/3/library/logging.html)
- [12-Factor App Logs](https://12factor.net/logs)

---

### 6. Label Auto-Creation Strategy

**Decision**: Attempt to apply label, create if 422 error received

**Rationale**:
- GitHub returns 422 Unprocessable Entity if label doesn't exist
- Can detect this error and create label, then retry application
- Default color: #EDEDED (light gray, neutral)
- Simpler than pre-checking label existence (saves API call)
- Optimistic approach (assume label exists, handle failure)

**Implementation Approach**:
```python
def add_label(issue_number, label_name):
    try:
        # Attempt to add label
        response = POST /issues/{issue_number}/labels
    except ValidationError as e:
        if "Label does not exist" in str(e):
            # Create label with default color
            POST /repos/{owner}/{repo}/labels
              { "name": label_name, "color": "EDEDED" }
            # Retry adding label to issue
            POST /issues/{issue_number}/labels
        else:
            raise
```

**Default Label Color**: #EDEDED (light gray) - neutral, non-distracting

**References**:
- [Create label API](https://docs.github.com/en/rest/issues/labels#create-a-label)

---

### 7. Testing Strategy

**Decision**: Three-tier testing (contract, integration, unit)

**Test Layers**:

1. **Contract Tests** (test/contract/):
   - Verify public service interface matches spec
   - Test Pydantic model validation rules
   - Mock GitHub API responses
   - Fast, no network calls
   - Run on every commit

2. **Integration Tests** (test/integration/):
   - Live GitHub API calls to farmer1st/farmcode-tests repo
   - Create/retrieve/update actual issues, comments, labels
   - Verify end-to-end workflows
   - Clean up test data after each test
   - Requires GITHUB_APP_PRIVATE_KEY_PATH env var
   - Run on demand (not in CI, due to rate limits)

3. **Unit Tests** (test/unit/):
   - Test authentication logic (JWT generation)
   - Test retry logic (with mocked failures)
   - Test error handling edge cases
   - Test logging output format
   - Fast, isolated, no external dependencies

**Test Data Management**:
- Use issue labels like `test-issue` to identify test artifacts
- Clean up in teardown: close issues, delete labels
- farmer1st/farmcode-tests repo dedicated to testing (spec requirement)

**Mocking Strategy**:
- Use `responses` library to mock requests
- Mock GitHub API responses for contract/unit tests
- Use fixtures for common test data (sample issues, comments)

**References**:
- [pytest documentation](https://docs.pytest.org/)
- [responses library](https://github.com/getsentry/responses)

---

## Technology Stack Summary

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Language | Python 3.11+ | Constitution requirement |
| Package Manager | uv | Constitution requirement (fast, reliable) |
| Linter | ruff | Constitution requirement |
| Type Checker | mypy | Constitution standard |
| Testing | pytest | Constitution requirement |
| JWT | PyJWT | Lightweight, RS256 support |
| HTTP Client | requests | Standard library alternative, widely used |
| Validation | Pydantic v2 | Constitution requirement |
| Logging | stdlib logging | 12-factor compliant, JSON formatter |
| Secrets | python-dotenv | Load .env files per constitution |

**Dependencies** (pyproject.toml):
```toml
[project]
name = "github-integration"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pyjwt[crypto]>=2.8.0",
    "requests>=2.31.0",
    "pydantic>=2.5.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "responses>=0.24.0",
    "mypy>=1.7.0",
    "ruff>=0.1.8",
]
```

---

## Open Questions Resolved

All technical unknowns from plan.md Technical Context have been researched and resolved. No NEEDS CLARIFICATION markers remain.

