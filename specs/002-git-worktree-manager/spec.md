# Feature Specification: Git Worktree Manager

**Feature Branch**: `002-git-worktree-manager`
**Created**: 2026-01-03
**Status**: Draft
**Input**: User description: "Feature 1.2: Git Worktree Manager - Service for managing git branches and worktrees. Capabilities: Create branches from main, create worktrees in sibling directories, create .plans folder structure, commit and push changes, remove worktrees, delete branches. This is the second foundation piece for the orchestrator."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Branch and Worktree (Priority: P1)

As the orchestrator system, I need to create a new feature branch and corresponding worktree so that each feature can be developed in isolation without interfering with other work.

**Why this priority**: This is the foundational capability. Without branch and worktree creation, no isolated feature development can occur. Every SDLC workflow begins with this step.

**Independent Test**: Can be fully tested by requesting a new worktree for issue #123 and verifying a branch exists with a worktree in a sibling directory.

**Acceptance Scenarios**:

1. **Given** a valid issue number (e.g., 123) and feature name (e.g., "add-user-auth"), **When** worktree creation is requested, **Then** a branch named "123-add-user-auth" is created from main and a worktree is created in a sibling directory (e.g., `../farmcode-123-add-user-auth/`)

2. **Given** a worktree creation request, **When** the branch already exists remotely, **Then** the system checks out the existing branch into the new worktree instead of creating a duplicate

3. **Given** a worktree creation request, **When** the sibling directory already exists, **Then** the system returns an error indicating the worktree already exists

---

### User Story 2 - Initialize Plans Structure (Priority: P1)

As the orchestrator system, I need to initialize the `.plans` folder structure within a worktree so that agents have a standardized location for specifications, plans, and reviews.

**Why this priority**: The `.plans` folder is where all SDLC artifacts are stored. Without this structure, agents cannot produce or find their deliverables.

**Independent Test**: Can be fully tested by initializing plans for issue #123 and verifying the folder structure exists with correct files.

**Acceptance Scenarios**:

1. **Given** an existing worktree for issue 123, **When** plans initialization is requested, **Then** a `.plans/123/` directory is created with subdirectories: `specs/`, `plans/`, `reviews/`

2. **Given** an existing worktree, **When** plans initialization is requested, **Then** a `README.md` file is created in `.plans/123/` with basic feature information (issue number, creation date, status)

3. **Given** plans initialization request, **When** the `.plans/123/` directory already exists, **Then** the system skips creation and returns success (idempotent operation)

---

### User Story 3 - Commit and Push Changes (Priority: P2)

As the orchestrator system, I need to commit changes within a worktree and push them to the remote repository so that work is saved and visible to other agents and humans.

**Why this priority**: Important for persisting work, but the system can function temporarily without it. Commits can be batched.

**Independent Test**: Can be fully tested by making changes in a worktree, committing with a message, and verifying the commit exists on the remote branch.

**Acceptance Scenarios**:

1. **Given** a worktree with uncommitted changes, **When** commit is requested with message "Add spec for user auth", **Then** all changes are staged, committed with the provided message, and pushed to the remote branch

2. **Given** a worktree with no changes, **When** commit is requested, **Then** the system returns success with a message indicating nothing to commit

3. **Given** a worktree, **When** commit is requested but push fails (e.g., network error), **Then** the system returns an error indicating the commit succeeded but push failed, with the option to retry push

---

### User Story 4 - Remove Worktree and Cleanup (Priority: P2)

As the orchestrator system, I need to remove worktrees and optionally delete branches after a feature is merged so that the local environment stays clean and resources are freed.

**Why this priority**: Important for system hygiene, but not blocking for core workflows. Can be done asynchronously.

**Independent Test**: Can be fully tested by removing a worktree for issue #123 and verifying the worktree directory is deleted and branch is optionally removed.

**Acceptance Scenarios**:

1. **Given** an existing worktree for issue 123, **When** worktree removal is requested, **Then** the worktree directory is deleted and the worktree is unregistered from git

2. **Given** worktree removal request with `delete_branch=true`, **When** removal is executed, **Then** both the worktree is removed and the local branch is deleted

3. **Given** worktree removal request with `delete_remote_branch=true`, **When** removal is executed and the branch is merged, **Then** the remote branch is also deleted

4. **Given** worktree removal request, **When** the worktree has uncommitted changes, **Then** the system returns an error and does not delete (unless force flag is provided)

---

### Edge Cases

- What happens when the main branch doesn't exist or is not accessible?
  - System returns error indicating main branch is required
- What happens when git is not installed or not in PATH?
  - System returns error with clear message about git dependency
- What happens when there's no network connection during push?
  - System completes local operations and returns partial success with retry option
- What happens when the user doesn't have write access to the repository?
  - System returns authentication/permission error on push operations
- What happens when disk space is insufficient for worktree creation?
  - System returns error indicating insufficient disk space
- What happens when worktree path contains special characters or spaces?
  - System handles paths with spaces correctly using proper escaping

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create git branches from the main branch with naming convention `{issue_number}-{feature_name}`
- **FR-002**: System MUST create worktrees in sibling directories with naming convention `{repo_name}-{issue_number}-{feature_name}`
- **FR-003**: System MUST support checking out existing remote branches into new worktrees
- **FR-004**: System MUST initialize `.plans/{issue_number}/` directory structure with `specs/`, `plans/`, and `reviews/` subdirectories
- **FR-005**: System MUST create a `README.md` in the `.plans/{issue_number}/` directory with feature metadata
- **FR-006**: System MUST stage, commit, and push changes in a single operation
- **FR-007**: System MUST support custom commit messages
- **FR-008**: System MUST remove worktrees and unregister them from git
- **FR-009**: System MUST optionally delete local branches during worktree cleanup
- **FR-010**: System MUST optionally delete remote branches during worktree cleanup
- **FR-011**: System MUST prevent deletion of worktrees with uncommitted changes (unless force flag provided)
- **FR-012**: System MUST handle all operations idempotently where possible (re-running same operation produces same result)
- **FR-013**: System MUST return clear error messages for all failure scenarios

### Key Entities

- **Worktree**: Represents a git worktree with associated branch, directory path, and issue number
- **Branch**: Represents a git branch with name, remote tracking status, and merge status
- **PlansFolder**: Represents the `.plans/{issue_number}/` structure with its subdirectories and metadata file

### Service Interface

**Service**: WorktreeService

| Method | Purpose | Inputs | Outputs |
|--------|---------|--------|---------|
| `create_worktree()` | Create branch from main and worktree in sibling directory | issue_number, feature_name | Worktree |
| `create_worktree_from_existing()` | Create worktree from existing remote branch | issue_number, feature_name, branch_name? | Worktree |
| `init_plans()` | Initialize .plans/{issue}/ structure | issue_number, feature_title? | PlansFolder |
| `get_plans()` | Get PlansFolder if exists | issue_number | PlansFolder or None |
| `commit_and_push()` | Stage, commit, and push changes | issue_number, message, push? | CommitResult |
| `push()` | Push commits to remote | issue_number | bool |
| `remove_worktree()` | Remove worktree and optionally delete branches | issue_number, delete_branch?, delete_remote_branch?, force? | OperationResult |
| `list_worktrees()` | List all managed worktrees | - | list[Worktree] |
| `get_worktree()` | Get worktree by issue number | issue_number | Worktree or None |
| `get_branch()` | Get branch info by name | name | Branch or None |

**Error Conditions**:
- `GitNotFoundError`: Git not installed or not in PATH
- `NotARepositoryError`: Path is not a git repository
- `MainBranchNotFoundError`: Main branch doesn't exist
- `WorktreeExistsError`: Worktree directory already exists
- `WorktreeNotFoundError`: No worktree for issue number
- `BranchNotFoundError`: Branch doesn't exist
- `UncommittedChangesError`: Dirty worktree blocks operation
- `PushError`: Push to remote failed

**Detailed contracts**: See `contracts/worktree-service.md` after planning phase.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Worktree creation completes in under 30 seconds for repositories up to 1GB
- **SC-002**: All operations return within 5 seconds for local-only actions (excluding network operations)
- **SC-003**: System correctly handles 50+ concurrent worktrees without conflicts
- **SC-004**: 100% of edge cases defined above are handled with appropriate error messages
- **SC-005**: Operations are idempotent - running the same create operation twice produces the same result without errors
- **SC-006**: Cleanup operations free 100% of disk space used by removed worktrees

## Assumptions

- Git is installed and available in the system PATH
- User has appropriate permissions (read/write) on the repository
- The repository has a `main` branch as the default branch
- Network connectivity is available for remote operations (push, fetch, remote branch deletion)
- Sufficient disk space exists for worktree creation
- The orchestrator provides valid issue numbers and feature names
