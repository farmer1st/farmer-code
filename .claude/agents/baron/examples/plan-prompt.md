# Plan Workflow Example

## Example Dispatch Prompt

```
Execute the PLAN workflow for this specification:

## Specification Path

specs/008-user-authentication/spec.md

## Configuration

- Force Research: false

## Instructions

Follow the plan workflow in `.claude/agents/baron/workflows/plan.md`:

1. Read the spec.md file
2. Read constitution from .specify/memory/constitution.md
3. Run setup-plan.sh to prepare artifacts
4. Phase 0: Generate research.md (resolve unknowns)
5. Phase 1: Generate data-model.md, contracts/, quickstart.md
6. Fill plan.md with technical context
7. Consult experts via Agent Hub for architecture decisions

## Output Format

Output your result in this format:

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

## Example Successful Output

```
Baron executing plan workflow...

Reading spec.md from specs/008-user-authentication/spec.md...
Spec loaded successfully.

Running setup-plan.sh...
Plan directory prepared.

Loading constitution.md...
Key principles:
- TDD: Tests before implementation
- YAGNI: No unnecessary complexity
- User Journey Mapping: Required for each user story

Phase 0: Generating research.md...
- Decision: Use OAuth2 with PKCE flow
- Rationale: Industry standard for SPAs, no client secret exposed
- Alternatives: Session-based auth (rejected: doesn't scale for mobile)

Phase 1: Generating design artifacts...
- Created data-model.md with User, Session, Token entities
- Created contracts/auth-api.yaml with login/logout/refresh endpoints
- Created quickstart.md with local development setup

Filling plan.md...
- Technical context complete
- Constitution check filled
- User journey mapping: AUTH-001, AUTH-002, AUTH-003

Updating agent context...
Agent context updated with OAuth2, JWT technologies.

<!-- BARON_RESULT_START -->
{
    "success": true,
    "plan_path": "specs/008-user-authentication/plan.md",
    "research_path": "specs/008-user-authentication/research.md",
    "data_model_path": "specs/008-user-authentication/data-model.md",
    "contracts_dir": "specs/008-user-authentication/contracts",
    "quickstart_path": "specs/008-user-authentication/quickstart.md",
    "duration_seconds": 145.7
}
<!-- BARON_RESULT_END -->
```

## Example With Force Research

When `Force Research: true`, regenerate research.md even if it exists:

```
Execute the PLAN workflow for this specification:

## Specification Path

specs/008-user-authentication/spec.md

## Configuration

- Force Research: true
```

This is useful when:
- Requirements have changed significantly
- Previous research is outdated
- New team decisions need to be captured

## Example Blocked on Escalation

```
Baron executing plan workflow...

Reading spec.md...
Running setup-plan.sh...

Phase 0: Generating research.md...
- Need architecture decision on data storage approach

Consulting @duc via ask_expert...
Question: "Should we use PostgreSQL or MongoDB for user data?"
Status: PENDING (async response required)

Saving state for resumption...
Continuing with other sections...

Phase 1: Generating data-model.md...
- User entity defined (storage-agnostic)
- Session entity defined

Blocked on architecture decision. Cannot complete contracts until resolved.

<!-- BARON_RESULT_START -->
{
    "success": false,
    "blocked_on_escalation": true,
    "error": "Waiting for @duc to respond on data storage decision",
    "duration_seconds": 62.3
}
<!-- BARON_RESULT_END -->
```

## Example Failure

```
Baron executing plan workflow...

Reading spec.md from specs/008-user-authentication/spec.md...
ERROR: File not found

<!-- BARON_RESULT_START -->
{
    "success": false,
    "error": "Spec file not found: specs/008-user-authentication/spec.md",
    "duration_seconds": 1.2
}
<!-- BARON_RESULT_END -->
```
