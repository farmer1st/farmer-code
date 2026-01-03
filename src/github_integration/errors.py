"""
Custom Exceptions

Exception hierarchy for GitHub API errors with meaningful error messages
and error codes for client handling.
"""


class GitHubAPIError(Exception):
    """Base exception for all GitHub API errors"""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"


class AuthenticationError(GitHubAPIError):
    """
    GitHub App authentication failed.

    Raised when:
    - PEM file not found or invalid permissions
    - JWT generation fails
    - Installation access token request fails
    """

    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="AUTHENTICATION_ERROR")


class ResourceNotFoundError(GitHubAPIError):
    """
    GitHub resource not found (404).

    Raised when:
    - Issue number doesn't exist
    - PR number doesn't exist
    - Repository not found
    - Branch not found
    """

    def __init__(self, resource_type: str, identifier: str | int) -> None:
        message = f"{resource_type} not found: {identifier}"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND")
        self.resource_type = resource_type
        self.identifier = identifier


class ValidationError(GitHubAPIError):
    """
    Input validation failed.

    Raised when:
    - Required field missing or empty
    - Field value exceeds length limits
    - Field value doesn't match pattern
    - Pydantic validation fails
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field


class RateLimitExceeded(GitHubAPIError):
    """
    GitHub API rate limit exceeded (429).

    Raised when:
    - Rate limit hit (check wait_seconds for reset time)

    Attributes:
        wait_seconds: Number of seconds to wait before retry
    """

    def __init__(self, message: str, wait_seconds: int) -> None:
        super().__init__(message, error_code="RATE_LIMIT_EXCEEDED")
        self.wait_seconds = wait_seconds


class ServerError(GitHubAPIError):
    """
    GitHub API server error (5xx) or network timeout.

    Raised when:
    - GitHub API returns 5xx after retries
    - Network timeout
    - Connection error after retries

    Note: Retry logic (3 attempts, 1s delay) already applied before raising this.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message, error_code="SERVER_ERROR")
        self.status_code = status_code
