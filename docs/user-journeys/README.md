# User Journey Documentation Guide

This directory contains all user journey documentation for FarmCode orchestrator.

**📊 [View all journeys →](./JOURNEYS.md)** - Complete list with status and test coverage

## What are User Journeys?

User journeys document end-to-end workflows from a user's perspective. Each journey:
- Has a unique ID (e.g., `ORC-001`)
- Maps to one or more E2E tests
- Tracks implementation status and test coverage
- Links to related journeys and features

## Journey Structure

Each journey is documented in a separate markdown file following this structure:

```markdown
# [DOMAIN-NNN]: [Journey Name]

**Actor**: [Who performs this journey]
**Goal**: [What they want to accomplish]
**Preconditions**: [What must be true before starting]
**Priority**: [P1/P2/P3]

## Steps:
1-N. [Detailed steps with expected outcomes]

## Success Criteria:
- [Measurable outcomes]

## E2E Test Coverage:
- Test file, markers, coverage status

## Related Journeys:
- Links to other journeys
```

## Journey Domains

User journeys are organized by domain using 2-4 letter prefixes:

| Domain | Description | Example IDs |
|--------|-------------|-------------|
| **ORC** | Orchestrator - AI agent workflow orchestration | ORC-001, ORC-002 |
| **GH**  | GitHub - Direct GitHub integration operations | GH-001, GH-002 |
| **UI**  | User Interface - Web/TUI user interactions | UI-001, UI-002 |

## Journey ID Format

Journey IDs follow the pattern: `[DOMAIN]-[NNN]`

- **DOMAIN**: 2-4 letter domain code (uppercase)
- **NNN**: 3-digit sequential number (001, 002, 003, ...)
- **Examples**: `ORC-001`, `GH-023`, `UI-007`

## Journey Development Workflow

1. **During Specification**: Identify journeys and assign unique IDs
2. **During Planning**: Map journeys to user stories and tasks
3. **During Test Design**: Design E2E tests for each journey
4. **During Implementation**: Tag E2E tests with `@pytest.mark.journey("DOMAIN-NNN")`
5. **During Review**: Verify journey coverage in test reports
6. **Ongoing**: Update journey docs when behavior changes

## Adding a New Journey

### 1. Assign Journey ID
Get next sequential number for the domain:
```bash
# Check existing journeys in domain
ls docs/user-journeys/ORC-*.md
# Assign next number (e.g., ORC-006)
```

### 2. Create Journey File
Create `DOMAIN-NNN-[descriptive-name].md` following the template structure above.

### 3. Update Journey List
Add your journey to [JOURNEYS.md](./JOURNEYS.md) table.

### 4. Implement and Tag Tests
When implementing E2E tests, add the journey marker:
```python
@pytest.mark.e2e
@pytest.mark.journey("ORC-006")
def test_your_journey():
    """Test ORC-006: Your Journey Name"""
    # Test implementation
```

### 5. Verify Coverage
Run journey-tagged tests to verify:
```bash
# See all journey-tagged tests
pytest --co -m journey

# Run your journey's tests
pytest -m "journey('ORC-006')" -v
```

## Running Journey Tests

```bash
# Run all journey-tagged tests
pytest -m journey -v

# Run specific journey
pytest -m "journey('ORC-001')" -v

# Generate journey coverage report (shown automatically at end)
pytest -m journey

# List all journey-tagged tests without running
pytest --co -m journey
```

## Journey Coverage Report

When you run journey-tagged tests, you'll see a coverage summary:

```
=================== User Journey Test Coverage ===================

ORC-001: ✅ PASSED (1/1 tests passing, 100% coverage)
ORC-005: ✅ PASSED (1/1 tests passing, 100% coverage)

Journey Coverage: 2/2 journeys passing
```

This helps track which user journeys are fully tested and working.

## Journey Coverage Goals

- **P1 Journeys**: 100% E2E test coverage required before v1.0 release
- **P2 Journeys**: 80% E2E test coverage recommended for v1.1
- **P3 Journeys**: 50% E2E test coverage minimum for v2.0

## Files in This Directory

- **[JOURNEYS.md](./JOURNEYS.md)** - Complete list of all journeys with status
- **README.md** - This file (journey documentation guide)
- **ORC-001-create-issue.md** - Create issue for new feature request
- **ORC-002-agent-feedback.md** - Agent provides feedback via comment
- **ORC-003-workflow-progression.md** - Progress issue through workflow phases
- **ORC-004-link-pull-request.md** - Link pull request to feature issue
- **ORC-005-full-sdlc-workflow.md** - Complete 8-phase SDLC workflow
- **WT-001-create-worktree.md** - Create worktree for feature development
- **WT-002-init-plans.md** - Initialize plans folder structure
- **WT-003-commit-push.md** - Commit and push feature changes
- **WT-004-cleanup-worktree.md** - Cleanup worktree after feature completion

## Related Documentation

- **[JOURNEYS.md](./JOURNEYS.md)** - View all journeys with status and coverage
- **[Constitution - Principle XI](../../.specify/memory/constitution.md#xi-documentation-and-user-journeys)** - Journey standards
- **[SDLC Workflow Reference](../../references/sdlc-workflow.md)** - The 8-phase workflow
- **E2E Test Guide** (future) - How to write journey tests
