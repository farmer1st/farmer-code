"""
Structured Logging

JSON logging to stdout/stderr for worktree operations following 12-factor app pattern.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.

    Format:
    {
        "timestamp": "2026-01-03T10:30:00.123Z",
        "level": "INFO",
        "message": "Created worktree",
        "context": {
            "method": "create_worktree",
            "issue_number": 123,
            "branch": "123-add-auth",
            "duration_ms": 1234
        }
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add context from extra fields
        if hasattr(record, "context"):
            log_data["context"] = record.context

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str = "worktree_manager") -> logging.Logger:
    """
    Setup structured JSON logger.

    Args:
        name: Logger name (defaults to "worktree_manager")

    Returns:
        Logger configured for structured JSON output

    Example:
        logger = setup_logger()
        logger.info(
            "Created worktree",
            extra={"context": {"issue_number": 123, "branch": "123-add-auth"}}
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
