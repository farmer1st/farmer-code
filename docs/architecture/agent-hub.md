# Agent Hub Architecture

This document describes the architecture of the Agent Hub module, the central coordination layer for all agent interactions.

## Overview

The Agent Hub is the evolution of the Knowledge Router, providing a unified interface for:

1. **Routing questions** to appropriate expert agents
2. **Managing sessions** for multi-turn conversations
3. **Validating confidence** and escalating to humans
4. **Logging all exchanges** for audit and retrospective

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Agent Hub                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      AgentHub                              │   │
│  │  (Central Facade - Coordinates all operations)            │   │
│  └─────────────────────────────┬────────────────────────────┘   │
│                                │                                  │
│    ┌───────────────────────────┼───────────────────────────┐     │
│    │           │               │               │           │     │
│    ▼           ▼               ▼               ▼           ▼     │
│ ┌─────────┐ ┌─────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│ │ Agent   │ │ Session │ │Confidence │ │Escalation │ │   QA    │ │
│ │ Router  │ │ Manager │ │ Validator │ │  Handler  │ │ Logger  │ │
│ └────┬────┘ └────┬────┘ └─────┬─────┘ └─────┬─────┘ └────┬────┘ │
│      │           │             │             │            │      │
│      │     ┌─────┴─────┐       │             │     ┌──────┴────┐│
│      │     │  Session  │       │             │     │  JSONL    ││
│      │     │  Storage  │       │             │     │   Files   ││
│      │     └───────────┘       │             │     └───────────┘│
│      │                         │             │                   │
│      ▼                         │             │                   │
│ ┌─────────┐                    │             │                   │
│ │ Claude  │                    │             │                   │
│ │   CLI   │                    │             │                   │
│ └─────────┘                    │             │                   │
└────────────────────────────────┼─────────────┼───────────────────┘
                                 │             │
                                 ▼             ▼
                            ┌─────────┐   ┌─────────┐
                            │  Config │   │ GitHub  │
                            │  (YAML) │   │   API   │
                            └─────────┘   └─────────┘
```

## Component Responsibilities

### AgentHub (Facade)

The main entry point for all agent interactions.

**Responsibilities:**
- Coordinate routing, validation, and logging
- Manage sessions for multi-turn conversations
- Handle escalation lifecycle
- Expose MCP tools

**Key Methods:**
- `ask_expert()` - Route question and return response
- `check_escalation()` - Get escalation status
- `add_human_response()` - Process human feedback
- `get_session()` / `close_session()` - Session management

### AgentRouter

Dispatches questions to Claude CLI agents.

**Responsibilities:**
- Resolve topic to agent mapping
- Spawn Claude CLI process
- Parse agent responses
- Handle timeouts and errors

### SessionManager

Maintains conversation context.

**Responsibilities:**
- Create and store sessions
- Add messages to sessions
- Track session status (active/closed/expired)
- Provide session history for context

### ConfidenceValidator

Validates agent answers against thresholds.

**Responsibilities:**
- Look up topic-specific thresholds
- Compare confidence to threshold
- Return validation outcome (ACCEPTED/ESCALATE)

### EscalationHandler

Manages human review workflow.

**Responsibilities:**
- Create escalation requests
- Format GitHub comments
- Process human responses
- Handle CONFIRM/CORRECT/ADD_CONTEXT actions

### QALogger

Provides audit trail for all exchanges.

**Responsibilities:**
- Log complete Q&A exchanges
- Include session and escalation context
- Write to feature-specific JSONL files
- Support log retrieval by feature

## Data Flow

### ask_expert Flow

```
1. Client calls ask_expert(topic, question)
        │
        ▼
2. AgentHub validates topic
        │
        ▼
3. AgentHub creates/retrieves session
        │
        ▼
4. AgentRouter dispatches to agent
        │
        ▼
5. AgentRouter parses answer
        │
        ▼
6. ConfidenceValidator validates answer
        │
        ├── High confidence ──► Return RESOLVED
        │
        └── Low confidence ──► Create escalation
                │              Return PENDING_HUMAN
                ▼
7. QALogger logs exchange
        │
        ▼
8. Return HubResponse to client
```

### Escalation Resolution Flow

```
1. Client calls check_escalation(escalation_id)
        │
        ▼
2. Return current status (pending/resolved)
        │
        ▼
3. Human provides response via add_human_response()
        │
        ├── CONFIRM ──► Accept tentative answer
        │
        ├── CORRECT ──► Use human's answer (100% confidence)
        │
        └── ADD_CONTEXT ──► Mark as NEEDS_REROUTE
                            Client can re-ask with context
```

## Session Architecture

### Session Model

```python
Session:
    id: str              # UUID
    agent_id: str        # Agent handling this session
    feature_id: str      # Feature grouping
    messages: [Message]  # Conversation history
    created_at: datetime
    updated_at: datetime
    status: SessionStatus  # ACTIVE, CLOSED, EXPIRED
```

### Message Model

```python
Message:
    role: MessageRole    # USER, ASSISTANT, HUMAN
    content: str         # Message text
    timestamp: datetime
    metadata: dict       # Additional context (confidence, etc.)
```

### Session Lifecycle

```
                    create()
                       │
                       ▼
    ┌──────────────[ACTIVE]──────────────┐
    │                  │                  │
    │   add_message()  │     timeout      │
    │   (loops back)   │                  │
    │                  ▼                  ▼
    │            close()              [EXPIRED]
    │                  │
    │                  ▼
    │            [CLOSED]
    │
    └─────────────────────────────────────
```

## MCP Server Architecture

The Agent Hub exposes functionality via MCP for Claude Agent SDK integration.

```
┌─────────────────────────────────────┐
│           Claude Agent              │
│   (using claude_code_sdk)           │
└──────────────────┬──────────────────┘
                   │
                   │ MCP Protocol
                   │
                   ▼
┌─────────────────────────────────────┐
│         MCP Server                  │
│  ┌─────────────────────────────┐    │
│  │  ask_expert tool            │    │
│  │  check_escalation tool      │    │
│  └──────────────┬──────────────┘    │
└─────────────────┼───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│           AgentHub                  │
│      (same instance)                │
└─────────────────────────────────────┘
```

## Configuration Architecture

### Config Loading

```
routing.yaml ──parse──► RoutingConfig
                             │
          ┌──────────────────┴──────────────────┐
          │                                      │
    ┌─────┴─────┐                        ┌───────┴───────┐
    │  Agents   │                        │   Overrides   │
    │           │                        │               │
    │ architect │                        │ security: 95% │
    │ devops    │                        │ legal: 90%    │
    │ security  │                        │               │
    └───────────┘                        └───────────────┘
```

### Threshold Resolution

1. Check topic in overrides → use override threshold
2. Else → use default threshold (80%)

## Error Handling

### Error Hierarchy

```
AgentHubError (base)
├── UnknownTopicError    # Topic not configured
├── SessionNotFoundError # Session doesn't exist
├── SessionClosedError   # Session already closed
├── EscalationError      # Escalation not found
├── AgentDispatchError   # Agent failed to start
├── AgentTimeoutError    # Agent timed out
└── RoutingError         # General routing failure
```

### Error Propagation

- Validation errors (topic, session) → raise immediately
- Agent errors → catch and convert to appropriate error
- Logging errors → log warning but don't fail request

## Design Decisions

### Why In-Memory Sessions?

- **Simplicity**: No external dependencies for local dev
- **Performance**: Fast access without I/O
- **Sufficient**: 5-10 concurrent sessions is the target
- **Replaceable**: Interface allows future persistence layer

### Why MCP over REST?

- **Agent SDK Integration**: MCP is native to Claude Agent SDK
- **Standard Protocol**: Follows Anthropic's Model Context Protocol
- **Tool-Based**: Agents naturally understand tools

### Why JSONL for Logs?

- **Append-Only**: Safe for concurrent writes
- **Human-Readable**: Easy debugging
- **Streamable**: Can process large files line by line
- **Simple**: No database dependencies

## Testing Strategy

### Test Pyramid

```
           /\
          /  \  E2E Tests (AH-001 to AH-005)
         /    \  - Full journey validation
        /──────\
       /        \  Integration Tests
      /          \  - Component interaction
     /────────────\
    /              \  Unit Tests
   /                \  - Isolated components
  /──────────────────\
```

### Journey Coverage

| Journey | Focus |
|---------|-------|
| AH-001 | Routing to correct agent |
| AH-002 | Session context preservation |
| AH-003 | Confidence escalation |
| AH-004 | Escalation tracking |
| AH-005 | Audit logging |

## Future Considerations

### Persistent Sessions

If needed, sessions could be backed by:
- SQLite for single-node
- Redis for distributed

### Additional MCP Tools

Potential future tools:
- `add_human_response` - Process human feedback
- `get_session_history` - Retrieve conversation
- `close_session` - End conversation

### Federation

For multi-hub deployments:
- Central routing registry
- Cross-hub session forwarding
- Distributed logging
