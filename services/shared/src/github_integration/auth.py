"""
GitHub App Authentication

Handles JWT generation and installation access token management with caching.
"""

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import jwt
import requests

from .errors import AuthenticationError
from .logger import logger


@dataclass
class InstallationToken:
    """
    Cached installation access token with expiration tracking.

    Attributes:
        token: The access token string
        expires_at: When the token expires (UTC)
    """

    token: str
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if token is expired (with 5-minute buffer for safety)"""
        buffer_seconds = 300  # 5 minutes
        now = datetime.now(UTC)
        expires_with_buffer = self.expires_at.timestamp() - buffer_seconds
        return now.timestamp() >= expires_with_buffer


class GitHubAppAuth:
    """
    Manages GitHub App authentication with JWT generation and token caching.

    GitHub App authentication flow:
    1. Generate JWT using App ID and private key (valid for 10 minutes)
    2. Use JWT to request installation access token (valid for 1 hour)
    3. Cache installation token until expiration
    4. Use installation token for all API requests
    """

    def __init__(self, app_id: int, installation_id: int, private_key_path: str) -> None:
        """
        Initialize GitHub App authentication.

        Args:
            app_id: GitHub App ID (e.g., 2578431)
            installation_id: Installation ID (e.g., 102211688)
            private_key_path: Path to PEM file (must have permissions 600)

        Raises:
            FileNotFoundError: If PEM file doesn't exist
            PermissionError: If PEM file permissions != 600
            AuthenticationError: If PEM file is invalid
        """
        self.app_id = app_id
        self.installation_id = installation_id
        self.private_key_path = Path(private_key_path)

        # Validate PEM file exists
        if not self.private_key_path.exists():
            raise FileNotFoundError(f"GitHub App private key not found: {self.private_key_path}")

        # Validate PEM file permissions (must be 600)
        if self.private_key_path.stat().st_mode & 0o777 != 0o600:
            raise PermissionError(
                f"GitHub App private key must have permissions 600: {self.private_key_path}"
            )

        # Load private key
        try:
            self.private_key = self.private_key_path.read_text()
        except Exception as e:
            raise AuthenticationError(f"Failed to read private key: {e}") from e

        # Token cache
        self._cached_token: InstallationToken | None = None

    def _generate_jwt(self) -> str:
        """
        Generate JWT for GitHub App authentication.

        JWT is valid for 10 minutes and used to request installation token.

        Returns:
            JWT string

        Raises:
            AuthenticationError: If JWT generation fails
        """
        now = int(time.time())
        payload = {
            "iat": now - 60,  # Issued at (60s ago to account for clock skew)
            "exp": now + 600,  # Expires in 10 minutes
            "iss": self.app_id,  # GitHub App ID
        }

        try:
            token = jwt.encode(payload, self.private_key, algorithm="RS256")
            logger.info(
                "Generated GitHub App JWT",
                extra={
                    "context": {
                        "app_id": self.app_id,
                        "expires_in_seconds": 600,
                    }
                },
            )
            return token
        except Exception as e:
            raise AuthenticationError(f"Failed to generate JWT: {e}") from e

    def _fetch_installation_token(self) -> InstallationToken:
        """
        Fetch installation access token using JWT.

        Returns:
            InstallationToken with token and expiration

        Raises:
            AuthenticationError: If token fetch fails
        """
        jwt_token = self._generate_jwt()

        url = f"https://api.github.com/app/installations/{self.installation_id}/access_tokens"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            response = requests.post(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            token = data["token"]
            expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))

            logger.info(
                "Fetched GitHub installation access token",
                extra={
                    "context": {
                        "installation_id": self.installation_id,
                        "expires_at": expires_at.isoformat(),
                    }
                },
            )

            return InstallationToken(token=token, expires_at=expires_at)

        except requests.HTTPError as e:
            raise AuthenticationError(
                f"Failed to fetch installation token: {e.response.status_code} {e.response.text}"
            ) from e
        except Exception as e:
            raise AuthenticationError(f"Failed to fetch installation token: {e}") from e

    def get_installation_token(self) -> str:
        """
        Get cached installation access token (or fetch new one if expired).

        This is the main method callers should use. It handles caching automatically.

        Returns:
            Installation access token string

        Raises:
            AuthenticationError: If token fetch fails
        """
        # Return cached token if valid
        if self._cached_token and not self._cached_token.is_expired():
            logger.debug(
                "Using cached installation token",
                extra={"context": {"expires_at": self._cached_token.expires_at.isoformat()}},
            )
            return self._cached_token.token

        # Fetch new token
        logger.info("Installation token expired or not cached, fetching new token")
        self._cached_token = self._fetch_installation_token()
        return self._cached_token.token
