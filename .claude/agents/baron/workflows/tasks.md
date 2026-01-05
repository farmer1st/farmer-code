# Tasks Workflow Instructions

Execute this workflow to generate an actionable task list from an implementation plan.

## Prerequisites

- plan.md file exists at the specified path
- spec.md exists in the same feature directory
- data-model.md exists (created during plan workflow)
- contracts/ directory exists with API schemas
- `.specify/templates/tasks-template.md` exists
- `.specify/memory/constitution.md` exists

## Workflow Steps

### Step 1: Read Plan and Supporting Documents

Read all required documents:

1. Parse the `plan_path` from the dispatch prompt
2. Read plan.md completely
3. Read spec.md from the same directory
4. Read data-model.md if it exists
5. Read API contracts from contracts/ directory
6. Read constitution for TDD requirements

### Step 2: Load Tasks Template

Read `.specify/templates/tasks-template.md`:

1. Understand required sections
2. Note format requirements:
   - Task ID format: `T001`, `T002`, etc.
   - Priority markers: `[P]` for parallel execution
   - User story markers: `[US1]`, `[US2]`, etc.
   - Checkbox format: `- [ ]` for pending, `- [X]` for complete

### Step 3: Extract User Stories

From spec.md, identify all user stories:

1. List each user story with its ID
2. Map to journey IDs from plan.md
3. Group related functionality

### Step 4: Apply Constitution Principles

Enforce TDD ordering per Constitution Principle I:

1. **Test tasks MUST come before implementation tasks**
2. Within each user story:
   - First: Unit test tasks
   - Second: Implementation tasks
   - Third: Integration test tasks
   - Fourth: Documentation tasks

### Step 5: Generate Task List

For each user story, generate tasks:

1. **Setup tasks** (if needed):
   - Create directories
   - Initialize configuration files

2. **Test tasks** (FIRST per TDD):
   - Unit tests for models/validation
   - Unit tests for business logic
   - Mark with `[P]` if independent

3. **Implementation tasks**:
   - Core functionality
   - Error handling
   - Mark dependencies clearly

4. **Integration test tasks**:
   - End-to-end tests
   - Journey marker: `@pytest.mark.journey("XXX-NNN")`

5. **Documentation tasks**:
   - User journey docs (REQUIRED per Principle XI)
   - README updates

### Step 6: Add Parallel Execution Markers

Mark tasks that can run in parallel:

- Tasks that modify different files
- Tasks with no dependencies on each other
- Use `[P]` marker: `- [ ] T005 [P] [US1] Create model for User entity`

### Step 7: Include Dependency Information

For each task, note dependencies:

```markdown
- [ ] T010 [US1] Implement login endpoint
  - Depends on: T008 (User model), T009 (Auth service)
```

### Step 8: Add Phase Boundaries

Group tasks into phases:

```markdown
## Phase 1: Setup

## Phase 2: Foundational (Core Models)

## Phase 3: User Story 1 (Priority: P1) MVP

## Phase 4: User Story 2 (Priority: P1) MVP
```

### Step 9: Include Checkpoints

Add checkpoint markers at phase boundaries:

```markdown
**Checkpoint**: Phase complete when all tests pass and models validated
```

### Step 10: Count Tasks and Tests

Calculate totals:

- Total task count
- Test task count (for TDD verification)
- Tasks per user story

### Step 11: Output Result

Output the structured result between markers:

```json
<!-- BARON_RESULT_START -->
{
  "success": true,
  "tasks_path": "specs/NNN-feature/tasks.md",
  "task_count": 45,
  "test_count": 20,
  "duration_seconds": 60.0
}
<!-- BARON_RESULT_END -->
```

## TDD Ordering Example

For a user story "Add user authentication":

```markdown
### Tests for User Story 1

- [ ] T008 [P] [US1] Unit test for UserModel validation
- [ ] T009 [P] [US1] Unit test for AuthService.login()
- [ ] T010 [P] [US1] Unit test for password hashing

### Implementation for User Story 1

- [ ] T011 [US1] Create UserModel in models/user.py
- [ ] T012 [US1] Implement AuthService.login() in services/auth.py
- [ ] T013 [US1] Add password hashing utility

### Integration Test for User Story 1

- [ ] T014 [US1] Integration test for login flow
  - Mark with @pytest.mark.journey("AUTH-001")

### Documentation for User Story 1

- [ ] T015 [US1] Create user journey doc
```

## Error Handling

If an error occurs:

```json
<!-- BARON_RESULT_START -->
{
  "success": false,
  "error": "Plan file not found: specs/NNN-feature/plan.md",
  "duration_seconds": 2.0
}
<!-- BARON_RESULT_END -->
```

## Validation Checklist

Before outputting result, verify:

- [ ] Every user story has tasks
- [ ] Test tasks appear before implementation tasks
- [ ] Parallel markers `[P]` on independent tasks
- [ ] User story markers `[USn]` on all tasks
- [ ] Integration tests have journey markers
- [ ] Documentation tasks include user journey docs
- [ ] Phase boundaries clearly marked
- [ ] Checkpoints after each phase
