"""
Unit Tests for Retry Logic

Tests the retry behavior of GitHubAPIClient for various error scenarios:
- Server errors (5xx) trigger retries
- Network errors (ConnectionError, Timeout) trigger retries
- Client errors (404, 429) do not trigger retries
- Max retries respected
- Retry delay applied between attempts
"""

import time
from unittest.mock import MagicMock, patch

import pytest
import requests
from src.github_integration.client import GitHubAPIClient
from src.github_integration.errors import (
    RateLimitExceeded,
    ResourceNotFoundError,
    ServerError,
)


@pytest.fixture
def mock_auth():
    """Create a mock GitHubAppAuth instance"""
    auth = MagicMock()
    auth.get_installation_token.return_value = "test-token-12345"
    return auth


@pytest.fixture
def client(mock_auth):
    """Create a GitHubAPIClient with mocked auth"""
    return GitHubAPIClient(auth=mock_auth, repository="owner/repo")


class TestRetryOnServerErrors:
    """Tests for retry behavior on 5xx server errors"""

    def test_retry_on_500_then_success(self, client):
        """Should retry on 500 error and succeed on second attempt"""
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = '{"id": 1}'
        mock_response_success.json.return_value = {"id": 1}

        with patch("src.github_integration.client.requests.request") as mock_request:
            with patch("src.github_integration.client.time.sleep") as mock_sleep:
                mock_request.side_effect = [mock_response_fail, mock_response_success]

                result = client.get("/test")

                assert result == {"id": 1}
                assert mock_request.call_count == 2
                mock_sleep.assert_called_once_with(1)  # 1 second retry delay

    def test_retry_on_502_bad_gateway(self, client):
        """Should retry on 502 Bad Gateway error"""
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 502
        mock_response_fail.text = "Bad Gateway"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = '{"status": "ok"}'
        mock_response_success.json.return_value = {"status": "ok"}

        with patch("src.github_integration.client.requests.request") as mock_request:
            with patch("src.github_integration.client.time.sleep"):
                mock_request.side_effect = [mock_response_fail, mock_response_success]

                result = client.get("/test")

                assert result == {"status": "ok"}
                assert mock_request.call_count == 2

    def test_retry_on_503_service_unavailable(self, client):
        """Should retry on 503 Service Unavailable error"""
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 503
        mock_response_fail.text = "Service Unavailable"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = '{"result": "done"}'
        mock_response_success.json.return_value = {"result": "done"}

        with patch("src.github_integration.client.requests.request") as mock_request:
            with patch("src.github_integration.client.time.sleep"):
                mock_request.side_effect = [mock_response_fail, mock_response_success]

                result = client.get("/test")

                assert result == {"result": "done"}

    def test_max_retries_exhausted_raises_server_error(self, client):
        """Should raise ServerError after exhausting all retries"""
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal Server Error"

        with patch("src.github_integration.client.requests.request") as mock_request:
            with patch("src.github_integration.client.time.sleep") as mock_sleep:
                mock_request.return_value = mock_response_fail

                with pytest.raises(ServerError) as exc_info:
                    client.get("/test")

                assert "after 3 retries" in str(exc_info.value)
                assert exc_info.value.status_code == 500
                assert mock_request.call_count == 3  # MAX_RETRIES
                assert mock_sleep.call_count == 2  # Sleeps between retries

    def test_retry_delay_is_one_second(self, client):
        """Should wait 1 second between retry attempts"""
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Error"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = "{}"
        mock_response_success.json.return_value = {}

        with patch("src.github_integration.client.requests.request") as mock_request:
            with patch("src.github_integration.client.time.sleep") as mock_sleep:
                mock_request.side_effect = [
                    mock_response_fail,
                    mock_response_fail,
                    mock_response_success,
                ]

                client.get("/test")

                # Should sleep twice with RETRY_DELAY (1 second)
                assert mock_sleep.call_count == 2
                mock_sleep.assert_any_call(1)


class TestRetryOnNetworkErrors:
    """Tests for retry behavior on network errors"""

    def test_retry_on_connection_error(self, client):
        """Should retry on ConnectionError"""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = '{"id": 42}'
        mock_response_success.json.return_value = {"id": 42}

        with patch("src.github_integration.client.requests.request") as mock_request:
            with patch("src.github_integration.client.time.sleep"):
                mock_request.side_effect = [
                    requests.ConnectionError("Connection refused"),
                    mock_response_success,
                ]

                result = client.get("/test")

                assert result == {"id": 42}
                assert mock_request.call_count == 2

    def test_retry_on_timeout(self, client):
        """Should retry on Timeout"""
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = '{"success": true}'
        mock_response_success.json.return_value = {"success": True}

        with patch("src.github_integration.client.requests.request") as mock_request:
            with patch("src.github_integration.client.time.sleep"):
                mock_request.side_effect = [
                    requests.Timeout("Read timed out"),
                    mock_response_success,
                ]

                result = client.get("/test")

                assert result == {"success": True}
                assert mock_request.call_count == 2

    def test_network_error_exhausts_retries(self, client):
        """Should raise ServerError after network errors exhaust retries"""
        with patch("src.github_integration.client.requests.request") as mock_request:
            with patch("src.github_integration.client.time.sleep"):
                mock_request.side_effect = requests.ConnectionError("Connection refused")

                with pytest.raises(ServerError) as exc_info:
                    client.get("/test")

                assert "Network error" in str(exc_info.value)
                assert "3 retries" in str(exc_info.value)
                assert mock_request.call_count == 3


class TestNoRetryOnClientErrors:
    """Tests for scenarios that should NOT trigger retries"""

    def test_no_retry_on_404(self, client):
        """Should NOT retry on 404 Not Found - immediate failure"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.headers = {}

        with patch("src.github_integration.client.requests.request") as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(ResourceNotFoundError):
                client.get("/repos/owner/repo/issues/9999")

            # Should only make ONE request - no retries
            assert mock_request.call_count == 1

    def test_no_retry_on_rate_limit(self, client):
        """Should NOT retry on 429 Rate Limit - immediate failure"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {"X-RateLimit-Reset": str(int(time.time()) + 3600)}

        with patch("src.github_integration.client.requests.request") as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(RateLimitExceeded):
                client.get("/test")

            # Should only make ONE request - no retries
            assert mock_request.call_count == 1


class TestRateLimitHandling:
    """Tests for rate limit detection and handling"""

    def test_rate_limit_extracts_wait_time_from_header(self, client):
        """Should extract wait time from X-RateLimit-Reset header"""
        # Implementation enforces minimum 1 hour, so test with 2 hours
        future_time = int(time.time()) + 7200  # 2 hours from now
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {"X-RateLimit-Reset": str(future_time)}

        with patch("src.github_integration.client.requests.request") as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(RateLimitExceeded) as exc_info:
                client.get("/test")

            # Wait time should be approximately 7200 seconds (2 hours)
            assert exc_info.value.wait_seconds >= 7199
            assert exc_info.value.wait_seconds <= 7201

    def test_rate_limit_defaults_to_one_hour_if_no_header(self, client):
        """Should default to 1 hour wait time if header is missing"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {}

        with patch("src.github_integration.client.requests.request") as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(RateLimitExceeded) as exc_info:
                client.get("/test")

            # Should default to at least 1 hour (3600 seconds)
            assert exc_info.value.wait_seconds >= 3600


class TestSuccessfulRequests:
    """Tests for successful request handling"""

    def test_success_on_first_attempt(self, client):
        """Should succeed without retries on 200 response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "value"}'
        mock_response.json.return_value = {"data": "value"}

        with patch("src.github_integration.client.requests.request") as mock_request:
            mock_request.return_value = mock_response

            result = client.get("/test")

            assert result == {"data": "value"}
            assert mock_request.call_count == 1

    def test_empty_response_returns_empty_dict(self, client):
        """Should return empty dict for empty response body"""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.text = ""

        with patch("src.github_integration.client.requests.request") as mock_request:
            mock_request.return_value = mock_response

            result = client.delete("/test")

            assert result == {}

    def test_authentication_header_included(self, client, mock_auth):
        """Should include Bearer token in Authorization header"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "{}"
        mock_response.json.return_value = {}

        with patch("src.github_integration.client.requests.request") as mock_request:
            mock_request.return_value = mock_response

            client.get("/test")

            call_args = mock_request.call_args
            headers = call_args.kwargs["headers"]
            assert headers["Authorization"] == "Bearer test-token-12345"
            mock_auth.get_installation_token.assert_called()
