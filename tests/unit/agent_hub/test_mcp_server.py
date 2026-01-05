"""Unit tests for Agent Hub MCP Server (T074).

Tests the MCP server implementation that exposes Agent Hub functionality
as MCP tools for Claude Agent SDK integration.
"""

from unittest.mock import MagicMock

import pytest

from agent_hub.exceptions import EscalationError, UnknownTopicError
from agent_hub.models import HubResponse, ResponseStatus


class TestMCPServerInitialization:
    """Tests for MCP server initialization."""

    def test_create_mcp_server_returns_fastmcp_instance(self):
        """MCP server can be created."""
        from agent_hub.mcp_server import create_mcp_server

        server = create_mcp_server()
        assert server is not None
        assert server.name == "agent-hub"

    def test_mcp_server_has_ask_expert_tool(self):
        """MCP server exposes ask_expert tool."""
        from agent_hub.mcp_server import create_mcp_server

        server = create_mcp_server()
        # FastMCP registers tools internally
        tools = server._tool_manager._tools
        assert "ask_expert" in tools

    def test_mcp_server_has_check_escalation_tool(self):
        """MCP server exposes check_escalation tool."""
        from agent_hub.mcp_server import create_mcp_server

        server = create_mcp_server()
        tools = server._tool_manager._tools
        assert "check_escalation" in tools


class TestAskExpertMCPTool:
    """Tests for ask_expert MCP tool (T071)."""

    @pytest.fixture
    def mock_hub(self):
        """Create a mock AgentHub."""
        hub = MagicMock()
        hub.ask_expert.return_value = HubResponse(
            answer="Use Redis for caching",
            rationale="Based on scale requirements",
            confidence=85,
            uncertainty_reasons=[],
            session_id="session-123",
            status=ResponseStatus.RESOLVED,
            escalation_id=None,
        )
        return hub

    def test_ask_expert_tool_routes_question(self, mock_hub):
        """ask_expert tool routes question to hub."""
        from agent_hub.mcp_server import create_mcp_server, set_hub

        server = create_mcp_server()
        set_hub(mock_hub)

        # Get the tool function
        tool_fn = server._tool_manager._tools["ask_expert"].fn

        # Call the tool
        result = tool_fn(
            topic="architecture",
            question="What caching should we use?",
            context="10K users",
            feature_id="005-test",
        )

        mock_hub.ask_expert.assert_called_once_with(
            topic="architecture",
            question="What caching should we use?",
            context="10K users",
            feature_id="005-test",
            session_id=None,
        )
        assert result["answer"] == "Use Redis for caching"
        assert result["status"] == "resolved"
        assert result["session_id"] == "session-123"

    def test_ask_expert_tool_with_session_id(self, mock_hub):
        """ask_expert tool passes session_id for multi-turn."""
        from agent_hub.mcp_server import create_mcp_server, set_hub

        server = create_mcp_server()
        set_hub(mock_hub)

        tool_fn = server._tool_manager._tools["ask_expert"].fn
        tool_fn(
            topic="architecture",
            question="Follow-up question",
            session_id="existing-session",
        )

        mock_hub.ask_expert.assert_called_once()
        call_args = mock_hub.ask_expert.call_args
        assert call_args.kwargs["session_id"] == "existing-session"

    def test_ask_expert_tool_returns_escalation_id_when_pending(self, mock_hub):
        """ask_expert returns escalation_id for PENDING_HUMAN status."""
        mock_hub.ask_expert.return_value = HubResponse(
            answer="Tentative: Use Redis",
            rationale="Low confidence",
            confidence=45,
            uncertainty_reasons=["Need human verification"],
            session_id="session-456",
            status=ResponseStatus.PENDING_HUMAN,
            escalation_id="escalation-789",
        )

        from agent_hub.mcp_server import create_mcp_server, set_hub

        server = create_mcp_server()
        set_hub(mock_hub)

        tool_fn = server._tool_manager._tools["ask_expert"].fn
        result = tool_fn(topic="architecture", question="Critical decision?")

        assert result["status"] == "pending_human"
        assert result["escalation_id"] == "escalation-789"

    def test_ask_expert_tool_handles_unknown_topic_error(self, mock_hub):
        """ask_expert returns error for unknown topic."""
        mock_hub.ask_expert.side_effect = UnknownTopicError(
            "unknown_topic", ["architecture", "product"]
        )

        from agent_hub.mcp_server import create_mcp_server, set_hub

        server = create_mcp_server()
        set_hub(mock_hub)

        tool_fn = server._tool_manager._tools["ask_expert"].fn
        result = tool_fn(topic="unknown_topic", question="Test?")

        assert result["error"] is True
        assert "unknown_topic" in result["message"]
        assert "architecture" in result["available_topics"]


class TestCheckEscalationMCPTool:
    """Tests for check_escalation MCP tool (T072)."""

    @pytest.fixture
    def mock_hub(self):
        """Create a mock AgentHub with escalation."""
        hub = MagicMock()
        # Return an EscalationRequest mock
        escalation = MagicMock()
        escalation.id = "escalation-123"
        escalation.status = "pending"
        escalation.question.question = "Original question"
        escalation.tentative_answer.confidence = 45
        escalation.threshold_used = 80
        hub.check_escalation.return_value = escalation
        return hub

    def test_check_escalation_returns_status(self, mock_hub):
        """check_escalation returns escalation status."""
        from agent_hub.mcp_server import create_mcp_server, set_hub

        server = create_mcp_server()
        set_hub(mock_hub)

        tool_fn = server._tool_manager._tools["check_escalation"].fn
        result = tool_fn(escalation_id="escalation-123")

        mock_hub.check_escalation.assert_called_once_with("escalation-123")
        assert result["escalation_id"] == "escalation-123"
        assert result["status"] == "pending"

    def test_check_escalation_handles_not_found(self, mock_hub):
        """check_escalation returns error for missing escalation."""
        mock_hub.check_escalation.side_effect = EscalationError("Escalation not found: invalid-id")

        from agent_hub.mcp_server import create_mcp_server, set_hub

        server = create_mcp_server()
        set_hub(mock_hub)

        tool_fn = server._tool_manager._tools["check_escalation"].fn
        result = tool_fn(escalation_id="invalid-id")

        assert result["error"] is True
        assert "not found" in result["message"].lower()


class TestMCPServerEntryPoint:
    """Tests for MCP server entry point (T073)."""

    def test_mcp_server_module_is_runnable(self):
        """MCP server can be run as python -m agent_hub.mcp_server."""
        # Verify the module has a main block
        import agent_hub.mcp_server as mcp_module

        assert hasattr(mcp_module, "create_mcp_server")
        assert hasattr(mcp_module, "set_hub")

    def test_mcp_server_can_be_configured_with_hub(self):
        """MCP server can be configured with a custom hub."""
        from agent_hub.mcp_server import get_hub, set_hub

        mock_hub = MagicMock()
        set_hub(mock_hub)

        assert get_hub() is mock_hub
