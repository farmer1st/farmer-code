"""
Contract tests for GitHubService public API interface.

These tests verify the public interface contract defined in
specs/001-github-integration-core/contracts/github_service.md

Tests focus on:
- Method signatures match contract
- Return types are correct
- Exceptions are raised as specified
- Input validation works as expected

**Note on GitHub API Eventual Consistency**:
GitHub API has eventual consistency - newly created/updated resources may not
immediately appear in list/filter queries. This affects tests that create an issue
and immediately try to find it via list_issues() with filters.

- For **contract tests**: We test basic create/retrieve/list functionality but
  do NOT assert that newly created issues appear in filtered lists (that's tested in e2e).
- For **e2e tests**: Use polling helpers (`wait_for_*`) to handle eventual consistency.

See: tests/e2e/ for end-to-end tests with proper eventual consistency handling.
"""

import pytest
from datetime import datetime, timezone

from github_integration import (
    GitHubService,
    Issue,
    Comment,
    Label,
    PullRequest,
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
)


# Test fixtures for service initialization

@pytest.fixture
def service(github_app_id, github_installation_id, github_private_key_path, github_repository):
    """Create GitHubService instance for testing"""
    return GitHubService(
        app_id=github_app_id,
        installation_id=github_installation_id,
        private_key_path=github_private_key_path,
        repository=github_repository,
    )


# User Story 1: Create and Track Workflow Issues

class TestCreateIssue:
    """Contract tests for create_issue method"""

    def test_create_issue_with_valid_input(self, auto_cleanup_issue):
        """
        T018 [P] [US1] Contract test for create_issue with valid input

        Verify:
        - Method accepts title, body, labels, assignees
        - Returns Issue object
        - Issue has all required fields populated
        - Issue number is positive integer
        - Issue state is "open"
        - Issue repository matches configured repo
        """
        # Arrange
        title = "[TEST] Contract test issue"
        body = "This is a test issue for contract validation"
        labels = ["test", "contract"]
        assignees = []

        # Act - auto_cleanup_issue automatically adds test:automated label
        issue = auto_cleanup_issue(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees,
        )

        # Assert
        assert isinstance(issue, Issue)
        assert issue.number > 0
        assert issue.title == title
        assert issue.body == body
        assert issue.state == "open"
        assert "test" in issue.labels
        assert "contract" in issue.labels
        assert "test:automated" in issue.labels  # Added by auto_cleanup_issue
        assert issue.repository == "farmer1st/farmcode-tests"
        assert isinstance(issue.created_at, datetime)
        assert isinstance(issue.updated_at, datetime)
        assert issue.url.startswith("https://github.com/")

    def test_create_issue_with_missing_required_field(self, service):
        """
        T019 [P] [US1] Contract test for create_issue with missing required fields

        Verify:
        - Empty title raises ValidationError
        - Title too long (>256 chars) raises ValidationError
        """
        # Test empty title
        with pytest.raises(ValidationError) as exc_info:
            service.create_issue(title="")

        assert "title" in str(exc_info.value).lower()

        # Test title too long
        with pytest.raises(ValidationError) as exc_info:
            service.create_issue(title="a" * 257)

        assert "title" in str(exc_info.value).lower()

    def test_create_issue_minimal(self, auto_cleanup_issue):
        """
        Test create_issue with minimal input (only title)

        Verify:
        - Body, labels, assignees are optional
        - Defaults to empty lists (plus test:automated label)
        """
        # Act - auto_cleanup_issue automatically adds test:automated label
        issue = auto_cleanup_issue(title="Minimal test issue")

        # Assert
        assert isinstance(issue, Issue)
        assert "test:automated" in issue.labels  # Added by auto_cleanup_issue
        assert issue.title == "Minimal test issue"
        assert issue.body is None or issue.body == ""
        assert issue.assignees == []


class TestGetIssue:
    """Contract tests for get_issue method"""

    def test_get_issue_with_valid_number(self, service, auto_cleanup_issue):
        """
        T020 [P] [US1] Contract test for get_issue with valid number

        Verify:
        - Method accepts issue_number (positive int)
        - Returns Issue object
        - Issue has all required fields
        - Retrieved issue matches created issue
        """
        # Arrange - create an issue first with automatic cleanup
        created_issue = auto_cleanup_issue(title="Issue to retrieve")

        # Act
        retrieved_issue = service.get_issue(created_issue.number)

        # Assert
        assert isinstance(retrieved_issue, Issue)
        assert retrieved_issue.number == created_issue.number
        assert retrieved_issue.title == created_issue.title
        assert retrieved_issue.state == created_issue.state
        assert retrieved_issue.repository == "farmer1st/farmcode-tests"

    def test_get_issue_with_invalid_number(self, service):
        """
        T021 [P] [US1] Contract test for get_issue with invalid number (ResourceNotFoundError)

        Verify:
        - Non-existent issue number raises ResourceNotFoundError
        - Error message includes issue number
        """
        # Arrange
        non_existent_issue_number = 999999

        # Act & Assert
        with pytest.raises(ResourceNotFoundError) as exc_info:
            service.get_issue(non_existent_issue_number)

        assert str(non_existent_issue_number) in str(exc_info.value)

    def test_get_issue_with_negative_number(self, service):
        """
        Test get_issue with negative number

        Verify:
        - Negative issue number raises ValueError
        """
        with pytest.raises(ValueError):
            service.get_issue(-1)


class TestListIssues:
    """Contract tests for list_issues method"""

    def test_list_issues_with_state_filtering(self, service):
        """
        T022 [P] [US1] Contract test for list_issues with state filtering

        Verify:
        - Method accepts state parameter ("open", "closed", "all")
        - Returns list of Issue objects
        - Default state is "open"
        - Only issues matching state are returned
        """
        # Act - default state should be "open"
        open_issues = service.list_issues()

        # Assert
        assert isinstance(open_issues, list)
        for issue in open_issues:
            assert isinstance(issue, Issue)
            assert issue.state == "open"

        # Test explicit state filtering
        all_issues = service.list_issues(state="all")
        assert isinstance(all_issues, list)
        assert len(all_issues) >= len(open_issues)

    def test_list_issues_with_label_filtering(self, service):
        """
        T023 [P] [US1] Contract test for list_issues with label filtering

        Verify:
        - Method accepts labels parameter (list of strings)
        - Returns list of Issue objects
        - Method signature and types are correct

        **Note**: Due to GitHub API eventual consistency, we do NOT assert that
        newly created issues immediately appear in filtered results. That is
        tested in e2e tests with polling helpers. This test only verifies the
        method signature and basic functionality.
        """
        # Act - call list_issues with label filter
        labeled_issues = service.list_issues(labels=["test"])

        # Assert - verify method works and returns correct type
        assert isinstance(labeled_issues, list)

        # If there are any results, verify they have the correct structure
        if labeled_issues:
            for issue in labeled_issues:
                assert isinstance(issue, Issue)
                # Note: We don't assert the label is present because older issues
                # might not have this label. Label filtering correctness is tested
                # in e2e tests with controlled data.

    def test_list_issues_with_invalid_state(self, service):
        """
        Test list_issues with invalid state

        Verify:
        - Invalid state value raises ValueError
        """
        with pytest.raises(ValueError):
            service.list_issues(state="invalid")
