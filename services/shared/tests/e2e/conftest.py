"""Fixtures for GitHub e2e tests.

These tests require GitHub credentials to run.
Set these environment variables:
- GITHUB_APP_ID
- GITHUB_INSTALLATION_ID
- GITHUB_PRIVATE_KEY_PATH
- GITHUB_REPOSITORY (e.g., "farmer1st/farmer-code-tests")
"""

import os

import pytest

from github_integration import GitHubService


@pytest.fixture
def github_app_id():
    """Get GitHub App ID from environment."""
    value = os.environ.get("GITHUB_APP_ID")
    if not value:
        pytest.skip("GITHUB_APP_ID not set")
    return value


@pytest.fixture
def github_installation_id():
    """Get GitHub Installation ID from environment."""
    value = os.environ.get("GITHUB_INSTALLATION_ID")
    if not value:
        pytest.skip("GITHUB_INSTALLATION_ID not set")
    return value


@pytest.fixture
def github_private_key_path():
    """Get GitHub private key path from environment."""
    value = os.environ.get("GITHUB_PRIVATE_KEY_PATH")
    if not value:
        pytest.skip("GITHUB_PRIVATE_KEY_PATH not set")
    return value


@pytest.fixture
def github_repository():
    """Get GitHub repository from environment."""
    value = os.environ.get("GITHUB_REPOSITORY", "farmer1st/farmer-code-tests")
    return value


@pytest.fixture
def service(github_app_id, github_installation_id, github_private_key_path, github_repository):
    """Create GitHubService instance for e2e testing."""
    return GitHubService(
        app_id=github_app_id,
        installation_id=github_installation_id,
        private_key_path=github_private_key_path,
        repository=github_repository,
    )


@pytest.fixture
def auto_cleanup_issue(service):
    """Create issue with automatic cleanup after test.

    Returns a function that creates issues and registers them for cleanup.
    """
    created_issues = []

    def _create(title: str, body: str = "", labels: list[str] | None = None):
        labels = labels or []
        labels.append("test:automated")  # Mark as automated test issue
        issue = service.create_issue(title=title, body=body, labels=labels)
        created_issues.append(issue.number)
        return issue

    yield _create

    # Cleanup: close all created issues
    for issue_number in created_issues:
        try:
            service.update_issue(issue_number, state="closed")
        except Exception:
            pass  # Ignore cleanup errors
