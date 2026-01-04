# Feature Specification: Knowledge Router

**Feature Branch**: `004-knowledge-router`
**Created**: 2026-01-03
**Status**: Draft
**Input**: User description: "Question-answer orchestration system where @baron (PM) runs SpecKit commands and asks structured questions, knowledge agents (architect, product) answer without repo access, answers are routed based on confidence thresholds, and all Q&A is logged for retrospective improvement of agent knowledge bases."

## Overview

The Knowledge Router orchestrates a question-answer protocol between @baron (the PM) and specialized agents.

**@baron** is the Project Manager agent - the CLI that runs and executes SpecKit commands. SpecKit is @baron's toolset for creating specifications, plans, and tasks. @baron has full repo access and drives the entire workflow.

This system separates agents into three tiers:

- **@baron (PM)** - The running CLI with full repo access. Executes SpecKit commands, asks questions, writes artifacts, dispatches tasks.
- **Knowledge Agents** (no repo access) - @duc (architect), @veuve (product). Answer questions from their expertise only.
- **Execution Agents** (scoped repo access) - Specialists who write files in designated directories.

### Agent Roster

| Agent | Role | Type | Access Scope |
|-------|------|------|--------------|
| **@baron** | Project Manager | Driver | Full repo, runs SpecKit |
| **@duc** | Architect | Knowledge | None - answers only (ALL technical decisions: backend, frontend, infra, data, security) |
| **@veuve** | Product | Knowledge | None - answers only |
| **@marie** | QA | Execution | `tests/` |
| **@dede** | Developer | Execution | `src/` |
| **@gustave** | DevOps | Execution | `k8s/`, `argocd/`, `kustomize/`, `helm/`, `.github/workflows/` |
| **@degaulle** | Reviewer | Execution | Read-only + review comments |

### Feature Types

Not all features require code. The system supports different feature types:

| Type | Description | Agents Involved |
|------|-------------|-----------------|
| **Full Stack** | New feature with frontend + backend + tests | @duc, @veuve, @marie, @dede, @degaulle |
| **Backend Only** | API or service changes | @duc, @veuve, @marie, @dede, @degaulle |
| **Infra/DevOps** | Deploy app, add manifests, ArgoCD config | @duc, @veuve, @gustave, @degaulle |
| **Capacity Change** | Scale pods, adjust resources | @gustave, @degaulle |
| **Config Update** | Environment variables, feature flags | @gustave |

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENT ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  KNOWLEDGE AGENTS (no repo)        EXECUTION AGENTS (scoped access)      │
│  ─────────────────────────         ────────────────────────────────      │
│  @duc    - ALL architecture        @marie    - tests/                    │
│  @veuve  - Product/business        @dede     - src/                      │
│                                    @gustave  - k8s/, argocd/, helm/      │
│                                    @degaulle - reviewer (read + comment) │
│           │                                      │                       │
│           │ answers                              │ code/manifests        │
│           ▼                                      ▼                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    @baron (PM Agent)                             │    │
│  │              The CLI that runs SpecKit commands                  │    │
│  │                  (has full repo access)                          │    │
│  │                                                                  │    │
│  │  • Runs /speckit.specify, /speckit.clarify, /speckit.plan, etc  │    │
│  │  • Generates structured questions                                │    │
│  │  • Routes questions to knowledge agents                          │    │
│  │  • Validates answers against confidence threshold                │    │
│  │  • Writes artifacts (spec.md, plan.md, tasks.md)                │    │
│  │  • Dispatches tasks to execution agents                          │    │
│  │  • Logs all Q&A for retrospectives                              │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│                     ┌─────────────────┐                                  │
│                     │     HUMAN       │                                  │
│                     │  (escalations,  │                                  │
│                     │   approvals)    │                                  │
│                     └─────────────────┘                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **@baron drives** - As the PM, @baron knows what information is needed and runs SpecKit to create artifacts
2. **Agents answer** - Knowledge agents provide expertise, not file operations
3. **Confidence gates** - Low-confidence answers escalate to humans
4. **Learning loop** - All Q&A is logged for retrospective improvement

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Route Questions to Knowledge Agents (Priority: P1)

@baron generates structured questions while running SpecKit commands (e.g., during `/speckit.specify`). Each question has a suggested target (architect, product, human). The Knowledge Router dispatches questions to the appropriate knowledge agent based on topic and routing configuration.

**Why this priority**: This is the core capability. Without question routing, knowledge agents cannot contribute to the workflow.

**Independent Test**: Can be tested by submitting a question with target "architect", verifying it reaches @duc, and receiving a structured answer.

**Acceptance Scenarios**:

1. **Given** a question tagged `target: architect` about authentication methods, **When** routed, **Then** the question is dispatched to @duc with only the question context (no repo access).
2. **Given** a question tagged `target: product` about feature scope, **When** routed, **Then** the question is dispatched to @veuve.
3. **Given** routing configuration overrides "budget" topic to always go to human, **When** a budget question arrives with `target: architect`, **Then** the override applies and question goes to human.

---

### User Story 2 - Receive and Validate Agent Answers (Priority: P1)

Knowledge agents return structured answers with a confidence score (0-100%). The router validates the confidence against a threshold (default 80%). High-confidence answers are returned to @baron for artifact creation. Low-confidence answers escalate to human.

**Why this priority**: Confidence-based routing is the quality gate that prevents uncertain answers from becoming artifacts. This protects spec quality.

**Independent Test**: Can be tested by submitting an answer with 65% confidence, verifying it triggers human escalation rather than returning to @baron.

**Acceptance Scenarios**:

1. **Given** an agent answer with confidence 92%, **When** validated against 80% threshold, **Then** answer is accepted and returned to @baron.
2. **Given** an agent answer with confidence 65%, **When** validated, **Then** answer is escalated to human with the agent's tentative answer, rationale, and uncertainty reasons.
3. **Given** confidence threshold configured at 90% for "security" topics, **When** a security answer arrives at 85%, **Then** it escalates despite being above default threshold.

---

### User Story 3 - Escalate Low-Confidence Answers to Human (Priority: P1)

When an agent's confidence is below threshold, the human receives the tentative answer with full context. Human can confirm, correct, or provide additional context for the agent to re-answer.

**Why this priority**: Human escalation is the safety net. Without it, uncertain answers would either block the workflow or produce low-quality artifacts.

**Independent Test**: Can be tested by triggering an escalation, verifying human sees all context, and confirming each response option (confirm/correct/add context) works.

**Acceptance Scenarios**:

1. **Given** an escalated answer, **When** human confirms it, **Then** the original answer is returned to @baron with `validated_by: human` flag.
2. **Given** an escalated answer, **When** human corrects it, **Then** the corrected answer is returned to @baron with human as the source.
3. **Given** an escalated answer, **When** human provides additional context, **Then** the question is re-routed to the original agent with the new context appended.
4. **Given** an escalated answer, **When** human chooses to chat directly with @baron, **Then** an interactive session begins for that question only.

---

### User Story 4 - Log All Q&A for Retrospectives (Priority: P1)

Every question, answer, confidence score, escalation, and human intervention is logged. This data enables post-feature retrospectives to identify improvement opportunities for agent knowledge bases.

**Why this priority**: The learning loop is what makes this system improve over time. Without logging, there's no path to better agent confidence.

**Independent Test**: Can be tested by completing a feature workflow, then retrieving the Q&A log and verifying all interactions are captured with timestamps.

**Acceptance Scenarios**:

1. **Given** a completed feature workflow, **When** the Q&A log is retrieved, **Then** it contains all questions asked, answers received, confidence scores, and routing decisions.
2. **Given** a human escalation occurred, **When** the log is reviewed, **Then** it includes the original agent answer, human action taken, and any additional context provided.
3. **Given** a question was re-routed after additional context, **When** the log is reviewed, **Then** both the original and follow-up exchanges are linked.

---

### User Story 5 - Dispatch Execution Tasks to Specialists (Priority: P2)

After SpecKit creates tasks.md, individual tasks are dispatched to execution agents based on task type. Unlike knowledge agents, execution agents have scoped repo access limited to their designated directories.

**Why this priority**: Task execution is essential but follows the knowledge phase. The Q&A protocol must work before tasks can be created.

**Independent Test**: Can be tested by dispatching a task to @dede, verifying they receive only that task's context and can only modify files within scope.

**Acceptance Scenarios**:

1. **Given** a test task from tasks.md, **When** dispatched, **Then** @marie receives the task details, acceptance criteria, and write access only to `tests/`.
2. **Given** an implementation task, **When** dispatched, **Then** @dede receives the task, related test file paths, and write access only to `src/`.
3. **Given** an infrastructure task (e.g., "deploy Grafana Alloy"), **When** dispatched, **Then** @gustave receives the task and write access only to `k8s/`, `argocd/`, `kustomize/`, `helm/`.
4. **Given** an execution agent attempts to modify files outside their scope, **When** detected, **Then** the operation is blocked and logged.
5. **Given** a review task, **When** dispatched, **Then** @degaulle receives read access to changed files and can post review comments.

---

### User Story 6 - Configure Routing Rules (Priority: P2)

Administrators configure routing rules: topic-to-agent mappings, confidence thresholds per topic, model selection per agent role, and override rules.

**Why this priority**: Configurability enables tuning the system to organizational needs. Important but can use sensible defaults initially.

**Independent Test**: Can be tested by modifying routing config, then verifying questions are routed according to new rules.

**Acceptance Scenarios**:

1. **Given** routing config maps "authentication" to "architect", **When** an auth question arrives, **Then** it routes to @duc.
2. **Given** confidence threshold for "compliance" is set to 95%, **When** a compliance answer arrives at 90%, **Then** it escalates despite high confidence.
3. **Given** model config maps "architect" to "opus", **When** @duc is invoked, **Then** the opus model is used.

---

### User Story 7 - Generate Retrospective Report (Priority: P2)

After feature completion, generate a retrospective report analyzing Q&A patterns: which questions had low confidence, what additional context humans provided, and recommendations for improving agent knowledge.

**Why this priority**: The retro report turns logged data into actionable improvements. Important for the learning loop but not blocking for core workflow.

**Independent Test**: Can be tested by completing a feature with varied confidence levels, then generating the report and verifying insights are present.

**Acceptance Scenarios**:

1. **Given** a completed feature with 15 questions (11 high-confidence, 4 escalated), **When** retro report is generated, **Then** it shows 73% direct acceptance rate and lists the 4 escalated topics.
2. **Given** humans frequently added "customer segment" context, **When** report is generated, **Then** it recommends adding customer segment to the feature intake template.
3. **Given** @duc consistently low confidence on "caching" questions, **When** report is generated, **Then** it recommends updating @duc's knowledge base with caching patterns.

---

### User Story 8 - Handle Agent Unavailability (Priority: P3)

If a knowledge agent times out or fails, the system gracefully degrades: escalate to human or try an alternate agent.

**Why this priority**: Robustness is important but edge case. Core happy path takes precedence.

**Independent Test**: Can be tested by simulating agent timeout, verifying graceful escalation to human.

**Acceptance Scenarios**:

1. **Given** @duc times out after 2 minutes, **When** detected, **Then** the question escalates to human with note "Agent unavailable".
2. **Given** @duc fails with error, **When** detected, **Then** the error is logged and question escalates to human.
3. **Given** fallback config specifies @veuve as backup for @duc, **When** @duc is unavailable, **Then** question routes to @veuve before escalating to human.

---

### Edge Cases

- What happens when a question has no clear target (ambiguous topic)?
- How does the system handle conflicting answers from multiple agents?
- What happens if human doesn't respond to an escalation within a time limit?
- How are circular dependencies in questions handled (Q2 depends on Q1 answer)?
- What happens if the confidence threshold is set to 100% (all answers escalate)?
- How does the system handle very long agent responses that exceed context limits?

## Requirements *(mandatory)*

### Functional Requirements

**Question Routing**
- **FR-001**: System MUST route questions based on topic-to-agent configuration.
- **FR-002**: System MUST support routing overrides that supersede @baron's suggested target.
- **FR-003**: System MUST support topic-specific confidence thresholds.
- **FR-004**: System MUST dispatch questions to knowledge agents without repo access.

**Answer Validation**
- **FR-005**: System MUST validate agent answers against confidence threshold (default 80%).
- **FR-006**: System MUST accept high-confidence answers and return to @baron.
- **FR-007**: System MUST escalate low-confidence answers to human.
- **FR-008**: System MUST include agent's tentative answer, rationale, and uncertainty reasons in escalations.

**Human Escalation**
- **FR-009**: System MUST allow humans to confirm escalated answers.
- **FR-010**: System MUST allow humans to correct escalated answers.
- **FR-011**: System MUST allow humans to provide additional context for re-routing to agent.
- **FR-012**: System MUST allow humans to enter direct chat with @baron for complex clarifications.

**Q&A Logging**
- **FR-013**: System MUST log all questions with timestamp, target, topic, and routing decision.
- **FR-014**: System MUST log all answers with confidence, rationale, and uncertainty reasons.
- **FR-015**: System MUST log all human interventions with action taken and context provided.
- **FR-016**: System MUST link related Q&A exchanges (re-routes, follow-ups).

**Task Execution**
- **FR-017**: System MUST dispatch execution tasks to specialist agents with scoped repo access.
- **FR-018**: System MUST enforce file access boundaries per execution agent role:
  - @marie: `tests/` only
  - @dede: `src/` only
  - @gustave: `k8s/`, `argocd/`, `kustomize/`, `helm/`, `.github/workflows/`
  - @degaulle: read-only + review comments
- **FR-019**: System MUST include only task-relevant context for execution agents.
- **FR-020**: System MUST support infrastructure-only features that bypass @marie and @dede.

**Configuration**
- **FR-021**: System MUST support configurable topic-to-agent routing rules.
- **FR-022**: System MUST support configurable confidence thresholds per topic.
- **FR-023**: System MUST support configurable model selection per agent role.
- **FR-024**: System MUST support configurable timeout per agent role.

**Retrospective**
- **FR-025**: System MUST generate retrospective reports from Q&A logs.
- **FR-026**: System MUST identify patterns in low-confidence answers.
- **FR-027**: System MUST recommend improvements based on human intervention patterns.

### Key Entities

- **Question**: A structured query from @baron with id, topic, suggested target, context, and optional answer choices.
- **Answer**: An agent's response with question reference, answer content, rationale, confidence score (0-100), and uncertainty reasons.
- **EscalationRequest**: A low-confidence answer packaged for human review with all context needed to confirm, correct, or enrich.
- **HumanResponse**: Human's action on an escalation: confirm, correct (with new answer), or add_context (for re-routing).
- **RoutingRule**: Configuration mapping topics to agents, with optional confidence threshold override.
- **QALogEntry**: Immutable record of a question-answer exchange for retrospective analysis.
- **ExecutionTask**: A task extracted from tasks.md with scoped file access permissions for specialist agents.
- **RetroReport**: Aggregated analysis of Q&A patterns with improvement recommendations.

### Service Interface

**Service**: KnowledgeRouterService

| Method                 | Purpose                                    | Inputs                                | Outputs            |
|------------------------|--------------------------------------------|---------------------------------------|--------------------|
| `route_question()`     | Route question to appropriate agent        | Question                              | AgentHandle        |
| `submit_answer()`      | Receive and validate agent answer          | Answer                                | AcceptedOrEscalate |
| `escalate_to_human()`  | Package low-confidence answer for human    | Answer, Question                      | EscalationRequest  |
| `handle_human_response()` | Process human's escalation response     | EscalationRequest, HumanResponse      | Answer (final)     |
| `dispatch_task()`      | Send execution task to specialist          | ExecutionTask, role                   | AgentHandle        |
| `get_qa_log()`         | Retrieve Q&A log for a feature             | feature_id                            | list[QALogEntry]   |
| `generate_retro()`     | Generate retrospective report              | feature_id                            | RetroReport        |
| `configure_routing()`  | Update routing rules                       | list[RoutingRule]                     | void               |
| `get_agent_status()`   | Check status of dispatched agent           | AgentHandle                           | AgentStatus        |

**Error Conditions**:
- Agent timeout: Escalate to human with "unavailable" note
- Invalid topic: Route to human with "unknown topic" note
- Configuration error: Fail fast with clear error message
- Human escalation timeout: Configurable behavior (block or use agent answer with warning)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Questions are routed to correct agent based on configuration 100% of the time.
- **SC-002**: Confidence threshold correctly gates answers (high → accept, low → escalate) 100% of the time.
- **SC-003**: Human escalations include complete context for decision-making in 100% of cases.
- **SC-004**: Q&A log captures all exchanges with no data loss.
- **SC-005**: Retrospective reports correctly identify improvement opportunities based on logged patterns.
- **SC-006**: Average feature confidence score improves by 10% after implementing retro recommendations.
- **SC-007**: Execution agents cannot access files outside their designated scope.
- **SC-008**: System handles at least 5 concurrent agent interactions without conflicts.

## Assumptions

- Claude CLI (`claude`) is installed on the system and available in PATH.
- @baron generates questions in the defined structured format while running SpecKit commands.
- Knowledge agents have comprehensive knowledge bases loaded via system prompts.
- Human escalations are handled via GitHub issue comments (or alternative UI).
- tasks.md follows a parseable format with clear task boundaries.
- Routing configuration is provided at initialization or via configuration file.

## Dependencies

- **Orchestrator State Machine (003)**: Triggers @baron to start feature workflows.
- **Git Worktree Manager (002)**: Provides worktree paths where @baron and execution agents operate.
- **SpecKit**: The command set that @baron executes to create artifacts.
- **Claude CLI**: External dependency for spawning @baron and other agents.
- **GitHub Integration (001)**: For human escalation via issue comments.
