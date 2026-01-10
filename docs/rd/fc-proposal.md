# Farmer Code Proposal

**Version:** 0.4.0-draft
**Status:** R&D Discussion
**Last Updated:** 2026-01-10

> **Related:** For agent definitions, A2A protocol, and Chat Portal, see [agents-proposal.md](./agents-proposal.md).

> **v0.4.0 Changes:** Simplified architecture - replaced DynamoDB with Git-Journaling,
> replaced Event Sourcing with simple State Machine, added self-healing rewind (always
> to SPECIFY), added Brain/Muscle node strategy, added Town Crier for AWAIT states,
> added Vauban agent for releases, updated workflow phases (MERGE, AWAIT_STAGING, AWAIT_PROD),
> switched to A2A REST binding (from JSON-RPC) for simpler agent communication.

## Executive Summary

**Farmer Code** is an SDLC automation system that uses AI agents to implement features
from GitHub Issues. It orchestrates a workflow through phases: SPECIFY → PLAN → TASKS →
TEST_DESIGN → IMPLEMENT → VERIFY → REVIEW → MERGE → RELEASE → RETRO.

**Key characteristics:**

- **Ephemeral agents**: Scale-to-zero, spawned per issue, destroyed on completion
- **Git-Journaling**: Phase results stored in `.farmercode/issue-{id}/` (no DynamoDB)
- **Self-healing rewind**: On REJECT at any phase, rewind to SPECIFY (max 5 attempts)
- **Town Crier**: CI/CD wakes hibernating orchestrators after deployments
- **Brain/Muscle nodes**: Reserved EC2 for infra, Spot for compute

**What Farmer Code is NOT:**

- Not a chat system (see Chat Portal in [agents-proposal.md](./agents-proposal.md))
- Not an agent definition system (agents defined in `farmer1st-ai-agents` repo)
- Not always-on (agents are ephemeral, scale to zero when idle)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Workflow & Phases](#2-workflow--phases)
3. [Kubernetes Infrastructure](#3-kubernetes-infrastructure)
4. [Orchestrator Loop](#4-orchestrator-loop)
5. [Persistence (Git-Journaling)](#5-persistence-git-journaling)
6. [Workflow State Machine](#6-workflow-state-machine)
7. [Self-Healing Rewind](#7-self-healing-rewind)
8. [Resilience Patterns](#8-resilience-patterns)
9. [GitHub Integration](#9-github-integration)
10. [Why Custom Workflow Engine](#10-why-custom-workflow-engine)
11. [Security](#11-security)
12. [Testing Strategy](#12-testing-strategy)
13. [CI/CD Pipeline](#13-cicd-pipeline)
14. [Observability](#14-observability)
15. [Open Questions](#15-open-questions)

**See also:** [agents-proposal.md](./agents-proposal.md) for Agent Architecture, A2A Protocol, Human Escalation, and Chat Portal.

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
│  │  k3d (local) / EKS (cloud)  │  Git (Journal)  │  GitHub  │  Slack   │   │
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
| Persistence | Workflow state in CRD, history in Git journal | K8s CRD, Git |
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
| Documentation | Colocated + `docs/` | Victor |

### 1.3 Documentation Structure (Colocated + Aggregated)

Following the [Spotify monorepo documentation pattern](https://engineering.atspotify.com/2019/10/solving-documentation-for-monoliths-and-monorepos/),
we use **colocated documentation** (docs near code) with a **centralized aggregation point**.

**Why Colocated?**

| Aspect | Benefit |
|--------|---------|
| Ownership | Docs live with code owners (matches CODEOWNERS) |
| Discoverability | Devs find docs where they expect (`cd service && ls docs/`) |
| Freshness | Docs updated alongside code changes in same PR |
| CI integration | Each service can validate its own docs |

**Documentation Locations:**

```
my-app/
│
├── docs/                               # Root: Cross-cutting, getting started
│   ├── index.md                        # Links to subdocs
│   ├── architecture/                   # System-wide design decisions
│   ├── getting-started/                # Onboarding guides
│   ├── adr/                            # Architecture Decision Records
│   └── mkdocs.yml                      # Aggregates all subdocs
│
├── services/
│   ├── [domain]/
│   │   ├── docs/                       # Domain-level docs
│   │   │   ├── index.md
│   │   │   ├── api.md                  # API documentation
│   │   │   ├── runbooks/               # Operational runbooks
│   │   │   └── mkdocs.yml              # Optional: standalone build
│   │   │
│   │   ├── auth-service/
│   │   │   └── docs/                   # Service-specific docs
│   │   │       ├── index.md
│   │   │       └── api.md
│   │   └── ...
│   │
│   └── shared/
│       └── docs/                       # Shared library docs
│           ├── contracts.md
│           └── clients.md
│
├── apps/
│   └── portal/
│       └── docs/                       # App-specific docs
│           ├── components.md
│           └── state-management.md
│
├── infra/
│   ├── terraform/
│   │   └── docs/                       # IaC documentation
│   │       ├── modules.md
│   │       └── environments.md
│   │
│   └── k8s/
│       └── docs/                       # K8s manifests docs
│           ├── overlays.md
│           └── secrets.md
│
└── mkdocs.yml                          # Root aggregator
```

**Aggregation with MkDocs Monorepo Plugin:**

The root `mkdocs.yml` uses [mkdocs-monorepo-plugin](https://github.com/backstage/mkdocs-monorepo-plugin)
to build a unified documentation site from colocated sources:

```yaml
# mkdocs.yml (root)
site_name: MyApp Documentation
plugins:
  - monorepo

nav:
  - Home: docs/index.md
  - Getting Started: docs/getting-started/
  - Architecture: docs/architecture/
  - Services:
    - User Management: '!include ./services/user-management/docs/mkdocs.yml'
    - Payments: '!include ./services/payments/docs/mkdocs.yml'
  - Apps:
    - Portal: '!include ./apps/portal/docs/mkdocs.yml'
  - Infrastructure:
    - Terraform: '!include ./infra/terraform/docs/mkdocs.yml'
    - Kubernetes: '!include ./infra/k8s/docs/mkdocs.yml'
  - ADRs: docs/adr/
```

**Service-Level mkdocs.yml:**

```yaml
# services/user-management/docs/mkdocs.yml
site_name: User Management
docs_dir: .
nav:
  - Overview: index.md
  - API Reference: api.md
  - Runbooks: runbooks/
```

**Documentation Ownership:**

| Location | Owner | Content |
|----------|-------|---------|
| `docs/` | Victor | Architecture, onboarding, cross-cutting |
| `services/[domain]/docs/` | Domain team | Domain overview, shared patterns |
| `services/[domain]/[service]/docs/` | Service owner | API docs, runbooks |
| `apps/*/docs/` | Dali | UI components, state, routing |
| `infra/terraform/docs/` | Gus | Module usage, environment setup |
| `infra/k8s/docs/` | Gus | Manifest patterns, overlays |

**Benefits:**

1. **Single site** — `mkdocs build` produces unified docs at `site/`
2. **Colocated authoring** — Teams edit docs in their own directories
3. **Independent builds** — Each service can run `mkdocs serve` locally
4. **CODEOWNERS alignment** — Docs PRs route to correct reviewers

---

## 2. Agent Architecture

> **Moved to [agents-proposal.md](./agents-proposal.md)**
>
> Agent definitions, versioning, SDK abstraction, and A2A protocol are now documented
> in the Agent Platform proposal. This section provides a brief summary for context.

**Key points:**

- Agents defined in `farmer1st-ai-agents` repo (prompts, KB, skills, MCP configs)
- Each agent has `config.yaml`, `prompt.md`, `agent-card.json`
- A2A REST API: `POST /jobs`, `GET /jobs/{id}`
- SDK abstraction allows provider swaps (Claude → OpenAI → local)

**Farmer Code uses agents in ephemeral mode:**

| Aspect | Ephemeral (Farmer Code) | Permanent (Chat Portal) |
|--------|------------------------|------------------------|
| Namespace | `fc-{issue-id}` | `ai-agents` |
| Lifecycle | Created/destroyed per issue | Always running |
| Replicas | Scale-to-zero | Always 1+ |
| Escalation | Enabled | Disabled |
| Worktree | Mounted | None |

---

## 3. Farmer Code (SDLC App)

> **Note:** Agent definitions, A2A protocol details, and SDK abstraction are in
> [agents-proposal.md](./agents-proposal.md). This section focuses on the Farmer Code
> workflow system that uses those agents.

### 3.1 Overview

Farmer Code automates the software development lifecycle using AI agents:

```
Issue → SPECIFY → PLAN → TASKS → TEST_DESIGN → IMPLEMENT → VERIFY → REVIEW → MERGE
     → AWAIT_STAGING → AWAIT_PROD → RETRO → DONE
```

**Key simplifications (v0.5.0):**
- **Self-healing rewind**: On REJECT at any phase, rewind to SPECIFY (max 5 attempts)
- **Hibernation states**: AWAIT_STAGING and AWAIT_PROD scale to zero while waiting for CI/CD
- **Town Crier**: CI/CD wakes hibernating orchestrators via CRD annotation

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
| Gus | DevOps - gitops, infrastructure | `gitops` (includes docs) | HumanTech |
| Vauban | Release engineer - staging/prod | `release` | HumanTech |
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

The workflow is **strictly linear** with self-healing rewind on failure (Section 10).
Each phase has **one owner agent**. On REJECT, workflow rewinds to SPECIFY.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              Issue Workflow                                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐                       │
│  │  Baron   │   │  Baron   │   │  Baron   │   │  Marie   │                       │
│  │ SPECIFY  │──▶│   PLAN   │──▶│  TASKS   │──▶│TEST_DESIGN│                      │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘                       │
│       ▲                                              │                            │
│       │                                              ▼                            │
│       │    ┌────────────────────────────────────────────────────────────────┐    │
│       │    │                IMPLEMENT (sequential by domain)                 │    │
│       │    │  ┌──────────┐   ┌──────────┐   ┌──────────┐                    │    │
│       │    │  │  Dede    │──▶│  Dali    │──▶│   Gus    │  Each agent scans  │    │
│       │    │  │ backend  │   │ frontend │   │  gitops  │  tasks.md for their │    │
│       │    │  └──────────┘   └──────────┘   └──────────┘  domain tasks       │    │
│       │    └────────────────────────────────────────────────────────────────┘    │
│       │                                              │                            │
│       │                                              ▼                            │
│       │    ┌──────────┐   ┌──────────┐   ┌──────────┐                            │
│       │    │  Marie   │   │ General  │   │ General  │                            │
│  REJECT    │  VERIFY  │──▶│  REVIEW  │──▶│  MERGE   │                            │
│       │    └──────────┘   └──────────┘   └──────────┘                            │
│       │                                        │                                  │
│       │                                        ▼                                  │
│       │    ┌──────────────────────────────────────────────────────────────────┐  │
│       │    │                    AWAIT_STAGING (Hibernation)                    │  │
│       │    │  Orchestrator scales to 0. CI deploys via ArgoCD.                │  │
│       │    │  Town Crier annotates CRD when staging tests pass.               │  │
│       │    │  Vauban wakes to verify staging health.                          │  │
│       │    └──────────────────────────────────────────────────────────────────┘  │
│       │                                        │                                  │
│       │                         ◀──── REJECT ──┤                                  │
│       │                                        ▼                                  │
│       │    ┌──────────────────────────────────────────────────────────────────┐  │
│       │    │                    AWAIT_PROD (Hibernation)                       │  │
│       │    │  Manual approval → CI deploys to production.                     │  │
│       │    │  Town Crier annotates CRD when prod verification passes.         │  │
│       │    │  Vauban wakes to verify production health.                       │  │
│       │    └──────────────────────────────────────────────────────────────────┘  │
│       │                                        │                                  │
│       │                         ◀──── REJECT ──┤                                  │
│       │                                        ▼                                  │
│       │    ┌──────────────────────────────────────────────────────────────────┐  │
│       │    │                       RETRO (Learning Loop)                       │  │
│       │    │  ┌──────────┐                                                    │  │
│       │    │  │ Socrate  │  Analyzes: confidence, escalations, conversations  │  │
│       │    │  │  RETRO   │  Outputs: PRs for prompt/KB improvements + reports │  │
│       │    │  └──────────┘  Human approves changes via Slack                  │  │
│       │    └──────────────────────────────────────────────────────────────────┘  │
│       │                                        │                                  │
│       │                         ◀──── REJECT ──┤                                  │
│       │                                        ▼                                  │
│       │                                      DONE                                 │
│       │                                                                           │
│  ┌────┴──────────────────────────────────────────────────────────────────────┐   │
│  │                      SELF-HEALING REWIND (Section 10)                      │   │
│  │  Any phase can return outcome: REJECT with a rejection_reason              │   │
│  │  → Workflow rewinds to SPECIFY (max 5 attempts)                            │   │
│  │  → Rejection reason becomes context for Baron to improve the spec          │   │
│  │  → After 5 failures, escalate to human                                     │   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Phase Details:**

| Phase | Owner | Input | Output | Outcome |
|-------|-------|-------|--------|---------|
| SPECIFY | Baron | GitHub issue | `.specify/spec.md` | PASS / REJECT |
| PLAN | Baron | spec.md | `.specify/plan.md` | PASS / REJECT |
| TASKS | Baron | plan.md | `.specify/tasks.md` | PASS / REJECT |
| TEST_DESIGN | Marie | tasks.md | Test cases in `tests/` | PASS / REJECT |
| IMPLEMENT | Dede, Dali, Gus | tasks.md | Code + docs | PASS / REJECT |
| VERIFY | Marie | Code + tests | Test results | PASS / REJECT |
| REVIEW | General | PR | Review comments | PASS / REJECT |
| MERGE | General | Approved review | Merged PR | PASS / REJECT |
| AWAIT_STAGING | Vauban | Merged PR | Staging verification | PASS / REJECT / WAITING_FOR_CI |
| AWAIT_PROD | Vauban | Staging passed | Prod verification | PASS / REJECT / WAITING_FOR_CI |
| RETRO | Socrate | All journal files | PRs for improvements | PASS / REJECT |
| DONE | — | — | Issue closed | — |

**Hibernation Phases:**

| Phase | Hibernation Trigger | Wake Trigger | Agent on Wake |
|-------|--------------------|--------------|--------------|
| AWAIT_STAGING | MERGE completes | Town Crier annotation (staging tests pass) | Vauban |
| AWAIT_PROD | AWAIT_STAGING passes | Town Crier annotation (prod deploy success) | Vauban |

**Rewind Constraints (from Section 10):**

| Constraint | Value | Purpose |
|------------|-------|---------|
| Max rewinds | 5 | Prevent infinite retry loops |
| Rewind target | Always SPECIFY | Simplicity over targeted feedback |
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
  currentPhaseIndex: 4
  currentJobId: "job-uuid-1234"
  rewindCount: 0
  lastOutcome: "PASS"
```

### 4.4 Hybrid Node Strategy (Brain vs Muscle)

To optimize costs (~$138/month target), we use a **hybrid infrastructure** with Reserved and Spot instances:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        EKS Node Strategy                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │    BRAIN NODE (Reserved EC2)        │  │    MUSCLE NODE (Spot EC2)       │  │
│  │    t3.large (~$60/mo)               │  │    t3.xlarge (~$50/mo)          │  │
│  ├─────────────────────────────────────┤  ├─────────────────────────────────┤  │
│  │                                     │  │                                  │  │
│  │  "Always On" Stable Infrastructure  │  │  "Scale-to-Zero" Workers         │  │
│  │                                     │  │                                  │  │
│  │  • Kopf Operator                    │  │  • Orchestrator pods             │  │
│  │  • ARC Listener                     │  │  • Baron, Dede, Dali             │  │
│  │  • ARC Runner Controller            │  │  • Marie, Victor, General        │  │
│  │                                     │  │  • Vauban, Socrate               │  │
│  │                                     │  │                                  │  │
│  │  nodeSelector:                      │  │  nodeSelector:                   │  │
│  │    role: brain                      │  │    role: muscle                  │  │
│  │                                     │  │  tolerations:                    │  │
│  │                                     │  │    - key: spot                   │  │
│  │                                     │  │      value: "true"               │  │
│  │                                     │  │                                  │  │
│  └─────────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                                  │
│  Network: fck-nat (t4g.nano) instead of AWS NAT Gateway (~$28/mo savings)       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Node Group Configuration:**

| Node Group | Instance | Pricing | Purpose | Pods |
|------------|----------|---------|---------|------|
| Brain | t3.large | Reserved | Always-on infrastructure | Operator, ARC |
| Muscle | t3.xlarge | Spot | Compute-heavy, interruptible | Orchestrators, Agents |

**Scale-to-Zero Pattern:**

Agent pods are deployed with `replicas=0`. The orchestrator:
1. Scales agent to 1 replica before dispatching work
2. Polls `GET /jobs/{id}` until completion
3. Scales agent back to 0 immediately (cost savings)

```yaml
# Agent Deployment (scale-to-zero)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: baron
spec:
  replicas: 0  # Orchestrator wakes when needed
  selector:
    matchLabels:
      app: baron
  template:
    metadata:
      labels:
        app: baron
    spec:
      nodeSelector:
        role: muscle
      tolerations:
        - key: spot
          operator: Equal
          value: "true"
      containers:
        - name: baron
          image: ghcr.io/farmer1st/baron:latest
          resources:
            requests:
              cpu: "1000m"  # Beefy for LLM inference
              memory: "2Gi"
```

**Cost Breakdown (Target ~$138/mo):**

| Item | Monthly Cost |
|------|--------------|
| Brain Node (t3.large Reserved) | ~$60 |
| Muscle Node (t3.xlarge Spot, avg utilization) | ~$50 |
| fck-nat (t4g.nano) | ~$8 |
| EBS Storage | ~$10 |
| Data Transfer | ~$10 |
| **Total** | **~$138** |

### 4.5 Kubernetes Operator (kopf)

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

### 4.6 Scale-to-Zero and Town Crier

**Scale-to-Zero Pattern:**

Agent deployments start with `replicas: 0`. The orchestrator scales agents up before dispatch
and back to zero after completion. This minimizes compute costs during idle periods.

```python
async def dispatch_to_agent(agent: str, job: Job) -> str:
    """Scale agent to 1, send job, then scale back to 0."""
    apps_v1 = client.AppsV1Api()

    # 1. Scale up
    await scale_deployment(agent, replicas=1)
    await wait_for_ready(agent, timeout=60)

    # 2. Post job
    job_id = await post_job(agent, job)

    # 3. Poll until done (agent does work, commits to journal)
    while True:
        status = await get_job_status(agent, job_id)
        if status.outcome in ("pass", "reject", "waiting_for_ci"):
            break
        await asyncio.sleep(5)

    # 4. Scale down
    await scale_deployment(agent, replicas=0)

    return status.outcome
```

**Town Crier Pattern:**

During AWAIT_STAGING and AWAIT_PROD phases, the orchestrator hibernates (scales to 0).
CI/CD pipelines use the "Town Crier" script to wake hibernating orchestrators when
deployments succeed.

```yaml
# .github/workflows/deploy-staging.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: kubectl apply -k overlays/staging

      - name: Run smoke tests
        run: ./scripts/smoke-test.sh staging

      - name: Town Crier - Wake Orchestrator
        if: success()
        run: |
          # Find orchestrators waiting for staging
          WORKFLOWS=$(kubectl get issueworkflow -o json | jq -r '
            .items[] |
            select(.status.phase == "await_staging") |
            select(.status.outcome == "waiting_for_ci") |
            .metadata.name
          ')

          # Annotate each to trigger wake
          for WF in $WORKFLOWS; do
            kubectl annotate issueworkflow $WF \
              farmercode.io/wake="true" \
              farmercode.io/wake-reason="staging-deploy-success" \
              farmercode.io/wake-timestamp="$(date -Iseconds)" \
              --overwrite
          done
```

**Operator Watches for Wake Annotation:**

```python
@kopf.on.field('farmercode.io', 'v1', 'issueworkflows', field='metadata.annotations')
async def on_wake_annotation(old, new, spec, name, namespace, logger, **kwargs):
    """Wake hibernating orchestrator when CI annotates the CRD."""
    if new.get('farmercode.io/wake') == 'true' and old.get('farmercode.io/wake') != 'true':
        logger.info(f"Town Crier waking orchestrator for {name}")

        # Scale orchestrator back up
        workflow_ns = f"fc-{name}"
        await scale_deployment(f"{workflow_ns}/orchestrator", replicas=1)

        # Clear the wake annotation
        await patch_crd_annotations(name, {
            'farmercode.io/wake': None,
            'farmercode.io/wake-reason': None,
            'farmercode.io/wake-timestamp': None,
        })
```

**Hibernation Flow:**

```
MERGE phase completes
    │
    ▼
Orchestrator sets: phase=await_staging, outcome=waiting_for_ci
    │
    ▼
Orchestrator scales itself to 0 (hibernation)
    │
    ▼
ArgoCD deploys to staging (independent of Farmer Code)
    │
    ▼
CI pipeline runs smoke tests
    │
    ▼
Town Crier script annotates CRD: farmercode.io/wake=true
    │
    ▼
Operator detects annotation, scales orchestrator to 1
    │
    ▼
Orchestrator resumes, dispatches Vauban to verify staging
    │
    ▼
If Vauban returns PASS → advance to AWAIT_PROD
If Vauban returns REJECT → rewind to SPECIFY
```

---

## 5. Agent Communication (A2A REST Binding)

We implement the [Google A2A Protocol](https://github.com/google/A2A) using the **REST binding**.
A2A supports multiple bindings (JSON-RPC, gRPC, REST) — we chose REST for simplicity and alignment
with our "lite" architecture philosophy.

### 5.1 Protocol Overview

Orchestrator communicates with agents using simple REST endpoints:

```
┌──────────────┐                                           ┌──────────────┐
│              │  POST /jobs                               │              │
│ Orchestrator │ ──────────────────────────────────────────▶│    Agent     │
│              │  {phase, context, issue_id}               │   (Baron)    │
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
│              │  {phase: "specify", outcome: "pass"}      │              │
└──────────────┘                                           └──────────────┘
```

**REST Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/agent.json` | GET | Agent discovery (A2A standard) |
| `/jobs` | POST | Create a new job |
| `/jobs/{job_id}` | GET | Poll job status |
| `/jobs/{job_id}` | DELETE | Cancel a running job |
| `/health` | GET | Liveness/readiness probe |

### 5.2 Job Lifecycle

| Status | Description |
|--------|-------------|
| `pending` | Job received, queued |
| `working` | Agent actively processing |
| `completed` | Finished with outcome |
| `failed` | Error occurred |
| `canceled` | Job was canceled |

**Outcome values** (when status is `completed`):

| Outcome | Meaning |
|---------|---------|
| `pass` | Phase succeeded, advance to next |
| `reject` | Phase failed, rewind to SPECIFY |
| `waiting_for_ci` | Hibernating until Town Crier wakes |

### 5.3 Request/Response Schemas

**POST /jobs - Create Job:**

```python
class CreateJobRequest(BaseModel):
    phase: str                    # "specify", "plan", etc.
    issue_id: str                 # "issue-42"
    context: dict                 # Phase-specific context
    rewind_context: dict | None   # Present if this is a rewind

class CreateJobResponse(BaseModel):
    job_id: str                   # "job-abc123"
    status: str                   # "pending"

# Example
POST /jobs
{
    "phase": "specify",
    "issue_id": "issue-42",
    "context": {
        "repo": "farmer1st/myapp",
        "feature_description": "Add user authentication"
    }
}

# Response: 201 Created
{
    "job_id": "job-abc123",
    "status": "pending"
}
```

**GET /jobs/{job_id} - Poll Status:**

```python
class JobStatusResponse(BaseModel):
    job_id: str
    status: str                   # "pending", "working", "completed", "failed"
    phase: str
    outcome: str | None           # "pass", "reject", "waiting_for_ci" (when completed)
    reject_reason: str | None     # Explanation if outcome is "reject"
    error: str | None             # Error message if status is "failed"
    started_at: datetime
    completed_at: datetime | None

# Example
GET /jobs/job-abc123

# Response: 200 OK
{
    "job_id": "job-abc123",
    "status": "completed",
    "phase": "specify",
    "outcome": "pass",
    "reject_reason": null,
    "started_at": "2026-01-09T10:00:00Z",
    "completed_at": "2026-01-09T10:05:00Z"
}
```

### 5.4 Agent Implementation

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()
jobs: dict[str, Job] = {}  # In-memory for simplicity; real impl uses CRD

@app.post("/jobs", status_code=201)
async def create_job(request: CreateJobRequest) -> CreateJobResponse:
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    job = Job(
        job_id=job_id,
        phase=request.phase,
        issue_id=request.issue_id,
        context=request.context,
        status="pending"
    )
    jobs[job_id] = job

    # Start async processing
    asyncio.create_task(process_job(job))

    return CreateJobResponse(job_id=job_id, status="pending")

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> JobStatusResponse:
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id].to_response()

async def process_job(job: Job):
    """Execute the agent's work for this phase."""
    job.status = "working"

    try:
        # Run agent logic (Claude SDK, file operations, etc.)
        result = await run_agent_phase(job.phase, job.context)

        # Commit results to Git journal
        await commit_to_journal(job.issue_id, job.phase, result)

        job.status = "completed"
        job.outcome = result.outcome  # "pass" or "reject"
        job.reject_reason = result.reject_reason

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
```

### 5.5 Service Discovery

Within a Kubernetes namespace, services use simple names:

| Context | URL Pattern | Example |
|---------|-------------|---------|
| **Within workflow namespace** | `http://{agent}:{port}` | `http://baron:8002/jobs` |
| **Cross-namespace (rare)** | `http://{agent}.{namespace}.svc:{port}` | `http://baron.fc-issue-42.svc:8002/jobs` |

**Agent Card (A2A Standard):**

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
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"]
}
```

### 5.6 Why REST over JSON-RPC?

| Factor | JSON-RPC | REST |
|--------|----------|------|
| **Simplicity** | Method names in body | HTTP verbs + URLs |
| **Debugging** | Parse JSON body | `curl GET /jobs/123` |
| **OpenAPI** | Custom tooling | Native support |
| **Caching** | Manual | HTTP cache headers |
| **Our use case** | Overkill | Perfect fit |

We can add JSON-RPC or gRPC bindings later if needed for external agent integration.

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

## 8. Persistence (Git-Journaling)

We use **"Git as the Database"** for workflow persistence. This eliminates DynamoDB costs and leverages the fact that agents already clone the repository.

### 8.1 Two Sources of Truth

| Source | What It Holds | Why |
|--------|---------------|-----|
| **Kubernetes CRD** | Current state pointer (phase index, job ID) | Crash-recoverable, kubectl-editable |
| **Git Journal** | Phase results, logs, metrics | Immutable, auditable, versioned |

**No DynamoDB in the critical path.** DynamoDB is optional for analytics only (fire-and-forget).

### 8.2 Journal Location

Agents write JSON journals directly to the Git repository in a hidden folder:

```
.farmercode/
└── issue-{id}/
    ├── baron.json          # Baron's journal (SPECIFY, PLAN, TASKS)
    ├── marie.json          # Marie's journal (TEST_DESIGN, VERIFY)
    ├── dede.json           # Dede's journal (IMPLEMENT_BACKEND)
    ├── dali.json           # Dali's journal (IMPLEMENT_FRONTEND)
    ├── gus.json            # Gus's journal (IMPLEMENT_GITOPS)
    ├── victor.json         # Victor's journal (DOCS_QA)
    ├── general.json        # General's journal (REVIEW, MERGE)
    ├── vauban.json         # Vauban's journal (RELEASE_STAGING, RELEASE_PROD)
    └── socrate.json        # Socrate's journal (RETRO)
```

### 8.3 Journal Schema

```json
{
  "meta": {
    "agent": "marie",
    "phase": "VERIFY",
    "job_id": "job-uuid-1234",
    "started_at": "2026-01-09T10:00:00Z",
    "last_updated": "2026-01-09T10:05:30Z"
  },
  "status": {
    "phase": "COMPLETED",
    "outcome": "PASS",
    "reject_reason": null,
    "error_msg": null
  },
  "context": {
    "trigger_reason": "Verification after IMPLEMENT_BACKEND",
    "rewind_attempt": 0
  },
  "output": {
    "commit_sha": "abc1234",
    "files_modified": ["src/auth.py", "tests/test_auth.py"],
    "metrics": {
      "tests_run": 47,
      "tests_passed": 47,
      "coverage_percent": 87.3
    }
  },
  "logs": [
    { "ts": "10:01:00", "level": "INFO", "msg": "Starting verification..." },
    { "ts": "10:03:00", "level": "THOUGHT", "msg": "All tests passing" }
  ]
}
```

### 8.4 Status and Outcome Fields

| Field | Values | Purpose |
|-------|--------|---------|
| `status.phase` | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` | Job lifecycle state |
| `status.outcome` | `PENDING`, `PASS`, `REJECT`, `WAITING_FOR_CI` | Business result |

**Outcome meanings:**
- `PASS` → Advance to next phase
- `REJECT` → Trigger rewind to SPECIFY (self-healing)
- `WAITING_FOR_CI` → Stay in phase, wait for CI result
- `FAILED` → Workflow fails, human intervention required

### 8.5 Why Git-Journaling?

| Aspect | DynamoDB (rejected) | Git-Journaling (adopted) |
|--------|---------------------|--------------------------|
| Cost | ~$25/mo minimum | $0 (repo already exists) |
| Audit trail | Query GSI | `git log .farmercode/` |
| Debugging | Read DynamoDB console | `cat .farmercode/issue-42/marie.json` |
| Backup | Point-in-time recovery | Git history (free) |
| Local dev | Run DynamoDB Local | Just use filesystem |
| Recovery | Replay events | Journal already in repo |

### 8.6 Access Patterns

| Pattern | Implementation |
|---------|---------------|
| Get phase result | `git show HEAD:.farmercode/issue-42/marie.json` |
| Get history | `git log --oneline .farmercode/issue-42/` |
| Check if phase done | Read journal, check `status.phase == "COMPLETED"` |
| Rebuild state | CRD has current pointer, journal has last outcome |

---

## 9. Workflow State Machine

### 9.1 Simplified State Model

Instead of complex event sourcing, we use a simple state machine approach:

| Source of Truth | Purpose | Location |
|----------------|---------|----------|
| **CRD status** | Current workflow position | `spec.status.phase`, `spec.status.outcome` |
| **Git Journal** | Phase execution history | `.farmercode/issue-{id}/{agent}.json` |
| **Git artifacts** | Work products (code, specs) | Feature branch |

**Key insight:** Event replay would reconstruct workflow position but not artifacts (AI outputs
are non-deterministic). Since we need Git for artifacts anyway, we store phase history there too
and keep the CRD as the single pointer to "where are we now?"

### 9.2 State Machine Definition

```python
from enum import Enum
from typing import Literal

class Phase(str, Enum):
    SPECIFY = "specify"
    PLAN = "plan"
    TASKS = "tasks"
    TEST_DESIGN = "test_design"
    IMPLEMENT = "implement"
    VERIFY = "verify"
    REVIEW = "review"
    MERGE = "merge"
    AWAIT_STAGING = "await_staging"
    AWAIT_PROD = "await_prod"
    RETRO = "retro"
    DONE = "done"

class Outcome(str, Enum):
    PASS = "pass"           # Phase succeeded, advance to next
    REJECT = "reject"       # Phase failed, rewind to SPECIFY
    WAITING_FOR_CI = "waiting_for_ci"  # Hibernating until Town Crier wakes us

# Linear phase order (happy path)
PHASE_ORDER = [
    Phase.SPECIFY, Phase.PLAN, Phase.TASKS, Phase.TEST_DESIGN,
    Phase.IMPLEMENT, Phase.VERIFY, Phase.REVIEW, Phase.MERGE,
    Phase.AWAIT_STAGING, Phase.AWAIT_PROD, Phase.RETRO, Phase.DONE
]
```

### 9.3 Outcome-Based Transitions

The state machine uses a simple outcome-based model:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  SPECIFY ──▶ PLAN ──▶ TASKS ──▶ TEST_DESIGN ──▶ IMPLEMENT ──▶ VERIFY    │
│     ▲                                                            │       │
│     │                                                            ▼       │
│     │          ◀─────────── outcome: REJECT ◀────────────── REVIEW      │
│     │                                                            │       │
│     │                                                   outcome: PASS    │
│     │                                                            ▼       │
│     │                                                         MERGE      │
│     │                                                            │       │
│     │                                                            ▼       │
│     │                                                    AWAIT_STAGING   │
│     │                                                 (hibernate)  │     │
│     │                                         ◀─ Town Crier wakes  │     │
│     │          ◀─────────── outcome: REJECT ◀────────────────────┘      │
│     │                                                            │       │
│     │                                                            ▼       │
│     │                                                     AWAIT_PROD     │
│     │                                                 (hibernate)  │     │
│     │                                         ◀─ Town Crier wakes  │     │
│     │          ◀─────────── outcome: REJECT ◀────────────────────┘      │
│     │                                                            │       │
│     │                                                            ▼       │
│     └──────────────────────────────────────────────────────── RETRO ───▶ DONE
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Decision logic:**

```python
def next_phase(current: Phase, outcome: Outcome, rewind_count: int) -> Phase | None:
    """Determine next phase based on outcome."""
    MAX_REWINDS = 5

    match outcome:
        case Outcome.PASS:
            # Advance to next phase in linear order
            idx = PHASE_ORDER.index(current)
            if idx + 1 < len(PHASE_ORDER):
                return PHASE_ORDER[idx + 1]
            return None  # Done

        case Outcome.REJECT:
            if rewind_count >= MAX_REWINDS:
                return None  # Escalate to human
            # Always rewind to SPECIFY with rejection reason
            return Phase.SPECIFY

        case Outcome.WAITING_FOR_CI:
            # Stay in current phase, hibernate
            return current
```

### 9.4 Rewind Mechanics

On `outcome: REJECT`, the workflow rewinds to SPECIFY phase. The rejection reason becomes
the new feature description, creating a self-correcting loop:

```python
@dataclass
class RewindContext:
    """Context passed to SPECIFY when rewinding."""
    original_feature: str           # Original issue description
    rejection_reason: str           # Why we were rejected
    rejected_at_phase: str          # Where rejection occurred
    rewind_attempt: int             # 1, 2, 3... (max 5)
    previous_artifacts: list[str]   # Commits from prior attempts

def create_rewind_prompt(ctx: RewindContext) -> str:
    """Create the prompt for the SPECIFY phase on rewind."""
    return f"""
    Original Feature: {ctx.original_feature}

    Previous Attempt #{ctx.rewind_attempt} was REJECTED at {ctx.rejected_at_phase}.

    Rejection Reason: {ctx.rejection_reason}

    Please re-specify this feature addressing the rejection reason.
    """
```

### 9.5 Hibernation States

Two phases involve hibernation while waiting for CI/CD:

| Phase | Trigger | Wake Condition | Mechanism |
|-------|---------|----------------|-----------|
| `AWAIT_STAGING` | ArgoCD deploys to staging | Staging smoke tests pass | Town Crier annotation |
| `AWAIT_PROD` | Manual approval + deploy | Production verification | Town Crier annotation |

During hibernation:
1. Orchestrator pod scales to 0 replicas
2. CRD status shows `outcome: WAITING_FOR_CI`
3. No compute costs incurred
4. Town Crier wakes the orchestrator when deployment succeeds

### 9.6 CRD Status Schema

```yaml
apiVersion: farmercode.io/v1
kind: IssueWorkflow
metadata:
  name: issue-42
  annotations:
    farmercode.io/wake: "true"  # Set by Town Crier to wake
spec:
  repo: "farmer1st/myapp"
  issue_number: 42
status:
  phase: "await_staging"
  outcome: "waiting_for_ci"
  rewind_count: 0
  last_agent: "vauban"
  last_job_id: "job-abc123"
  hibernating_since: "2026-01-09T10:30:00Z"
  history:
    - phase: "specify"
      outcome: "pass"
      agent: "baron"
      completed_at: "2026-01-09T09:00:00Z"
    - phase: "plan"
      outcome: "pass"
      agent: "baron"
      completed_at: "2026-01-09T09:15:00Z"
    # ... etc
```

### 9.7 Comparison: Event Sourcing vs State Machine

| Aspect | Event Sourcing (Old) | State Machine (New) |
|--------|---------------------|---------------------|
| **Complexity** | High (event store, projections, replay) | Low (CRD + journal files) |
| **Infrastructure** | DynamoDB required | Just Kubernetes + Git |
| **Recovery** | Replay events | Read CRD status, resume |
| **Audit trail** | Event stream | Git commit history |
| **Debugging** | Query event store | Read journal files |
| **Cost** | DynamoDB on-demand pricing | Zero (Git is free) |

The simplified approach trades some flexibility (no arbitrary replay) for dramatically
reduced complexity and infrastructure requirements.

---

## 10. Self-Healing Rewind

### 10.1 Simplified Feedback Model

Instead of complex targeted feedback loops (spec ambiguity → SPECIFY, test failure → IMPLEMENT),
we use a simple universal rewind:

**Any REJECT → Rewind to SPECIFY**

| Old Model (Complex) | New Model (Simple) |
|--------------------|-------------------|
| `VERIFY → IMPLEMENT` on test failure | `REJECT → SPECIFY` |
| `REVIEW → PLAN` on architectural issue | `REJECT → SPECIFY` |
| `IMPLEMENT → SPECIFY` on spec ambiguity | `REJECT → SPECIFY` |
| Targeted transitions, complex routing | Single rewind target |

### 10.2 Why Always SPECIFY?

1. **Simplicity**: One rule is easier to implement and debug
2. **Context accumulation**: Each rewind includes the full rejection reason
3. **Self-correcting**: Baron can adjust the spec based on what failed downstream
4. **Predictable**: No complex state machine with multiple back-edges

The rejection reason carries all context needed:

```
Rejection at VERIFY: "Tests fail because spec didn't account for edge case X"
→ Baron rewrites spec to handle edge case X
→ Full pipeline re-runs with improved spec
```

### 10.3 Rewind Loop Protection

Maximum 5 rewind attempts before human escalation:

```python
async def handle_rejection(
    crd: IssueWorkflow,
    rejected_phase: str,
    rejection_reason: str
) -> str:
    """Handle REJECT outcome from any phase."""
    MAX_REWINDS = 5

    rewind_count = crd.status.rewind_count + 1

    if rewind_count > MAX_REWINDS:
        # Too many failures — escalate to human
        await github.post_comment(
            crd.spec.issue_number,
            f"## ⚠️ Human Intervention Required\n\n"
            f"Workflow failed {MAX_REWINDS} times. "
            f"Last rejection at **{rejected_phase}**: {rejection_reason}\n\n"
            f"Please review and provide guidance."
        )
        return "escalated"

    # Create rewind context
    rewind_context = {
        "original_feature": crd.spec.feature_description,
        "rejection_reason": rejection_reason,
        "rejected_at_phase": rejected_phase,
        "rewind_attempt": rewind_count,
    }

    # Update CRD and rewind to SPECIFY
    await update_crd_status(
        crd.metadata.name,
        phase="specify",
        outcome=None,
        rewind_count=rewind_count,
        rewind_context=rewind_context
    )

    return "rewinding"
```

### 10.4 GitHub Notifications

```python
async def post_rewind_comment(
    issue_number: int,
    rejected_phase: str,
    rejection_reason: str,
    rewind_attempt: int
):
    comment = f"""
## 🔄 Workflow Rewinding (Attempt {rewind_attempt}/5)

**Rejected at:** `{rejected_phase}`
**Reason:** {rejection_reason}

The workflow is automatically restarting from SPECIFY to address this issue.
"""
    await github.post_comment(issue_number, comment)
```

### 10.5 Comparison: Complex vs Simple

| Aspect | Complex Feedback Loops | Simple Rewind |
|--------|----------------------|---------------|
| **Transitions** | N×M possible edges | Always → SPECIFY |
| **Decision logic** | Which phase to target? | None needed |
| **Context** | Partial (phase-specific) | Full (rejection reason) |
| **Recovery** | Resume mid-pipeline | Full re-run |
| **Debugging** | "Why did it go to PLAN?" | "It rewound to SPECIFY" |
| **Implementation** | Complex routing table | One `if` statement |

The tradeoff: More compute (full re-run) for dramatically simpler implementation.
Since agent costs dominate and full re-runs are rare, this is acceptable.

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

## 17. Open Questions

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
