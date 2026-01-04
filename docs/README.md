# FarmCode Documentation

Welcome to the FarmCode documentation. This project implements an AI-driven orchestration system for automated software development lifecycle (SDLC) management.

## Quick Links

| Section | Description |
|---------|-------------|
| [Getting Started](./getting-started/README.md) | Setup, installation, and first steps |
| [Architecture](./architecture/README.md) | System design, module interactions, diagrams |
| [Modules](./modules/README.md) | Detailed module documentation |
| [API Reference](./api/README.md) | REST API and library documentation |
| [User Journeys](./user-journeys/JOURNEYS.md) | End-to-end workflow documentation |
| [Configuration](./configuration/README.md) | Environment variables and config files |
| [Testing](./testing/README.md) | How to run and write tests |

## Project Overview

FarmCode is an AI-orchestrated development system that:

- **Automates SDLC Phases**: Issues, specs, planning, implementation, review
- **Routes Questions**: Intelligent routing to specialist AI agents
- **Manages Git Worktrees**: Isolated development environments per feature
- **Tracks Workflow State**: State machine managing phase transitions
- **Validates Quality**: Confidence-based answer validation with human escalation

## Core Modules

| Module | Purpose | Documentation |
|--------|---------|---------------|
| `github_integration` | GitHub API operations (issues, PRs, comments) | [Module Docs](./modules/github-integration.md) |
| `worktree_manager` | Git worktree creation and management | [Module Docs](./modules/worktree-manager.md) |
| `orchestrator` | SDLC workflow state machine | [Module Docs](./modules/orchestrator.md) |
| `knowledge_router` | AI agent Q&A routing and validation | [Module Docs](./modules/knowledge-router.md) |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FarmCode Orchestrator                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   GitHub     │  │   Worktree   │  │   Knowledge      │  │
│  │ Integration  │◄─┤   Manager    │◄─┤   Router         │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                 │                   │             │
│         ▼                 ▼                   ▼             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Orchestrator Service                 │  │
│  │  (State Machine, Phase Execution, Agent Dispatch)    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

See [Architecture Documentation](./architecture/README.md) for detailed diagrams.

## Getting Started

1. **Clone the repository**:
   ```bash
   git clone https://github.com/farmer1st/farmcode.git
   cd farmcode
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run tests**:
   ```bash
   uv run pytest
   ```

4. **Read the getting started guide**: [Getting Started](./getting-started/README.md)

## Key Concepts

### SDLC Workflow

FarmCode implements an 8-phase SDLC workflow:

1. **Issue & Worktree Creation** - Branch and workspace setup
2. **Architecture & Specs** - System design (Gate 1)
3. **Implementation Plans** - Execution planning (Gate 2)
4. **Test Design** - Test planning (Gate 3)
5. **Implementation** - TDD development
6. **Code Review** - Agent review against specs
7. **Human Review** - Final approval (Gate 4)
8. **Merge & Deploy** - Integration to main

### Knowledge Routing

Questions are routed to specialist AI agents based on topic:

- **@duc** - Architecture, design patterns
- **@gustave** - DevOps, infrastructure
- **@marie** - Testing, QA
- **@dede** - Code review, debugging
- **@dali** - Frontend, UI/UX

Answers are validated against confidence thresholds (default 80%), with low-confidence answers escalated to human review.

## Constitution

This project follows a strict constitution defining development principles:

- **Test-First Development** (NON-NEGOTIABLE)
- **Specification-Driven Development**
- **Independent User Stories**
- **Human Approval Gates**
- **Thin Client Architecture** (NON-NEGOTIABLE)

See [Constitution](./.specify/memory/constitution.md) for full details.

## Contributing

1. Read the [Development Workflow](./getting-started/development-workflow.md)
2. Follow the [Constitution](../.specify/memory/constitution.md)
3. Create a feature branch with proper naming
4. Write tests first (TDD is mandatory)
5. Submit PR with documentation updates

## Related Documentation

- [SpecKit Templates](../.specify/templates/) - Feature specification templates
- [Feature Specs](../specs/) - Completed feature specifications
- [SDLC Workflow Reference](../references/sdlc-workflow.md) - Detailed workflow phases
