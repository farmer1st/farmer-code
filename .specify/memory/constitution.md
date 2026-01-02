<!--
Sync Impact Report:
- Version change: 1.1.0 → 1.1.1
- Modified principles: Principle VIII (Technology Stack Standards) - refined frontend UI tooling
- Added sections: None
- Removed sections: None
- Templates requiring updates:
  ✅ plan-template.md - No changes needed (inherits from constitution)
  ✅ spec-template.md - No changes needed
  ✅ tasks-template.md - No changes needed
  ✅ All command files reviewed - no updates needed
- Follow-up TODOs: None
- Rationale for PATCH bump: Clarification of frontend UI component strategy (shadcn/ui)
Previous changes:
- 1.0.0 → 1.1.0: Added Principle VIII (Technology Stack Standards) and Monorepo Structure
- Initial: 1.0.0 ratified with 7 core principles
-->

# Farm Code Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

**Rule**: Tests MUST be written before implementation code. No exceptions.

**Implementation**:
- Tests are designed and approved BEFORE any code is written
- Tests MUST fail initially (red phase)
- Implementation proceeds only to make tests pass (green phase)
- Refactoring occurs only after tests pass
- Red-Green-Refactor cycle is strictly enforced

**Rationale**: Test-first development ensures code meets requirements, reduces defects, provides living documentation, and enables confident refactoring. This is the foundation of quality in Farm Code.

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

**Rule**: All artifacts MUST be versioned using semantic versioning.

**Implementation**:
- Constitution: MAJOR.MINOR.PATCH (backward compatibility semantics)
- Specifications: Linked to feature branches and issue numbers
- All changes tracked through Git with meaningful commit messages
- Breaking changes require MAJOR version bump and migration plan

**Rationale**: Versioning enables traceability, rollback capability, change impact analysis, and coordination across distributed teams.

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

**Frontend Stack** (TypeScript):
- **Language**: TypeScript 5.0+
- **Framework**: Next.js 14+ (App Router) for full-stack React applications
- **UI Components**: shadcn/ui (Radix UI primitives + Tailwind CSS)
- **Styling**: Tailwind CSS for utility-first styling
- **Linting**: ESLint + Prettier for code quality
- **Testing**: Vitest for unit/integration tests, Playwright for E2E
- **State Management**: React Context/Zustand (avoid Redux unless justified)

**Development Tools**:
- **Containerization**: Docker for local development and deployment
- **CI/CD**: GitHub Actions with Turborepo remote caching
- **Code Quality**: Pre-commit hooks enforcing linting and tests
- **Documentation**: Markdown for all documentation

**Rationale**: Standardized tooling reduces cognitive load, enables code sharing, simplifies CI/CD, and ensures consistent developer experience. The selected tools are industry-standard, well-maintained, and optimized for monorepo development.

## Monorepo Structure

**Repository Layout**:

```
farmcode/
├── apps/
│   ├── api/              # Backend API (Python/FastAPI)
│   │   ├── src/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── web/              # Frontend application (Next.js)
│       ├── src/
│       ├── tests/
│       └── package.json
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
- Contracts documented in contracts/ directory
- Data models documented in data-model.md
- Quickstart.md provides end-to-end validation
- NEEDS CLARIFICATION markers require resolution before implementation
- API endpoints documented with OpenAPI/Swagger
- Components documented with JSDoc/TSDoc

**Performance Standards**:
- API response time: p95 < 200ms for CRUD operations
- Frontend: Core Web Vitals passing (LCP < 2.5s, FID < 100ms, CLS < 0.1)
- Build time: Incremental builds < 10s with Turborepo caching
- Bundle size: Frontend < 200KB initial load (gzipped)

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

**Version**: 1.1.1 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-01-02
