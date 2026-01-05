# Development Workflow

How to contribute to Farmer Code following our development standards.

## Workflow Overview

Farmer Code uses a specification-driven, test-first development workflow:

```
1. Create Spec → 2. Plan → 3. Tasks → 4. Implement (TDD) → 5. Review → 6. Merge
```

## Prerequisites

Before contributing, understand:

1. **[Constitution](../../.specify/memory/constitution.md)** - Development principles
2. **[Architecture](../architecture/README.md)** - System design
3. **[User Journeys](../user-journeys/JOURNEYS.md)** - Feature workflows

## Step 1: Create Feature Specification

Use SpecKit to create a feature specification:

```bash
# Run the specify command
/speckit.specify "Add OAuth2 authentication"
```

This creates:
- `specs/###-feature-name/spec.md` - Feature specification
- User stories with priorities (P1, P2, P3)
- Acceptance criteria

## Step 2: Plan Implementation

Generate an implementation plan:

```bash
/speckit.plan
```

This creates:
- `specs/###-feature-name/plan.md` - Implementation plan
- `specs/###-feature-name/data-model.md` - Data models
- `specs/###-feature-name/contracts/` - API contracts
- `specs/###-feature-name/research.md` - Research findings

**Gate 1**: Plan requires human approval before proceeding.

## Step 3: Generate Tasks

Create an actionable task list:

```bash
/speckit.tasks
```

This creates:
- `specs/###-feature-name/tasks.md` - Task list organized by user story

## Step 4: Implement with TDD

Implement following Test-First Development (NON-NEGOTIABLE):

### TDD Cycle

1. **Write Test First** (Red)
   ```python
   def test_question_routes_to_architect():
       hub = AgentHub(config)
       response = hub.ask_expert(topic="architecture", question="...")
       assert response.status.value == "resolved"
   ```

2. **Run Test - Should Fail**
   ```bash
   uv run pytest tests/unit/agent_hub/test_hub.py -v
   # FAILED - ask_expert not implemented
   ```

3. **Implement Minimal Code** (Green)
   ```python
   def ask_expert(self, topic: str, question: str, ...) -> HubResponse:
       agent = self.config.get_agent_for_topic(topic)
       return self._dispatch_to_agent(agent, question)
   ```

4. **Run Test - Should Pass**
   ```bash
   uv run pytest tests/unit/agent_hub/test_hub.py -v
   # PASSED
   ```

5. **Refactor** (Clean)
   - Improve code quality
   - Maintain passing tests

### Commit After Each Task

```bash
git add .
git commit -m "feat(agent-hub): implement question routing"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Test changes
- `refactor:` - Code restructuring

## Step 5: Update Documentation

After implementing, update docs:

1. **Module README**: `src/[module]/README.md`
2. **Module Doc**: `docs/modules/[module-name].md`
3. **User Journeys**: `docs/user-journeys/[DOMAIN]-[NNN]-*.md`
4. **Journey Index**: `docs/user-journeys/JOURNEYS.md`
5. **Architecture** (if new component): `docs/architecture/`

## Step 6: Create Pull Request

```bash
# Push branch
git push -u origin 123-feature-name

# Create PR
gh pr create --title "feat: Add OAuth2 authentication" --body "..."
```

PR requirements:
- All tests pass
- Linting passes (`uv run ruff check .`)
- Type checking passes (`uv run mypy src/`)
- Documentation updated
- E2E tests tagged with journey markers

**Gate 4**: PR requires human approval before merge.

## Quality Checks

Before submitting PR, verify:

```bash
# Run all quality checks
uv run ruff check .           # Linting
uv run mypy src/              # Type checking
uv run pytest                 # All tests
uv run pytest -m journey      # Journey tests

# Check coverage
uv run pytest --cov=src --cov-report=term-missing
```

## Branch Naming

Follow this pattern:

```
{issue_number}-{feature-name}
```

Examples:
- `123-add-oauth2-auth`
- `456-fix-routing-bug`
- `789-refactor-state-machine`

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Examples:
```
feat(agent-hub): implement expert routing

- Add AgentHub class with ask_expert method
- Add AgentRouter for Claude CLI spawning
- Add ConfidenceValidator for answer validation

Closes #123
```

## Test Organization

```
tests/
├── unit/                    # Pure unit tests (no external deps)
│   └── [module]/           # Tests per module
├── integration/             # Integration tests (mocked externals)
│   └── [module]/
├── contract/                # Contract/schema tests
│   └── [module]/
└── e2e/                     # End-to-end tests (real externals)
    └── [module]/
```

### Journey Markers

E2E tests MUST have journey markers:

```python
@pytest.mark.e2e
@pytest.mark.journey("AH-001")
def test_route_question_to_architect_e2e():
    """Test AH-001: Route Question to Expert Agent."""
    ...
```

## Common Pitfalls

### Don't Skip Tests

```python
# WRONG - implementing before test
def route_question(self, question):
    return self.config.get_agent(question.topic)

# RIGHT - test first
def test_route_question():
    ...  # Write this first
```

### Don't Over-Engineer

```python
# WRONG - abstract factory for simple case
class AgentFactory(ABC):
    @abstractmethod
    def create_agent(self): ...

# RIGHT - simple implementation
def get_agent(topic: str) -> Agent:
    return self.agents.get(topic)
```

### Don't Forget Documentation

```bash
# Before PR, check:
cat src/[module]/README.md         # Module docs exist
cat docs/modules/[module-name].md  # Extended docs exist
cat docs/user-journeys/[DOMAIN]-*.md  # Journey docs exist
```

## Getting Help

- Ask questions via GitHub issues
- Review existing specs in `specs/`
- Check user journeys for workflow understanding
- Consult the Constitution for principles
