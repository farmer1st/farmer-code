"""Agent Hub Service - Central Coordination Layer.

The Agent Hub Service is the central coordination layer for all agent interactions.
It routes requests to agent services, validates confidence, manages sessions,
and handles human escalation via GitHub comments.

All agent invocations MUST go through this service (single pattern).
"""

__version__ = "0.1.0"
__service_name__ = "agent-hub"
