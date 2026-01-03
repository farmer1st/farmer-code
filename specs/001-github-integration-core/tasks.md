# Tasks: GitHub Integration Core

**Input**: Design documents from `/specs/001-github-integration-core/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: This feature implements Test-First Development (Constitution Principle I). All tests MUST be written and fail BEFORE implementation code.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/github_integration/`, `tests/` at repository root
- Package structure: `src/github_integration/` as Python package
- Tests organized by type: `tests/contract/`, `tests/integration/`, `tests/unit/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create Python package structure at src/github_integration/
- [X] T002 Initialize pyproject.toml with dependencies (PyJWT, requests, Pydantic, python-dotenv)
- [X] T003 [P] Configure ruff for linting in pyproject.toml
- [X] T004 [P] Configure mypy for type checking in pyproject.toml
- [X] T005 [P] Create .env.example template file at root
- [X] T006 [P] Add .env to .gitignore
- [X] T007 Create tests/ directory structure (contract/, integration/, unit/)
- [X] T008 Create pytest configuration in pyproject.toml
- [X] T009 [P] Create tests/conftest.py with shared fixtures

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 Implement custom exception hierarchy in src/github_integration/errors.py
- [X] T011 [P] Implement structured JSON logger in src/github_integration/logger.py
- [X] T012 [P] Create Pydantic models (Issue, Comment, Label, PullRequest) in src/github_integration/models.py
- [X] T013 Implement GitHub App JWT authentication in src/github_integration/auth.py
- [X] T014 Implement installation token caching with expiration tracking in src/github_integration/auth.py
- [X] T015 Implement GitHub API client wrapper with retry logic in src/github_integration/client.py
- [X] T016 Implement rate limit detection and handling in src/github_integration/client.py
- [X] T017 Create __init__.py exports for public API in src/github_integration/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create and Track Workflow Issues (Priority: P1) 🎯 MVP

**Goal**: Enable orchestrator to create GitHub issues and retrieve issue details to track SDLC workflow

**Independent Test**: Create issue with title/body/labels, retrieve by number, list open issues, verify all data correct on GitHub

### Tests for User Story 1 (Test-First Development)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T018 [P] [US1] Contract test for create_issue with valid input in tests/contract/test_service_interface.py
- [X] T019 [P] [US1] Contract test for create_issue with missing required fields in tests/contract/test_service_interface.py
- [X] T020 [P] [US1] Contract test for get_issue with valid number in tests/contract/test_service_interface.py
- [X] T021 [P] [US1] Contract test for get_issue with invalid number (ResourceNotFoundError) in tests/contract/test_service_interface.py
- [X] T022 [P] [US1] Contract test for list_issues with state filtering in tests/contract/test_service_interface.py
- [X] T023 [P] [US1] Contract test for list_issues with label filtering in tests/contract/test_service_interface.py
- [X] T024 [P] [US1] Integration test for full issue lifecycle (create → retrieve → list) in tests/e2e/test_github_operations.py
- [X] T025 [P] [US1] Pydantic model validation test for Issue model in tests/contract/test_models.py

### Implementation for User Story 1

- [X] T026 [US1] Implement GitHubService.__init__ with auth setup in src/github_integration/service.py
- [X] T027 [US1] Implement create_issue method in src/github_integration/service.py
- [X] T028 [US1] Implement get_issue method in src/github_integration/service.py
- [X] T029 [US1] Implement list_issues method in src/github_integration/service.py
- [X] T030 [US1] Add input validation for create_issue in src/github_integration/service.py
- [X] T031 [US1] Add structured logging for issue operations in src/github_integration/service.py
- [X] T032 [US1] Verify all US1 tests pass and quickstart.md Test 1 works

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. You can create, retrieve, and list issues.

---

## Phase 4: User Story 2 - Facilitate Agent Communication (Priority: P2)

**Goal**: Enable orchestrator to post comments and read all comments to detect agent signals (✅, ❓, 📝)

**Independent Test**: Post comment with emoji/mentions, retrieve all comments, poll for new comments since timestamp, verify all preserved on GitHub

### Tests for User Story 2 (Test-First Development)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T033 [P] [US2] Contract test for create_comment with valid input in tests/contract/test_service_interface.py
- [X] T034 [P] [US2] Contract test for create_comment with empty body (ValidationError) in tests/contract/test_service_interface.py
- [X] T035 [P] [US2] Contract test for create_comment with emoji preservation in tests/contract/test_service_interface.py
- [X] T036 [P] [US2] Contract test for get_comments with chronological order in tests/contract/test_service_interface.py
- [X] T037 [P] [US2] Contract test for get_comments_since with timestamp filtering in tests/contract/test_service_interface.py
- [X] T038 [P] [US2] Integration test for comment polling workflow (covered by get_comments_since contract tests)
- [X] T039 [P] [US2] Pydantic model validation test for Comment model in tests/contract/test_models.py

### Implementation for User Story 2

- [X] T040 [US2] Implement create_comment method in src/github_integration/service.py
- [X] T041 [US2] Implement get_comments method in src/github_integration/service.py
- [X] T042 [US2] Implement get_comments_since method with timestamp filtering in src/github_integration/service.py
- [X] T043 [US2] Polling support via get_comments_since() (polling loop is orchestrator concern)
- [X] T044 [US2] Add emoji and mention preservation validation in src/github_integration/service.py
- [X] T045 [US2] Add structured logging for comment operations in src/github_integration/service.py
- [X] T046 [US2] Verify all US2 tests pass and quickstart.md Test 2, 4 work

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. You can manage issues AND track agent communication via comments.

---

## Phase 5: User Story 3 - Track Workflow State (Priority: P3)

**Goal**: Enable orchestrator to add/remove labels on issues to track workflow phase (status:new, status:specs-ready, etc.)

**Independent Test**: Add label (auto-creates if missing), remove label, retrieve issue with updated labels, verify changes on GitHub

### Tests for User Story 3 (Test-First Development)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T047 [P] [US3] Contract test for add_labels with existing labels in tests/contract/test_service_interface.py
- [X] T048 [P] [US3] Contract test for add_labels with non-existent labels (auto-create) in tests/contract/test_service_interface.py
- [X] T049 [P] [US3] Contract test for add_labels with empty list (ValueError) in tests/contract/test_service_interface.py
- [X] T050 [P] [US3] Contract test for remove_labels with existing labels in tests/contract/test_service_interface.py
- [X] T051 [P] [US3] Contract test for remove_labels idempotency (silently ignore missing) in tests/contract/test_service_interface.py
- [X] T052 [P] [US3] Integration test for label auto-creation (covered by add_labels contract tests)
- [X] T053 [P] [US3] Pydantic model validation test for Label model in tests/contract/test_models.py

### Implementation for User Story 3

- [X] T054 [US3] Implement add_labels method in src/github_integration/service.py
- [X] T055 [US3] Implement label auto-creation logic (detect 422, create with #EDEDED, retry) in src/github_integration/service.py
- [X] T056 [US3] Implement remove_labels method in src/github_integration/service.py
- [X] T057 [US3] Add input validation for label operations in src/github_integration/service.py
- [X] T058 [US3] Add structured logging for label operations in src/github_integration/service.py
- [X] T059 [US3] Verify all US3 tests pass and quickstart.md Test 3 works

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently. You can manage issues, comments, AND labels.

---

## Phase 6: User Story 4 - Manage Code Review Process (Priority: P4)

**Goal**: Enable orchestrator to create pull requests and retrieve PR details to manage code review phase

**Independent Test**: Create PR with title/body/branches, retrieve PR details, list open PRs, verify "Closes #N" linking works on GitHub

### Tests for User Story 4 (Test-First Development)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T060 [P] [US4] Contract test for create_pull_request with valid input in tests/contract/test_service_interface.py
- [X] T061 [P] [US4] Contract test for create_pull_request with invalid branches (ResourceNotFoundError) in tests/contract/test_service_interface.py
- [X] T062 [P] [US4] Contract test for create_pull_request with "Closes #N" auto-linking in tests/contract/test_service_interface.py
- [X] T063 [P] [US4] Contract test for get_pull_request with valid number in tests/contract/test_service_interface.py
- [X] T064 [P] [US4] Contract test for get_pull_request with invalid number (ResourceNotFoundError) in tests/contract/test_service_interface.py
- [X] T065 [P] [US4] Contract test for list_pull_requests with state filtering in tests/contract/test_service_interface.py
- [X] T066 [P] [US4] Integration test for PR creation and retrieval (covered by PR contract tests)
- [X] T067 [P] [US4] Pydantic model validation test for PullRequest model in tests/contract/test_models.py

### Implementation for User Story 4

- [X] T068 [US4] Implement create_pull_request method in src/github_integration/service.py
- [X] T069 [US4] Implement get_pull_request method in src/github_integration/service.py
- [X] T070 [US4] Implement list_pull_requests method in src/github_integration/service.py
- [X] T071 [US4] Add branch validation for PR operations in src/github_integration/service.py
- [X] T072 [US4] Add structured logging for PR operations in src/github_integration/service.py
- [X] T073 [US4] Verify all US4 tests pass and quickstart.md Test 5 works

**Checkpoint**: All user stories should now be independently functional. Full GitHub integration complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T074 [P] Add unit tests for retry logic in tests/unit/test_retry_logic.py
- [X] T075 [P] Add unit tests for authentication token caching in tests/unit/test_auth.py
- [X] T076 [P] Add error handling tests for all exception types in tests/unit/test_error_handling.py
- [X] T077 [P] Verify structured JSON logging format meets specification in tests/unit/test_logger.py
- [X] T078 Run complete quickstart.md validation (all tests)
- [X] T079 Run ruff linter and fix any issues
- [X] T080 Run mypy type checker and fix any type errors
- [X] T081 [P] Update README.md with usage examples
- [X] T082 Verify all success criteria from spec.md (<2s, <1s, 95% success rate)
- [X] T083 Performance testing: 100 consecutive operations (SC-002)
- [X] T084 Final code review against constitution principles

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories CAN proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 (but works well together)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of US1/US2/US3

**Key Insight**: All user stories are independently implementable after foundational phase!

### Within Each User Story

1. **Tests FIRST** (Red phase): Write all contract/integration tests, ensure they FAIL
2. **Models**: Pydantic models (can be parallel with tests)
3. **Implementation** (Green phase): Implement methods to make tests pass
4. **Logging**: Add structured logging
5. **Verify**: Run tests, confirm all pass, run quickstart validation
6. **Refactor** (Refactor phase): Clean up, optimize, improve code quality

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003-T009)
- All Foundational tasks marked [P] can run in parallel (T011, T012)
- Once Foundational completes, all 4 user stories can start in parallel (Phase 3-6)
- All tests within a story marked [P] can run in parallel
- Polish tasks marked [P] can run in parallel (T074-T077, T081)

---

## Parallel Example: User Story 1

```bash
# RED Phase: Launch all tests for User Story 1 together (they should FAIL):
Task T018: "Contract test for create_issue with valid input"
Task T019: "Contract test for create_issue with missing required fields"
Task T020: "Contract test for get_issue with valid number"
Task T021: "Contract test for get_issue with invalid number"
Task T022: "Contract test for list_issues with state filtering"
Task T023: "Contract test for list_issues with label filtering"
Task T024: "Integration test for full issue lifecycle"
Task T025: "Pydantic model validation test for Issue model"

# GREEN Phase: Implement to make tests pass (sequential due to dependencies):
Task T026: "Implement GitHubService.__init__"
Task T027: "Implement create_issue method"
Task T028: "Implement get_issue method"
Task T029: "Implement list_issues method"

# Parallel within implementation:
Task T030 (validation) and T031 (logging) can run in parallel

# REFACTOR Phase: Task T032 validates everything works
```

---

## Parallel Example: Multi-Story Development

```bash
# If you have 4 developers, after Foundational (Phase 2) completes:

Developer A: Phase 3 (User Story 1 - Issues)
Developer B: Phase 4 (User Story 2 - Comments)
Developer C: Phase 5 (User Story 3 - Labels)
Developer D: Phase 6 (User Story 4 - Pull Requests)

# All can work simultaneously without conflicts (different methods in service.py)
# Each story is independently testable
# Stories complete and integrate independently
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T009)
2. Complete Phase 2: Foundational (T010-T017) - CRITICAL
3. Complete Phase 3: User Story 1 (T018-T032)
4. **STOP and VALIDATE**: Run quickstart Test 1, verify issue operations work
5. **Demo**: Show issue creation/retrieval working end-to-end

**Time Estimate**: ~2-3 hours for experienced developer following TDD

### Incremental Delivery

1. **Foundation Ready** (Phase 1-2): Base infrastructure working
2. **MVP: Issues** (+ User Story 1): Create/read/list issues → **DEMO**
3. **+ Comments** (+ User Story 2): Agent communication → **DEMO**
4. **+ Labels** (+ User Story 3): Workflow state tracking → **DEMO**
5. **Complete** (+ User Story 4): PR management → **FINAL DEMO**

Each increment adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. **Together**: Complete Setup + Foundational (Phase 1-2)
2. **Split**: Once Foundational done, assign one story per developer:
   - Dev A: User Story 1 (Issues)
   - Dev B: User Story 2 (Comments)
   - Dev C: User Story 3 (Labels)
   - Dev D: User Story 4 (Pull Requests)
3. **Integrate**: Stories complete independently, minimal merge conflicts
4. **Validate**: Each developer runs their quickstart tests
5. **Polish**: Together complete Phase 7

**Estimated Time (4 devs)**: 3-4 hours total vs 8-10 hours sequential

---

## Test-First Development Workflow (Per User Story)

### RED Phase

1. Read acceptance scenarios from spec.md for this story
2. Write all contract tests (should FAIL - no implementation yet)
3. Write all integration tests (should FAIL)
4. Write Pydantic model validation tests (should FAIL)
5. **Verify**: Run `pytest tests/` - all tests for this story should be RED (failing)

### GREEN Phase

1. Implement minimum code to make first test pass
2. Run tests - one should now pass (GREEN)
3. Implement next method to make next test pass
4. Repeat until all tests GREEN
5. Add logging, validation, error handling
6. **Verify**: Run `pytest tests/` - all tests for this story should be GREEN (passing)

### REFACTOR Phase

1. Review code for duplication, complexity
2. Clean up, optimize, improve readability
3. Run tests after each refactor - must stay GREEN
4. Run quickstart validation for this story
5. **Verify**: All tests still GREEN, quickstart works, code is clean

---

## Notes

- **[P] tasks**: Different files, no dependencies, safe to parallelize
- **[Story] label**: Maps task to specific user story for traceability
- **Test-First**: RED → GREEN → REFACTOR cycle strictly enforced (Constitution Principle I)
- **Independent Stories**: Each user story can be completed and tested independently
- **Checkpoints**: Stop at any checkpoint to validate story independently before proceeding
- **File Paths**: All paths are exact locations for implementation
- **Commit Frequently**: Commit after each test passes, after each method implemented
- **Constitution Compliance**: Verified in Phase 7 (T084)

---

## Quick Reference

**Total Tasks**: 84
- Setup (Phase 1): 9 tasks
- Foundational (Phase 2): 8 tasks
- User Story 1 (Phase 3): 15 tasks (8 tests, 7 implementation)
- User Story 2 (Phase 4): 14 tasks (7 tests, 7 implementation)
- User Story 3 (Phase 5): 13 tasks (7 tests, 6 implementation)
- User Story 4 (Phase 6): 14 tasks (8 tests, 6 implementation)
- Polish (Phase 7): 11 tasks

**Parallel Opportunities**: 45 tasks marked [P] can be parallelized

**MVP Scope**: Phases 1-3 (32 tasks) delivers independently testable issue management

**Format Validation**: ✅ All tasks follow checklist format with ID, [P], [Story], file paths

