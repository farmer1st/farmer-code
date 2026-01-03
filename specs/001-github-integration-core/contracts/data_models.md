# Contract: Pydantic Data Models

**Version**: 1.0.0
**Date**: 2026-01-02
**Purpose**: JSON schema and validation contracts for GitHub entities

## Overview

This document defines the JSON schemas and validation rules for all Pydantic models used in the GitHub Integration service. These contracts ensure type safety and data integrity across the service boundary.

---

## Model: Issue

**Purpose**: Represents a GitHub issue
**Immutability**: Frozen (cannot be modified after creation)

### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "number": {
      "type": "integer",
      "minimum": 1,
      "description": "Issue number (unique within repo)"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 256,
      "description": "Issue title"
    },
    "body": {
      "type": ["string", "null"],
      "description": "Issue description (markdown)"
    },
    "state": {
      "type": "string",
      "enum": ["open", "closed"],
      "description": "Issue state"
    },
    "labels": {
      "type": "array",
      "items": {"type": "string"},
      "default": [],
      "description": "Label names"
    },
    "assignees": {
      "type": "array",
      "items": {"type": "string"},
      "default": [],
      "description": "Assigned usernames"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Creation timestamp (UTC)"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Last update timestamp (UTC)"
    },
    "repository": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$",
      "description": "Repository full name (owner/repo)"
    },
    "url": {
      "type": "string",
      "format": "uri",
      "description": "GitHub issue URL"
    }
  },
  "required": ["number", "title", "state", "created_at", "updated_at", "repository", "url"]
}
```

### Example JSON

```json
{
  "number": 42,
  "title": "Add user authentication",
  "body": "Implement OAuth2 flow",
  "state": "open",
  "labels": ["status:new", "priority:p1"],
  "assignees": ["duc"],
  "created_at": "2026-01-02T10:30:00Z",
  "updated_at": "2026-01-02T10:30:00Z",
  "repository": "farmer1st/farmcode-tests",
  "url": "https://github.com/farmer1st/farmcode-tests/issues/42"
}
```

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| number | Must be positive integer | "number: Input should be greater than 0" |
| title | 1-256 characters | "title: String should have at least 1 characters" |
| state | Must be "open" or "closed" | "state: Input should be 'open' or 'closed'" |
| created_at | ISO 8601 with timezone | "created_at: Input should be a valid datetime" |
| repository | Format "owner/repo" | "repository: String should match pattern '^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$'" |

---

## Model: Comment

**Purpose**: Represents a GitHub issue comment
**Immutability**: Frozen (cannot be modified after creation)

### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "minimum": 1,
      "description": "Comment ID (unique globally)"
    },
    "issue_number": {
      "type": "integer",
      "minimum": 1,
      "description": "Parent issue number"
    },
    "author": {
      "type": "string",
      "minLength": 1,
      "description": "Comment author username"
    },
    "body": {
      "type": "string",
      "minLength": 1,
      "description": "Comment text (markdown)"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Creation timestamp (UTC)"
    },
    "url": {
      "type": "string",
      "format": "uri",
      "description": "GitHub comment URL"
    }
  },
  "required": ["id", "issue_number", "author", "body", "created_at", "url"]
}
```

### Example JSON

```json
{
  "id": 987654321,
  "issue_number": 42,
  "author": "dede",
  "body": "✅ Backend plan complete. @baron",
  "created_at": "2026-01-02T11:15:00Z",
  "url": "https://github.com/farmer1st/farmcode-tests/issues/42#issuecomment-987654321"
}
```

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| id | Must be positive integer | "id: Input should be greater than 0" |
| issue_number | Must be positive integer | "issue_number: Input should be greater than 0" |
| body | At least 1 character | "body: String should have at least 1 characters" |

---

## Model: Label

**Purpose**: Represents a GitHub label
**Immutability**: Frozen (cannot be modified after creation)

### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50,
      "description": "Label name"
    },
    "color": {
      "type": "string",
      "pattern": "^[0-9A-Fa-f]{6}$",
      "description": "Hex color code (without #)"
    },
    "description": {
      "type": ["string", "null"],
      "description": "Label description"
    }
  },
  "required": ["name", "color"]
}
```

### Example JSON

```json
{
  "name": "status:specs-ready",
  "color": "EDEDED",
  "description": "Specifications approved and ready for planning"
}
```

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| name | 1-50 characters | "name: String should have at most 50 characters" |
| color | Exactly 6 hex digits | "color: String should match pattern '^[0-9A-Fa-f]{6}$'" |

**Default Color for Auto-Creation**: EDEDED (light gray)

---

## Model: PullRequest

**Purpose**: Represents a GitHub pull request
**Immutability**: Frozen (cannot be modified after creation)

### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "number": {
      "type": "integer",
      "minimum": 1,
      "description": "PR number (unique within repo)"
    },
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 256,
      "description": "PR title"
    },
    "body": {
      "type": ["string", "null"],
      "description": "PR description (markdown)"
    },
    "state": {
      "type": "string",
      "enum": ["open", "closed"],
      "description": "PR state"
    },
    "merged": {
      "type": "boolean",
      "description": "Whether PR is merged"
    },
    "base_branch": {
      "type": "string",
      "minLength": 1,
      "description": "Base branch name"
    },
    "head_branch": {
      "type": "string",
      "minLength": 1,
      "description": "Head branch name"
    },
    "linked_issues": {
      "type": "array",
      "items": {"type": "integer", "minimum": 1},
      "default": [],
      "description": "Linked issue numbers"
    },
    "url": {
      "type": "string",
      "format": "uri",
      "description": "GitHub PR URL"
    }
  },
  "required": ["number", "title", "state", "merged", "base_branch", "head_branch", "url"]
}
```

### Example JSON

```json
{
  "number": 15,
  "title": "Add user authentication",
  "body": "Closes #42\n\nImplements OAuth2 flow",
  "state": "open",
  "merged": false,
  "base_branch": "main",
  "head_branch": "123-add-auth",
  "linked_issues": [42],
  "url": "https://github.com/farmer1st/farmcode-tests/pull/15"
}
```

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| number | Must be positive integer | "number: Input should be greater than 0" |
| title | 1-256 characters | "title: String should have at least 1 characters" |
| state | Must be "open" or "closed" | "state: Input should be 'open' or 'closed'" |
| merged | Must be boolean | "merged: Input should be a valid boolean" |

---

## Request Model: CreateIssueRequest

**Purpose**: Validate issue creation requests

### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 256,
      "description": "Issue title"
    },
    "body": {
      "type": ["string", "null"],
      "description": "Issue description"
    },
    "labels": {
      "type": "array",
      "items": {"type": "string"},
      "default": [],
      "description": "Initial labels"
    },
    "assignees": {
      "type": "array",
      "items": {"type": "string"},
      "default": [],
      "description": "Assignees"
    }
  },
  "required": ["title"]
}
```

### Example JSON

```json
{
  "title": "Add user authentication",
  "body": "Implement OAuth2 flow",
  "labels": ["status:new"],
  "assignees": ["duc"]
}
```

---

## Request Model: CreateCommentRequest

**Purpose**: Validate comment creation requests

### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "body": {
      "type": "string",
      "minLength": 1,
      "description": "Comment text"
    }
  },
  "required": ["body"]
}
```

### Example JSON

```json
{
  "body": "✅ Backend plan complete. @baron"
}
```

---

## Request Model: CreatePullRequestRequest

**Purpose**: Validate PR creation requests

### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 256,
      "description": "PR title"
    },
    "body": {
      "type": ["string", "null"],
      "description": "PR description"
    },
    "base": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9/_-]+$",
      "description": "Base branch"
    },
    "head": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9/_-]+$",
      "description": "Head branch"
    }
  },
  "required": ["title", "base", "head"]
}
```

### Example JSON

```json
{
  "title": "Add user authentication",
  "body": "Closes #42",
  "base": "main",
  "head": "123-add-auth"
}
```

---

## Response Model: OperationResult\<T\>

**Purpose**: Wrapper for operation results with error handling

### JSON Schema

```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether operation succeeded"
    },
    "data": {
      "description": "Result data if successful (type varies by operation)"
    },
    "error": {
      "type": ["string", "null"],
      "description": "Error message if failed"
    },
    "error_code": {
      "type": ["string", "null"],
      "description": "Error code for client handling"
    }
  },
  "required": ["success"]
}
```

### Example JSON (Success)

```json
{
  "success": true,
  "data": {
    "number": 42,
    "title": "Add user authentication",
    "state": "open",
    ...
  },
  "error": null,
  "error_code": null
}
```

### Example JSON (Failure)

```json
{
  "success": false,
  "data": null,
  "error": "Issue not found",
  "error_code": "RESOURCE_NOT_FOUND"
}
```

### Error Codes

| Code | Meaning | HTTP Equivalent |
|------|---------|-----------------|
| VALIDATION_ERROR | Input validation failed | 400 Bad Request |
| AUTHENTICATION_ERROR | GitHub auth failed | 401 Unauthorized |
| RESOURCE_NOT_FOUND | Issue/PR/comment not found | 404 Not Found |
| RATE_LIMIT_EXCEEDED | GitHub rate limit hit | 429 Too Many Requests |
| SERVER_ERROR | GitHub API unavailable | 500 Server Error |

---

## Serialization/Deserialization

All models support JSON serialization via Pydantic:

### To JSON

```python
issue = Issue(number=42, title="Test", ...)
json_str = issue.model_dump_json()
```

### From JSON

```python
json_data = '{"number": 42, "title": "Test", ...}'
issue = Issue.model_validate_json(json_data)
```

### To Dict

```python
issue_dict = issue.model_dump()
```

### From Dict

```python
issue_dict = {"number": 42, "title": "Test", ...}
issue = Issue.model_validate(issue_dict)
```

---

## Validation Error Format

When Pydantic validation fails, errors are returned in this format:

```python
{
  "type": "validation_error",
  "errors": [
    {
      "type": "greater_than",
      "loc": ["number"],
      "msg": "Input should be greater than 0",
      "input": -1
    },
    {
      "type": "string_too_short",
      "loc": ["title"],
      "msg": "String should have at least 1 characters",
      "input": "",
      "ctx": {"min_length": 1}
    }
  ]
}
```

**Fields**:
- `type`: Error category
- `loc`: Field path (e.g., ["number"], ["labels", 0])
- `msg`: Human-readable error message
- `input`: The invalid value that was provided
- `ctx`: Additional context (limits, patterns, etc.)

---

## Type Safety Guarantees

All models are:
- **Immutable**: Cannot be modified after creation (ConfigDict frozen=True)
- **Type-checked**: Runtime validation via Pydantic
- **Serializable**: JSON conversion built-in
- **Self-documenting**: Field descriptions and constraints explicit

**Example Type Safety**:
```python
# Valid
issue = Issue(number=42, title="Test", state="open", ...)

# Invalid - Pydantic raises ValidationError
issue = Issue(number=-1, ...)  # number must be > 0
issue = Issue(number=42, title="", ...)  # title too short
issue = Issue(number=42, title="Test", state="invalid", ...)  # state invalid
```

