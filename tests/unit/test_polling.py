"""Unit tests for Signal Polling (User Story 4).

Tests cover:
- T056: poll_for_signal()
- T057: Signal detection (checkmark and "approved")
- T058: Poll timeout handling
"""

from unittest.mock import MagicMock

import pytest

from orchestrator import (
    PollTimeoutError,
    SignalType,
)


class TestPollForSignal:
    """T056: Unit tests for poll_for_signal()."""

    def test_poll_finds_agent_complete_signal(self, signal_poller, mock_github):
        """Should detect agent complete signal (checkmark emoji)."""
        mock_comment = MagicMock()
        mock_comment.id = 456
        mock_comment.body = "Specification complete ✅"
        mock_comment.user.login = "github-actions[bot]"

        mock_github.get_issue_comments.return_value = [mock_comment]

        result = signal_poller.poll_for_signal(
            issue_number=123,
            signal_type=SignalType.AGENT_COMPLETE,
            timeout_seconds=5,
            interval_seconds=1,
        )

        assert result.detected is True
        assert result.signal_type == SignalType.AGENT_COMPLETE
        assert result.comment_id == 456
        assert result.comment_author == "github-actions[bot]"

    def test_poll_finds_human_approval_signal(self, signal_poller, mock_github):
        """Should detect human approval signal ('approved')."""
        mock_comment = MagicMock()
        mock_comment.id = 789
        mock_comment.body = "Looks good, approved!"
        mock_comment.user.login = "reviewer"

        mock_github.get_issue_comments.return_value = [mock_comment]

        result = signal_poller.poll_for_signal(
            issue_number=123,
            signal_type=SignalType.HUMAN_APPROVAL,
            timeout_seconds=5,
            interval_seconds=1,
        )

        assert result.detected is True
        assert result.signal_type == SignalType.HUMAN_APPROVAL
        assert result.comment_id == 789

    def test_poll_returns_not_detected_when_no_signal(self, signal_poller, mock_github):
        """Should return not detected when signal not found."""
        mock_comment = MagicMock()
        mock_comment.id = 100
        mock_comment.body = "Just a regular comment"
        mock_comment.user.login = "user"

        mock_github.get_issue_comments.return_value = [mock_comment]

        result = signal_poller.poll_for_signal(
            issue_number=123,
            signal_type=SignalType.AGENT_COMPLETE,
            timeout_seconds=1,
            interval_seconds=0.5,
        )

        assert result.detected is False
        assert result.poll_count >= 1


class TestSignalDetection:
    """T057: Unit tests for signal detection logic."""

    def test_detects_checkmark_emoji(self, signal_poller, mock_github):
        """Should detect checkmark emoji for agent complete."""
        test_cases = [
            "Done ✅",
            "✅ Complete",
            "Task ✅ finished",
        ]

        for body in test_cases:
            mock_comment = MagicMock()
            mock_comment.id = 1
            mock_comment.body = body
            mock_comment.user.login = "bot"
            mock_github.get_issue_comments.return_value = [mock_comment]

            result = signal_poller.poll_for_signal(
                issue_number=123,
                signal_type=SignalType.AGENT_COMPLETE,
                timeout_seconds=1,
                interval_seconds=1,
            )
            assert result.detected is True, f"Failed for body: {body}"

    def test_detects_approved_case_insensitive(self, signal_poller, mock_github):
        """Should detect 'approved' in any case."""
        test_cases = [
            "Approved",
            "APPROVED",
            "approved",
            "I have approved this",
        ]

        for body in test_cases:
            mock_comment = MagicMock()
            mock_comment.id = 1
            mock_comment.body = body
            mock_comment.user.login = "human"
            mock_github.get_issue_comments.return_value = [mock_comment]

            result = signal_poller.poll_for_signal(
                issue_number=123,
                signal_type=SignalType.HUMAN_APPROVAL,
                timeout_seconds=1,
                interval_seconds=1,
            )
            assert result.detected is True, f"Failed for body: {body}"

    def test_ignores_wrong_signal_type(self, signal_poller, mock_github):
        """Should not detect wrong signal type."""
        mock_comment = MagicMock()
        mock_comment.id = 1
        mock_comment.body = "approved"  # Human approval signal
        mock_comment.user.login = "user"
        mock_github.get_issue_comments.return_value = [mock_comment]

        # Looking for agent complete, not approval
        result = signal_poller.poll_for_signal(
            issue_number=123,
            signal_type=SignalType.AGENT_COMPLETE,
            timeout_seconds=1,
            interval_seconds=1,
        )
        assert result.detected is False


class TestPollTimeoutHandling:
    """T058: Unit tests for poll timeout handling."""

    def test_raises_timeout_error(self, signal_poller, mock_github):
        """Should raise PollTimeoutError when timeout exceeded."""
        mock_github.get_issue_comments.return_value = []  # No comments

        with pytest.raises(PollTimeoutError):
            signal_poller.poll_for_signal(
                issue_number=123,
                signal_type=SignalType.AGENT_COMPLETE,
                timeout_seconds=1,
                interval_seconds=0.5,
                raise_on_timeout=True,
            )

    def test_returns_not_detected_without_raise(self, signal_poller, mock_github):
        """Should return not detected when not raising on timeout."""
        mock_github.get_issue_comments.return_value = []

        result = signal_poller.poll_for_signal(
            issue_number=123,
            signal_type=SignalType.AGENT_COMPLETE,
            timeout_seconds=1,
            interval_seconds=0.5,
            raise_on_timeout=False,
        )

        assert result.detected is False
        assert result.poll_count >= 1

    def test_increments_poll_count(self, signal_poller, mock_github):
        """Should track poll count correctly."""
        mock_github.get_issue_comments.return_value = []

        result = signal_poller.poll_for_signal(
            issue_number=123,
            signal_type=SignalType.AGENT_COMPLETE,
            timeout_seconds=1,
            interval_seconds=0.3,
            raise_on_timeout=False,
        )

        # With 1s timeout and 0.3s interval, should poll 3-4 times
        assert result.poll_count >= 2


class TestPollerConfiguration:
    """Additional tests for poller configuration."""

    def test_respects_interval(self, signal_poller, mock_github):
        """Should wait between polls."""
        mock_github.get_issue_comments.return_value = []

        import time

        start = time.time()
        signal_poller.poll_for_signal(
            issue_number=123,
            signal_type=SignalType.AGENT_COMPLETE,
            timeout_seconds=0.5,
            interval_seconds=0.2,
            raise_on_timeout=False,
        )
        elapsed = time.time() - start

        # Should take at least 0.4s (2 waits of 0.2s)
        assert elapsed >= 0.3


# Fixtures


@pytest.fixture
def mock_github():
    """Create a mock GitHub service."""
    mock = MagicMock()
    mock.get_issue_comments.return_value = []
    return mock


@pytest.fixture
def signal_poller(mock_github):
    """Create a SignalPoller with mocked GitHub service."""
    from orchestrator.polling import SignalPoller

    return SignalPoller(github_service=mock_github)
