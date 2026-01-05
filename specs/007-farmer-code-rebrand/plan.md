# Implementation Plan: Farmer Code Rebrand

**Branch**: `007-farmer-code-rebrand` | **Date**: 2026-01-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-farmer-code-rebrand/spec.md`

## Summary

Rebrand the application from "farmcode/farm code" to "Farmer Code" across all documentation, configuration files, and code comments. This is a text-only change with no functional code modifications. The goal is consistent brand presentation with "Farmer Code" (capitalized, two words) for display text while maintaining technical identifiers in appropriate formats.

## Technical Context

**Language/Version**: N/A (text changes only)
**Primary Dependencies**: grep/sed for search and replace
**Storage**: N/A
**Testing**: Verification via grep to confirm no remaining instances
**Target Platform**: N/A
**Project Type**: Existing monorepo - documentation update
**Performance Goals**: N/A
**Constraints**: Must not break imports, paths, or technical identifiers
**Scale/Scope**: ~50 files to review, ~20 files requiring changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | N/A | No code changes - verification via grep |
| II. Specification-Driven Development | PASS | Spec created before implementation |
| III. Independent User Stories | PASS | Each story independently testable |
| IV. Human Approval Gates | PASS | Standard PR review |
| V. Parallel-First Execution | PASS | All file edits can run in parallel |
| VI. Simplicity and YAGNI | PASS | Minimal change - text only |
| VII. Versioning | PASS | Will use conventional commit |
| VIII. Technology Stack | N/A | No new tech |
| IX. Thin Client | N/A | No client changes |
| X. Security-First | N/A | No security implications |
| XI. Documentation | PASS | This IS documentation update |
| XII. CI/CD | PASS | Will run lint/tests |

**Gate Status**: PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/007-farmer-code-rebrand/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output (minimal - no unknowns)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

No new source code. Files to be modified:

```text
# Configuration
pyproject.toml           # Update project name/description

# Root Documentation
CLAUDE.md                # Update project name references

# Module Documentation
.claude/CLAUDE.md        # Update project name references
src/agent_hub/README.md  # Update any brand references
src/github_integration/README.md  # Update if present
src/worktree_manager/README.md    # Update if present
src/orchestrator/README.md        # Update if present

# Docs folder
docs/README.md           # Update project name
docs/**/*.md             # Scan all markdown files

# Constitution (special case)
.specify/memory/constitution.md  # "Farm Code" → "Farmer Code"
```

**Structure Decision**: No new structure - editing existing files only.

## User Journey Mapping (REQUIRED per Constitution Principle XI)

**Journey Domain**: FC (Farmer Code - rebrand)

This feature is a maintenance/housekeeping task rather than user-facing functionality. However, we map the user stories for consistency:

| User Story | Journey ID | Journey Name | Priority |
|------------|------------|--------------|----------|
| US1: Consistent Brand in Documentation | FC-001 | Documentation Brand Consistency | P1 |
| US2: Correct Project Metadata | FC-002 | Project Metadata Branding | P1 |
| US3: Developer Context Files | FC-003 | AI Context File Branding | P2 |

**Journey Files to Create**: None - this is a maintenance feature, not a user-facing workflow.

**E2E Test Markers**: None - verification via grep commands, not E2E tests.

## Complexity Tracking

No complexity violations. This is a minimal text-change feature.

## Implementation Approach

### Phase 1: Audit

1. Search for all instances of "farmcode" (case-insensitive, whole word)
2. Search for all instances of "farm code" (two words)
3. Categorize each as:
   - **Display text** → Change to "Farmer Code"
   - **Technical identifier** → Leave as-is or use `farmer-code`/`farmer_code`
   - **Path/import** → Leave as-is

### Phase 2: Update

1. Update pyproject.toml project metadata
2. Update CLAUDE.md files
3. Update README files
4. Update constitution (Farm Code → Farmer Code)
5. Update any remaining documentation

### Phase 3: Verify

1. Grep for "farmcode" in prose (should be zero)
2. Grep for "farm code" (should be zero)
3. Verify all READMEs have "Farmer Code"
4. Run lint and tests to ensure nothing broken
