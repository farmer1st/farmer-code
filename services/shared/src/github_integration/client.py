"""
GitHub API Client

Lightweight wrapper around requests library for GitHub API calls with retry logic
and rate limit detection.
"""

import time
from typing import Any

import requests

from .auth import GitHubAppAuth
from .errors import RateLimitExceeded, ResourceNotFoundError, ServerError
from .logger import logger


class GitHubAPIClient:
    """
    GitHub API client with retry logic and rate limit handling.

    Features:
    - Fixed retry: 3 attempts with 1-second delay
    - Rate limit detection and error reporting
    - Structured logging for all requests
    - Installation token authentication
    """

    BASE_URL = "https://api.github.com"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self, auth: GitHubAppAuth, repository: str) -> None:
        """
        Initialize GitHub API client.

        Args:
            auth: GitHub App authentication instance
            repository: Target repository in format "owner/repo"
        """
        self.auth = auth
        self.repository = repository
        self.owner, self.repo = repository.split("/")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers with authentication token"""
        token = self.auth.get_installation_token()
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _check_rate_limit(self, response: requests.Response) -> None:
        """
        Check if response indicates rate limit exceeded.

        Args:
            response: HTTP response from GitHub API

        Raises:
            RateLimitExceeded: If rate limit hit
        """
        if response.status_code == 429:
            # Get wait time from header (defaults to 3600 if not present)
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            now = int(time.time())
            wait_seconds = max(reset_time - now, 3600)  # At least 1 hour

            logger.error(
                "GitHub rate limit exceeded",
                extra={
                    "context": {
                        "status_code": 429,
                        "wait_seconds": wait_seconds,
                        "reset_time": reset_time,
                    }
                },
            )

            raise RateLimitExceeded(
                f"GitHub rate limit exceeded. Wait {wait_seconds} seconds",
                wait_seconds=wait_seconds,
            )

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """
        Make HTTP request to GitHub API with retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path (e.g., "/repos/owner/repo/issues")
            json: Request body (for POST, PATCH)
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            ResourceNotFoundError: If resource not found (404)
            RateLimitExceeded: If rate limit hit (429)
            ServerError: If server error after retries (5xx)
        """
        url = f"{self.BASE_URL}{path}"
        headers = self._get_headers()

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(
                    f"GitHub API request: {method} {path}",
                    extra={
                        "context": {
                            "method": method,
                            "path": path,
                            "attempt": attempt,
                        }
                    },
                )

                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    params=params,
                    timeout=30,
                )

                # Check rate limit first
                self._check_rate_limit(response)

                # Handle 404 - resource not found
                if response.status_code == 404:
                    logger.error(
                        "GitHub resource not found",
                        extra={
                            "context": {
                                "method": method,
                                "path": path,
                                "status_code": 404,
                            }
                        },
                    )
                    # Extract resource type from path
                    resource_type = "Resource"
                    if "/issues/" in path:
                        resource_type = "Issue"
                    elif "/pulls/" in path:
                        resource_type = "Pull Request"
                    raise ResourceNotFoundError(resource_type, path)

                # Handle 5xx - server error (retry)
                if 500 <= response.status_code < 600:
                    logger.warning(
                        f"GitHub server error (attempt {attempt}/{self.MAX_RETRIES})",
                        extra={
                            "context": {
                                "method": method,
                                "path": path,
                                "status_code": response.status_code,
                                "attempt": attempt,
                            }
                        },
                    )
                    if attempt < self.MAX_RETRIES:
                        time.sleep(self.RETRY_DELAY)
                        continue
                    else:
                        raise ServerError(
                            f"GitHub API server error after {self.MAX_RETRIES} retries",
                            status_code=response.status_code,
                        )

                # Raise for other HTTP errors (4xx except 404/429)
                response.raise_for_status()

                # Success - return JSON data
                return response.json() if response.text else {}

            except (requests.ConnectionError, requests.Timeout) as e:
                logger.warning(
                    f"Network error (attempt {attempt}/{self.MAX_RETRIES}): {e}",
                    extra={
                        "context": {
                            "method": method,
                            "path": path,
                            "error": str(e),
                            "attempt": attempt,
                        }
                    },
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY)
                    continue
                else:
                    raise ServerError(f"Network error after {self.MAX_RETRIES} retries: {e}") from e

            except (RateLimitExceeded, ResourceNotFoundError):
                # Don't retry rate limit or 404 errors
                raise

            except requests.HTTPError as e:
                # Other HTTP errors - don't retry
                logger.error(
                    f"GitHub API HTTP error: {e}",
                    extra={
                        "context": {
                            "method": method,
                            "path": path,
                            "status_code": e.response.status_code,
                            "error": str(e),
                        }
                    },
                )
                raise ServerError(
                    f"GitHub API error: {e.response.status_code} {e.response.text}",
                    status_code=e.response.status_code,
                ) from e

        # Should never reach here, but for type safety
        raise ServerError(f"Request failed after {self.MAX_RETRIES} retries")

    # Convenience methods for HTTP verbs

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET request"""
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict[str, Any]) -> Any:
        """POST request"""
        return self._request("POST", path, json=json)

    def patch(self, path: str, json: dict[str, Any]) -> Any:
        """PATCH request"""
        return self._request("PATCH", path, json=json)

    def delete(self, path: str) -> Any:
        """DELETE request"""
        return self._request("DELETE", path)
