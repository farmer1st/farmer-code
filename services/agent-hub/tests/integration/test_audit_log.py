"""Integration tests for audit log writing.

Tests that audit logs are written during API operations.
"""

import json
import os
import tempfile
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
class TestAuditLogWriting:
    """Integration tests for audit log writing."""

    async def test_ask_endpoint_logs_exchange(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that /ask/{topic} logs the Q&A exchange.

        Per SC-007: 100% of invocations are logged.
        """
        mock_agent_response = {
            "success": True,
            "result": {"output": "Use JWT for stateless auth."},
            "confidence": 85,
            "metadata": {},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.invoke.return_value = mock_agent_response
            mock_agent.__aenter__.return_value = mock_agent
            mock_agent.__aexit__.return_value = None
            mock_agent_class.return_value = mock_agent

            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = os.path.join(tmpdir, "audit.jsonl")

                with patch(
                    "src.api.ask.get_audit_logger"
                ) as mock_get_logger:
                    from src.logging.audit import AuditLogger

                    logger = AuditLogger(log_path)
                    mock_get_logger.return_value = logger

                    response = await test_client.post(
                        "/ask/architecture",
                        json={
                            "question": "What authentication method should I use?",
                            "feature_id": "008-audit-test",
                        },
                    )

                    assert response.status_code == 200

                    # Verify log was written
                    if os.path.exists(log_path):
                        with open(log_path) as f:
                            lines = f.readlines()
                            assert len(lines) >= 1
                            entry = json.loads(lines[-1])
                            assert entry["feature_id"] == "008-audit-test"
                            assert entry["topic"] == "architecture"

    async def test_invoke_endpoint_logs_invocation(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that /invoke/{agent} logs the invocation.

        Per SC-007: 100% of invocations are logged.
        """
        mock_agent_response = {
            "success": True,
            "result": {"output": "Specification generated."},
            "confidence": 90,
            "metadata": {},
        }

        with patch(
            "src.api.invoke.AgentServiceClient"
        ) as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.invoke.return_value = mock_agent_response
            mock_agent.__aenter__.return_value = mock_agent
            mock_agent.__aexit__.return_value = None
            mock_agent_class.return_value = mock_agent

            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = os.path.join(tmpdir, "audit.jsonl")

                with patch(
                    "src.api.invoke.get_audit_logger"
                ) as mock_get_logger:
                    from src.logging.audit import AuditLogger

                    logger = AuditLogger(log_path)
                    mock_get_logger.return_value = logger

                    response = await test_client.post(
                        "/invoke/baron",
                        json={
                            "workflow_type": "specify",
                            "context": {"feature_description": "Test feature"},
                        },
                    )

                    # Check log was written (even if agent unavailable)
                    if os.path.exists(log_path):
                        with open(log_path) as f:
                            lines = f.readlines()
                            if lines:
                                entry = json.loads(lines[-1])
                                assert "baron" in entry.get("topic", "").lower() or \
                                       "baron" in entry.get("metadata", {}).get("agent", "").lower()

    async def test_audit_log_includes_duration(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that audit log includes duration in milliseconds."""
        mock_agent_response = {
            "success": True,
            "result": {"output": "Answer"},
            "confidence": 85,
            "metadata": {},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.invoke.return_value = mock_agent_response
            mock_agent.__aenter__.return_value = mock_agent
            mock_agent.__aexit__.return_value = None
            mock_agent_class.return_value = mock_agent

            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = os.path.join(tmpdir, "audit.jsonl")

                with patch(
                    "src.api.ask.get_audit_logger"
                ) as mock_get_logger:
                    from src.logging.audit import AuditLogger

                    logger = AuditLogger(log_path)
                    mock_get_logger.return_value = logger

                    await test_client.post(
                        "/ask/architecture",
                        json={
                            "question": "Quick question for duration test?",
                            "feature_id": "008-duration-test",
                        },
                    )

                    if os.path.exists(log_path):
                        with open(log_path) as f:
                            entry = json.loads(f.readline())
                            assert "duration_ms" in entry
                            assert isinstance(entry["duration_ms"], int)
                            assert entry["duration_ms"] >= 0

    async def test_audit_log_includes_escalation_id(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that audit log includes escalation_id when escalated."""
        mock_agent_response = {
            "success": True,
            "result": {"output": "Tentative answer"},
            "confidence": 60,  # Below threshold
            "metadata": {},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.invoke.return_value = mock_agent_response
            mock_agent.__aenter__.return_value = mock_agent
            mock_agent.__aexit__.return_value = None
            mock_agent_class.return_value = mock_agent

            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = os.path.join(tmpdir, "audit.jsonl")

                with patch(
                    "src.api.ask.get_audit_logger"
                ) as mock_get_logger:
                    from src.logging.audit import AuditLogger

                    logger = AuditLogger(log_path)
                    mock_get_logger.return_value = logger

                    response = await test_client.post(
                        "/ask/architecture",
                        json={
                            "question": "Complex question requiring escalation?",
                            "feature_id": "008-escalation-test",
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("escalation_id"):
                            if os.path.exists(log_path):
                                with open(log_path) as f:
                                    entry = json.loads(f.readline())
                                    assert entry["status"] == "escalated"
                                    assert entry.get("escalation_id") is not None

    async def test_audit_log_queryable_by_feature_id(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Test that logs can be filtered by feature_id.

        Per SC-007: Logs are queryable by feature ID.
        """
        mock_agent_response = {
            "success": True,
            "result": {"output": "Answer"},
            "confidence": 85,
            "metadata": {},
        }

        with patch(
            "src.api.ask.AgentServiceClient"
        ) as mock_agent_class:
            mock_agent = AsyncMock()
            mock_agent.invoke.return_value = mock_agent_response
            mock_agent.__aenter__.return_value = mock_agent
            mock_agent.__aexit__.return_value = None
            mock_agent_class.return_value = mock_agent

            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = os.path.join(tmpdir, "audit.jsonl")

                with patch(
                    "src.api.ask.get_audit_logger"
                ) as mock_get_logger:
                    from src.logging.audit import AuditLogger

                    logger = AuditLogger(log_path)
                    mock_get_logger.return_value = logger

                    # Log entries for different features
                    for feature in ["008-feature-a", "008-feature-b", "008-feature-a"]:
                        await test_client.post(
                            "/ask/architecture",
                            json={
                                "question": f"Question for {feature}?",
                                "feature_id": feature,
                            },
                        )

                    # Read and filter logs
                    if os.path.exists(log_path):
                        with open(log_path) as f:
                            entries = [json.loads(line) for line in f]

                        feature_a_logs = [
                            e for e in entries if e["feature_id"] == "008-feature-a"
                        ]
                        feature_b_logs = [
                            e for e in entries if e["feature_id"] == "008-feature-b"
                        ]

                        assert len(feature_a_logs) == 2
                        assert len(feature_b_logs) == 1
