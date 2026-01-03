# Data Model: GitHub Integration Core

**Phase**: 1 (Design & Contracts)
**Date**: 2026-01-02
**Purpose**: Define Pydantic models for GitHub entities and validation rules

## Overview

This service uses Pydantic v2 models to validate and structure GitHub API data. Models represent GitHub entities (Issue, Comment, Label, PullRequest) with type safety and validation.

**Design Principle**: Models are immutable data transfer objects (DTOs). No business logic, just data structure and validation.

---

## Core Models

### 1. Issue

Represents a GitHub issue with metadata.

**Source**: GitHub Issues API responses
**Validation**: Per FR-002, FR-003 from spec

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class Issue(BaseModel):
    """Represents a GitHub issue"""

    model_config = ConfigDict(frozen=True)  # Immutable

    number: int = Field(..., description="Issue number (unique within repo)", gt=0)
    title: str = Field(..., description="Issue title", min_length=1, max_length=256)
    body: Optional[str] = Field(None, description="Issue description (markdown)")
    state: str = Field(..., description="Issue state", pattern="^(open|closed)$")
    labels: list[str] = Field(default_factory=list, description="Label names")
    assignees: list[str] = Field(default_factory=list, description="Assigned usernames")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")
    repository: str = Field(..., description="Repository full name (owner/repo)")
    url: str = Field(..., description="GitHub issue URL")

    def has_label(self, label_name: str) -> bool:
        """Check if issue has specific label"""
        return label_name in self.labels
```

**Validation Rules**:
- `number`: Must be positive integer
- `title`: Required, 1-256 characters
- `body`: Optional markdown text
- `state`: Must be "open" or "closed"
- `labels`: List of label names (may be empty)
- `assignees`: List of usernames (may be empty)
- `created_at`, `updated_at`: ISO 8601 datetime with timezone
- `repository`: Format "owner/repo"
- `url`: Full GitHub URL

**Example**:
```python
issue = Issue(
    number=42,
    title="Add user authentication",
    body="Implement OAuth2 flow",
    state="open",
    labels=["status:new", "priority:p1"],
    assignees=["duc"],
    created_at=datetime(2026, 1, 2, 10, 30, 0),
    updated_at=datetime(2026, 1, 2, 10, 30, 0),
    repository="farmer1st/farmcode-tests",
    url="https://github.com/farmer1st/farmcode-tests/issues/42"
)
```

---

### 2. Comment

Represents an issue comment.

**Source**: GitHub Issue Comments API responses
**Validation**: Per FR-005, FR-006 from spec

```python
class Comment(BaseModel):
    """Represents a GitHub issue comment"""

    model_config = ConfigDict(frozen=True)  # Immutable

    id: int = Field(..., description="Comment ID (unique globally)", gt=0)
    issue_number: int = Field(..., description="Parent issue number", gt=0)
    author: str = Field(..., description="Comment author username")
    body: str = Field(..., description="Comment text (markdown)", min_length=1)
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    url: str = Field(..., description="GitHub comment URL")

    def contains_signal(self, signal: str) -> bool:
        """Check if comment contains agent signal (e.g., ✅, ❓, 📝)"""
        return signal in self.body

    def extract_mentions(self) -> list[str]:
        """Extract @mentions from comment body"""
        import re
        return re.findall(r'@(\w+)', self.body)
```

**Validation Rules**:
- `id`: Must be positive integer (GitHub comment ID)
- `issue_number`: Must be positive integer
- `author`: Username (may be bot like "github-actions[bot]")
- `body`: Required markdown text (may contain emoji)
- `created_at`: ISO 8601 datetime with timezone
- `url`: Full GitHub comment URL

**Example**:
```python
comment = Comment(
    id=987654321,
    issue_number=42,
    author="dede",
    body="✅ Backend plan complete. @baron",
    created_at=datetime(2026, 1, 2, 11, 15, 0),
    url="https://github.com/farmer1st/farmcode-tests/issues/42#issuecomment-987654321"
)
```

---

### 3. Label

Represents a GitHub label.

**Source**: GitHub Labels API responses
**Validation**: Per FR-008, FR-009 from spec

```python
class Label(BaseModel):
    """Represents a GitHub label"""

    model_config = ConfigDict(frozen=True)  # Immutable

    name: str = Field(..., description="Label name", min_length=1, max_length=50)
    color: str = Field(..., description="Hex color code (without #)", pattern="^[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, description="Label description")

    @property
    def hex_color(self) -> str:
        """Get color with # prefix for display"""
        return f"#{self.color}"
```

**Validation Rules**:
- `name`: Required, 1-50 characters
- `color`: 6-character hex code (e.g., "EDEDED"), no # prefix
- `description`: Optional descriptive text

**Example**:
```python
label = Label(
    name="status:specs-ready",
    color="EDEDED",
    description="Specifications approved and ready for planning"
)
```

**Default Label for Auto-Creation** (from clarifications):
- Name: As requested
- Color: "EDEDED" (light gray)
- Description: None (optional)

---

### 4. PullRequest

Represents a GitHub pull request.

**Source**: GitHub Pull Requests API responses
**Validation**: Per FR-010, FR-011 from spec

```python
class PullRequest(BaseModel):
    """Represents a GitHub pull request"""

    model_config = ConfigDict(frozen=True)  # Immutable

    number: int = Field(..., description="PR number (unique within repo)", gt=0)
    title: str = Field(..., description="PR title", min_length=1, max_length=256)
    body: Optional[str] = Field(None, description="PR description (markdown)")
    state: str = Field(..., description="PR state", pattern="^(open|closed)$")
    merged: bool = Field(..., description="Whether PR is merged")
    base_branch: str = Field(..., description="Base branch name (e.g., main)")
    head_branch: str = Field(..., description="Head branch name (e.g., 123-add-auth)")
    linked_issues: list[int] = Field(default_factory=list, description="Linked issue numbers")
    url: str = Field(..., description="GitHub PR URL")

    def is_linked_to(self, issue_number: int) -> bool:
        """Check if PR is linked to specific issue"""
        return issue_number in self.linked_issues
```

**Validation Rules**:
- `number`: Must be positive integer
- `title`: Required, 1-256 characters
- `body`: Optional markdown text
- `state`: Must be "open" or "closed"
- `merged`: Boolean (can be closed without merging)
- `base_branch`: Branch name (typically "main")
- `head_branch`: Branch name (e.g., "123-feature-name")
- `linked_issues`: List of issue numbers extracted from "Closes #123" syntax
- `url`: Full GitHub PR URL

**Example**:
```python
pr = PullRequest(
    number=15,
    title="Add user authentication",
    body="Closes #42\n\nImplements OAuth2 flow",
    state="open",
    merged=False,
    base_branch="main",
    head_branch="123-add-auth",
    linked_issues=[42],
    url="https://github.com/farmer1st/farmcode-tests/pull/15"
)
```

---

## Request Models

Input validation for service operations.

### CreateIssueRequest

```python
class CreateIssueRequest(BaseModel):
    """Request to create a new issue"""

    title: str = Field(..., description="Issue title", min_length=1, max_length=256)
    body: Optional[str] = Field(None, description="Issue description")
    labels: list[str] = Field(default_factory=list, description="Initial labels")
    assignees: list[str] = Field(default_factory=list, description="Assignees")
```

### CreateCommentRequest

```python
class CreateCommentRequest(BaseModel):
    """Request to create a comment"""

    body: str = Field(..., description="Comment text", min_length=1)
```

### CreatePullRequestRequest

```python
class CreatePullRequestRequest(BaseModel):
    """Request to create a pull request"""

    title: str = Field(..., description="PR title", min_length=1, max_length=256)
    body: Optional[str] = Field(None, description="PR description")
    base: str = Field(..., description="Base branch", pattern="^[a-zA-Z0-9/_-]+$")
    head: str = Field(..., description="Head branch", pattern="^[a-zA-Z0-9/_-]+$")
```

---

## Response Models

Wrapper for operation results with error handling.

### OperationResult

```python
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class OperationResult(BaseModel, Generic[T]):
    """Generic result wrapper for service operations"""

    success: bool = Field(..., description="Whether operation succeeded")
    data: Optional[T] = Field(None, description="Result data if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code for client handling")

    @classmethod
    def ok(cls, data: T) -> "OperationResult[T]":
        """Create successful result"""
        return cls(success=True, data=data, error=None, error_code=None)

    @classmethod
    def fail(cls, error: str, error_code: str) -> "OperationResult[T]":
        """Create failed result"""
        return cls(success=False, data=None, error=error, error_code=error_code)
```

**Example Usage**:
```python
# Success
result = OperationResult.ok(issue)

# Failure
result = OperationResult.fail(
    error="Issue not found",
    error_code="RESOURCE_NOT_FOUND"
)
```

---

## Entity Relationships

```
Issue (1) ─── (N) Comment
  │
  └─── (N) Label
  │
  └─── (0..1) PullRequest
```

**Relationships**:
- One Issue has many Comments
- One Issue has many Labels
- One Issue may have one PullRequest (via "Closes #N" link)

**No Database**: These relationships exist only in GitHub. This service is stateless - all data comes from/goes to GitHub API.

---

## State Transitions

### Issue States

```
┌──────┐
│ open │ ◄──┐
└──┬───┘    │
   │        │
   │ close  │ reopen
   │        │
   ▼        │
┌────────┐ │
│ closed ├─┘
└────────┘
```

**Transitions**:
- New issues start in `open` state
- Can be closed (manual or via PR merge)
- Can be reopened from closed state

### Pull Request States

```
┌──────┐
│ open │ ────close───► ┌────────┐
└──┬───┘               │ closed │
   │                   └────────┘
   │ merge                 ▲
   │                       │
   ▼                       │
┌────────┐                │
│ merged ├────────────────┘
└────────┘
(state=closed, merged=true)
```

**Transitions**:
- New PRs start in `open` state
- Can be closed without merging (state=closed, merged=false)
- Can be merged (state=closed, merged=true)

---

## Validation Edge Cases

### Empty/Null Values

- **Issue.body**: May be null (optional description)
- **Issue.labels**: May be empty list (no labels)
- **Issue.assignees**: May be empty list (unassigned)
- **Label.description**: May be null (optional)
- **PullRequest.body**: May be null (optional description)
- **PullRequest.linked_issues**: May be empty list (no linked issues)

### Special Characters

- **Issue.title**: May contain unicode, emoji (✅, ❓, 📝)
- **Comment.body**: May contain markdown, emoji, @mentions
- **Label.name**: Allowed: alphanumeric, `-`, `_`, `:` (e.g., "status:new")

### Length Limits

- **Issue.title**: Max 256 characters (GitHub limit)
- **Issue.body**: No enforced limit (may be 100KB+, see edge cases in spec)
- **Label.name**: Max 50 characters (GitHub limit)
- **Label.color**: Exactly 6 hex characters

---

## Type Safety

All models use Pydantic v2 with strict mode:
- Type checking enforced at runtime
- Automatic validation on instantiation
- Immutable (ConfigDict frozen=True)
- JSON serialization/deserialization built-in

**Example Validation**:
```python
# Valid
issue = Issue(number=42, title="Test", state="open", ...)

# Invalid - raises ValidationError
issue = Issue(number=-1, ...)  # number must be > 0
issue = Issue(number=42, title="", state="open", ...)  # title min_length=1
issue = Issue(number=42, title="Test", state="invalid", ...)  # state must be open/closed
```

---

## Future Extensibility

Models designed for easy extension:
- Add new fields without breaking existing code
- Pydantic handles unknown fields gracefully (ignore or error)
- Version fields can be added if API evolves
- No database coupling - easy to adapt to GitHub API changes

