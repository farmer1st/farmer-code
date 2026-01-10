# Farmer1st Agent Platform Proposal

**Version:** 0.1.0-draft
**Status:** R&D Discussion
**Last Updated:** 2026-01-10

> This document describes the **Agent Platform** — reusable AI agents that can be deployed
> in different contexts (Chat Portal, Farmer Code, future apps). For the Farmer Code
> workflow system specifically, see [fc-proposal.md](./fc-proposal.md).

## Executive Summary

The Agent Platform provides:

- **Reusable agent definitions** stored in Git (prompts, KB, skills, MCP configs)
- **A2A REST API** for agent-to-agent and app-to-agent communication
- **Two deployment modes**: Permanent (Chat Portal) and Ephemeral (Farmer Code)
- **Human escalation** with confidence-based routing to humans
- **SDK abstraction** allowing provider swaps (Claude → OpenAI → local)

**Key principle:** Agents are independent, reusable units — not tied to any single application.

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Agent Communication (A2A REST)](#2-agent-communication-a2a-rest)
3. [Human Escalation](#3-human-escalation)
4. [Deployment Modes](#4-deployment-modes)
5. [Chat Portal](#5-chat-portal)
6. [Future Agents](#6-future-agents)

---

## 1. Agent Architecture

### 1.1 Agent Definitions Repository

All agent definitions live in a single monorepo (`farmer1st-ai-agents`):

```
farmer1st-ai-agents/
├── agents/
│   │
│   │  # SDLC Agents (used by Farmer Code)
│   ├── baron/                   # PM - specify, plan, tasks
│   │   ├── agent-card.json      # A2A agent card
│   │   ├── config.yaml          # Runtime configuration
│   │   ├── prompt.md            # System prompt
│   │   ├── bio.md               # Agent persona
│   │   ├── knowledge/           # KB files
│   │   │   ├── 01-workflow.md
│   │   │   └── 02-best-practices.md
│   │   ├── skills/              # Skill definitions
│   │   ├── mcp/                 # MCP server configs
│   │   └── scripts/             # Custom scripts
│   ├── marie/                   # QA - test design, verification
│   ├── dede/                    # Backend developer
│   ├── dali/                    # Frontend developer
│   ├── gus/                     # DevOps - infrastructure
│   ├── vauban/                  # Release engineer - staging/prod
│   ├── victor/                  # Docs QA
│   ├── general/                 # Code reviewer
│   ├── socrate/                 # Retro analyst
│   │
│   │  # Product & Strategy Agents
│   ├── veuve/                   # Product Owner - features, roadmap
│   ├── duc/                     # Tech Owner - architecture, tech debt
│   │
│   │  # Future Agents (Chat Portal)
│   ├── hr-assistant/            # HR questions, policies
│   ├── finops/                  # Cost analysis, budgets
│   ├── security/                # Security reviews, compliance
│   │
│   │  # Human Bridges (deterministic, not AI)
│   ├── human-product/           # Bridge to product human
│   └── human-tech/              # Bridge to technical human
│
└── shared/
    └── prompts/                 # Shared prompt fragments
```

### 1.2 Agent Configuration

**config.yaml:**

```yaml
# agents/baron/config.yaml
name: baron
display_name: "Baron - PM Agent"
domain: product
port: 8002

escalation:
  enabled: true
  target: human-product
  confidence_threshold: 80

skills:
  - specify.feature
  - specify.plan
  - specify.tasks

allowed_tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep

mcp_servers:
  - github-tools
  - speckit-tools
```

### 1.3 Agent Card (A2A Standard)

Each agent publishes an agent card at `/.well-known/agent.json`:

```json
{
  "name": "baron",
  "description": "PM Agent - Creates specifications, plans, and task lists",
  "url": "http://baron:8002",
  "version": "2.1.0",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "specify.feature",
      "name": "Create Feature Specification",
      "description": "Generate a feature specification from a natural language description",
      "tags": ["specification", "planning"],
      "inputModes": ["text"],
      "outputModes": ["text", "file"]
    }
  ],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"]
}
```

### 1.4 Versioning Strategy

**Per-agent semantic versioning with Git tags:**

```
baron@1.0.0
baron@1.1.0
baron@2.0.0
duc@1.0.0
marie@1.2.0
```

**Tag discovery:**

```python
def get_agent_versions(agent_name: str, limit: int = 5) -> list[str]:
    """Fetch last N versions for an agent from GitHub tags."""
    tags = github.list_tags(pattern=f"{agent_name}@*")
    return sorted(tags, key=semver_key, reverse=True)[:limit]
```

### 1.5 SDK Abstraction Layer

We use the **Claude Agent SDK** with OAuth authentication (no API keys):

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
    permission_mode="acceptEdits",
    system_prompt=AGENT_SYSTEM_PROMPT,
    cwd="/path/to/workspace",
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Your prompt here")
    async for message in client.receive_response():
        # Process response...
```

**Provider abstraction for future:**

```python
class AgentRuntime(ABC):
    """Abstract base for agent runtimes."""

    @abstractmethod
    async def invoke(self, prompt: str, context: dict) -> AgentResponse:
        pass

class ClaudeAgentRuntime(AgentRuntime):
    """Claude Agent SDK implementation."""
    pass

class OpenAIRuntime(AgentRuntime):
    """Future: OpenAI implementation."""
    pass
```

---

## 2. Agent Communication (A2A REST)

We implement the [Google A2A Protocol](https://github.com/google/A2A) using the **REST binding**
for simplicity.

### 2.1 REST Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/agent.json` | GET | Agent discovery (A2A standard) |
| `/jobs` | POST | Create a new job |
| `/jobs/{job_id}` | GET | Poll job status |
| `/jobs/{job_id}` | DELETE | Cancel a running job |
| `/health` | GET | Liveness/readiness probe |

### 2.2 Request/Response Flow

```
┌──────────────┐                                           ┌──────────────┐
│              │  POST /jobs                               │              │
│   Caller     │ ──────────────────────────────────────────▶│    Agent     │
│              │  {task, context}                          │              │
│              │                                           │              │
│              │  201 Created                              │              │
│              │ ◀──────────────────────────────────────────│              │
│              │  {job_id: "job-abc123"}                   │              │
│              │                                           │              │
│              │  GET /jobs/job-abc123                     │              │
│              │ ──────────────────────────────────────────▶│              │
│              │                                           │              │
│              │  200 OK                                   │              │
│              │ ◀──────────────────────────────────────────│              │
│              │  {status: "completed", result: {...}}     │              │
└──────────────┘                                           └──────────────┘
```

### 2.3 Job Lifecycle

| Status | Description |
|--------|-------------|
| `pending` | Job received, queued |
| `working` | Agent actively processing |
| `completed` | Finished successfully |
| `failed` | Error occurred |
| `canceled` | Job was canceled |

### 2.4 Schemas

```python
class CreateJobRequest(BaseModel):
    task: str                     # What to do
    context: dict                 # Task-specific context
    session_id: str | None        # For conversation continuity

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: dict | None           # Present when completed
    error: str | None             # Present when failed
    started_at: datetime
    completed_at: datetime | None
```

### 2.5 Service Discovery

Within Kubernetes, agents use simple DNS names:

| Context | URL Pattern |
|---------|-------------|
| Same namespace | `http://{agent}:{port}` |
| Cross-namespace | `http://{agent}.{namespace}.svc:{port}` |

---

## 3. Human Escalation

### 3.1 Confidence-Based Escalation

When an agent's confidence drops below threshold (default 80%), it escalates to a human:

```python
class AgentRuntime:
    async def maybe_escalate(
        self,
        question: str,
        confidence: int,
        context: dict
    ) -> EscalationResult:
        if not self.escalation_enabled:
            return EscalationResult(escalated=False)

        if confidence >= self.confidence_threshold:
            return EscalationResult(escalated=False)

        # Post to GitHub Issue
        comment_id = await github.post_comment(
            issue=context["issue_number"],
            body=f"/human: {question}\n\nConfidence: {confidence}%"
        )

        # Notify via Slack
        await slack.notify(f"Human input needed on #{context['issue_number']}")

        # Poll for response
        response = await self.poll_for_response(comment_id)

        return EscalationResult(escalated=True, human_response=response)
```

### 3.2 Escalation Flow

```
Agent has low confidence (65%)
    │
    ▼
Posts comment: "/human: Should auth use JWT or sessions?"
    │
    ▼
GitHub Action → Slack notification
    │
    ▼
Human replies: "/duc Use JWT for stateless auth"
    │
    ▼
Agent polls, sees /duc prefix, processes response
    │
    ▼
Continues with confidence: 100% (human-verified)
```

### 3.3 Escalation Modes

| Context | Escalation | Behavior |
|---------|------------|----------|
| Farmer Code workflow | Enabled | Low confidence → wait for human → timeout fails |
| Chat Portal | Disabled | Always answer, show confidence to user |

### 3.4 Human Bridges

`human-product` and `human-tech` are **not AI agents** — they're GitHub + Slack integrations
that route escalations to the appropriate humans.

---

## 4. Deployment Modes

Agents support two deployment modes using the **same container image**:

### 4.1 Permanent Mode (Chat Portal)

- Agents run in `ai-agents` namespace
- Always-on (`replicas: 1`)
- Shared across all users
- No escalation (human is present)
- No worktree needed

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: baron
  namespace: ai-agents
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: agent
          image: ghcr.io/farmer1st/agent-runtime:latest
          env:
            - name: AGENT_NAME
              value: baron
            - name: ESCALATION_ENABLED
              value: "false"
```

### 4.2 Ephemeral Mode (Farmer Code)

- Agents run in `fc-{issue-id}` namespace
- Scale-to-zero when idle
- One instance per issue
- Escalation enabled
- Worktree mounted

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: baron
  namespace: fc-issue-42
spec:
  replicas: 0  # Scaled up by orchestrator when needed
  template:
    spec:
      containers:
        - name: agent
          image: ghcr.io/farmer1st/agent-runtime:latest
          env:
            - name: AGENT_NAME
              value: baron
            - name: ESCALATION_ENABLED
              value: "true"
            - name: WORKTREE_PATH
              value: /volumes/worktrees/issue-42
            - name: ISSUE_ID
              value: issue-42
```

### 4.3 Configuration Differences

| Variable | Permanent | Ephemeral |
|----------|-----------|-----------|
| `ESCALATION_ENABLED` | `false` | `true` |
| `WORKTREE_PATH` | Not set | `/volumes/worktrees/{issue}` |
| `ISSUE_ID` | Not set | `{issue-id}` |
| Namespace | `ai-agents` | `fc-{issue-id}` |
| Lifecycle | Always running | Created/destroyed per issue |

---

## 5. Chat Portal

### 5.1 Purpose

The Chat Portal is a web application for direct human-agent interaction:

- **Backlog refinement**: Chat with Veuve to refine feature requests
- **Technical discussion**: Chat with Duc about architecture
- **KB management**: Update agent knowledge bases via conversation
- **Issue creation**: Help articulate bug reports or feature requests

### 5.2 Backlog Refinement Flow

```
Human: "I want users to be able to reset their passwords"
    │
    ▼
Chat Portal → Veuve (Product Owner)
    │
    ▼
Veuve: "Should this include email verification? SMS fallback?"
    │
    ▼
Human: "Yes email, no SMS for now"
    │
    ▼
Veuve creates/updates GitHub Issue with refined description
    │
    ▼
Human reviews, adds "READY" label when satisfied
    │
    ▼
Farmer Code workflow starts automatically
```

### 5.3 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chat Portal                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────────────────────────────┐ │
│  │   React UI   │      │        ai-agents namespace           │ │
│  │   (PWA)      │      │                                      │ │
│  └──────┬───────┘      │  ┌────────┐  ┌────────┐  ┌────────┐ │ │
│         │              │  │ Veuve  │  │  Duc   │  │  HR    │ │ │
│         ▼              │  │ :8002  │  │ :8003  │  │ :8004  │ │ │
│  ┌──────────────┐      │  └────────┘  └────────┘  └────────┘ │ │
│  │  Portal API  │─────▶│                                      │ │
│  │  (FastAPI)   │      │  All agents always running           │ │
│  └──────────────┘      │  No escalation (human is present)    │ │
│                        └──────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.4 Session Management

Chat Portal maintains conversation sessions per user:

```python
class ChatSession:
    user_id: str
    agent: str
    messages: list[Message]
    created_at: datetime
    last_activity: datetime

# Sessions stored in Redis for fast access
# Archived to Git for long-term storage
```

---

## 6. Future Agents

Beyond SDLC, the platform supports domain-specific agents:

| Agent | Domain | Use Cases |
|-------|--------|-----------|
| `hr-assistant` | HR | Policy questions, leave requests, onboarding |
| `finops` | Finance | Cost analysis, budget tracking, optimization |
| `security` | Security | Compliance checks, vulnerability triage |
| `support` | Customer | Ticket routing, FAQ, escalation |

These agents:
- Deploy in `ai-agents` namespace (permanent mode)
- Use the same A2A REST API
- Have their own KB and prompts in `farmer1st-ai-agents` repo
- Can be accessed via Chat Portal or integrated into other apps

---

## Appendix: Comparison with Farmer Code

| Aspect | Agent Platform | Farmer Code |
|--------|---------------|-------------|
| **Focus** | Reusable agent definitions | SDLC workflow orchestration |
| **Deployment** | Permanent or ephemeral | Ephemeral only |
| **Namespace** | `ai-agents` or `fc-*` | `fc-{issue-id}` |
| **Orchestration** | None (direct calls) | State machine with phases |
| **Persistence** | Redis + Git | Git journal + CRD |
| **Escalation** | Configurable | Always enabled |

See [fc-proposal.md](./fc-proposal.md) for Farmer Code specifics.
