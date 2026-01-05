"""
GitHubService

Main service interface for GitHub operations with type-safe methods and
structured logging.
"""

import re
from datetime import datetime
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from .auth import GitHubAppAuth
from .client import GitHubAPIClient
from .errors import ResourceNotFoundError, ValidationError
from .logger import logger
from .models import (
    Comment,
    CreateCommentRequest,
    CreateIssueRequest,
    CreatePullRequestRequest,
    Issue,
    PullRequest,
)


class GitHubService:
    """
    Main service interface for GitHub operations.

    Handles GitHub App authentication, API calls, retry logic,
    and error handling for the Farmer Code orchestrator.
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
            raise ValueError(f"Invalid repository format: {repository}. Must be 'owner/repo'")

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
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
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
        labels: list[str] | None = None,
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

    def _parse_issue(self, data: dict[str, Any]) -> Issue:
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
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
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
                raise ValidationError(
                    "title: String should have at least 1 characters", field="title"
                )
            if len(title) > 256:
                raise ValidationError(
                    "title: String should have at most 256 characters", field="title"
                )

        # Build update payload (only include provided fields)
        data: dict[str, Any] = {}
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

    # User Story 2: Comment Operations

    def create_comment(self, issue_number: int, body: str) -> Comment:
        """
        Post a comment to an issue.

        Args:
            issue_number: Target issue number (must be positive)
            body: Comment text in markdown (may include emoji, @mentions)

        Returns:
            Comment: Created comment with ID, timestamp, URL

        Raises:
            ValueError: If body is empty or issue_number <= 0
            ResourceNotFoundError: If issue doesn't exist
            AuthenticationError: If GitHub App auth fails
            RateLimitExceeded: If GitHub rate limit hit
            ServerError: If GitHub API returns 5xx after retries
        """
        # Validate issue number
        if issue_number <= 0:
            raise ValueError(f"Issue number must be positive: {issue_number}")

        # Validate input using Pydantic
        try:
            request = CreateCommentRequest(body=body)
        except PydanticValidationError as e:
            first_error = e.errors()[0]
            field = first_error["loc"][0] if first_error["loc"] else "unknown"
            message = first_error["msg"]
            raise ValidationError(f"{field}: {message}", field=str(field)) from e

        # Make API call
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = {"body": request.body}

        response = self.client.post(path, json=data)

        # Parse response into Comment model
        comment = self._parse_comment(response, issue_number)

        logger.info(
            "Created GitHub comment",
            extra={
                "context": {
                    "method": "create_comment",
                    "issue_number": issue_number,
                    "comment_id": comment.id,
                    "repository": self.repository,
                }
            },
        )

        return comment

    def get_comments(self, issue_number: int) -> list[Comment]:
        """
        Get all comments on an issue in chronological order.

        Args:
            issue_number: Issue number (must be positive)

        Returns:
            list[Comment]: All comments sorted by creation time (oldest first)
                           Empty list if no comments

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
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"

        response = self.client.get(path)

        # Parse response into list of Comment models
        comments = [self._parse_comment(comment_data, issue_number) for comment_data in response]

        logger.info(
            "Retrieved GitHub comments",
            extra={
                "context": {
                    "method": "get_comments",
                    "issue_number": issue_number,
                    "count": len(comments),
                    "repository": self.repository,
                }
            },
        )

        return comments

    def get_comments_since(self, issue_number: int, since: datetime) -> list[Comment]:
        """
        Get comments posted after a specific timestamp.

        Used for incremental polling - only fetch new comments since last check.

        Args:
            issue_number: Issue number (must be positive)
            since: Timestamp to filter from (UTC timezone required)

        Returns:
            list[Comment]: New comments posted after `since` timestamp
                           Empty list if no new comments

        Raises:
            ValueError: If issue_number <= 0 or since not timezone-aware
            ResourceNotFoundError: If issue doesn't exist
            AuthenticationError: If GitHub App auth fails
            RateLimitExceeded: If GitHub rate limit hit
            ServerError: If GitHub API returns 5xx after retries
        """
        # Validate issue number
        if issue_number <= 0:
            raise ValueError(f"Issue number must be positive: {issue_number}")

        # Validate timezone
        if since.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (use datetime with tzinfo)")

        # Make API call with since parameter
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/comments"
        params = {"since": since.isoformat()}

        response = self.client.get(path, params=params)

        # Parse response into list of Comment models
        comments = [self._parse_comment(comment_data, issue_number) for comment_data in response]

        logger.info(
            "Retrieved GitHub comments since timestamp",
            extra={
                "context": {
                    "method": "get_comments_since",
                    "issue_number": issue_number,
                    "since": since.isoformat(),
                    "count": len(comments),
                    "repository": self.repository,
                }
            },
        )

        return comments

    def _parse_comment(self, data: dict[str, Any], issue_number: int) -> Comment:
        """
        Parse GitHub API comment response into Comment model.

        Args:
            data: Raw GitHub API response for a comment
            issue_number: Parent issue number

        Returns:
            Comment: Parsed comment model
        """
        return Comment(
            id=data["id"],
            issue_number=issue_number,
            author=data["user"]["login"],
            body=data["body"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            url=data["html_url"],
        )

    # User Story 3: Label Operations

    def add_labels(self, issue_number: int, labels: list[str]) -> None:
        """
        Add labels to an issue. Auto-creates labels that don't exist.

        Args:
            issue_number: Target issue number (must be positive)
            labels: List of label names to add (non-empty)

        Raises:
            ValueError: If labels list is empty or issue_number <= 0
            ResourceNotFoundError: If issue doesn't exist
            AuthenticationError: If GitHub App auth fails
            RateLimitExceeded: If GitHub rate limit hit
            ServerError: If GitHub API returns 5xx after retries

        Note:
            If a label doesn't exist in the repository, it will be created
            automatically with default color #EDEDED (light gray).
        """
        # Validate issue number
        if issue_number <= 0:
            raise ValueError(f"Issue number must be positive: {issue_number}")

        # Validate labels list
        if not labels:
            raise ValueError("Labels list cannot be empty")

        # Try to add labels - may fail if label doesn't exist
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/labels"

        try:
            self.client.post(path, json={"labels": labels})
        except Exception as e:
            # Check if it's a 422 error indicating label doesn't exist
            if "422" in str(e) or "Validation Failed" in str(e):
                # Auto-create missing labels and retry
                for label_name in labels:
                    self._ensure_label_exists(label_name)
                # Retry adding labels
                self.client.post(path, json={"labels": labels})
            else:
                raise

        logger.info(
            "Added labels to GitHub issue",
            extra={
                "context": {
                    "method": "add_labels",
                    "issue_number": issue_number,
                    "labels": labels,
                    "repository": self.repository,
                }
            },
        )

    def remove_labels(self, issue_number: int, labels: list[str]) -> None:
        """
        Remove labels from an issue.

        Args:
            issue_number: Target issue number (must be positive)
            labels: List of label names to remove (non-empty)

        Raises:
            ValueError: If labels list is empty or issue_number <= 0
            ResourceNotFoundError: If issue doesn't exist
            AuthenticationError: If GitHub App auth fails
            RateLimitExceeded: If GitHub rate limit hit
            ServerError: If GitHub API returns 5xx after retries

        Note:
            Removing a label that is not on the issue is silently ignored (idempotent).
        """
        # Validate issue number
        if issue_number <= 0:
            raise ValueError(f"Issue number must be positive: {issue_number}")

        # Validate labels list
        if not labels:
            raise ValueError("Labels list cannot be empty")

        owner, repo = self.repository.split("/")

        # Remove each label individually (GitHub API doesn't support bulk remove)
        for label_name in labels:
            path = f"/repos/{owner}/{repo}/issues/{issue_number}/labels/{label_name}"
            try:
                self.client.delete(path)
            except ResourceNotFoundError:
                # Silently ignore 404 errors (label not on issue) - idempotent
                continue

        logger.info(
            "Removed labels from GitHub issue",
            extra={
                "context": {
                    "method": "remove_labels",
                    "issue_number": issue_number,
                    "labels": labels,
                    "repository": self.repository,
                }
            },
        )

    def _ensure_label_exists(self, label_name: str) -> None:
        """
        Ensure a label exists in the repository, creating it if necessary.

        Args:
            label_name: Name of the label to ensure exists

        Note:
            Creates label with default color #EDEDED (light gray) if it doesn't exist.
        """
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/labels"

        try:
            self.client.post(
                path,
                json={
                    "name": label_name,
                    "color": "EDEDED",  # Default light gray
                },
            )
            logger.info(
                "Created new GitHub label",
                extra={
                    "context": {
                        "method": "_ensure_label_exists",
                        "label_name": label_name,
                        "color": "EDEDED",
                        "repository": self.repository,
                    }
                },
            )
        except Exception as e:
            # 422 means label already exists - that's fine
            if "422" in str(e) or "already_exists" in str(e).lower():
                pass
            else:
                raise

    # User Story 4: Pull Request Operations

    def create_pull_request(
        self,
        title: str,
        body: str | None = None,
        base: str = "main",
        head: str = "",
    ) -> PullRequest:
        """
        Create a new pull request.

        Args:
            title: PR title (1-256 characters, required)
            body: PR description in markdown (optional, may include "Closes #N")
            base: Base branch to merge into (defaults to "main")
            head: Head branch with changes (required)

        Returns:
            PullRequest: Created PR with number, URL, state

        Raises:
            ValidationError: If title is empty/too long or branches invalid
            ResourceNotFoundError: If base or head branch doesn't exist
            AuthenticationError: If GitHub App auth fails
            RateLimitExceeded: If GitHub rate limit hit
            ServerError: If GitHub API returns 5xx after retries
        """
        # Validate input using Pydantic
        try:
            request = CreatePullRequestRequest(
                title=title,
                body=body,
                base=base,
                head=head,
            )
        except PydanticValidationError as e:
            first_error = e.errors()[0]
            field = first_error["loc"][0] if first_error["loc"] else "unknown"
            message = first_error["msg"]
            raise ValidationError(f"{field}: {message}", field=str(field)) from e

        # Make API call
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/pulls"
        data = {
            "title": request.title,
            "body": request.body or "",
            "base": request.base,
            "head": request.head,
        }

        response = self.client.post(path, json=data)

        # Parse response into PullRequest model
        pr = self._parse_pull_request(response)

        logger.info(
            "Created GitHub pull request",
            extra={
                "context": {
                    "method": "create_pull_request",
                    "pr_number": pr.number,
                    "base": base,
                    "head": head,
                    "repository": self.repository,
                }
            },
        )

        return pr

    def get_pull_request(self, pr_number: int) -> PullRequest:
        """
        Get pull request details by PR number.

        Args:
            pr_number: Pull request number (must be positive)

        Returns:
            PullRequest: PR with current state, branches, merge status

        Raises:
            ValueError: If pr_number <= 0
            ResourceNotFoundError: If PR doesn't exist
            AuthenticationError: If GitHub App auth fails
            RateLimitExceeded: If GitHub rate limit hit
            ServerError: If GitHub API returns 5xx after retries
        """
        # Validate PR number
        if pr_number <= 0:
            raise ValueError(f"PR number must be positive: {pr_number}")

        # Make API call
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/pulls/{pr_number}"

        response = self.client.get(path)

        # Parse response into PullRequest model
        pr = self._parse_pull_request(response)

        logger.info(
            "Retrieved GitHub pull request",
            extra={
                "context": {
                    "method": "get_pull_request",
                    "pr_number": pr.number,
                    "repository": self.repository,
                }
            },
        )

        return pr

    def list_pull_requests(self, state: str = "open") -> list[PullRequest]:
        """
        List pull requests in the repository with optional filtering.

        Args:
            state: Filter by state ("open", "closed", or "all"), defaults to "open"

        Returns:
            list[PullRequest]: List of matching PRs (may be empty)

        Raises:
            ValueError: If state not in ["open", "closed", "all"]
            AuthenticationError: If GitHub App auth fails
            RateLimitExceeded: If GitHub rate limit hit
            ServerError: If GitHub API returns 5xx after retries
        """
        # Validate state
        if state not in ["open", "closed", "all"]:
            raise ValueError(f"Invalid state: {state}. Must be 'open', 'closed', or 'all'")

        # Make API call
        owner, repo = self.repository.split("/")
        path = f"/repos/{owner}/{repo}/pulls"

        params = {"state": state}

        response = self.client.get(path, params=params)

        # Parse response into list of PullRequest models
        prs = [self._parse_pull_request(pr_data) for pr_data in response]

        logger.info(
            "Listed GitHub pull requests",
            extra={
                "context": {
                    "method": "list_pull_requests",
                    "state": state,
                    "count": len(prs),
                    "repository": self.repository,
                }
            },
        )

        return prs

    def _parse_pull_request(self, data: dict[str, Any]) -> PullRequest:
        """
        Parse GitHub API pull request response into PullRequest model.

        Args:
            data: Raw GitHub API response for a pull request

        Returns:
            PullRequest: Parsed pull request model
        """
        # Extract linked issues from body (e.g., "Closes #42")
        linked_issues: list[int] = []
        body = data.get("body") or ""
        import re

        matches = re.findall(r"(?:closes|fixes|resolves)\s+#(\d+)", body, re.IGNORECASE)
        linked_issues = [int(m) for m in matches]

        return PullRequest(
            number=data["number"],
            title=data["title"],
            body=data.get("body"),
            state=data["state"],
            merged=data.get("merged", False),
            base_branch=data["base"]["ref"],
            head_branch=data["head"]["ref"],
            linked_issues=linked_issues,
            url=data["html_url"],
        )
