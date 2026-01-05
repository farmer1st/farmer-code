# Quickstart: Agent Hub

**Feature**: 005-agent-hub-refactor
**Date**: 2026-01-05

## Overview

The Agent Hub is the central coordination layer for all agent interactions. It routes questions to expert agents, manages conversation sessions, validates confidence, and handles human escalations.

## Installation

The Agent Hub is part of the farmcode package:

```bash
# From repository root
uv pip install -e .
```

## Basic Usage

### 1. Route a Question to an Expert

```python
from agent_hub import AgentHub, HubConfig
from agent_hub.config import ConfigLoader

# Load configuration
config = ConfigLoader.load_from_file("config/agents.yaml")

# Create hub
hub = AgentHub(config)

# Ask an expert
response = await hub.ask_expert(
    topic="architecture",
    question="What database should we use for user sessions?",
    context="We expect 10K concurrent users"
)

if response.status == "resolved":
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence}%")
else:
    print(f"Escalated to human: {response.escalation_id}")
```

### 2. Multi-Turn Conversation

```python
# First question - creates a session
response1 = await hub.ask_expert(
    topic="architecture",
    question="What caching strategy should we use?"
)

# Follow-up question - same session
response2 = await hub.ask_expert(
    topic="architecture",
    question="What about cache invalidation?",
    session_id=response1.session_id  # Continue conversation
)

# Expert has context from first question
```

### 3. Handle Escalations

```python
# If confidence is low, response will have pending_human status
response = await hub.ask_expert(
    topic="security",
    question="Should we implement OAuth1 for legacy support?"
)

if response.status == "pending_human":
    # Poll for human response
    while True:
        status = await hub.check_escalation(response.escalation_id)

        if status.status == "resolved":
            print(f"Human {status.action}: {status.corrected_answer or 'confirmed'}")
            break
        elif status.status == "needs_reroute":
            # Human added context, re-ask
            response = await hub.ask_expert(
                topic="security",
                question="Should we implement OAuth1 for legacy support?",
                context=status.additional_context,
                session_id=response.session_id
            )
            break

        await asyncio.sleep(30)  # Check every 30 seconds
```

## Configuration

### Agent Configuration (YAML)

```yaml
# config/agents.yaml
defaults:
  confidence_threshold: 80
  model: sonnet
  timeout: 120

agents:
  architect:
    name: "@duc"
    topics:
      - architecture
      - database
      - caching
      - security
    model: opus

  product:
    name: "@veuve"
    topics:
      - requirements
      - features
      - ux

  qa:
    name: "@marie"
    topics:
      - testing
      - edge-cases
      - coverage

overrides:
  security:
    confidence_threshold: 95  # Higher threshold for security topics
```

## MCP Server Usage

For use with Claude Agent SDK:

```python
from claude_code_sdk import query, ClaudeCodeOptions

async for event in query(
    prompt="Ask the architect about caching strategy",
    options=ClaudeCodeOptions(
        mcp_servers={
            "agent-hub": {
                "command": "python",
                "args": ["-m", "agent_hub.mcp_server"]
            }
        }
    )
):
    # Agent can now use ask_expert and check_escalation tools
    pass
```

## Running Tests

```bash
# Unit tests
uv run pytest tests/unit/agent_hub/ -v

# Integration tests
uv run pytest tests/integration/agent_hub/ -v

# E2E tests (requires credentials)
RUN_E2E_TESTS=1 uv run pytest tests/e2e/agent_hub/ -v

# All tests
uv run pytest tests/ -v
```

## Verification Checklist

After implementation, verify:

- [ ] `from agent_hub import AgentHub` works
- [ ] Questions route to correct agents by topic
- [ ] Sessions preserve conversation context
- [ ] Low confidence triggers escalation
- [ ] Human responses are processed correctly
- [ ] All tests pass
- [ ] No references to "knowledge_router" remain in code
