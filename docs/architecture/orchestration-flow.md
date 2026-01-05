# Orchestration Flow

This document describes the complete orchestration system for Farmer Code, including Baron PM Agent, Agent Hub, domain experts, and human escalation flows.

## Overview

Farmer Code uses a multi-agent orchestration system where:

1. **Baron PM Agent** drives the speckit workflow (specify → plan → tasks)
2. **Agent Hub** coordinates expert consultations and human escalations
3. **Domain Experts** provide specialized knowledge (@duc, @veuve, @marie)
4. **Human Reviewers** approve critical decisions and resolve escalations
5. **Orchestrator** manages the overall SDLC state machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER / DEVELOPER                                │
│                     (Feature Request / Approval / Feedback)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATOR SERVICE                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       State Machine                                  │   │
│  │  IDLE → PHASE_1 → PHASE_2 → GATE_1 → DONE                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  BaronDispatcher │  │  Phase Executor  │  │  Label Sync / Polling    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
          │                       │                        │
          ▼                       ▼                        ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐
│   BARON PM       │  │   WORKTREE       │  │   GITHUB INTEGRATION         │
│   AGENT          │  │   MANAGER        │  │                              │
│                  │  │                  │  │  - Issues                    │
│  - Specify       │  │  - Create        │  │  - Comments                  │
│  - Plan          │  │  - Init Plans    │  │  - Labels                    │
│  - Tasks         │  │  - Commit/Push   │  │  - Pull Requests             │
└──────────────────┘  └──────────────────┘  └──────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT HUB (MCP)                                 │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  Question Router │  │  Session Manager │  │  Escalation Handler      │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Expert Agents                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ @duc        │  │ @veuve      │  │ @marie      │  │ @gustave    │  │  │
│  │  │ Architecture│  │ Product     │  │ Testing     │  │ DevOps      │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            HUMAN REVIEWERS                                   │
│                   (Async Escalation Resolution)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Roles

### Baron PM Agent

Baron is a Claude Agent SDK agent that acts as a Product Manager for the speckit workflow:

| Workflow | Input | Output | Purpose |
|----------|-------|--------|---------|
| **Specify** | Feature description | spec.md | Create feature specification |
| **Plan** | spec.md | plan.md + artifacts | Generate implementation plan |
| **Tasks** | plan.md | tasks.md | Generate TDD-ordered task list |

Baron consults domain experts via Agent Hub for specialized questions.

### Agent Hub Experts

| Expert | Topic | Specialty |
|--------|-------|-----------|
| **@duc** | `architecture` | System design, API contracts, data models |
| **@veuve** | `product` | User stories, requirements, success criteria |
| **@marie** | `testing` | Test strategy, edge cases, quality assurance |
| **@gustave** | `devops` | Infrastructure, deployment, CI/CD |
| **@charles** | `security` | Authentication, authorization, compliance |

## Communication Flows

### 1. Baron → Agent Hub → Expert

When Baron needs domain expertise:

```
Baron                    Agent Hub                 Expert (@duc)
  │                          │                          │
  ├──ask_expert(topic,q)────►│                          │
  │                          ├──route_question()───────►│
  │                          │                          ├──process
  │                          │◄──answer(confidence)─────┤
  │                          ├──validate_confidence()   │
  │                          │                          │
  │◄──answer─────────────────┤                          │
  │                          │                          │
```

**MCP Tool Call:**
```json
{
  "tool": "ask_expert",
  "topic": "architecture",
  "question": "Should we use PostgreSQL or MongoDB for user data?",
  "context": "Feature requires complex queries and transactions"
}
```

### 2. Low Confidence → Human Escalation

When an expert's answer has low confidence:

```
Baron          Agent Hub           Expert            Human
  │                │                  │                 │
  ├──ask_expert───►│                  │                 │
  │                ├─────────────────►│                 │
  │                │◄──confidence:65──┤                 │
  │                │                  │                 │
  │                ├──create_escalation()               │
  │                │                  │                 │
  │◄──blocked──────┤                  │                 │
  │                │                  │                 │
  │  (continues    │                  │                 │
  │   other work)  │                  │                 │
  │                │◄───────────────────────response────┤
  │                │                  │                 │
  │◄──answer───────┤                  │                 │
  │                │                  │                 │
```

**Escalation Request (GitHub Issue Comment):**
```markdown
## 🔄 Human Review Required

**Question:** Should we use PostgreSQL or MongoDB for user data?
**Expert:** @duc (Architecture)
**Confidence:** 65%

### Expert's Answer
PostgreSQL would work, but MongoDB might be simpler for this use case.

### Why Review Needed
Confidence below 80% threshold. Multiple valid approaches exist.

### Options
- [ ] **CONFIRM** - Accept expert's answer
- [ ] **CORRECT** - Provide different answer
- [ ] **CONTEXT** - Add more context for re-evaluation

Please reply with your decision.
```

### 3. Session Continuity

Agent Hub maintains conversation sessions for multi-turn interactions:

```
Baron                    Agent Hub                 Expert
  │                          │                        │
  ├──ask_expert(session:A)──►│                        │
  │                          ├──create_session(A)────►│
  │                          │◄──answer───────────────┤
  │◄──answer─────────────────┤                        │
  │                          │                        │
  │ (later...)               │                        │
  │                          │                        │
  ├──ask_expert(session:A)──►│                        │
  │                          ├──resume_session(A)────►│
  │                          │◄──answer (with ctx)────┤
  │◄──answer─────────────────┤                        │
```

Sessions preserve context for follow-up questions within the same feature.

## The Speckit Workflow

### Complete Flow

```
User: "I want to add OAuth2 authentication"
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│                  1. SPECIFY                          │
│                                                      │
│  Input: Natural language description                 │
│  Baron:                                              │
│    - Creates feature branch and directory            │
│    - Loads spec-template.md                          │
│    - Analyzes requirements                           │
│    - Consults @veuve for product questions           │
│    - Writes spec.md                                  │
│  Output: specs/008-oauth2-auth/spec.md               │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│                  2. PLAN                             │
│                                                      │
│  Input: spec.md                                      │
│  Baron:                                              │
│    - Runs research phase (resolve unknowns)          │
│    - Consults @duc for architecture decisions        │
│    - Generates data-model.md                         │
│    - Generates API contracts                         │
│    - Writes plan.md with constitution check          │
│  Output: plan.md, research.md, data-model.md,        │
│          contracts/, quickstart.md                   │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│                  3. TASKS                            │
│                                                      │
│  Input: plan.md                                      │
│  Baron:                                              │
│    - Reads all design artifacts                      │
│    - Applies TDD ordering (tests first)              │
│    - Consults @marie for test strategy               │
│    - Generates dependency-ordered tasks              │
│    - Writes tasks.md                                 │
│  Output: specs/008-oauth2-auth/tasks.md              │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│                  4. IMPLEMENT                        │
│                                                      │
│  Input: tasks.md                                     │
│  Developer/Agent:                                    │
│    - Executes tasks in order                         │
│    - Writes tests first (TDD)                        │
│    - Implements features                             │
│    - Runs quality checks                             │
│  Output: Working code with tests                     │
└─────────────────────────────────────────────────────┘
```

### Baron Result Format

All Baron workflows output structured JSON:

```
Baron executing specify workflow...
[agent activity...]

<!-- BARON_RESULT_START -->
{
    "success": true,
    "spec_path": "specs/008-oauth2-auth/spec.md",
    "feature_id": "008-oauth2-auth",
    "branch_name": "008-oauth2-auth",
    "duration_seconds": 45.2
}
<!-- BARON_RESULT_END -->
```

The BaronDispatcher parses results between these markers.

## SDLC State Machine Integration

Baron workflows integrate with the orchestrator state machine:

```
                    ┌─────────────────────────────────────────────┐
                    │              SDLC PHASES                     │
                    └─────────────────────────────────────────────┘

IDLE ──────────────────────────────────────────────────────────────►
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 1: Setup                                                   │
│  - Create GitHub issue                                            │
│  - Create branch and worktree                                     │
│  - Initialize .plans directory                                    │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 2: Specification (Baron /speckit.specify)                  │
│  - Baron creates spec.md                                          │
│  - Expert consultations via Agent Hub                             │
│  - Human escalations if needed                                    │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 3: Planning (Baron /speckit.plan)                          │
│  - Baron creates plan.md and artifacts                            │
│  - Architecture decisions via @duc                                │
│  - Research phase resolves unknowns                               │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 4: Tasks (Baron /speckit.tasks)                            │
│  - Baron creates tasks.md                                         │
│  - TDD ordering enforced                                          │
│  - Test strategy via @marie                                       │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  GATE 1: Human Approval                                           │
│  - Review spec, plan, tasks                                       │
│  - Approve to proceed with implementation                         │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 5-7: Implementation (/speckit.implement)                   │
│  - Execute tasks in order                                         │
│  - Agent or human implements                                      │
│  - Tests first per TDD                                            │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────┐
│  PHASE 8: Review & Merge                                          │
│  - Create pull request                                            │
│  - Code review                                                    │
│  - Merge to main                                                  │
└──────────────────────────────────────────────────────────────────┘
           │
           ▼
        DONE
```

## Async Escalation Handling

When Baron is blocked on human escalation:

1. **Baron saves state** to `.baron-state.json`
2. **Baron continues** with non-blocked sections
3. **Escalation posted** to GitHub issue
4. **Human responds** (async, could be hours/days)
5. **Next Baron invocation** checks escalation status
6. **Baron resumes** with human response incorporated

```python
# Baron checks escalation status on resume
response = check_escalation(escalation_id)
if response.status == "resolved":
    # Continue with response
    answer = response.final_answer
else:
    # Still pending, continue other work
    continue_non_blocked_sections()
```

## Constitution Compliance

Baron enforces constitution principles throughout:

| Principle | Enforcement |
|-----------|-------------|
| **I. TDD** | Tasks workflow orders tests before implementation |
| **VI. YAGNI** | Plan workflow avoids unnecessary complexity |
| **XI. User Journeys** | Plan workflow maps user stories to journey IDs |

The constitution is loaded at the start of each workflow from `.specify/memory/constitution.md`.

## Error Handling

### Baron Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `DispatchError` | Claude CLI failed | Retry with backoff |
| `ParseError` | Missing result markers | Check agent output |
| `TimeoutError` | Agent took too long | Increase timeout |

### Agent Hub Errors

| Error | Cause | Recovery |
|-------|-------|----------|
| `RoutingError` | Unknown topic | Check topic mapping |
| `SessionNotFound` | Session expired | Create new session |
| `EscalationTimeout` | Human didn't respond | Re-escalate or skip |

## Monitoring & Observability

### Structured Logging

All components log in JSON format:

```json
{
  "timestamp": "2026-01-05T10:00:00Z",
  "level": "info",
  "component": "baron",
  "workflow": "specify",
  "feature_id": "008-oauth2-auth",
  "message": "Consulting expert @duc for architecture",
  "duration_ms": 1500
}
```

### Journey Markers

Integration tests use journey markers for traceability:

```python
@pytest.mark.journey("BRN-001")
def test_baron_creates_spec():
    ...
```

## Related Documentation

- [Baron Agent README](../../.claude/agents/baron/README.md)
- [Agent Hub Architecture](./agent-hub.md)
- [System Overview](./system-overview.md)
- [Module Interactions](./module-interactions.md)
- [User Journeys](../user-journeys/JOURNEYS.md)
- [Constitution](../../.specify/memory/constitution.md)
