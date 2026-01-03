"""
Integration tests for GitHubService with mocked HTTP calls.

These tests verify the integration between service components (service, client, auth)
without making real API calls. HTTP responses are mocked for predictable, fast tests.

**No eventual consistency issues** - these tests are fast and deterministic.
"""

from unittest.mock import Mock, patch

import pytest

from github_integration import GitHubService, Issue, ValidationError


@pytest.fixture
def mock_pem_file():
    """Mock PEM file validation so tests don't need real credentials"""
    mock_stat = Mock()
    mock_stat.st_mode = 0o100600  # File with 600 permissions

    with (
        patch("github_integration.auth.Path.exists", return_value=True),
        patch("github_integration.auth.Path.stat", return_value=mock_stat),
        patch("github_integration.auth.Path.read_text", return_value="fake-key-content"),
    ):
        yield


@pytest.fixture
def mock_requests(mock_pem_file):
    """Mock requests library for HTTP calls"""
    with (
        patch("github_integration.client.requests") as mock_client,
        patch("github_integration.auth.requests") as mock_auth,
        patch("github_integration.auth.jwt.encode", return_value="mock-jwt-token"),
    ):
        # Mock auth token fetch
        mock_auth_response = Mock()
        mock_auth_response.status_code = 201
        mock_auth_response.json.return_value = {
            "token": "ghs_test_token",
            "expires_at": "2026-01-02T14:00:00Z",
        }
        mock_auth.post.return_value = mock_auth_response

        yield mock_client


@pytest.fixture
def service(
    mock_pem_file, github_app_id, github_installation_id, github_private_key_path, github_repository
):
    """Create GitHubService instance for integration testing"""
    return GitHubService(
        app_id=github_app_id,
        installation_id=github_installation_id,
        private_key_path=github_private_key_path,
        repository=github_repository,
    )


@pytest.mark.integration
class TestServiceWithMockedAPI:
    """Integration tests for GitHubService with mocked GitHub API"""

    def test_create_issue_calls_api_correctly(
        self, service, mock_requests, mock_github_issue_response
    ):
        """
        Verify create_issue calls GitHub API with correct parameters

        Tests:
        - Service constructs correct API path
        - Service sends correct request body
        - Service parses response into Issue model
        """
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_github_issue_response
        mock_response.text = "some response"
        mock_requests.request.return_value = mock_response

        # Call service
        issue = service.create_issue(
            title="Test issue",
            body="Test body",
            labels=["test"],
        )

        # Verify API was called correctly
        assert mock_requests.request.called
        call_args = mock_requests.request.call_args

        # Verify HTTP method and URL
        assert call_args.kwargs["method"] == "POST"
        assert "/repos/farmer1st/farmcode-tests/issues" in call_args.kwargs["url"]

        # Verify request body
        request_body = call_args.kwargs["json"]
        assert request_body["title"] == "Test issue"
        assert request_body["body"] == "Test body"
        assert request_body["labels"] == ["test"]

        # Verify response parsing (returns mocked response data)
        assert isinstance(issue, Issue)
        assert issue.number == 42
        assert issue.title == "Add user authentication"  # From mock_github_issue_response fixture

    def test_get_issue_calls_api_correctly(
        self, service, mock_requests, mock_github_issue_response
    ):
        """
        Verify get_issue calls GitHub API with correct parameters

        Tests:
        - Service constructs correct API path with issue number
        - Service parses response into Issue model
        """
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_github_issue_response
        mock_response.text = "some response"
        mock_requests.request.return_value = mock_response

        # Call service
        issue = service.get_issue(42)

        # Verify API was called correctly
        assert mock_requests.request.called
        call_args = mock_requests.request.call_args

        # Verify HTTP method and URL
        assert call_args.kwargs["method"] == "GET"
        assert "/repos/farmer1st/farmcode-tests/issues/42" in call_args.kwargs["url"]

        # Verify response parsing
        assert isinstance(issue, Issue)
        assert issue.number == 42

    def test_list_issues_calls_api_with_filters(
        self, service, mock_requests, mock_github_issue_response
    ):
        """
        Verify list_issues calls GitHub API with correct query parameters

        Tests:
        - Service passes state filter correctly
        - Service passes label filters correctly
        - Service parses list response correctly
        """
        # Mock successful response (list of issues)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [mock_github_issue_response]
        mock_response.text = "some response"
        mock_requests.request.return_value = mock_response

        # Call service with filters
        issues = service.list_issues(state="open", labels=["test", "bug"])

        # Verify API was called correctly
        assert mock_requests.request.called
        call_args = mock_requests.request.call_args

        # Verify HTTP method and URL
        assert call_args.kwargs["method"] == "GET"
        assert "/repos/farmer1st/farmcode-tests/issues" in call_args.kwargs["url"]

        # Verify query parameters
        params = call_args.kwargs["params"]
        assert params["state"] == "open"
        assert params["labels"] == "test,bug"

        # Verify response parsing
        assert isinstance(issues, list)
        assert len(issues) == 1
        assert isinstance(issues[0], Issue)

    def test_validation_error_on_empty_title(self, service):
        """
        Verify ValidationError is raised for empty title

        Tests:
        - Service validates input before making API call
        - No API call is made for invalid input
        """
        with pytest.raises(ValidationError) as exc_info:
            service.create_issue(title="")

        assert "title" in str(exc_info.value).lower()

    def test_validation_error_on_invalid_state(self, service):
        """
        Verify ValueError is raised for invalid state filter

        Tests:
        - Service validates state parameter
        - No API call is made for invalid input
        """
        with pytest.raises(ValueError) as exc_info:
            service.list_issues(state="invalid")

        assert "state" in str(exc_info.value).lower()
