"""
Unit Tests for Structured JSON Logging

Tests that the logger produces JSON output matching the specification:
{
    "timestamp": "2026-01-02T10:30:00.123Z",
    "level": "INFO",
    "message": "Created GitHub issue",
    "context": {
        "method": "create_issue",
        "issue_number": 42,
        "repository": "farmer1st/farmer-code-tests",
        "duration_ms": 234
    }
}
"""

import json
import logging
from datetime import datetime
from io import StringIO
from unittest.mock import patch

from src.github_integration.logger import JSONFormatter, logger, setup_logger


class TestJSONFormatter:
    """Tests for JSONFormatter class"""

    def test_formats_log_record_as_json(self):
        """Should format log record as valid JSON"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_includes_timestamp(self):
        """Should include ISO format timestamp"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "timestamp" in parsed
        # Verify it's a valid ISO timestamp
        timestamp = parsed["timestamp"]
        assert isinstance(timestamp, str)
        # Should be parseable as ISO format
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_includes_level(self):
        """Should include log level name"""
        formatter = JSONFormatter()

        levels = [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARNING"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRITICAL"),
        ]

        for level, expected_name in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )
            output = formatter.format(record)
            parsed = json.loads(output)

            assert parsed["level"] == expected_name

    def test_includes_message(self):
        """Should include log message"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Created GitHub issue",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["message"] == "Created GitHub issue"

    def test_includes_context_when_provided(self):
        """Should include context dict when provided via extra"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Created issue",
            args=(),
            exc_info=None,
        )
        # Add context via the record attribute
        record.context = {
            "method": "create_issue",
            "issue_number": 42,
            "repository": "farmer1st/farmer-code-tests",
            "duration_ms": 234,
        }

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "context" in parsed
        assert parsed["context"]["method"] == "create_issue"
        assert parsed["context"]["issue_number"] == 42
        assert parsed["context"]["repository"] == "farmer1st/farmer-code-tests"
        assert parsed["context"]["duration_ms"] == 234

    def test_no_context_when_not_provided(self):
        """Should not include context key when not provided"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Simple message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "context" not in parsed

    def test_includes_exception_when_present(self):
        """Should include exception info when present"""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="An error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "Test error" in parsed["exception"]

    def test_message_with_format_args(self):
        """Should format message with args"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Issue #%d created in %s",
            args=(42, "test-repo"),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["message"] == "Issue #42 created in test-repo"


class TestSetupLogger:
    """Tests for setup_logger function"""

    def test_returns_logger_instance(self):
        """Should return a Logger instance"""
        test_logger = setup_logger("test_logger_1")
        assert isinstance(test_logger, logging.Logger)

    def test_logger_has_correct_name(self):
        """Should set correct logger name"""
        test_logger = setup_logger("custom_name")
        assert test_logger.name == "custom_name"

    def test_default_name_is_github_integration(self):
        """Default logger name should be 'github_integration'"""
        # Note: We test the default by checking the module-level logger
        assert logger.name == "github_integration"

    def test_logger_level_is_info(self):
        """Logger level should be INFO"""
        test_logger = setup_logger("test_logger_2")
        assert test_logger.level == logging.INFO

    def test_logger_does_not_propagate(self):
        """Logger should not propagate to parent"""
        test_logger = setup_logger("test_logger_3")
        assert test_logger.propagate is False

    def test_only_configures_once(self):
        """Should only add handlers once even if called multiple times"""
        test_logger = setup_logger("test_logger_repeat")
        initial_handler_count = len(test_logger.handlers)

        # Call again
        test_logger = setup_logger("test_logger_repeat")

        assert len(test_logger.handlers) == initial_handler_count


class TestLoggerOutput:
    """Tests for actual logger output"""

    def test_info_goes_to_stdout(self):
        """INFO logs should go to stdout via a StreamHandler"""
        test_logger = setup_logger("test_stdout_check")

        # Find handlers that handle INFO level
        info_handlers = [
            h
            for h in test_logger.handlers
            if isinstance(h, logging.StreamHandler) and h.level <= logging.INFO
        ]
        # Should have at least one handler for INFO
        assert len(info_handlers) >= 1

    def test_error_goes_to_stderr(self):
        """ERROR logs should go to stderr via a StreamHandler"""
        test_logger = setup_logger("test_stderr_check")

        # Find handlers that handle WARNING+ levels
        error_handlers = [
            h
            for h in test_logger.handlers
            if isinstance(h, logging.StreamHandler) and h.level >= logging.WARNING
        ]
        # Should have at least one handler for errors
        assert len(error_handlers) >= 1

    def test_log_with_context_extra(self):
        """Should support logging with context in extra dict"""
        test_logger = setup_logger("test_context")

        # Capture handler output
        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(JSONFormatter())
        test_logger.addHandler(handler)

        test_logger.info(
            "Created issue",
            extra={
                "context": {
                    "issue_number": 123,
                    "repository": "test/repo",
                }
            },
        )

        output = string_io.getvalue()
        parsed = json.loads(output)

        assert parsed["message"] == "Created issue"
        assert parsed["context"]["issue_number"] == 123
        assert parsed["context"]["repository"] == "test/repo"


class TestLogFormatSpec:
    """Tests that verify the log format matches specification"""

    def test_matches_spec_format(self):
        """Log output should match the specification format"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="github_integration",
            level=logging.INFO,
            pathname="service.py",
            lineno=42,
            msg="Created GitHub issue",
            args=(),
            exc_info=None,
        )
        record.context = {
            "method": "create_issue",
            "issue_number": 42,
            "repository": "farmer1st/farmer-code-tests",
            "duration_ms": 234,
        }

        output = formatter.format(record)
        parsed = json.loads(output)

        # Verify all required fields are present
        required_fields = ["timestamp", "level", "message"]
        for field in required_fields:
            assert field in parsed, f"Missing required field: {field}"

        # Verify format
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Created GitHub issue"
        assert "context" in parsed
        assert parsed["context"]["method"] == "create_issue"

    def test_json_is_single_line(self):
        """JSON output should be single line (no pretty printing)"""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.context = {"key": "value", "nested": {"a": 1}}

        output = formatter.format(record)

        # Should be single line
        assert "\n" not in output
        # Should still be valid JSON
        json.loads(output)

    def test_timestamp_is_utc(self):
        """Timestamp should be in UTC"""
        formatter = JSONFormatter()

        with patch("src.github_integration.logger.datetime") as mock_datetime:
            # Mock datetime.now to return a known time
            from datetime import UTC

            mock_now = datetime(2026, 1, 2, 10, 30, 0, 123000, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test",
                args=(),
                exc_info=None,
            )

            output = formatter.format(record)
            parsed = json.loads(output)

            # Timestamp should contain timezone info
            timestamp = parsed["timestamp"]
            assert "+" in timestamp or "Z" in timestamp
