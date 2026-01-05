# Example: Specify Workflow Dispatch Prompt

## Dispatch Prompt Template

```markdown
Execute the SPECIFY workflow for this feature:

## Feature Description

{feature_description}

## Configuration

- Feature Number: {feature_number or "auto"}
- Short Name: {short_name or "auto"}

## Instructions

Follow the specify workflow in `.claude/agents/baron/workflows/specify.md`:

1. Run create-new-feature.sh to set up branch and directory
2. Read spec-template.md from .specify/templates/
3. Read constitution from .specify/memory/constitution.md
4. Analyze the feature description
5. Consult experts via Agent Hub if needed (max 3 questions)
6. Fill all mandatory template sections
7. Write spec.md to the feature directory
8. Create quality checklist in checklists/requirements.md

## Output Format

Output your result in this format:

<!-- BARON_RESULT_START -->
{
  "success": true,
  "spec_path": "specs/NNN-feature/spec.md",
  "feature_id": "NNN-feature",
  "branch_name": "NNN-feature",
  "duration_seconds": 45.2
}
<!-- BARON_RESULT_END -->
```

## Example: Simple Feature

```markdown
Execute the SPECIFY workflow for this feature:

## Feature Description

Add a health check endpoint that returns the service status including database connectivity, memory usage, and uptime.

## Configuration

- Feature Number: auto
- Short Name: auto

## Instructions

Follow the specify workflow...
```

## Example: With Explicit Number

```markdown
Execute the SPECIFY workflow for this feature:

## Feature Description

Implement OAuth2 authentication with Google and GitHub providers, including user registration, login, and token refresh.

## Configuration

- Feature Number: 10
- Short Name: oauth2-auth

## Instructions

Follow the specify workflow...
```

## Expected Success Output

```
Baron executing specify workflow...

Reading templates and constitution...
Analyzing feature: "Add a health check endpoint..."
Generated short name: health-check-endpoint
Running create-new-feature.sh...
Branch created: 009-health-check-endpoint
Writing specification...
Creating quality checklist...
Specification complete.

<!-- BARON_RESULT_START -->
{
  "success": true,
  "spec_path": "specs/009-health-check-endpoint/spec.md",
  "feature_id": "009-health-check-endpoint",
  "branch_name": "009-health-check-endpoint",
  "duration_seconds": 42.5
}
<!-- BARON_RESULT_END -->
```

## Expected Error Output

```
Baron executing specify workflow...

Error: Template not found at .specify/templates/spec-template.md

<!-- BARON_RESULT_START -->
{
  "success": false,
  "error": "Template not found: .specify/templates/spec-template.md",
  "duration_seconds": 1.2
}
<!-- BARON_RESULT_END -->
```
