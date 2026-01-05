# Tasks: Farmer Code Rebrand

**Input**: Design documents from `/specs/007-farmer-code-rebrand/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: No automated tests - verification via grep commands.

**Organization**: Tasks grouped by user story for independent verification.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Journey ID Convention

This is a maintenance feature - no user journey files will be created.

---

## Phase 1: Audit

**Purpose**: Identify all files requiring brand updates

- [ ] T001 Search for "farmcode" instances in all markdown files
- [ ] T002 [P] Search for "farm code" (two words) instances in all files
- [ ] T003 [P] Search for "Farm Code" instances in constitution and docs

**Checkpoint**: Audit complete - all files to update identified

---

## Phase 2: User Story 1 - Consistent Brand in Documentation (Priority: P1)

**Goal**: Update all README and documentation files to use "Farmer Code"

**Independent Test**: Grep for "farmcode" in prose - should find zero instances

### Implementation for User Story 1

- [ ] T004 [P] [US1] Update docs/README.md to use "Farmer Code"
- [ ] T005 [P] [US1] Update docs/architecture/agent-hub.md brand references
- [ ] T006 [P] [US1] Update docs/modules/agent-hub.md brand references
- [ ] T007 [P] [US1] Update src/agent_hub/README.md brand references
- [ ] T008 [P] [US1] Update src/orchestrator/README.md if "farmcode" present
- [ ] T009 [P] [US1] Update src/github_integration/README.md if "farmcode" present
- [ ] T010 [P] [US1] Update src/worktree_manager/README.md if "farmcode" present
- [ ] T011 [US1] Scan all docs/**/*.md and update any remaining "farmcode" references

**Checkpoint**: All documentation displays "Farmer Code" consistently

---

## Phase 3: User Story 2 - Correct Project Metadata (Priority: P1)

**Goal**: Update pyproject.toml to use "Farmer Code" in display name

**Independent Test**: Check pyproject.toml contains "Farmer Code" in description

### Implementation for User Story 2

- [ ] T012 [US2] Update pyproject.toml description to use "Farmer Code"

**Checkpoint**: Project metadata shows correct brand name

---

## Phase 4: User Story 3 - Developer Context Files (Priority: P2)

**Goal**: Update CLAUDE.md and constitution to use "Farmer Code"

**Independent Test**: Read CLAUDE.md - verify "Farmer Code" is used

### Implementation for User Story 3

- [ ] T013 [P] [US3] Update CLAUDE.md project name to "Farmer Code"
- [ ] T014 [P] [US3] Update .claude/CLAUDE.md project references to "Farmer Code"
- [ ] T015 [US3] Update .specify/memory/constitution.md from "Farm Code" to "Farmer Code"

**Checkpoint**: All developer context files use "Farmer Code"

---

## Phase 5: Verification & Polish

**Purpose**: Verify no remaining instances and run quality checks

### Verification

- [ ] T016 Verify grep "farmcode" in *.md returns zero prose instances
- [ ] T017 Verify grep "farm code" (lowercase) returns zero instances
- [ ] T018 Run linting (uv run ruff check) to ensure no issues
- [ ] T019 Run tests (uv run pytest) to ensure nothing broken

**Checkpoint**: All success criteria verified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Audit)**: No dependencies - start immediately
- **Phase 2-4 (User Stories)**: Can run in parallel after audit
- **Phase 5 (Verification)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (Documentation)**: No dependencies
- **US2 (Metadata)**: No dependencies
- **US3 (Context Files)**: No dependencies

All user stories can be executed in parallel.

### Parallel Opportunities

All tasks within each user story marked [P] can run in parallel:

```bash
# Phase 2 - All docs can be updated in parallel:
T004, T005, T006, T007, T008, T009, T010

# Phase 4 - Context files in parallel:
T013, T014
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Audit
2. Complete Phase 2: US1 (Documentation) - most visible
3. Complete Phase 3: US2 (Metadata)
4. Complete Phase 4: US3 (Context Files)
5. Complete Phase 5: Verification

### Recommended Approach

Since this is a simple find-replace task:

1. Run audit commands to find all instances
2. Update all files in a single pass
3. Verify via grep
4. Commit and push

---

## Metrics

- **Total Tasks**: 19
- **Phase 1 (Audit)**: 3 tasks
- **Phase 2 (US1 - Docs)**: 8 tasks
- **Phase 3 (US2 - Metadata)**: 1 task
- **Phase 4 (US3 - Context)**: 3 tasks
- **Phase 5 (Verification)**: 4 tasks
- **Parallel Opportunities**: 12 tasks marked [P]

---

## Notes

- [P] tasks = different files, can edit in parallel
- No tests required - verification via grep commands
- Preserve technical identifiers (paths, imports) - only update prose
- Constitution special case: "Farm Code" → "Farmer Code" (already capitalized differently)
