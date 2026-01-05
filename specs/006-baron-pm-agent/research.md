# Research: Baron PM Agent

**Feature**: 006-baron-pm-agent
**Date**: 2026-01-05
**Status**: Complete

## Research Topics

### 1. Baron Execution Model

**Decision**: Baron runs as a Claude Agent SDK agent dispatched by the Orchestrator via ClaudeCLIRunner

**Rationale**:
- Baron is an AGENT with system prompts and tool access, NOT a Python library
- Reuses existing ClaudeCLIRunner infrastructure from orchestrator module
- Claude CLI supports MCP servers for Agent Hub integration
- Agent prompts define workflow logic; Python only handles dispatch
- Consistent with existing agent dispatch patterns

**Alternatives Considered**:
- Python library with classes/methods: Rejected - overcomplicates what should be agent behavior
- Standalone Python script: Rejected - doesn't integrate with orchestrator workflow
- FastAPI service: Rejected - overcomplicated for single-purpose agent

**Implementation Pattern**:
```python
# BaronDispatcher triggers Baron via ClaudeCLIRunner
class BaronDispatcher:
    def dispatch_specify(self, feature_description: str) -> SpecifyResult:
        """Dispatch Baron to run specify workflow."""
        prompt = self._load_dispatch_prompt("specify", feature_description)
        result = self.runner.dispatch(
            prompt=prompt,
            system_prompt=self._load_system_prompt(),
            mcp_servers=["agent-hub"],
            allowed_tools=["Read", "Write", "Bash", "Glob", "Grep"],
            model="sonnet",
            timeout=600,
        )
        return self._parse_specify_result(result)
```

**Agent Configuration**:
```yaml
# .claude/agents/baron/config.yaml
name: baron-pm
model: claude-sonnet-4-20250514
tools:
  - Read      # Read templates, specs, constitution
  - Write     # Write spec.md, plan.md, tasks.md, state files
  - Bash      # Run .specify/scripts/bash/* scripts
  - Glob      # Find files
  - Grep      # Search codebase
mcp_servers:
  - agent-hub  # ask_expert, check_escalation
timeout: 600   # 10 minutes for full cycle
```

### 2. Agent Hub MCP Integration

**Decision**: Baron uses Agent Hub via MCP tools, not direct Python imports

**Rationale**:
- Baron runs as external agent (spawned process)
- MCP is the standard for Claude tool integration
- Clean separation - Baron doesn't import agent_hub internals
- Follows existing pattern from Agent Hub research

**MCP Tools Available**:
```
ask_expert(topic, question, context, session_id) -> HubResponse
check_escalation(escalation_id) -> EscalationRequest
```

**Expert Topics Baron Uses**:
- `architecture` → @duc for technical decisions
- `product` → @veuve for requirements clarification
- `testing` → @marie for test strategy questions

**Session Management**:
- Baron maintains session_id across related questions
- Sessions enable multi-turn conversation with context
- Close session when workflow section completes

### 3. Template Loading Strategy

**Decision**: Baron uses Read tool directly to load templates from `.specify/templates/`

**Rationale**:
- Baron is an agent with full Read tool access
- Templates are markdown files - simple text processing
- No Python code needed; agent handles string manipulation natively
- Claude excels at understanding and filling structured templates

**Templates Baron Uses**:
```
.specify/templates/
├── spec-template.md       # For /speckit.specify
├── plan-template.md       # For /speckit.plan
└── tasks-template.md      # For /speckit.tasks
```

**Agent Workflow**:
1. Baron receives dispatch prompt with feature context
2. Uses Read tool to load relevant template
3. Uses Read tool to load constitution and any referenced specs
4. Intelligently fills template sections (Claude's native capability)
5. Uses Write tool to save completed artifact

**Key Insight**: Template loading is NOT Python code. It's agent behavior defined in Baron's system prompt. The agent knows which template to use for each workflow and how to fill it.

### 4. Workflow State Persistence

**Decision**: Baron uses Write tool to persist JSON state in specs/{NNN-feature}/.baron-state.json

**Rationale**:
- Baron may be interrupted (timeout, escalation delay)
- State file enables resumption from checkpoint
- JSON is human-readable for debugging
- Agent uses Read/Write tools directly - no Python code needed

**State Structure**:
```json
{
  "workflow_id": "uuid",
  "feature_id": "006-baron-pm-agent",
  "current_phase": "plan",
  "current_step": "research",
  "completed_steps": ["specify"],
  "blocked_sections": [],
  "pending_escalations": ["esc-123"],
  "expert_consultations": [
    {
      "topic": "architecture",
      "question": "...",
      "answer": "...",
      "session_id": "sess-456"
    }
  ],
  "created_at": "2026-01-05T10:00:00Z",
  "updated_at": "2026-01-05T10:05:00Z"
}
```

**Agent Checkpoint Behavior** (defined in system prompt):
- After each major step, Baron uses Write tool to update state file
- On dispatch, Baron first checks for existing state file with Read tool
- If state exists: Resume from checkpoint
- If not: Start fresh workflow
- State file deleted on successful completion

**Key Insight**: State management is agent behavior, not Python code. Baron's system prompt instructs it when and how to checkpoint.

### 5. Bash Script Execution

**Decision**: Use subprocess via Bash tool for speckit scripts

**Rationale**:
- Scripts in `.specify/scripts/bash/` need execution
- Baron has access to Bash tool as Claude agent
- Scripts handle branch creation, directory setup, etc.
- Reuse existing scripts rather than reimplementing

**Scripts Baron Executes**:
```bash
.specify/scripts/bash/create-new-feature.sh --json "{description}" --number N --short-name "name"
.specify/scripts/bash/setup-plan.sh --json
.specify/scripts/bash/update-agent-context.sh claude
```

**Error Handling**:
- Parse JSON output from scripts
- Check exit codes for success/failure
- Log script output for debugging
- Retry transient failures (up to 3 times)

### 6. Error Handling and Recovery

**Decision**: Graceful degradation with checkpoint-based recovery

**Rationale**:
- Long-running workflows may fail mid-execution
- Human escalations may take hours to resolve
- Checkpoint enables resumption without data loss
- Constitution requires robust error handling

**Error Categories**:
1. **Transient errors** (retry 3x with 1s delay):
   - Network timeouts
   - Agent Hub unavailable
   - Script execution failures

2. **Recoverable errors** (save state, pause):
   - Human escalation pending
   - Expert answer low confidence
   - Rate limit exceeded

3. **Fatal errors** (fail workflow):
   - Invalid feature spec
   - Missing templates
   - Constitution not found

**Recovery Flow**:
```
Workflow starts → Read state file
  → If exists: Resume from checkpoint
  → If not: Start fresh

On error:
  → Save current state
  → Log error details
  → Return partial result with blocked_sections
```

### 7. Constitution Compliance

**Decision**: Read constitution at workflow start, reference throughout

**Rationale**:
- Constitution is mandatory (spec FR-006)
- Baron must verify compliance during planning
- Constitution check section required in plan.md
- TDD enforcement for task generation

**Implementation**:
- Baron reads `.specify/memory/constitution.md` first
- Extracts principles and requirements
- References during artifact generation
- Fills Constitution Check section with compliance verification

**Key Principles Baron Enforces**:
- Principle I: TDD - tasks ordered with tests before implementation
- Principle VI: YAGNI - no premature complexity in plans
- Principle XI: User journeys mapped in plan.md
- Principle XII: CI integration considered

### 8. Artifact Generation Order

**Decision**: Sequential workflow with dependency tracking (defined in agent prompts)

**Rationale**:
- spec.md → plan.md → tasks.md (strict order)
- Within plan.md: research.md → data-model.md → contracts/ → quickstart.md
- Each artifact depends on previous ones
- Order is defined in Baron's workflow prompts, not Python code

**Agent Workflow Order** (defined in dispatch prompts):

**dispatch_specify(feature_description)**:
```
Baron receives: "Execute specify workflow for: {feature_description}"
Baron actions:
  1. Read feature description from prompt
  2. Read .specify/templates/spec-template.md
  3. Read .specify/memory/constitution.md
  4. Consult experts via ask_expert MCP tool (max 3 questions)
  5. Write spec.md following template structure
  6. Create quality checklist
  7. Output structured result for parsing
```

**dispatch_plan(spec_path)**:
```
Baron receives: "Execute plan workflow for spec at: {spec_path}"
Baron actions:
  1. Read spec.md and constitution
  2. Phase 0: Generate research.md (resolve unknowns)
  3. Phase 1: Generate data-model.md
  4. Phase 1: Generate contracts/
  5. Phase 1: Generate quickstart.md
  6. Fill plan.md with technical context
  7. Output structured result for parsing
```

**dispatch_tasks(plan_path)**:
```
Baron receives: "Execute tasks workflow for plan at: {plan_path}"
Baron actions:
  1. Read spec.md, plan.md, data-model.md, contracts/
  2. Generate ordered task list (TDD enforced per constitution)
  3. Write tasks.md
  4. Output structured result for parsing
```

**Key Insight**: These workflows are NOT Python methods. They're prompt instructions that tell Baron what to do. The only Python is the dispatcher that builds the prompt and parses the result.

## NEEDS CLARIFICATION Resolutions

All technical questions resolved through research. No remaining clarifications needed.

## Summary

| Topic | Decision | Confidence |
|-------|----------|------------|
| Execution model | Claude Agent SDK via ClaudeCLIRunner (agent, NOT Python library) | High |
| Agent Hub integration | MCP tools (ask_expert, check_escalation) | High |
| Template loading | Agent uses Read tool directly (no Python code) | High |
| State persistence | Agent uses Write tool for JSON state (no Python code) | High |
| Script execution | Agent uses Bash tool directly | High |
| Error handling | Agent behavior for checkpoint-based recovery | High |
| Constitution compliance | Agent reads and enforces throughout | High |
| Artifact order | Sequential workflows defined in dispatch prompts | High |
| Python code scope | MINIMAL: Only BaronDispatcher in orchestrator module | High |

