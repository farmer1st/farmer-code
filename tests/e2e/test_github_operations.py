"""
End-to-end tests for GitHub operations with real GitHub API.

These tests make actual API calls to GitHub (farmer1st/farmer-code-tests repository)
and verify complete workflows with real GitHub responses.

**Important**: These tests handle GitHub's eventual consistency using polling helpers.
GitHub API has eventual consistency - newly created/updated resources may not
immediately appear in list/filter queries. Tests use `wait_for_*` helpers to poll
until conditions are met (with 10s timeout).

Prerequisites:
- GitHub App must be installed on farmer1st/farmer-code-tests
- PEM file must exist at path specified in GITHUB_APP_PRIVATE_KEY_PATH
- GitHub API rate limit must not be exceeded
- Internet connection required

Run with: pytest tests/e2e/ -v -m e2e
"""

import pytest

from github_integration import GitHubService, Issue
from tests.conftest import wait_for_issue_in_list


@pytest.fixture
def service(github_app_id, github_installation_id, github_private_key_path, github_repository):
    """Create GitHubService instance for e2e testing"""
    return GitHubService(
        app_id=github_app_id,
        installation_id=github_installation_id,
        private_key_path=github_private_key_path,
        repository=github_repository,
    )


@pytest.mark.e2e
class TestFullIssueLifecycle:
    """
    T024 [P] [US1] E2E test for full issue lifecycle (create → retrieve → list)

    Tests the complete workflow with real GitHub API:
    1. Create issue with title, body, labels
    2. Retrieve issue by number
    3. Verify issue appears in list_issues (with polling for eventual consistency)
    4. Verify all data persisted correctly on GitHub
    """

    @pytest.mark.journey("ORC-001")
    def test_full_issue_lifecycle(self, service, auto_cleanup_issue):
        """
        Full e2e test: Create → Retrieve → List

        This test verifies:
        - Issue is created on GitHub
        - Issue can be retrieved by number
        - Issue appears in filtered lists (handles eventual consistency)
        - All data (title, body, labels) is persisted

        Note: Uses polling helpers to wait for GitHub's indexing/caching.
        """
        # Step 1: Create issue with automatic cleanup
        title = "[E2E TEST] Full lifecycle test"
        body = "This is an e2e test for the full issue lifecycle"
        labels = ["test", "e2e"]

        created_issue = auto_cleanup_issue(
            title=title,
            body=body,
            labels=labels,
        )

        # Verify creation
        assert isinstance(created_issue, Issue)
        assert created_issue.number > 0
        assert created_issue.title == title
        assert created_issue.body == body
        assert set(labels).issubset(set(created_issue.labels))
        assert "test:automated" in created_issue.labels  # Added by auto_cleanup_issue
        assert created_issue.state == "open"
        assert created_issue.repository == "farmer1st/farmer-code-tests"

        # Step 2: Retrieve issue by number
        retrieved_issue = service.get_issue(created_issue.number)

        # Verify retrieval
        assert retrieved_issue.number == created_issue.number
        assert retrieved_issue.title == created_issue.title
        assert retrieved_issue.body == created_issue.body
        assert set(labels).issubset(set(retrieved_issue.labels))
        assert retrieved_issue.state == created_issue.state

        # Step 3: Wait for issue to appear in list (handles eventual consistency)
        # Note: GitHub API may take a moment to index newly created issues
        assert wait_for_issue_in_list(service, created_issue.number, state="open", timeout=10.0), (
            f"Issue #{created_issue.number} did not appear in list after 10s"
        )

        # Step 4: Wait for issue to appear in label-filtered list
        # Note: Label indexing may have additional delay
        assert wait_for_issue_in_list(
            service, created_issue.number, labels=["test"], timeout=10.0
        ), f"Issue #{created_issue.number} did not appear in label-filtered list after 10s"

    @pytest.mark.journey("ORC-005")
    def test_create_multiple_issues(self, service, auto_cleanup_issue):
        """
        Test creating multiple issues in sequence

        Verifies:
        - Each issue gets unique issue number
        - All issues can be retrieved
        - All issues appear in list (with eventual consistency handling)

        Note: Uses polling to wait for GitHub's indexing of batch-created issues.
        """
        # Create 3 issues with automatic cleanup
        issues = []
        for i in range(3):
            issue = auto_cleanup_issue(
                title=f"[E2E TEST] Batch issue {i + 1}",
                body=f"Test issue number {i + 1}",
                labels=["test", "batch"],
            )
            issues.append(issue)

        # Verify all have unique numbers
        issue_numbers = [issue.number for issue in issues]
        assert len(issue_numbers) == len(set(issue_numbers))

        # Verify all can be retrieved
        for created_issue in issues:
            retrieved = service.get_issue(created_issue.number)
            assert retrieved.number == created_issue.number
            assert retrieved.title == created_issue.title

        # Verify all appear in list (with polling for eventual consistency)
        for created_issue in issues:
            assert wait_for_issue_in_list(
                service, created_issue.number, labels=["batch"], timeout=10.0
            ), f"Issue #{created_issue.number} not found in batch list after 10s"
