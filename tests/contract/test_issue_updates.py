"""
Contract tests for issue update and close operations.

These operations are needed for test cleanup and issue lifecycle management.
"""

import pytest

from github_integration import GitHubService, ResourceNotFoundError, ValidationError


@pytest.fixture
def service(github_app_id, github_installation_id, github_private_key_path, github_repository):
    """Create GitHubService instance for testing"""
    return GitHubService(
        app_id=github_app_id,
        installation_id=github_installation_id,
        private_key_path=github_private_key_path,
        repository=github_repository,
    )


@pytest.mark.contract
class TestUpdateIssue:
    """Contract tests for update_issue method"""

    def test_update_issue_title(self, service, auto_cleanup_issue):
        """
        Update only the title of an issue

        Verify:
        - Title is updated
        - Other fields remain unchanged
        """
        # Create test issue with automatic cleanup
        issue = auto_cleanup_issue(
            title="Original title",
            body="Original body"
        )

        # Update title only
        updated = service.update_issue(issue.number, title="New title")

        # Verify
        assert updated.number == issue.number
        assert updated.title == "New title"
        assert updated.body == "Original body"
        assert updated.state == "open"

    def test_update_issue_state(self, service, auto_cleanup_issue):
        """
        Update only the state (close an issue)

        Verify:
        - State changes from "open" to "closed"
        - Other fields remain unchanged
        """
        # Create test issue with automatic cleanup
        issue = auto_cleanup_issue(title="Test issue")

        # Close it
        updated = service.update_issue(issue.number, state="closed")

        # Verify
        assert updated.number == issue.number
        assert updated.state == "closed"
        assert updated.title == issue.title

    def test_update_issue_multiple_fields(self, service, auto_cleanup_issue):
        """
        Update multiple fields at once

        Verify:
        - All specified fields are updated
        - Unspecified fields remain unchanged
        """
        # Create test issue with automatic cleanup
        issue = auto_cleanup_issue(
            title="Original",
            body="Original body"
        )

        # Update multiple fields
        updated = service.update_issue(
            issue.number,
            title="Updated title",
            body="Updated body",
            state="closed"
        )

        # Verify
        assert updated.title == "Updated title"
        assert updated.body == "Updated body"
        assert updated.state == "closed"

    def test_update_issue_invalid_state(self, service, auto_cleanup_issue):
        """
        Verify ValueError raised for invalid state

        Verify:
        - Invalid state raises ValueError
        - Issue is not modified
        """
        # Create test issue with automatic cleanup
        issue = auto_cleanup_issue(title="Test")

        # Try invalid state
        with pytest.raises(ValueError) as exc_info:
            service.update_issue(issue.number, state="invalid")

        assert "state" in str(exc_info.value).lower()

    def test_update_issue_not_found(self, service):
        """
        Verify ResourceNotFoundError for non-existent issue

        Verify:
        - Non-existent issue number raises ResourceNotFoundError
        """
        with pytest.raises(ResourceNotFoundError):
            service.update_issue(999999, title="New title")

    def test_update_issue_empty_title(self, service, auto_cleanup_issue):
        """
        Verify ValidationError for empty title

        Verify:
        - Empty title raises ValidationError
        """
        # Create test issue with automatic cleanup
        issue = auto_cleanup_issue(title="Test")

        # Try empty title
        with pytest.raises(ValidationError) as exc_info:
            service.update_issue(issue.number, title="")

        assert "title" in str(exc_info.value).lower()


@pytest.mark.contract
class TestCloseIssue:
    """Contract tests for close_issue method"""

    def test_close_open_issue(self, service, auto_cleanup_issue):
        """
        Close an open issue

        Verify:
        - State changes to "closed"
        - Returns updated issue
        """
        # Create test issue with automatic cleanup
        issue = auto_cleanup_issue(title="Test issue")
        assert issue.state == "open"

        # Close it
        closed = service.close_issue(issue.number)

        # Verify
        assert closed.number == issue.number
        assert closed.state == "closed"

    def test_close_already_closed_issue(self, service, auto_cleanup_issue):
        """
        Close an already-closed issue (idempotent)

        Verify:
        - No error raised
        - State remains "closed"
        """
        # Create issue and close it
        issue = auto_cleanup_issue(title="Test")
        service.close_issue(issue.number)

        # Close again
        closed_again = service.close_issue(issue.number)

        # Verify - still closed, no error
        assert closed_again.state == "closed"

    def test_close_nonexistent_issue(self, service):
        """
        Verify ResourceNotFoundError for non-existent issue

        Verify:
        - Non-existent issue raises ResourceNotFoundError
        """
        with pytest.raises(ResourceNotFoundError):
            service.close_issue(999999)

    def test_close_invalid_issue_number(self, service):
        """
        Verify ValueError for negative issue number

        Verify:
        - Negative issue number raises ValueError
        """
        with pytest.raises(ValueError):
            service.close_issue(-1)
