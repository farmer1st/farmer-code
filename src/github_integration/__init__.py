"""
GitHub Integration Core

Provides programmatic access to GitHub operations (issues, comments, labels, PRs)
for the FarmCode AI agent orchestration system.

Public API:
- GitHubService: Main service interface
- Models: Issue, Comment, Label, PullRequest
- Exceptions: GitHubAPIError, AuthenticationError, ResourceNotFoundError,
              ValidationError, RateLimitExceeded, ServerError
"""

__version__ = "0.1.0"

# Public API - Service
# Public API - Exceptions
from .errors import (
    AuthenticationError,
    GitHubAPIError,
    RateLimitExceeded,
    ResourceNotFoundError,
    ServerError,
    ValidationError,
)

# Public API - Models
from .models import Comment, Issue, Label, PullRequest
from .service import GitHubService

__all__ = [
    # Service
    "GitHubService",
    # Models
    "Issue",
    "Comment",
    "Label",
    "PullRequest",
    # Exceptions
    "GitHubAPIError",
    "AuthenticationError",
    "ResourceNotFoundError",
    "ValidationError",
    "RateLimitExceeded",
    "ServerError",
]
