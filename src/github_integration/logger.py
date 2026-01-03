"""
Structured Logging

JSON logging to stdout/stderr for GitHub operations following 12-factor app pattern.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.

    Format:
    {
        "timestamp": "2026-01-02T10:30:00.123Z",
        "level": "INFO",
        "message": "Created GitHub issue",
        "context": {
            "method": "create_issue",
            "issue_number": 42,
            "repository": "farmer1st/farmcode-tests",
            "duration_ms": 234
        }
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add context from extra fields
        if hasattr(record, "context"):
            log_data["context"] = record.context  # type: ignore

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str = "github_integration") -> logging.Logger:
    """
    Setup structured JSON logger.

    Args:
        name: Logger name (defaults to "github_integration")

    Returns:
        Logger configured for structured JSON output

    Example:
        logger = setup_logger()
        logger.info(
            "Created GitHub issue",
            extra={"context": {"issue_number": 42, "repository": "farmer1st/farmcode-tests"}}
        )
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # INFO and DEBUG to stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.addFilter(lambda record: record.levelno < logging.WARNING)
        stdout_handler.setFormatter(JSONFormatter())
        logger.addHandler(stdout_handler)

        # WARNING, ERROR, CRITICAL to stderr
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.setFormatter(JSONFormatter())
        logger.addHandler(stderr_handler)

    return logger


# Default logger instance
logger = setup_logger()
