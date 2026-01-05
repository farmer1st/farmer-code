# Specify Workflow

## Objective

Create a feature specification (spec.md) from a natural language description.

## Input

You receive a dispatch prompt with:
- `feature_description`: Natural language description of the feature
- `feature_number`: (optional) Explicit feature number
- `short_name`: (optional) Short name for branch

## Steps

### 1. Check for Existing State

```bash
# Check if resuming from previous run
Read specs/{feature_id}/.baron-state.json
```

If state exists with `current_phase: "specify"`:
- Resume from last checkpoint
- Skip completed steps

### 2. Generate Feature Identifiers

If `feature_number` and `short_name` not provided:
- Analyze the feature description
- Generate a 2-4 word short name (e.g., "oauth2-auth", "health-check")
- Determine next available feature number

### 3. Run Setup Script

```bash
.specify/scripts/bash/create-new-feature.sh --json "{description}" --number {N} --short-name "{name}"
```

Parse JSON output for:
- `BRANCH_NAME`: Git branch created
- `SPEC_FILE`: Path to spec.md
- `FEATURE_DIR`: Feature directory path

### 4. Load Template and Constitution

```bash
Read .specify/templates/spec-template.md
Read .specify/memory/constitution.md
```

Understand:
- Required sections in spec template
- Constitution principles to follow

### 5. Analyze Feature

From the feature description, extract:
- **Actors**: Who uses this feature?
- **Actions**: What can they do?
- **Data**: What information is involved?
- **Constraints**: What limitations exist?

### 6. Consult Experts (If Needed)

If any aspect is unclear (max 3 questions):

```
ask_expert(
  topic="product",  # or "architecture", "testing"
  question="Specific question about the feature",
  context="Relevant context from description"
)
```

Handle responses:
- **High confidence**: Incorporate answer
- **Low confidence / pending_human**: Note for escalation

### 7. Fill Template Sections

Complete all mandatory sections:

- **Overview**: What the feature does and why
- **User Scenarios & Testing**: User stories with acceptance criteria
- **Requirements**: Functional requirements, key entities, service interface
- **Success Criteria**: Measurable outcomes

### 8. Write Specification

```bash
Write {SPEC_FILE}
```

Write the completed specification to the file.

### 9. Create Quality Checklist

```bash
mkdir -p {FEATURE_DIR}/checklists
Write {FEATURE_DIR}/checklists/requirements.md
```

Create checklist with items for:
- Content quality
- Requirement completeness
- Feature readiness

### 10. Save State (If Incomplete)

If blocked on escalation:

```json
{
  "workflow_id": "uuid",
  "feature_id": "{NNN-short-name}",
  "current_phase": "specify",
  "blocked_on": "escalation-id",
  ...
}
```

Write to `{FEATURE_DIR}/.baron-state.json`

### 11. Output Result

```
<!-- BARON_RESULT_START -->
{
  "success": true,
  "spec_path": "{SPEC_FILE}",
  "feature_id": "{NNN-short-name}",
  "branch_name": "{BRANCH_NAME}",
  "duration_seconds": {elapsed_time}
}
<!-- BARON_RESULT_END -->
```

## Error Handling

| Error | Action |
|-------|--------|
| Script fails | Retry once, then report error |
| Template not found | Report error, cannot proceed |
| Constitution not found | Report error, cannot proceed |
| Expert timeout | Proceed with best judgment, note in spec |

## Constitution Compliance

Before completing, verify:
- [ ] No implementation details in spec
- [ ] User stories are independent and testable
- [ ] Success criteria are measurable
- [ ] All mandatory sections completed
