# Tasks: Git Worktree Manager

**Input**: Design documents from `/specs/002-git-worktree-manager/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/worktree-service.md

**Tests**: TDD enforced per constitution - tests written FIRST, must FAIL before implementation.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- All paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create module structure following github_integration pattern

- [x] T001 Create src/worktree_manager/ directory structure
- [x] T002 [P] Create src/worktree_manager/__init__.py with public exports placeholder
- [x] T003 [P] Create tests/unit/test_worktree_models.py with pytest imports
- [x] T004 [P] Create tests/contract/test_worktree_service.py with pytest imports
- [x] T005 [P] Create tests/integration/test_worktree_integration.py with pytest imports
- [x] T006 [P] Create tests/e2e/test_worktree_e2e.py with pytest imports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure used by ALL user stories - MUST complete before any story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational

- [x] T007 [P] Unit tests for GitClient in tests/unit/test_git_client.py (test run_command, check git availability)
- [x] T008 [P] Unit tests for custom exceptions in tests/unit/test_worktree_errors.py

### Implementation for Foundational

- [x] T009 [P] Create src/worktree_manager/errors.py with exception hierarchy (WorktreeError, GitNotFoundError, GitCommandError, NotARepositoryError, MainBranchNotFoundError, BranchExistsError, BranchNotFoundError, WorktreeExistsError, WorktreeNotFoundError, UncommittedChangesError, PushError)
- [x] T010 [P] Create src/worktree_manager/logger.py following github_integration/logger.py pattern
- [x] T011 Create src/worktree_manager/git_client.py with run_command() wrapper using subprocess.run() (depends on T009)
- [x] T012 Add git availability check to GitClient.__init__() in src/worktree_manager/git_client.py
- [x] T013 Add repository validation to GitClient in src/worktree_manager/git_client.py
- [x] T014 Run foundational tests - verify T007, T008 pass

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - Create Branch and Worktree (Priority: P1) 🎯 MVP

**Goal**: Create feature branches from main and worktrees in sibling directories for isolated development

**Independent Test**: Request worktree for issue #123 → verify branch exists + worktree in sibling directory

### Tests for User Story 1

> **TDD: Write tests FIRST, ensure they FAIL before implementation**

- [x] T015 [P] [US1] Unit tests for Worktree model in tests/unit/test_worktree_models.py (validation, properties)
- [x] T016 [P] [US1] Unit tests for Branch model in tests/unit/test_worktree_models.py (validation, is_tracking, is_synced)
- [x] T017 [P] [US1] Unit tests for CreateWorktreeRequest model in tests/unit/test_worktree_models.py (validation, branch_name property)
- [x] T018 [US1] Contract tests for create_worktree() in tests/contract/test_worktree_service.py (new branch, existing remote, directory exists error)
- [x] T019 [US1] Contract tests for create_worktree_from_existing() in tests/contract/test_worktree_service.py

### Implementation for User Story 1

- [x] T020 [P] [US1] Create Worktree model in src/worktree_manager/models.py (issue_number, feature_name, path, main_repo_path, branch_name, is_clean, created_at, plans_path property)
- [x] T021 [P] [US1] Create Branch model in src/worktree_manager/models.py (name, remote, remote_branch, is_local, is_remote, is_merged, ahead, behind, is_tracking, is_synced properties)
- [x] T022 [P] [US1] Create CreateWorktreeRequest model in src/worktree_manager/models.py (issue_number, feature_name with pattern validation, branch_name property)
- [x] T023 [US1] Create WorktreeService class with __init__(repo_path) in src/worktree_manager/service.py (validate git, validate repo)
- [x] T024 [US1] Implement _get_worktree_path() helper in src/worktree_manager/service.py (sibling directory naming)
- [x] T025 [US1] Implement create_worktree() in src/worktree_manager/service.py (create branch from main, git worktree add)
- [x] T026 [US1] Implement create_worktree_from_existing() in src/worktree_manager/service.py (fetch, checkout existing branch)
- [x] T027 [US1] Add error handling for WorktreeExistsError, MainBranchNotFoundError in src/worktree_manager/service.py
- [x] T028 [US1] Update src/worktree_manager/__init__.py with US1 exports (Worktree, Branch, CreateWorktreeRequest, WorktreeService)
- [x] T029 [US1] Run US1 tests - verify T015-T019 pass

**Checkpoint**: User Story 1 complete - can create worktrees for isolated feature development

---

## Phase 4: User Story 2 - Initialize Plans Structure (Priority: P1)

**Goal**: Create standardized .plans/{issue_number}/ folder structure for SDLC artifacts

**Independent Test**: Initialize plans for issue #123 → verify .plans/123/ with specs/, plans/, reviews/, README.md

### Tests for User Story 2

> **TDD: Write tests FIRST, ensure they FAIL before implementation**

- [x] T030 [P] [US2] Unit tests for PlansFolder model in tests/unit/test_worktree_models.py (validation, path property, is_complete)
- [x] T031 [US2] Contract tests for init_plans() in tests/contract/test_worktree_service.py (create structure, idempotent, README content)
- [x] T032 [US2] Contract tests for get_plans() in tests/contract/test_worktree_service.py (exists, not exists)

### Implementation for User Story 2

- [x] T033 [P] [US2] Create PlansFolder model in src/worktree_manager/models.py (issue_number, worktree_path, has_specs, has_plans, has_reviews, has_readme, path property, is_complete property)
- [x] T034 [US2] Implement init_plans() in src/worktree_manager/service.py (create directories, create README.md with metadata)
- [x] T035 [US2] Implement get_plans() in src/worktree_manager/service.py (check existence, return PlansFolder or None)
- [x] T036 [US2] Add idempotency to init_plans() - return existing if already initialized
- [x] T037 [US2] Update src/worktree_manager/__init__.py with US2 exports (PlansFolder)
- [x] T038 [US2] Run US2 tests - verify T030-T032 pass

**Checkpoint**: User Stories 1 AND 2 complete - can create worktrees with .plans/ structure

---

## Phase 5: User Story 3 - Commit and Push Changes (Priority: P2)

**Goal**: Stage, commit, and push changes in worktrees to persist work to remote

**Independent Test**: Make changes in worktree, commit with message → verify commit exists on remote branch

### Tests for User Story 3

> **TDD: Write tests FIRST, ensure they FAIL before implementation**

- [x] T039 [P] [US3] Unit tests for CommitRequest model in tests/unit/test_worktree_models.py (validation)
- [x] T040 [P] [US3] Unit tests for CommitResult model in tests/unit/test_worktree_models.py (validation)
- [x] T041 [US3] Contract tests for commit_and_push() in tests/contract/test_worktree_service.py (commit+push, nothing to commit, push fails)
- [x] T042 [US3] Contract tests for push() in tests/contract/test_worktree_service.py

### Implementation for User Story 3

- [x] T043 [P] [US3] Create CommitRequest model in src/worktree_manager/models.py (message with validation, push flag)
- [x] T044 [P] [US3] Create CommitResult model in src/worktree_manager/models.py (commit_sha, pushed, nothing_to_commit, push_error)
- [x] T045 [US3] Implement _has_changes() helper in src/worktree_manager/service.py (git status check)
- [x] T046 [US3] Implement commit_and_push() in src/worktree_manager/service.py (git add, git commit, git push)
- [x] T047 [US3] Implement push() in src/worktree_manager/service.py (git push with tracking)
- [x] T048 [US3] Add partial failure handling - commit OK but push failed in src/worktree_manager/service.py
- [x] T049 [US3] Update src/worktree_manager/__init__.py with US3 exports (CommitRequest, CommitResult)
- [x] T050 [US3] Run US3 tests - verify T039-T042 pass

**Checkpoint**: User Stories 1, 2, AND 3 complete - can create worktrees, init plans, commit/push changes

---

## Phase 6: User Story 4 - Remove Worktree and Cleanup (Priority: P2)

**Goal**: Remove worktrees and optionally delete branches to keep local environment clean

**Independent Test**: Remove worktree for issue #123 → verify directory deleted, worktree unregistered, branches optionally removed

### Tests for User Story 4

> **TDD: Write tests FIRST, ensure they FAIL before implementation**

- [x] T051 [P] [US4] Unit tests for OperationStatus enum in tests/unit/test_worktree_models.py
- [x] T052 [P] [US4] Unit tests for OperationResult model in tests/unit/test_worktree_models.py
- [x] T053 [P] [US4] Unit tests for RemoveWorktreeRequest model in tests/unit/test_worktree_models.py
- [x] T054 [US4] Contract tests for remove_worktree() in tests/contract/test_worktree_service.py (remove only, delete local branch, delete remote branch, uncommitted changes error, force)

### Implementation for User Story 4

- [x] T055 [P] [US4] Create OperationStatus enum in src/worktree_manager/models.py (SUCCESS, PARTIAL, FAILED)
- [x] T056 [P] [US4] Create OperationResult model in src/worktree_manager/models.py (status, message, worktree, retry_possible)
- [x] T057 [P] [US4] Create RemoveWorktreeRequest model in src/worktree_manager/models.py (issue_number, delete_branch, delete_remote_branch, force)
- [x] T058 [US4] Implement _check_uncommitted_changes() in src/worktree_manager/service.py
- [x] T059 [US4] Implement remove_worktree() in src/worktree_manager/service.py (git worktree remove, git branch -d)
- [x] T060 [US4] Add delete_remote_branch support in src/worktree_manager/service.py (git push origin --delete)
- [x] T061 [US4] Add force flag handling for dirty worktrees in src/worktree_manager/service.py
- [x] T062 [US4] Add partial failure handling (worktree removed but branch delete failed) in src/worktree_manager/service.py
- [x] T063 [US4] Update src/worktree_manager/__init__.py with US4 exports (OperationStatus, OperationResult, RemoveWorktreeRequest)
- [x] T064 [US4] Run US4 tests - verify T051-T054 pass

**Checkpoint**: All 4 user stories complete - full worktree lifecycle management available

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Query methods, integration tests, E2E tests, final validation

### Query Methods

- [x] T065 [P] Unit tests for list_worktrees() in tests/unit/test_worktree_service.py
- [x] T066 [P] Unit tests for get_worktree() in tests/unit/test_worktree_service.py
- [x] T067 [P] Unit tests for get_branch() in tests/unit/test_worktree_service.py
- [x] T068 Implement list_worktrees() in src/worktree_manager/service.py (git worktree list --porcelain)
- [x] T069 Implement get_worktree() in src/worktree_manager/service.py (lookup by issue_number)
- [x] T070 Implement get_branch() in src/worktree_manager/service.py (git branch -vv)

### Integration Tests

- [x] T071 [P] Integration test for full worktree lifecycle in tests/integration/test_worktree_integration.py (create → init plans → commit → remove)
- [x] T072 [P] Integration test for existing branch checkout in tests/integration/test_worktree_integration.py
- [x] T073 [P] Integration test for error scenarios in tests/integration/test_worktree_integration.py (git not found, not a repo, disk full mock)

### E2E Tests (farmer1st/farmcode-tests)

- [x] T074 E2E test for create_worktree() against farmcode-tests in tests/e2e/test_worktree_e2e.py
- [x] T075 E2E test for init_plans() against farmcode-tests in tests/e2e/test_worktree_e2e.py
- [x] T076 E2E test for commit_and_push() against farmcode-tests in tests/e2e/test_worktree_e2e.py
- [x] T077 E2E test for remove_worktree() against farmcode-tests in tests/e2e/test_worktree_e2e.py

### Final Validation

- [x] T078 Run all unit tests - verify passing
- [x] T079 Run all contract tests - verify passing
- [x] T080 Run all integration tests - verify passing
- [x] T081 Run all E2E tests - verify passing
- [x] T082 Run ruff check src/worktree_manager/ - fix any lint errors
- [x] T083 Run mypy src/worktree_manager/ - fix any type errors
- [x] T084 Validate quickstart.md examples work correctly
- [x] T085 Update src/worktree_manager/__init__.py with final public API exports

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phases 3-6)**: Depend on Foundational completion
  - US1 + US2 (both P1) can run in parallel
  - US3 + US4 (both P2) can run in parallel after P1 complete
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: After Foundational - no dependencies on other stories
- **US2 (P1)**: After Foundational - needs get_worktree() from US1 to find worktree path
- **US3 (P2)**: After Foundational - needs get_worktree() from US1
- **US4 (P2)**: After Foundational - needs get_worktree() from US1

### Within Each User Story

1. Tests written FIRST - must FAIL
2. Models before services
3. Helpers before main methods
4. Run tests - must PASS
5. Story checkpoint before next priority

### Parallel Opportunities

**Phase 1 (all parallel)**:
- T002, T003, T004, T005, T006

**Phase 2 (tests parallel, then implementation)**:
- T007, T008 (parallel)
- T009, T010 (parallel)

**Phase 3 US1 (tests parallel, models parallel)**:
- T015, T016, T017 (parallel)
- T020, T021, T022 (parallel)

**Phase 4 US2**:
- T030 (parallel with T031 prep)

**Phase 5 US3**:
- T039, T040 (parallel)
- T043, T044 (parallel)

**Phase 6 US4**:
- T051, T052, T053 (parallel)
- T055, T056, T057 (parallel)

**Phase 7 Polish**:
- T065, T066, T067 (parallel)
- T071, T072, T073 (parallel)

---

## Parallel Example: User Story 1

```bash
# Launch all model tests in parallel:
Task: "T015 [P] [US1] Unit tests for Worktree model"
Task: "T016 [P] [US1] Unit tests for Branch model"
Task: "T017 [P] [US1] Unit tests for CreateWorktreeRequest model"

# Launch all models in parallel after tests:
Task: "T020 [P] [US1] Create Worktree model"
Task: "T021 [P] [US1] Create Branch model"
Task: "T022 [P] [US1] Create CreateWorktreeRequest model"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (create worktrees)
4. Complete Phase 4: User Story 2 (init .plans/)
5. **STOP and VALIDATE**: Test US1 + US2 independently
6. Deploy/demo if ready - basic worktree management works

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test → Can create worktrees (MVP core)
3. Add US2 → Test → Can create worktrees with .plans/ structure
4. Add US3 → Test → Can commit and push changes
5. Add US4 → Test → Can cleanup worktrees
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together
2. Once Foundational done:
   - Developer A: US1 (create worktree)
   - Developer B: US2 (init plans)
3. After P1 stories done:
   - Developer A: US3 (commit/push)
   - Developer B: US4 (remove/cleanup)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- TDD enforced: tests MUST fail before implementation
- Test repository: farmer1st/farmcode-tests for E2E
- Follow github_integration patterns for consistency
- All paths use pathlib.Path for cross-platform support
- Commit after each task or logical group
