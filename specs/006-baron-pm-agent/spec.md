# Feature Specification: Baron PM Agent

**Feature Branch**: `006-baron-pm-agent`
**Created**: 2026-01-05
**Status**: Draft
**Input**: Baron PM Agent - autonomous planning agent that creates specs, plans, and tasks using speckit workflows

## Overview

Baron is an autonomous Project Manager (PM) agent that handles the planning phases of feature development. When triggered by a feature request, Baron creates the specification (spec.md), implementation plan (plan.md), and task list (tasks.md) by executing speckit-like workflows autonomously. Baron uses the Agent Hub to consult domain experts (@duc, @veuve, @marie) when clarification is needed and handles async human escalations gracefully.

Baron is a "planner" agent - it does NOT write code. After Baron completes its work, the Workflow Orchestrator triggers the implementation agent (@dede) to execute the tasks.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Feature Specification (Priority: P1)

When a feature request is received, Baron autonomously creates a complete feature specification document (spec.md) by analyzing the request, consulting experts as needed, and writing a structured specification.

**Why this priority**: The specification is the foundation - without it, no planning or implementation can happen. This is Baron's core value proposition.

**Independent Test**: Can be fully tested by providing a feature description and verifying Baron produces a valid spec.md that follows the template structure.

**Acceptance Scenarios**:

1. **Given** a feature description, **When** Baron executes the specify workflow, **Then** a spec.md file is created in the correct specs directory
2. **Given** a feature description with unclear requirements, **When** Baron needs clarification, **Then** Baron consults the appropriate expert via Agent Hub
3. **Given** an expert provides a low-confidence answer, **When** human escalation is triggered, **Then** Baron waits for resolution before continuing
4. **Given** a complete specification, **When** Baron finishes, **Then** the spec contains all mandatory sections (user stories, requirements, success criteria)

---

### User Story 2 - Generate Implementation Plan (Priority: P1)

After the specification is complete, Baron generates an implementation plan (plan.md) that includes technical context, research findings, data models, and API contracts.

**Why this priority**: The plan bridges specification to implementation - it's essential for the implementation agent to understand HOW to build the feature.

**Independent Test**: Can be tested by providing a spec.md and verifying Baron produces a valid plan.md with all required sections.

**Acceptance Scenarios**:

1. **Given** a complete spec.md, **When** Baron executes the plan workflow, **Then** a plan.md file is created
2. **Given** technical questions arise, **When** Baron consults @duc (Architect), **Then** the answers are incorporated into the Technical Context section
3. **Given** the plan requires research, **When** Baron executes Phase 0, **Then** a research.md file is created with findings
4. **Given** the feature involves data, **When** Baron completes planning, **Then** a data-model.md file is created

---

### User Story 3 - Generate Task List (Priority: P1)

After the plan is complete, Baron generates an actionable task list (tasks.md) with dependency ordering that the implementation agent can execute.

**Why this priority**: Tasks are the executable units - without them, the implementation agent cannot proceed.

**Independent Test**: Can be tested by providing a plan.md and verifying Baron produces a valid tasks.md with ordered, testable tasks.

**Acceptance Scenarios**:

1. **Given** a complete plan.md, **When** Baron executes the tasks workflow, **Then** a tasks.md file is created
2. **Given** tasks have dependencies, **When** tasks.md is generated, **Then** tasks are ordered so dependencies come first
3. **Given** each task, **When** listed in tasks.md, **Then** the task includes acceptance criteria and test requirements
4. **Given** the constitution requires TDD, **When** tasks are generated, **Then** each implementation task is preceded by a test task

---

### User Story 4 - Handle Async Human Escalation (Priority: P2)

When Baron receives a "pending" response from an expert consultation (indicating human escalation), Baron continues with non-blocked work and checks back periodically until the escalation is resolved.

**Why this priority**: Enables Baron to be productive during human review delays rather than blocking entirely.

**Independent Test**: Can be tested by simulating a pending escalation and verifying Baron continues with other sections, then incorporates the answer when resolved.

**Acceptance Scenarios**:

1. **Given** an expert returns "pending_human" status, **When** Baron has other sections to complete, **Then** Baron continues with non-blocked work
2. **Given** a pending escalation, **When** Baron periodically checks status, **Then** status is retrieved via `check_escalation`
3. **Given** an escalation is resolved, **When** Baron checks status, **Then** Baron incorporates the answer and completes the blocked section
4. **Given** an escalation returns "needs_reroute", **When** Baron receives additional context, **Then** Baron re-asks the expert with the new context

---

### User Story 5 - Consult Domain Experts (Priority: P2)

During any workflow phase, Baron can consult domain experts through the Agent Hub when it needs specialized knowledge or faces uncertainty.

**Why this priority**: Expert consultation ensures Baron makes informed decisions rather than guessing.

**Independent Test**: Can be tested by triggering situations where Baron needs expert input and verifying correct expert is consulted.

**Acceptance Scenarios**:

1. **Given** a question about system architecture, **When** Baron needs clarification, **Then** Baron calls `ask_expert` with topic "architecture" (routes to @duc)
2. **Given** a question about product requirements, **When** Baron needs clarification, **Then** Baron calls `ask_expert` with topic "product" (routes to @veuve)
3. **Given** a question about testing strategy, **When** Baron needs clarification, **Then** Baron calls `ask_expert` with topic "testing" (routes to @marie)
4. **Given** an expert answer with high confidence, **When** Baron receives the response, **Then** Baron incorporates the answer and continues

---

### User Story 6 - Respect Constitution Principles (Priority: P2)

Baron must read and apply the project constitution principles during all planning activities, ensuring generated artifacts comply with established standards.

**Why this priority**: Constitution compliance ensures consistency across all features and prevents violations during planning.

**Independent Test**: Can be tested by checking that generated artifacts reference and comply with constitution principles.

**Acceptance Scenarios**:

1. **Given** the constitution exists, **When** Baron starts any workflow, **Then** Baron reads the constitution first
2. **Given** TDD is required by constitution, **When** generating tasks, **Then** test tasks precede implementation tasks
3. **Given** thin-client architecture is required, **When** planning UI features, **Then** all business logic is planned for backend
4. **Given** the constitution check section in plan template, **When** Baron completes planning, **Then** the section is filled with compliance verification

---

### Edge Cases

- What happens when Baron cannot determine the right expert to consult? Route to default expert or ask human
- How does Baron handle conflicting expert answers? Escalate conflict to human for resolution
- What happens when Baron's workflow is interrupted? Save state and resume from last checkpoint
- How does Baron handle extremely large feature requests? Break into sub-features or request decomposition
- What happens when all experts have low confidence? Escalate the entire question chain to human

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Baron MUST execute the specify workflow to create spec.md from a feature description
- **FR-002**: Baron MUST execute the plan workflow to create plan.md from a specification
- **FR-003**: Baron MUST execute the tasks workflow to create tasks.md from a plan
- **FR-004**: Baron MUST consult domain experts via Agent Hub when facing uncertainty
- **FR-005**: Baron MUST handle async human escalations without blocking entirely
- **FR-006**: Baron MUST read and apply the project constitution during planning
- **FR-007**: Baron MUST follow the spec, plan, and task templates defined in the project
- **FR-008**: Baron MUST create artifacts in the correct directory structure (specs/NNN-feature-name/)
- **FR-009**: Baron MUST NOT write implementation code (that is @dede's responsibility)
- **FR-010**: Baron MUST report completion status to the Workflow Orchestrator

### Key Entities

- **BaronAgent**: The autonomous PM agent that executes planning workflows
- **PlanningWorkflow**: Represents the current workflow state (specify, plan, tasks)
- **WorkflowState**: Tracks progress through workflow phases and blocked sections
- **ExpertConsultation**: Record of a question asked to an expert and its resolution

### Service Interface

**Service**: BaronAgent

| Method             | Purpose                              | Inputs                    | Outputs               |
|--------------------|--------------------------------------|---------------------------|-----------------------|
| `run_specify()`    | Execute specify workflow             | feature_description       | SpecifyResult         |
| `run_plan()`       | Execute plan workflow                | spec_path                 | PlanResult            |
| `run_tasks()`      | Execute tasks workflow               | plan_path                 | TasksResult           |
| `run_full_cycle()` | Execute all three workflows in order | feature_description       | FullCycleResult       |
| `get_status()`     | Get current workflow status          | workflow_id               | WorkflowStatus        |
| `resume()`         | Resume interrupted workflow          | workflow_id               | ResumeResult          |

**Error Conditions**:
- Invalid feature description: Returns error requesting more detail
- Expert consultation timeout: Returns partial result with blocked sections noted
- Template not found: Returns error with template path
- Constitution not found: Returns error (cannot proceed without constitution)

## Architecture Context

### Baron in the Agent Ecosystem

```
Workflow Orchestrator
        │
        ├── trigger: "planning" phase
        ▼
┌─────────────────┐
│     BARON       │
│   (PM Agent)    │
│                 │
│  Uses: Agent    │
│  Hub MCP tools  │
└────────┬────────┘
         │
         │ ask_expert()
         │ check_escalation()
         ▼
┌─────────────────┐
│   AGENT HUB     │
│                 │
│  @duc, @veuve,  │
│  @marie, human  │
└─────────────────┘
```

### Baron's Agentic Loop

Baron runs as an SDK agent with an agentic loop that:
1. Reads the feature description and constitution
2. Determines what to do next (THINK)
3. Uses tools to accomplish it (ACT) - read/write files, consult experts
4. Observes results (OBSERVE)
5. Decides if more work is needed (DECIDE)
6. Repeats until workflow is complete

### Speckit Integration

Baron incorporates the logic from speckit skills:
- Reads templates from `.specify/templates/`
- Runs bash scripts from `.specify/scripts/bash/`
- Follows the same workflow structure as interactive speckit
- Key difference: Baron makes decisions autonomously rather than asking the user

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Baron creates valid spec.md files that pass the quality checklist (100% of mandatory sections complete)
- **SC-002**: Baron creates valid plan.md files with all required artifacts (research.md, data-model.md when applicable)
- **SC-003**: Baron creates valid tasks.md files with correctly ordered, testable tasks
- **SC-004**: Expert consultations are routed to correct agents based on topic (100% accuracy)
- **SC-005**: Async escalations are handled without blocking unrelated work
- **SC-006**: Generated artifacts comply with constitution principles (verified by constitution check section)
- **SC-007**: Baron completes a full planning cycle (specify + plan + tasks) within 10 minutes for typical features

## Assumptions

- The Agent Hub (Feature 005) is complete and operational
- The Workflow Orchestrator can trigger Baron and receive completion status
- Expert agents (@duc, @veuve, @marie) are available via Agent Hub
- Templates and scripts in `.specify/` are stable and tested
- The constitution is complete and up-to-date

## Dependencies

- Feature 005 (Agent Hub Refactor) must be complete - Baron uses Agent Hub for expert consultation
- Feature 003 (Orchestrator State Machine) provides the trigger mechanism
- Claude Agent SDK for autonomous agent execution
