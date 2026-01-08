"""GitHub API client for Agent Hub service.

Posts escalation comments to GitHub issues/PRs.
"""

import os
from typing import Any

import httpx


class GitHubError(Exception):
    """Error from GitHub API."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class GitHubClient:
    """HTTP client for GitHub API."""

    def __init__(
        self,
        token: str | None = None,
        repo: str | None = None,
    ) -> None:
        """Initialize GitHub client.

        Args:
            token: GitHub API token (default from env)
            repo: Repository in format "owner/repo" (default from env)
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.repo = repo or os.environ.get("GITHUB_REPO", "farmer1st/farmer-code")
        self.base_url = "https://api.github.com"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GitHubClient":
        """Enter async context."""
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit async context."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def post_escalation_comment(
        self,
        issue_number: int,
        question: str,
        tentative_answer: str,
        confidence: int,
        uncertainty_reasons: list[str] | None = None,
        escalation_id: str | None = None,
    ) -> int:
        """Post an escalation comment to a GitHub issue.

        Args:
            issue_number: GitHub issue number
            question: Original question
            tentative_answer: Agent's tentative answer
            confidence: Confidence level
            uncertainty_reasons: Reasons for uncertainty
            escalation_id: Escalation ID for tracking

        Returns:
            GitHub comment ID

        Raises:
            GitHubError: On API failure
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        # Build comment body
        body = self._format_escalation_comment(
            question=question,
            tentative_answer=tentative_answer,
            confidence=confidence,
            uncertainty_reasons=uncertainty_reasons,
            escalation_id=escalation_id,
        )

        try:
            response = await self._client.post(
                f"/repos/{self.repo}/issues/{issue_number}/comments",
                json={"body": body},
            )

            if response.status_code == 201:
                return response.json()["id"]

            raise GitHubError(
                message=f"Failed to post comment: {response.text}",
                status_code=response.status_code,
            )

        except httpx.RequestError as e:
            raise GitHubError(f"Failed to connect to GitHub: {e}") from e

    def _format_escalation_comment(
        self,
        question: str,
        tentative_answer: str,
        confidence: int,
        uncertainty_reasons: list[str] | None = None,
        escalation_id: str | None = None,
    ) -> str:
        """Format the escalation comment body.

        Args:
            question: Original question
            tentative_answer: Agent's answer
            confidence: Confidence level
            uncertainty_reasons: Reasons for uncertainty
            escalation_id: Escalation ID

        Returns:
            Formatted markdown comment
        """
        reasons_list = ""
        if uncertainty_reasons:
            reasons_list = "\n".join(f"- {reason}" for reason in uncertainty_reasons)

        comment = f"""## Human Review Required

**Confidence:** {confidence}%

### Question
{question}

### Tentative Answer
{tentative_answer}

"""

        if reasons_list:
            comment += f"""### Uncertainty Reasons
{reasons_list}

"""

        comment += """### How to Respond

Reply to this comment with one of the following:

- `/confirm` - Accept the tentative answer as correct
- `/correct <your answer>` - Provide the correct answer
- `/context <additional info>` - Add more context for re-evaluation

"""

        if escalation_id:
            comment += f"\n---\n_Escalation ID: {escalation_id}_"

        return comment

    async def get_issue(self, issue_number: int) -> dict[str, Any]:
        """Get GitHub issue details.

        Args:
            issue_number: Issue number

        Returns:
            Issue data dict

        Raises:
            GitHubError: On API failure
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async with statement.")

        try:
            response = await self._client.get(f"/repos/{self.repo}/issues/{issue_number}")

            if response.status_code == 200:
                return response.json()

            raise GitHubError(
                message=f"Failed to get issue: {response.text}",
                status_code=response.status_code,
            )

        except httpx.RequestError as e:
            raise GitHubError(f"Failed to connect to GitHub: {e}") from e
