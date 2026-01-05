"""MCP Server for Agent Hub (T070-T073).

Exposes Agent Hub functionality as MCP tools for Claude Agent SDK integration.

Usage:
    python -m agent_hub.mcp_server

Tools:
    - ask_expert: Route a question to the appropriate expert agent
    - check_escalation: Check the status of a pending human escalation
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from .exceptions import EscalationError, UnknownTopicError
from .hub import AgentHub

# Module-level hub instance (set via set_hub for dependency injection)
_hub: AgentHub | None = None


def get_hub() -> AgentHub:
    """Get the configured AgentHub instance.

    Returns:
        The configured AgentHub.

    Raises:
        RuntimeError: If hub not configured via set_hub().
    """
    if _hub is None:
        raise RuntimeError("AgentHub not configured. Call set_hub() first.")
    return _hub


def set_hub(hub: AgentHub) -> None:
    """Set the AgentHub instance for MCP tools.

    Args:
        hub: The AgentHub instance to use.
    """
    global _hub
    _hub = hub


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server with Agent Hub tools.

    Returns:
        Configured FastMCP server instance.
    """
    mcp = FastMCP("agent-hub")

    @mcp.tool()
    def ask_expert(
        topic: str,
        question: str,
        context: str = "",
        feature_id: str = "",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Route a question to the appropriate expert agent.

        Args:
            topic: Domain topic (architecture, product, testing, etc.).
            question: The question to ask the expert.
            context: Additional context for the question.
            feature_id: Feature ID for grouping questions.
            session_id: Optional session ID for multi-turn conversations.

        Returns:
            dict with answer, confidence, session_id, status, and escalation_id.
        """
        try:
            hub = get_hub()
            response = hub.ask_expert(
                topic=topic,
                question=question,
                context=context,
                feature_id=feature_id,
                session_id=session_id,
            )
            return {
                "answer": response.answer,
                "rationale": response.rationale,
                "confidence": response.confidence,
                "uncertainty_reasons": response.uncertainty_reasons,
                "session_id": response.session_id,
                "status": response.status.value,
                "escalation_id": response.escalation_id,
            }
        except UnknownTopicError as e:
            return {
                "error": True,
                "message": str(e),
                "available_topics": e.available_topics,
            }
        except Exception as e:
            return {
                "error": True,
                "message": str(e),
            }

    @mcp.tool()
    def check_escalation(escalation_id: str) -> dict[str, Any]:
        """Check the status of a pending human escalation.

        Args:
            escalation_id: The escalation ID to check.

        Returns:
            dict with escalation_id, status, question, and threshold info.
        """
        try:
            hub = get_hub()
            escalation = hub.check_escalation(escalation_id)
            return {
                "escalation_id": escalation.id,
                "status": escalation.status,
                "question": escalation.question.question,
                "confidence": escalation.tentative_answer.confidence,
                "threshold": escalation.threshold_used,
            }
        except EscalationError as e:
            return {
                "error": True,
                "message": str(e),
            }
        except Exception as e:
            return {
                "error": True,
                "message": str(e),
            }

    return mcp


# Entry point for python -m agent_hub.mcp_server (T073)
if __name__ == "__main__":
    from .config import ConfigLoader

    # Load default config if available
    try:
        config = ConfigLoader.load_from_file("agent_hub_config.yaml")
    except FileNotFoundError:
        # Use minimal default config for standalone mode
        from .config import RoutingConfig

        config = RoutingConfig()

    # Create and configure hub
    hub = AgentHub(config)
    set_hub(hub)

    # Create and run server
    server = create_mcp_server()
    server.run()
