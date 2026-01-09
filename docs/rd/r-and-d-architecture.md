# Farmer1st Architecture Proposal

**Version:** 0.3.18-draft
**Status:** R&D Discussion
**Last Updated:** 2026-01-09

## Executive Summary

This document proposes a unified architecture for the Farmer1st agent ecosystem, covering:

- **Farmer Code**: SDLC automation with AI agents (specify, plan, code, test, review)
- **Agent Platform**: Reusable agents across multiple applications
- **Future Chat Portal**: Direct human-agent interaction for KB management

Key design principles:

1. **Agents are independent, reusable units** - not tied to Farmer Code
2. **GitHub is the source of truth** - agent definitions, KB, prompts all in Git
3. **Local-first, cloud-ready** - same architecture runs on laptop or EKS
4. **SDK abstraction** - swap Claude for another provider without rewrites
5. **Human-in-the-loop** - confidence-based escalation with audit trail

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Agent Architecture](#2-agent-architecture)
3. [Farmer Code (SDLC App)](#3-farmer-code-sdlc-app)
4. [Kubernetes Infrastructure](#4-kubernetes-infrastructure)
5. [Agent Communication (A2A)](#5-agent-communication-a2a)
6. [Human Escalation](#6-human-escalation)
7. [GitHub Integration](#7-github-integration)
8. [Persistence (DynamoDB)](#8-persistence-dynamodb)
9. [Event Sourcing](#9-event-sourcing)
10. [Feedback Loops](#10-feedback-loops)
11. [Resilience Patterns](#11-resilience-patterns)
12. [Why Custom Workflow Engine](#12-why-custom-workflow-engine)
13. [Security](#13-security)
14. [Testing Strategy](#14-testing-strategy)
15. [CI/CD Pipeline](#15-cicd-pipeline)
16. [Observability](#16-observability)
17. [Future: Chat Portal](#17-future-chat-portal)
18. [Open Questions](#18-open-questions)

---

## 1. System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Farmer1st Platform                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│  │  Farmer Code    │     │  Chat Portal    │     │  Other Apps     │       │
│  │  (SDLC)         │     │  (Future)       │     │  (Future)       │       │
│  └────────┬────────┘     └────────┬────────┘     └────────┬────────┘       │
│           │                       │                       │                 │
│           └───────────────────────┼───────────────────────┘                 │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Agent Platform (Google A2A Protocol)              │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐ │   │
│  │   │  Baron  │  │   Duc   │  │  Marie  │  │  Dede   │  │ Reviewer │ │   │
│  │   │  (PM)   │  │ (Arch)  │  │  (QA)   │  │ (Code)  │  │ (Review) │ │   │
│  │   └─────────┘  └─────────┘  └─────────┘  └─────────┘  └──────────┘ │   │
│  │                                                                      │   │
│  │   Future agents (HR, FinOps, Security, DevOps) via Chat Portal       │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Infrastructure Layer                             │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  k3d (local) / EKS (cloud)  │  DynamoDB  │  GitHub  │  Slack        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Summary

| Component | Purpose | Technology |
|-----------|---------|------------|
| Farmer Code | SDLC automation (spec → code → test → review) | FastAPI, PWA |
| Agent Platform | Reusable AI agents with A2A communication | Python, Claude SDK |
| Agent Definitions | KB, prompts, MCP, skills per agent | GitHub monorepo |
| Operator | Kubernetes operator for issue lifecycle | Python (kopf) |
| Persistence | Workflow state, conversations, training data | DynamoDB |
| Observability | Metrics, traces, logs | OpenTelemetry, Grafana |

### 1.2 Monorepo Structure (Apps Built by Farmer Code)

**Foundational Decision**: Farmer Code builds **monorepo applications** containing all code, infrastructure, and deployment manifests in a single repository. This is non-negotiable for AI-first development.

**Why Monorepo?**

| Aspect | Benefit |
|--------|---------|
| AI reasoning | Agent sees entire codebase — atomic changes across services, apps, infra |
| Demo capability | Clone one repo, run `docker compose up` — full stack running |
| Atomic PRs | Single PR for feature: code + tests + infra + gitops |
| Simplified onboarding | One repo to clone, one set of patterns to learn |
| Refactoring | Rename/move across boundaries in single commit |

**Canonical Directory Structure:**

```
my-app/                                 # Single monorepo per application
│
├── apps/                               # Frontend applications
│   ├── web/                            # Main web PWA (React + Vite)
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   └── main.tsx
│   │   ├── public/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── Dockerfile
│   │
│   └── admin/                          # Admin portal (if needed)
│       └── ...
│
├── services/                           # Backend services (domain-organized)
│   │
│   ├── [domain]/                       # e.g., user-management, surveys, payments
│   │   ├── bff/                        # Backend-for-Frontend (optional, GraphQL)
│   │   │   ├── src/
│   │   │   │   ├── api/
│   │   │   │   ├── core/
│   │   │   │   └── main.py
│   │   │   ├── tests/
│   │   │   │   ├── unit/
│   │   │   │   ├── integration/
│   │   │   │   └── contract/
│   │   │   ├── Dockerfile
│   │   │   └── pyproject.toml
│   │   │
│   │   ├── auth-service/               # Domain services
│   │   │   ├── src/
│   │   │   ├── tests/
│   │   │   ├── Dockerfile
│   │   │   └── pyproject.toml
│   │   │
│   │   └── profile-service/
│   │       └── ...
│   │
│   ├── shared/                         # Cross-service shared code
│   │   ├── src/
│   │   │   ├── contracts/              # API contracts (Pydantic models)
│   │   │   ├── clients/                # Service clients
│   │   │   └── utils/
│   │   └── pyproject.toml
│   │
│   └── tests/                          # Cross-service tests
│       ├── e2e/
│       ├── integration/
│       └── contract/
│
├── packages/                           # Shared libraries
│   ├── shared-types/                   # Cross-language types
│   ├── api-clients/                    # Generated API clients
│   └── ui-components/                  # Shared React components (shadcn/ui)
│
├── platform/                           # Platform service configs
│   ├── supertokens/                    # Auth server config
│   ├── openfga/                        # Authorization model
│   └── temporal/                       # Workflow definitions (if used)
│
├── infra/                              # ALL infrastructure lives here
│   │
│   ├── terraform/                      # Infrastructure as Code
│   │   ├── modules/                    # Reusable modules
│   │   │   ├── vpc/
│   │   │   ├── eks/
│   │   │   ├── rds-postgresql/
│   │   │   ├── elasticache-redis/
│   │   │   └── s3-bucket/
│   │   │
│   │   └── environments/               # Environment-specific
│   │       ├── dev/
│   │       │   ├── main.tf
│   │       │   ├── variables.tf
│   │       │   └── terraform.tfvars
│   │       ├── staging/
│   │       └── prod/
│   │
│   ├── k8s/                            # GitOps manifests (Kustomize)
│   │   ├── base/                       # Base manifests (shared)
│   │   │   ├── [domain]/               # Per-domain services
│   │   │   │   ├── deployment.yaml
│   │   │   │   ├── service.yaml
│   │   │   │   └── kustomization.yaml
│   │   │   └── platform/               # Platform services
│   │   │
│   │   └── overlays/                   # Environment overlays
│   │       ├── local/                  # Local k3d
│   │       │   └── kustomization.yaml
│   │       ├── dev/                    # Dev cluster
│   │       │   ├── kustomization.yaml
│   │       │   └── patches/
│   │       ├── staging/
│   │       └── prod/
│   │
│   └── docker/                         # Local dev containers
│       ├── postgres/
│       ├── redis/
│       └── localstack/
│
├── tools/                              # Developer tooling
│   ├── seed-data/                      # Demo/test data
│   │   ├── scenarios/
│   │   │   ├── demo-basic/
│   │   │   └── demo-full/
│   │   └── seed.py
│   │
│   └── scripts/
│       ├── setup.sh
│       ├── reset-db.sh
│       └── generate-clients.sh
│
├── docs/                               # Documentation (MkDocs)
│   ├── index.md
│   ├── architecture/
│   ├── api/
│   └── guides/
│
├── specs/                              # Feature specifications (SpecKit)
│   ├── 001-feature-name/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   └── ...
│
├── .specify/                           # SpecKit framework
│   ├── memory/
│   │   └── constitution.md
│   └── templates/
│
├── .github/                            # GitHub Actions
│   └── workflows/
│       ├── ci.yml
│       ├── build-images.yml
│       └── deploy.yml
│
├── docker-compose.yml                  # Full stack local dev
├── docker-compose.override.yml         # Local overrides
├── pyproject.toml                      # Python workspace root
├── package.json                        # Node workspace root
├── mkdocs.yml
├── Makefile
├── CLAUDE.md                           # AI instructions
└── README.md
```

**Service Internal Structure** (consistent pattern):

```
service-name/
├── src/
│   ├── main.py                         # FastAPI entry point
│   ├── api/                            # Endpoints
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── [routes].py
│   ├── core/                           # Business logic
│   │   └── [domain].py
│   ├── db/                             # Database (SQLAlchemy)
│   │   ├── models.py
│   │   └── repository.py
│   └── clients/                        # External service clients
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── e2e/
├── Dockerfile
├── pyproject.toml
└── alembic/                            # Migrations (if DB)
    └── versions/
```

**Key Conventions:**

| Element | Convention | Example |
|---------|------------|---------|
| Domain folders | Kebab-case | `user-management`, `access-control` |
| Services | Kebab-case | `auth-service`, `profile-service` |
| Frontend apps | Kebab-case | `web`, `admin`, `mobile` |
| Container images | `ghcr.io/farmer1st/{app}-{service}:sha-{commit}` | `ghcr.io/farmer1st/myapp-auth-service:sha-abc123` |
| K8s namespaces | Domain-based | `user-management`, `surveys` |

**What Lives Where:**

| Content | Location | Managed By |
|---------|----------|------------|
| Application code | `apps/`, `services/` | Dede, Dali |
| Shared libraries | `packages/` | Dede |
| Terraform modules | `infra/terraform/modules/` | Gus |
| Terraform envs | `infra/terraform/environments/` | Gus |
| K8s base manifests | `infra/k8s/base/` | Gus |
| K8s env overlays | `infra/k8s/overlays/{env}/` | Gus (via deploy PRs) |
| Feature specs | `specs/` | Baron |
| Documentation | `docs/` | Victor |

---

## 2. Agent Architecture

### 2.1 Agent Definitions Repository

All agent definitions live in a single monorepo (`farmer1st-ai-agents`):

```
farmer1st-ai-agents/
├── agents/
│   │
│   │  # Workflow Agents (participate in SDLC phases)
│   ├── baron/                   # PM - specify, plan, tasks
│   │   ├── agent-card.json      # A2A agent card
│   │   ├── config.yaml          # Runtime configuration (incl. escalation target)
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
│   ├── gus/                     # DevOps - gitops, releases
│   ├── victor/                  # Docs QA - consistency, product docs
│   ├── general/                 # Code reviewer
│   ├── socrate/                 # Retro analyst - learning loop, RAG
│   │
│   │  # Issue Creators & Consultants
│   ├── veuve/                   # Product Owner - features, roadmap
│   ├── duc/                     # Tech Owner - architecture, tech debt
│   │
│   │  # Human Bridges (deterministic, not AI)
│   ├── human-product/           # Bridge to product human
│   └── human-tech/              # Bridge to technical human
│
└── shared/
    └── prompts/                 # Shared prompt fragments
```

**Agent config.yaml example:**

```yaml
# agents/dede/config.yaml
name: dede
domain: backend
escalation_target: human-tech
skills:
  - implement.backend
  - document.api
```

### 2.2 Agent Card (Google A2A Protocol)

We adopt the [Google A2A Protocol](https://github.com/google/A2A) — an open standard for agent-to-agent communication.
Each agent publishes an agent card at `/.well-known/agent.json`:

```json
{
  "name": "baron",
  "description": "PM Agent - Creates specifications, plans, and task lists",
  "url": "http://baron:8002",
  "version": "2.1.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "skills": [
    {
      "id": "specify.feature",
      "name": "Create Feature Specification",
      "description": "Generate a feature specification from a natural language description",
      "tags": ["specification", "planning"],
      "inputModes": ["text"],
      "outputModes": ["text", "file"]
    },
    {
      "id": "specify.plan",
      "name": "Create Implementation Plan",
      "description": "Generate an implementation plan from a specification",
      "tags": ["planning", "architecture"],
      "inputModes": ["text", "file"],
      "outputModes": ["text", "file"]
    },
    {
      "id": "specify.tasks",
      "name": "Generate Task List",
      "description": "Generate actionable tasks from a plan",
      "tags": ["tasks", "planning"],
      "inputModes": ["text", "file"],
      "outputModes": ["text", "file"]
    }
  ],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "authentication": {
    "schemes": ["bearer"]
  }
}
```

**A2A Protocol Compliance:**

| A2A Feature | Support |
|-------------|---------|
| JSON-RPC 2.0 | Yes |
| Agent discovery (`/.well-known/agent.json`) | Yes |
| Task lifecycle states | Yes (`submitted`, `working`, `input-required`, `completed`, `failed`) |
| SSE streaming | Yes (via `tasks/sendSubscribe`) |
| Push notifications | Future |
| gRPC | Future |

### 2.3 Versioning Strategy

**Per-agent semantic versioning with Git tags:**

```
baron@1.0.0
baron@1.1.0
baron@2.0.0
duc@1.0.0
duc@1.5.0
marie@1.2.0
```

**Tag discovery via GitHub API:**

```python
def get_agent_versions(agent_name: str, limit: int = 5) -> list[str]:
    """Fetch last N versions for an agent from GitHub tags."""
    tags = github.list_tags(pattern=f"{agent_name}@*")
    return sorted(tags, key=semver_key, reverse=True)[:limit]
```

### 2.4 SDK Abstraction Layer

We use the **Claude Agent SDK** (`claude_agent_sdk` package), which leverages Claude Code's
built-in OAuth authentication. **No API key is required** — authentication is handled
via Claude Pro/Max subscription login.

> **IMPORTANT:** Do NOT use the `anthropic` Python package with API keys. The Claude Agent
> SDK provides a higher-level abstraction with built-in tools and MCP server support.
> See `../sdk-agent-poc` for a working reference implementation.

**Claude Agent SDK Pattern:**

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    tool,
    create_sdk_mcp_server,
)

# No API key needed — uses Claude Code's built-in OAuth authentication
options = ClaudeAgentOptions(
    allowed_tools=[
        # Built-in tools
        "Read", "Write", "Edit", "Glob", "Grep",  # File operations
        "Bash",                                     # Shell commands
        "WebSearch",                                # Web search
        # Custom MCP tools
        "mcp__custom-tools__my_tool",
    ],
    permission_mode="acceptEdits",
    mcp_servers={"custom-tools": custom_tools_server},
    system_prompt=AGENT_SYSTEM_PROMPT,
    cwd="/path/to/worktree",
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Your prompt here")
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
                elif isinstance(block, ToolUseBlock):
                    print(f"Using tool: {block.name}")
```

**Custom Tools via MCP:**

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("extract_confidence", "Extract confidence score from response", {"response": str})
async def extract_confidence(args: dict) -> dict:
    # Custom logic to determine confidence
    confidence = analyze_confidence(args["response"])
    return {"content": [{"type": "text", "text": str(confidence)}]}

custom_tools_server = create_sdk_mcp_server(
    name="agent-tools",
    version="1.0.0",
    tools=[extract_confidence, ...]
)
```

**Abstraction for Future Providers:**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AgentResponse:
    content: str
    confidence: int  # 0-100
    artifacts: list[dict]
    status: str  # "completed", "input-required", "failed"

class AgentRuntime(ABC):
    """Abstract base for agent runtimes. Swap implementations without changing agents."""

    @abstractmethod
    async def invoke(self, prompt: str, context: dict, session_id: str) -> AgentResponse:
        pass

class ClaudeAgentRuntime(AgentRuntime):
    """Implementation using Claude Agent SDK (OAuth, not API key)."""

    def __init__(self, agent_config: dict, worktree_path: str):
        self.config = agent_config
        self.worktree_path = worktree_path
        self.options = ClaudeAgentOptions(
            allowed_tools=agent_config.get("allowed_tools", []),
            system_prompt=agent_config.get("system_prompt", ""),
            cwd=worktree_path,
        )

    async def invoke(self, prompt: str, context: dict, session_id: str) -> AgentResponse:
        async with ClaudeSDKClient(options=self.options) as client:
            await client.query(prompt)
            # Process response and extract confidence...

class FutureProviderRuntime(AgentRuntime):
    """Future: OpenAI, Gemini, local models (would need API keys)."""
    pass
```

### 2.5 Agent Pod Architecture

**Pod-per-agent-per-issue (operator-injected):**

The Kubernetes Operator (Section 4.3) spawns agent pods for each feature with a specific
version defined in environment variables. Each pod loads only that version at startup—no
multi-version caching or hot-reload complexity.

**v1 Pod Lifecycle:**
- Pods stay alive for the **entire feature duration** (including human escalation waits)
- Pods terminate only when the issue workflow completes (success or failure)
- Simple polling model for human input (see Section 6.1)

**Future Enhancement:**
- Stop-and-go pattern (Section 11.2) where pods checkpoint and exit during human waits
- More resource-efficient but requires webhook infrastructure

**Why pod-per-issue (not shared pools)?**

| Shared Pools (rejected) | Pod-per-Feature (adopted) |
|-------------------------|---------------------------|
| Complex routing/affinity | Simple: one pod = one feature |
| Session context leakage risk | Natural isolation via worktree |
| Memory pressure from many sessions | Clean pod lifecycle |
| Harder to debug | Clear lineage per issue |

We considered shared agent pools for efficiency but chose pod-per-issue for v1 because:

1. **Simplicity**: No complex routing or session affinity
2. **Isolation**: Natural process + filesystem isolation via worktree
3. **Cost**: EKS pods are cheap, and they're ephemeral (die on completion)
4. **Debugging**: One pod = one feature = easy to trace

> **Future Optimization:** If costs become significant at scale, migrate to shared
> pools with worktree-based process isolation.

```
Namespace: fc-issue-auth-123/        # Ephemeral namespace per issue
└── Pod: baron                        # Simple name within namespace
    ├── Environment:
    │   AGENT_NAME=baron
    │   AGENT_VERSION=2.0.0
    │   WORKTREE_PATH=/volumes/worktrees/issue-auth-123
    │
    ├── Startup:
    │   1. Fetch baron@2.0.0 config from GitHub (single version)
    │   2. Load config to /agent/config/
    │   3. Ready to serve
    │
    └── Request handling:
        POST /invoke (http://baron:8002 within namespace)
        → Load config from /agent/config/ (pre-loaded at startup)
        → Execute via SDK abstraction
        → Return response with confidence score
```

**Why single-version pods?**

| Multi-Version (rejected) | Single-Version (adopted) |
|--------------------------|--------------------------|
| Complex version routing | Simple: one pod = one version |
| Memory overhead for cached versions | Minimal footprint |
| Race conditions on refresh | Immutable after startup |
| Harder to debug | Clear lineage per issue |

**Pod lifecycle:**

```python
class AgentPod:
    """Agent pod loads a single version at startup."""

    def __init__(self):
        self.agent_name = os.environ["AGENT_NAME"]
        self.agent_version = os.environ["AGENT_VERSION"]
        self.worktree_path = os.environ["WORKTREE_PATH"]
        self.config = None

    async def startup(self):
        """Load agent config once at startup."""
        self.config = await fetch_agent_config(
            agent=self.agent_name,
            version=self.agent_version,
        )
        # Claude Agent SDK uses OAuth from Claude Code — no API key needed
        self.runtime = ClaudeAgentRuntime(
            agent_config=self.config,
            worktree_path=self.worktree_path,
        )

    @app.post("/invoke")
    async def invoke(self, request: InvokeRequest, session_id: str = Header(...)):
        """Invoke agent with pre-loaded config."""
        return await self.runtime.invoke(
            prompt=request.prompt,
            context=request.context,
            session_id=session_id,
        )
```

When a new agent version is needed, the Operator terminates the old pod and spawns
a new one with the updated `AGENT_VERSION` environment variable.

---

## 3. Farmer Code (SDLC App)

### 3.1 Overview

Farmer Code automates the software development lifecycle using AI agents:

```
Issue Created → READY label → SPECIFY → PLAN → TASKS → TEST_DESIGN → IMPLEMENT → VERIFY → DOCS_QA → REVIEW → RELEASE → RETRO
```

### 3.2 Components

| Component | Purpose | Deployment |
|-----------|---------|------------|
| PWA (UI) | Kanban board, issue management | CloudFlare Pages |
| API | Backend for UI, creates IssueWorkflow CRDs | EKS pod |
| Operator | Watches CRDs, manages issue pods | EKS pod |
| Issue Orchestrator | Per-issue workflow state machine | Long-running pod |
| Agent Pods | All agents spawn per issue | Long-running pods |

### 3.3 Agent Roster

**Workflow Agents** (participate in phases):

| Agent | Role | Domain | Escalates To |
|-------|------|--------|--------------|
| Baron | PM - specify, plan, tasks | — | Smart (Product or Tech) |
| Marie | QA - test design, verification | `test` | HumanTech |
| Dede | Backend developer | `backend` (includes docs) | HumanTech |
| Dali | Frontend developer | `frontend` (includes docs) | HumanTech |
| Gus | DevOps - gitops, releases | `gitops` (includes docs) | HumanTech |
| Victor | Docs QA - consistency, product docs | — | Smart (Product or Tech) |
| General | Code reviewer | — | HumanTech |
| Socrate | Retro analyst - learning loop, RAG | — | Smart (Product or Tech) |

**Issue Creators & Consultants** (can initiate issues, consulted on-demand):

| Agent | Role | Creates Issues For | Escalates To |
|-------|------|-------------------|--------------|
| Veuve | Product Owner - features, roadmap, vision | Product features | HumanProduct |
| Duc | Tech Owner - architecture, tech debt, infra | Technical issues | HumanTech |

**Human Bridges** (deterministic code, not AI):

| Agent | Role | Channel |
|-------|------|---------|
| HumanProduct | Bridge to product human | Slack, GitHub |
| HumanTech | Bridge to technical human | Slack, GitHub |

### 3.4 Issue Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Issue Lifecycle                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  GitHub Issue Created                                                            │
│  (by Veuve, Duc, human, or future: Sentry/observability)                        │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  BACKLOG (no "READY" label)                                              │    │
│  │  - Visible in Kanban                                                     │    │
│  │  - Humans chat with agents via Chat Portal to refine                     │    │
│  │  - Labels define type: feature, bug, tech-debt, infra                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│       │                                                                          │
│       │ Human adds "READY" label                                                 │
│       ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  WORKFLOW STARTS AUTOMATICALLY                                           │    │
│  │  - IssueWorkflow CRD created                                             │    │
│  │  - All agent pods spawned                                                │    │
│  │  - Orchestrator begins SPECIFY phase                                     │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Issue Types (labels):**

| Label | Description | Example |
|-------|-------------|---------|
| `feature` | New user-facing functionality | "Add user authentication" |
| `bug` | Defect fix | "Login fails on Safari" |
| `tech-debt` | Refactoring, cleanup | "Migrate to new ORM" |
| `infra` | Infrastructure changes | "Add Redis caching layer" |

### 3.5 Workflow Phases

The workflow is **strictly linear** with feedback loops for error recovery (Section 10).
Each phase has **one owner agent**. Agents can consult any other agent during their phase.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              Issue Workflow                                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐                       │
│  │  Baron   │   │  Baron   │   │  Baron   │   │  Marie   │                       │
│  │ SPECIFY  │──▶│   PLAN   │──▶│  TASKS   │──▶│TEST_DESIGN│                      │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘                       │
│                                                     │                             │
│                                                     ▼                             │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                    IMPLEMENT (sequential by domain)                         │  │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐                                │  │
│  │  │  Dede    │──▶│  Dali    │──▶│   Gus    │  Each agent scans tasks.md    │  │
│  │  │ backend  │   │ frontend │   │  gitops  │  and does their domain tasks   │  │
│  │  └──────────┘   └──────────┘   └──────────┘  (no-op if no matching tasks)  │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                     │                             │
│                                                     ▼                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐       │
│  │  Marie   │   │  Victor  │   │ General  │   │   Gus    │   │   Gus    │       │
│  │  VERIFY  │──▶│ DOCS_QA  │──▶│  REVIEW  │──▶│ RELEASE  │──▶│ RELEASE  │       │
│  └──────────┘   └──────────┘   └──────────┘   │ STAGING  │   │  PROD    │       │
│                                                └──────────┘   └──────────┘       │
│                                                                    │              │
│                                                                    ▼              │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                           RETRO (Learning Loop)                             │  │
│  │  ┌──────────┐                                                              │  │
│  │  │ Socrate  │  Analyzes: confidence scores, escalations, A2A conversations │  │
│  │  │  RETRO   │  Outputs: PRs for prompt/KB improvements + reports           │  │
│  │  └──────────┘  Human approves changes via Slack (approve/change/reject)    │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                     │                             │
│                                                     ▼                             │
│                                                   Done                            │
│                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                         FEEDBACK TRIGGERS                                   │  │
│  │  • spec_ambiguity    → back to SPECIFY                                     │  │
│  │  • plan_infeasible   → back to PLAN                                        │  │
│  │  • test_failure      → back to IMPLEMENT                                   │  │
│  │  • docs_inconsistent → back to IMPLEMENT                                   │  │
│  │  • review_changes    → back to IMPLEMENT                                   │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                   │
│  Note: RELEASE_DEV is automated (CI/CD), no agent involved                       │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Phase Details:**

| Phase | Owner | Input | Output |
|-------|-------|-------|--------|
| SPECIFY | Baron | GitHub issue | `.specify/spec.md` |
| PLAN | Baron | spec.md | `.specify/plan.md` |
| TASKS | Baron | plan.md | `.specify/tasks.md` (with domain tags) |
| TEST_DESIGN | Marie | tasks.md | Test cases in `tests/` |
| IMPLEMENT | Dede, Dali, Gus | tasks.md | Code + docs (each does their domain) |
| VERIFY | Marie | Code + tests | Test results, integrity check |
| DOCS_QA | Victor | All docs | Consistency check, product docs update |
| REVIEW | General | PR | Review comments, approval |
| RELEASE_STAGING | Gus | Approved PR | Deployed to staging |
| RELEASE_PROD | Gus | Staging verified | Deployed to production |
| RETRO | Socrate | All events + conversations | PRs for improvements + reports |

**Feedback Loop Constraints (from Section 10.4):**

| Constraint | Value | Purpose |
|------------|-------|---------|
| Max total loops | 5 | Prevent runaway workflows |
| Max same transition | 2 | Detect oscillation patterns |
| Escalation on breach | Human | Workflow pauses for intervention |

### 3.6 Domain-Based Task Routing

Baron generates `tasks.md` with explicit domain tags. Each implementing agent
scans the task list and executes only tasks matching their domain.

**Example tasks.md:**

```markdown
## Tasks for issue-auth-123

- [ ] Create user model and auth endpoints `domain:backend` @dede
- [ ] Create login/register React components `domain:frontend` @dali
- [ ] Add auth service Kubernetes manifests `domain:gitops` @gus
- [ ] Write unit tests for auth service `domain:test` @marie
```

**Domain assignments:**

| Domain | Agent | Includes |
|--------|-------|----------|
| `backend` | Dede | Backend code + API documentation |
| `frontend` | Dali | Frontend code + UI documentation |
| `gitops` | Gus | K8s manifests + infrastructure docs |
| `test` | Marie | Test cases |

**Execution order:** `backend` → `frontend` → `gitops`

If an agent has no tasks in their domain, they no-op and the workflow continues.

### 3.7 Agent Consultation (A2A)

Any agent can consult any other agent during their phase via A2A. This is not
special to any agent — Duc, Veuve, or any other agent can be consulted.

```python
class AnyAgent:
    async def do_work(self) -> Result:
        # Agent identifies a question outside their expertise
        if self.needs_consultation():
            response = await self.a2a_client.send_task(
                agent="duc",  # or "veuve", "marie", etc.
                skill="clarify.architecture",
                message={"question": "Should this use event sourcing or CRUD?"}
            )

            # If consulted agent has low confidence, THEY escalate (not us)
            # We receive the final answer (possibly human-verified)
            ...
```

**Escalation is vertical:** If Duc is consulted and has <80% confidence, Duc
escalates to HumanTech. The requesting agent receives the final answer.

**Audit trail:** All consultations are logged as events:
```python
AgentConsulted(from_agent="baron", to_agent="duc", question="...", response="...", confidence=85)
```

### 3.8 Orchestrator Per Issue

Each issue gets its own long-running orchestrator pod. The orchestrator implements
**Event Sourcing** (Section 9) for auditability and crash recovery:

- **State from events** — rehydrate on restart, never store mutable state
- **Idempotent execution** — safe to restart at any point
- **Polling for human input** — v1 uses polling, future versions may use webhooks

**v1 Lifecycle (Polling):**
- Orchestrator pod stays alive for the entire feature duration
- When human input is needed, the orchestrator polls GitHub for responses
- Simple, predictable, easy to debug

**Future Enhancement (Stop-and-Go):**
- Orchestrator checkpoints state and exits when waiting for human input
- Webhook triggers new Job when human responds
- More resource-efficient for long-running features

```python
class IssueOrchestrator:
    """Event-sourced orchestrator with polling for human input (v1)."""

    def __init__(
        self,
        issue_id: str,
        workflow_config: WorkflowDefinition,
        event_store: EventStore,
        projection: WorkflowProjection,
    ):
        self.issue_id = issue_id
        self.workflow_config = workflow_config
        self.event_store = event_store
        self.projection = projection
        # No self.current_phase — state comes from events

    async def run(self) -> OrchestratorResult:
        """
        Run workflow with automatic recovery.

        This method runs until the feature is complete or fails:
        1. Rehydrate state from the event store (crash recovery)
        2. Resume from wherever we left off
        3. Poll for human input when escalation is needed (v1)
        4. Continue until workflow completes
        """
        # === REHYDRATE STATE FROM EVENTS (Section 9.4) ===
        state = await self.projection.get_state(self.issue_id)

        # Already done? Exit immediately.
        if state.status == "completed":
            return OrchestratorResult(status="already_completed")

        # Already failed? Exit with failure.
        if state.status == "failed":
            return OrchestratorResult(status="already_failed", error=state.error)

        # === EXECUTE WORKFLOW (with feedback loop support) ===
        while True:
            state = await self.projection.get_state(self.issue_id)
            phases_to_run = self._get_remaining_phases(state)

            if not phases_to_run:
                break  # All phases complete

            phase = phases_to_run[0]  # Process one phase at a time

            # Record phase start
            await self.event_store.append(PhaseStarted(
                issue_id=self.issue_id,
                phase=phase.name,
                agent=phase.agent,
            ))

            # Execute phase with error handling
            try:
                result = await self._execute_phase(phase)
            except Exception as e:
                # === HANDLE PHASE FAILURE ===
                error_code = type(e).__name__
                is_retryable = isinstance(e, (TimeoutError, ConnectionError, RateLimitError))

                await self.event_store.append(PhaseFailed(
                    issue_id=self.issue_id,
                    phase=phase.name,
                    agent=phase.agent,
                    error_code=error_code,
                    error_message=str(e),
                    retryable=is_retryable,
                ))

                if is_retryable and self._can_retry(phase):
                    logger.warning(f"Phase {phase.name} failed with retryable error, will retry: {e}")
                    await asyncio.sleep(self.config.retry_backoff.total_seconds())
                    continue  # Retry the same phase

                # Non-retryable or max retries exceeded → fail workflow
                logger.error(f"Phase {phase.name} failed permanently: {e}")
                await self.event_store.append(WorkflowFailed(
                    issue_id=self.issue_id,
                    reason=str(e),
                    failed_phase=phase.name,
                    recoverable=is_retryable,
                ))
                return OrchestratorResult(status="failed", error=str(e))

            # === HANDLE ESCALATION (v1: polling) ===
            if result.status == "input_required":
                await self.event_store.append(EscalationRequested(
                    issue_id=self.issue_id,
                    agent=phase.agent,
                    question=result.question,
                    confidence=result.confidence,
                ))

                # v1: Poll for human response (pod stays alive)
                response = await self._poll_for_human_response(
                    question=result.question,
                    timeout=self.config.escalation_timeout,
                )

                await self.event_store.append(EscalationResolved(
                    issue_id=self.issue_id,
                    agent=phase.agent,
                    human_response=response.text,
                    responded_by=response.user,
                ))

                # Re-execute phase with human input
                result = await self._execute_phase(phase, human_context=response)

            # === HANDLE FEEDBACK LOOPS (Section 10) ===
            if result.feedback_trigger:
                next_phase = self.workflow_config.get_feedback_target(
                    from_phase=phase.name,
                    trigger=result.feedback_trigger,
                )
                if next_phase:
                    await self.event_store.append(FeedbackRequested(
                        issue_id=self.issue_id,
                        from_phase=phase.name,
                        to_phase=next_phase,
                        reason=result.feedback_trigger,
                    ))
                    # Loop continues, _get_remaining_phases will return from target phase
                    continue

            # === RECORD SUCCESS ===
            await self.event_store.append(PhaseCompleted(
                issue_id=self.issue_id,
                phase=phase.name,
                agent=phase.agent,
                confidence=result.confidence,
                commit_sha=result.commit_sha,
            ))

        # === WORKFLOW COMPLETE ===
        await self.event_store.append(WorkflowCompleted(issue_id=self.issue_id))
        return OrchestratorResult(status="completed")

    def _get_remaining_phases(self, state: WorkflowState) -> list[Phase]:
        """Determine which phases still need to run."""
        if state.pending_feedback:
            # Feedback loop: restart from target phase
            return self.workflow_config.get_phases_from(state.pending_feedback["to_phase"])
        # Normal: skip completed phases
        return [p for p in self.workflow_config.phases if p.name not in state.phases_completed]

    async def _poll_for_human_response(
        self,
        question: str,
        timeout: timedelta,
    ) -> HumanResponse:
        """Poll GitHub for human response (v1 implementation)."""
        deadline = datetime.now() + timeout
        while datetime.now() < deadline:
            response = await self.github.check_for_response(
                issue=self.issue_number,
                comment_id=self.escalation_comment_id,
            )
            if response:
                return response
            await asyncio.sleep(self.config.poll_interval.total_seconds())

        raise EscalationTimeoutError(f"No response within {timeout}")
```

**v1 Pod lifecycle (Polling):**

```
Pod: Start → SPECIFY → PLAN → TASKS → needs human input → POLL → human responds
                                                                      ↓
     ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
     ↓
     IMPLEMENT → VERIFY → REVIEW → Done → Pod terminates
```

**Future: Stop-and-Go lifecycle (webhook-triggered):**

```
Job 1: Start → SPECIFY → PLAN → needs input → CHECKPOINT → EXIT (pod dies)
                                                    ↓
                                        (hours/days pass, no resources used)
                                                    ↓
                                        Human responds via GitHub
                                                    ↓
                                        Webhook triggers new Job
                                                    ↓
Job 2: Rehydrate → Skip completed → IMPLEMENT → VERIFY → REVIEW → Done
```

The v1 polling approach is simpler to implement and debug. The stop-and-go pattern
can be introduced later when resource efficiency becomes a priority.

### 3.9 Learning Loop (RETRO Phase)

After RELEASE_PROD, Socrate runs the RETRO phase to analyze the issue lifecycle and
propose improvements to agent prompts and knowledge bases.

**What Socrate Analyzes:**

| Data Source | What Socrate Looks For |
|-------------|------------------------|
| Event store | Phase durations, bottlenecks, feedback loops triggered |
| Confidence scores | Which agents struggled? Patterns in low-confidence responses |
| Escalations | What questions went to humans? What were the answers? |
| A2A conversations | What did agents ask each other? Gaps in knowledge? |
| Human responses | What corrections did humans make? Training data |

**What Socrate Produces:**

1. **PRs to `farmer1st-ai-agents`**:
   - Prompt improvements (clearer instructions, edge cases)
   - KB additions (new knowledge from human responses)
   - Skill refinements

2. **Reports/Dashboards**:
   - Issue retrospective summary
   - Agent performance metrics
   - Escalation patterns

**Approval Flow (v1):**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Socrate RETRO Approval Flow                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Socrate analyzes issue-auth-123 lifecycle                                       │
│       │                                                                          │
│       ▼                                                                          │
│  Socrate creates PR to farmer1st-ai-agents:                                      │
│  "Improve Baron's planning prompt for auth-related features"                     │
│       │                                                                          │
│       ▼                                                                          │
│  Socrate posts to Slack (smart: HumanTech or HumanProduct):                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │ 📊 RETRO: issue-auth-123 complete                                        │    │
│  │                                                                          │    │
│  │ Proposed improvement: Baron planning prompt                              │    │
│  │ PR: github.com/farmer1st/ai-agents/pull/456                             │    │
│  │                                                                          │    │
│  │ Reply: approve | change <feedback> | reject                              │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│       │                                                                          │
│       ▼                                                                          │
│  Human reviews and responds                                                      │
│       │                                                                          │
│       ├── "approve" → Socrate merges PR                                          │
│       ├── "change: also add example for OAuth" → Socrate updates PR, re-asks     │
│       └── "reject" → Socrate closes PR, logs reason                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Future Enhancement: Auto-Approve:**

When confidence in Socrate's suggestions is high (based on historical approval rates),
low-risk changes can be auto-merged:

```python
class SocrateAgent:
    async def propose_improvement(self, improvement: Improvement) -> None:
        pr = await self.create_pr(improvement)

        if self.can_auto_approve(improvement):
            # Future: auto-merge low-risk, high-confidence improvements
            await self.merge_pr(pr)
            await self.notify_humans(pr, action="auto-merged")
        else:
            # v1: always ask human
            await self.request_human_approval(pr)

    def can_auto_approve(self, improvement: Improvement) -> bool:
        # Future: based on improvement type, historical approval rate, risk score
        return False  # v1: never auto-approve
```

---

## 4. Kubernetes Infrastructure

### 4.1 Namespace Strategy

We use **namespace-per-issue** for workflow isolation and **a permanent namespace** for
Chat Portal agents:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Kubernetes Namespaces                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ai-agents/                          # PERMANENT - Chat Portal agents            │
│  ├── baron          (always running)                                            │
│  ├── duc            (always running)                                            │
│  ├── veuve          (always running)                                            │
│  ├── human-product  (always running)                                            │
│  └── human-tech     (always running)                                            │
│                                                                                  │
│  fc-issue-auth-123/                  # EPHEMERAL - per Issue Workflow            │
│  ├── orchestrator                                                               │
│  ├── baron                                                                      │
│  ├── marie                                                                      │
│  ├── dede                                                                       │
│  ├── dali                                                                       │
│  ├── gus                                                                        │
│  ├── victor                                                                     │
│  ├── general                                                                    │
│  ├── socrate                                                                    │
│  ├── veuve                                                                      │
│  ├── duc                                                                        │
│  ├── human-product                                                              │
│  └── human-tech                                                                 │
│      ↑                                                                          │
│      └── Namespace deleted when workflow completes                              │
│                                                                                  │
│  fc-issue-payment-456/               # Another ephemeral namespace               │
│  └── ...                                                                        │
│                                                                                  │
│  farmercode/                         # Infrastructure namespace                  │
│  ├── farmercode-api                                                             │
│  └── farmercode-operator                                                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Why namespace-per-issue?**

| Aspect | Single Namespace (rejected) | Namespace-per-Issue (adopted) |
|--------|----------------------------|------------------------------|
| Pod naming | `baron-issue-auth-123` | `baron` (simple) |
| Cleanup | Delete pods by label | Delete namespace (cascades) |
| Isolation | Shared resources | Complete isolation |
| Resource quotas | Complex per-label | Simple per-namespace |
| Service discovery | All in one namespace | Clean per-issue DNS |

**Naming conventions:**

| Namespace | Purpose | Lifecycle |
|-----------|---------|-----------|
| `ai-agents` | Permanent agents for Chat Portal | Always exists |
| `fc-{issue-id}` | Ephemeral workflow agents | Created/deleted per issue |
| `farmercode` | API, Operator, infrastructure | Always exists |

**Service discovery within workflow:**
- Agents in `fc-issue-auth-123` call each other via simple names: `http://baron:8002`
- No cross-namespace calls needed — each workflow has its own agent copies

### 4.2 Custom Resource Definition (CRD)

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: issueworkflows.farmercode.io
spec:
  group: farmercode.io
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                repo:
                  type: string
                branch:
                  type: string
                issueNumber:
                  type: integer
                workflow:
                  type: string
                agents:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      version:
                        type: string
            status:
              type: object
              properties:
                phase:
                  type: string
                worktreePath:
                  type: string
                pods:
                  type: array
                  items:
                    type: object
  scope: Namespaced
  names:
    plural: issueworkflows
    singular: issueworkflow
    kind: IssueWorkflow
    shortNames:
      - fw
```

### 4.3 Example IssueWorkflow

```yaml
apiVersion: farmercode.io/v1
kind: IssueWorkflow
metadata:
  name: issue-auth-123
  namespace: farmercode            # CRD lives in infrastructure namespace
  labels:
    issue-type: feature
spec:
  repo: farmer1st/my-app
  branch: issue/auth-123
  issueNumber: 42
  workflow: sdlc-standard
  agents:
    # Workflow agents
    - name: baron
      version: "2.0.0"
    - name: marie
      version: "1.2.0"
    - name: dede
      version: "3.0.0"
    - name: dali
      version: "1.0.0"
    - name: gus
      version: "2.1.0"
    - name: victor
      version: "1.0.0"
    - name: general
      version: "1.0.0"
    - name: socrate
      version: "1.0.0"
    # Consultants (can be invoked via A2A)
    - name: veuve
      version: "1.0.0"
    - name: duc
      version: "1.5.0"
    # Human bridges
    - name: human-product
      version: "1.0.0"
    - name: human-tech
      version: "1.0.0"
status:
  phase: implement
  workflowNamespace: fc-issue-auth-123   # Ephemeral namespace for this workflow
  worktreePath: /volumes/worktrees/issue-auth-123
  pods:                                   # Simple names within workflow namespace
    - name: orchestrator
      status: Running
    - name: baron
      status: Running
    - name: marie
      status: Running
    - name: dede
      status: Running
    - name: dali
      status: Running
    - name: gus
      status: Running
    - name: victor
      status: Running
    - name: general
      status: Running
    - name: socrate
      status: Running
    - name: veuve
      status: Running
    - name: duc
      status: Running
    - name: human-product
      status: Running
    - name: human-tech
      status: Running
```

### 4.4 Kubernetes Operator (kopf)

```python
import kopf
import kubernetes
from kubernetes import client

WORKFLOW_NS_PREFIX = "fc-"  # fc-issue-auth-123

@kopf.on.create('farmercode.io', 'v1', 'issueworkflows')
async def on_issue_created(spec, name, namespace, logger, **kwargs):
    """Handle new issue workflow creation."""
    logger.info(f"Creating issue workflow: {name}")

    v1 = client.CoreV1Api()
    workflow_ns = f"{WORKFLOW_NS_PREFIX}{name}"

    # 1. Create ephemeral namespace for this workflow
    ns = client.V1Namespace(
        metadata=client.V1ObjectMeta(
            name=workflow_ns,
            labels={
                "app": "farmercode",
                "issue": name,
                "managed-by": "farmercode-operator",
            }
        )
    )
    v1.create_namespace(body=ns)
    logger.info(f"Created namespace: {workflow_ns}")

    # 2. Create worktree on shared volume
    worktree_path = f"/volumes/worktrees/{name}"
    await create_worktree(
        repo=spec['repo'],
        branch=spec['branch'],
        path=worktree_path
    )

    # 3. Spawn orchestrator pod (simple name within workflow namespace)
    orchestrator_pod = create_orchestrator_pod(
        name="orchestrator",  # Simple name
        issue_id=name,
        worktree_path=worktree_path,
        agents=spec['agents'],
        workflow=spec['workflow']
    )
    v1.create_namespaced_pod(namespace=workflow_ns, body=orchestrator_pod)

    # 4. Spawn agent pods (simple names within workflow namespace)
    for agent in spec['agents']:
        agent_pod = create_agent_pod(
            name=agent['name'],  # Simple name: "baron", "marie", etc.
            agent_name=agent['name'],
            agent_version=agent['version'],
            worktree_path=worktree_path,
            issue_id=name,
        )
        v1.create_namespaced_pod(namespace=workflow_ns, body=agent_pod)

    return {'workflowNamespace': workflow_ns, 'worktreePath': worktree_path}


@kopf.on.delete('farmercode.io', 'v1', 'issueworkflows')
async def on_issue_deleted(spec, name, namespace, logger, **kwargs):
    """Cleanup issue workflow resources."""
    logger.info(f"Deleting issue workflow: {name}")

    v1 = client.CoreV1Api()
    workflow_ns = f"{WORKFLOW_NS_PREFIX}{name}"

    # Delete namespace — cascades deletion of all pods, services, etc.
    try:
        v1.delete_namespace(name=workflow_ns)
        logger.info(f"Deleted namespace: {workflow_ns}")
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 404:
            raise

    # Archive/delete worktree
    await cleanup_worktree(f"/volumes/worktrees/{name}")


def create_agent_pod(
    name: str,
    agent_name: str,
    agent_version: str,
    worktree_path: str,
    issue_id: str,
):
    """
    Create a pod spec for an agent.

    NOTE: Claude Agent SDK uses OAuth from Claude Code — no API key secret needed.
    Authentication is handled via the base image which has Claude Code pre-configured.
    """
    return client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=name,
            labels={
                "app": "farmercode-agent",
                "agent": agent_name,
                "issue": issue_id,
            }
        ),
        spec=client.V1PodSpec(
            containers=[
                client.V1Container(
                    name="agent",
                    image="ghcr.io/farmer1st/agent-runtime:latest",
                    env=[
                        client.V1EnvVar(name="AGENT_NAME", value=agent_name),
                        client.V1EnvVar(name="AGENT_VERSION", value=agent_version),
                        client.V1EnvVar(name="WORKTREE_PATH", value=worktree_path),
                        client.V1EnvVar(name="ISSUE_ID", value=issue_id),
                    ],
                    volume_mounts=[
                        client.V1VolumeMount(
                            name="worktrees",
                            mount_path="/volumes/worktrees"
                        ),
                        # Claude Code config for OAuth authentication
                        client.V1VolumeMount(
                            name="claude-config",
                            mount_path="/home/agent/.claude",
                            read_only=True
                        )
                    ]
                )
            ],
            volumes=[
                client.V1Volume(
                    name="worktrees",
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name="worktrees-pvc"
                    )
                ),
                # Claude Code OAuth config (not API keys)
                client.V1Volume(
                    name="claude-config",
                    secret=client.V1SecretVolumeSource(
                        secret_name="claude-oauth-config"
                    )
                )
            ]
        )
    )
```

### 4.5 Local Development (k3d)

```bash
# Create cluster with shared volume
k3d cluster create farmercode \
  --volume /tmp/farmercode/worktrees:/volumes/worktrees \
  --port 8080:80@loadbalancer

# Deploy infrastructure namespace and components
kubectl create namespace farmercode
kubectl apply -f infrastructure/dynamodb-local.yaml
kubectl apply -f infrastructure/operator.yaml
kubectl apply -f apps/farmercode-api.yaml

# Create ai-agents namespace for Chat Portal (permanent agents)
kubectl create namespace ai-agents
kubectl apply -f apps/chat-portal-agents.yaml

# Create a test issue workflow (operator will create fc-issue-test-001 namespace)
kubectl apply -f - <<EOF
apiVersion: farmercode.io/v1
kind: IssueWorkflow
metadata:
  name: issue-test-001
spec:
  repo: farmer1st/test-app
  branch: feature/test-001
  workflow: sdlc-standard
  agents:
    - name: baron
      version: latest
EOF
```

---

## 5. Agent Communication (A2A)

We implement the [Google A2A Protocol](https://github.com/google/A2A) for agent-to-agent
communication. A2A is an open protocol that defines JSON-RPC 2.0 endpoints for agent discovery and task execution.

### 5.1 Protocol Overview

Agents communicate using JSON-RPC 2.0 over HTTP:

```
┌──────────────┐         A2A Request (JSON-RPC 2.0)         ┌──────────────┐
│              │ ──────────────────────────────────────────▶│              │
│    Baron     │  POST http://duc:8002/a2a                   │     Duc      │
│              │  {"jsonrpc":"2.0","method":"tasks/send",...}│              │
│              │                                             │              │
│              │         A2A Response                        │              │
│              │ ◀──────────────────────────────────────────│              │
│              │  {"jsonrpc":"2.0","result":{"id":"..."},...}│              │
└──────────────┘                                             └──────────────┘
```

**A2A Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/agent.json` | GET | Agent discovery (capabilities) |
| `/a2a` | POST | JSON-RPC 2.0 endpoint for all operations |

**JSON-RPC Methods:**

| Method | Purpose |
|--------|---------|
| `tasks/send` | Send a task to an agent |
| `tasks/sendSubscribe` | Send task with SSE streaming |
| `tasks/get` | Get task status/result |
| `tasks/cancel` | Cancel a running task |

### 5.2 Task Lifecycle States

| State | Description |
|-------|-------------|
| `submitted` | Task received, queued for processing |
| `working` | Agent actively processing |
| `input-required` | Blocked on human input (triggers escalation) |
| `completed` | Successfully finished |
| `failed` | Error occurred |
| `canceled` | Task was canceled |

### 5.3 Streaming Responses

For long-running tasks, agents use SSE via `tasks/sendSubscribe`:

```python
@app.post("/a2a")
async def a2a_endpoint(request: JSONRPCRequest):
    if request.method == "tasks/sendSubscribe":
        return StreamingResponse(
            stream_task(request.params),
            media_type="text/event-stream"
        )
    # ... handle other methods

async def stream_task(params: dict):
    task_id = generate_task_id()

    # Task submitted
    yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': {'id': task_id, 'status': {'state': 'submitted'}}})}\n\n"

    # Task working
    yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': {'id': task_id, 'status': {'state': 'working'}}})}\n\n"

    async for chunk in runtime.invoke_stream(params["message"]):
        yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': {'id': task_id, 'artifact': {'parts': [{'type': 'text', 'text': chunk}]}}})}\n\n"

    # Task completed
    final = await runtime.get_result(task_id)
    yield f"data: {json.dumps({'jsonrpc': '2.0', 'result': {'id': task_id, 'status': {'state': 'completed'}, 'artifacts': final.artifacts}})}\n\n"
```

### 5.4 Session Isolation

Each feature gets isolated conversation contexts stored in **DynamoDB** (not files):

```
DynamoDB Table: farmercode
───────────────────────────────────────────────────────────
PK                    SK                        Data
───────────────────────────────────────────────────────────
issue#auth-123      conversation#baron#001    {messages: [...]}
issue#auth-123      conversation#duc#002      {messages: [...]}
issue#auth-123      conversation#marie#003    {messages: [...]}
issue#payment-456   conversation#baron#001    {messages: [...]}
```

The Claude SDK adapter reads/writes conversation history to DynamoDB, keyed by issue ID
and agent. This ensures:
- Persistence across pod restarts
- Queryable conversation history for training
- No file system state to manage

### 5.5 Service Discovery

A2A URLs vary based on namespace context (see Section 4.1 for namespace strategy):

| Context | URL Pattern | Example |
|---------|-------------|---------|
| **Within workflow namespace** | `http://{agent}:{port}` | `http://duc:8002/a2a` |
| **Chat Portal → workflow** | Not applicable | Workflows isolated |
| **Chat Portal internal** | `http://{agent}:{port}` | `http://baron:8002/a2a` |
| **Cross-namespace (rare)** | `http://{agent}.{namespace}.svc:{port}` | `http://baron.ai-agents.svc:8002/a2a` |

**Why simple names work:**

Within a Kubernetes namespace, services are discoverable by their short name. Since each
workflow runs in its own namespace (`fc-{issue-id}`), agents call each other using simple
names like `http://duc:8002`. This provides:

1. **Automatic isolation** — calls stay within the workflow namespace
2. **Simple configuration** — no namespace prefixes needed
3. **Consistent addressing** — same code works in any workflow namespace

**Agent Card URL:**

The `url` field in agent cards uses simple names. The actual URL resolution happens at
the Kubernetes DNS level based on which namespace the caller is in.

```json
{
  "name": "baron",
  "url": "http://baron:8002"
}
```

---

## 6. Human Escalation

### 6.1 Confidence-Based Escalation

When an agent has low confidence (<80%), it escalates to a human.

**v1 Approach: Polling**

The orchestrator polls GitHub for human responses. This keeps the implementation simple
and avoids webhook infrastructure complexity. Pods stay alive during the wait.

**Future: Webhook-Triggered Resumption**

Replace polling with GitHub webhooks + stop-and-go pattern (Section 11.2) for better
resource efficiency.

```python
class AgentRuntime:
    def __init__(self, config: AgentConfig):
        self.escalation_enabled = config.escalation_enabled
        self.confidence_threshold = config.confidence_threshold  # default: 80
        self.poll_interval = config.poll_interval  # default: 30s
        self.escalation_timeout = config.escalation_timeout  # default: 4 hours

    async def maybe_escalate(
        self,
        question: str,
        confidence: int,
        github_issue: int
    ) -> EscalationResult:
        if not self.escalation_enabled:
            return EscalationResult(escalated=False)

        if confidence >= self.confidence_threshold:
            return EscalationResult(escalated=False)

        # Post escalation comment
        comment_id = await github.post_comment(
            issue=github_issue,
            body=f"/human: {question}\n\nConfidence: {confidence}%"
        )

        # Notify via Slack
        await slack.send_notification(
            channel="#farmercode-escalations",
            message=f"Human input needed on issue #{github_issue}"
        )

        # v1: Poll for response (pod stays alive)
        # Future: Checkpoint and exit, webhook triggers resume
        response = await self.poll_for_response(
            issue=github_issue,
            comment_id=comment_id,
            agent_prefix=f"/{self.agent_name}"
        )

        return EscalationResult(
            escalated=True,
            human_response=response
        )
```

| Approach | v1 (Polling) | Future (Webhooks) |
|----------|--------------|-------------------|
| Implementation | Simple | Requires webhook infrastructure |
| Resource usage | Pod idles during wait | Pod terminates, zero resource usage |
| Latency | Poll interval (30s default) | Near-instant on webhook |
| Debugging | Easy (pod stays alive) | Requires event replay |

### 6.2 Escalation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Human Escalation Flow                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Baron asks Duc: "Should auth use JWT or sessions?"                         │
│       │                                                                     │
│       ▼                                                                     │
│  Duc evaluates → confidence: 65% (below 80% threshold)                      │
│       │                                                                     │
│       ▼                                                                     │
│  Duc posts comment on GitHub Issue #42:                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ /human: Should this service use JWT tokens or server-side sessions? │   │
│  │                                                                      │   │
│  │ Context: Auth service for multi-tenant SaaS                         │   │
│  │ Confidence: 65%                                                      │   │
│  │ Options I'm considering:                                             │   │
│  │ - JWT: Stateless, good for microservices                            │   │
│  │ - Sessions: Simpler revocation, established pattern                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  GitHub Action triggers → Slack notification sent                           │
│       │                                                                     │
│       ▼                                                                     │
│  Human replies in Slack (or directly on issue):                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ /duc Use JWT - we need stateless auth for the API gateway.          │   │
│  │ Make sure to implement token refresh and blacklisting for logout.    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                     │
│       ▼                                                                     │
│  Duc (polling) sees /duc reply                                              │
│       │                                                                     │
│       ▼                                                                     │
│  Duc incorporates feedback → returns to Baron with confidence: 100%         │
│  (human-verified)                                                           │
│       │                                                                     │
│       ▼                                                                     │
│  Baron continues workflow                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Escalation Modes

| Context | Escalation | Behavior |
|---------|------------|----------|
| Farmer Code workflow | Enabled | Low confidence → `/human` → wait → fail on timeout |
| Direct chat (future portal) | Disabled | Always answer, show confidence to user |

### 6.4 Confidence Persistence

All confidence scores are persisted for training:

```python
@dataclass
class ConfidenceRecord:
    timestamp: datetime
    issue_id: str
    source_agent: str      # Who asked
    target_agent: str      # Who answered
    question: str
    answer: str
    confidence: int        # 0-100
    escalated: bool
    human_response: str | None
    final_outcome: str     # "accepted", "rejected", "modified"
```

### 6.5 Human Bridge Implementation

Human Bridge agents (`human-product`, `human-tech`) are **not AI agents** — they're a
GitHub + Slack integration that routes escalations to humans and returns responses.

**Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Human Bridge Flow                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. Agent (e.g., Duc) needs human input                                          │
│       │                                                                          │
│       ▼                                                                          │
│  2. Agent posts comment to GitHub Issue:                                         │
│     ┌─────────────────────────────────────────────────────────────────────────┐ │
│     │ /human: Should this service use JWT or sessions?                        │ │
│     │ Confidence: 65%                                                         │ │
│     │ Context: Auth service for multi-tenant SaaS                             │ │
│     └─────────────────────────────────────────────────────────────────────────┘ │
│       │                                                                          │
│       ▼                                                                          │
│  3. GitHub Action detects `/human:` prefix → sends to Slack                      │
│     ┌─────────────────────────────────────────────────────────────────────────┐ │
│     │ #farmercode-escalations                                                 │ │
│     │ 🤖 Duc needs input on issue #42                                         │ │
│     │ Q: Should this service use JWT or sessions?                             │ │
│     │ Reply with: /duc <your answer>                                          │ │
│     └─────────────────────────────────────────────────────────────────────────┘ │
│       │                                                                          │
│       ▼                                                                          │
│  4. Human replies in Slack: "/duc Use JWT for stateless auth"                    │
│       │                                                                          │
│       ▼                                                                          │
│  5. Slack bot posts human's reply as GitHub comment:                             │
│     ┌─────────────────────────────────────────────────────────────────────────┐ │
│     │ /duc Use JWT for stateless auth. Implement token refresh.               │ │
│     │ — @john.smith via Slack                                                 │ │
│     └─────────────────────────────────────────────────────────────────────────┘ │
│       │                                                                          │
│       ▼                                                                          │
│  6. Duc (polling) sees comment starting with `/duc` → processes response         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Agent Polling Logic:**

Each agent polls GitHub for comments prefixed with their name:

```python
class AgentRuntime:
    async def poll_for_human_response(
        self,
        issue_number: int,
        timeout: timedelta,
    ) -> HumanResponse | None:
        """Poll for human response addressed to this agent."""
        prefix = f"/{self.agent_name}"  # e.g., "/duc", "/veuve", "/baron"
        deadline = datetime.now() + timeout

        while datetime.now() < deadline:
            comments = await self.github.get_issue_comments(
                issue=issue_number,
                since=self.escalation_timestamp,
            )

            for comment in comments:
                if comment.body.startswith(prefix):
                    # Extract response (strip prefix and author line)
                    response_text = comment.body[len(prefix):].strip()
                    return HumanResponse(
                        text=response_text,
                        user=comment.user.login,
                        timestamp=comment.created_at,
                    )

            await asyncio.sleep(self.config.poll_interval.total_seconds())

        return None  # Timeout
```

**GitHub Action (escalation-to-slack.yml):**

```yaml
name: Escalation to Slack
on:
  issue_comment:
    types: [created]

jobs:
  notify:
    if: startsWith(github.event.comment.body, '/human:')
    runs-on: ubuntu-latest
    steps:
      - name: Parse escalation
        id: parse
        run: |
          BODY="${{ github.event.comment.body }}"
          QUESTION=$(echo "$BODY" | sed 's|^/human:||')
          AGENT=$(echo "${{ github.event.comment.user.login }}" | sed 's|farmer1st-||')
          echo "question=$QUESTION" >> $GITHUB_OUTPUT
          echo "agent=$AGENT" >> $GITHUB_OUTPUT

      - name: Send to Slack
        uses: slackapi/slack-github-action@v1
        with:
          channel-id: ${{ secrets.SLACK_ESCALATION_CHANNEL }}
          payload: |
            {
              "text": "🤖 ${{ steps.parse.outputs.agent }} needs input on issue #${{ github.event.issue.number }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Question:* ${{ steps.parse.outputs.question }}\n\nReply with: `/${{ steps.parse.outputs.agent }} <your answer>`"
                  }
                }
              ]
            }
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
```

**Slack Bot (posts responses to GitHub):**

```python
@slack_app.event("message")
async def handle_slack_response(event: dict, say):
    """Handle Slack messages that are agent responses."""
    text = event.get("text", "")

    # Check if message is addressed to an agent (e.g., "/duc ...")
    agent_prefixes = ["/duc", "/veuve", "/baron", "/marie", "/dede", "/gus"]
    matching_prefix = next((p for p in agent_prefixes if text.startswith(p)), None)

    if not matching_prefix:
        return  # Not an agent response

    # Find the active escalation for this agent
    escalation = await db.get_active_escalation(agent=matching_prefix[1:])
    if not escalation:
        await say(f"No active escalation for {matching_prefix}")
        return

    # Post response to GitHub
    user_info = await slack_app.client.users_info(user=event["user"])
    username = user_info["user"]["real_name"]

    await github.post_comment(
        issue=escalation.issue_number,
        body=f"{text}\n— @{username} via Slack"
    )

    await say(f"✅ Response posted to GitHub issue #{escalation.issue_number}")
```

**Why This Design?**

| Aspect | Benefit |
|--------|---------|
| GitHub as source of truth | All escalations and responses are in issue history |
| Agent-prefixed responses | Multiple agents can have concurrent escalations on same issue |
| Slack for notifications | Humans get real-time alerts, can respond from mobile |
| Polling (v1) | Simple, no webhook infrastructure needed |

---

## 7. GitHub Integration

### 7.1 Issue Structure

Each feature creates a GitHub issue hierarchy:

```
Issue #42: [Feature] User Authentication
├── Sub-issue #43: [Baron] Spec, Plan, Tasks
├── Sub-issue #44: [Duc] Architecture Review
├── Sub-issue #45: [Marie] Test Strategy
├── Sub-issue #46: [Dede] Implementation
└── Sub-issue #47: [Reviewer] Code Review
```

### 7.2 GitHub Apps Per Agent

Each agent is a separate GitHub App:

| Agent | GitHub App | Permissions |
|-------|------------|-------------|
| Baron | `farmer1st-baron` | Issues: write, Contents: write |
| Duc | `farmer1st-duc` | Issues: write |
| Marie | `farmer1st-marie` | Issues: write, Contents: write, Checks: write |
| Dede | `farmer1st-dede` | Issues: write, Contents: write, PRs: write |
| Reviewer | `farmer1st-reviewer` | Issues: write, PRs: write |

This allows each agent to post comments under their own identity for audit purposes.

### 7.3 Worktree Management

```python
async def create_worktree(repo: str, branch: str, path: str):
    """Create a git worktree for a feature."""

    # Clone if not exists
    repo_path = f"/repos/{repo.replace('/', '-')}"
    if not os.path.exists(repo_path):
        await run(f"git clone git@github.com:{repo}.git {repo_path}")

    # Fetch latest
    await run(f"git -C {repo_path} fetch origin")

    # Create worktree
    await run(f"git -C {repo_path} worktree add {path} -b {branch}")

    return path

async def cleanup_worktree(path: str):
    """Remove worktree and optionally archive."""
    # Archive conversations for training
    await archive_conversations(path)

    # Remove worktree
    repo_path = get_repo_path(path)
    await run(f"git -C {repo_path} worktree remove {path}")
```

### 7.4 Git State Validation

When an agent receives a task, it validates the git state before proceeding. This ensures:

- **Correctness**: Agent works on expected commit, not stale state
- **Efficiency**: Same agent doing multiple phases skips unnecessary fetches
- **Robustness**: Pod crash/restart recovers to correct state
- **Safety**: Detects corruption, race conditions, or unexpected changes

**The Pattern:**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Git State Validation Flow                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Orchestrator calls agent:                                                       │
│    invoke(skill="specify.plan", expected_commit_sha="abc123")                   │
│                         │                                                        │
│                         ▼                                                        │
│  Agent checks: current HEAD == expected_sha?                                     │
│                         │                                                        │
│           ┌─────────────┴─────────────┐                                          │
│           │                           │                                          │
│           ▼ YES                       ▼ NO                                       │
│  Skip fetch, proceed          Fetch from origin                                  │
│  (common for Baron            Checkout expected_sha                              │
│   doing SPECIFY→PLAN→TASKS)           │                                          │
│           │                           ▼                                          │
│           │               Validate: HEAD == expected_sha?                        │
│           │                           │                                          │
│           │              ┌────────────┴────────────┐                             │
│           │              │                         │                             │
│           │              ▼ YES                     ▼ NO                          │
│           │         Proceed                   REJECT TASK                        │
│           │              │                    (GitStateError)                    │
│           │              │                         │                             │
│           └──────────────┴─────────────────────────┘                             │
│                         │                                                        │
│                         ▼                                                        │
│              Execute task, commit result                                         │
│              Return new_commit_sha to orchestrator                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Agent Implementation:**

```python
class AgentRuntime:
    async def handle_task(self, task: AgentTask) -> PhaseResult:
        """Handle incoming task with git state validation."""
        expected_sha = task.expected_commit_sha

        # Check current state
        current_sha = await self.git.rev_parse("HEAD")

        if current_sha == expected_sha:
            # Already at correct state (same agent continuing, e.g., Baron SPECIFY→PLAN)
            logger.debug(f"Already at expected SHA {expected_sha[:8]}, skipping fetch")
        else:
            # Need to sync - different agent or pod restarted
            logger.info(f"At {current_sha[:8]}, need {expected_sha[:8]}, fetching...")
            await self.git.fetch("origin")
            await self.git.checkout(expected_sha)

            # Validate after fetch
            actual_sha = await self.git.rev_parse("HEAD")
            if actual_sha != expected_sha:
                # Something is wrong - reject immediately
                raise GitStateError(
                    f"Expected SHA {expected_sha} but got {actual_sha} after fetch. "
                    "Possible causes: force push, branch deleted, or fetch failed."
                )

        # Proceed with task
        result = await self.execute_skill(task.skill, task.context)

        # Commit and push
        new_sha = await self.git.commit_and_push(
            message=f"[{self.agent_name}] {task.skill}: {task.summary}",
            idempotency_key=task.idempotency_key,
        )

        return PhaseResult(
            status="completed",
            commit_sha=new_sha,
            confidence=result.confidence,
            artifacts=result.artifacts,
        )
```

**Orchestrator Side:**

```python
class IssueOrchestrator:
    async def _execute_phase(self, phase: Phase) -> PhaseResult:
        """Execute a phase, passing expected commit SHA."""
        state = await self.projection.get_state(self.issue_id)

        # For first phase, use branch HEAD; otherwise use last phase's commit
        if state.last_commit_sha:
            expected_sha = state.last_commit_sha
        else:
            expected_sha = await self.git.get_branch_head(self.branch_name)

        return await self.agent_client.invoke(
            agent=phase.agent,
            skill=phase.skill,
            context={
                "issue_id": self.issue_id,
                "expected_commit_sha": expected_sha,
                "issue_context": state.issue_context,
                ...
            }
        )
```

**Scenarios:**

| Scenario | current_sha | expected_sha | Action |
|----------|-------------|--------------|--------|
| Baron continues (SPECIFY→PLAN) | abc123 | abc123 | Skip fetch, proceed |
| Duc starts after Baron | xyz789 | abc123 | Fetch, checkout, proceed |
| Pod crashed, restarted | (empty) | abc123 | Fetch, checkout, proceed |
| Someone force-pushed | def456 | abc123 | Fetch, **still def456** → REJECT |
| Network issue | abc123 | abc123 | Skip fetch (lucky), proceed |

**Error Handling:**

When `GitStateError` is raised, the orchestrator records a `PhaseFailed` event and stops
the workflow. This requires human investigation — the git state is inconsistent with what
the workflow expects.

### 7.5 Release and Deployment Flow

After code passes VERIFY phase and PR is merged to main, features flow through Kustomize
overlays for deployment. This enables feature-scoped rollback and clear promotion gates.

**GitOps Structure** (see Section 1.2 for full monorepo layout):

```
infra/k8s/
├── base/                               # Shared manifests (all environments)
│   ├── user-management/
│   │   ├── auth-service/
│   │   │   ├── deployment.yaml         # image: ${AUTH_SERVICE_IMAGE}
│   │   │   ├── service.yaml
│   │   │   └── kustomization.yaml
│   │   └── profile-service/
│   │       └── ...
│   └── kustomization.yaml
│
└── overlays/                           # Environment-specific
    ├── dev/
    │   ├── kustomization.yaml          # patches, image tags for dev
    │   └── patches/
    │       └── auth-service-image.yaml # image: ghcr.io/.../auth-service:sha-abc123
    ├── staging/
    │   └── ...
    └── prod/
        └── ...
```

**ArgoCD Application per Environment:**

```yaml
# ArgoCD watches different overlay paths
- name: myapp-dev
  source:
    path: infra/k8s/overlays/dev
  destination:
    namespace: myapp-dev

- name: myapp-staging
  source:
    path: infra/k8s/overlays/staging
  destination:
    namespace: myapp-staging

- name: myapp-prod
  source:
    path: infra/k8s/overlays/prod
  destination:
    namespace: myapp-prod
```

**Release Lifecycle:**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Feature #42 Release Lifecycle                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. Code Development (feature branch)                                            │
│     └── Branch: feature/42-user-avatars                                          │
│         ├── apps/web/src/Avatar.tsx (changed)                                    │
│         ├── services/user-management/profile-service/src/avatar.py (changed)    │
│         └── services/payments/ (unchanged)                                       │
│                                                                                  │
│  2. Code PR Merged to Main                                                       │
│     └── CI triggers:                                                             │
│         ├── Build web:sha-abc123 (new)                                           │
│         ├── Build profile-service:sha-def456 (new)                               │
│         └── Skip payments services (no changes)                                  │
│                                                                                  │
│  3. Deploy PR for Dev                                                            │
│     └── Branch: deploy/42-to-dev (from main)                                     │
│         └── Changes in infra/k8s/overlays/dev/:                                  │
│             ├── kustomization.yaml (update image tags)                           │
│             │   images:                                                          │
│             │     - name: web                                                    │
│             │       newTag: sha-abc123                                           │
│             │     - name: profile-service                                        │
│             │       newTag: sha-def456                                           │
│                                                                                  │
│     └── Merge to main → ArgoCD syncs dev overlay → Only changed services deploy │
│         (payments unchanged, ArgoCD does nothing to it)                          │
│                                                                                  │
│  4. Promote to Staging (after dev validation)                                    │
│     └── Branch: deploy/42-to-staging (from main)                                 │
│         └── Changes in infra/k8s/overlays/staging/:                              │
│             └── Same image tags as dev (sha-abc123, sha-def456)                  │
│                                                                                  │
│     └── Merge to main → ArgoCD syncs staging overlay                             │
│                                                                                  │
│  5. Promote to Prod (after staging validation)                                   │
│     └── Branch: deploy/42-to-prod (from main)                                    │
│         └── Changes in infra/k8s/overlays/prod/:                                 │
│             └── Same image tags                                                  │
│                                                                                  │
│     └── Merge to main → ArgoCD syncs prod overlay → Production deployment        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**ArgoCD Behavior:**

ArgoCD compares desired state (git) vs actual state (cluster). When an overlay update only
changes web and profile-service image tags:

| Service | Manifest Changed? | ArgoCD Action |
|---------|-------------------|---------------|
| web | Yes (new image tag) | Redeploy |
| profile-service | Yes (new image tag) | Redeploy |
| auth-service | No | No action |
| payment-service | No | No action |

This means:
- **Deployment is surgical** — only affected services redeploy
- **Rollback is feature-scoped** — reverting the overlay changes only affects services that were part of that feature

**Deployment Tracking (DynamoDB):**

```python
@dataclass
class FeatureDeployment:
    """Track what's deployed where for rollback capability."""
    issue_id: str              # "42"
    environment: str           # "dev", "staging", "prod"
    commit_sha: str            # Commit on main that updated the overlay
    previous_commit_sha: str   # For easy rollback
    overlay_path: str          # "infra/k8s/overlays/dev"
    services_changed: list[str]  # ["web", "profile-service"]
    image_tags: dict[str, str]  # {"web": "sha-abc123", "profile-service": "sha-def456"}
    deployed_at: datetime
    deployed_by: str           # "gus" (agent) or "human:@john"
```

**DynamoDB Schema:**

```
PK                     SK                              Attributes
─────────────────────────────────────────────────────────────────
deploy#42             env#dev                         {commit_sha, overlay_path, services, images, ...}
deploy#42             env#staging                     {commit_sha, overlay_path, services, images, ...}
deploy#42             env#prod                        {commit_sha, overlay_path, services, images, ...}
deploy#43             env#dev                         {...}
```

**Rollback Flow:**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Rollback Feature #42 from Dev                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Human/Agent: "/rollback feature #42 from dev"                                   │
│       │                                                                          │
│       ▼                                                                          │
│  Gus looks up deployment record:                                                 │
│    - commit_sha: "abc123"                                                        │
│    - previous_commit_sha: "xyz789"                                               │
│    - overlay_path: "infra/k8s/overlays/dev"                                      │
│    - services_changed: ["web", "profile-service"]                                │
│       │                                                                          │
│       ▼                                                                          │
│  Gus creates revert PR:                                                          │
│    Branch: rollback/42-from-dev (from main)                                      │
│    Changes: Revert image tags in infra/k8s/overlays/dev/kustomization.yaml       │
│       │                                                                          │
│       ▼                                                                          │
│  Merge to main → ArgoCD syncs dev overlay                                        │
│       │                                                                          │
│       ▼                                                                          │
│  Only web and profile-service roll back to previous versions                     │
│  (auth-service, payments unaffected — weren't part of feature #42)               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Kustomize Image Override Example:**

```yaml
# infra/k8s/overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

images:
  # Feature #42 deployment
  - name: web
    newName: ghcr.io/farmer1st/myapp-web
    newTag: sha-abc123
  - name: profile-service
    newName: ghcr.io/farmer1st/myapp-profile-service
    newTag: sha-def456
  # Other services at their current versions
  - name: auth-service
    newName: ghcr.io/farmer1st/myapp-auth-service
    newTag: sha-older123
```

**Why This Design:**

| Aspect | Benefit |
|--------|---------|
| **PRs for overlay changes** | Audit trail, review, easy revert (not direct commits) |
| **Kustomize overlays** | DRY base manifests, env-specific patches |
| **Single main branch** | All config on main, ArgoCD watches different paths |
| **Feature-scoped deployment** | Only affected services deploy (ArgoCD is smart) |
| **Feature-scoped rollback** | Revert overlay changes without affecting other features |
| **Immutable image tags** | Same sha-abc123 flows dev → staging → prod |
| **Deployment tracking** | Know exactly what's where, enable safe rollback |

**Gus Agent Role:**

The Gus (DevOps) agent handles all release operations:

| Phase | Gus's Actions |
|-------|---------------|
| RELEASE_DEV | Update `infra/k8s/overlays/dev/` with new image tags, create PR |
| RELEASE_STAGING | Update `infra/k8s/overlays/staging/` with same tags, create PR |
| RELEASE_PROD | Update `infra/k8s/overlays/prod/` with same tags, create PR |
| Rollback | Look up deployment record, revert overlay changes via PR |

**Promotion Triggers:**

| Trigger | Action |
|---------|--------|
| PR merge to main (code) | Gus creates deploy PR updating `overlays/dev/` (automatic) |
| Human approval | Gus creates deploy PR updating `overlays/staging/` |
| Human approval | Gus creates deploy PR updating `overlays/prod/` |
| Rollback request | Gus creates revert PR for target overlay |

**Terraform vs GitOps Separation:**

| Change Type | Location | Approval | Applied By |
|-------------|----------|----------|------------|
| App code | `apps/`, `services/` | Code review | CI/CD |
| K8s manifests | `infra/k8s/overlays/` | Deploy PR | ArgoCD |
| Infrastructure | `infra/terraform/` | Separate PR + human | Terraform (Atlantis or manual) |

Terraform changes (VPC, RDS, EKS) follow a separate approval workflow and are not auto-applied.
This separation ensures infrastructure changes get appropriate scrutiny.

---

## 8. Persistence (DynamoDB)

### 8.1 Single-Table Design with Event Store

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        DynamoDB Table: farmercode                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  PK                      SK                              Attributes              │
│  ───────────────────────────────────────────────────────────────────────────    │
│                                                                                  │
│  # Events (append-only, immutable) - PRIMARY DATA                                │
│  # SK format: event#{version} — version-only for uniqueness, timestamp as attr  │
│  issue#auth-123        event#00000001  {type: WorkflowCreated, ts: 2024-01-08T10:00:00}
│  issue#auth-123        event#00000002  {type: PhaseStarted, ts: 2024-01-08T10:00:01}
│  issue#auth-123        event#00000003  {type: AgentInvoked, ts: 2024-01-08T10:05:32}
│  issue#auth-123        event#00000004  {type: CommitCreated, ts: 2024-01-08T10:05:45}
│  issue#auth-123        event#00000005  {type: PhaseCompleted, ts: 2024-01-08T10:05:46}
│  issue#auth-123        event#00000006  {type: FeedbackRequested, ts: 2024-01-08T10:47:30}
│  ...                                                                             │
│                                                                                  │
│  # Projections (computed views, can be rebuilt from events)                      │
│  issue#auth-123        projection#current_state        {phase, status, last_sha}
│  issue#auth-123        projection#timeline             {phases: [...]}        │
│  issue#auth-123        projection#metrics              {tokens, duration, ...}│
│                                                                                  │
│  # Conversations                                                                 │
│  issue#auth-123        conversation#baron#001          messages[]             │
│  issue#auth-123        conversation#duc#002            messages[]             │
│                                                                                  │
│  # Templates                                                                     │
│  template#sdlc-standard  metadata                        phases[], transitions[]│
│                                                                                  │
│  GSI1 (status-index):                                                           │
│  GSI1PK=status           GSI1SK=created_at               For kanban queries     │
│                                                                                  │
│  GSI2 (event-type-index):                                                       │
│  GSI2PK=event_type       GSI2SK=timestamp                For "show all feedback"│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**

- **Events are immutable** — append-only, never updated or deleted
- **Projections are computed** — can be rebuilt from events at any time
- **Version in SK** — enables lexicographic sorting and range queries
- **GSI for analytics** — query events by type across all features

### 8.2 Access Patterns

| Access Pattern | Key Condition |
|----------------|---------------|
| Get all events for feature | `PK = issue#X, SK begins_with event#` |
| Get events from version N | `PK = issue#X, SK >= event#N` |
| Get current state projection | `PK = issue#X, SK = projection#current_state` |
| List all conversations for feature | `PK = issue#X, SK begins_with conversation#` |
| List features by status (kanban) | `GSI1PK = status, GSI1SK between dates` |
| List all feedback events | `GSI2PK = FeedbackRequested, GSI2SK between dates` |
| Get workflow template | `PK = template#X, SK = metadata` |

### 8.3 Local Development

```yaml
# docker-compose.yaml (or k3d deployment)
services:
  dynamodb-local:
    image: amazon/dynamodb-local
    ports:
      - "8000:8000"
    command: "-jar DynamoDBLocal.jar -sharedDb"
```

```python
# Configuration
import boto3

def get_dynamodb():
    if os.environ.get("LOCAL_DEV"):
        return boto3.resource(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
    else:
        return boto3.resource('dynamodb', region_name='us-east-1')
```

### 8.4 Schema Evolution Strategy

DynamoDB is schemaless, but our application layer has implicit schemas. Strategy for
handling evolution:

**1. Event Schema Versioning:**

Events are immutable, so we version the schema within the event data:

```python
@dataclass
class PhaseCompleted(WorkflowEvent):
    schema_version: int = 2  # Increment when structure changes
    phase: str
    agent: str
    confidence: int
    # v2 additions:
    tokens_used: int = 0      # New field with default
    duration_ms: int = 0      # New field with default
```

**2. Projection Rebuilding:**

Since projections are derived from events, schema changes only affect the projection
code. Old events are transformed on read:

```python
def _apply_event(self, state: WorkflowState, event: WorkflowEvent) -> WorkflowState:
    match event:
        case PhaseCompleted():
            # Handle both v1 and v2 events
            tokens = getattr(event, 'tokens_used', 0)  # Default for v1 events
            ...
```

**3. Migration Script Pattern:**

For breaking changes, run a one-time migration that re-serializes events:

```bash
# migration_20260115_add_tokens.py
# - Read all events
# - Add missing fields with defaults
# - Write back (same PK/SK, just updated data)
```

**4. GSI Changes:**

Adding new GSIs is safe (background build). Removing GSIs requires application
changes first (stop querying the index before deletion).

| Change Type | Strategy |
|-------------|----------|
| Add optional field | Default in code, no migration needed |
| Add required field | Migration script to backfill |
| Add GSI | Create async, no downtime |
| Rename field | Dual-read period, then migration |
| Remove field | Stop reading first, then ignore |

---

## 9. Event Sourcing

### 9.1 Why Event Sourcing?

The state-based persistence model (storing `phase: planning`) has critical limitations:

| Issue | Impact |
|-------|--------|
| Lost history | "How did we get to this state?" is unanswerable |
| No replay | Can't debug by replaying what happened |
| Recovery gaps | If crash at T=5, what was state at T=4? |
| Audit weakness | Compliance needs full trail, not snapshots |
| Debugging nightmare | "Why did Baron produce this spec?" — no context |

**Event sourcing** stores the sequence of events that produced the state, enabling full replay and recovery:

```
State = fold(initialState, events)
```

### 9.2 Event Schema

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

@dataclass
class WorkflowEvent:
    event_id: UUID
    issue_id: str
    timestamp: datetime
    version: int

@dataclass
class WorkflowCreated(WorkflowEvent):
    repo: str
    branch: str
    issue_number: int
    requested_by: str
    agent_versions: dict[str, str]

@dataclass
class PhaseStarted(WorkflowEvent):
    phase: str
    agent: str
    agent_version: str
    input_context: dict

@dataclass
class PhaseCompleted(WorkflowEvent):
    phase: str
    agent: str
    confidence: int
    artifacts_created: list[str]
    commit_sha: str
    tokens_used: int
    duration_ms: int

@dataclass
class PhaseFailed(WorkflowEvent):
    phase: str
    agent: str
    error_code: str
    error_message: str
    retryable: bool

@dataclass
class PhaseInterrupted(WorkflowEvent):
    """Logged when a phase is interrupted by pod termination (Section 11.7)."""
    phase: str
    agent: str
    reason: str  # "pod_termination", "timeout", etc.

@dataclass
class EscalationRequested(WorkflowEvent):
    agent: str
    question: str
    confidence: int
    options: list[str]
    github_comment_id: int

@dataclass
class EscalationResolved(WorkflowEvent):
    agent: str
    human_response: str
    responded_by: str
    response_time_ms: int

@dataclass
class AgentConsulted(WorkflowEvent):
    """Logged when one agent consults another via A2A (Section 3.7)."""
    from_agent: str          # Who asked
    to_agent: str            # Who answered
    skill: str               # A2A skill invoked (e.g., "clarify.architecture")
    question: str            # The question asked
    response: str            # The response received
    confidence: int          # Consulted agent's confidence (0-100)
    escalated_to_human: bool # Did the consulted agent escalate?
    tokens_used: int
    duration_ms: int

@dataclass
class FeedbackRequested(WorkflowEvent):
    from_phase: str
    to_phase: str
    reason: str
    feedback_details: dict

@dataclass
class CommitCreated(WorkflowEvent):
    commit_sha: str
    files_changed: list[str]
    agent: str
    message: str

@dataclass
class WorkflowCompleted(WorkflowEvent):
    total_duration_ms: int
    total_tokens: int
    phases_completed: int
    escalations_count: int
    feedback_loops_count: int

@dataclass
class WorkflowFailed(WorkflowEvent):
    reason: str
    failed_phase: str
    recoverable: bool
```

### 9.3 Event Store Implementation

```python
from botocore.exceptions import ClientError

class EventStore:
    """Append-only event store backed by DynamoDB with optimistic concurrency."""

    MAX_APPEND_RETRIES = 5

    async def append(self, event: WorkflowEvent) -> int:
        """
        Append event with optimistic concurrency control.

        Uses retry loop to handle race conditions where two processes attempt
        to write the same version simultaneously. DynamoDB's conditional write
        ensures exactly one succeeds; the other retries with an updated version.
        """
        for attempt in range(self.MAX_APPEND_RETRIES):
            current_version = await self._get_current_version(event.issue_id)
            new_version = current_version + 1

            try:
                await self.table.put_item(
                    Item={
                        'PK': f'issue#{event.issue_id}',
                        'SK': f'event#{str(new_version).zfill(8)}',
                        'event_type': event.__class__.__name__,
                        'version': new_version,
                        'timestamp': event.timestamp.isoformat(),
                        'data': self._serialize_event(event),
                    },
                    ConditionExpression='attribute_not_exists(SK)'
                )
                return new_version
            except ClientError as e:
                if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    # Another process wrote first — retry with fresh version
                    if attempt < self.MAX_APPEND_RETRIES - 1:
                        continue
                    raise EventStoreConflictError(
                        f"Failed to append event after {self.MAX_APPEND_RETRIES} attempts"
                    ) from e
                raise

        raise EventStoreConflictError("Unreachable: retry loop exhausted")

    async def _get_current_version(self, issue_id: str) -> int:
        """Get the latest event version for an issue."""
        response = await self.table.query(
            KeyConditionExpression=Key('PK').eq(f'issue#{issue_id}') &
                                  Key('SK').begins_with('event#'),
            ScanIndexForward=False,  # Descending order
            Limit=1
        )
        if response['Items']:
            return response['Items'][0]['version']
        return 0

    async def get_events(
        self,
        issue_id: str,
        from_version: int = 0,
        event_types: list[str] | None = None
    ) -> list[WorkflowEvent]:
        """Retrieve events for replay or projection.

        Args:
            issue_id: The issue to get events for
            from_version: Only return events with version > from_version
            event_types: Optional list of event type names to filter by
        """
        # Build key condition - use version range if from_version specified
        if from_version > 0:
            key_condition = (
                Key('PK').eq(f'issue#{issue_id}') &
                Key('SK').gt(f'event#{str(from_version).zfill(8)}')
            )
        else:
            key_condition = (
                Key('PK').eq(f'issue#{issue_id}') &
                Key('SK').begins_with('event#')
            )

        response = await self.table.query(KeyConditionExpression=key_condition)
        events = [self._deserialize_event(item) for item in response['Items']]

        # Filter by event types if specified
        if event_types:
            events = [e for e in events if e.__class__.__name__ in event_types]

        return events
```

> **Optimistic Concurrency:** The append operation uses a retry loop to handle race
> conditions. If two processes try to write the same version, DynamoDB's conditional
> write ensures exactly one succeeds. The losing process catches `ConditionalCheckFailedException`,
> re-reads the current version, and retries. After 5 failed attempts, it raises an error
> for investigation (indicates severe contention or a bug).

### 9.4 State Projection

```python
@dataclass
class WorkflowState:
    """Current state computed from events."""
    issue_id: str
    status: Literal["pending", "running", "paused", "completed", "failed"]
    current_phase: str | None
    phases_completed: list[str]
    last_commit_sha: str | None
    pending_escalation: dict | None
    pending_feedback: dict | None
    total_tokens: int
    # Error fields (populated from WorkflowFailed event)
    error: str | None = None
    error_code: str | None = None
    failed_phase: str | None = None

class WorkflowProjection:
    """Projects events into current state."""

    async def get_state(self, issue_id: str) -> WorkflowState:
        events = await self.event_store.get_events(issue_id)
        state = WorkflowState.initial(issue_id)
        for event in events:
            state = self._apply_event(state, event)
        return state

    def _apply_event(self, state: WorkflowState, event: WorkflowEvent) -> WorkflowState:
        match event:
            case PhaseCompleted():
                return replace(state,
                    phases_completed=[*state.phases_completed, event.phase],
                    last_commit_sha=event.commit_sha,
                    total_tokens=state.total_tokens + event.tokens_used,
                )
            case EscalationRequested():
                return replace(state, status="paused", pending_escalation={...})
            case FeedbackRequested():
                return replace(state, pending_feedback={...})
            case WorkflowFailed():
                return replace(state,
                    status="failed",
                    error=event.reason,
                    error_code=getattr(event, 'error_code', None),
                    failed_phase=event.failed_phase,
                )
            case WorkflowCompleted():
                return replace(state, status="completed")
            # ... other event handlers
```

### 9.5 Crash Recovery

```python
class IssueOrchestrator:
    async def run(self):
        """Run workflow with automatic recovery."""
        state = await self.projection.get_state(self.issue_id)

        if state.status == "completed":
            return

        if state.pending_escalation:
            await self._wait_for_escalation(state.pending_escalation)
            state = await self.projection.get_state(self.issue_id)

        phases_to_run = [p for p in self.phases if p not in state.phases_completed]
        for phase in phases_to_run:
            await self._run_phase(phase)
```

### 9.6 State Model Clarification

There are three distinct "states" in the system:

| State Type | Location | Purpose | Replay? |
|------------|----------|---------|---------|
| **Workflow position** | DynamoDB events + projection | "Where are we in the pipeline?" | Yes (for audit) |
| **Work product** | Git worktree | "What did agents produce?" | No (AI non-deterministic) |
| **Conversation history** | DynamoDB conversations | "What was discussed?" | No (context only) |

**Key insight:** Event replay reconstructs **workflow position** (which phases completed,
what confidence scores were), not the actual **artifacts** (code, specs). The artifacts
live in Git, and replaying events wouldn't reproduce them anyway because AI outputs are
non-deterministic.

**Projection vs Replay:**
- **Normal operations:** Read `projection#current_state` directly (fast)
- **Audit/debugging:** Replay events to see full history (slow but complete)

The projection is updated after each event, so there's no need to replay events for
normal workflow operations.

---

## 10. Feedback Loops

### 10.1 The Problem with Linear Pipelines

A linear workflow assumes everything succeeds first time:

```
Baron(specify) → Baron(plan) → Baron(tasks) → Marie(tests) → Dede(code) → Marie(verify) → Review → Done
```

In reality, software development is iterative:

| Scenario | Required Handling |
|----------|-------------------|
| Reviewer finds security issue | Loop back to Dede or Baron |
| Tests fail in verify phase | Loop back to Dede |
| Dede discovers spec is ambiguous | Loop back to Baron |
| Plan is too complex mid-implementation | Revise plan |

### 10.2 State Machine Model

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                                                                                │
│   SPECIFY ──▶ PLAN ──▶ TASKS ──▶ TEST_DESIGN ──▶ IMPLEMENT ──▶ VERIFY ──▶ REVIEW
│      ▲          ▲                                    ▲           │         │   │
│      │          │         feedback:plan_infeasible   │           │         │   │
│      │          └────────────────────────────────────┤           │         │   │
│      │                                               │           │         │   │
│      │          feedback:spec_ambiguity              │           │         │   │
│      └───────────────────────────────────────────────┤           │         │   │
│                                                      │           │         │   │
│                         feedback:test_failure        │           │         │   │
│                         ─────────────────────────────┴───────────┘         │   │
│                                                                            │   │
│                         feedback:minor_changes                             │   │
│                         ◀──────────────────────────────────────────────────┘   │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 Workflow Definition with Feedback Edges

```python
class Phase(str, Enum):
    SPECIFY = "specify"
    PLAN = "plan"
    TASKS = "tasks"
    TEST_DESIGN = "test_design"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    DOCS_QA = "docs_qa"
    REVIEW = "review"
    RELEASE_STAGING = "release_staging"
    RELEASE_PROD = "release_prod"
    RETRO = "retro"
    DONE = "done"

@dataclass
class Transition:
    from_phase: Phase
    to_phase: Phase
    trigger: str  # "success", "feedback:test_failure", etc.
    condition: Callable | None = None
    priority: int = 0

SDLC_WORKFLOW = WorkflowDefinition(
    transitions=[
        # Happy path (matches Section 3.5 diagram)
        Transition(Phase.SPECIFY, Phase.PLAN, "success"),
        Transition(Phase.PLAN, Phase.TASKS, "success"),
        Transition(Phase.TASKS, Phase.TEST_DESIGN, "success"),
        Transition(Phase.TEST_DESIGN, Phase.IMPLEMENT, "success"),
        Transition(Phase.IMPLEMENT, Phase.VERIFY, "success"),
        Transition(Phase.VERIFY, Phase.DOCS_QA, "success"),
        Transition(Phase.DOCS_QA, Phase.REVIEW, "success"),
        Transition(Phase.REVIEW, Phase.RELEASE_STAGING, "success"),
        Transition(Phase.RELEASE_STAGING, Phase.RELEASE_PROD, "success"),
        Transition(Phase.RELEASE_PROD, Phase.RETRO, "success"),
        Transition(Phase.RETRO, Phase.DONE, "success"),

        # Feedback loops (from Section 3.5)
        Transition(Phase.REVIEW, Phase.IMPLEMENT, "feedback:minor_changes", priority=10),
        Transition(Phase.REVIEW, Phase.PLAN, "feedback:architectural_rework", priority=10),
        Transition(Phase.VERIFY, Phase.IMPLEMENT, "feedback:test_failure", priority=10),
        Transition(Phase.DOCS_QA, Phase.IMPLEMENT, "feedback:docs_inconsistent", priority=10),
        Transition(Phase.IMPLEMENT, Phase.SPECIFY, "feedback:spec_ambiguity", priority=10),
        Transition(Phase.IMPLEMENT, Phase.PLAN, "feedback:plan_infeasible", priority=10),
    ],
    max_feedback_loops=5,
)
```

### 10.4 Infinite Loop Protection

Loop counts are derived from the event store (FeedbackRequested events), not stored
in memory. This ensures counts survive pod restarts and are always accurate.

```python
class FeedbackLoopProtection:
    def __init__(
        self,
        event_store: EventStore,
        issue_id: str,
        max_total_loops: int = 5,
        max_same_transition: int = 2,
    ):
        self.event_store = event_store
        self.issue_id = issue_id
        self.max_total_loops = max_total_loops
        self.max_same_transition = max_same_transition

    async def check_transition(self, from_phase: str, to_phase: str, reason: str) -> bool:
        """Check if transition is allowed based on event history."""
        # Count from events — survives pod restarts
        feedback_events = await self.event_store.get_events(
            self.issue_id,
            event_types=["FeedbackRequested"]
        )

        total_loops = len(feedback_events)
        if total_loops >= self.max_total_loops:
            return False

        transition_key = f"{from_phase}->{to_phase}:{reason}"
        same_transition_count = sum(
            1 for e in feedback_events
            if f"{e.from_phase}->{e.to_phase}:{e.reason}" == transition_key
        )
        if same_transition_count >= self.max_same_transition:
            return False

        return True
```

> **Why derive from events?** The orchestrator pod may restart during a long-running
> workflow. By counting FeedbackRequested events from the event store, we ensure loop
> protection is crash-consistent. The event store is the single source of truth.

### 10.5 GitHub Notifications

```python
async def post_feedback_comment(issue_number: int, from_phase: str, to_phase: str, result: PhaseResult):
    comment = f"""
## 🔄 Feedback Loop Detected

**From:** `{from_phase}` → **To:** `{to_phase}`
**Reason:** {result.feedback_type}

### Suggested Changes
{chr(10).join(f"- {change}" for change in result.suggested_changes)}

*Workflow is automatically retrying.*
"""
    await github.post_comment(issue_number, comment)
```

---

## 11. Resilience Patterns

### 11.1 Git Optimistic Lock (Race Condition Handling)

**Problem:** Multiple agents on the same branch can have push conflicts.

**Solution:** Push-rebase-retry loop with idempotency and conflict escalation.

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class GitWorkspaceManager:
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(min=2, max=10))
    async def _push_with_rebase_loop(self, workspace_path: str, branch: str) -> str:
        try:
            await run(f"git -C {workspace_path} push origin HEAD")
        except Exception as e:
            if "non-fast-forward" in str(e):
                await run(f"git -C {workspace_path} fetch origin {branch}")
                try:
                    await run(f"git -C {workspace_path} rebase origin/{branch}")
                except Exception as rebase_error:
                    if "CONFLICT" in str(rebase_error) or "could not apply" in str(rebase_error):
                        # Abort rebase and escalate — agent cannot resolve merge conflicts
                        await run(f"git -C {workspace_path} rebase --abort")
                        raise GitMergeConflictError(
                            f"Merge conflict on {branch}. Human intervention required.",
                            conflicting_files=self._parse_conflict_files(str(rebase_error))
                        )
                    raise
                raise GitPushConflictError("Rebased, retrying...")
            raise
        return (await run(f"git -C {workspace_path} rev-parse HEAD")).stdout.strip()
```

**Merge Conflict Escalation:**

When rebase fails due to actual merge conflicts (not just stale ref), the agent
cannot automatically resolve conflicting changes. The workflow escalates to a human
with the list of conflicting files. The human resolves conflicts manually, and the
workflow resumes from the IMPLEMENT phase.

### 11.2 Stop-and-Go Workflow (Future Enhancement)

> **Note:** This is a **future enhancement**. v1 uses the simpler polling approach
> where pods stay alive during human wait times. See Section 3.4 and 6.1 for v1 behavior.

**Problem:** Jobs waiting for human input waste resources (pods idle for hours/days).

**Solution:** Checkpoint state and exit. Resume with new Job when human responds via webhook.

```
Job 1: Phase 1 → Phase 2 → needs input → CHECKPOINT → EXIT (pod terminates)
                                ↓
                    (hours/days pass, zero resource usage)
                                ↓
                    Human responds via GitHub
                                ↓
                    GitHub webhook triggers API
                                ↓
                    API creates new Job
                                ↓
Job 2: Rehydrate state → Skip 1,2 → Resume Phase 3 → ... → Done
```

**Prerequisites for Stop-and-Go:**
- GitHub webhook handler in the API
- Network connectivity for incoming webhooks (not available in all environments)
- Robust event sourcing (already implemented in v1)

**Implementation sketch (future):**

```python
class IssueOrchestrator:
    async def run(self):
        state = await self.projection.get_state(self.issue_id)

        for phase in phases_to_run:
            result = await self._execute_phase(phase)

            if result.status == "input_required":
                # Future: Checkpoint and exit
                await self._checkpoint_for_human_input(phase, result)
                return OrchestratorResult(status="waiting_human")  # Job exits

            await self.event_store.append(PhaseCompleted(...))


# Webhook handler (future)
@app.post("/webhooks/github/issue-comment")
async def on_issue_comment(payload: GitHubWebhookPayload):
    if is_human_response(payload):
        issue_id = extract_issue_id(payload)
        # Spawn new orchestrator job to resume
        await k8s.create_job(f"orchestrator-{issue_id}-resume")
```

**v1 vs Future comparison:**

| Aspect | v1 (Polling) | Future (Stop-and-Go) |
|--------|--------------|----------------------|
| Pod during wait | Stays alive, polls | Terminates |
| Resource cost | ~$X/hour per waiting feature | $0 during wait |
| Resume trigger | Poll detects response | Webhook creates Job |
| Complexity | Simple | Requires webhook infra |
| When to adopt | Now (v1) | When resource costs matter |

### 11.3 Idempotency Keys

```python
async def commit_and_push(workspace_path: str, message: str, idempotency_key: str):
    # Check if already committed
    existing = await run(f"git log --grep='Idempotency-Key: {idempotency_key}'")
    if existing.stdout.strip():
        return existing.stdout.split()[0]

    full_message = f"{message}\n\nIdempotency-Key: {idempotency_key}"
    await run(f"git commit -m '{full_message}'")
    ...
```

### 11.4 Circuit Breakers

```python
from circuitbreaker import circuit

class AgentClient:
    @circuit(failure_threshold=3, recovery_timeout=60)
    async def invoke(self, agent: str, skill: str, context: dict) -> AgentResponse:
        # Within workflow namespace, use simple names (see Section 5.5)
        response = await httpx.post(f"http://{agent}:8002/a2a", ...)
        return AgentResponse(**response.json())
```

### 11.5 Watchdog for Stale Escalations

A safety net for edge cases where escalations might be missed:

**v1 (Polling):** Catches cases where:
- Orchestrator pod crashed during polling
- Polling loop had a transient failure
- Human responded but orchestrator missed it

**Future (Webhooks):** Catches cases where:
- Webhook delivery failed
- Webhook handler had an error

```python
async def check_stale_escalations():
    """Cron job to catch missed escalation responses."""
    # Find escalations waiting longer than expected
    threshold = datetime.now() - timedelta(hours=self.config.stale_threshold_hours)
    waiting = await dynamodb.query(status="waiting_human", updated_at__lt=threshold)

    for workflow in waiting:
        response = await github.check_for_response(workflow.comment_id)
        if response:
            # v1: Wake up the orchestrator (it may have crashed)
            # Future: Spawn new Job (stop-and-go pattern)
            await resume_workflow(workflow.issue_id, response)
```

### 11.6 Rate Limiting

**External API Protection:**

| API | Rate Limit | Strategy |
|-----|------------|----------|
| Claude API | Per-account limits | Token bucket per agent |
| GitHub API | 5000 req/hr (authenticated) | Shared rate limiter across all agents |

```python
from limits import strategies, storage

# In-memory for local, Redis for cloud
limiter_storage = storage.MemoryStorage()  # or RedisStorage()

class RateLimitedClaudeClient:
    def __init__(self):
        self.limiter = strategies.FixedWindowRateLimiter(limiter_storage)
        # Claude rate limits vary by tier; configure per deployment
        self.rate_limit = parse("100/minute")

    async def invoke(self, prompt: str, **kwargs) -> Response:
        if not self.limiter.hit(self.rate_limit, "claude_api"):
            raise RateLimitExceededError("Claude API rate limit reached")
        return await self._client.invoke(prompt, **kwargs)
```

**Internal A2A Protection:**

Agent-to-agent calls are trusted (internal cluster), but we still protect against
runaway loops or misbehaving agents:

```python
# Per-agent-pair rate limit to detect consultation loops
A2A_RATE_LIMIT = "50/minute"  # Per agent-to-agent pair

async def send_a2a_task(from_agent: str, to_agent: str, task: Task) -> Response:
    key = f"a2a:{from_agent}:{to_agent}"
    if not limiter.hit(A2A_RATE_LIMIT, key):
        logger.warning(f"A2A rate limit: {from_agent} → {to_agent}")
        raise A2ARateLimitError(f"Too many consultations from {from_agent} to {to_agent}")
    return await _send_task(to_agent, task)
```

### 11.7 Graceful Shutdown

When Kubernetes terminates a pod (namespace deletion, rolling update, manual kill), we need
to handle in-flight operations gracefully to avoid data loss.

**The Problem:**

```
SIGTERM received → Pod has 30s (terminationGracePeriodSeconds) → SIGKILL
                   ↓
                   Without handling: Claude API calls abandoned, events not persisted
```

**Solution: SIGTERM Handler**

```python
import signal
import asyncio

class AgentPod:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.active_tasks: set[asyncio.Task] = set()

    def setup_signal_handlers(self):
        """Register SIGTERM handler for graceful shutdown."""
        loop = asyncio.get_event_loop()

        def handle_sigterm():
            logger.info("SIGTERM received, initiating graceful shutdown...")
            self.shutdown_event.set()

        loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
        loop.add_signal_handler(signal.SIGINT, handle_sigterm)

    async def run(self):
        """Main loop with shutdown awareness."""
        self.setup_signal_handlers()

        while not self.shutdown_event.is_set():
            try:
                # Check for work with timeout (allows shutdown check)
                task = await asyncio.wait_for(
                    self.get_next_task(),
                    timeout=5.0
                )
                await self.process_task(task)
            except asyncio.TimeoutError:
                continue  # Loop back to check shutdown_event

        # Graceful shutdown: wait for active tasks
        await self.graceful_shutdown()

    async def graceful_shutdown(self):
        """Complete in-flight work before exiting."""
        if not self.active_tasks:
            logger.info("No active tasks, shutting down immediately")
            return

        logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")

        # Wait up to 25s for tasks (leave 5s buffer before SIGKILL)
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.active_tasks, return_exceptions=True),
                timeout=25.0
            )
            logger.info("All tasks completed, shutting down")
        except asyncio.TimeoutError:
            logger.warning("Shutdown timeout, some tasks may be incomplete")
            # Log which tasks are still running for debugging
            for task in self.active_tasks:
                if not task.done():
                    logger.warning(f"Incomplete task: {task.get_name()}")
```

**Orchestrator Checkpoint on Shutdown:**

The orchestrator records its current state before exiting, enabling recovery on restart:

```python
class IssueOrchestrator:
    async def graceful_shutdown(self):
        """Checkpoint state before shutdown."""
        if self.current_phase_task and not self.current_phase_task.done():
            # Record that we were interrupted mid-phase
            await self.event_store.append(PhaseInterrupted(
                issue_id=self.issue_id,
                phase=self.current_phase,
                agent=self.current_agent,
                reason="pod_termination",
            ))
            logger.info(f"Checkpointed interruption at phase {self.current_phase}")

        # On restart, orchestrator will see PhaseInterrupted and retry the phase
```

**Kubernetes Configuration:**

```yaml
spec:
  terminationGracePeriodSeconds: 30  # Default, adjust if needed
  containers:
    - name: agent
      lifecycle:
        preStop:
          exec:
            command: ["/bin/sh", "-c", "sleep 5"]  # Allow time for SIGTERM handling
```

**What Gets Protected:**

| Operation | Without Graceful Shutdown | With Graceful Shutdown |
|-----------|---------------------------|------------------------|
| Claude API call | Abandoned mid-request | Completes or times out cleanly |
| Event store write | May be lost | Completes before exit |
| Git commit/push | Partial state | Completes or rolls back |
| A2A consultation | Caller hangs | Returns error, caller retries |

---

## 12. Why Custom Workflow Engine

We evaluated [Temporal](https://temporal.io/) but chose a custom event-sourced workflow engine.

### 12.1 Why Not Temporal?

| Factor | Temporal | Custom (our choice) |
|--------|----------|---------------------|
| **Workflow definition** | Code (Python/Go classes) | Data (JSON/YAML in DynamoDB) |
| **AI modification** | Requires code changes, CI, deployment | AI can edit workflow JSON at runtime |
| **Determinism** | Required for replay | Not needed (we don't replay AI outputs) |
| **Ops burden** | Temporal cluster + workers | DynamoDB only |
| **Learning curve** | New paradigm | Standard event sourcing |

### 12.2 The Key Differentiator: Workflow-as-Data

Our workflows are JSON definitions stored in DynamoDB:

```json
{
  "id": "sdlc-standard",
  "phases": ["SPECIFY", "PLAN", "TASKS", "TEST_DESIGN", "IMPLEMENT", "VERIFY", "REVIEW"],
  "transitions": [
    {"from": "SPECIFY", "to": "PLAN", "trigger": "success"},
    {"from": "REVIEW", "to": "IMPLEMENT", "trigger": "feedback:minor_changes"},
    ...
  ],
  "max_feedback_loops": 5
}
```

**Why this matters:**
1. **AI-modifiable**: Baron can adjust the workflow graph mid-execution based on feature complexity
2. **No deployment needed**: Workflow changes don't require CI/CD
3. **Dynamic adaptation**: Skip phases for trivial changes, add phases for complex features
4. **A/B testing**: Run different workflow variants without code changes

### 12.3 Trade-offs Accepted

By choosing custom over Temporal, we accept:
- Building and maintaining event sourcing ourselves
- Building and maintaining checkpointing ourselves
- No built-in visibility UI (we'll build a simpler one)
- No built-in retry policies (we implement with tenacity)

These trade-offs are acceptable because workflow-as-data enables AI agents to participate
in workflow design, which is central to our vision.

---

## 13. Security

### 13.1 Claude Agent SDK Authentication

> **IMPORTANT:** We use the **Claude Agent SDK** which authenticates via **OAuth** (Claude
> Pro/Max subscription), NOT via Anthropic API keys. Do not confuse this with the `anthropic`
> Python package which requires `ANTHROPIC_API_KEY`.

**How it works:**

1. Claude Code CLI stores OAuth tokens in `~/.claude/` after user login
2. The Claude Agent SDK reads these tokens automatically
3. Agent pods mount this config directory as a secret
4. No API keys are needed or used

**Local Development:**

```bash
# 1. Login to Claude Code (one-time setup)
claude login

# 2. Copy OAuth config to k3d secret
kubectl create secret generic claude-oauth-config \
  --from-file=config.json=$HOME/.claude/config.json \
  --from-file=credentials.json=$HOME/.claude/credentials.json
```

**Cloud (EKS):**

For production, the OAuth tokens are stored in AWS Secrets Manager and synced to K8s:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: claude-oauth-config
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: claude-oauth-config
  data:
    - secretKey: config.json
      remoteRef:
        key: farmercode/claude-oauth-config
    - secretKey: credentials.json
      remoteRef:
        key: farmercode/claude-oauth-credentials
```

### 13.2 Credential Manager Service

**The Problem:**

Claude Code CLI expects `credentials.json` on disk and refreshes tokens frequently. With
600+ pods (12 agents × 50 concurrent issues) sharing credentials:

- If each pod has a copy from K8s secret → tokens desync after first refresh
- If Pod A refreshes → Pod B still has stale token → auth fails
- K8s secrets don't auto-update when tokens refresh

**Solution: Central Credential Manager**

A lightweight service that holds the canonical credentials and handles all token refreshes:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      Credential Manager Service                                  │
│                      (Single instance in farmercode namespace)                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Startup:                                                                        │
│    - Load credentials.json from K8s secret (seeded from initial `claude login`) │
│                                                                                  │
│  Background loop (every 5 min):                                                  │
│    - Check if access_token expires within 10 min                                 │
│    - If yes → use refresh_token to get new tokens (mutex-protected)              │
│    - Write updated credentials.json                                              │
│                                                                                  │
│  GET /credentials:                                                               │
│    - Return current credentials.json content                                     │
│    - Pods call this on startup + every 15 min                                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
         ▲           ▲           ▲           ▲
         │           │           │           │
    ┌────┴───┐  ┌────┴───┐  ┌────┴───┐  ┌────┴───┐
    │ Baron  │  │  Duc   │  │ Marie  │  │  ...   │  (600+ pods fetch credentials)
    └────────┘  └────────┘  └────────┘  └────────┘
```

**Timing Configuration:**

| Setting | Value | Reason |
|---------|-------|--------|
| Check interval | 5 min | Catch token expiry early |
| Refresh threshold | 10 min before expiry | Buffer to avoid expired tokens |
| Pod refresh interval | 15 min | Get updates after service refreshes |

**Credential Manager Implementation:**

```python
class CredentialManager:
    CHECK_INTERVAL = timedelta(minutes=5)
    REFRESH_THRESHOLD = timedelta(minutes=10)

    def __init__(self):
        self.credentials_path = "/data/credentials.json"
        self.lock = asyncio.Lock()

    async def refresh_loop(self):
        """Background task - runs continuously."""
        while True:
            await self.refresh_if_needed()
            await asyncio.sleep(self.CHECK_INTERVAL.total_seconds())

    async def refresh_if_needed(self):
        """Check token expiry and refresh if needed."""
        async with self.lock:  # Prevent concurrent refreshes
            creds = self.load_credentials()
            expires_at = self.decode_token_expiry(creds["access_token"])
            time_left = expires_at - datetime.now()

            if time_left < self.REFRESH_THRESHOLD:
                logger.info(f"Token expires in {time_left}, refreshing...")
                new_tokens = await self.refresh_tokens(creds["refresh_token"])
                creds["access_token"] = new_tokens["access_token"]
                if "refresh_token" in new_tokens:  # Handle rotation
                    creds["refresh_token"] = new_tokens["refresh_token"]
                self.save_credentials(creds)
                logger.info("Token refreshed successfully")

    @app.get("/credentials")
    async def get_credentials(self) -> dict:
        """Endpoint for pods to fetch current credentials."""
        return self.load_credentials()

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """Call Claude's OAuth token refresh endpoint."""
        # This replicates what Claude Code CLI does internally
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://auth.anthropic.com/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": CLAUDE_CODE_CLIENT_ID,
                }
            )
            return response.json()
```

**Pod Startup (updated):**

```python
class AgentPod:
    CREDENTIAL_REFRESH_INTERVAL = timedelta(minutes=15)

    async def startup(self):
        # Fetch credentials from central service (not K8s secret)
        await self.refresh_credentials()

        # Schedule periodic refresh
        asyncio.create_task(self.credential_refresh_loop())

        # Continue with normal startup...
        self.config = await fetch_agent_config(...)

    async def credential_refresh_loop(self):
        """Periodically fetch fresh credentials from central service."""
        while True:
            await asyncio.sleep(self.CREDENTIAL_REFRESH_INTERVAL.total_seconds())
            await self.refresh_credentials()

    async def refresh_credentials(self):
        """Fetch credentials from Credential Manager and write to disk."""
        response = await httpx.get("http://credential-manager.farmercode.svc:8080/credentials")
        creds = response.json()
        Path("/home/agent/.claude/credentials.json").write_text(json.dumps(creds))
        logger.debug("Credentials refreshed from central service")
```

**Kubernetes Deployment:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: credential-manager
  namespace: farmercode
spec:
  replicas: 1  # Single instance to avoid refresh conflicts
  selector:
    matchLabels:
      app: credential-manager
  template:
    metadata:
      labels:
        app: credential-manager
    spec:
      containers:
        - name: credential-manager
          image: ghcr.io/farmer1st/credential-manager:latest
          ports:
            - containerPort: 8080
          volumeMounts:
            - name: credentials
              mountPath: /data
      volumes:
        - name: credentials
          secret:
            secretName: claude-oauth-config  # Initial seed
---
apiVersion: v1
kind: Service
metadata:
  name: credential-manager
  namespace: farmercode
spec:
  selector:
    app: credential-manager
  ports:
    - port: 8080
```

**Why Single Instance?**

- Token refresh must be serialized (one refresh at a time)
- Multiple instances would cause race conditions
- Single instance with mutex is simple and reliable
- If it crashes, K8s restarts it; pods retry on next interval

### 13.3 Other Secrets

| Secret | Storage (Local) | Storage (Cloud) | Rotation |
|--------|-----------------|-----------------|----------|
| Claude OAuth config | Credential Manager Service | Credential Manager + AWS Secrets Manager | Automatic (see 13.2) |
| GitHub App keys | `.env` file | AWS Secrets Manager → K8s Secret | Manual, quarterly |
| DynamoDB credentials | Not needed (local) | IAM role (IRSA) | Automatic |

### 13.4 Future Enhancements (v2)

| Enhancement | Purpose |
|-------------|---------|
| mTLS between agent pods | Encrypt agent-to-agent communication |
| NetworkPolicy | Restrict which pods can communicate |
| Audit logging | Log credential access for compliance |
| RBAC per issue | Isolate feature access by team |

---

## 14. Testing Strategy

### 14.1 Mock Claude Responses

Testing agents without hitting Claude API (expensive, slow, non-deterministic):

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_claude_runtime():
    """Replace ClaudeAgentRuntime with deterministic mock."""
    runtime = AsyncMock()
    runtime.invoke.return_value = AgentResponse(
        content="Generated specification for user authentication...",
        confidence=85,
        artifacts=[{"type": "file", "path": ".specify/spec.md"}],
        status="completed",
    )
    return runtime

# tests/test_baron.py
async def test_baron_specify_creates_spec(mock_claude_runtime):
    baron = BaronAgent(runtime=mock_claude_runtime)
    result = await baron.specify("Add user authentication")

    assert result.status == "completed"
    assert result.confidence >= 80
    mock_claude_runtime.invoke.assert_called_once()
```

### 14.2 Test Levels

| Level | What | Claude | Location |
|-------|------|--------|----------|
| Unit | Single functions | Mock | `services/*/tests/unit/` |
| Integration | Multi-component | Mock | `services/*/tests/integration/` |
| Contract | API contracts | Mock | `services/*/tests/contract/` |
| E2E | Full workflow | Mock | `services/tests/e2e/` |

### 14.3 Mock Maintenance

```
tests/
├── fixtures/
│   └── claude_responses/
│       ├── baron_specify_auth.json     # Recorded real response
│       ├── baron_plan_auth.json
│       ├── marie_tests_auth.json
│       └── ...
├── conftest.py                          # Mock fixtures
```

**Update process:**
1. Periodically record real Claude responses for representative tasks
2. Store in `tests/fixtures/claude_responses/`
3. Update when prompts change significantly
4. Flag tests that use stale fixtures (>90 days old)

### 14.4 Operator Testing

```python
# tests/test_operator.py
import kopf.testing

async def test_feature_workflow_creates_pods():
    with kopf.testing.KopfRunner(['run', 'operator.py']) as runner:
        # Create IssueWorkflow CRD
        kubectl_create(FEATURE_WORKFLOW_YAML)

        # Wait for pods
        await wait_for_pods(namespace='farmercode', count=5)

        # Verify orchestrator + agent pods exist
        pods = list_pods(namespace='farmercode')
        assert any('orchestrator' in p.name for p in pods)
        assert any('baron' in p.name for p in pods)
```

---

## 15. CI/CD Pipeline

### 15.1 Repository Structure

| Repository | Purpose | CI Output |
|------------|---------|-----------|
| `farmer1st-ai-agents` | Agent definitions | Git tags (`baron@1.0.0`) |
| `farmcode` | Farmer Code app | Container images |
| `farmer1st-gitops` | K8s manifests | ArgoCD sync |

### 15.2 GitHub Actions Workflows

**farmcode CI/CD:**

```yaml
# .github/workflows/ci.yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest
      - run: uv run ruff check
      - run: uv run mypy

  build:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        image:
          - farmercode-api
          - farmercode-operator
          - agent-runtime
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/${{ matrix.image }}/Dockerfile
          push: true
          tags: |
            ghcr.io/farmer1st/${{ matrix.image }}:latest
            ghcr.io/farmer1st/${{ matrix.image }}:${{ github.sha }}
```

**PWA Deployment (CloudFlare Pages):**

```yaml
# .github/workflows/pwa.yaml
name: Deploy PWA

on:
  push:
    branches: [main]
    paths:
      - 'pwa/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
        working-directory: pwa
      - run: npm run build
        working-directory: pwa
      - uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: farmercode
          directory: pwa/dist
```

### 15.3 ArgoCD Configuration

```yaml
# ArgoCD Application per environment (not using Image Updater for Farmer Code apps)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-dev
spec:
  source:
    repoURL: https://github.com/farmer1st/myapp.git
    path: infra/k8s/overlays/dev
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp-dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### 15.4 Branching Strategy and Farmer Code Integration

**Foundational Principle**: Farmer Code automates the SDLC, but respects Git as the source of truth.
All changes flow through PRs — agents never push directly to main (except for their feature branch work).

**Branch Types:**

```
main                                    # Protected, requires PR
├── feature/{issue-id}-{slug}          # Agent work happens here
├── deploy/{issue-id}-to-{env}         # Overlay update PRs
└── rollback/{issue-id}-from-{env}     # Rollback PRs
```

**Complete Flow: Issue to Production**

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        Issue #42: Add User Avatars — Complete Flow                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 1: SPECIFICATION & PLANNING (Baron)                                       │    │
│  │  Branch: feature/42-user-avatars (created from main)                             │    │
│  ├─────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  Baron creates branch → SPECIFY → PLAN → TASKS                                   │    │
│  │  Commits: specs/042-user-avatars/spec.md, plan.md, tasks.md                      │    │
│  │  Pushes to feature/42-user-avatars                                               │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                           │                                              │
│                                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 2: IMPLEMENTATION (Marie → Dede → Dali → Gus)                             │    │
│  │  Branch: feature/42-user-avatars (continues)                                      │    │
│  ├─────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  Marie: TEST_DESIGN → writes test files                                          │    │
│  │  Dede: IMPLEMENT backend → services/user-management/profile-service/...          │    │
│  │  Dali: IMPLEMENT frontend → apps/web/src/components/Avatar.tsx                   │    │
│  │  Gus: IMPLEMENT gitops → infra/k8s/base/user-management/... (if needed)          │    │
│  │  Marie: VERIFY → runs tests, all pass                                            │    │
│  │  Victor: DOCS_QA → updates docs/                                                 │    │
│  │  General: REVIEW → code review pass                                              │    │
│  │                                                                                  │    │
│  │  All commits pushed to feature/42-user-avatars                                   │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                           │                                              │
│                                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 3: CODE PR TO MAIN                                                        │    │
│  │  PR: feature/42-user-avatars → main                                              │    │
│  ├─────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  General (or Gus) creates PR:                                                    │    │
│  │    Title: "feat(#42): Add user avatars"                                          │    │
│  │    Body: Summary of changes, test results, screenshots                           │    │
│  │                                                                                  │    │
│  │  CI runs: tests, lint, type check, build                                         │    │
│  │  Human reviews (optional based on confidence)                                    │    │
│  │  PR merged to main                                                               │    │
│  │                                                                                  │    │
│  │  CI triggers on main:                                                            │    │
│  │    → Build ghcr.io/farmer1st/myapp-web:sha-abc123                                │    │
│  │    → Build ghcr.io/farmer1st/myapp-profile-service:sha-def456                    │    │
│  │    → Push to registry                                                            │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                           │                                              │
│                                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 4: RELEASE_DEV (Gus)                                                      │    │
│  │  PR: deploy/42-to-dev → main                                                     │    │
│  ├─────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  Gus creates deploy/42-to-dev branch from main                                   │    │
│  │  Gus updates infra/k8s/overlays/dev/kustomization.yaml:                          │    │
│  │    images:                                                                       │    │
│  │      - name: web                                                                 │    │
│  │        newTag: sha-abc123                                                        │    │
│  │      - name: profile-service                                                     │    │
│  │        newTag: sha-def456                                                        │    │
│  │                                                                                  │    │
│  │  Gus creates PR, CI validates overlay syntax                                     │    │
│  │  PR auto-merged (dev is automated)                                               │    │
│  │                                                                                  │    │
│  │  ArgoCD detects change to overlays/dev/ → syncs → deploys to dev cluster         │    │
│  │  Gus records deployment in DynamoDB                                              │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                           │                                              │
│                                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 5: DEV VALIDATION                                                         │    │
│  │  (Automated + Human)                                                             │    │
│  ├─────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  Automated: E2E tests run against dev environment                                │    │
│  │  Human: Manual QA, stakeholder preview (optional)                                │    │
│  │                                                                                  │    │
│  │  If issues found → fix on feature branch → new PR → repeat from Phase 3          │    │
│  │  If OK → human approves promotion to staging                                     │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                           │                                              │
│                                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 6: RELEASE_STAGING (Gus)                                                  │    │
│  │  PR: deploy/42-to-staging → main                                                 │    │
│  ├─────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  Triggered by: Human approval (Slack command or GitHub comment)                  │    │
│  │                                                                                  │    │
│  │  Gus creates deploy/42-to-staging branch                                         │    │
│  │  Gus updates infra/k8s/overlays/staging/kustomization.yaml                       │    │
│  │    (same image tags as dev — immutable images)                                   │    │
│  │                                                                                  │    │
│  │  PR requires human approval                                                      │    │
│  │  PR merged → ArgoCD syncs staging                                                │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                           │                                              │
│                                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 7: STAGING VALIDATION → RELEASE_PROD                                      │    │
│  │  PR: deploy/42-to-prod → main                                                    │    │
│  ├─────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  Same pattern as staging:                                                        │    │
│  │    - Human approval required                                                     │    │
│  │    - Gus creates deploy/42-to-prod branch                                        │    │
│  │    - Updates infra/k8s/overlays/prod/kustomization.yaml                          │    │
│  │    - PR requires 2 approvals (stricter for prod)                                 │    │
│  │    - Merge → ArgoCD syncs prod                                                   │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                           │                                              │
│                                           ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │  PHASE 8: RETRO (Socrate)                                                        │    │
│  ├─────────────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                                  │    │
│  │  Socrate analyzes the issue lifecycle:                                           │    │
│  │    - Confidence scores, escalations, A2A conversations                           │    │
│  │    - Proposes prompt/KB improvements                                             │    │
│  │    - Creates PR to farmer1st-ai-agents repo                                      │    │
│  │                                                                                  │    │
│  │  Workflow complete, namespace fc-42 deleted                                      │    │
│  │                                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

**Branch Protection Rules:**

| Branch | Protection | Rationale |
|--------|------------|-----------|
| `main` | Require PR, CI pass, 1 approval (code), auto-merge OK for deploy PRs | Source of truth |
| `feature/*` | None (agents work freely) | Agent workspace |
| `deploy/*-to-dev` | CI pass only, auto-merge allowed | Fast iteration |
| `deploy/*-to-staging` | CI pass, 1 human approval | QA gate |
| `deploy/*-to-prod` | CI pass, 2 human approvals | Production safety |

**Who Creates What:**

| Branch/PR | Created By | Merged By |
|-----------|------------|-----------|
| `feature/{issue}-*` | Baron (at workflow start) | General (code PR) |
| Code PR to main | General | Human or auto (if high confidence) |
| `deploy/*-to-dev` | Gus | Auto-merge |
| `deploy/*-to-staging` | Gus | Human |
| `deploy/*-to-prod` | Gus | Human (2 approvals) |
| `rollback/*` | Gus | Human |

**Git Commit Conventions:**

```
# Feature branch commits (by agents)
[Baron] specify: create spec for user avatars
[Baron] plan: create implementation plan
[Marie] test: add avatar component tests
[Dede] feat: implement avatar upload endpoint
[Dali] feat: add avatar component to profile page
[Gus] infra: add avatar service deployment manifest
[Victor] docs: update API documentation for avatars

# Code PR title
feat(#42): Add user avatars

# Deploy PR title
deploy(#42): Release user avatars to dev
deploy(#42): Promote user avatars to staging
deploy(#42): Release user avatars to prod

# Rollback PR title
rollback(#42): Revert user avatars from dev
```

**Farmer Code Workflow Phases vs Git Operations:**

| Phase | Agent | Git Operation |
|-------|-------|---------------|
| SPECIFY | Baron | Commit to feature branch |
| PLAN | Baron | Commit to feature branch |
| TASKS | Baron | Commit to feature branch |
| TEST_DESIGN | Marie | Commit to feature branch |
| IMPLEMENT | Dede/Dali/Gus | Commits to feature branch |
| VERIFY | Marie | Commit test results |
| DOCS_QA | Victor | Commit to feature branch |
| REVIEW | General | Create PR to main |
| (CI) | — | Build images on main merge |
| RELEASE_DEV | Gus | Create deploy PR, update overlay |
| RELEASE_STAGING | Gus | Create deploy PR (human approval) |
| RELEASE_PROD | Gus | Create deploy PR (2 approvals) |
| RETRO | Socrate | PR to ai-agents repo |

**Why No Direct Pushes to Main:**

1. **Audit trail** — Every change has a PR with context
2. **CI validation** — Tests run before merge
3. **Rollback simplicity** — Revert a PR, not hunt for commits
4. **Human gates** — Staging/prod require approval
5. **Feature isolation** — Bad feature doesn't block others

**Handling Concurrent Features:**

```
main ─────●─────────●─────────●─────────●─────────→
          │         │         │         │
          │    feature/42     │    feature/43
          │    (avatars)      │    (notifications)
          │         │         │         │
          │         ▼         │         ▼
          │    PR merged      │    PR merged
          │         │         │         │
          ▼         ▼         ▼         ▼
    overlays/dev updated   overlays/dev updated
    (avatars)              (notifications)
```

Each feature updates its own image tags in the overlay. ArgoCD handles the merge — if both
features are deployed, both image tags are present. No conflicts because each service has
its own image entry.

**Rollback Scenario:**

```
Feature #42 broke prod. Rollback:

1. Human: "/rollback #42 from prod"

2. Gus looks up deployment record:
   - commit_sha: "abc123" (the deploy commit)
   - services: ["web", "profile-service"]
   - previous tags: {"web": "sha-old1", "profile-service": "sha-old2"}

3. Gus creates rollback/42-from-prod branch
   - Reverts image tags in overlays/prod/kustomization.yaml

4. PR created, requires 2 approvals (prod)

5. Merge → ArgoCD syncs → services rolled back

6. Feature #43 (notifications) unaffected — different services
```

---

## 16. Observability

### 16.1 Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Metrics | OpenTelemetry → Grafana Cloud | Latency, throughput, errors |
| Traces | OpenTelemetry → Grafana Cloud | Request flows across services |
| Logs | OpenTelemetry → Grafana Cloud | Structured JSON logs |
| Frontend | Grafana Faro | PWA performance, errors |
| Collection | Grafana Alloy | OTEL collector in cluster |

### 16.2 Key Metrics

| Metric | Description |
|--------|-------------|
| `feature.duration` | Time from start to completion |
| `feature.phase.duration` | Time per workflow phase |
| `agent.invocation.duration` | Agent response time |
| `agent.invocation.tokens` | Tokens used per invocation |
| `agent.confidence.score` | Confidence distribution |
| `escalation.count` | Human escalations per issue |
| `escalation.response_time` | Human response latency |

### 16.3 Tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer("farmercode")

@tracer.start_as_current_span("invoke_agent")
async def invoke_agent(agent: str, version: str, prompt: str):
    span = trace.get_current_span()
    span.set_attribute("agent.name", agent)
    span.set_attribute("agent.version", version)

    result = await runtime.invoke(prompt)

    span.set_attribute("agent.confidence", result.confidence)
    span.set_attribute("agent.tokens", result.tokens_used)

    return result
```

---

## 17. Future: Chat Portal

A separate application for direct human-agent interaction:

### 17.1 Purpose

- **Backlog refinement**: Chat with agents to refine issues before they're READY
- **Issue creation**: Help humans articulate feature requests or bug reports
- Chat with any agent (not just SDLC agents)
- Update agent KB and prompts
- Review/approve KB changes (commits to GitHub)
- No worktree needed (not tied to issues)

### 17.2 Backlog Refinement Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Chat Portal: Backlog Refinement                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Human: "I want users to be able to reset their passwords"                       │
│       │                                                                          │
│       ▼                                                                          │
│  Chat Portal → Veuve (Product Owner)                                             │
│       │                                                                          │
│       ▼                                                                          │
│  Veuve: "Should this include email verification? What about SMS as fallback?"   │
│       │                                                                          │
│       ▼                                                                          │
│  Human: "Yes email, no SMS for now"                                              │
│       │                                                                          │
│       ▼                                                                          │
│  Veuve creates/updates GitHub Issue #123 with refined description               │
│       │                                                                          │
│       ▼                                                                          │
│  Human reviews issue, adds "READY" label when satisfied                          │
│       │                                                                          │
│       ▼                                                                          │
│  Farmer Code workflow starts automatically                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 17.3 Architecture Differences

| Aspect | Farmer Code | Chat Portal |
|--------|-------------|-------------|
| Namespace | `fc-{issue-id}` (ephemeral) | `ai-agents` (permanent) |
| Agents | SDLC workflow agents | All agents (Veuve, Duc, future HR, FinOps) |
| Pods | Ephemeral (per issue, deleted on completion) | Permanent (always running, shared) |
| Escalation | Enabled | Disabled (human is already present) |
| Worktree | Required | Not needed |
| Context | Issue-scoped | User session-scoped |
| Purpose | Execute workflow | Refine backlog, update KB, brainstorm, roadmap |

**Same Image, Different Config:**

Agents in both namespaces use the **same container image** (`ghcr.io/farmer1st/agent-runtime`).
The only differences are environment variables:

| Variable | Workflow (`fc-*`) | Chat Portal (`ai-agents`) |
|----------|-------------------|---------------------------|
| `ESCALATION_ENABLED` | `true` | `false` |
| `WORKTREE_PATH` | `/volumes/worktrees/{issue}` | Not set |
| `ISSUE_ID` | `{issue-id}` | Not set |

**Why Duplicate Instead of Share?**

| Option | Pros | Cons |
|--------|------|------|
| **Shared pools** | Lower cost (fewer pods) | Complex routing, session affinity, context leakage risk |
| **Duplicate pods** | Simple isolation, no routing | Higher cost (more pods) |

We choose **duplication for simplicity**. Cost optimization via shared pools can be
explored later when scale justifies the added complexity. For now:

- Each workflow gets its own isolated agent pods
- Chat Portal has its own permanent agent pods
- No cross-namespace communication needed
- Easy to debug and reason about

### 17.4 Permanent Agent Deployment

Chat Portal agents live in the `ai-agents` namespace and are always running:

```yaml
# apps/chat-portal-agents.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: baron
  namespace: ai-agents
spec:
  replicas: 1
  selector:
    matchLabels:
      agent: baron
  template:
    metadata:
      labels:
        agent: baron
        app: chat-portal
    spec:
      containers:
        - name: agent
          image: ghcr.io/farmer1st/agent-runtime:latest
          env:
            - name: AGENT_NAME
              value: baron
            - name: AGENT_VERSION
              value: "2.0.0"
            - name: ESCALATION_ENABLED
              value: "false"  # Human is present in chat
          ports:
            - containerPort: 8002
---
apiVersion: v1
kind: Service
metadata:
  name: baron
  namespace: ai-agents
spec:
  selector:
    agent: baron
  ports:
    - port: 8002
```

**Service discovery:** Chat Portal backend (in `ai-agents` namespace) calls agents via simple names: `http://baron:8002` (see Section 5.5)

### 17.5 MkDocs Integration (Concept)

Custom MkDocs plugin for KB editing via chat:

```
User: "Update Baron's knowledge about our new API versioning strategy"
       │
       ▼
Chat Portal → Baron agent (no escalation mode)
       │
       ▼
Baron generates updated KB content
       │
       ▼
Plugin creates PR to farmer1st-ai-agents repo
       │
       ▼
User reviews/approves PR
       │
       ▼
Merged → Agent picks up new version on next refresh
```

---

## 18. Open Questions

| # | Question | Options | Decision |
|---|----------|---------|----------|
| 1 | Agent pod resource limits | Fixed vs autoscaling | TBD |
| 2 | Conversation archival | S3 vs DynamoDB | TBD |
| 3 | Multi-region | Single region vs global | Single (start simple) |
| 4 | Chat Portal agent config refresh | 1min / 5min / 15min | 5min |
| 5 | Max concurrent issues | 10 / 50 / unlimited | TBD |
| 6 | Worktree storage (EKS) | EFS vs EBS | EFS (shared) |

**Note on Question 4:** This applies to the **Chat Portal (Section 17)** where agents are
long-running and may need to refresh their config. Farmer Code issue pods (Section 2.5)
load config once at startup and don't hot-reload—they terminate when the feature completes.

**Note on Authentication:** Claude Agent SDK uses OAuth tokens (Claude Pro/Max subscription),
NOT API keys. OAuth tokens refresh automatically. See Section 13.1.

---

## Appendix A: Technology Stack Summary

| Layer | Technology |
|-------|------------|
| **Frontend** | React, TypeScript, Vite, Tailwind, shadcn/ui |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2 |
| **Agent Runtime** | Claude Agent SDK (OAuth, not API keys) |
| **Database** | DynamoDB (local + cloud) |
| **Container Registry** | GitHub Container Registry (GHCR) |
| **Orchestration** | Kubernetes (k3d local, EKS cloud) |
| **Operator Framework** | kopf (Python) |
| **CI/CD** | GitHub Actions, ArgoCD, Image Updater |
| **Frontend Hosting** | CloudFlare Pages |
| **Observability** | OpenTelemetry, Grafana Alloy, Grafana Cloud, Faro |
| **Secrets** | OAuth tokens, AWS Secrets Manager, K8s Secrets |
| **Source Control** | GitHub (monorepo for agents) |

> **Reference Implementation:** See `../sdk-agent-poc` for a working Claude Agent SDK example
> showing OAuth authentication, built-in tools, and custom MCP tools.

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **A2A** | Agent-to-Agent protocol for inter-agent communication |
| **Agent Card** | JSON descriptor of agent capabilities and skills |
| **ai-agents** | Permanent Kubernetes namespace for Chat Portal agents (always running) |
| **Backlog** | GitHub issues without "READY" label; refined via Chat Portal |
| **Circuit Breaker** | Pattern to prevent cascade failures by failing fast when a service is unhealthy |
| **Claude Agent SDK** | Python SDK for building agents with Claude; uses OAuth authentication (not API keys) |
| **Confidence Score** | 0-100 rating of agent's certainty in its response |
| **CRD** | Custom Resource Definition (Kubernetes) |
| **Domain** | Task category (backend, frontend, gitops, test) determining which agent handles it |
| **Escalation** | Routing low-confidence decisions to humans via HumanProduct or HumanTech |
| **Event Sourcing** | Storing state changes as immutable events; state computed via replay |
| **fc-{issue-id}** | Ephemeral Kubernetes namespace for Issue Workflow agents (deleted on completion) |
| **Feedback Loop** | Workflow transition back to an earlier phase based on agent output |
| **Git Optimistic Lock** | Push-rebase-retry pattern for handling concurrent git modifications |
| **Human Bridge** | Deterministic agent (HumanProduct, HumanTech) that bridges to actual humans |
| **Idempotency Key** | Unique identifier to prevent duplicate operations on retry |
| **Issue Workflow** | K8s custom resource representing a GitHub issue being processed |
| **kopf** | Kubernetes Operator Pythonic Framework |
| **Projection** | Computed view of current state derived from event history |
| **READY Label** | GitHub label that triggers workflow start for an issue |
| **Rehydration** | Rebuilding state by replaying events from the event store |
| **RETRO** | Final workflow phase where Socrate analyzes the issue lifecycle and proposes improvements |
| **Smart Escalation** | Baron/Victor/Socrate ability to choose between HumanProduct and HumanTech |
| **Socrate** | Learning loop agent that analyzes completed issues and proposes prompt/KB improvements |
| **SpecKit** | Framework for spec-driven development (specify, plan, tasks) |
| **Stop-and-Go** | Future workflow pattern where jobs checkpoint and exit rather than waiting idle (v1 uses polling instead) |
| **Vertical Escalation** | Consulted agent escalates to human (not the requester) |
| **Watchdog** | Cron job to catch missed escalation responses and resume stale workflows |
| **Worktree** | Git worktree for isolated issue development |
