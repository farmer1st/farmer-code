<!--
Sync Impact Report:
- Version change: 1.6.4 → 1.7.0
- Modified principles: XI (Documentation and User Journeys)
- Added sections: Documentation Directory Structure with explicit docs/ folder requirements
- Removed sections: None
- Templates requiring updates:
  - tasks-template.md - add documentation tasks for docs/ folder structure
- Follow-up TODOs:
  - Create missing docs/ structure for existing features
  - Add docs/ structure validation to CI (optional)
- Rationale for MINOR bump: Added new requirement (docs/ folder structure) that affects all features
Previous changes:
- 1.6.3 → 1.6.4: Added Redocly CLI tooling and API-first workflow
- 1.6.2 → 1.6.3: Added comprehensive API Documentation Standards in Quality Standards
- 1.6.1 → 1.6.2: Added Service Interface requirement in Documentation Requirements
- 1.6.0 → 1.6.1: Reverted to manual tagging (release-please blocked by org)
- 1.5.2 → 1.6.0: Added conventional commits requirement
- 1.5.1 → 1.5.2: Added release-please (later removed)
- 1.5.0 → 1.5.1: Made E2E tests mandatory in CI
- 1.4.0 → 1.5.0: Added Principle XII (Continuous Integration and Delivery)
- 1.3.0 → 1.4.0: Added Principle XI (Documentation and User Journeys)
- 1.2.1 → 1.3.0: Added Principle X (Security-First Development)
- 1.2.0 → 1.2.1: Added deployment strategy (local-first with AWS/K8s option)
- 1.1.3 → 1.2.0: Added Principle IX (Thin Client Architecture)
- 1.1.2 → 1.1.3: Changed to Vite + React for SPA architecture
- 1.1.1 → 1.1.2: Added Pydantic v2 for backend data validation
- 1.1.0 → 1.1.1: Added shadcn/ui for UI components
- 1.0.0 → 1.1.0: Added Principle VIII (Technology Stack Standards) and Monorepo Structure
- Initial: 1.0.0 ratified with 7 core principles
-->

# Farmer Code Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

**Rule**: Tests MUST be written before implementation code. No exceptions.

**Implementation**:
- Tests are designed and approved BEFORE any code is written
- Tests MUST fail initially (red phase)
- Implementation proceeds only to make tests pass (green phase)
- Refactoring occurs only after tests pass
- Red-Green-Refactor cycle is strictly enforced

**Rationale**: Test-first development ensures code meets requirements, reduces defects, provides living documentation, and enables confident refactoring. This is the foundation of quality in Farmer Code.

### II. Specification-Driven Development

**Rule**: All features MUST have approved specifications before implementation begins.

**Implementation**:
- User scenarios define what to build (spec.md)
- Implementation plans define how to build it (plan.md)
- Test plans define verification criteria (tests.md)
- Human approval gates ensure alignment at each stage
- Specifications are versioned and linked to implementation

**Rationale**: Specifications prevent miscommunication, enable parallel work, provide audit trails, and ensure stakeholder alignment before costly implementation begins.

### III. Independent User Stories

**Rule**: User stories MUST be independently implementable, testable, and deliverable.

**Implementation**:
- Each user story has explicit priority (P1, P2, P3...)
- Stories can be implemented in isolation
- Each story delivers measurable value
- Story completion includes independent verification
- MVP is achievable with P1 stories alone

**Rationale**: Independent stories enable incremental delivery, parallel development, risk mitigation, and allow stopping at any checkpoint while retaining delivered value.

### IV. Human Approval Gates

**Rule**: Four mandatory human approval gates MUST be passed before merge.

**Gates**:
1. **Gate 1 - Specifications**: Human approves architecture and specs
2. **Gate 2 - Plans**: Human approves implementation plans
3. **Gate 3 - Tests**: Human approves test design
4. **Gate 4 - Review**: Human approves code review and merge

**Rationale**: Human oversight ensures alignment with business goals, catches architectural issues early, validates test coverage, and maintains code quality standards that AI agents cannot fully evaluate.

### V. Parallel-First Execution

**Rule**: Tasks MUST be designed for maximum parallelization where dependencies allow.

**Implementation**:
- Tasks marked [P] indicate parallel execution capability
- Foundational phase MUST complete before user story work begins
- User stories can execute in parallel after foundation is ready
- Within stories, models/tests can run in parallel
- Sequential dependencies are explicitly documented

**Rationale**: Parallel execution reduces delivery time, maximizes resource utilization, and enables team scaling while maintaining quality through proper dependency management.

### VI. Simplicity and YAGNI

**Rule**: Implement only what is needed. Complexity MUST be justified.

**Implementation**:
- Start with simplest solution that meets requirements
- Additional complexity requires documentation in Complexity Tracking table
- Simpler alternatives MUST be considered and rejected reasons documented
- Premature abstraction is prohibited
- Future requirements do not justify current complexity

**Rationale**: Simple code is maintainable, debuggable, and adaptable. Complexity creates technical debt and hinders velocity. YAGNI (You Aren't Gonna Need It) prevents over-engineering.

### VII. Versioning and Change Control

**Rule**: All artifacts MUST be versioned using semantic versioning. All commits MUST use conventional commit format.

**Implementation**:
- Constitution: MAJOR.MINOR.PATCH (backward compatibility semantics)
- Specifications: Linked to feature branches and issue numbers
- All changes tracked through Git with conventional commit messages
- Breaking changes require MAJOR version bump and migration plan

**Conventional Commits** (REQUIRED):
- Format: `<type>(<scope>): <description>`
- **Types** (required prefix):
  - `feat:` - New feature (bumps MINOR version)
  - `fix:` - Bug fix (bumps PATCH version)
  - `docs:` - Documentation only
  - `style:` - Formatting, no code change
  - `refactor:` - Code restructuring, no behavior change
  - `test:` - Adding/updating tests
  - `chore:` - Maintenance, dependencies, CI
- **Breaking changes**: Add `!` after type or include `BREAKING CHANGE:` in body
  - Example: `feat!: remove deprecated API` (bumps MAJOR version)
- **Scope** (optional): Component affected, e.g., `feat(auth): add OAuth`
- **Examples**:
  ```
  feat: add user authentication
  fix(api): handle null response from GitHub
  docs: update README with setup instructions
  feat!: change API response format
  chore: update dependencies
  ```

**Rationale**: Versioning enables traceability, rollback capability, change impact analysis, and coordination across distributed teams. Conventional commits enable automated changelog generation and semantic versioning via release-please.

### VIII. Technology Stack Standards

**Rule**: All projects MUST use the approved technology stack. Deviations require justification in Complexity Tracking.

**Monorepo Management**:
- **Build System**: Turborepo for task orchestration and caching
- **Package Manager**: pnpm for workspace management
- **Version Control**: GitHub with branch protection and required reviews
- **Monorepo Structure**: Apps and packages organized by domain

**Backend Stack** (Python):
- **Language**: Python 3.11+
- **Package Manager**: uv for fast, reliable dependency management
- **Linter/Formatter**: ruff for code quality and formatting
- **Testing**: pytest with pytest-asyncio for async code
- **Type Checking**: mypy for static type analysis
- **Framework**: FastAPI (API services) or similar based on requirements
- **Data Validation**: Pydantic v2 for data models, validation, and settings management
- **Database**: SQLAlchemy 2.0+ ORM with async support
- **Migrations**: Alembic for database schema versioning

**Database Management**:
- **Local Development**: SQLite for simplicity and zero-config
- **Cloud Deployment**: PostgreSQL on RDS (when moving to AWS)
- **ORM**: SQLAlchemy async with declarative models
- **Migrations**:
  - Alembic for all schema changes
  - Sequential numbering: 001_initial.py, 002_add_users.py, etc.
  - Never edit existing migrations (create new ones)
  - Migration script MUST include upgrade() and downgrade()
  - Test migrations: run upgrade, then downgrade before committing
- **Schema Standards**:
  - All tables MUST have: `id` (UUID/int primary key), `created_at`, `updated_at`
  - Use database constraints: NOT NULL, UNIQUE, FOREIGN KEY
  - Indexes on frequently queried columns
  - Soft deletes via `deleted_at` column (preserve data)
- **Transactions**:
  - Multi-step operations MUST use database transactions
  - Use SQLAlchemy session.begin() context manager
  - Rollback on exceptions
- **Backup Strategy**:
  - Local: SQLite file copied before migrations (automatic)
  - Cloud: RDS automated backups (daily, 7-day retention)

**Frontend Stack** (TypeScript):
- **Language**: TypeScript 5.0+
- **Build Tool**: Vite for fast builds and hot module replacement
- **Framework**: React 18+ for UI components (SPA architecture)
- **Routing**: React Router v6 for client-side routing
- **UI Components**: shadcn/ui (Radix UI primitives + Tailwind CSS)
- **Styling**: Tailwind CSS for utility-first styling
- **Linting**: ESLint + Prettier for code quality
- **Testing**: Vitest for unit/integration tests, Playwright for E2E
- **State Management**: React Context/Zustand (avoid Redux unless justified)
- **HTTP Client**: TanStack Query (React Query) for server state management

**Development Tools**:
- **Containerization**: Docker for local development and deployment
- **CI/CD**: GitHub Actions with Turborepo remote caching
- **Code Quality**: Pre-commit hooks enforcing linting and tests
- **Documentation**: Markdown for all documentation

**Deployment Strategy**:
- **Primary**: Local deployment (development, single-user, on-premises)
- **Future Option**: AWS deployment with SPA (S3/CloudFront) + Kubernetes workloads
- **Architecture**: Local-first, cloud-ready (avoid cloud-specific dependencies)
- **Constraints**:
  - Backend MUST run in containers (Docker/Podman)
  - Frontend MUST be deployable as static files
  - No hard dependencies on cloud-specific services (use abstraction)
  - Configuration MUST support both local and cloud environments
  - Database/storage MUST be swappable (local SQLite/PostgreSQL vs RDS)
  - Secrets management MUST work locally and in cloud
- **Design Principles**:
  - 12-factor app methodology where applicable
  - Environment-based configuration (not deployment-based)
  - Stateless backend services (horizontal scaling ready)
  - Health checks and readiness probes
  - Graceful shutdown handling

**Rationale**: Standardized tooling reduces cognitive load, enables code sharing, simplifies CI/CD, and ensures consistent developer experience. The selected tools are industry-standard, well-maintained, and optimized for monorepo development. The SPA architecture with Vite provides fast builds, simple deployment, and clear separation between frontend and backend concerns. Local-first design ensures no vendor lock-in while keeping cloud deployment as a viable option.

### IX. Thin Client Architecture (NON-NEGOTIABLE)

**Rule**: ALL business logic, validation, and intelligence MUST reside in the backend. Clients are presentation-only.

**Implementation**:
- Backend APIs MUST be completely client-agnostic
- Frontend MUST NOT contain any business logic or domain rules
- All validation, calculations, and decisions happen server-side
- Clients only handle: UI rendering, user input collection, API calls, display formatting
- API design MUST support multiple client types (web, TUI, mobile, CLI, etc.)
- Backend MUST return fully processed, ready-to-display data
- Frontend state management limited to UI state only (not business state)

**Prohibited in Clients**:
- ❌ Business rule validation (e.g., "is this order valid?")
- ❌ Calculations or transformations (e.g., "calculate total price")
- ❌ Authorization decisions (e.g., "can user do this?")
- ❌ Data filtering based on business rules
- ❌ Workflow logic or state machines
- ❌ Domain-specific algorithms

**Allowed in Clients**:
- ✅ Form input validation (format only, e.g., "is email format valid?")
- ✅ UI state (modals open/closed, current tab, etc.)
- ✅ Display formatting (dates, currency display)
- ✅ Client-side routing and navigation
- ✅ Optimistic UI updates (with server confirmation)
- ✅ Caching server responses

**API Design Requirements**:
- Endpoints MUST return complete, processed data structures
- Backend MUST handle all filtering, sorting, pagination
- Responses MUST include all display-ready information
- Backend MUST perform all access control checks
- APIs MUST be RESTful or GraphQL (not RPC-style with client logic)
- OpenAPI/Swagger specs MUST document all endpoints

**Multi-Client Support**:
- Same backend APIs serve web, TUI, mobile, CLI clients
- Client type detected via User-Agent or explicit client parameter
- Response format may vary (JSON, text, etc.) but data is identical
- Feature parity across all client types
- Backend testing MUST NOT assume specific client type

**Rationale**: Thin client architecture enables multiple client implementations, simplifies testing, centralizes security and business logic, prevents logic duplication, and makes the system easier to maintain and evolve. When adding a TUI or mobile client later, no backend changes should be needed.

### X. Security-First Development

**Rule**: Security is a habit, not a feature. Follow secure coding practices from day one.

**Implementation**:
- **Secrets Management**:
  - API keys, credentials MUST use environment variables (.env files)
  - .env files MUST be in .gitignore (never committed)
  - Use python-dotenv or similar for loading secrets
  - Template file (.env.example) with dummy values for documentation

- **Authentication** (for future Google OAuth):
  - Local development: Optional authentication (single-user mode)
  - Cloud deployment: Google OAuth required
  - JWT tokens with expiration (1 hour access, 7 day refresh)
  - Refresh token rotation on use

- **Input Validation**:
  - All user inputs validated with Pydantic models (backend)
  - SQL injection prevented via SQLAlchemy ORM (no raw SQL)
  - Type checking with mypy ensures type safety

- **HTTPS/TLS**:
  - Local development: HTTP acceptable (localhost only)
  - Cloud deployment: HTTPS required (CloudFront handles TLS)

- **CORS Configuration**:
  - Local: Allow localhost origins
  - Cloud: Restrict to specific domain(s)
  - Never use CORS "*" wildcard in production

**Prohibited**:
- ❌ Secrets in version control (API keys, passwords, tokens)
- ❌ Raw SQL queries (use ORM)
- ❌ Eval() or exec() functions
- ❌ Unvalidated user input directly in queries
- ❌ Storing passwords in plain text (even for testing)

**Allowed Simplifications** (small internal tool):
- ✅ HTTP on localhost during development
- ✅ Simple auth or no auth for local single-user mode
- ✅ Self-signed certs for local HTTPS testing
- ✅ Basic error messages (no sensitive data exposure)

**Dependency Security**:
- GitHub Dependabot enabled for vulnerability alerts
- Regular dependency updates (monthly review)
- Pin major versions, allow patch updates

**Rationale**: Security habits prevent future vulnerabilities. Even internal tools benefit from secure defaults. Preparing for Google OAuth now (environment-based config) makes cloud deployment smooth. Small tool = practical security, not enterprise paranoia.

### XI. Documentation and User Journeys

**Rule**: Every feature MUST have comprehensive documentation and user journeys mapped to tests.

**User Journey Requirements**:
- **Unique Journey IDs**: Format `[DOMAIN]-[NNN]` where:
  - DOMAIN = 2-4 letter code for domain (e.g., ORC=Orchestrator, GH=GitHub, UI=User Interface)
  - NNN = 3-digit sequential number (001, 002, 003, etc.)
  - Examples: `ORC-001`, `GH-023`, `UI-007`

- **Journey Documentation** (in `docs/user-journeys/[DOMAIN]-[NNN]-[name].md`):
  ```markdown
  # [DOMAIN-NNN]: [Journey Name]

  **Actor**: [Who performs this journey]
  **Goal**: [What they want to accomplish]
  **Preconditions**: [What must be true before starting]
  **Priority**: [P1/P2/P3]

  ## Steps:
  1. [Action description]
     - Expected outcome: [What should happen]
     - System behavior: [How system responds]

  2. [Next action]
     ...

  ## Success Criteria:
  - [Measurable outcome 1]
  - [Measurable outcome 2]

  ## E2E Test Coverage:
  - Test file: `tests/e2e/test_[journey_name].py`
  - Journey marker: `@pytest.mark.journey("[DOMAIN]-[NNN]")`
  - Covered steps: [List which steps are covered]
  - Test status: [Link to latest test results]

  ## Related Journeys:
  - [DOMAIN-XXX]: [Related journey name]
  ```

- **Journey Registry** (in `docs/user-journeys/README.md`):
  - Table of all journeys with ID, name, priority, status, test coverage
  - Shows which journeys are implemented, tested, passing
  - Links to journey documentation files

**Documentation Requirements**:
- **Feature README** (`src/[module]/README.md`):
  - Purpose and scope
  - Quick start guide
  - Installation/setup instructions
  - Usage examples
  - API reference links

- **API Documentation** (see detailed requirements in Quality Standards below):
  - REST APIs: OpenAPI spec with Swagger UI and ReDoc
  - Python libraries: Google-style docstrings with module README
  - TypeScript: JSDoc/TSDoc comments
  - All public interfaces documented

- **Architecture Documentation**:
  - System architecture diagrams (draw.io or Mermaid)
  - Data flow diagrams
  - Component relationships
  - Integration points

- **User-Facing Documentation** (when applicable):
  - Troubleshooting guides
  - Configuration options
  - Common use cases
  - FAQ section

**Documentation Directory Structure** (REQUIRED):

The `docs/` folder MUST contain comprehensive project documentation:

```
docs/
├── README.md                    # Documentation index and navigation
├── getting-started/             # Developer onboarding
│   ├── README.md               # Setup and installation guide
│   ├── quickstart.md           # Quick start tutorial
│   └── development-workflow.md # How to contribute
├── architecture/                # System design documentation
│   ├── README.md               # Architecture overview
│   ├── system-overview.md      # High-level system design
│   ├── module-interactions.md  # How modules work together
│   └── diagrams/               # Mermaid/draw.io diagrams
├── modules/                     # Detailed module documentation
│   ├── README.md               # Module index
│   ├── [module-name].md        # One file per module (links to src/[module]/README.md)
│   └── ...
├── api/                         # API documentation
│   ├── README.md               # API overview
│   └── openapi.yaml            # OpenAPI spec (when REST APIs exist)
├── user-journeys/               # User journey documentation
│   ├── README.md               # Journey guide
│   ├── JOURNEYS.md             # Journey registry
│   └── [DOMAIN]-[NNN]-*.md     # Individual journey docs
├── configuration/               # Configuration documentation
│   ├── README.md               # Configuration overview
│   └── environment-variables.md # All env vars documented
└── testing/                     # Testing documentation
    ├── README.md               # Testing overview
    ├── running-tests.md        # How to run tests
    └── writing-tests.md        # How to write tests
```

**Documentation Requirements by Type**:

- **docs/README.md** (REQUIRED): Entry point with links to all documentation sections
- **docs/getting-started/** (REQUIRED): Must exist before first feature is merged
- **docs/architecture/** (REQUIRED): Updated when new modules are added
- **docs/modules/**: One doc per module, created with each new module
- **docs/api/**: Required when REST APIs are added
- **docs/user-journeys/**: Journey docs created per user story (Principle XI)
- **docs/configuration/**: Required when configurable options exist
- **docs/testing/**: Required, explains how to test the project

**Documentation Enforcement**:
- Missing docs/ structure blocks PR merge
- Each new module MUST have corresponding docs/modules/[name].md
- Each feature MUST update docs/architecture/ if it adds new components
- CI should verify docs/ structure exists (optional linting)

**Test-to-Journey Mapping**:
- **E2E Tests MUST be tagged** with journey markers:
  ```python
  @pytest.mark.e2e
  @pytest.mark.journey("ORC-001")
  def test_create_issue_for_new_feature():
      """Test ORC-001: Create Issue for New Feature Request"""
      # Test implementation
  ```

- **Test Reports MUST show journey coverage**:
  - Which journeys are covered by tests
  - Pass/fail status per journey
  - Coverage percentage per journey
  - Uncovered journeys highlighted

- **Pytest Configuration**:
  ```toml
  [tool.pytest.ini_options]
  markers = [
      "journey(id): Mark test as covering specific user journey (e.g., ORC-001)",
      # ... other markers
  ]
  ```

**Journey Development Workflow**:
1. **During Specification**: Identify user journeys and assign IDs
2. **During Planning**: Map journeys to implementation tasks
3. **During Test Design**: Design E2E tests for each journey
4. **During Implementation**: Tag E2E tests with journey markers
5. **During Review**: Verify journey coverage in test reports
6. **Ongoing**: Update journey docs when behavior changes

**Documentation Updates**:
- Documentation MUST be updated with every feature change
- Outdated documentation is a blocking issue (same as failing tests)
- PR checklist MUST include documentation verification
- Journey coverage MUST NOT decrease between releases

**Documentation Update Frequency**:

Understanding the hierarchy:
```
Roadmap (strategic plan, quarters/months)
  └── Feature (large deliverable, 2-8 weeks, has spec.md/plan.md/tasks.md)
       └── User Story (user-facing functionality, 2-5 days, P1/P2/P3)
            └── Task (single unit of work, 15min-2 hours, T001, T002...)
```

**Update docs at FEATURE level** (primary documentation point):
- After completing feature OR after each major user story
- Update: Module README.md, user journeys, API docs, architecture diagrams
- Mark journeys as implemented in registry
- Example: After completing "GitHub Integration Core" feature

**Sometimes update docs at USER STORY level** (if story is substantial):
- When user story introduces new component or major functionality
- Update: README API reference section, related journey docs
- Example: User Story 2 (Comments) adds significant new methods

**Never update docs at TASK level** (too granular):
- Tasks are implementation details
- Code comments and docstrings are sufficient
- No separate documentation needed

**Practical Example**:
```
Feature 001: GitHub Integration Core
├── US1 (Issues): ✅ Implemented
│   └── Docs updated: README.md + ORC-001 journey
├── US2 (Comments): 📋 Planned
│   └── Will update: README.md (add comment methods) + ORC-002 journey
├── US3 (Labels): 📋 Planned
└── US4 (PRs): 📋 Planned
```

**Rationale**: User journeys provide end-to-end validation that the system works as users expect. Mapping tests to journeys ensures comprehensive coverage and makes test reports meaningful to stakeholders. Documentation prevents knowledge silos and enables new contributors to onboard quickly. For Farmer Code orchestrator, user journeys represent the 8-phase SDLC workflow that is the core value proposition. Documenting at the feature/story level (not task level) ensures docs stay current without creating update burden for every small change.

### XII. Continuous Integration and Delivery

**Rule**: All code changes MUST pass automated quality gates before merge. Releases follow semantic versioning with automated changelog generation.

**CI Pipeline Requirements**:
- **Trigger**: On every PR and push to main branch
- **Required Checks** (all must pass):
  - Linting (ruff for Python, ESLint for TypeScript)
  - Type checking (mypy --strict for Python, tsc for TypeScript)
  - Unit tests with coverage threshold
  - Integration tests (mocked external dependencies)
  - E2E tests (contract + e2e tests against real APIs)
- **Optional Checks**:
  - Performance benchmarks (for critical paths)

**E2E Test Requirements** (NON-NEGOTIABLE):
- E2E tests MUST run in CI and MUST pass
- If credentials are missing, CI MUST fail (not skip)
- Store API credentials as GitHub Secrets (e.g., GH_APP_PRIVATE_KEY)
- E2E job creates credential files from secrets with correct permissions
- No graceful degradation - missing credentials = failed build

**Security Scanning**:
- **CodeQL**: Enabled for all repositories
  - Runs on PR and push to main
  - Weekly scheduled scan (catch new vulnerability patterns)
  - Security-extended query suite
- **Dependabot**: Enabled for dependency updates
  - Automated PRs for security patches
  - Weekly check for outdated dependencies

**Branch Protection Rules**:
- Main branch protected (no direct pushes)
- Required reviews: At least 1 approval
- Required status checks: CI must pass
- Dismiss stale reviews on new commits
- Require branches to be up-to-date before merge

**Release Workflow** (manual tagging):
- **Versioning**: Semantic versioning (vMAJOR.MINOR.PATCH)
- **How to release**:
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```
- **Workflow triggers on tag push**:
  - Generates changelog from commits since last tag
  - Creates GitHub Release with changelog
  - Marks pre-release for -alpha, -beta, -rc tags

**Tagging Convention**:
```
v1.0.0        # Stable release
v1.1.0        # Feature release
v1.1.1        # Bug fix release
v2.0.0-alpha  # Pre-release (alpha)
v2.0.0-beta.1 # Pre-release (beta, iteration 1)
v2.0.0-rc.1   # Release candidate
```

**Workflow Files**:
```
.github/workflows/
├── ci.yml      # Lint, typecheck, test on PR/push
├── codeql.yml  # Security scanning
└── release.yml # Creates GitHub Release on tag push
```

**CI Best Practices**:
- ✅ Cache dependencies (uv, pnpm) for faster builds
- ✅ Run jobs in parallel where possible
- ✅ Fail fast on first error
- ✅ Use matrix builds for multi-version testing (when needed)
- ✅ Keep CI config DRY with reusable workflows
- ❌ Don't skip CI checks (even for "small" changes)
- ❌ Don't store secrets in workflow files (use GitHub Secrets)

**Rationale**: Automated CI/CD ensures consistent quality, catches issues early, and enables confident releases. CodeQL provides ongoing security analysis. Semantic versioning with automated releases reduces manual overhead and provides clear communication about changes.

## Monorepo Structure

**Repository Layout**:

```
farmcode/
├── apps/
│   ├── api/              # Backend API (Python/FastAPI)
│   │   ├── src/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── web/              # Frontend SPA (Vite + React)
│       ├── src/
│       ├── tests/
│       ├── package.json
│       └── vite.config.ts
├── packages/
│   ├── shared-types/     # Shared TypeScript types
│   ├── ui/               # shadcn/ui components (copied into project)
│   └── python-utils/     # Shared Python utilities
├── specs/                # Feature specifications
│   └── [###-feature]/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── .specify/             # SpecKit templates and memory
├── turbo.json           # Turborepo configuration
├── package.json         # Root workspace config
└── pnpm-workspace.yaml  # pnpm workspace config
```

**Workspace Rules**:
- Apps MUST NOT depend on other apps
- Apps MAY depend on packages
- Packages MUST have clear, single responsibilities
- Shared code MUST live in packages, not duplicated across apps
- Each workspace MUST have its own tests

## Development Workflow

**Workflow Stages** (from references/sdlc-workflow.md):

1. **Issue & Worktree Creation**: Branch and workspace setup
2. **Architecture & Specs**: @duc designs system architecture → Gate 1
3. **Implementation Plans**: @dede/@dali/@gus create execution plans → Gate 2
4. **Test Design**: @marie designs comprehensive tests → Gate 3
5. **Implementation (TDD)**: Agents write tests first, then code until passing
6. **Code Review**: Agents review against specs and standards
7. **Merge & Deploy**: Human approval → Gate 4 → Merge to main

**Enforcement**:
- Each phase has clear deliverables and completion criteria
- Agents communicate via GitHub issue comments for full transparency
- Labels track workflow state (status:new → status:done)
- All work isolated in Git worktrees to prevent conflicts

## Quality Standards

**Testing Requirements**:
- Contract tests for all public interfaces
- Integration tests for user journeys
- Unit tests for critical logic (when requested)
- Coverage targets defined per feature
- Tests MUST fail before implementation (enforced)
- Backend: pytest with minimum 80% coverage for new code
- Frontend: Vitest for unit tests, Playwright for E2E

**Code Review Standards**:
- Reviewers MUST verify against specifications
- Implementation MUST match approved plans
- All tests MUST pass before review completion
- Security vulnerabilities are blocking issues
- Review feedback MUST be addressed before merge
- Type errors are blocking (TypeScript strict mode, mypy strict)
- Linting violations MUST be fixed (ruff, ESLint)

**Documentation Requirements**:
- All features have spec.md, plan.md, and tasks.md
- User journeys documented per Principle XI (Documentation and User Journeys)
- **Service Interface** section in spec.md when feature exposes an API:
  - Backend services: Method signatures, inputs, outputs, error conditions
  - REST APIs: Endpoints, request/response formats
  - Summary table in spec.md, detailed contracts in contracts/ directory
- Contracts documented in contracts/ directory
- Data models documented in data-model.md
- Feature README.md in each module directory
- Quickstart.md provides end-to-end validation
- NEEDS CLARIFICATION markers require resolution before implementation
- API endpoints documented with OpenAPI/Swagger
- Components documented with JSDoc/TSDoc
- E2E tests MUST be tagged with journey markers

**Performance Standards**:
- API response time: p95 < 200ms for CRUD operations
- Frontend: Core Web Vitals passing (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- Build time: Incremental builds < 10s with Turborepo caching
- Bundle size: Frontend < 200KB initial load (gzipped)

**Error Handling Standards**:
- **Backend Error Handling**:
  - All exceptions MUST be caught at endpoint level
  - Use FastAPI exception handlers for consistent responses
  - Never expose internal errors to clients (stack traces, file paths)
  - Return appropriate HTTP status codes (400, 404, 500, etc.)
  - Include helpful error messages for users
  - Log full error details server-side (with stack trace)

- **Frontend Error Handling**:
  - API errors MUST be caught and displayed to user
  - Use toast notifications or error boundaries for display
  - Provide actionable error messages ("Try again" button)
  - Log errors to console for debugging (development only)

- **Error Response Format**:
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Invalid input provided",
      "details": ["Field 'email' is required", "Field 'age' must be positive"]
    }
  }
  ```

**Logging Standards**:
- **Log Format**: Structured JSON logs for backend
  ```json
  {
    "timestamp": "2026-01-02T10:30:00Z",
    "level": "INFO",
    "message": "User action completed",
    "context": {
      "user_id": "123",
      "action": "create_item",
      "duration_ms": 45
    }
  }
  ```

- **Log Levels**:
  - **DEBUG**: Development only (verbose internal state)
  - **INFO**: Normal operations (user actions, API calls)
  - **WARNING**: Recoverable issues (deprecated API usage, slow queries)
  - **ERROR**: Failures that need attention (failed operations, exceptions)
  - **CRITICAL**: System-level failures (database unavailable, startup failures)

- **What to Log**:
  - ✅ API requests (method, path, status, duration)
  - ✅ User actions (what happened, who did it, when)
  - ✅ Errors and exceptions (full stack trace at ERROR level)
  - ✅ Performance metrics (slow queries, long operations)
  - ✅ Authentication events (login, logout, token refresh)
  - ❌ Passwords or tokens (never log credentials)
  - ❌ Full request/response bodies (may contain sensitive data)

- **Logging Tools**:
  - Backend: Python logging module with JSON formatter
  - Local development: Console output with pretty formatting
  - Cloud deployment: CloudWatch Logs (when on AWS)
  - Log rotation: Daily rotation, keep 7 days locally

**Rationale**: Consistent error handling improves user experience and debuggability. Structured logging enables easy searching and filtering. For a small internal tool, keep logging simple but useful for troubleshooting.

**API Documentation Standards**:

All APIs and public interfaces MUST be documented for discoverability and usability.

- **REST APIs (FastAPI)** - API-First Approach:

  **Tooling**: Redocly CLI for linting, preview, and static doc generation
  ```bash
  # Install (or use npx for zero-install)
  npm install -g @redocly/cli

  # Key commands
  npx @redocly/cli lint docs/api/openapi.yaml        # Validate spec
  npx @redocly/cli preview-docs docs/api/openapi.yaml # Live preview
  npx @redocly/cli build-docs docs/api/openapi.yaml -o docs/api/index.html # Static HTML
  ```

  **Workflow** (spec is source of truth):
  1. Write `docs/api/openapi.yaml` during `/speckit.plan` phase
  2. Validate with `redocly lint` in CI (blocks merge if invalid)
  3. Generate static docs with `redocly build-docs`
  4. Implement FastAPI endpoints to match spec
  5. Runtime `/docs` and `/redoc` for development

  **File Structure**:
  ```
  docs/api/
  ├── openapi.yaml    # Source of truth (version controlled)
  ├── index.html      # Static ReDoc (generated, viewable offline)
  └── redocly.yaml    # Redocly configuration (optional)
  ```

  **CI Integration** (required):
  - Lint OpenAPI spec on every PR
  - Build static docs on merge to main
  - Deploy to GitHub Pages on release (optional)

  **Spec Requirements** - All endpoints MUST have:
  - Description (what it does)
  - Request/response schemas (Pydantic models)
  - Example values
  - Error response documentation
  - Authentication requirements noted

- **Python Libraries** (non-REST services):
  - **Google-style docstrings** for all public functions, classes, methods:
    ```python
    def create_worktree(self, request: CreateWorktreeRequest) -> OperationResult:
        """Create a new git worktree for isolated feature development.

        Args:
            request: Configuration for the new worktree including
                branch name and optional source branch.

        Returns:
            OperationResult with status and created worktree details.

        Raises:
            BranchExistsError: If branch already exists locally.
            WorktreeExistsError: If worktree path already exists.
            GitCommandError: If git command fails unexpectedly.

        Example:
            >>> service = WorktreeService("/path/to/repo")
            >>> result = service.create_worktree(
            ...     CreateWorktreeRequest(branch_name="feature-123")
            ... )
            >>> print(result.status)
            OperationStatus.SUCCESS
        """
    ```
  - **Module README.md** (`src/[module]/README.md`):
    - Purpose and scope
    - Installation/setup
    - Quick start example
    - Public API summary table
    - Error handling guidance
    - Links to contracts/ for detailed specs
  - **Contracts directory** (`specs/[feature]/contracts/`):
    - Detailed interface specifications
    - Input/output schemas
    - Error conditions
    - Integration examples

- **TypeScript/Frontend**:
  - JSDoc/TSDoc comments for exported functions and components
  - Props documented with TypeScript interfaces
  - Storybook stories for UI components (when applicable)

- **Documentation File Structure**:
  ```
  docs/
  └── api/
      ├── openapi.yaml          # Exported OpenAPI spec
      └── README.md             # API overview and quick links
  src/[module]/
  └── README.md                 # Module documentation
  specs/[feature]/
  └── contracts/                # Detailed interface specs
  ```

- **Documentation Maintenance**:
  - Update docstrings when function signatures change
  - Regenerate OpenAPI export before each release
  - Module README updated at feature completion
  - Broken documentation links are blocking issues

**Rationale**: Well-documented APIs reduce onboarding time, prevent misuse, and enable multiple clients to integrate correctly. OpenAPI with ReDoc provides interactive, searchable documentation. Google-style docstrings are IDE-friendly and generate good docs.

## Governance

**Amendment Process**:
1. Proposed changes documented with rationale
2. Impact on existing templates and workflows analyzed
3. Sync Impact Report generated showing affected artifacts
4. Version bumped according to semantic versioning rules
5. All dependent templates updated to maintain consistency

**Versioning Rules**:
- **MAJOR**: Backward incompatible governance changes (e.g., removing principle, changing gates)
- **MINOR**: New principles added or material expansions (e.g., adding new quality standard)
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

**Compliance Enforcement**:
- All PRs MUST pass constitution compliance checks
- Constitution Check section in plan.md verifies adherence
- Complexity violations require explicit justification
- Human reviewers verify constitutional compliance at each gate
- This constitution supersedes conflicting practices
- CI/CD pipelines enforce linting, type checking, and test requirements
- Pre-commit hooks prevent committing non-compliant code

**Guidance Document**: See `.specify/templates/` for implementation guidance and workflow execution details.

**Version**: 1.7.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-04
