"""
Shared pytest fixtures for GitHub Integration tests.
"""

import os
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import pytest

# GitHub App Configuration Fixtures

@pytest.fixture
def github_app_id() -> int:
    """GitHub App ID"""
    return 2578431


@pytest.fixture
def github_installation_id() -> int:
    """GitHub App Installation ID"""
    return 102211688


@pytest.fixture
def github_repository() -> str:
    """Target GitHub repository"""
    return "farmer1st/farmcode-tests"


@pytest.fixture
def github_private_key_path() -> str:
    """Path to GitHub App private key (PEM file)"""
    return os.getenv("GITHUB_APP_PRIVATE_KEY_PATH", "./.keys/orchestrator.pem")


# Test Data Fixtures

@pytest.fixture
def sample_issue_data() -> dict[str, Any]:
    """Sample issue data for testing"""
    return {
        "number": 42,
        "title": "Add user authentication",
        "body": "Implement OAuth2 flow",
        "state": "open",
        "labels": ["status:new", "priority:p1"],
        "assignees": ["duc"],
        "created_at": datetime(2026, 1, 2, 10, 30, 0, tzinfo=UTC),
        "updated_at": datetime(2026, 1, 2, 10, 30, 0, tzinfo=UTC),
        "repository": "farmer1st/farmcode-tests",
        "url": "https://github.com/farmer1st/farmcode-tests/issues/42",
    }


@pytest.fixture
def sample_comment_data() -> dict[str, Any]:
    """Sample comment data for testing"""
    return {
        "id": 987654321,
        "issue_number": 42,
        "author": "dede",
        "body": "✅ Backend plan complete. @baron",
        "created_at": datetime(2026, 1, 2, 11, 15, 0, tzinfo=UTC),
        "url": "https://github.com/farmer1st/farmcode-tests/issues/42#issuecomment-987654321",
    }


@pytest.fixture
def sample_label_data() -> dict[str, Any]:
    """Sample label data for testing"""
    return {
        "name": "status:specs-ready",
        "color": "EDEDED",
        "description": "Specifications approved and ready for planning",
    }


@pytest.fixture
def sample_pr_data() -> dict[str, Any]:
    """Sample pull request data for testing"""
    return {
        "number": 15,
        "title": "Add user authentication",
        "body": "Closes #42\\n\\nImplements OAuth2 flow",
        "state": "open",
        "merged": False,
        "base_branch": "main",
        "head_branch": "123-add-auth",
        "linked_issues": [42],
        "url": "https://github.com/farmer1st/farmcode-tests/pull/15",
    }


# GitHub API Mock Response Fixtures

@pytest.fixture
def mock_github_issue_response() -> dict[str, Any]:
    """Mock GitHub API response for issue"""
    return {
        "number": 42,
        "title": "Add user authentication",
        "body": "Implement OAuth2 flow",
        "state": "open",
        "labels": [
            {"name": "status:new", "color": "EDEDED"},
            {"name": "priority:p1", "color": "FF0000"},
        ],
        "assignees": [{"login": "duc"}],
        "created_at": "2026-01-02T10:30:00Z",
        "updated_at": "2026-01-02T10:30:00Z",
        "html_url": "https://github.com/farmer1st/farmcode-tests/issues/42",
    }


@pytest.fixture
def mock_github_comment_response() -> dict[str, Any]:
    """Mock GitHub API response for comment"""
    return {
        "id": 987654321,
        "user": {"login": "dede"},
        "body": "✅ Backend plan complete. @baron",
        "created_at": "2026-01-02T11:15:00Z",
        "html_url": "https://github.com/farmer1st/farmcode-tests/issues/42#issuecomment-987654321",
    }


@pytest.fixture
def mock_github_pr_response() -> dict[str, Any]:
    """Mock GitHub API response for pull request"""
    return {
        "number": 15,
        "title": "Add user authentication",
        "body": "Closes #42\\n\\nImplements OAuth2 flow",
        "state": "open",
        "merged": False,
        "base": {"ref": "main"},
        "head": {"ref": "123-add-auth"},
        "html_url": "https://github.com/farmer1st/farmcode-tests/pull/15",
    }


# E2E Test Helpers (for handling eventual consistency with real GitHub API)

def wait_for_condition(condition_fn, timeout: float = 10.0, poll_interval: float = 0.5) -> bool:
    """
    Poll until condition is met or timeout.

    Args:
        condition_fn: Callable that returns True when condition is met
        timeout: Maximum seconds to wait
        poll_interval: Seconds between polls

    Returns:
        True if condition met, False if timeout
    """
    import time
    start = time.time()
    while time.time() - start < timeout:
        if condition_fn():
            return True
        time.sleep(poll_interval)
    return False


def wait_for_issue_in_list(
    service,
    issue_number: int,
    state: str = "open",
    labels: list[str] | None = None,
    timeout: float = 10.0,
) -> bool:
    """
    Wait for issue to appear in list results (handles GitHub eventual consistency).

    Note: GitHub API has eventual consistency - newly created issues may not
    immediately appear in list/filter queries. This helper polls until the
    issue appears or timeout.

    Args:
        service: GitHubService instance
        issue_number: Issue number to wait for
        state: Issue state filter ("open", "closed", "all")
        labels: Label filter (optional)
        timeout: Maximum seconds to wait (default: 10s)

    Returns:
        True if issue found, False if timeout

    Example:
        issue = service.create_issue(title="Test")
        assert wait_for_issue_in_list(service, issue.number, labels=["test"])
    """
    def check():
        issues = service.list_issues(state=state, labels=labels)
        return any(i.number == issue_number for i in issues)

    return wait_for_condition(check, timeout=timeout)


def wait_for_issue_labels(
    service,
    issue_number: int,
    expected_labels: list[str],
    timeout: float = 10.0,
) -> bool:
    """
    Wait for issue to have expected labels (handles eventual consistency).

    Args:
        service: GitHubService instance
        issue_number: Issue number
        expected_labels: Labels that should be present
        timeout: Maximum seconds to wait

    Returns:
        True if labels present, False if timeout
    """
    def check():
        issue = service.get_issue(issue_number)
        return all(label in issue.labels for label in expected_labels)

    return wait_for_condition(check, timeout=timeout)


# Test Cleanup Fixtures


@pytest.fixture
def cleanup_issues():
    """
    Fixture that provides automatic cleanup for test issues.

    Usage:
        def test_example(cleanup_issues):
            issue_numbers = []

            # Register issue for cleanup
            issue = create_test_issue()
            cleanup_issues.append(issue.number)

            # Test code here...

            # Issues will be automatically closed after test completes (even if test fails)

    Returns:
        List to append issue numbers for cleanup
    """
    issues_to_cleanup = []
    yield issues_to_cleanup

    # Cleanup runs after test completes (even if test failed)
    if issues_to_cleanup:
        # Import here to avoid circular dependency
        import os

        from github_integration import GitHubService

        # Create service for cleanup
        service = GitHubService(
            app_id=2578431,
            installation_id=102211688,
            private_key_path=os.getenv("GITHUB_APP_PRIVATE_KEY_PATH", "./.keys/orchestrator.pem"),
            repository="farmer1st/farmcode-tests",
        )

        # Close all registered issues
        for issue_number in issues_to_cleanup:
            try:
                service.close_issue(issue_number)
            except Exception:
                # Silently ignore cleanup errors to avoid masking test failures
                pass


@pytest.fixture
def auto_cleanup_issue(service):
    """
    Fixture that automatically tags and cleans up created issues.

    Usage:
        def test_example(auto_cleanup_issue):
            issue = auto_cleanup_issue(
                title="Test issue",
                body="Test body",
                labels=["bug"]  # test:automated will be added automatically
            )

            # Test code here...

            # Issue will be automatically closed after test completes

    Args:
        service: GitHubService fixture

    Returns:
        Function to create issues with automatic cleanup
    """
    created_issues = []

    def create_issue_with_cleanup(
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ):
        """Create issue with automatic test:automated label and cleanup"""
        # Add test:automated label
        test_labels = labels or []
        if "test:automated" not in test_labels:
            test_labels = test_labels + ["test:automated"]

        # Create issue
        issue = service.create_issue(
            title=title,
            body=body,
            labels=test_labels,
            assignees=assignees,
        )

        # Register for cleanup
        created_issues.append(issue.number)

        return issue

    yield create_issue_with_cleanup

    # Cleanup all created issues
    for issue_number in created_issues:
        try:
            service.close_issue(issue_number)
        except Exception:
            # Silently ignore cleanup errors
            pass


# Journey Reporting Hooks


def pytest_configure(config):
    """Initialize journey tracking"""
    config.journey_results = defaultdict(lambda: {"passed": [], "failed": []})


def pytest_runtest_logreport(report):
    """Collect journey test results"""
    # This hook receives report but not item/config, so we store results for later
    # The actual aggregation happens in pytest_sessionfinish
    pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add journey ID to test reports and track results"""
    outcome = yield
    report = outcome.get_result()

    # Extract journey marker
    journey_marker = item.get_closest_marker("journey")
    if journey_marker and journey_marker.args:
        journey_id = journey_marker.args[0]
        report.journey_id = journey_id

        # Track results when test completes
        if report.when == "call":
            test_name = report.nodeid
            journey_results = item.session.config.journey_results

            if report.passed:
                journey_results[journey_id]["passed"].append(test_name)
            elif report.failed:
                journey_results[journey_id]["failed"].append(test_name)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print journey coverage summary after test run"""
    if not hasattr(config, "journey_results") or not config.journey_results:
        return

    journey_results = config.journey_results

    # Print journey summary
    terminalreporter.write_sep("=", "User Journey Test Coverage")
    terminalreporter.write_line("")

    # Sort journeys by ID
    sorted_journeys = sorted(journey_results.items())

    for journey_id, results in sorted_journeys:
        total = len(results["passed"]) + len(results["failed"])
        passed = len(results["passed"])
        failed = len(results["failed"])

        if failed > 0:
            status = "❌ FAILED"
            color = "red"
        else:
            status = "✅ PASSED"
            color = "green"

        coverage_pct = (passed / total * 100) if total > 0 else 0

        msg = f"{journey_id}: {status} ({passed}/{total} tests, {coverage_pct:.0f}%)"
        terminalreporter.write_line(msg, **{color: True})

        # Show failed tests
        if failed > 0:
            for test in results["failed"]:
                terminalreporter.write_line(f"  ❌ {test}", red=True)

    terminalreporter.write_line("")

    # Summary stats
    total_journeys = len(journey_results)
    passing_journeys = sum(1 for r in journey_results.values() if len(r["failed"]) == 0)

    terminalreporter.write_line(
        f"Journey Coverage: {passing_journeys}/{total_journeys} journeys passing",
        **{"green" if passing_journeys == total_journeys else "yellow": True}
    )
    terminalreporter.write_line("")
