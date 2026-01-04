# Research: Knowledge Router

**Feature**: 004-knowledge-router
**Date**: 2026-01-03
**Status**: Complete

## Research Areas

### 1. Claude CLI Spawning Patterns

**Finding**: Already implemented in `src/orchestrator/agent_runner.py`

**Decision**: Extend existing `ClaudeCLIRunner` for knowledge router use cases.

**Existing Implementation**:
```python
class ClaudeCLIRunner:
    def dispatch(self, config: AgentConfig, context: dict) -> AgentResult:
        cmd = [self._claude_path, "--model", config.model, "--print"]
        if config.prompt:
            cmd.extend(["-p", config.prompt])
        # ... skills, plugins, mcp
        result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
        return AgentResult(success=result.returncode == 0, stdout=result.stdout, ...)
```

**Extension Needed for Knowledge Router**:
- Add `--output-format json` flag for structured answers
- Parse JSON response for `confidence`, `answer`, `rationale` fields
- Add agent role context in prompt (e.g., "You are @duc, the architect...")

**Rationale**: Reusing existing code reduces duplication and leverages tested patterns.

**Alternatives Considered**:
- SDK-based agent invocation → rejected (CLI is simpler for local-first)
- Async subprocess → rejected (YAGNI, sync is sufficient for single user)

---

### 2. Confidence Score Implementation

**Finding**: Agents must self-report confidence in their answers.

**Decision**: Include confidence instruction in agent prompt, parse from JSON response.

**Prompt Template**:
```
You are @duc, the Architecture Agent.

Answer the following question. Your response MUST be valid JSON with this structure:
{
  "answer": "your answer here",
  "rationale": "why you believe this is correct",
  "confidence": 85,  // 0-100 percentage
  "uncertainty_reasons": ["reason 1", "reason 2"]  // if confidence < 100
}

Base your confidence on:
- 90-100: You have specific knowledge/documentation about this
- 70-89: You're making an informed inference based on patterns
- 50-69: You have general knowledge but significant uncertainty
- 0-49: You're guessing, recommend human input

Question: {question}
Context: {context}
```

**Validation**:
- Parse response as JSON
- Validate `confidence` is int 0-100
- If parsing fails, treat as 0% confidence (escalate to human)

**Rationale**: Self-reported confidence aligns with how LLMs work. They can assess their own uncertainty.

**Alternatives Considered**:
- External confidence scoring model → rejected (adds complexity, latency)
- Binary confident/not-confident → rejected (threshold needs gradation)
- No confidence, always ask human → rejected (defeats automation purpose)

---

### 3. GitHub Comment Format for Escalations

**Finding**: Use existing GitHub Integration (Feature 001) for posting comments.

**Decision**: Structured markdown format for human escalations.

**Escalation Comment Template**:
```markdown
## 🔸 Agent Needs Validation

**Question**: {question}
**Agent**: @{agent_role} ({agent_name})
**Confidence**: {confidence}%

### Tentative Answer
{answer}

### Rationale
{rationale}

### Uncertainty
{uncertainty_reasons as bullet list}

---

**Please respond with one of:**
- ✅ **Confirm**: "confirmed" - Accept this answer
- ✏️ **Correct**: "correct: [your answer]" - Provide different answer
- 💬 **Context**: "context: [additional info]" - Add context for re-evaluation
```

**Detection Patterns** (for polling):
- Confirmation: `/confirmed/i`
- Correction: `/^correct:\s*(.+)$/im`
- Context: `/^context:\s*(.+)$/im`

**Rationale**: Leverage existing comment polling from orchestrator. Structured format makes parsing reliable.

**Alternatives Considered**:
- Custom UI for escalations → rejected (YAGNI, GitHub comments work)
- Slack integration → rejected (adds external dependency)
- Email notifications → rejected (not real-time enough)

---

### 4. Routing Configuration Schema

**Finding**: Need flexible topic-to-agent mapping with confidence overrides.

**Decision**: YAML configuration file with layered rules.

**Schema** (`config/routing.yaml`):
```yaml
# Knowledge Router Configuration

defaults:
  confidence_threshold: 80
  timeout_seconds: 120
  model: sonnet

agents:
  architect:
    name: "@duc"
    topics:
      - authentication
      - authorization
      - api_design
      - database
      - caching
      - architecture
      - security_patterns
      - infrastructure
    model: opus  # Override for complex decisions

  product:
    name: "@veuve"
    topics:
      - scope
      - priority
      - user_experience
      - business_logic
      - features
    model: sonnet

overrides:
  # Topic-specific rules that override agent defaults
  security:
    confidence_threshold: 95  # Higher bar for security
    agent: architect

  compliance:
    confidence_threshold: 95
    agent: human  # Always escalate compliance questions

  budget:
    agent: human  # Always ask humans about budget

  timeline:
    agent: human  # Always ask humans about timeline

execution_agents:
  qa:
    name: "@marie"
    scope: ["tests/"]
    model: sonnet

  dev:
    name: "@dede"
    scope: ["src/"]
    model: sonnet

  devops:
    name: "@gustave"
    scope: ["k8s/", "argocd/", "kustomize/", "helm/", ".github/workflows/"]
    model: sonnet

  reviewer:
    name: "@degaulle"
    scope: []  # Read-only
    model: opus  # Thorough review
```

**Loading Logic**:
```python
def get_agent_for_topic(topic: str, config: RoutingConfig) -> str:
    # 1. Check overrides first
    if topic in config.overrides:
        override = config.overrides[topic]
        if override.agent == "human":
            return "human"
        return override.agent

    # 2. Find agent by topic
    for agent_id, agent in config.agents.items():
        if topic in agent.topics:
            return agent_id

    # 3. Default to human if no match
    return "human"
```

**Rationale**: YAML is human-readable and easy to edit. Layered rules allow flexible configuration.

**Alternatives Considered**:
- JSON config → rejected (less readable, no comments)
- Database for config → rejected (YAGNI, file is sufficient)
- Hardcoded routing → rejected (not configurable)

---

## Summary of Decisions

| Area | Decision | Key Insight |
|------|----------|-------------|
| CLI Spawning | Extend existing `ClaudeCLIRunner` | Reuse tested code |
| Confidence | Self-reported in JSON, 0-100 scale | Agents can assess uncertainty |
| Escalation | GitHub comments with structured markdown | Leverage existing integration |
| Routing | YAML config with layered overrides | Flexible, human-readable |

## Next Steps

1. Generate data-model.md with Pydantic models
2. Generate JSON schemas in contracts/
3. Generate quickstart.md for validation
