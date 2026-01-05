# Plan Workflow Instructions

Execute this workflow to generate an implementation plan from a feature specification.

## Prerequisites

- spec.md file exists at the specified path
- `.specify/templates/plan-template.md` exists
- `.specify/memory/constitution.md` exists
- `.specify/scripts/bash/setup-plan.sh` is executable

## Workflow Steps

### Step 1: Check State (Resumption Support)

Check if this is a resumption from a previous blocked state:

```bash
# Check for existing state file
if [ -f "$SPECS_DIR/.baron-state.json" ]; then
  # Read state and resume from checkpoint
  STATE=$(cat "$SPECS_DIR/.baron-state.json")
fi
```

If state exists with `status: "blocked"`, check escalation status via `check_escalation` MCP tool before continuing.

### Step 2: Read Specification

Read the spec.md file from the dispatch prompt:

1. Parse the `spec_path` from the dispatch prompt
2. Read the full contents of spec.md
3. Extract:
   - Summary and scope
   - User stories
   - Functional requirements
   - Success criteria
   - Assumptions and constraints

### Step 3: Run Setup Script

Execute the setup script to prepare the plan directory:

```bash
.specify/scripts/bash/setup-plan.sh --json
```

Parse the JSON output for:
- `FEATURE_SPEC`: Path to spec.md
- `IMPL_PLAN`: Path to plan.md (template copied)
- `SPECS_DIR`: Feature specs directory
- `BRANCH`: Current branch name

### Step 4: Load Templates and Constitution

1. Read `.specify/templates/plan-template.md`
2. Read `.specify/memory/constitution.md`
3. Understand template structure and required sections
4. Note constitution principles that apply to planning:
   - Principle I: TDD (tests before implementation)
   - Principle VI: YAGNI (no unnecessary complexity)
   - Principle XI: User journey mapping

### Step 5: Phase 0 - Research

Generate `research.md` to resolve unknowns:

1. **Identify unknowns** from spec.md:
   - Technology choices not specified
   - Integration points unclear
   - Architecture decisions pending

2. **Research each unknown**:
   - Consult experts via `ask_expert` MCP tool (max 3 questions)
   - Architecture questions → topic: "architecture" (routes to @duc)
   - Product questions → topic: "product" (routes to @veuve)
   - Testing questions → topic: "testing" (routes to @marie)

3. **Document findings** in `research.md`:
   - Decision: What was chosen
   - Rationale: Why this choice
   - Alternatives: What else was considered

### Step 6: Phase 1 - Design Artifacts

Generate design artifacts from spec and research:

1. **data-model.md**:
   - Extract entities from requirements
   - Define fields and relationships
   - Document validation rules
   - Note state transitions if applicable

2. **contracts/** directory:
   - Generate OpenAPI/GraphQL schemas
   - Define API endpoints from user actions
   - Use standard REST patterns
   - Include request/response models

3. **quickstart.md**:
   - Define local development setup
   - List required tools and dependencies
   - Include test commands

### Step 7: Fill Plan Template

Complete the plan.md template:

1. **Technical Context**:
   - Technology stack decisions
   - Integration points
   - External dependencies
   - Mark unknowns as "NEEDS CLARIFICATION"

2. **Constitution Check Section**:
   - List applicable principles
   - Document compliance approach
   - Note any justified exceptions

3. **User Journey Mapping** (REQUIRED per Principle XI):
   - Assign journey domain code (2-4 letters)
   - Map each user story to a journey ID
   - List journey files to create

4. **Architecture Decisions**:
   - Key design choices
   - Trade-offs considered
   - Rationale for each decision

### Step 8: Update Agent Context

Run the agent context update script:

```bash
.specify/scripts/bash/update-agent-context.sh claude
```

This updates `.claude/CLAUDE.md` with new technology from this plan.

### Step 9: Consult Experts (If Needed)

For complex architecture decisions, use `ask_expert`:

```json
{
  "tool": "ask_expert",
  "topic": "architecture",
  "question": "Should we use WebSockets or SSE for real-time updates?",
  "context": "Feature requires low-latency push notifications"
}
```

If expert consultation is pending (async), save state and continue with other sections.

### Step 10: Output Result

Output the structured result between markers:

```json
<!-- BARON_RESULT_START -->
{
  "success": true,
  "plan_path": "specs/NNN-feature/plan.md",
  "research_path": "specs/NNN-feature/research.md",
  "data_model_path": "specs/NNN-feature/data-model.md",
  "contracts_dir": "specs/NNN-feature/contracts",
  "quickstart_path": "specs/NNN-feature/quickstart.md",
  "duration_seconds": 120.0
}
<!-- BARON_RESULT_END -->
```

## Error Handling

If an error occurs:

1. Log the error context
2. Save partial state to `.baron-state.json`
3. Output error result:

```json
<!-- BARON_RESULT_START -->
{
  "success": false,
  "error": "Descriptive error message",
  "duration_seconds": 30.0
}
<!-- BARON_RESULT_END -->
```

## Blocked State

If waiting for human escalation:

```json
<!-- BARON_RESULT_START -->
{
  "success": false,
  "blocked_on_escalation": true,
  "error": "Waiting for @duc to approve architecture decision",
  "duration_seconds": 45.0
}
<!-- BARON_RESULT_END -->
```

Save state to resume later with completed sections preserved.
