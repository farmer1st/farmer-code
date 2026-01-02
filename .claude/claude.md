# Farm Code Project Instructions

## Constitution

**CRITICAL**: This project has a constitution at `.specify/memory/constitution.md` (v1.3.0) that defines **10 core principles** and quality standards. You MUST follow these principles in ALL code you write.

### Non-Negotiable Principles

1. **Test-First Development (NON-NEGOTIABLE)**: Write tests BEFORE implementation. Red-Green-Refactor cycle strictly enforced.

2. **Thin Client Architecture (NON-NEGOTIABLE)**: ALL business logic in backend. Frontend is presentation-only. No intelligence in UI.

3. **Security-First Development**: Use .env for secrets, validate inputs with Pydantic, prevent SQL injection via SQLAlchemy ORM.

### Key Standards

**Technology Stack**:
- Backend: Python 3.11+, FastAPI, SQLAlchemy, Pydantic, uv, ruff
- Frontend: TypeScript, Vite, React 18+, shadcn/ui, Tailwind CSS
- Database: SQLite (local) → PostgreSQL (cloud)
- Migrations: Alembic

**Error Handling**:
- Use FastAPI exception handlers
- Return consistent error format: `{"error": {"code": "...", "message": "...", "details": [...]}}`
- Structured JSON logging

**Database**:
- All tables have: `id`, `created_at`, `updated_at`, `deleted_at`
- Use Alembic migrations for schema changes
- Transactions for multi-step operations

**API Design**:
- Backend APIs MUST be client-agnostic (support web, TUI, CLI, mobile)
- RESTful endpoints with OpenAPI documentation
- Backend handles ALL business logic, filtering, sorting, pagination

**Deployment**:
- Local-first (primary), cloud-ready (future option)
- Containers via Docker
- No cloud-specific dependencies

### Before Writing Code

1. **Read the full constitution**: `.specify/memory/constitution.md`
2. **Check Constitution Check section** in relevant plan.md
3. **Verify compliance** with all 10 principles
4. **Ask if unsure** - don't guess!

### SpecKit Workflow

When working on features, follow this workflow:
1. `/speckit.specify` - Create specification
2. `/speckit.plan` - Generate implementation plan
3. `/speckit.tasks` - Generate task list
4. `/speckit.implement` - Execute tasks (TDD enforced)

Each command automatically references the constitution.

### Quick Reference

- Constitution: `.specify/memory/constitution.md`
- Templates: `.specify/templates/`
- Commands: `.claude/commands/speckit.*.md`

**Remember**: The constitution supersedes all other practices. When in doubt, check the constitution first.
