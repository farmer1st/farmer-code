"""Q&A logging for Knowledge Router.

This module handles immutable logging of all Q&A exchanges
for retrospective analysis and knowledge improvement.
"""

import json
from pathlib import Path
from typing import Any

from .models import QALogEntry


class QALogger:
    """Logger for Q&A exchanges.

    Writes immutable log entries to JSONL files organized by feature_id.
    Supports retrieval by feature_id and exchange chain traversal.
    """

    def __init__(self, log_dir: str | Path = "logs/qa") -> None:
        """Initialize the logger.

        Args:
            log_dir: Directory for log files. Each feature gets its own file.
        """
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def log_exchange(self, entry: QALogEntry) -> None:
        """Log a Q&A exchange.

        Appends the entry to the feature's JSONL log file.

        Args:
            entry: The log entry to write.
        """
        log_path = self._get_log_path(entry.feature_id)

        # Convert to JSON-serializable dict
        data = self._serialize_entry(entry)

        # Append to JSONL file
        with open(log_path, "a") as f:
            f.write(json.dumps(data, default=str) + "\n")

    def get_logs_for_feature(self, feature_id: str) -> list[dict[str, Any]]:
        """Retrieve all log entries for a feature.

        Args:
            feature_id: The feature ID to retrieve logs for.

        Returns:
            List of log entries as dictionaries.
        """
        log_path = self._get_log_path(feature_id)

        if not log_path.exists():
            return []

        entries = []
        with open(log_path) as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return entries

    def get_exchange_chain(
        self,
        entry_id: str,
        feature_id: str,
    ) -> list[dict[str, Any]]:
        """Retrieve a chain of related exchanges.

        Follows parent_id links to build the complete chain
        from the original exchange to the final one.

        Args:
            entry_id: The ID of the entry to start from.
            feature_id: The feature the entries belong to.

        Returns:
            List of entries from original to current, in order.
        """
        all_entries = self.get_logs_for_feature(feature_id)

        # Build lookup by ID
        by_id = {e["id"]: e for e in all_entries}

        # Find the target entry
        if entry_id not in by_id:
            return []

        # Walk back to find the root
        chain_ids = []
        current_id: str | None = entry_id

        while current_id is not None:
            if current_id not in by_id:
                break
            chain_ids.append(current_id)
            current_id = by_id[current_id].get("parent_id")

        # Reverse to get chronological order
        chain_ids.reverse()

        return [by_id[entry_id] for entry_id in chain_ids]

    def _get_log_path(self, feature_id: str) -> Path:
        """Get the log file path for a feature.

        Args:
            feature_id: The feature ID.

        Returns:
            Path to the JSONL log file.
        """
        return self._log_dir / f"{feature_id}.jsonl"

    def _serialize_entry(self, entry: QALogEntry) -> dict[str, Any]:
        """Serialize a log entry to a JSON-safe dictionary.

        Args:
            entry: The log entry to serialize.

        Returns:
            Dictionary safe for JSON serialization.
        """
        # Use Pydantic's model_dump for proper serialization
        return entry.model_dump(mode="json")
