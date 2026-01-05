# Feature Specification: GitHub Integration Core

**Feature Branch**: `001-github-integration-core`
**Created**: 2026-01-02
**Status**: Draft
**Input**: User description: "Backend service for GitHub operations - CRUD for issues, comments, labels, PRs, and webhook receiver for real-time monitoring"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Track Workflow Issues (Priority: P1)

As the Farmer Code orchestrator, I need to create GitHub issues to represent features being developed, and retrieve issue details to understand what work needs to be done, so that I can initiate and track the SDLC workflow.

**Why this priority**: This is the absolute foundation. Without the ability to create and read issues, the orchestrator cannot start any workflow. Every workflow begins with a GitHub issue as the source of truth.

**Independent Test**: Can be fully tested by creating a new issue via the service with title and description, retrieving the created issue by number, and verifying the issue exists on GitHub. Delivers immediate value by establishing the single source of truth for all work.

**Acceptance Scenarios**:

1. **Given** a connected GitHub repository, **When** the orchestrator creates an issue with title "Add user authentication" and description, **Then** a new issue is created on GitHub with correct title, body, and returns the issue number
2. **Given** an existing issue number, **When** the orchestrator retrieves the issue details, **Then** the issue title, body, state, labels, and metadata are returned
3. **Given** a repository with multiple issues, **When** the orchestrator requests all open issues, **Then** all issues with state "open" are returned with their details
4. **Given** an issue creation request with missing required fields, **When** the request is processed, **Then** a validation error is returned with specific missing field information

---

### User Story 2 - Facilitate Agent Communication (Priority: P2)

As the Farmer Code orchestrator, I need to post comments to issues on behalf of agents and read all comments to detect agent signals (completion, questions, blocks), so that I can coordinate multi-agent workflows and track progress.

**Why this priority**: Agent communication is the heartbeat of the system. Agents signal completion (✅), ask questions (❓), and report status (📝) via comments. Without this, the orchestrator cannot detect when agents finish their work or need help.

**Independent Test**: Can be tested by posting a comment "✅ Specs complete. @baron" to an issue, retrieving all comments, and verifying the comment appears with correct author and timestamp. Delivers value by enabling the orchestrator to track agent progress.

**Acceptance Scenarios**:

1. **Given** an existing issue, **When** the orchestrator posts a comment with text "✅ Backend plan complete. @baron", **Then** the comment appears on the GitHub issue with the configured author
2. **Given** an issue with existing comments, **When** the orchestrator retrieves all comments, **Then** all comments are returned in chronological order with author, body, and timestamp
3. **Given** the orchestrator last checked comments at timestamp T, **When** it requests comments since T, **Then** only new comments posted after T are returned
4. **Given** a comment post request with emoji characters (✅, ❓, 📝), **When** the comment is posted, **Then** emoji characters are preserved correctly on GitHub

---

### User Story 3 - Track Workflow State (Priority: P3)

As the Farmer Code orchestrator, I need to add and remove labels on issues to track the current workflow phase (status:new, status:specs-ready, etc.), so that both the system and humans can understand workflow progress at a glance.

**Why this priority**: Labels are the visual state indicator. While the orchestrator tracks state internally, labels make the workflow transparent to humans on GitHub and enable filtering/reporting.

**Independent Test**: Can be tested by adding label "status:specs-ready" to an issue, removing label "status:new", retrieving the issue, and verifying the labels reflect the change on GitHub.

**Acceptance Scenarios**:

1. **Given** an issue with label "status:new", **When** the orchestrator adds label "status:specs-ready" and removes "status:new", **Then** the issue on GitHub shows only "status:specs-ready"
2. **Given** an issue without any labels, **When** the orchestrator adds multiple labels in one operation, **Then** all labels are applied to the issue
3. **Given** an issue with multiple labels, **When** the orchestrator retrieves the issue, **Then** all current labels are included in the response
4. **Given** an attempt to add a label that doesn't exist in the repository, **When** the operation is executed, **Then** the label is created automatically with a default color and applied to the issue

---

### User Story 4 - Manage Code Review Process (Priority: P4)

As the Farmer Code orchestrator, I need to create pull requests and retrieve PR details to manage the code review phase of the workflow, so that agent-generated code can be reviewed and merged.

**Why this priority**: PR operations are essential for workflow completion, but only needed in Phase 6-8. The orchestrator can function through Phase 1-5 without this, making it lower priority for the initial bootstrap.

**Independent Test**: Can be tested by creating a PR from branch "123-test-feature" to "main" with title and body, retrieving the PR details, and verifying the PR exists on GitHub with correct base and head branches.

**Acceptance Scenarios**:

1. **Given** a branch with commits, **When** the orchestrator creates a PR with title, body, base "main", and head "123-add-auth", **Then** a new PR is created on GitHub linking the issue
2. **Given** an existing PR number, **When** the orchestrator retrieves PR details, **Then** the PR title, body, state, base branch, head branch, and linked issue are returned
3. **Given** a PR creation request, **When** the body includes "Closes #123", **Then** the PR is automatically linked to issue #123 on GitHub
4. **Given** multiple PRs in the repository, **When** the orchestrator requests all open PRs, **Then** all PRs with state "open" are returned

---

### Edge Cases

- What happens when GitHub API rate limit is exceeded?
- How does the service handle GitHub API downtime or 5xx errors?
- What happens when authentication token expires or is revoked?
- How does the service handle network timeouts during API calls?
- What happens when creating an issue in a repository that doesn't exist?
- How does the service handle special characters, emojis, and markdown in issue/comment bodies?
- What happens when trying to read comments from a deleted or inaccessible issue?
- How does the service handle very long issue descriptions (100KB+)?
- What happens when polling interval causes rate limit issues (too frequent polling)?
- How does the service handle missed comments during temporary network outages?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Service MUST authenticate with GitHub using GitHub App credentials (App ID: 2578431, Installation ID: 102211688) by generating installation access tokens from the private key (PEM file) accessed via GITHUB_APP_PRIVATE_KEY_PATH environment variable
- **FR-002**: Service MUST create issues with title, body, and optional labels, returning the created issue number
- **FR-003**: Service MUST retrieve issue details by issue number including title, body, state, labels, assignees, created date, and updated date
- **FR-004**: Service MUST list all issues in a repository with filtering by state (open/closed) and labels
- **FR-005**: Service MUST post comments to issues with formatted text including emoji characters
- **FR-006**: Service MUST retrieve all comments on an issue in chronological order with author, body, timestamp, and comment ID
- **FR-007**: Service MUST support retrieving comments since a specific timestamp to enable incremental polling
- **FR-008**: Service MUST add labels to issues individually or in batches
- **FR-009**: Service MUST automatically create labels that don't exist in the repository when attempting to add them to an issue, using a default color
- **FR-010**: Service MUST remove labels from issues individually or in batches
- **FR-011**: Service MUST create pull requests with title, body, base branch, head branch, and optional issue linking
- **FR-012**: Service MUST retrieve pull request details including state, branches, linked issues, and review status
- **FR-013**: Service MUST list all pull requests in a repository with filtering by state
- **FR-014**: Service MUST handle GitHub API rate limits by respecting rate limit headers and returning appropriate errors when limits are exceeded
- **FR-015**: Service MUST retry failed API requests up to 3 times with 1-second delay between attempts for transient errors (network timeouts, 5xx responses)
- **FR-016**: Service MUST validate all API requests and return meaningful error messages for invalid input
- **FR-017**: Service MUST log all GitHub API operations including request, response, and errors as structured JSON to stdout/stderr
- **FR-018**: Service MUST expose operations via a RESTful API or programmatic interface for use by the orchestrator

### Key Entities

- **Issue**: Represents a GitHub issue with attributes including issue number (unique identifier), title, body/description, state (open/closed), labels (array of label names), assignees (array of usernames), creation timestamp, last updated timestamp, and repository reference
- **Comment**: Represents an issue comment with attributes including comment ID (unique identifier), issue number (parent issue), author (username or bot name), body (markdown text), timestamp, and reactions
- **Label**: Represents a GitHub label with attributes including name (e.g., "status:new"), color (hex code), and description
- **Pull Request**: Represents a GitHub pull request with attributes including PR number, title, body, state (open/closed/merged), base branch, head branch, linked issues (array of issue numbers), review status, and merge status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Orchestrator can create an issue and retrieve it within 2 seconds under normal GitHub API availability
- **SC-002**: Service successfully handles 100 consecutive API operations (mix of create, read, update) without errors when GitHub API is healthy
- **SC-003**: Comment retrieval latency is under 1 second for issues with up to 100 comments
- **SC-004**: Polling mechanism detects new comments within 10 seconds (based on 5-10 second poll interval)
- **SC-005**: Service achieves 95% success rate for API operations under normal GitHub availability conditions
- **SC-006**: Service gracefully handles GitHub rate limiting by returning appropriate error codes 100% of the time when limits are exceeded
- **SC-007**: All API operations return meaningful error messages that enable the orchestrator to determine corrective action without examining logs

## Clarifications

### Session 2026-01-02

- Q: When the GitHub API returns an error (rate limit, 5xx, network timeout), how should the service handle retry logic? → A: Fixed 3 retries with 1-second delay between attempts
- Q: Where should the service write log output for GitHub API operations (FR-016)? → A: Structured JSON to stdout/stderr (12-factor app pattern)
- Q: How should the GitHub authentication token (PAT or App token) be stored and accessed by the service? → A: PEM file on disk (chmod 600), path in env var GITHUB_APP_PRIVATE_KEY_PATH (current path: ./keys/orchestrator.pem)
- Q: What should happen when a label that doesn't exist in the repository is added to an issue? → A: Create the label automatically with a default color
- Q: Which GitHub repository should the service connect to for the farmcode-tests testing repository? → A: farmer1st/farmcode-tests

## Assumptions *(if applicable)*

- The GitHub App (ID: 2578431) has been registered with necessary permissions (read/write issues, read/write pull requests) and installed (Installation ID: 102211688)
- The private key PEM file is stored at ./keys/orchestrator.pem with file permissions 600
- The service will connect to the farmer1st/farmcode-tests repository for testing purposes initially (multi-repo support is deferred)
- The service will use github.com (GitHub Enterprise Server support is out of scope)
- The service runs as a backend service accessible only to the orchestrator (no direct human/UI access)
- **The service runs locally on developer's machine (Mac/Linux/Windows) without publicly accessible endpoint**
- **The service uses REST API polling (every 5-10 seconds) for monitoring issue comments and updates** - this is the ONLY approach for Feature 1.1
- Webhook support is explicitly deferred to a future feature (requires public endpoint or tunneling solution like ngrok)

## Out of Scope *(if applicable)*

- **Webhook integration** (deferred to future feature - requires publicly accessible endpoint incompatible with local-first design)
- GitHub Actions integration or workflow management
- Repository management (creating/deleting repos, managing settings)
- Team and organization management
- Branch protection rules management
- GitHub Discussions or Projects integration
- Issue template management
- Advanced PR operations (merge, approve, request changes) - only create/read in scope
- Comment editing or deletion (only create/read in scope)
- Reactions or emoji responses to comments
- Multi-repository orchestration in a single workflow
- Credential/token management UI
- Rate limit prediction or optimization beyond basic retry logic
