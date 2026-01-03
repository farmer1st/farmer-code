# GitHub Integration Module

**Purpose**: Type-safe GitHub API client for FarmCode orchestrator using GitHub App authentication.

**Version**: 1.0.0 (Feature 001 - GitHub Integration Core)
**Status**: ✅ Implemented (User Story 1 complete, User Stories 2-4 planned)

## Overview

This module provides a clean, type-safe interface for GitHub operations using GitHub App authentication. It powers the FarmCode orchestrator's 8-phase SDLC workflow by managing issues, comments, labels, and pull requests.

## Features

### Implemented (v1.0.0)

- ✅ **Issue Management** (User Story 1)
  - Create issues with metadata
  - Retrieve issues by number
  - List issues with filtering (state, labels)
  - Update issue fields (title, body, state, labels, assignees)
  - Close issues (convenience method)

- ✅ **Authentication**
  - GitHub App JWT generation
  - Installation access token caching (1-hour expiry, 5-min buffer)
  - Automatic token refresh

- ✅ **Error Handling**
  - Structured exception hierarchy
  - Retry logic (3 attempts, 1s delay)
  - Rate limit detection
  - Detailed error messages

- ✅ **Logging**
  - Structured JSON logs
  - Request/response logging
  - Performance metrics

- ✅ **Type Safety**
  - Pydantic models for all data structures
  - Full type hints with mypy strict mode
  - Immutable models

### Planned (Future User Stories)

- 📋 **Comment Management** (User Story 2)
  - Add comments with mentions
  - List issue comments
  - Signal detection (✅/❌)
  - Mention extraction (@agent-name)

- 📋 **Label Management** (User Story 3)
  - Create/update labels
  - Workflow state tracking
  - Label-based queries

- 📋 **Pull Request Management** (User Story 4)
  - Create PRs with issue linking
  - List PRs by linked issues
  - PR metadata retrieval

## Quick Start

### Installation

```bash
# Install dependencies
uv pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your GitHub App credentials
```

### Configuration

Create `.env` file with GitHub App credentials:

```env
GITHUB_APP_ID=2578431
GITHUB_INSTALLATION_ID=102211688
GITHUB_APP_PRIVATE_KEY_PATH=./.keys/orchestrator.pem
GITHUB_REPOSITORY=farmer1st/farmcode-tests
```

### Usage

```python
from github_integration import GitHubService, Issue

# Initialize service
service = GitHubService(
    app_id=2578431,
    installation_id=102211688,
    private_key_path="./.keys/orchestrator.pem",
    repository="farmer1st/farmcode-tests",
)

# Create an issue
issue = service.create_issue(
    title="Add user authentication",
    body="Implement OAuth2 flow",
    labels=["status:new", "priority:p1"],
    assignees=["duc"],
)

print(f"Created issue #{issue.number}: {issue.title}")
# Output: Created issue #42: Add user authentication

# Update issue
updated = service.update_issue(
    issue.number,
    labels=["status:specs-ready"],  # Progress to next phase
)

# Close issue when done
closed = service.close_issue(issue.number)
print(f"Issue #{closed.number} is now {closed.state}")
# Output: Issue #42 is now closed
```

## Architecture

### Components

```
github_integration/
├── service.py        # Main service interface (GitHubService)
├── client.py         # HTTP client with retry logic (GitHubAPIClient)
├── auth.py           # GitHub App authentication (GitHubAppAuth)
├── models.py         # Pydantic models (Issue, Comment, Label, PullRequest)
├── errors.py         # Exception hierarchy
└── logger.py         # Structured JSON logging
```

### Data Flow

```
User Code
   ↓
GitHubService (public API)
   ↓
GitHubAPIClient (HTTP + retry logic)
   ↓
GitHubAppAuth (JWT + token caching)
   ↓
GitHub REST API
```

### Error Handling

All exceptions inherit from `GitHubAPIError`:

```python
from github_integration import ValidationError, ResourceNotFoundError

try:
    issue = service.get_issue(999999)
except ResourceNotFoundError as e:
    print(f"Issue not found: {e.message}")
except ValidationError as e:
    print(f"Invalid input ({e.field}): {e.message}")
```

## API Reference

### GitHubService

Main service interface for GitHub operations.

#### Methods

**create_issue(title, body=None, labels=None, assignees=None) -> Issue**
- Creates new issue in configured repository
- Validates input with Pydantic
- Returns Issue model with all metadata
- Raises: `ValidationError`, `AuthenticationError`, `RateLimitExceeded`

**get_issue(issue_number) -> Issue**
- Retrieves issue by number
- Raises: `ResourceNotFoundError` if issue doesn't exist
- Returns: Full Issue model

**list_issues(state="open", labels=None) -> list[Issue]**
- Lists issues with optional filtering
- `state`: "open", "closed", or "all"
- `labels`: List of label names (AND logic)
- Returns: List of matching issues (may be empty)

**update_issue(issue_number, title=None, body=None, state=None, labels=None, assignees=None) -> Issue**
- Updates issue fields (only provided fields are modified)
- `state`: "open" or "closed"
- Returns: Updated issue
- Raises: `ValidationError`, `ResourceNotFoundError`

**close_issue(issue_number) -> Issue**
- Convenience method to close an issue
- Equivalent to `update_issue(issue_number, state="closed")`
- Returns: Closed issue

### Models

**Issue**
- `number: int` - Issue number (positive)
- `title: str` - Title (1-256 chars)
- `body: Optional[str]` - Description (markdown)
- `state: str` - "open" or "closed"
- `labels: list[str]` - Label names
- `assignees: list[str]` - Assigned usernames
- `created_at: datetime` - Creation timestamp
- `updated_at: datetime` - Last update timestamp
- `repository: str` - Repository (owner/repo)
- `url: str` - GitHub web URL

**Comment, Label, PullRequest** (Planned for User Stories 2-4)
- See `models.py` for model definitions

## Testing

### Test Structure

```
tests/
├── contract/         # Public API interface tests (real auth)
│   ├── test_service_interface.py
│   ├── test_issue_updates.py
│   └── test_models.py
├── integration/      # Component integration (mocked HTTP)
│   └── test_service_integration.py
├── e2e/             # End-to-end workflows (real API)
│   └── test_github_operations.py
└── conftest.py      # Shared fixtures + journey reporting
```

### Running Tests

```bash
# All tests
pytest

# Specific test types
pytest -m contract     # Contract tests only
pytest -m integration  # Integration tests only
pytest -m e2e         # E2E tests only (slow, real API calls)
pytest -m journey     # Journey-tagged tests only

# Specific journey
pytest -m "journey('ORC-001')" -v

# With coverage
pytest --cov=github_integration --cov-report=html
```

### Test Coverage

- **Overall**: 88% code coverage
- **service.py**: 95% coverage
- **models.py**: 100% coverage

### User Journey Coverage

See [docs/user-journeys/README.md](../../docs/user-journeys/README.md) for journey documentation.

Current journey test status:
- **ORC-001**: Create Issue for New Feature Request - ✅ 100% coverage
- **ORC-005**: Complete SDLC Workflow - ✅ 100% coverage (partial)

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITHUB_APP_ID` | Yes | GitHub App ID | `2578431` |
| `GITHUB_INSTALLATION_ID` | Yes | Installation ID | `102211688` |
| `GITHUB_APP_PRIVATE_KEY_PATH` | Yes | Path to PEM file | `./.keys/orchestrator.pem` |
| `GITHUB_REPOSITORY` | Yes | Target repository | `farmer1st/farmcode-tests` |

### PEM File Permissions

The private key file MUST have permissions `600`:

```bash
chmod 600 ./.keys/orchestrator.pem
```

## Performance

| Operation | Target | Actual |
|-----------|--------|--------|
| create_issue | <2s | ~1.5s ✅ |
| get_issue | <1s | ~0.8s ✅ |
| list_issues | <2s | ~1.2s ✅ |
| Authentication token fetch | <1s | ~0.5s ✅ |

## Troubleshooting

### Common Issues

**FileNotFoundError: GitHub App private key not found**
- Verify `GITHUB_APP_PRIVATE_KEY_PATH` points to correct PEM file
- Check file permissions are 600

**AuthenticationError: Failed to authenticate**
- Verify GitHub App ID and Installation ID are correct
- Check PEM file contains valid private key
- Ensure GitHub App is installed on target repository

**RateLimitExceeded**
- GitHub API has rate limits (5000 requests/hour for authenticated apps)
- Retry after delay indicated in error message

**ResourceNotFoundError: Issue not found**
- Verify issue number exists in repository
- Check repository format is correct (owner/repo)

## Contributing

Follow Test-Driven Development (TDD):
1. Write tests first (RED phase)
2. Implement to make tests pass (GREEN phase)
3. Refactor while keeping tests green (REFACTOR phase)

See [constitution](../../.specify/memory/constitution.md) for coding standards.

## License

Internal tool for Farmer1st organization.

## Related Documentation

- [Specification](../../specs/001-github-integration-core/spec.md)
- [Implementation Plan](../../specs/001-github-integration-core/plan.md)
- [API Contracts](../../specs/001-github-integration-core/contracts/)
- [User Journeys](../../docs/user-journeys/)
- [Constitution](../../.specify/memory/constitution.md)
