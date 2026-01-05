# Tasks Workflow Example

## Example Dispatch Prompt

```
Execute the TASKS workflow for this plan:

## Plan Path

specs/008-user-authentication/plan.md

## Instructions

Follow the tasks workflow in `.claude/agents/baron/workflows/tasks.md`:

1. Read plan.md, spec.md, data-model.md, contracts/
2. Read tasks-template.md from .specify/templates/
3. Read constitution for TDD requirements
4. Generate ordered task list (test tasks before implementation)
5. Write tasks.md to the feature directory

## Output Format

Output your result in this format:

<!-- BARON_RESULT_START -->
{
  "success": true,
  "tasks_path": "specs/NNN-feature/tasks.md",
  "task_count": 25,
  "test_count": 12,
  "duration_seconds": 60.0
}
<!-- BARON_RESULT_END -->
```

## Example Successful Output

```
Baron executing tasks workflow...

Reading plan.md from specs/008-user-authentication/plan.md...
Plan loaded successfully.

Reading spec.md...
Found 3 user stories:
- US1: User Login
- US2: User Registration
- US3: Password Reset

Reading data-model.md...
Found entities: User, Session, Token

Reading contracts/...
Found API endpoints: POST /login, POST /register, POST /reset-password

Loading constitution.md...
Key principle: TDD - tests before implementation

Generating task list...
- Phase 1: Setup (3 tasks)
- Phase 2: Foundational (6 tasks)
- Phase 3: US1 Login (8 tasks, 4 tests)
- Phase 4: US2 Registration (9 tasks, 4 tests)
- Phase 5: US3 Password Reset (7 tasks, 3 tests)
- Phase 6: Polish (4 tasks)

Writing tasks.md...
Task list generated successfully.

<!-- BARON_RESULT_START -->
{
    "success": true,
    "tasks_path": "specs/008-user-authentication/tasks.md",
    "task_count": 37,
    "test_count": 11,
    "duration_seconds": 52.3
}
<!-- BARON_RESULT_END -->
```

## Example Generated tasks.md (Excerpt)

```markdown
# Tasks: User Authentication

**Input**: Design documents from `/specs/008-user-authentication/`
**Prerequisites**: plan.md (required), spec.md (required)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel
- **[Story]**: User story (US1, US2, US3)

## Journey ID Convention

**Journey Domain**: AUTH

| User Story | Journey ID | Journey Name |
|------------|------------|--------------|
| US1: User Login | AUTH-001 | User Login Flow |
| US2: User Registration | AUTH-002 | User Registration |
| US3: Password Reset | AUTH-003 | Password Reset Flow |

---

## Phase 1: Setup

- [X] T001 Create directory structure for auth module
- [X] T002 [P] Create __init__.py files

---

## Phase 2: Foundational (Core Models)

### Tests for User Model

- [ ] T003 [P] Unit test for User model validation
- [ ] T004 [P] Unit test for password hashing

### Implementation for Models

- [ ] T005 Create User model in models/user.py
- [ ] T006 Implement password hashing utility

---

## Phase 3: User Story 1 - User Login (Priority: P1) MVP

**Journey ID**: AUTH-001

### Tests for User Story 1

- [ ] T007 [P] [US1] Unit test for login request validation
- [ ] T008 [P] [US1] Unit test for AuthService.login()
- [ ] T009 [P] [US1] Unit test for token generation

### Implementation for User Story 1

- [ ] T010 [US1] Create LoginRequest model
- [ ] T011 [US1] Implement AuthService.login()
- [ ] T012 [US1] Create login endpoint POST /login

### Integration Test for User Story 1

- [ ] T013 [US1] Integration test for login flow
  - Mark with `@pytest.mark.journey("AUTH-001")`

### Documentation for User Story 1

- [ ] T014 [US1] Create user journey doc in docs/user-journeys/AUTH-001-login.md

**Checkpoint**: US1 complete when users can log in successfully

---

## Dependencies & Execution Order

- Phase 1: No dependencies
- Phase 2: Depends on Phase 1
- Phase 3+: All depend on Phase 2
```

## Example Failure

```
Baron executing tasks workflow...

Reading plan.md from specs/999-missing/plan.md...
ERROR: Plan file not found

<!-- BARON_RESULT_START -->
{
    "success": false,
    "error": "Plan file not found: specs/999-missing/plan.md",
    "duration_seconds": 1.5
}
<!-- BARON_RESULT_END -->
```

## TDD Verification

The `test_count` in the result should be verified:

- `test_count` represents tasks that create tests
- Should be approximately 30-50% of `task_count`
- Zero test count is a TDD violation

Example verification:
```python
assert result.test_count > 0, "TDD requires test tasks"
assert result.test_count <= result.task_count
```
