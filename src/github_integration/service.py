"""
GitHubService

Main service interface for GitHub operations with type-safe methods and
structured logging.
"""

from datetime import datetime, timezone
from typing import Optional
import re

from pydantic import ValidationError as PydanticValidationError

from .auth import GitHubAppAuth
from .client import GitHubAPIClient
from .errors import ValidationError
from .logger import logger
from .models import Comment, CreateIssueRequest, Issue, Label, PullRequest


class GitHubService:
    """
    Main service interface for GitHub operations.

    Handles GitHub App authentication, API calls, retry logic,
    and error handling for the FarmCode orchestrator.
    """

    def __init__(
        self,
        app_id: int,
        installation_id: int,
        private_key_path: str,
        repository: str,
    ) -> None:
        """
        Initialize GitHub service.

        Args:
            app_id: GitHub App ID (e.g., 2578431)
            installation_id: GitHub App installation ID (e.g., 102211688)
            private_key_path: Path to PEM file (from GITHUB_APP_PRIVATE_KEY_PATH env var)
            repository: Target repository in format "owner/repo" (e.g., farmer1st/farmcode-tests)

        Raises:
            FileNotFoundError: If PEM file doesn't exist
            PermissionError: If PEM file permissions != 600
            ValueError: If repository format invalid
        """
        # Validate repository format
        if not re.match(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$", repository):
            raise ValueError(
                f"Invalid repository format: {repository}. Must be 'owner/repo'"
            )

        self.app_id = app_id
        self.installation_id = installation_id
        self.repository = repository

        # Initialize authentication
        self.auth = GitHubAppAuth(
            app_id=app_id,
            installation_id=installation_id,
            private_key_path=private_key_path,
        )

        # Initialize API client
        self.client = GitHubAPIClient(auth=self.auth, repository=repository)

        logger.info(
            "Initialized GitHubService",
            extra={
                "context": {
                    "app_id": app_id,
                    "installation_id": installation_id,
                    "repository": repository,
                }
            },
        )

    def create_issue(
        self,
        title: str,
        body: Optional[str] = None,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
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
        """
        # Validate input using Pydantic
        try:
            request = CreateIssueRequest(
                title=title,
                body=body,
                labels=labels or [],
                assignees=assignees or [],
            )
        except PydanticValidationError as e:
            # Extract first error message
            first_error = e.errors()[0]
            field = first_error["loc"][0] if first_error["loc"] else "unknown"
            message = first_error["msg"]
            raise ValidationError(f"{field}: {message}", field=str(field)) from e

        # Prepare API request
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/issues"
        data = {
            "title": request.title,
            "body": request.body or "",
            "labels": request.labels,
            "assignees": request.assignees,
        }

        # Make API call
        response = self.client.post(path, json=data)

        # Parse response into Issue model
        issue = self._parse_issue(response)

        logger.info(
            "Created GitHub issue",
            extra={
                "context": {
                    "method": "create_issue",
                    "issue_number": issue.number,
                    "repository": self.repository,
                    "labels": issue.labels,
                }
            },
        )

        return issue

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
        """
        # Validate issue number
        if issue_number <= 0:
            raise ValueError(f"Issue number must be positive: {issue_number}")

        # Make API call
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/issues/{issue_number}"

        response = self.client.get(path)

        # Parse response into Issue model
        issue = self._parse_issue(response)

        logger.info(
            "Retrieved GitHub issue",
            extra={
                "context": {
                    "method": "get_issue",
                    "issue_number": issue.number,
                    "repository": self.repository,
                }
            },
        )

        return issue

    def list_issues(
        self,
        state: str = "open",
        labels: Optional[list[str]] = None,
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
        """
        # Validate state
        if state not in ["open", "closed", "all"]:
            raise ValueError(f"Invalid state: {state}. Must be 'open', 'closed', or 'all'")

        # Prepare API request
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/issues"

        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)

        # Make API call (GitHub API returns list directly)
        response = self.client.get(path, params=params)

        # Parse response into list of Issue models
        issues = [self._parse_issue(issue_data) for issue_data in response]

        logger.info(
            "Listed GitHub issues",
            extra={
                "context": {
                    "method": "list_issues",
                    "state": state,
                    "labels": labels,
                    "count": len(issues),
                    "repository": self.repository,
                }
            },
        )

        return issues

    def _parse_issue(self, data: dict) -> Issue:
        """
        Parse GitHub API issue response into Issue model.

        Args:
            data: Raw GitHub API response for an issue

        Returns:
            Issue: Parsed issue model
        """
        return Issue(
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            labels=[label["name"] for label in data.get("labels", [])],
            assignees=[assignee["login"] for assignee in data.get("assignees", [])],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            repository=self.repository,
            url=data["html_url"],
        )

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
        """
        # Validate issue number
        if issue_number <= 0:
            raise ValueError(f"Issue number must be positive: {issue_number}")

        # Validate state if provided
        if state is not None and state not in ["open", "closed"]:
            raise ValueError(f"Invalid state: {state}. Must be 'open' or 'closed'")

        # Validate title if provided
        if title is not None:
            if len(title) == 0:
                raise ValidationError("title: String should have at least 1 characters", field="title")
            if len(title) > 256:
                raise ValidationError("title: String should have at most 256 characters", field="title")

        # Build update payload (only include provided fields)
        data = {}
        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if state is not None:
            data["state"] = state
        if labels is not None:
            data["labels"] = labels
        if assignees is not None:
            data["assignees"] = assignees

        # Make API call
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/issues/{issue_number}"

        response = self.client.patch(path, json=data)

        # Parse response into Issue model
        issue = self._parse_issue(response)

        logger.info(
            "Updated GitHub issue",
            extra={
                "context": {
                    "method": "update_issue",
                    "issue_number": issue.number,
                    "repository": self.repository,
                    "updated_fields": list(data.keys()),
                }
            },
        )

        return issue

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
        """
        return self.update_issue(issue_number, state="closed")

    # Methods for User Story 2, 3, 4 will be added in later phases
