"""
Pydantic Data Models

Type-safe models for GitHub entities (Issue, Comment, Label, PullRequest).
All models are immutable (frozen=True) and validated at runtime.
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Issue(BaseModel):
    """Represents a GitHub issue"""

    model_config = ConfigDict(frozen=True)  # Immutable

    number: int = Field(..., description="Issue number (unique within repo)", gt=0)
    title: str = Field(..., description="Issue title", min_length=1, max_length=256)
    body: str | None = Field(None, description="Issue description (markdown)")
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
        return re.findall(r"@(\w+)", self.body)


class Label(BaseModel):
    """Represents a GitHub label"""

    model_config = ConfigDict(frozen=True)  # Immutable

    name: str = Field(..., description="Label name", min_length=1, max_length=50)
    color: str = Field(..., description="Hex color code (without #)", pattern="^[0-9A-Fa-f]{6}$")
    description: str | None = Field(None, description="Label description")

    @property
    def hex_color(self) -> str:
        """Get color with # prefix for display"""
        return f"#{self.color}"


class PullRequest(BaseModel):
    """Represents a GitHub pull request"""

    model_config = ConfigDict(frozen=True)  # Immutable

    number: int = Field(..., description="PR number (unique within repo)", gt=0)
    title: str = Field(..., description="PR title", min_length=1, max_length=256)
    body: str | None = Field(None, description="PR description (markdown)")
    state: str = Field(..., description="PR state", pattern="^(open|closed)$")
    merged: bool = Field(..., description="Whether PR is merged")
    base_branch: str = Field(..., description="Base branch name (e.g., main)")
    head_branch: str = Field(..., description="Head branch name (e.g., 123-add-auth)")
    linked_issues: list[int] = Field(default_factory=list, description="Linked issue numbers")
    url: str = Field(..., description="GitHub PR URL")

    def is_linked_to(self, issue_number: int) -> bool:
        """Check if PR is linked to specific issue"""
        return issue_number in self.linked_issues


# Request Models


class CreateIssueRequest(BaseModel):
    """Request to create a new issue"""

    title: str = Field(..., description="Issue title", min_length=1, max_length=256)
    body: str | None = Field(None, description="Issue description")
    labels: list[str] = Field(default_factory=list, description="Initial labels")
    assignees: list[str] = Field(default_factory=list, description="Assignees")


class CreateCommentRequest(BaseModel):
    """Request to create a comment"""

    body: str = Field(..., description="Comment text", min_length=1)


class CreatePullRequestRequest(BaseModel):
    """Request to create a pull request"""

    title: str = Field(..., description="PR title", min_length=1, max_length=256)
    body: str | None = Field(None, description="PR description")
    base: str = Field(..., description="Base branch", pattern="^[a-zA-Z0-9/_-]+$")
    head: str = Field(..., description="Head branch", pattern="^[a-zA-Z0-9/_-]+$")
