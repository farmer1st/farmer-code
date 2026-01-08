# Farmer1st Architecture Proposal

**Version:** 0.2.0-draft
**Status:** R&D Discussion
**Last Updated:** 2025-01-08

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
12. [CI/CD Pipeline](#12-cicd-pipeline)
13. [Observability](#13-observability)
14. [Future: Chat Portal](#14-future-chat-portal)
15. [Open Questions](#15-open-questions)

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
│  │                        Agent Platform (A2A)                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │   │
│  │   │  Baron  │  │   Duc   │  │  Marie  │  │  Dede   │  │   HR    │  │   │
│  │   │  (PM)   │  │ (Arch)  │  │  (QA)   │  │ (Code)  │  │ (Admin) │  │   │
│  │   └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │   │
│  │                                                                      │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐                             │   │
│  │   │ FinOps  │  │Security │  │ DevOps  │  ...more agents             │   │
│  │   └─────────┘  └─────────┘  └─────────┘                             │   │
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
| Operator | Kubernetes operator for feature lifecycle | Python (kopf) |
| Persistence | Workflow state, conversations, training data | DynamoDB |
| Observability | Metrics, traces, logs | OpenTelemetry, Grafana |

---

## 2. Agent Architecture

### 2.1 Agent Definitions Repository

All agent definitions live in a single monorepo (`farmer1st-ai-agents`):

```
farmer1st-ai-agents/
├── agents/
│   ├── baron/
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
│   ├── duc/
│   ├── marie/
│   ├── dede/
│   ├── hr/
│   ├── finops/
│   └── ...
└── shared/
    └── prompts/                 # Shared prompt fragments
```

### 2.2 Agent Card (A2A)

Each agent publishes an agent card describing its capabilities:

```json
{
  "name": "baron",
  "description": "PM Agent - Creates specifications, plans, and task lists",
  "version": "2.1.0",
  "url": "http://baron:8002",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "humanEscalation": true
  },
  "skills": [
    {
      "id": "specify.feature",
      "name": "Create Feature Specification",
      "inputSchema": {"type": "object", "properties": {"description": {"type": "string"}}},
      "outputSchema": {"type": "object", "properties": {"spec_path": {"type": "string"}}}
    },
    {
      "id": "specify.plan",
      "name": "Create Implementation Plan",
      "inputSchema": {"type": "object", "properties": {"spec_path": {"type": "string"}}}
    },
    {
      "id": "specify.tasks",
      "name": "Generate Task List",
      "inputSchema": {"type": "object", "properties": {"plan_path": {"type": "string"}}}
    }
  ],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text", "artifact"]
}
```

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

Abstract the LLM provider to allow swapping Claude for other models:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AgentResponse:
    content: str
    confidence: int  # 0-100
    artifacts: list[dict]
    status: str  # "completed", "input-required", "failed"

@dataclass
class AgentCard:
    name: str
    version: str
    skills: list[dict]
    capabilities: dict

class AgentRuntime(ABC):
    """Abstract base for agent runtimes. Swap implementations without changing agents."""

    @abstractmethod
    async def invoke(
        self,
        prompt: str,
        context: dict,
        session_id: str
    ) -> AgentResponse:
        """Invoke the agent with a prompt."""
        pass

    @abstractmethod
    def get_agent_card(self) -> AgentCard:
        """Return the agent's capability card."""
        pass

class ClaudeAgentRuntime(AgentRuntime):
    """Implementation using Claude Agent SDK (Claude Code CLI wrapper)."""

    def __init__(self, agent_config: dict, credentials_path: str):
        self.config = agent_config
        self.credentials = credentials_path
        # Claude SDK initialization

    async def invoke(self, prompt: str, context: dict, session_id: str) -> AgentResponse:
        # Route to session-specific conversation file
        conversation_path = f"/conversations/{session_id}.json"
        # Invoke Claude Code CLI with session isolation
        ...

class FutureProviderRuntime(AgentRuntime):
    """Future: OpenAI, Gemini, local models, etc."""
    pass
```

### 2.5 Agent Pod Architecture

**Single pod per agent, multiple versions cached:**

```
baron-pod
├── Startup:
│   1. Fetch last 5 tags matching baron@* from GitHub API
│   2. Download each version's config to /versions/baron@X.Y.Z/
│   3. Ready to serve
│
├── Periodic refresh (every 5 min):
│   - Check for new tags
│   - Download new versions (no restart needed)
│
└── Request handling:
    POST /invoke/baron/2.0.0
    → Load config from /versions/baron@2.0.0/
    → Execute via SDK abstraction
    → Return response with confidence score
```

**Request routing:**

```python
@app.post("/invoke/{agent}/{version}")
async def invoke_agent(
    agent: str,
    version: str,
    request: InvokeRequest,
    session_id: str = Header(...)
):
    config = load_agent_config(agent, version)  # From cached versions
    runtime = ClaudeAgentRuntime(config, credentials_path="/secrets/credentials.json")
    response = await runtime.invoke(
        prompt=request.prompt,
        context=request.context,
        session_id=session_id
    )
    return response
```

---

## 3. Farmer Code (SDLC App)

### 3.1 Overview

Farmer Code automates the software development lifecycle using AI agents:

```
Feature Request → Spec → Plan → Tasks → Tests → Code → Verify → Review → Done
```

### 3.2 Components

| Component | Purpose | Deployment |
|-----------|---------|------------|
| PWA (UI) | Kanban board, feature management | CloudFlare Pages |
| API | Backend for UI, creates FeatureWorkflow CRDs | EKS pod |
| Operator | Watches CRDs, manages feature pods | EKS pod |
| Feature Orchestrator | Per-feature workflow state machine | Ephemeral pod |
| Agent Pods | Baron, Duc, Marie, Dede, Reviewer | Ephemeral pods |

### 3.3 Workflow Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Feature Workflow                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1        Phase 2        Phase 3        Phase 4        Phase 5       │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │  Baron   │   │  Baron   │   │  Baron   │   │  Marie   │   │  Dede    │  │
│  │ specify  │──▶│  plan    │──▶│  tasks   │──▶│  tests   │──▶│  code    │  │
│  │ .feature │   │          │   │          │   │ (write)  │   │          │  │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘  │
│       │              │              │              │              │         │
│       │              ▼              │              │              │         │
│       │         ┌──────────┐       │              │              │         │
│       │         │   Duc    │       │              │              │         │
│       │         │ (consult)│       │              │              │         │
│       │         └──────────┘       │              │              │         │
│       │                            │              │              │         │
│       ▼                            ▼              ▼              ▼         │
│  .specify/spec.md          .specify/tasks.md   tests/        src/         │
│  .specify/plan.md                                                          │
│                                                                             │
│  Phase 6        Phase 7                                                    │
│  ┌──────────┐   ┌──────────┐                                               │
│  │  Marie   │   │ Reviewer │                                               │
│  │ (verify) │──▶│  review  │──▶ Done                                       │
│  └──────────┘   └──────────┘                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Agent Roles:**

| Agent | Role | Artifacts |
|-------|------|-----------|
| Baron | PM - spec, plan, tasks | `.specify/spec.md`, `.specify/plan.md`, `.specify/tasks.md` |
| Duc | Architecture advisor (on-demand) | Consulted by Baron, Dede |
| Marie | QA - write tests, verify tests pass | `tests/` |
| Dede | Developer - implement code | `src/` |
| Reviewer | Code review | PR comments, approval |

### 3.4 Orchestrator Per Feature

Each feature gets its own orchestrator pod:

```python
# Simplified orchestrator logic
class FeatureOrchestrator:
    def __init__(self, feature_id: str, workflow_config: dict):
        self.feature_id = feature_id
        self.agents = workflow_config['agents']
        self.phases = workflow_config['phases']
        self.current_phase = 0

    async def run(self):
        # Create worktree
        worktree_path = await self.create_worktree()

        # Spawn agent pods
        await self.spawn_agent_pods(worktree_path)

        # Execute phases
        for phase in self.phases:
            agent = self.get_agent(phase.agent)
            result = await self.invoke_agent_a2a(agent, phase.skill, phase.input)

            if result.status == "input-required":
                # Human escalation in progress, wait
                result = await self.wait_for_human_response(result.task_id)

            if result.status == "failed":
                await self.fail_workflow(result.error)
                return

            # Update GitHub issue with progress
            await self.post_progress(phase, result)

        # Cleanup
        await self.terminate_agent_pods()
        await self.archive_worktree()
```

---

## 4. Kubernetes Infrastructure

### 4.1 Custom Resource Definition (CRD)

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: featureworkflows.farmercode.io
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
    plural: featureworkflows
    singular: featureworkflow
    kind: FeatureWorkflow
    shortNames:
      - fw
```

### 4.2 Example FeatureWorkflow

```yaml
apiVersion: farmercode.io/v1
kind: FeatureWorkflow
metadata:
  name: feature-auth-123
  namespace: farmercode
spec:
  repo: farmer1st/my-app
  branch: feature/auth-123
  issueNumber: 42
  workflow: sdlc-standard
  agents:
    - name: baron
      version: "2.0.0"
    - name: duc
      version: "1.5.0"
    - name: marie
      version: "1.2.0"
    - name: dede
      version: "3.0.0"
    - name: reviewer
      version: "1.0.0"
status:
  phase: planning
  worktreePath: /volumes/worktrees/feature-auth-123
  pods:
    - name: orchestrator-auth-123
      status: Running
    - name: baron-auth-123
      status: Running
    - name: duc-auth-123
      status: Running
```

### 4.3 Kubernetes Operator (kopf)

```python
import kopf
import kubernetes
from kubernetes import client

@kopf.on.create('farmercode.io', 'v1', 'featureworkflows')
async def on_feature_created(spec, name, namespace, logger, **kwargs):
    """Handle new feature workflow creation."""
    logger.info(f"Creating feature workflow: {name}")

    # 1. Create worktree on shared volume
    worktree_path = f"/volumes/worktrees/{name}"
    await create_worktree(
        repo=spec['repo'],
        branch=spec['branch'],
        path=worktree_path
    )

    # 2. Spawn orchestrator pod
    orchestrator_pod = create_orchestrator_pod(
        name=f"orchestrator-{name}",
        feature_id=name,
        worktree_path=worktree_path,
        agents=spec['agents'],
        workflow=spec['workflow']
    )

    v1 = client.CoreV1Api()
    v1.create_namespaced_pod(namespace=namespace, body=orchestrator_pod)

    # 3. Spawn agent pods
    for agent in spec['agents']:
        agent_pod = create_agent_pod(
            name=f"{agent['name']}-{name}",
            agent_name=agent['name'],
            agent_version=agent['version'],
            worktree_path=worktree_path
        )
        v1.create_namespaced_pod(namespace=namespace, body=agent_pod)

    return {'worktreePath': worktree_path}


@kopf.on.delete('farmercode.io', 'v1', 'featureworkflows')
async def on_feature_deleted(spec, name, namespace, logger, **kwargs):
    """Cleanup feature workflow resources."""
    logger.info(f"Deleting feature workflow: {name}")

    v1 = client.CoreV1Api()

    # Delete all pods for this feature
    pods = v1.list_namespaced_pod(
        namespace=namespace,
        label_selector=f"feature={name}"
    )
    for pod in pods.items:
        v1.delete_namespaced_pod(name=pod.metadata.name, namespace=namespace)

    # Archive/delete worktree
    await cleanup_worktree(f"/volumes/worktrees/{name}")


def create_agent_pod(name: str, agent_name: str, agent_version: str, worktree_path: str):
    """Create a pod spec for an agent."""
    return client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=name,
            labels={
                "app": "farmercode-agent",
                "agent": agent_name,
                "feature": name.split('-', 1)[1] if '-' in name else name
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
                    ],
                    volume_mounts=[
                        client.V1VolumeMount(
                            name="worktrees",
                            mount_path="/volumes/worktrees"
                        ),
                        client.V1VolumeMount(
                            name="credentials",
                            mount_path="/secrets",
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
                client.V1Volume(
                    name="credentials",
                    secret=client.V1SecretVolumeSource(
                        secret_name="claude-credentials"
                    )
                )
            ]
        )
    )
```

### 4.4 Local Development (k3d)

```bash
# Create cluster with shared volume
k3d cluster create farmercode \
  --volume /tmp/farmercode/worktrees:/volumes/worktrees \
  --port 8080:80@loadbalancer

# Deploy DynamoDB Local
kubectl apply -f infrastructure/dynamodb-local.yaml

# Deploy operator
kubectl apply -f infrastructure/operator.yaml

# Deploy API
kubectl apply -f apps/farmercode-api.yaml

# Create a test feature
kubectl apply -f - <<EOF
apiVersion: farmercode.io/v1
kind: FeatureWorkflow
metadata:
  name: feature-test-001
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

### 5.1 Protocol Overview

Agents communicate using the A2A (Agent-to-Agent) protocol:

```
┌──────────────┐         A2A Request          ┌──────────────┐
│              │ ─────────────────────────────▶│              │
│    Baron     │  POST /invoke/duc/1.5.0      │     Duc      │
│              │  {task_id, prompt, context}  │              │
│              │                              │              │
│              │         A2A Response         │              │
│              │ ◀─────────────────────────────│              │
│              │  {status, content, confidence}│              │
└──────────────┘                              └──────────────┘
```

### 5.2 Task Lifecycle States

| State | Description |
|-------|-------------|
| `submitted` | Task received, queued for processing |
| `working` | Agent actively processing |
| `input-required` | Blocked on human input |
| `completed` | Successfully finished |
| `failed` | Error occurred |

### 5.3 Streaming Responses

For long-running tasks, agents use Server-Sent Events (SSE):

```python
@app.post("/invoke/{agent}/{version}")
async def invoke_agent(agent: str, version: str, request: InvokeRequest):
    task_id = generate_task_id()

    async def event_stream():
        yield f"event: task-created\ndata: {json.dumps({'task_id': task_id})}\n\n"

        async for chunk in runtime.invoke_stream(request.prompt):
            yield f"event: progress\ndata: {json.dumps({'content': chunk})}\n\n"

        final = await runtime.get_result(task_id)
        yield f"event: completed\ndata: {json.dumps(final)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 5.4 Session Isolation

Each feature gets isolated conversation contexts:

```
/conversations/
├── feature-auth-123/
│   ├── baron.json      # Baron's conversation history
│   ├── duc.json        # Duc's conversation history
│   └── marie.json      # Marie's conversation history
├── feature-payment-456/
│   ├── baron.json
│   └── ...
```

Claude Code CLI uses the worktree path for session isolation automatically.

---

## 6. Human Escalation

### 6.1 Confidence-Based Escalation

When an agent has low confidence (<80%), it escalates to a human:

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

        # Poll for response
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
    feature_id: str
    source_agent: str      # Who asked
    target_agent: str      # Who answered
    question: str
    answer: str
    confidence: int        # 0-100
    escalated: bool
    human_response: str | None
    final_outcome: str     # "accepted", "rejected", "modified"
```

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
│  feature#auth-123        event#00001#2024-01-08T10:00:00  {type: WorkflowCreated}│
│  feature#auth-123        event#00002#2024-01-08T10:00:01  {type: PhaseStarted}   │
│  feature#auth-123        event#00003#2024-01-08T10:05:32  {type: AgentInvoked}   │
│  feature#auth-123        event#00004#2024-01-08T10:05:45  {type: CommitCreated}  │
│  feature#auth-123        event#00005#2024-01-08T10:05:46  {type: PhaseCompleted} │
│  feature#auth-123        event#00006#2024-01-08T10:47:30  {type: FeedbackRequested}
│  ...                                                                             │
│                                                                                  │
│  # Projections (computed views, can be rebuilt from events)                      │
│  feature#auth-123        projection#current_state        {phase, status, last_sha}
│  feature#auth-123        projection#timeline             {phases: [...]}        │
│  feature#auth-123        projection#metrics              {tokens, duration, ...}│
│                                                                                  │
│  # Conversations                                                                 │
│  feature#auth-123        conversation#baron#001          messages[]             │
│  feature#auth-123        conversation#duc#002            messages[]             │
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
| Get all events for feature | `PK = feature#X, SK begins_with event#` |
| Get events from version N | `PK = feature#X, SK >= event#N` |
| Get current state projection | `PK = feature#X, SK = projection#current_state` |
| List all conversations for feature | `PK = feature#X, SK begins_with conversation#` |
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
    feature_id: str
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
class EventStore:
    """Append-only event store backed by DynamoDB."""

    async def append(self, event: WorkflowEvent) -> int:
        """Append event and return new version number."""
        current_version = await self._get_current_version(event.feature_id)
        new_version = current_version + 1

        await self.table.put_item(
            Item={
                'PK': f'feature#{event.feature_id}',
                'SK': f'event#{str(new_version).zfill(8)}#{event.timestamp.isoformat()}',
                'event_type': event.__class__.__name__,
                'version': new_version,
                'data': self._serialize_event(event),
            },
            ConditionExpression='attribute_not_exists(SK)'
        )
        return new_version

    async def get_events(
        self,
        feature_id: str,
        from_version: int = 0,
        event_types: list[str] | None = None
    ) -> list[WorkflowEvent]:
        """Retrieve events for replay or projection."""
        response = await self.table.query(
            KeyConditionExpression=Key('PK').eq(f'feature#{feature_id}') &
                                  Key('SK').begins_with('event#')
        )
        return [self._deserialize_event(item) for item in response['Items']]
```

### 9.4 State Projection

```python
@dataclass
class WorkflowState:
    """Current state computed from events."""
    feature_id: str
    status: Literal["pending", "running", "paused", "completed", "failed"]
    current_phase: str | None
    phases_completed: list[str]
    last_commit_sha: str | None
    pending_escalation: dict | None
    pending_feedback: dict | None
    total_tokens: int

class WorkflowProjection:
    """Projects events into current state."""

    async def get_state(self, feature_id: str) -> WorkflowState:
        events = await self.event_store.get_events(feature_id)
        state = WorkflowState.initial(feature_id)
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
            # ... other event handlers
```

### 9.5 Crash Recovery

```python
class FeatureOrchestrator:
    async def run(self):
        """Run workflow with automatic recovery."""
        state = await self.projection.get_state(self.feature_id)

        if state.status == "completed":
            return

        if state.pending_escalation:
            await self._wait_for_escalation(state.pending_escalation)
            state = await self.projection.get_state(self.feature_id)

        phases_to_run = [p for p in self.phases if p not in state.phases_completed]
        for phase in phases_to_run:
            await self._run_phase(phase)
```

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
    REVIEW = "review"
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
        # Happy path
        Transition(Phase.SPECIFY, Phase.PLAN, "success"),
        Transition(Phase.PLAN, Phase.TASKS, "success"),
        Transition(Phase.VERIFY, Phase.REVIEW, "success"),
        Transition(Phase.REVIEW, Phase.DONE, "success"),

        # Feedback loops
        Transition(Phase.REVIEW, Phase.IMPLEMENT, "feedback:minor_changes", priority=10),
        Transition(Phase.REVIEW, Phase.PLAN, "feedback:architectural_rework", priority=10),
        Transition(Phase.VERIFY, Phase.IMPLEMENT, "feedback:test_failure", priority=10),
        Transition(Phase.IMPLEMENT, Phase.SPECIFY, "feedback:spec_ambiguity", priority=10),
    ],
    max_feedback_loops=5,
)
```

### 10.4 Infinite Loop Protection

```python
class FeedbackLoopProtection:
    def __init__(self, max_total_loops: int = 5, max_same_transition: int = 2):
        self.max_total_loops = max_total_loops
        self.max_same_transition = max_same_transition
        self.transition_counts: dict[str, int] = {}

    def check_transition(self, from_phase: str, to_phase: str, reason: str) -> bool:
        transition_key = f"{from_phase}->{to_phase}:{reason}"
        if self.total_loops >= self.max_total_loops:
            return False
        if self.transition_counts.get(transition_key, 0) >= self.max_same_transition:
            return False
        return True
```

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

**Solution:** Push-rebase-retry loop with idempotency.

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
                await run(f"git -C {workspace_path} rebase origin/{branch}")
                raise GitPushConflictError("Rebased, retrying...")
            raise
        return (await run(f"git -C {workspace_path} rev-parse HEAD")).stdout.strip()
```

### 11.2 Stop-and-Go Workflow (Sleeping Orchestrator)

**Problem:** Jobs waiting for human input waste resources.

**Solution:** Checkpoint state and exit. Resume with new Job when human responds.

```
Job 1: Phase 1 → Phase 2 → needs input → CHECKPOINT → EXIT
                                ↓
                    (hours/days pass)
                                ↓
                    Human responds via GitHub
                                ↓
Job 2: Load state → Skip 1,2 → Resume Phase 3 → ... → Done
```

```python
class FeatureOrchestrator:
    async def run(self):
        state = await self.projection.get_state(self.feature_id)

        for phase in phases_to_run:
            result = await self._execute_phase(phase)

            if result.status == "input_required":
                await self._suspend_for_human_input(phase, result)
                return  # Job exits, will be resumed later

            await self.event_store.append(PhaseCompleted(...))
```

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
        response = await httpx.post(f"http://{agent}.agents.svc/a2a/invoke", ...)
        return AgentResponse(**response.json())
```

### 11.5 Watchdog for Missed Webhooks

```python
async def check_stale_escalations():
    """Cron job to catch missed webhook responses."""
    waiting = await dynamodb.query(status="waiting_human", updated_at__lt=threshold)
    for workflow in waiting:
        response = await github.check_for_response(workflow.comment_id)
        if response:
            await resume_workflow(workflow.feature_id, response)
```

---

## 12. CI/CD Pipeline

### 12.1 Repository Structure

| Repository | Purpose | CI Output |
|------------|---------|-----------|
| `farmer1st-ai-agents` | Agent definitions | Git tags (`baron@1.0.0`) |
| `farmcode` | Farmer Code app | Container images |
| `farmer1st-gitops` | K8s manifests | ArgoCD sync |

### 12.2 GitHub Actions Workflows

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

### 12.3 ArgoCD Image Updater

```yaml
# argocd/apps/farmercode.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: farmercode
  annotations:
    argocd-image-updater.argoproj.io/image-list: |
      api=ghcr.io/farmer1st/farmercode-api,
      operator=ghcr.io/farmer1st/farmercode-operator,
      runtime=ghcr.io/farmer1st/agent-runtime
    argocd-image-updater.argoproj.io/api.update-strategy: latest
    argocd-image-updater.argoproj.io/write-back-method: git
spec:
  source:
    repoURL: https://github.com/farmer1st/farmer1st-gitops.git
    path: apps/farmercode
  destination:
    server: https://kubernetes.default.svc
    namespace: farmercode
```

---

## 13. Observability

### 13.1 Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| Metrics | OpenTelemetry → Grafana Cloud | Latency, throughput, errors |
| Traces | OpenTelemetry → Grafana Cloud | Request flows across services |
| Logs | OpenTelemetry → Grafana Cloud | Structured JSON logs |
| Frontend | Grafana Faro | PWA performance, errors |
| Collection | Grafana Alloy | OTEL collector in cluster |

### 13.2 Key Metrics

| Metric | Description |
|--------|-------------|
| `feature.duration` | Time from start to completion |
| `feature.phase.duration` | Time per workflow phase |
| `agent.invocation.duration` | Agent response time |
| `agent.invocation.tokens` | Tokens used per invocation |
| `agent.confidence.score` | Confidence distribution |
| `escalation.count` | Human escalations per feature |
| `escalation.response_time` | Human response latency |

### 13.3 Tracing

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

## 14. Future: Chat Portal

A separate application for direct human-agent interaction:

### 14.1 Purpose

- Chat with any agent (not just SDLC agents)
- Update agent KB and prompts
- Review/approve KB changes (commits to GitHub)
- No worktree needed (not tied to features)

### 14.2 Architecture Differences

| Aspect | Farmer Code | Chat Portal |
|--------|-------------|-------------|
| Agents | SDLC subset (Baron, Duc, Marie, Dede) | All agents (HR, FinOps, etc.) |
| Pods | Ephemeral (per feature) | Permanent (always running) |
| Escalation | Enabled | Disabled |
| Worktree | Required | Not needed |
| Context | Feature-scoped | User session-scoped |

### 14.3 MkDocs Integration (Concept)

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

## 15. Open Questions

| # | Question | Options | Decision |
|---|----------|---------|----------|
| 1 | Agent pod resource limits | Fixed vs autoscaling | TBD |
| 2 | Conversation archival | S3 vs DynamoDB | TBD |
| 3 | Multi-region | Single region vs global | Single (start simple) |
| 4 | Agent hot-reload frequency | 1min / 5min / 15min | 5min |
| 5 | Max concurrent features | 10 / 50 / unlimited | TBD |
| 6 | Worktree storage (EKS) | EFS vs EBS | EFS (shared) |
| 7 | Claude credentials rotation | Manual vs automated | Manual (initially) |

---

## Appendix A: Technology Stack Summary

| Layer | Technology |
|-------|------------|
| **Frontend** | React, TypeScript, Vite, Tailwind, shadcn/ui |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2 |
| **Agent Runtime** | Claude Agent SDK (abstracted) |
| **Database** | DynamoDB (local + cloud) |
| **Container Registry** | GitHub Container Registry (GHCR) |
| **Orchestration** | Kubernetes (k3d local, EKS cloud) |
| **Operator Framework** | kopf (Python) |
| **CI/CD** | GitHub Actions, ArgoCD, Image Updater |
| **Frontend Hosting** | CloudFlare Pages |
| **Observability** | OpenTelemetry, Grafana Alloy, Grafana Cloud, Faro |
| **Secrets** | AWS Secrets Manager, K8s Secrets |
| **Source Control** | GitHub (monorepo for agents) |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **A2A** | Agent-to-Agent protocol for inter-agent communication |
| **Agent Card** | JSON descriptor of agent capabilities and skills |
| **Circuit Breaker** | Pattern to prevent cascade failures by failing fast when a service is unhealthy |
| **Confidence Score** | 0-100 rating of agent's certainty in its response |
| **CRD** | Custom Resource Definition (Kubernetes) |
| **Escalation** | Routing low-confidence decisions to humans |
| **Event Sourcing** | Storing state changes as immutable events; state computed via replay |
| **Feature Workflow** | K8s custom resource representing a feature in progress |
| **Feedback Loop** | Workflow transition back to an earlier phase based on agent output |
| **Git Optimistic Lock** | Push-rebase-retry pattern for handling concurrent git modifications |
| **Idempotency Key** | Unique identifier to prevent duplicate operations on retry |
| **kopf** | Kubernetes Operator Pythonic Framework |
| **Projection** | Computed view of current state derived from event history |
| **Rehydration** | Rebuilding state by replaying events from the event store |
| **Stop-and-Go** | Workflow pattern where jobs checkpoint and exit rather than waiting idle |
| **Watchdog** | Cron job to catch missed webhook responses and resume stale workflows |
| **Worktree** | Git worktree for isolated feature development |
| **SpecKit** | Framework for spec-driven development (specify, plan, tasks) |
