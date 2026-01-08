# Agent Delegation Architecture Proposals

This document provides a comprehensive analysis of architectural patterns for agent-to-agent communication in Farmer Code. The analysis evaluates **nine approaches** while considering the critical requirement of **conversation persistence for training and prompt improvement**.

> **Constraint**: All proposals assume continued use of the **Claude Agent SDK** (wrapper around Claude Code CLI) as the agent runtime.

## Executive Summary

### Primary Patterns

| Pattern | Complexity | Persistence | Decoupling | Claude SDK Fit | Recommendation |
|---------|------------|-------------|------------|----------------|----------------|
| **Agent Hub (Current)** | Low | Good | Medium | Excellent | Baseline |
| **Redis Streams** | Medium | Excellent | High | Good | Consider for scale |
| **MCP-Native** | Medium | Medium | High | Excellent | Strong alternative |
| **LangGraph** | High | Excellent | Low | Partial | Not recommended |

### Additional Patterns Evaluated

| Pattern | Complexity | Persistence | Decoupling | Claude SDK Fit | Recommendation |
|---------|------------|-------------|------------|----------------|----------------|
| **Blackboard Architecture** | Medium | Excellent | Medium | Good | **Strong candidate** |
| **Temporal (Durable Execution)** | Medium | Excellent | Medium | Good | **Best for reliability** |
| **A2A Protocol (Google)** | Medium | Medium | High | Good | Complement to MCP |
| **Event Sourcing + CQRS** | High | Excellent | High | Medium | Overkill for now |
| **Actor Model (Ray/Dapr)** | High | Good | High | Medium | Overkill for now |

**Bottom Line**: The current Agent Hub architecture is well-suited for the project's needs. However, two patterns stand out for future consideration:

1. **Blackboard Architecture** - Recent research (2025) shows 13-57% improvement over traditional patterns with lower token consumption. Excellent fit for shared knowledge and training data capture.

2. **Temporal (Durable Execution)** - Industry adoption (OpenAI Codex uses it) and excellent fault tolerance. Best choice if reliability and automatic recovery are priorities.

---

## 1. Current Architecture: Agent Hub (FastAPI)

### Overview

The current architecture uses a centralized **Agent Hub** as a REST-based coordination layer. Agent services (Baron, Duc, Marie) are independent FastAPI services invoked via HTTP.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator                                │
│                     (State Machine)                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Agent Hub                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Router    │  │   Session   │  │ Escalation  │              │
│  │             │  │   Manager   │  │   Handler   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Baron   │    │   Duc    │    │  Marie   │
    │  :8002   │    │  :8003   │    │  :8004   │
    └──────────┘    └──────────┘    └──────────┘
```

### Communication Pattern

- **Protocol**: REST/HTTP (JSON-RPC style)
- **Discovery**: Static routing configuration (`router.py`)
- **Session State**: SQLite database (per-service)
- **Message Flow**: Request-response (synchronous)

### Conversation Persistence

| Aspect | Implementation | Training Suitability |
|--------|----------------|---------------------|
| Sessions | SQLite `sessions` table | Good |
| Messages | SQLite `messages` table | Good |
| Escalations | SQLite `escalations` table | Good |
| Agent Responses | `InvokeResponse` stored in workflow | Good |
| Audit Trail | JSONL files per feature | Excellent |

**Current persistence code** (`session_manager.py:117-169`):
```python
def add_message(
    self,
    session_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> Message:
    """Add a message to a session with full persistence."""
```

### Strengths

1. **Simple to understand and debug** - REST APIs are well-tooled
2. **Claude SDK native** - Agents use SDK directly, no adaptation layer
3. **Persistence built-in** - SQLite stores all conversations
4. **Type safety** - Pydantic contracts enforce schema
5. **Low latency** - Direct HTTP calls, no broker overhead

### Weaknesses

1. **Tight coupling** - Router has hardcoded agent URLs
2. **No async messaging** - Blocking request-response only
3. **Single point of failure** - Agent Hub must be available
4. **Limited replay** - No native message replay capability
5. **Scale ceiling** - SQLite doesn't scale horizontally

### Training Data Capture

```
Current Flow:
┌──────────────────────────────────────────────────────────────┐
│  User Question → Agent Hub → Agent → Response                 │
│        │              │           │         │                 │
│        ▼              ▼           ▼         ▼                 │
│  [Message Table] [Session Table] [Invoke Logs] [JSONL Audit]  │
└──────────────────────────────────────────────────────────────┘
```

**Captured Data**:
- Full conversation history (question + answer)
- Confidence scores
- Uncertainty reasons
- Tool usage metadata
- Escalation outcomes
- Human corrections

---

## 2. Redis Streams Architecture

### Overview

[Redis Streams](https://redis.io/learn/howtos/solutions/microservices/interservice-communication) provides a distributed, persistent message log that decouples producers from consumers. Unlike pub/sub (fire-and-forget), Streams persist messages and support consumer groups for parallel processing.

```
┌───────────────────────────────────────────────────────────────────┐
│                       Orchestrator                                 │
└────────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
┌───────────────────────────────────────────────────────────────────┐
│                        Redis                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    REQUESTS_STREAM                           │  │
│  │  [msg1: {to: baron, request: {...}}]                        │  │
│  │  [msg2: {to: duc, request: {...}}]                          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   RESPONSES_STREAM                           │  │
│  │  [msg1: {from: baron, response: {...}, confidence: 85}]     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────┐ │
│  │ baron_consumer_grp │ │ duc_consumer_group │ │ marie_cons_grp │ │
│  └────────────────────┘ └────────────────────┘ └────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
          │                        │                      │
          ▼                        ▼                      ▼
    ┌──────────┐            ┌──────────┐           ┌──────────┐
    │  Baron   │            │   Duc    │           │  Marie   │
    │ (SDK)    │            │  (SDK)   │           │  (SDK)   │
    └──────────┘            └──────────┘           └──────────┘
```

### Communication Pattern

- **Protocol**: Redis Streams (XADD/XREADGROUP)
- **Discovery**: Stream naming convention (e.g., `BARON_REQUESTS`)
- **Session State**: Redis Hash or separate stream per session
- **Message Flow**: Asynchronous with acknowledgment

### Implementation Sketch

**Producer (Orchestrator)**:
```python
async def dispatch_to_agent(agent: str, request: InvokeRequest) -> str:
    """Publish request to agent's stream, return message ID."""
    message_id = await redis.xadd(
        f"{agent.upper()}_REQUESTS",
        {
            "request_id": str(uuid4()),
            "payload": request.model_dump_json(),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    return message_id
```

**Consumer (Agent)**:
```python
async def consume_requests():
    """Agent consumes from its dedicated stream."""
    while True:
        messages = await redis.xreadgroup(
            groupname="baron_workers",
            consumername="worker_1",
            streams={"BARON_REQUESTS": ">"},
            block=5000
        )
        for stream, entries in messages:
            for msg_id, data in entries:
                result = await process_request(data)
                await publish_response(msg_id, result)
                await redis.xack("BARON_REQUESTS", "baron_workers", msg_id)
```

### Conversation Persistence

| Aspect | Implementation | Training Suitability |
|--------|----------------|---------------------|
| Message History | Stream entries (immutable) | Excellent |
| Session State | Redis Hash per session | Good |
| Replay Capability | `XRANGE` from any offset | Excellent |
| Cross-Session Memory | Redis Search / Vector | Excellent |
| Retention | Configurable MAXLEN/MINID | Excellent |

**Key advantage**: Messages are persisted until explicitly trimmed. Unlike pub/sub, late-joining consumers can read historical messages.

### Training Data Export

```python
async def export_training_data(session_id: str) -> list[dict]:
    """Export all messages for a session as training data."""
    # Get all request/response pairs
    requests = await redis.xrange(f"SESSION_{session_id}_REQUESTS")
    responses = await redis.xrange(f"SESSION_{session_id}_RESPONSES")

    # Combine into training format
    return [
        {
            "input": req["payload"],
            "output": resp["payload"],
            "confidence": resp.get("confidence"),
            "human_correction": resp.get("human_override"),
        }
        for req, resp in zip(requests, responses)
    ]
```

### Strengths

1. **Decoupled producers/consumers** - Agents don't need direct connectivity
2. **Persistent by default** - All messages stored until trimmed
3. **Consumer groups** - Multiple workers can process in parallel
4. **Replay capability** - Re-process from any point in stream
5. **Sub-millisecond latency** - Redis is extremely fast
6. **Simpler than Kafka** - Easier to deploy and operate

### Weaknesses

1. **Additional infrastructure** - Requires Redis cluster
2. **No request-response primitive** - Must correlate manually
3. **Schema evolution** - No built-in schema registry
4. **Operational complexity** - Need to manage retention, replication
5. **Async complexity** - Harder to reason about than REST

### Claude SDK Integration

The Claude Agent SDK expects a stateful environment with direct tool invocation. Integration requires:

1. **Wrapper service** - Agent wraps SDK and consumes from stream
2. **Response correlation** - Track request IDs through SDK invocation
3. **Session mapping** - Translate stream position to SDK session state

```python
class StreamAgent:
    """Wraps Claude SDK with Redis Streams interface."""

    def __init__(self, agent_name: str, redis: Redis):
        self.sdk = ClaudeSDKClient()
        self.redis = redis
        self.stream = f"{agent_name.upper()}_REQUESTS"

    async def run(self):
        async for message in self.consume():
            # Invoke Claude SDK
            result = await self.sdk.query(message["prompt"])
            # Publish to response stream
            await self.publish_response(message["id"], result)
```

---

## 3. MCP-Native Architecture (RESTful Discovery)

### Overview

The [Model Context Protocol](https://modelcontextprotocol.io/specification/2025-11-25) (MCP) provides a standardized way for agents to expose and discover capabilities. In this pattern, agents register as MCP servers, and other agents discover them through capability negotiation—**no central message bus required**.

```
┌───────────────────────────────────────────────────────────────────┐
│                       Orchestrator                                 │
│                  (MCP Client + Host)                               │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   MCP Client Registry                        │  │
│  │  baron: {tools: [specify, plan, tasks], url: localhost:8002} │  │
│  │  duc: {tools: [architecture, api_design], url: localhost:8003│  │
│  │  marie: {tools: [testing, qa_review], url: localhost:8004}   │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │    Baron     │    │     Duc      │    │    Marie     │
    │  MCP Server  │    │  MCP Server  │    │  MCP Server  │
    │              │    │              │    │              │
    │  Tools:      │    │  Tools:      │    │  Tools:      │
    │  - specify   │    │  - arch      │    │  - test      │
    │  - plan      │    │  - api       │    │  - qa        │
    │  - tasks     │    │  - design    │    │  - edge      │
    └──────────────┘    └──────────────┘    └──────────────┘
```

### Communication Pattern

- **Protocol**: JSON-RPC 2.0 over stdio/SSE/HTTP
- **Discovery**: MCP capability negotiation (`initialize` handshake)
- **Session State**: Client-managed (orchestrator tracks sessions)
- **Message Flow**: Request-response with notifications

### Agent as MCP Server

Each agent exposes itself as an MCP server with typed tools:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("baron")

@server.tool()
async def specify(
    feature_description: str,
    context: dict | None = None
) -> TextContent:
    """Create a feature specification from description.

    Args:
        feature_description: Natural language feature description
        context: Optional context (existing code, constraints)

    Returns:
        Generated spec.md content
    """
    sdk = ClaudeSDKClient()
    result = await sdk.query(
        prompt=f"Create spec for: {feature_description}",
        context=context
    )
    return TextContent(type="text", text=result.output)

# Expose capabilities on initialization
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="specify",
            description="Create feature specification",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_description": {"type": "string"},
                    "context": {"type": "object"}
                },
                "required": ["feature_description"]
            }
        ),
        # ... more tools
    ]
```

### Agent-to-Agent Communication

Per [Microsoft's analysis](https://developer.microsoft.com/blog/can-you-build-agent2agent-communication-on-mcp-yes) and [AWS's implementation guide](https://aws.amazon.com/blogs/opensource/open-protocols-for-agent-interoperability-part-1-inter-agent-communication-on-mcp/), MCP enables sophisticated agent-to-agent workflows:

```
Baron (Client) ──────────────────────────► Duc (Server)
      │                                          │
      │  1. Initialize + capability exchange     │
      │◄────────────────────────────────────────►│
      │                                          │
      │  2. Tool call: architecture_review()     │
      │─────────────────────────────────────────►│
      │                                          │
      │  3. Result + confidence                  │
      │◄─────────────────────────────────────────│
      │                                          │
      │  4. Sampling request (if needed)         │
      │◄─────────────────────────────────────────│
      │                                          │
      │  5. LLM result                          │
      │─────────────────────────────────────────►│
```

### Conversation Persistence

| Aspect | Implementation | Training Suitability |
|--------|----------------|---------------------|
| Tool Invocations | Client logs all calls | Good |
| Session State | MCP session with message list | Good |
| Sampling Requests | Logged by server | Good |
| Cross-Agent | Orchestrator aggregates | Good |
| Audit | Custom logging layer needed | Medium |

**Key consideration**: MCP doesn't have built-in persistence. A logging layer must be added:

```python
class PersistentMCPClient:
    """MCP client with conversation logging."""

    def __init__(self, db: Session, mcp_client: Client):
        self.db = db
        self.client = mcp_client

    async def call_tool(
        self,
        tool: str,
        arguments: dict,
        session_id: str
    ) -> CallToolResult:
        # Log the request
        request = MCPRequest(
            session_id=session_id,
            tool=tool,
            arguments=arguments,
            timestamp=datetime.utcnow()
        )
        self.db.add(request)

        # Make the call
        result = await self.client.call_tool(tool, arguments)

        # Log the response
        response = MCPResponse(
            request_id=request.id,
            result=result.model_dump(),
            timestamp=datetime.utcnow()
        )
        self.db.add(response)
        self.db.commit()

        return result
```

### Strengths

1. **Native Claude SDK integration** - MCP is built into Claude Code
2. **Typed tool interfaces** - Schema validation on both ends
3. **Dynamic discovery** - Agents advertise capabilities
4. **No message bus** - Direct peer-to-peer communication
5. **Bidirectional** - Servers can request sampling from clients
6. **Standard protocol** - Industry adoption (OpenAI, Microsoft, AWS)

### Weaknesses

1. **No built-in persistence** - Must add logging layer
2. **Connection management** - Must handle reconnection
3. **Limited async** - Primarily request-response
4. **Security considerations** - Tool descriptions treated as untrusted
5. **Newer ecosystem** - Fewer examples and patterns

### Claude SDK Integration

**Excellent fit**. The Claude Agent SDK natively supports MCP:

```python
from claude_agent_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    # Connect to agent's MCP server
    await client.connect_mcp_server(
        server_path="./agents/baron/mcp_server.py"
    )

    # Tools are automatically available
    result = await client.query(
        prompt="Plan the authentication feature",
        # Baron's tools (specify, plan, tasks) now available
    )
```

---

## 4. LangGraph Architecture

### Overview

[LangGraph](https://www.langchain.com/langgraph) is a graph-based orchestration framework for building stateful, multi-agent systems. Agents are nodes in a directed graph, with edges defining control flow and state shared across the graph.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LangGraph                                    │
│                                                                      │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     │
│    │ START   │────►│  Baron  │────►│   Duc   │────►│  Marie  │     │
│    └─────────┘     └────┬────┘     └────┬────┘     └────┬────┘     │
│                         │               │               │           │
│                         │   ┌───────────┘               │           │
│                         │   │                           │           │
│                         ▼   ▼                           ▼           │
│                    ┌─────────────┐              ┌─────────────┐     │
│                    │  Supervisor │              │    END      │     │
│                    └─────────────┘              └─────────────┘     │
│                                                                      │
│    ┌─────────────────────────────────────────────────────────────┐  │
│    │                      StateGraph                              │  │
│    │  {                                                           │  │
│    │    "messages": [...],                                        │  │
│    │    "current_agent": "baron",                                 │  │
│    │    "feature_spec": null,                                     │  │
│    │    "implementation_plan": null                               │  │
│    │  }                                                           │  │
│    └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Communication Pattern

- **Protocol**: In-process function calls (no network)
- **Discovery**: Static graph definition
- **Session State**: Centralized StateGraph with checkpointing
- **Message Flow**: Graph traversal with conditional edges

### Multi-Agent Implementation

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# Define shared state
class WorkflowState(TypedDict):
    messages: Annotated[list, add_messages]
    current_phase: str
    feature_spec: str | None
    implementation_plan: str | None
    task_list: str | None

# Create graph
workflow = StateGraph(WorkflowState)

# Add agent nodes
workflow.add_node("baron", baron_agent)
workflow.add_node("duc", duc_agent)
workflow.add_node("marie", marie_agent)
workflow.add_node("supervisor", supervisor_agent)

# Define edges
workflow.add_edge("baron", "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    route_to_next_agent,
    {
        "duc": "duc",
        "marie": "marie",
        "end": END
    }
)

# Add persistence
checkpointer = SqliteSaver.from_conn_string("workflow.db")
app = workflow.compile(checkpointer=checkpointer)

# Run with thread ID for persistence
config = {"configurable": {"thread_id": "feature-008"}}
result = app.invoke({"messages": [("user", "Plan auth feature")]}, config)
```

### Conversation Persistence

| Aspect | Implementation | Training Suitability |
|--------|----------------|---------------------|
| State Snapshots | Checkpointer (SQLite/Redis) | Excellent |
| Message History | `messages` in state | Excellent |
| Replay | Time-travel debugging | Excellent |
| Cross-Session | RedisStore for shared memory | Excellent |
| Branching | Full state at each node | Excellent |

[LangGraph + Redis](https://redis.io/blog/langgraph-redis-build-smarter-ai-agents-with-memory-persistence/) provides production-grade persistence:

```python
from langgraph_checkpoint_redis import RedisSaver

checkpointer = RedisSaver(
    redis_url="redis://localhost:6379",
    ttl=timedelta(days=30)  # Retain for training
)

# All state transitions persisted
app = workflow.compile(checkpointer=checkpointer)
```

### Strengths

1. **Excellent persistence** - Checkpointing is first-class
2. **Visual debugging** - Graph visualization and time-travel
3. **Human-in-the-loop** - Built-in interrupt/resume
4. **Fault tolerance** - Automatic recovery from checkpoints
5. **State isolation** - Clear boundaries between agents
6. **Rich ecosystem** - LangSmith observability

### Weaknesses

1. **Steep learning curve** - Graph theory, state machines required
2. **Tight coupling** - Agents must use LangGraph primitives
3. **LangChain dependency** - Heavy framework with opinions
4. **Claude SDK mismatch** - Different agent model than SDK
5. **Complexity ceiling** - >5 agents becomes hard to manage
6. **Abstraction overhead** - Simple tasks need graph boilerplate

### Claude SDK Integration

**Partial fit**. LangGraph has its own agent model that conflicts with Claude Agent SDK:

```python
# LangGraph expects this pattern:
def baron_agent(state: WorkflowState) -> WorkflowState:
    # LangGraph manages the LLM call
    response = model.invoke(state["messages"])
    return {"messages": [response]}

# But Claude SDK provides this:
async with ClaudeSDKClient() as client:
    # SDK manages its own loop, tools, and context
    result = await client.query(prompt, tools=[...])
```

**Integration options**:

1. **Wrapper nodes** - LangGraph node wraps SDK call (loses SDK loop benefits)
2. **Hybrid** - Use LangGraph for orchestration, SDK for agent execution
3. **Replace SDK** - Use LangGraph's ChatAnthropic directly (loses SDK tools)

```python
# Hybrid approach: LangGraph orchestrates, SDK executes
def baron_agent(state: WorkflowState) -> WorkflowState:
    # Extract prompt from state
    prompt = state["messages"][-1].content

    # Delegate to SDK (blocking call, loses streaming)
    import asyncio
    result = asyncio.run(invoke_baron_sdk(prompt))

    # Return to LangGraph state
    return {"messages": [AIMessage(content=result)]}
```

---

## 5. Blackboard Architecture

### Overview

The [Blackboard Architecture](https://arxiv.org/html/2507.01701v1) is a classic AI pattern experiencing a major resurgence with LLMs in 2025. A shared knowledge base (the "blackboard") is iteratively updated by specialist agents, with a control unit dynamically selecting which agent acts next based on the current state.

Recent research shows **13-57% improvement** over RAG and master-slave patterns while consuming **fewer tokens**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Control Unit                                    │
│              (LLM-based agent selector)                              │
│                                                                      │
│    Reads blackboard state → Selects relevant agent → Executes       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BLACKBOARD                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     Public Space                               │  │
│  │  - Current query and context                                   │  │
│  │  - All agent messages and intermediate results                 │  │
│  │  - Consensus state and decisions                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ Baron Space │ │  Duc Space  │ │ Marie Space │ │ Critic Space│   │
│  │  (private)  │ │  (private)  │ │  (private)  │ │  (private)  │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
        ▲                  ▲                  ▲                ▲
        │                  │                  │                │
   ┌────┴────┐       ┌─────┴────┐       ┌─────┴────┐     ┌─────┴────┐
   │  Baron  │       │   Duc    │       │  Marie   │     │  Critic  │
   │ Planner │       │ Architect│       │  Tester  │     │ Reviewer │
   └─────────┘       └──────────┘       └──────────┘     └──────────┘
```

### Communication Pattern

- **Protocol**: Shared memory reads/writes (no direct agent-to-agent messaging)
- **Discovery**: Control unit knows all agents; agents know only the blackboard
- **Session State**: Blackboard IS the session state
- **Message Flow**: Iterative cycles until consensus

### Key Innovation: No Agent Memory Modules

Per the [LbMAS research](https://arxiv.org/html/2507.01701v1):

> "All agents' messages are stored on the blackboard and the memory modules become unnecessary."

This eliminates per-agent context management and reduces total token consumption.

### Implementation Sketch

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Blackboard:
    """Shared knowledge base for all agents."""

    # Public space - visible to all agents
    query: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    messages: list[dict] = field(default_factory=list)  # All agent outputs
    consensus: str | None = None

    # Private spaces - agent-specific scratchpads
    private_spaces: dict[str, dict] = field(default_factory=dict)

    def post(self, agent: str, content: str, metadata: dict | None = None):
        """Agent posts to public space."""
        self.messages.append({
            "agent": agent,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_context_for_agent(self, agent: str) -> dict:
        """Get full context for an agent's next action."""
        return {
            "query": self.query,
            "context": self.context,
            "history": self.messages,
            "private": self.private_spaces.get(agent, {})
        }


class BlackboardOrchestrator:
    """Control unit that selects and executes agents."""

    def __init__(self, agents: dict[str, Agent], selector_llm: ClaudeSDKClient):
        self.agents = agents
        self.selector = selector_llm
        self.blackboard = Blackboard()

    async def solve(self, query: str, max_rounds: int = 5) -> str:
        """Iterate until consensus or max rounds."""
        self.blackboard.query = query

        for round in range(max_rounds):
            # Control unit selects next agent based on blackboard state
            agent_name = await self._select_agent()

            if agent_name == "CONSENSUS":
                break

            # Execute selected agent
            agent = self.agents[agent_name]
            result = await agent.execute(
                self.blackboard.get_context_for_agent(agent_name)
            )

            # Agent posts to blackboard
            self.blackboard.post(agent_name, result.output, result.metadata)

        return self.blackboard.consensus or self.blackboard.messages[-1]["content"]

    async def _select_agent(self) -> str:
        """Use LLM to select next agent based on blackboard state."""
        prompt = f"""
        Based on the current blackboard state, which agent should act next?

        Query: {self.blackboard.query}
        Messages so far: {len(self.blackboard.messages)}
        Last message: {self.blackboard.messages[-1] if self.blackboard.messages else 'None'}

        Available agents: {list(self.agents.keys())}

        Return ONLY the agent name, or "CONSENSUS" if the problem is solved.
        """
        result = await self.selector.query(prompt)
        return result.output.strip()
```

### Conversation Persistence

| Aspect | Implementation | Training Suitability |
|--------|----------------|---------------------|
| Full History | Blackboard.messages | Excellent |
| Agent Contributions | Tagged by agent | Excellent |
| Reasoning Chain | Sequential messages show thought process | Excellent |
| Consensus Points | Marked in blackboard | Excellent |
| Private Reasoning | Agent private spaces | Good |

**Key advantage for training**: The blackboard naturally captures the full reasoning chain across all agents, making it ideal for training data extraction.

```python
def export_training_data(blackboard: Blackboard) -> TrainingExample:
    """Export blackboard session as training example."""
    return TrainingExample(
        user_input=blackboard.query,
        agent_outputs=[
            {"agent": m["agent"], "content": m["content"]}
            for m in blackboard.messages
        ],
        final_output=blackboard.consensus,
        reasoning_chain=blackboard.messages,  # Full chain preserved
    )
```

### Strengths

1. **Token efficient** - Shared memory eliminates redundant context passing
2. **Natural audit trail** - Blackboard IS the conversation history
3. **Dynamic agent selection** - Control unit adapts to problem state
4. **Proven results** - 13-57% improvement in recent benchmarks
5. **Simple mental model** - Agents read/write to shared space
6. **Decentralized knowledge** - No single agent holds all context

### Weaknesses

1. **Single point of contention** - Blackboard can become bottleneck
2. **Control unit complexity** - Agent selection logic can be tricky
3. **No native distribution** - Blackboard typically in-memory
4. **Consensus definition** - Must define when problem is "solved"
5. **Agent ordering** - Control unit must handle agent selection well

### Claude SDK Integration

**Good fit**. Each agent wraps the Claude SDK and reads/writes to blackboard:

```python
class BlackboardAgent:
    """Agent that operates on blackboard via Claude SDK."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.sdk = ClaudeSDKClient()

    async def execute(self, context: dict) -> AgentResult:
        prompt = f"""
        You are {self.name}, a {self.role}.

        Current query: {context['query']}
        Previous contributions: {context['history']}

        Provide your contribution to solving this problem.
        """
        result = await self.sdk.query(prompt)
        return AgentResult(output=result.output, metadata={"role": self.role})
```

---

## 6. Temporal (Durable Execution)

### Overview

[Temporal](https://temporal.io/) provides **durable execution** - the ability to survive failures and resume exactly where execution left off. OpenAI uses Temporal for Codex. In March 2025, Temporal raised $146M at a $1.72B valuation, with investors citing AI applicability.

The key insight: agent workflows are long-running, failure-prone, and need exactly-once semantics. Temporal provides this out of the box.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Temporal Cluster                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Event History                               │  │
│  │  [WorkflowStarted] → [ActivityScheduled: baron_invoke]        │  │
│  │  → [ActivityCompleted: baron_invoke] → [ActivityScheduled:    │  │
│  │  duc_review] → [ActivityCompleted: duc_review] → ...          │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   Workflow Definition                         │    │
│  │  @workflow.defn                                              │    │
│  │  class SpecKitWorkflow:                                      │    │
│  │      @workflow.run                                           │    │
│  │      async def run(self, feature: str):                      │    │
│  │          spec = await workflow.execute_activity(             │    │
│  │              baron_specify, feature)                         │    │
│  │          plan = await workflow.execute_activity(             │    │
│  │              baron_plan, spec)                               │    │
│  │          # If we crash here, we resume from this point       │    │
│  │          tasks = await workflow.execute_activity(            │    │
│  │              baron_tasks, plan)                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │    Baron     │    │     Duc      │    │    Marie     │
    │  (Activity)  │    │  (Activity)  │    │  (Activity)  │
    └──────────────┘    └──────────────┘    └──────────────┘
```

### Communication Pattern

- **Protocol**: Temporal Activities (durable function calls)
- **Discovery**: Workflow defines activity routing
- **Session State**: Temporal Event History (immutable, persistent)
- **Message Flow**: Deterministic workflow replay

### Durable Execution Explained

When an activity (agent invocation) completes, the result is saved to Temporal's **Event History**. If the workflow crashes:

1. Temporal detects the failure
2. Workflow is replayed from Event History
3. Already-completed activities return cached results
4. Execution continues from the failure point

This means: **no lost work, ever**.

### Implementation with Pydantic AI + Temporal

Per [Temporal's integration guide](https://temporal.io/blog/build-durable-ai-agents-pydantic-ai-and-temporal):

```python
from temporalio import workflow, activity
from temporalio.client import Client
from claude_agent_sdk import ClaudeSDKClient

# Define activities (agent invocations)
@activity.defn
async def invoke_baron(request: InvokeRequest) -> InvokeResponse:
    """Durable activity wrapping Baron agent."""
    async with ClaudeSDKClient() as sdk:
        result = await sdk.query(
            prompt=request.context["prompt"],
            tools=request.context.get("tools", [])
        )
        return InvokeResponse(
            success=True,
            result=InvokeResult(output=result.output),
            confidence=85,
            metadata=InvokeMetadata(
                duration_ms=result.duration_ms,
                model_used=result.model
            )
        )

@activity.defn
async def invoke_duc(request: InvokeRequest) -> InvokeResponse:
    """Durable activity wrapping Duc agent."""
    # Similar implementation
    pass

# Define workflow (orchestration)
@workflow.defn
class SpecKitWorkflow:
    """Durable workflow for SpecKit phases."""

    @workflow.run
    async def run(self, feature_description: str) -> WorkflowResult:
        # Phase 1: Specify (survives crashes)
        spec_request = InvokeRequest(
            workflow_type="specify",
            context={"prompt": feature_description}
        )
        spec_result = await workflow.execute_activity(
            invoke_baron,
            spec_request,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )

        # Phase 2: Architecture Review (survives crashes)
        review_request = InvokeRequest(
            workflow_type="architecture_review",
            context={"spec": spec_result.result.output}
        )
        review_result = await workflow.execute_activity(
            invoke_duc,
            review_request,
            start_to_close_timeout=timedelta(minutes=10)
        )

        # Phase 3: Plan (survives crashes)
        plan_request = InvokeRequest(
            workflow_type="plan",
            context={
                "spec": spec_result.result.output,
                "architecture_notes": review_result.result.output
            }
        )
        plan_result = await workflow.execute_activity(
            invoke_baron,
            plan_request,
            start_to_close_timeout=timedelta(minutes=10)
        )

        return WorkflowResult(
            spec=spec_result.result.output,
            plan=plan_result.result.output
        )

# Start workflow
async def main():
    client = await Client.connect("localhost:7233")
    result = await client.execute_workflow(
        SpecKitWorkflow.run,
        "Add user authentication",
        id="feature-008-auth",
        task_queue="speckit-workers"
    )
```

### Conversation Persistence

| Aspect | Implementation | Training Suitability |
|--------|----------------|---------------------|
| Full History | Event History (immutable) | Excellent |
| Activity Results | Stored with workflow | Excellent |
| Replay | Native workflow replay | Excellent |
| Failure Points | Recorded in history | Excellent |
| Retry Attempts | All attempts logged | Excellent |

**Key advantage**: Event History is an immutable, append-only log of everything that happened. Perfect for training data.

```python
async def export_workflow_training_data(workflow_id: str) -> list[TrainingExample]:
    """Export workflow execution as training examples."""
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(workflow_id)

    # Get full event history
    history = await handle.fetch_history()

    examples = []
    for event in history.events:
        if event.event_type == EventType.ACTIVITY_TASK_COMPLETED:
            # Extract input/output from activity
            examples.append(TrainingExample(
                activity_name=event.activity_type,
                input=event.input,
                output=event.result,
                duration_ms=event.duration_ms
            ))

    return examples
```

### Strengths

1. **Bulletproof reliability** - Survives any failure
2. **Built-in persistence** - Event History is the audit trail
3. **Automatic retries** - Configurable retry policies
4. **Production proven** - OpenAI Codex uses Temporal
5. **Time-travel debugging** - Replay any workflow execution
6. **Visibility** - Temporal UI shows workflow state

### Weaknesses

1. **Infrastructure requirement** - Must run Temporal cluster
2. **Learning curve** - Deterministic workflow constraints
3. **Serialization requirements** - All data must be serializable
4. **Latency overhead** - Event persistence adds latency
5. **Vendor dependency** - Temporal-specific constructs

### Claude SDK Integration

**Good fit**. Activities wrap SDK calls with automatic durability:

```python
@activity.defn
async def durable_claude_query(prompt: str, tools: list | None = None) -> str:
    """Durable Claude SDK invocation."""
    # If this activity crashes and retries, Temporal handles it
    async with ClaudeSDKClient() as sdk:
        result = await sdk.query(prompt, tools=tools)
        return result.output
```

---

## 7. A2A Protocol (Google Agent2Agent)

### Overview

[A2A (Agent2Agent)](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) is Google's open protocol for agent-to-agent communication, announced April 2025 and now maintained by the Linux Foundation. While MCP focuses on **tool/data access**, A2A focuses on **task delegation between agents**.

As of July 2025, A2A v0.3 includes gRPC support, signed security cards, and 150+ supporting organizations.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Client Agent (Baron)                            │
│                                                                      │
│  1. Discover remote agent capabilities via Agent Card                │
│  2. Create task with requirements                                    │
│  3. Send task to remote agent                                        │
│  4. Poll for task completion or receive streaming updates            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                      A2A Protocol (HTTPS + JSON-RPC)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Remote Agent (Duc)                              │
│                                                                      │
│  1. Publish Agent Card describing capabilities                       │
│  2. Receive task from client                                         │
│  3. Process task (may involve sub-tasks to other agents)            │
│  4. Return task result with artifacts                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Card (Capability Discovery)

```json
{
  "name": "duc-architecture-agent",
  "description": "Expert in system architecture and API design",
  "url": "https://agents.farmer1st.com/duc",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "skills": [
    {
      "id": "architecture_review",
      "description": "Review system architecture for scalability and maintainability",
      "inputSchema": {
        "type": "object",
        "properties": {
          "spec": {"type": "string"},
          "constraints": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    {
      "id": "api_design",
      "description": "Design RESTful APIs following best practices"
    }
  ]
}
```

### A2A vs MCP

| Aspect | MCP | A2A |
|--------|-----|-----|
| **Focus** | Tool/data access | Agent-to-agent tasks |
| **Granularity** | Function calls | Complete tasks |
| **Lifecycle** | Synchronous | Long-running with status |
| **Discovery** | Capability negotiation | Agent Cards |
| **Use Case** | "Use this tool" | "Complete this task" |

**They are complementary**: An agent might use MCP to access tools locally, and A2A to delegate complex tasks to remote agents.

### Task Lifecycle

```
Task States:
  PENDING → IN_PROGRESS → COMPLETED
                       ↘ FAILED
                       ↘ CANCELLED

Task Object:
{
  "id": "task-12345",
  "skill": "architecture_review",
  "input": {"spec": "..."},
  "status": "IN_PROGRESS",
  "progress": 0.6,
  "artifacts": [],  // Intermediate results
  "result": null    // Final result when COMPLETED
}
```

### Implementation Sketch

```python
from a2a import A2AClient, AgentCard, Task

class A2AEnabledAgent:
    """Agent that can delegate to other A2A agents."""

    def __init__(self, name: str):
        self.name = name
        self.a2a_client = A2AClient()
        self.known_agents: dict[str, AgentCard] = {}

    async def discover_agent(self, url: str) -> AgentCard:
        """Fetch Agent Card from remote agent."""
        card = await self.a2a_client.get_agent_card(url)
        self.known_agents[card.name] = card
        return card

    async def delegate_task(
        self,
        agent_name: str,
        skill: str,
        input_data: dict
    ) -> Task:
        """Delegate a task to a remote agent."""
        card = self.known_agents[agent_name]

        task = await self.a2a_client.create_task(
            agent_url=card.url,
            skill=skill,
            input=input_data
        )

        # Poll for completion (or use streaming)
        while task.status in ["PENDING", "IN_PROGRESS"]:
            await asyncio.sleep(1)
            task = await self.a2a_client.get_task(card.url, task.id)

        return task

# Usage
baron = A2AEnabledAgent("baron")
await baron.discover_agent("https://agents.farmer1st.com/duc")

# Delegate architecture review to Duc
task = await baron.delegate_task(
    agent_name="duc-architecture-agent",
    skill="architecture_review",
    input_data={"spec": spec_content}
)

architecture_feedback = task.result
```

### Conversation Persistence

| Aspect | Implementation | Training Suitability |
|--------|----------------|---------------------|
| Task History | Task objects with full lifecycle | Good |
| Artifacts | Intermediate results captured | Good |
| Cross-Agent | Task chain preserved | Good |
| Status Updates | Progress tracking | Medium |

### Strengths

1. **Standard protocol** - Linux Foundation backed, 150+ orgs
2. **Task-oriented** - Natural fit for delegation patterns
3. **Long-running support** - Built for async tasks
4. **Streaming** - Real-time progress updates
5. **Complements MCP** - Different abstraction levels

### Weaknesses

1. **Newer than MCP** - Less ecosystem maturity
2. **Infrastructure needs** - Agents must expose HTTP endpoints
3. **No built-in persistence** - Must add task storage
4. **Google-centric** - Primary driver is Google

### Claude SDK Integration

**Good fit** for cross-agent delegation:

```python
class BaronWithA2A:
    """Baron agent with A2A delegation capability."""

    def __init__(self):
        self.sdk = ClaudeSDKClient()
        self.a2a = A2AClient()

    async def specify_with_review(self, feature: str) -> str:
        # Step 1: Baron creates spec using Claude SDK
        spec = await self.sdk.query(f"Create spec for: {feature}")

        # Step 2: Delegate architecture review to Duc via A2A
        review_task = await self.a2a.create_task(
            agent_url="https://duc.farmer1st.com",
            skill="architecture_review",
            input={"spec": spec.output}
        )

        # Step 3: Incorporate feedback
        final_spec = await self.sdk.query(
            f"Revise spec based on feedback: {review_task.result}"
        )

        return final_spec.output
```

---

## 8. Event Sourcing + CQRS

### Overview

[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html) stores all state changes as a sequence of immutable events. [CQRS](https://developer.confluent.io/courses/event-sourcing/cqrs/) separates read and write models. Together, they provide:

- **Complete audit trail** - Every state change recorded
- **Time-travel** - Reconstruct state at any point
- **Event replay** - Rebuild projections from events

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Event Store                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Stream: session-12345                                         │  │
│  │  ─────────────────────────────────────────────────────────────│  │
│  │  [0] SessionStarted {feature_id: "008", agent: "baron"}       │  │
│  │  [1] QuestionAsked {question: "Design auth system"}           │  │
│  │  [2] AgentInvoked {agent: "baron", prompt: "..."}             │  │
│  │  [3] AgentResponded {confidence: 85, output: "..."}           │  │
│  │  [4] EscalationCreated {reason: "Low confidence on JWT"}      │  │
│  │  [5] HumanResponded {action: "correct", response: "..."}      │  │
│  │  [6] SessionCompleted {final_output: "..."}                   │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       ┌────────────┐   ┌────────────┐   ┌────────────┐
       │   Read     │   │  Training  │   │  Analytics │
       │   Model    │   │   Export   │   │  Dashboard │
       │ (current   │   │ (replay    │   │ (aggregate │
       │  state)    │   │  events)   │   │  metrics)  │
       └────────────┘   └────────────┘   └────────────┘
```

### Event Types for Agent Communication

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

@dataclass
class Event:
    """Base event class."""
    event_id: str
    timestamp: datetime
    session_id: str

@dataclass
class SessionStarted(Event):
    feature_id: str
    initial_agent: str

@dataclass
class AgentInvoked(Event):
    agent: str
    workflow_type: str
    prompt: str
    context: dict

@dataclass
class AgentResponded(Event):
    agent: str
    output: str
    confidence: int
    tools_used: list[str]
    tokens_used: int

@dataclass
class EscalationCreated(Event):
    question: str
    tentative_answer: str
    uncertainty_reasons: list[str]

@dataclass
class HumanResponded(Event):
    action: Literal["confirm", "correct", "add_context"]
    response: str | None
    responder: str
```

### Training Data from Event Replay

```python
class TrainingDataProjection:
    """Build training dataset by replaying events."""

    def __init__(self):
        self.examples: list[TrainingExample] = []
        self.current_session: dict = {}

    def apply(self, event: Event):
        """Apply event to build training examples."""
        match event:
            case SessionStarted():
                self.current_session = {
                    "session_id": event.session_id,
                    "feature_id": event.feature_id
                }

            case AgentInvoked():
                self.current_session["last_prompt"] = event.prompt
                self.current_session["agent"] = event.agent

            case AgentResponded():
                self.examples.append(TrainingExample(
                    session_id=self.current_session["session_id"],
                    agent=event.agent,
                    user_input=self.current_session["last_prompt"],
                    agent_output=event.output,
                    confidence=event.confidence,
                    tools_used=event.tools_used
                ))

            case HumanResponded():
                # Augment last example with human feedback
                if self.examples:
                    self.examples[-1].human_action = event.action
                    self.examples[-1].human_correction = event.response

# Usage: replay all events to build training set
async def build_training_dataset(event_store: EventStore) -> list[TrainingExample]:
    projection = TrainingDataProjection()
    async for event in event_store.read_all():
        projection.apply(event)
    return projection.examples
```

### Strengths

1. **Complete history** - Nothing is ever lost
2. **Training-perfect** - Event replay builds any dataset
3. **Time-travel** - Debug any past state
4. **Audit compliance** - Immutable record
5. **Multiple projections** - Same events, different views

### Weaknesses

1. **Complexity** - Significant architecture change
2. **Storage growth** - Events accumulate forever
3. **Query complexity** - Must rebuild state from events
4. **Event schema evolution** - Versioning is hard
5. **Overkill** - May be too much for current needs

### Claude SDK Integration

**Medium fit** - requires wrapper to emit events:

```python
class EventSourcedAgent:
    """Agent that emits events for all actions."""

    def __init__(self, name: str, event_store: EventStore):
        self.name = name
        self.sdk = ClaudeSDKClient()
        self.event_store = event_store

    async def invoke(self, session_id: str, prompt: str) -> str:
        # Emit invocation event
        await self.event_store.append(AgentInvoked(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            session_id=session_id,
            agent=self.name,
            workflow_type="query",
            prompt=prompt,
            context={}
        ))

        # Execute via SDK
        result = await self.sdk.query(prompt)

        # Emit response event
        await self.event_store.append(AgentResponded(
            event_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            session_id=session_id,
            agent=self.name,
            output=result.output,
            confidence=85,
            tools_used=result.tools_used or [],
            tokens_used=result.tokens_used or 0
        ))

        return result.output
```

---

## 9. Actor Model (Ray / Dapr)

### Overview

The [Actor Model](https://docs.ray.io/en/latest/rllib/multi-agent-envs.html) treats agents as independent actors with:
- **Private state** - No shared memory
- **Async messaging** - Communicate via message passing
- **Location transparency** - Actors can run anywhere

[Ray](https://www.ray.io/) and [Dapr](https://dapr.io/) are popular implementations. Ray excels at distributed compute; Dapr at microservices.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Ray Cluster                                   │
│                                                                      │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│   │ Baron Actor  │    │  Duc Actor   │    │ Marie Actor  │         │
│   │              │    │              │    │              │         │
│   │ State:       │    │ State:       │    │ State:       │         │
│   │ - session    │    │ - session    │    │ - session    │         │
│   │ - context    │    │ - context    │    │ - context    │         │
│   │              │    │              │    │              │         │
│   │ Methods:     │    │ Methods:     │    │ Methods:     │         │
│   │ - specify()  │    │ - review()   │    │ - test()     │         │
│   │ - plan()     │    │ - design()   │    │ - qa()       │         │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘         │
│          │                   │                   │                  │
│          └───────────────────┼───────────────────┘                  │
│                              │                                       │
│                    Message Passing                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Ray Actor Implementation

```python
import ray
from claude_agent_sdk import ClaudeSDKClient

@ray.remote
class BaronActor:
    """Baron agent as Ray actor."""

    def __init__(self):
        self.sdk = ClaudeSDKClient()
        self.session_context = {}

    async def specify(self, feature: str) -> str:
        """Create specification (runs on any Ray node)."""
        result = await self.sdk.query(f"Create spec for: {feature}")
        self.session_context["spec"] = result.output
        return result.output

    async def plan(self) -> str:
        """Create plan based on stored spec."""
        spec = self.session_context.get("spec", "")
        result = await self.sdk.query(f"Create plan for spec: {spec}")
        self.session_context["plan"] = result.output
        return result.output

    def get_state(self) -> dict:
        """Return actor state for persistence."""
        return self.session_context

# Usage
ray.init()
baron = BaronActor.remote()

# Async method calls
spec = await baron.specify.remote("Add authentication")
plan = await baron.plan.remote()

# Parallel execution across agents
duc = DucActor.remote()
marie = MarieActor.remote()

# Run reviews in parallel
arch_review, test_plan = await asyncio.gather(
    duc.review.remote(spec),
    marie.test_plan.remote(spec)
)
```

### Strengths

1. **Horizontal scale** - Actors distribute across cluster
2. **Fault isolation** - Actor failure doesn't affect others
3. **Natural parallelism** - Easy concurrent execution
4. **State encapsulation** - Clean agent boundaries
5. **Industry adoption** - Ray powers OpenAI, Uber, Ant Group

### Weaknesses

1. **Infrastructure complexity** - Requires Ray/Dapr cluster
2. **Persistence is manual** - Must implement checkpointing
3. **Debugging difficulty** - Distributed tracing needed
4. **Overkill for small scale** - Complexity not justified
5. **SDK wrapping needed** - Actors wrap Claude SDK calls

### Claude SDK Integration

**Medium fit** - requires actor wrapping:

```python
@ray.remote
class ClaudeActor:
    """Generic Claude SDK actor."""

    def __init__(self, role: str, system_prompt: str):
        self.role = role
        self.system_prompt = system_prompt
        self.sdk = None  # Lazy init

    async def _ensure_sdk(self):
        if self.sdk is None:
            self.sdk = ClaudeSDKClient()

    async def query(self, prompt: str) -> str:
        await self._ensure_sdk()
        result = await self.sdk.query(
            prompt=prompt,
            system=self.system_prompt
        )
        return result.output
```

---

## 10. Comparison Matrix (Updated)

### Feature Comparison (All 9 Patterns)

| Feature | Agent Hub | Redis Streams | MCP-Native | LangGraph | Blackboard | Temporal | A2A | Event Sourcing | Actor Model |
|---------|-----------|---------------|------------|-----------|------------|----------|-----|----------------|-------------|
| **Complexity** | Low | Medium | Medium | High | Medium | Medium | Medium | High | High |
| **Learning Curve** | Low | Medium | Medium | High | Low | Medium | Low | High | High |
| **Claude SDK Fit** | Excellent | Good | Excellent | Partial | Good | Good | Good | Medium | Medium |
| **Decoupling** | Medium | High | High | Low | Medium | Medium | High | High | High |
| **Async Support** | No | Yes | Partial | Yes | No | Yes | Yes | Yes | Yes |
| **Message Replay** | No | Yes | No | Yes | Yes | Yes | No | Yes | No |
| **Built-in Persistence** | Yes | Yes | No | Yes | No | Yes | No | No | No |
| **Horizontal Scale** | Limited | Excellent | Good | Good | Limited | Good | Excellent | Good | Excellent |
| **Human-in-Loop** | Manual | Manual | Elicitation | Built-in | Manual | Signals | Manual | Manual | Manual |
| **Debugging** | Standard | Redis tools | MCP Inspector | Time-travel | Blackboard dump | Temporal UI | Task status | Event replay | Distributed trace |

### Conversation Persistence for Training (All 9 Patterns)

| Aspect | Agent Hub | Redis Streams | MCP | LangGraph | Blackboard | Temporal | A2A | Event Sourcing | Actors |
|--------|-----------|---------------|-----|-----------|------------|----------|-----|----------------|--------|
| **Capture Completeness** | Good | Excellent | Good | Excellent | Excellent | Excellent | Good | Excellent | Medium |
| **Query Flexibility** | SQL | Ranges | Custom | Checkpoints | Direct | History | Tasks | Projections | Custom |
| **Reasoning Chain** | Partial | Partial | Partial | Full | **Full** | Full | Partial | Full | Partial |
| **Human Corrections** | Escalation | Stream | Custom | State | Blackboard | Activity | Task | Event | Custom |
| **Token Efficiency** | Medium | Medium | Medium | Low | **High** | Medium | Medium | Medium | Medium |

### Best Fit by Use Case

| Use Case | Best Pattern | Runner-Up |
|----------|-------------|-----------|
| **Simple orchestration** | Agent Hub | MCP-Native |
| **Training data capture** | Blackboard | Event Sourcing |
| **Fault tolerance** | Temporal | LangGraph |
| **Horizontal scale** | Redis Streams | Actor Model |
| **Agent discovery** | MCP-Native | A2A |
| **Cross-org federation** | A2A | MCP-Native |
| **Token efficiency** | Blackboard | Agent Hub |
| **Audit compliance** | Event Sourcing | Temporal |

### Operational Comparison

| Aspect | Agent Hub | Redis Streams | Blackboard | Temporal |
|--------|-----------|---------------|------------|----------|
| **Infrastructure** | None extra | Redis cluster | None extra | Temporal cluster |
| **Deployment** | Simple | Medium | Simple | Medium |
| **Monitoring** | Standard | Redis metrics | Custom | Temporal UI |
| **Failure Recovery** | Retry | Consumer ACK | Re-run | Automatic |
| **Cost** | Low | Medium | Low | Medium |

---

## 6. Training Data Requirements Analysis

The primary goal is to persist conversations for training and prompt improvement. Here's what needs to be captured:

### Required Data Points

```python
class TrainingExample(BaseModel):
    """Single training example from agent interaction."""

    # Input context
    session_id: str
    feature_id: str
    agent: str
    workflow_type: str

    # The exchange
    user_input: str                    # Original question/request
    agent_output: str                  # Agent's response

    # Quality signals
    confidence: int                    # 0-100
    uncertainty_reasons: list[str]     # Why uncertain

    # Human feedback (if any)
    was_escalated: bool
    human_action: str | None           # confirm/correct/add_context
    human_correction: str | None       # The correction if any

    # Metadata
    model_used: str
    tools_used: list[str]
    duration_ms: int
    timestamp: datetime
```

### Capture Points by Architecture

**Agent Hub (Current)**:
```
Session.messages → TrainingExample.user_input/agent_output
InvokeResponse.confidence → TrainingExample.confidence
Escalation.human_response → TrainingExample.human_correction
```

**Redis Streams**:
```
REQUEST_STREAM entry → TrainingExample.user_input
RESPONSE_STREAM entry → TrainingExample.agent_output + confidence
CORRECTION_STREAM entry → TrainingExample.human_correction
```

**MCP-Native**:
```
call_tool() args → TrainingExample.user_input
CallToolResult → TrainingExample.agent_output
Custom correction endpoint → TrainingExample.human_correction
```

**LangGraph**:
```
StateGraph.messages → TrainingExample.user_input/agent_output
Checkpoint metadata → TrainingExample.confidence
Human interrupt → TrainingExample.human_correction
```

### Recommendation for Training Data

1. **Current Agent Hub** is already well-positioned:
   - SQLite tables capture sessions, messages, escalations
   - JSONL audit logs provide backup
   - Add explicit `TrainingExample` export

2. **Enhancement option**: Add Redis Streams for replay capability without replacing core architecture:
   ```python
   # After successful invocation, publish to training stream
   await redis.xadd("TRAINING_DATA", training_example.model_dump())
   ```

---

## 11. Recommendations (Updated)

### Tier 1: Strong Candidates

#### Option A: Blackboard Architecture (Recommended for Training Focus)

If your **primary goal is training data capture** and **token efficiency**, Blackboard is the strongest candidate:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Blackboard Orchestrator                       │
│              (replaces Agent Hub as central coordinator)         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BLACKBOARD                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Public: query, all messages, consensus                    │  │
│  │  → Directly exportable as training data                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│  Private spaces: baron, duc, marie, critic                      │
└─────────────────────────────────────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
      [Baron SDK]          [Duc SDK]           [Marie SDK]
```

**Why Blackboard**:
- 13-57% performance improvement (per 2025 research)
- Lower token consumption (shared context eliminates redundancy)
- Natural training data format (full reasoning chain preserved)
- Simple mental model (agents read/write shared state)
- Good Claude SDK fit

**Migration path**: Refactor Agent Hub's session/message storage into a Blackboard with control unit.

#### Option B: Temporal (Recommended for Reliability Focus)

If your **primary goal is fault tolerance** and **production reliability**, Temporal is the strongest candidate:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Temporal Cluster                              │
│              (manages workflow state and recovery)               │
│                                                                  │
│  Event History = complete audit trail + training data source    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
    [Baron Activity]     [Duc Activity]      [Marie Activity]
    (durable SDK call)   (durable SDK call)  (durable SDK call)
```

**Why Temporal**:
- Bulletproof reliability (OpenAI Codex uses it)
- Built-in persistence (Event History is immutable)
- Automatic recovery from any failure point
- Excellent training data capture (all activity inputs/outputs logged)
- Production-proven at scale

**Migration path**: Wrap existing agent services as Temporal Activities.

### Tier 2: Good Alternatives

#### Keep Agent Hub + Add Redis Streams

If you want **minimal disruption** while gaining **async capabilities**:

1. Keep Agent Hub for synchronous REST calls
2. Add Redis Streams for training data pipeline
3. Publish to stream after each successful invocation

#### MCP-Native for Federation

If you need **cross-system agent discovery**:

1. Expose agents as MCP servers
2. Use A2A Protocol for task delegation across organizations
3. Keep internal communication via Agent Hub

### Tier 3: Not Recommended (for now)

| Pattern | Reason |
|---------|--------|
| **LangGraph** | Claude SDK mismatch, framework lock-in |
| **Event Sourcing** | Overkill complexity for current scale |
| **Actor Model (Ray)** | Infrastructure overhead not justified |
| **Full CQRS** | Over-engineering for current needs |

### Decision Matrix

Answer these questions to pick your path:

1. **What's your #1 priority?**
   - Training data quality → **Blackboard**
   - Fault tolerance → **Temporal**
   - Minimal change → **Agent Hub + Redis**

2. **Infrastructure tolerance?**
   - No new infra → **Blackboard** or **Agent Hub**
   - Can add Redis → **Redis Streams**
   - Can add Temporal → **Temporal**

3. **Scale expectations?**
   - <100 sessions/day → Any pattern works
   - 100-10K sessions/day → **Blackboard** or **Temporal**
   - >10K sessions/day → **Redis Streams** or **Actor Model**

### Recommended Hybrid Architecture

For the best of all worlds, consider a **layered approach**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: Federation (Future)                                    │
│  - MCP servers for external consumers                            │
│  - A2A Protocol for cross-org delegation                         │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: Durability (Phase 2)                                   │
│  - Temporal for workflow orchestration                           │
│  - Automatic failure recovery                                    │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: Knowledge Sharing (Phase 1)                            │
│  - Blackboard for agent collaboration                            │
│  - Training data capture                                         │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Agent Execution (Current)                              │
│  - Claude Agent SDK for all agents                               │
│  - FastAPI services                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. Implementation Roadmap (Revised)

### Phase 1: Blackboard Integration (Recommended First Step)

```
Tasks:
- [ ] Create Blackboard data model (public space, private spaces)
- [ ] Implement BlackboardOrchestrator with LLM-based agent selection
- [ ] Migrate session/message storage to Blackboard format
- [ ] Add training data export from Blackboard.messages
- [ ] Implement consensus detection logic
- [ ] Add Critic agent role for quality validation
```

**Deliverable**: Agent Hub evolved into Blackboard-based orchestration with native training data capture.

### Phase 2: Durable Execution with Temporal (Production Hardening)

```
Tasks:
- [ ] Deploy Temporal cluster (or use Temporal Cloud)
- [ ] Wrap agent invocations as Temporal Activities
- [ ] Define SpecKitWorkflow with retry policies
- [ ] Implement training data export from Event History
- [ ] Add Temporal UI for workflow monitoring
- [ ] Configure alerting for failed workflows
```

**Deliverable**: Bulletproof workflow execution with automatic recovery.

### Phase 3: Federation Layer (Cross-System Integration)

```
Tasks:
- [ ] Expose agents as MCP servers
- [ ] Implement A2A Agent Cards for capability discovery
- [ ] Add task delegation via A2A Protocol
- [ ] Document external integration patterns
- [ ] Add authentication/authorization for external access
```

**Deliverable**: Agents discoverable and invokable by external systems.

### Phase 4: Scale Layer (If Needed)

```
Tasks:
- [ ] Add Redis Streams for high-throughput scenarios
- [ ] Implement consumer groups for parallel processing
- [ ] Add training data pipeline to ML infrastructure
- [ ] Consider Actor Model (Ray) for compute-intensive tasks
```

**Deliverable**: Horizontal scaling capability for >10K sessions/day.

---

## 13. References

### Blackboard Architecture
- [Exploring Advanced LLM Multi-Agent Systems Based on Blackboard Architecture (2025)](https://arxiv.org/html/2507.01701v1)
- [Building Intelligent Multi-Agent Systems with MCPs and the Blackboard Pattern](https://medium.com/@dp2580/building-intelligent-multi-agent-systems-with-mcps-and-the-blackboard-pattern-to-build-systems-a454705d5672)
- [Agent Blackboard: Multi-Agent Coordination System](https://github.com/claudioed/agent-blackboard)
- [The Blackboard Pattern: A Framework for Complex Problem Solving](https://dev.to/lovestaco/the-blackboard-pattern-a-framework-for-complex-problem-solving-4o1p)
- [Blackboard System - Wikipedia](https://en.wikipedia.org/wiki/Blackboard_system)

### Temporal (Durable Execution)
- [Build Durable AI Agents with Pydantic AI and Temporal](https://temporal.io/blog/build-durable-ai-agents-pydantic-ai-and-temporal)
- [Durable Execution meets AI: Why Temporal is Ideal for AI Agents](https://temporal.io/blog/durable-execution-meets-ai-why-temporal-is-the-perfect-foundation-for-ai)
- [How To Build a Durable AI Agent with Temporal and Python](https://learn.temporal.io/tutorials/ai/durable-ai-agent/)
- [Production-ready Agents with OpenAI Agents SDK + Temporal](https://temporal.io/blog/announcing-openai-agents-sdk-integration)
- [Pydantic AI Temporal Documentation](https://ai.pydantic.dev/durable_execution/temporal/)

### A2A Protocol (Google Agent2Agent)
- [Announcing the Agent2Agent Protocol (A2A) - Google Developers](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [Agent2Agent Protocol GitHub Repository](https://github.com/a2aproject/A2A)
- [A2A Protocol is Getting an Upgrade - Google Cloud](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade)
- [What Is Agent2Agent (A2A) Protocol? - IBM](https://www.ibm.com/think/topics/agent2agent-protocol)
- [ADK with Agent2Agent (A2A) Protocol - Google](https://google.github.io/adk-docs/a2a/)
- [Linux Foundation Launches A2A Protocol Project](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents)

### Redis Streams
- [Microservices Communication with Redis Streams](https://redis.io/learn/howtos/solutions/microservices/interservice-communication)
- [Event-Driven Architecture Using Redis Streams](https://www.harness.io/blog/event-driven-architecture-redis-streams)
- [Beyond the Hype: Why We Chose Redis Streams Over Kafka](https://dev.to/mtk3d/beyond-the-hype-why-we-chose-redis-streams-over-kafka-for-our-microservices-dmc)

### MCP (Model Context Protocol)
- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [Can You Build Agent2Agent Communication on MCP? Yes! - Microsoft](https://developer.microsoft.com/blog/can-you-build-agent2agent-communication-on-mcp-yes)
- [Open Protocols for Agent Interoperability - AWS](https://aws.amazon.com/blogs/opensource/open-protocols-for-agent-interoperability-part-1-inter-agent-communication-on-mcp/)
- [A Survey of Agent Interoperability Protocols](https://arxiv.org/html/2505.02279v1)

### LangGraph
- [LangGraph Multi-Agent Orchestration Guide](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langgraph-multi-agent-orchestration/langgraph-multi-agent-orchestration-complete-framework-guide-architecture-analysis-2025)
- [LangGraph & Redis: Build Smarter AI Agents](https://redis.io/blog/langgraph-redis-build-smarter-ai-agents-with-memory-persistence/)
- [LangGraph Multi-Agent Workflows](https://blog.langchain.com/langgraph-multi-agent-workflows/)
- [langgraph-checkpoint-redis](https://github.com/redis-developer/langgraph-redis)

### Event Sourcing & CQRS
- [Event Sourcing Pattern - Microservices.io](https://microservices.io/patterns/data/event-sourcing.html)
- [What is CQRS in Event Sourcing Patterns? - Confluent](https://developer.confluent.io/courses/event-sourcing/cqrs/)
- [Understanding Event Sourcing and CQRS Pattern - Mia Platform](https://mia-platform.eu/blog/understanding-event-sourcing-and-cqrs-pattern/)
- [Cloud-Native App Design: CQRS, Event Sourcing, Messaging - Akka](https://akka.io/blog/cloud-native-app-design-techniques-cqrs-event-sourcing-messaging)

### Actor Model (Ray / Dapr)
- [Ray: Your Gateway to Scalable AI - Analytics Vidhya](https://www.analyticsvidhya.com/blog/2025/03/ray/)
- [Multi-Agent Environments - Ray Documentation](https://docs.ray.io/en/latest/rllib/multi-agent-envs.html)
- [Top AI Agent Orchestration Frameworks 2025 - Kubiya](https://www.kubiya.ai/blog/ai-agent-orchestration-frameworks)
- [Learn Agentic AI with Dapr - GitHub](https://github.com/panaversity/learn-agentic-ai)

### Multi-Agent Orchestration Patterns
- [Four Design Patterns for Event-Driven, Multi-Agent Systems - Confluent](https://www.confluent.io/blog/event-driven-multi-agent-systems/)
- [How Agent Handoffs Work in Multi-Agent Systems - Towards Data Science](https://towardsdatascience.com/how-agent-handoffs-work-in-multi-agent-systems/)
- [Multi-Agent Systems: Architecture, Patterns, and Production Design - Comet](https://www.comet.com/site/blog/multi-agent-systems/)
- [Multi-Agent and Multi-LLM Architecture Guide 2025 - Collabnix](https://collabnix.com/multi-agent-and-multi-llm-architecture-complete-guide-for-2025/)
- [Saga Pattern: Orchestration vs Choreography - ByteByteGo](https://blog.bytebytego.com/p/saga-pattern-demystified-orchestration)

### Claude Agent SDK
- [Agent SDK Overview - Claude Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)

---

*Document version: 2.0.0*
*Last updated: 2026-01-08*
*Patterns evaluated: 9*
