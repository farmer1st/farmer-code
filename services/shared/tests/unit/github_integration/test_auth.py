"""
Unit Tests for Authentication Token Caching

Tests the GitHubAppAuth authentication and token caching behavior:
- JWT generation with correct payload
- Installation token caching behavior
- Token expiration with 5-minute buffer
- Token refresh when expired
- Error handling for authentication failures
"""

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from src.github_integration.auth import GitHubAppAuth, InstallationToken
from src.github_integration.errors import AuthenticationError

# Dummy key content that passes file validation (actual key validation is mocked)
DUMMY_KEY_CONTENT = "-----BEGIN RSA PRIVATE KEY-----\ndummy\n-----END RSA PRIVATE KEY-----"


@pytest.fixture
def temp_private_key():
    """Create a temporary PEM file with proper permissions"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
        f.write(DUMMY_KEY_CONTENT)
        f.flush()
        key_path = Path(f.name)
        key_path.chmod(0o600)
        yield str(key_path)
        key_path.unlink()


class TestInstallationToken:
    """Tests for InstallationToken dataclass"""

    def test_token_not_expired_when_fresh(self):
        """Token should not be expired when recently created"""
        token = InstallationToken(
            token="test-token",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        assert not token.is_expired()

    def test_token_expired_when_past(self):
        """Token should be expired when expires_at is in the past"""
        token = InstallationToken(
            token="test-token",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert token.is_expired()

    def test_token_expired_within_5_minute_buffer(self):
        """Token should be considered expired within 5-minute buffer"""
        # Token expires in 4 minutes - should be considered expired due to buffer
        token = InstallationToken(
            token="test-token",
            expires_at=datetime.now(UTC) + timedelta(minutes=4),
        )
        assert token.is_expired()

    def test_token_valid_outside_5_minute_buffer(self):
        """Token should be valid when more than 5 minutes from expiration"""
        # Token expires in 6 minutes - should still be valid
        token = InstallationToken(
            token="test-token",
            expires_at=datetime.now(UTC) + timedelta(minutes=6),
        )
        assert not token.is_expired()


class TestGitHubAppAuthInitialization:
    """Tests for GitHubAppAuth initialization"""

    def test_raises_file_not_found_for_missing_key(self):
        """Should raise FileNotFoundError if PEM file doesn't exist"""
        with pytest.raises(FileNotFoundError) as exc_info:
            GitHubAppAuth(
                app_id=12345,
                installation_id=67890,
                private_key_path="/nonexistent/path/key.pem",
            )
        assert "not found" in str(exc_info.value)

    def test_raises_permission_error_for_wrong_permissions(self):
        """Should raise PermissionError if PEM file has wrong permissions"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write(DUMMY_KEY_CONTENT)
            key_path = Path(f.name)
            key_path.chmod(0o644)  # Wrong permissions

            try:
                with pytest.raises(PermissionError) as exc_info:
                    GitHubAppAuth(
                        app_id=12345,
                        installation_id=67890,
                        private_key_path=str(key_path),
                    )
                assert "permissions 600" in str(exc_info.value)
            finally:
                key_path.unlink()

    def test_successful_initialization(self, temp_private_key):
        """Should initialize successfully with valid PEM file"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )
        assert auth.app_id == 12345
        assert auth.installation_id == 67890
        assert auth._cached_token is None


class TestTokenCaching:
    """Tests for token caching behavior"""

    def test_caches_token_after_first_fetch(self, temp_private_key):
        """Should cache token after first fetch"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "cached-token-12345",
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        }

        with patch("src.github_integration.auth.jwt.encode") as mock_jwt:
            mock_jwt.return_value = "mocked-jwt-token"

            with patch("src.github_integration.auth.requests.post") as mock_post:
                mock_post.return_value = mock_response

                # First call - should fetch
                token1 = auth.get_installation_token()
                assert token1 == "cached-token-12345"
                assert mock_post.call_count == 1

                # Second call - should use cache
                token2 = auth.get_installation_token()
                assert token2 == "cached-token-12345"
                assert mock_post.call_count == 1  # No additional API call

    def test_refreshes_token_when_expired(self, temp_private_key):
        """Should fetch new token when cached token is expired"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        # Set up an expired cached token
        auth._cached_token = InstallationToken(
            token="old-expired-token",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "new-fresh-token",
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        }

        with patch("src.github_integration.auth.jwt.encode") as mock_jwt:
            mock_jwt.return_value = "mocked-jwt-token"

            with patch("src.github_integration.auth.requests.post") as mock_post:
                mock_post.return_value = mock_response

                token = auth.get_installation_token()

                assert token == "new-fresh-token"
                assert mock_post.call_count == 1

    def test_refreshes_token_within_buffer_period(self, temp_private_key):
        """Should fetch new token when within 5-minute buffer period"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        # Token expires in 3 minutes (within 5-minute buffer)
        auth._cached_token = InstallationToken(
            token="almost-expired-token",
            expires_at=datetime.now(UTC) + timedelta(minutes=3),
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "refreshed-token",
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        }

        with patch("src.github_integration.auth.jwt.encode") as mock_jwt:
            mock_jwt.return_value = "mocked-jwt-token"

            with patch("src.github_integration.auth.requests.post") as mock_post:
                mock_post.return_value = mock_response

                token = auth.get_installation_token()

                assert token == "refreshed-token"
                assert mock_post.call_count == 1


class TestJWTGeneration:
    """Tests for JWT generation"""

    def test_jwt_generation_uses_correct_algorithm(self, temp_private_key):
        """JWT should be generated with RS256 algorithm"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        with patch("src.github_integration.auth.jwt.encode") as mock_encode:
            mock_encode.return_value = "mocked-jwt"

            auth._generate_jwt()

            mock_encode.assert_called_once()
            call_args = mock_encode.call_args
            assert call_args.kwargs.get("algorithm") == "RS256" or call_args.args[2] == "RS256"

    def test_jwt_payload_contains_app_id(self, temp_private_key):
        """JWT payload should contain app_id as 'iss' claim"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        with patch("src.github_integration.auth.jwt.encode") as mock_encode:
            mock_encode.return_value = "mocked-jwt"

            auth._generate_jwt()

            call_args = mock_encode.call_args
            payload = call_args.args[0]
            assert payload["iss"] == 12345

    def test_jwt_payload_contains_time_claims(self, temp_private_key):
        """JWT payload should contain iat and exp claims"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        with patch("src.github_integration.auth.time.time") as mock_time:
            mock_time.return_value = 1000000

            with patch("src.github_integration.auth.jwt.encode") as mock_encode:
                mock_encode.return_value = "mocked-jwt"

                auth._generate_jwt()

                call_args = mock_encode.call_args
                payload = call_args.args[0]

                # iat should be 60 seconds before 'now' for clock skew
                assert payload["iat"] == 1000000 - 60
                # exp should be 10 minutes (600s) after 'now'
                assert payload["exp"] == 1000000 + 600


class TestErrorHandling:
    """Tests for authentication error handling"""

    def test_raises_auth_error_on_http_error(self, temp_private_key):
        """Should raise AuthenticationError on HTTP error response"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Bad credentials"
        mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)

        with patch("src.github_integration.auth.jwt.encode") as mock_jwt:
            mock_jwt.return_value = "mocked-jwt-token"

            with patch("src.github_integration.auth.requests.post") as mock_post:
                mock_post.return_value = mock_response

                with pytest.raises(AuthenticationError) as exc_info:
                    auth.get_installation_token()

                assert "Failed to fetch installation token" in str(exc_info.value)

    def test_raises_auth_error_on_network_error(self, temp_private_key):
        """Should raise AuthenticationError on network errors"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        with patch("src.github_integration.auth.jwt.encode") as mock_jwt:
            mock_jwt.return_value = "mocked-jwt-token"

            with patch("src.github_integration.auth.requests.post") as mock_post:
                mock_post.side_effect = requests.ConnectionError("Connection refused")

                with pytest.raises(AuthenticationError) as exc_info:
                    auth.get_installation_token()

                assert "Failed to fetch installation token" in str(exc_info.value)

    def test_raises_auth_error_on_jwt_generation_failure(self, temp_private_key):
        """Should raise AuthenticationError if JWT generation fails"""
        auth = GitHubAppAuth(
            app_id=12345,
            installation_id=67890,
            private_key_path=temp_private_key,
        )

        with patch("src.github_integration.auth.jwt.encode") as mock_jwt:
            mock_jwt.side_effect = Exception("Invalid key format")

            with pytest.raises(AuthenticationError) as exc_info:
                auth.get_installation_token()

            assert "Failed to generate JWT" in str(exc_info.value)
