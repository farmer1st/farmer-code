# A2A Protocol Proposal for Farmer Code

This document explores adopting Google's [Agent2Agent (A2A) Protocol](https://a2a-protocol.org) for agent delegation in Farmer Code. The goal is to comprehensively map our use cases to A2A patterns and identify any issues or gaps before implementation.

> **Approach**: We will work through each use case in detail, designing the A2A implementation, and flag any problems we encounter along the way.

## Why A2A?

### Current Pain Points

1. **Tight coupling** - Agent Hub hardcodes agent URLs and routing logic
2. **No standard discovery** - Adding a new agent requires code changes
3. **Limited async** - Long-running tasks block the caller
4. **Custom persistence** - Each service manages its own conversation storage
5. **No federation** - Cannot delegate to agents outside our system

### What A2A Offers

| Capability | How A2A Addresses It |
|------------|---------------------|
| **Agent Discovery** | Agent Cards describe capabilities; clients discover dynamically |
| **Task Lifecycle** | Built-in state machine (submitted → working → completed/failed) |
| **Long-Running Tasks** | SSE streaming + push notifications for hours/days-long tasks |
| **Conversation Context** | Messages passed within task; history preserved |
| **Standard Protocol** | Linux Foundation backed, 150+ organizations, language-agnostic |

### Key Constraint

**Claude Agent SDK remains our agent runtime.** A2A is the communication layer between agents, not a replacement for how agents think and act.

```
┌─────────────────────────────────────────────────────────────────┐
│                    A2A Protocol Layer                            │
│              (discovery, task delegation, streaming)             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │    Baron     │    │     Duc      │    │    Marie     │
    │  A2A Server  │    │  A2A Server  │    │  A2A Server  │
    │      +       │    │      +       │    │      +       │
    │  Claude SDK  │    │  Claude SDK  │    │  Claude SDK  │
    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## Use Cases to Explore

### UC-1: Agent Discovery and Capability Advertisement

**Scenario**: Orchestrator needs to find which agent can handle "architecture review" without hardcoding.

**Current approach**: Static routing table in `router.py`

**A2A approach**: Each agent publishes an Agent Card

---

### UC-2: Simple Request-Response (Synchronous)

**Scenario**: Baron asks Duc for a quick architecture opinion (< 30 seconds)

**Current approach**: HTTP POST to `/invoke/duc`

**A2A approach**: `message/send` with immediate response

---

### UC-3: Long-Running Task with Progress Updates

**Scenario**: Baron creates a comprehensive spec (5-10 minutes), needs to stream progress

**Current approach**: Single blocking HTTP call, client waits

**A2A approach**: `message/stream` with SSE events

---

### UC-4: Human-in-the-Loop Escalation

**Scenario**: Agent is uncertain, needs human input before continuing

**Current approach**: Create Escalation record, post to GitHub, poll for response

**A2A approach**: Task enters `input-required` state, waits for human message

---

### UC-5: Multi-Turn Conversation

**Scenario**: Baron and Duc have a back-and-forth discussion about architecture

**Current approach**: Session with message history in SQLite

**A2A approach**: Task with conversation history in messages

---

### UC-6: Conversation Persistence for Training

**Scenario**: All agent exchanges must be captured for later training/fine-tuning

**Current approach**: JSONL logs + SQLite tables

**A2A approach**: Task history + artifacts contain full conversation

---

### UC-7: Agent-to-Agent Delegation Chain

**Scenario**: Baron delegates to Duc, who then delegates to Marie

**Current approach**: Nested HTTP calls, manual correlation

**A2A approach**: Chained tasks with parent-child relationship

---

### UC-8: Disconnection and Recovery

**Scenario**: Network blip during long-running task

**Current approach**: Request fails, must retry from scratch

**A2A approach**: `tasks/resubscribe` to resume stream

---

### UC-9: Parallel Agent Consultation

**Scenario**: Baron asks Duc and Marie simultaneously, aggregates responses

**Current approach**: asyncio.gather with HTTP calls

**A2A approach**: Multiple concurrent tasks

---

### UC-10: External Agent Federation

**Scenario**: Future - delegate to agents outside Farmer Code (partner systems)

**Current approach**: Not supported

**A2A approach**: Standard protocol enables cross-system delegation

---

## Detailed Design Per Use Case

### UC-1: Agent Discovery and Capability Advertisement

#### Agent Card Design

Each agent exposes an Agent Card at `/.well-known/agent.json`:

**Baron's Agent Card:**
```json
{
  "name": "baron",
  "description": "PM Agent - Creates specifications, plans, and task lists for features",
  "url": "http://localhost:8002",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "skills": [
    {
      "id": "specify",
      "name": "Create Specification",
      "description": "Generate a comprehensive feature specification from a natural language description",
      "tags": ["planning", "specification", "pm"],
      "inputModes": ["text"],
      "outputModes": ["text", "file"],
      "examples": [
        {
          "input": "Add user authentication with OAuth2",
          "output": "spec.md with user stories, acceptance criteria, and constraints"
        }
      ]
    },
    {
      "id": "plan",
      "name": "Create Implementation Plan",
      "description": "Generate a detailed implementation plan from a specification",
      "tags": ["planning", "architecture", "pm"],
      "inputModes": ["text", "file"],
      "outputModes": ["text", "file"]
    },
    {
      "id": "tasks",
      "name": "Generate Task List",
      "description": "Create an ordered, dependency-aware task list from a plan",
      "tags": ["planning", "tasks", "pm"],
      "inputModes": ["text", "file"],
      "outputModes": ["text", "file"]
    }
  ],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"]
}
```

**Duc's Agent Card:**
```json
{
  "name": "duc",
  "description": "Architecture Expert - Reviews system design and API contracts",
  "url": "http://localhost:8003",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "architecture_review",
      "name": "Architecture Review",
      "description": "Review system architecture for scalability, maintainability, and best practices",
      "tags": ["architecture", "review", "expert"]
    },
    {
      "id": "api_design",
      "name": "API Design",
      "description": "Design RESTful APIs following OpenAPI standards",
      "tags": ["api", "design", "expert"]
    },
    {
      "id": "data_model",
      "name": "Data Model Review",
      "description": "Review and suggest improvements to data models",
      "tags": ["database", "model", "expert"]
    }
  ]
}
```

**Marie's Agent Card:**
```json
{
  "name": "marie",
  "description": "Testing Expert - Designs test strategies and reviews test coverage",
  "url": "http://localhost:8004",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "test_strategy",
      "name": "Test Strategy",
      "description": "Design comprehensive test strategy for a feature",
      "tags": ["testing", "qa", "expert"]
    },
    {
      "id": "edge_cases",
      "name": "Edge Case Analysis",
      "description": "Identify edge cases and failure modes",
      "tags": ["testing", "edge-cases", "expert"]
    },
    {
      "id": "test_review",
      "name": "Test Review",
      "description": "Review existing tests for coverage and quality",
      "tags": ["testing", "review", "expert"]
    }
  ]
}
```

#### Discovery Flow

```
Orchestrator                              Agent Registry (or direct)
    │                                              │
    │  GET /.well-known/agent.json                │
    │─────────────────────────────────────────────►│ Baron
    │◄─────────────────────────────────────────────│
    │  (Agent Card)                                │
    │                                              │
    │  GET /.well-known/agent.json                │
    │─────────────────────────────────────────────►│ Duc
    │◄─────────────────────────────────────────────│
    │                                              │
    │  GET /.well-known/agent.json                │
    │─────────────────────────────────────────────►│ Marie
    │◄─────────────────────────────────────────────│
    │                                              │
    │  [Cache cards, match skills to requests]     │
```

#### Implementation

```python
from dataclasses import dataclass
import httpx

@dataclass
class AgentCard:
    name: str
    description: str
    url: str
    skills: list[dict]
    capabilities: dict

class A2AAgentRegistry:
    """Discovers and caches agent capabilities."""

    def __init__(self):
        self.agents: dict[str, AgentCard] = {}
        self.skill_index: dict[str, list[str]] = {}  # skill_id -> [agent_names]

    async def discover(self, agent_url: str) -> AgentCard:
        """Fetch Agent Card from agent."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{agent_url}/.well-known/agent.json")
            data = response.json()

            card = AgentCard(
                name=data["name"],
                description=data["description"],
                url=data["url"],
                skills=data["skills"],
                capabilities=data.get("capabilities", {})
            )

            self.agents[card.name] = card

            # Index skills for lookup
            for skill in card.skills:
                skill_id = skill["id"]
                if skill_id not in self.skill_index:
                    self.skill_index[skill_id] = []
                self.skill_index[skill_id].append(card.name)

            return card

    def find_agent_for_skill(self, skill_id: str) -> AgentCard | None:
        """Find an agent that can handle a skill."""
        agent_names = self.skill_index.get(skill_id, [])
        if agent_names:
            return self.agents[agent_names[0]]
        return None

    def find_agents_by_tag(self, tag: str) -> list[AgentCard]:
        """Find all agents with skills matching a tag."""
        results = []
        for agent in self.agents.values():
            for skill in agent.skills:
                if tag in skill.get("tags", []):
                    results.append(agent)
                    break
        return results
```

#### Potential Issues

| Issue | Severity | Mitigation |
|-------|----------|------------|
| Agent Card caching/staleness | Low | TTL-based refresh, version field |
| No central registry | Medium | Could add lightweight registry service |
| Skill ID collisions | Low | Namespace: `baron.specify`, `duc.architecture_review` |

---

### UC-2: Simple Request-Response (Synchronous)

#### Scenario

Baron needs a quick architecture opinion from Duc:

```
Baron: "Is REST or GraphQL better for this mobile API?"
Duc: "REST - simpler for your use case, better caching..."
```

#### A2A Flow

```
Baron (A2A Client)                        Duc (A2A Server)
    │                                              │
    │  POST /a2a                                   │
    │  {                                           │
    │    "jsonrpc": "2.0",                         │
    │    "method": "message/send",                 │
    │    "params": {                               │
    │      "message": {                            │
    │        "role": "user",                       │
    │        "parts": [{                           │
    │          "type": "text",                     │
    │          "text": "Is REST or GraphQL..."    │
    │        }]                                    │
    │      }                                       │
    │    },                                        │
    │    "id": "req-1"                             │
    │  }                                           │
    │─────────────────────────────────────────────►│
    │                                              │
    │  HTTP 200                                    │
    │  {                                           │
    │    "jsonrpc": "2.0",                         │
    │    "result": {                               │
    │      "task": {                               │
    │        "id": "task-abc",                     │
    │        "status": "completed",                │
    │        "messages": [                         │
    │          {"role": "user", ...},              │
    │          {"role": "agent", "parts": [{       │
    │            "text": "REST - simpler..."       │
    │          }]}                                 │
    │        ]                                     │
    │      }                                       │
    │    },                                        │
    │    "id": "req-1"                             │
    │  }                                           │
    │◄─────────────────────────────────────────────│
```

#### Implementation

**Baron as A2A Client:**
```python
class A2AClient:
    """Client for making A2A requests to other agents."""

    def __init__(self, registry: A2AAgentRegistry):
        self.registry = registry

    async def send_message(
        self,
        agent_name: str,
        message: str,
        skill_id: str | None = None
    ) -> dict:
        """Send a message and wait for response (synchronous pattern)."""
        agent = self.registry.agents[agent_name]

        request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": message}]
                }
            },
            "id": str(uuid4())
        }

        if skill_id:
            request["params"]["skill"] = skill_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{agent.url}/a2a",
                json=request,
                timeout=60.0  # Short timeout for sync requests
            )
            return response.json()["result"]["task"]
```

**Duc as A2A Server:**
```python
from fastapi import FastAPI, Request
from claude_agent_sdk import ClaudeSDKClient

app = FastAPI()

@app.post("/a2a")
async def handle_a2a(request: Request):
    """A2A JSON-RPC endpoint."""
    body = await request.json()
    method = body["method"]

    if method == "message/send":
        return await handle_message_send(body)
    # ... other methods

async def handle_message_send(body: dict) -> dict:
    """Handle synchronous message/send."""
    message = body["params"]["message"]
    user_text = message["parts"][0]["text"]

    # Invoke Claude SDK
    sdk = ClaudeSDKClient()
    result = await sdk.query(
        prompt=user_text,
        system="You are Duc, an architecture expert..."
    )

    # Build A2A response
    task = {
        "id": str(uuid4()),
        "status": "completed",
        "messages": [
            message,  # Echo user message
            {
                "role": "agent",
                "parts": [{"type": "text", "text": result.output}]
            }
        ]
    }

    return {
        "jsonrpc": "2.0",
        "result": {"task": task},
        "id": body["id"]
    }
```

#### Potential Issues

| Issue | Severity | Mitigation |
|-------|----------|------------|
| Timeout for "simple" requests | Medium | Skill metadata could include expected duration |
| No streaming for unexpectedly long responses | Medium | Client could use `message/stream` by default |

---

### UC-3: Long-Running Task with Progress Updates

#### Scenario

Baron creates a comprehensive specification (5-10 minutes). The client needs progress updates.

#### A2A Flow with SSE Streaming

```
Orchestrator (Client)                     Baron (A2A Server)
    │                                              │
    │  POST /a2a                                   │
    │  Accept: text/event-stream                   │
    │  {                                           │
    │    "method": "message/stream",               │
    │    "params": {                               │
    │      "message": {...},                       │
    │      "skill": "specify"                      │
    │    }                                         │
    │  }                                           │
    │─────────────────────────────────────────────►│
    │                                              │
    │  HTTP 200                                    │
    │  Content-Type: text/event-stream             │
    │                                              │
    │  event: task                                 │
    │  data: {"task": {"id": "t1", "status": "submitted"}}
    │◄─────────────────────────────────────────────│
    │                                              │
    │  event: status                               │
    │  data: {"status": "working", "message":      │
    │         "Analyzing feature description..."}  │
    │◄─────────────────────────────────────────────│
    │                                              │
    │  event: status                               │
    │  data: {"status": "working", "message":      │
    │         "Consulting Duc for architecture..."} │
    │◄─────────────────────────────────────────────│
    │                                              │
    │  event: artifact                             │
    │  data: {"artifact": {"name": "spec.md",      │
    │         "parts": [{"text": "# Spec..."}]},   │
    │         "append": false, "lastChunk": true}  │
    │◄─────────────────────────────────────────────│
    │                                              │
    │  event: status                               │
    │  data: {"status": "completed", "final": true}│
    │◄─────────────────────────────────────────────│
    │                                              │
    │  [Connection closes]                         │
```

#### Implementation

**Baron A2A Server with Streaming:**
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
import json

@app.post("/a2a")
async def handle_a2a(request: Request):
    body = await request.json()
    method = body["method"]

    if method == "message/stream":
        return StreamingResponse(
            stream_specify(body),
            media_type="text/event-stream"
        )

async def stream_specify(body: dict):
    """Stream specification creation with progress updates."""
    task_id = str(uuid4())
    message = body["params"]["message"]
    feature_description = message["parts"][0]["text"]

    # Send initial task
    yield format_sse("task", {
        "task": {
            "id": task_id,
            "status": "submitted",
            "messages": [message]
        }
    })

    # Phase 1: Analyze
    yield format_sse("status", {
        "type": "TaskStatusUpdateEvent",
        "taskId": task_id,
        "status": "working",
        "message": {
            "role": "agent",
            "parts": [{"text": "Analyzing feature description..."}]
        },
        "final": False
    })

    # Actually do the work with Claude SDK
    sdk = ClaudeSDKClient()

    # Phase 2: Consult experts (this is where Baron might call Duc)
    yield format_sse("status", {
        "type": "TaskStatusUpdateEvent",
        "taskId": task_id,
        "status": "working",
        "message": {
            "role": "agent",
            "parts": [{"text": "Consulting architecture expert..."}]
        },
        "final": False
    })

    # Baron invokes Claude SDK to create spec
    result = await sdk.query(
        prompt=f"Create a specification for: {feature_description}",
        system="You are Baron, a PM agent..."
    )

    # Phase 3: Send artifact
    yield format_sse("artifact", {
        "type": "TaskArtifactUpdateEvent",
        "taskId": task_id,
        "artifact": {
            "name": "spec.md",
            "mimeType": "text/markdown",
            "parts": [{"type": "text", "text": result.output}]
        },
        "append": False,
        "lastChunk": True
    })

    # Phase 4: Complete
    yield format_sse("status", {
        "type": "TaskStatusUpdateEvent",
        "taskId": task_id,
        "status": "completed",
        "final": True
    })

def format_sse(event: str, data: dict) -> str:
    """Format as Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
```

**Client consuming stream:**
```python
async def stream_task(agent_url: str, message: str, skill: str):
    """Stream a long-running task."""
    request = {
        "jsonrpc": "2.0",
        "method": "message/stream",
        "params": {
            "message": {"role": "user", "parts": [{"type": "text", "text": message}]},
            "skill": skill
        },
        "id": str(uuid4())
    }

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{agent_url}/a2a",
            json=request,
            headers={"Accept": "text/event-stream"}
        ) as response:
            task = None
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])

                    if "task" in data:
                        task = data["task"]
                        print(f"Task started: {task['id']}")

                    elif data.get("type") == "TaskStatusUpdateEvent":
                        print(f"Status: {data['status']}")
                        if msg := data.get("message"):
                            print(f"  {msg['parts'][0]['text']}")

                        if data.get("final"):
                            break

                    elif data.get("type") == "TaskArtifactUpdateEvent":
                        artifact = data["artifact"]
                        print(f"Artifact: {artifact['name']}")

            return task
```

#### Potential Issues

| Issue | Severity | Mitigation |
|-------|----------|------------|
| SSE connection timeout | High | Periodic heartbeat events |
| Large artifacts | Medium | Chunk with `append: true` |
| Client disconnect during processing | Medium | Task continues, use `tasks/get` to retrieve |

---

### UC-4: Human-in-the-Loop Escalation

#### Scenario

Baron is uncertain about a requirement and needs human clarification before continuing.

#### A2A Task State: `input-required`

```
Orchestrator                              Baron
    │                                        │
    │  message/stream (create spec)          │
    │───────────────────────────────────────►│
    │                                        │
    │  TaskStatusUpdateEvent                 │
    │  status: "working"                     │
    │◄───────────────────────────────────────│
    │                                        │
    │  TaskStatusUpdateEvent                 │
    │  status: "input-required"              │
    │  message: "Should auth use OAuth2      │
    │           or SAML? Need clarification" │
    │◄───────────────────────────────────────│
    │                                        │
    │  [Stream pauses, waiting for input]    │
    │                                        │
    │  ... Human provides answer via UI ...  │
    │                                        │
    │  message/send (same task_id)           │
    │  message: "Use OAuth2 with Google"     │
    │───────────────────────────────────────►│
    │                                        │
    │  TaskStatusUpdateEvent                 │
    │  status: "working"                     │
    │◄───────────────────────────────────────│
    │                                        │
    │  TaskStatusUpdateEvent                 │
    │  status: "completed"                   │
    │◄───────────────────────────────────────│
```

#### Implementation

**Baron detecting uncertainty and requesting input:**
```python
async def stream_specify_with_escalation(body: dict):
    """Specification with potential human escalation."""
    task_id = str(uuid4())
    message = body["params"]["message"]
    feature_description = message["parts"][0]["text"]

    # Store task state for continuation
    task_store[task_id] = {
        "status": "working",
        "messages": [message],
        "context": {"feature": feature_description}
    }

    yield format_sse("task", {"task": {"id": task_id, "status": "submitted"}})
    yield format_sse("status", {"status": "working", "final": False})

    # Analyze with Claude SDK
    sdk = ClaudeSDKClient()
    analysis = await sdk.query(
        prompt=f"Analyze this feature request. If anything is ambiguous, say NEED_CLARIFICATION: <question>. Feature: {feature_description}"
    )

    if "NEED_CLARIFICATION:" in analysis.output:
        # Extract the question
        question = analysis.output.split("NEED_CLARIFICATION:")[1].strip()

        # Update task state
        task_store[task_id]["status"] = "input-required"
        task_store[task_id]["pending_question"] = question

        # Signal to client that human input is needed
        yield format_sse("status", {
            "type": "TaskStatusUpdateEvent",
            "taskId": task_id,
            "status": "input-required",
            "message": {
                "role": "agent",
                "parts": [{"type": "text", "text": question}]
            },
            "final": False  # Task not complete, waiting for input
        })

        # Stream pauses here - client will send follow-up message
        return

    # No clarification needed, continue to completion
    # ... generate spec ...
```

**Continuing task after human input:**
```python
@app.post("/a2a")
async def handle_a2a(request: Request):
    body = await request.json()
    method = body["method"]
    params = body["params"]

    # Check if this is a continuation of an existing task
    if "taskId" in params:
        task_id = params["taskId"]
        if task_id in task_store:
            return await continue_task(task_id, body)

    # ... handle new tasks ...

async def continue_task(task_id: str, body: dict):
    """Continue a paused task with new input."""
    task = task_store[task_id]
    new_message = body["params"]["message"]

    # Add human's response to conversation
    task["messages"].append(new_message)
    human_answer = new_message["parts"][0]["text"]

    # Resume with the new context
    return StreamingResponse(
        resume_specify(task_id, human_answer),
        media_type="text/event-stream"
    )

async def resume_specify(task_id: str, human_answer: str):
    """Resume specification after human input."""
    task = task_store[task_id]

    yield format_sse("status", {
        "status": "working",
        "message": {"role": "agent", "parts": [{"text": "Resuming with clarification..."}]},
        "final": False
    })

    # Continue spec generation with the clarification
    sdk = ClaudeSDKClient()
    result = await sdk.query(
        prompt=f"""
        Feature: {task['context']['feature']}
        Clarification: {human_answer}

        Now create the complete specification.
        """
    )

    yield format_sse("artifact", {
        "artifact": {"name": "spec.md", "parts": [{"text": result.output}]},
        "lastChunk": True
    })

    yield format_sse("status", {"status": "completed", "final": True})

    # Cleanup
    del task_store[task_id]
```

#### Potential Issues

| Issue | Severity | Mitigation |
|-------|----------|------------|
| Task state persistence | High | Need durable storage (Redis/DB) |
| Long wait for human | High | Push notifications + webhooks |
| Multiple clarification rounds | Medium | Support iterative input-required states |
| Task expiration | Medium | TTL with cleanup, notify before expiry |

---

### UC-5: Multi-Turn Conversation

#### Scenario

Baron and Duc have a back-and-forth discussion about architecture choices.

#### A2A Conversation Model

All messages within a task form the conversation history:

```python
task = {
    "id": "task-123",
    "status": "completed",
    "messages": [
        # Turn 1: Baron asks
        {
            "role": "user",
            "parts": [{"text": "Should we use microservices or monolith?"}]
        },
        # Turn 1: Duc responds
        {
            "role": "agent",
            "parts": [{"text": "For your scale, I'd recommend starting with a modular monolith..."}]
        },
        # Turn 2: Baron follows up
        {
            "role": "user",
            "parts": [{"text": "What about if we need to scale the auth service independently?"}]
        },
        # Turn 2: Duc responds
        {
            "role": "agent",
            "parts": [{"text": "Good point. You could extract auth as a separate service later..."}]
        }
    ]
}
```

#### Implementation

**Multi-turn client:**
```python
class A2AConversation:
    """Manages a multi-turn conversation with an agent."""

    def __init__(self, client: A2AClient, agent_name: str):
        self.client = client
        self.agent_name = agent_name
        self.task_id: str | None = None
        self.messages: list[dict] = []

    async def send(self, message: str) -> str:
        """Send a message and get response, maintaining conversation."""
        user_message = {
            "role": "user",
            "parts": [{"type": "text", "text": message}]
        }
        self.messages.append(user_message)

        agent = self.client.registry.agents[self.agent_name]

        request = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": user_message,
                "history": self.messages[:-1]  # Previous messages as context
            },
            "id": str(uuid4())
        }

        if self.task_id:
            request["params"]["taskId"] = self.task_id

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{agent.url}/a2a", json=request)
            result = response.json()["result"]["task"]

        self.task_id = result["id"]

        # Extract agent's response
        agent_message = result["messages"][-1]
        self.messages.append(agent_message)

        return agent_message["parts"][0]["text"]

# Usage
conv = A2AConversation(client, "duc")
response1 = await conv.send("Should we use microservices or monolith?")
response2 = await conv.send("What about scaling auth independently?")
response3 = await conv.send("How would we handle the data migration?")
```

#### Potential Issues

| Issue | Severity | Mitigation |
|-------|----------|------------|
| Context window limits | High | Summarize older messages |
| History serialization overhead | Medium | Incremental history via taskId |
| Conversation branching | Low | Create new task for branches |

---

### UC-6: Conversation Persistence for Training

#### Scenario

All agent exchanges must be captured for later training and prompt improvement.

#### A2A Data Model for Training

Every task contains the full conversation + metadata:

```python
@dataclass
class TrainingExample:
    """Training example extracted from A2A task."""

    # Task metadata
    task_id: str
    agent_name: str
    skill_id: str
    status: str  # completed, failed, etc.

    # Conversation
    messages: list[dict]  # Full message history

    # Artifacts produced
    artifacts: list[dict]

    # Quality signals
    duration_ms: int
    required_human_input: bool
    escalation_count: int

    # For failed tasks
    error: str | None

    @classmethod
    def from_task(cls, task: dict, agent_name: str, skill_id: str) -> "TrainingExample":
        return cls(
            task_id=task["id"],
            agent_name=agent_name,
            skill_id=skill_id,
            status=task["status"],
            messages=task.get("messages", []),
            artifacts=task.get("artifacts", []),
            duration_ms=task.get("metadata", {}).get("duration_ms", 0),
            required_human_input="input-required" in task.get("history", {}).get("states", []),
            escalation_count=len([m for m in task.get("messages", []) if m.get("role") == "user"]) - 1,
            error=task.get("error")
        )
```

#### Persistence Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                    A2A Server (Baron)                            │
│                                                                  │
│  1. On task completion/failure                                   │
│  2. Serialize task to TrainingExample                            │
│  3. Persist to training store                                    │
└───────────────────────────────────┬─────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Training Data Store                           │
│                                                                  │
│  Option A: JSONL files (simple)                                  │
│  Option B: SQLite/PostgreSQL (queryable)                         │
│  Option C: Redis Streams (scalable)                              │
│  Option D: Cloud storage (S3/GCS) for batch training            │
└─────────────────────────────────────────────────────────────────┘
```

#### Implementation

**Training data capture middleware:**
```python
class TrainingDataCapture:
    """Middleware to capture all A2A tasks for training."""

    def __init__(self, store: TrainingStore):
        self.store = store

    async def on_task_complete(self, task: dict, agent_name: str, skill_id: str):
        """Called when any task completes."""
        example = TrainingExample.from_task(task, agent_name, skill_id)
        await self.store.save(example)

    async def on_task_failed(self, task: dict, agent_name: str, skill_id: str, error: str):
        """Called when any task fails - also valuable for training."""
        example = TrainingExample.from_task(task, agent_name, skill_id)
        example.error = error
        await self.store.save(example)

class JSONLTrainingStore:
    """Simple JSONL-based training store."""

    def __init__(self, path: Path):
        self.path = path

    async def save(self, example: TrainingExample):
        async with aiofiles.open(self.path, "a") as f:
            await f.write(json.dumps(asdict(example)) + "\n")

    async def export_for_training(self, filter_fn=None) -> list[dict]:
        """Export examples in format suitable for fine-tuning."""
        examples = []
        async with aiofiles.open(self.path) as f:
            async for line in f:
                example = json.loads(line)
                if filter_fn is None or filter_fn(example):
                    examples.append({
                        "messages": example["messages"],
                        "metadata": {
                            "agent": example["agent_name"],
                            "skill": example["skill_id"],
                            "successful": example["status"] == "completed"
                        }
                    })
        return examples
```

#### What Gets Captured

| Data Point | Source | Training Value |
|------------|--------|----------------|
| User request | `messages[0]` | Input examples |
| Agent response | `messages[-1]` | Output examples |
| Conversation flow | `messages[*]` | Multi-turn patterns |
| Artifacts | `artifacts[*]` | Long-form output |
| Human corrections | `input-required` messages | Error correction |
| Failure cases | Failed tasks | What not to do |
| Timing | `duration_ms` | Complexity signal |

#### Potential Issues

| Issue | Severity | Mitigation |
|-------|----------|------------|
| PII in training data | High | Scrubbing pipeline before export |
| Storage growth | Medium | Retention policy, archival |
| Incomplete tasks | Low | Capture partial for debugging |

---

### UC-7: Agent-to-Agent Delegation Chain

#### Scenario

Baron delegates to Duc, who then delegates to Marie.

```
Orchestrator → Baron (specify)
                  └──→ Duc (architecture review)
                          └──→ Marie (test strategy)
```

#### A2A Nested Tasks

Each agent is both client and server:

```
Orchestrator                Baron                    Duc                     Marie
    │                          │                       │                        │
    │  message/stream          │                       │                        │
    │  skill: specify          │                       │                        │
    │─────────────────────────►│                       │                        │
    │                          │                       │                        │
    │  status: working         │                       │                        │
    │◄─────────────────────────│                       │                        │
    │                          │                       │                        │
    │                          │  message/send         │                        │
    │                          │  skill: arch_review   │                        │
    │                          │──────────────────────►│                        │
    │                          │                       │                        │
    │  status: working         │                       │  message/send          │
    │  "Consulting Duc..."     │                       │  skill: test_strategy  │
    │◄─────────────────────────│                       │───────────────────────►│
    │                          │                       │                        │
    │                          │                       │  completed             │
    │                          │                       │◄───────────────────────│
    │                          │                       │                        │
    │                          │  completed            │                        │
    │                          │◄──────────────────────│                        │
    │                          │                       │                        │
    │  artifact: spec.md       │                       │                        │
    │◄─────────────────────────│                       │                        │
    │                          │                       │                        │
    │  status: completed       │                       │                        │
    │◄─────────────────────────│                       │                        │
```

#### Implementation

**Baron calling Duc during specification:**
```python
class BaronAgent:
    """Baron agent that delegates to other agents."""

    def __init__(self):
        self.sdk = ClaudeSDKClient()
        self.a2a_client = A2AClient(registry)

    async def specify(self, feature: str) -> AsyncGenerator:
        """Create specification, consulting experts as needed."""
        task_id = str(uuid4())

        yield format_sse("task", {"task": {"id": task_id, "status": "submitted"}})
        yield format_sse("status", {"status": "working", "final": False})

        # Step 1: Initial analysis
        initial = await self.sdk.query(f"Analyze feature: {feature}")

        # Step 2: Consult Duc for architecture
        yield format_sse("status", {
            "status": "working",
            "message": {"role": "agent", "parts": [{"text": "Consulting architecture expert..."}]},
            "final": False
        })

        duc_response = await self.a2a_client.send_message(
            agent_name="duc",
            message=f"Review architecture approach for: {feature}\n\nInitial analysis: {initial.output}",
            skill_id="architecture_review"
        )

        # Step 3: Maybe Duc consulted Marie (we see it in duc_response)
        arch_feedback = duc_response["messages"][-1]["parts"][0]["text"]

        # Step 4: Generate final spec
        yield format_sse("status", {
            "status": "working",
            "message": {"role": "agent", "parts": [{"text": "Generating specification..."}]},
            "final": False
        })

        final_spec = await self.sdk.query(f"""
            Feature: {feature}
            Architecture feedback: {arch_feedback}

            Generate the complete specification.
        """)

        yield format_sse("artifact", {
            "artifact": {"name": "spec.md", "parts": [{"text": final_spec.output}]},
            "lastChunk": True
        })

        yield format_sse("status", {"status": "completed", "final": True})
```

#### Correlation and Tracing

**Problem**: How do we trace the full chain for debugging/training?

**Solution**: Pass correlation context:

```python
request = {
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
        "message": {...},
        "metadata": {
            "correlationId": "orch-task-123",  # Root task ID
            "parentTaskId": "baron-task-456",  # Immediate parent
            "traceId": "trace-789",            # Distributed trace ID
            "depth": 2                          # Delegation depth
        }
    }
}
```

#### Potential Issues

| Issue | Severity | Mitigation |
|-------|----------|------------|
| Delegation cycles | High | Max depth limit, cycle detection |
| Latency accumulation | Medium | Parallel delegation where possible |
| Error propagation | Medium | Clear error chain in response |
| Correlation tracking | Medium | Trace context propagation |

---

## Open Questions and Concerns

### Q1: Task State Durability

**Question**: A2A doesn't specify how to persist task state. If Baron crashes mid-task, what happens?

**Concern Level**: HIGH

**Options**:
1. In-memory only (lose state on crash)
2. Redis for task state
3. Combine with Temporal for durability

### Q2: Authentication Between Agents

**Question**: How do agents authenticate to each other?

**Concern Level**: MEDIUM (local dev) / HIGH (production)

**Options**:
1. Mutual TLS
2. JWT tokens in headers
3. A2A signed cards (v0.3 feature)

### Q3: Rate Limiting and Back-pressure

**Question**: What if Baron overwhelms Duc with requests?

**Concern Level**: MEDIUM

**Options**:
1. Agent Card declares rate limits
2. HTTP 429 with retry-after
3. Queue at client side

### Q4: Large Artifact Handling

**Question**: What if spec.md is 100KB+?

**Concern Level**: LOW-MEDIUM

**Options**:
1. Chunked artifacts (`append: true`)
2. Reference artifacts (store in blob storage, return URL)
3. Compression

### Q5: Observability

**Question**: How do we monitor A2A communication?

**Concern Level**: MEDIUM

**Options**:
1. OpenTelemetry tracing
2. Structured logging with correlation IDs
3. Dedicated A2A metrics (requests, latency, errors per skill)

---

## Next Steps

1. **Prototype UC-1 and UC-2** - Basic discovery and sync request
2. **Add UC-3** - Streaming for long tasks
3. **Implement UC-4** - Human escalation flow
4. **Add UC-6** - Training data capture
5. **Test UC-8** - Disconnection handling
6. **Evaluate concerns** - Identify blockers

---

## References

- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [A2A Streaming & Async](https://a2a-protocol.org/latest/topics/streaming-and-async/)
- [A2A Python SDK](https://github.com/a2aproject/a2a-python)
- [Google ADK A2A Documentation](https://google.github.io/adk-docs/a2a/)

---

*Document version: 1.0.0*
*Last updated: 2026-01-08*

