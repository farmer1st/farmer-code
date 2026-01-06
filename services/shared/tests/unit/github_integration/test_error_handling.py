"""
Unit Tests for Error Handling

Tests all custom exception types and their attributes:
- GitHubAPIError (base exception)
- AuthenticationError
- ResourceNotFoundError
- ValidationError
- RateLimitExceeded
- ServerError
"""

import pytest
from src.github_integration.errors import (
    AuthenticationError,
    GitHubAPIError,
    RateLimitExceeded,
    ResourceNotFoundError,
    ServerError,
    ValidationError,
)


class TestGitHubAPIError:
    """Tests for base GitHubAPIError exception"""

    def test_creates_with_message(self):
        """Should create exception with message"""
        error = GitHubAPIError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"

    def test_default_error_code(self):
        """Should have default error code 'UNKNOWN_ERROR'"""
        error = GitHubAPIError("Test error")
        assert error.error_code == "UNKNOWN_ERROR"

    def test_custom_error_code(self):
        """Should accept custom error code"""
        error = GitHubAPIError("Test error", error_code="CUSTOM_CODE")
        assert error.error_code == "CUSTOM_CODE"

    def test_is_exception(self):
        """Should be an Exception subclass"""
        error = GitHubAPIError("Test")
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self):
        """Should be raisable and catchable"""
        with pytest.raises(GitHubAPIError) as exc_info:
            raise GitHubAPIError("Raised error")
        assert exc_info.value.message == "Raised error"


class TestAuthenticationError:
    """Tests for AuthenticationError exception"""

    def test_creates_with_message(self):
        """Should create with message"""
        error = AuthenticationError("Invalid credentials")
        assert str(error) == "Invalid credentials"
        assert error.message == "Invalid credentials"

    def test_has_authentication_error_code(self):
        """Should have error code 'AUTHENTICATION_ERROR'"""
        error = AuthenticationError("Test")
        assert error.error_code == "AUTHENTICATION_ERROR"

    def test_inherits_from_base(self):
        """Should inherit from GitHubAPIError"""
        error = AuthenticationError("Test")
        assert isinstance(error, GitHubAPIError)
        assert isinstance(error, Exception)

    def test_catches_as_github_api_error(self):
        """Should be catchable as GitHubAPIError"""
        with pytest.raises(GitHubAPIError):
            raise AuthenticationError("Auth failed")


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError exception"""

    def test_creates_with_resource_type_and_identifier(self):
        """Should create with resource type and identifier"""
        error = ResourceNotFoundError("Issue", 42)
        assert error.resource_type == "Issue"
        assert error.identifier == 42

    def test_generates_message_from_params(self):
        """Should generate message from resource type and identifier"""
        error = ResourceNotFoundError("Pull Request", 123)
        assert str(error) == "Pull Request not found: 123"
        assert error.message == "Pull Request not found: 123"

    def test_accepts_string_identifier(self):
        """Should accept string identifier"""
        error = ResourceNotFoundError("Branch", "feature/test")
        assert error.identifier == "feature/test"
        assert "feature/test" in str(error)

    def test_has_resource_not_found_error_code(self):
        """Should have error code 'RESOURCE_NOT_FOUND'"""
        error = ResourceNotFoundError("Issue", 1)
        assert error.error_code == "RESOURCE_NOT_FOUND"

    def test_inherits_from_base(self):
        """Should inherit from GitHubAPIError"""
        error = ResourceNotFoundError("Repo", "owner/repo")
        assert isinstance(error, GitHubAPIError)


class TestValidationError:
    """Tests for ValidationError exception"""

    def test_creates_with_message(self):
        """Should create with message"""
        error = ValidationError("Title cannot be empty")
        assert str(error) == "Title cannot be empty"
        assert error.message == "Title cannot be empty"

    def test_field_is_optional(self):
        """Field should be optional and default to None"""
        error = ValidationError("Some error")
        assert error.field is None

    def test_stores_field_name(self):
        """Should store field name when provided"""
        error = ValidationError("Title too long", field="title")
        assert error.field == "title"

    def test_has_validation_error_code(self):
        """Should have error code 'VALIDATION_ERROR'"""
        error = ValidationError("Test")
        assert error.error_code == "VALIDATION_ERROR"

    def test_inherits_from_base(self):
        """Should inherit from GitHubAPIError"""
        error = ValidationError("Test")
        assert isinstance(error, GitHubAPIError)


class TestRateLimitExceeded:
    """Tests for RateLimitExceeded exception"""

    def test_creates_with_message_and_wait_time(self):
        """Should create with message and wait_seconds"""
        error = RateLimitExceeded("Rate limit hit", wait_seconds=3600)
        assert str(error) == "Rate limit hit"
        assert error.wait_seconds == 3600

    def test_stores_wait_seconds(self):
        """Should store wait_seconds attribute"""
        error = RateLimitExceeded("Please wait", wait_seconds=1800)
        assert error.wait_seconds == 1800

    def test_has_rate_limit_error_code(self):
        """Should have error code 'RATE_LIMIT_EXCEEDED'"""
        error = RateLimitExceeded("Test", wait_seconds=60)
        assert error.error_code == "RATE_LIMIT_EXCEEDED"

    def test_inherits_from_base(self):
        """Should inherit from GitHubAPIError"""
        error = RateLimitExceeded("Test", wait_seconds=60)
        assert isinstance(error, GitHubAPIError)

    def test_wait_seconds_accessible_when_caught(self):
        """wait_seconds should be accessible when exception is caught"""
        try:
            raise RateLimitExceeded("Rate limit", wait_seconds=7200)
        except RateLimitExceeded as e:
            assert e.wait_seconds == 7200


class TestServerError:
    """Tests for ServerError exception"""

    def test_creates_with_message(self):
        """Should create with message"""
        error = ServerError("Internal server error")
        assert str(error) == "Internal server error"
        assert error.message == "Internal server error"

    def test_status_code_is_optional(self):
        """status_code should be optional and default to None"""
        error = ServerError("Network timeout")
        assert error.status_code is None

    def test_stores_status_code(self):
        """Should store status_code when provided"""
        error = ServerError("Bad Gateway", status_code=502)
        assert error.status_code == 502

    def test_has_server_error_code(self):
        """Should have error code 'SERVER_ERROR'"""
        error = ServerError("Test")
        assert error.error_code == "SERVER_ERROR"

    def test_inherits_from_base(self):
        """Should inherit from GitHubAPIError"""
        error = ServerError("Test")
        assert isinstance(error, GitHubAPIError)

    def test_various_5xx_status_codes(self):
        """Should handle various 5xx status codes"""
        codes = [500, 501, 502, 503, 504]
        for code in codes:
            error = ServerError(f"Error {code}", status_code=code)
            assert error.status_code == code


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy"""

    def test_all_errors_inherit_from_base(self):
        """All custom errors should inherit from GitHubAPIError"""
        errors = [
            AuthenticationError("test"),
            ResourceNotFoundError("type", "id"),
            ValidationError("test"),
            RateLimitExceeded("test", wait_seconds=60),
            ServerError("test"),
        ]
        for error in errors:
            assert isinstance(error, GitHubAPIError)
            assert isinstance(error, Exception)

    def test_catch_all_as_github_api_error(self):
        """All custom errors should be catchable as GitHubAPIError"""
        errors_to_raise = [
            AuthenticationError("auth"),
            ResourceNotFoundError("Resource", 1),
            ValidationError("invalid"),
            RateLimitExceeded("rate", wait_seconds=60),
            ServerError("server"),
        ]

        for error in errors_to_raise:
            with pytest.raises(GitHubAPIError):
                raise error

    def test_specific_catch_before_base(self):
        """Specific exceptions should be catchable before base"""
        try:
            raise RateLimitExceeded("Rate limit", wait_seconds=3600)
        except RateLimitExceeded as e:
            assert e.wait_seconds == 3600
        except GitHubAPIError:
            pytest.fail("Should have caught RateLimitExceeded specifically")


class TestErrorMessages:
    """Tests for error message formatting"""

    def test_authentication_error_message_preserved(self):
        """AuthenticationError should preserve full message"""
        msg = "Failed to read PEM file: /path/to/key.pem"
        error = AuthenticationError(msg)
        assert str(error) == msg

    def test_resource_not_found_formats_message(self):
        """ResourceNotFoundError should format message with type and id"""
        error = ResourceNotFoundError("Issue", 12345)
        assert "Issue" in str(error)
        assert "12345" in str(error)
        assert "not found" in str(error)

    def test_validation_error_message_preserved(self):
        """ValidationError should preserve full message"""
        msg = "Title exceeds 256 character limit"
        error = ValidationError(msg, field="title")
        assert str(error) == msg

    def test_rate_limit_message_preserved(self):
        """RateLimitExceeded should preserve full message"""
        msg = "GitHub rate limit exceeded. Wait 3600 seconds"
        error = RateLimitExceeded(msg, wait_seconds=3600)
        assert str(error) == msg

    def test_server_error_message_preserved(self):
        """ServerError should preserve full message"""
        msg = "GitHub API returned 502 Bad Gateway after 3 retries"
        error = ServerError(msg, status_code=502)
        assert str(error) == msg
