# User Journey Registry

This directory contains all user journey documentation for FarmCode.

## Journey Domains

| Domain | Description |
|--------|-------------|
| **ORC** | Orchestrator - AI agent workflow orchestration and SDLC management |
| **GH**  | GitHub - Direct GitHub integration operations (future) |
| **UI**  | User Interface - Web/TUI user interactions (future) |

## Active Journeys

| Journey ID | Name | Priority | Status | Test Coverage | Last Updated |
|------------|------|----------|--------|---------------|--------------|
| [ORC-001](./ORC-001-create-issue.md) | Create Issue for New Feature Request | P1 | ✅ Implemented | ✅ 100% (1/1 tests) | 2026-01-02 |
| [ORC-002](./ORC-002-agent-feedback.md) | Agent Provides Feedback via Comment | P2 | 📋 Planned | ⏳ 0% (0/0 tests) | 2026-01-02 |
| [ORC-003](./ORC-003-workflow-progression.md) | Progress Issue Through Workflow Phases | P2 | 📋 Planned | ⏳ 0% (0 tests) | 2026-01-02 |
| [ORC-004](./ORC-004-link-pull-request.md) | Link Pull Request to Feature Issue | P3 | 📋 Planned | ⏳ 0% (0 tests) | 2026-01-02 |
| [ORC-005](./ORC-005-full-sdlc-workflow.md) | Complete 8-Phase SDLC Workflow | P1 | ✅ Implemented | ✅ 100% (1/1 tests) | 2026-01-02 |

## Status Legend

- ✅ **Implemented**: Fully implemented and tested
- 🚧 **In Progress**: Currently being developed
- 📋 **Planned**: Designed but not yet implemented
- ⏸️ **Paused**: Development temporarily halted
- ❌ **Deprecated**: No longer supported

## Test Coverage by Journey

```
ORC-001: ████████████████████ 100% (1/1 E2E tests passing)
ORC-002: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
ORC-003: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
ORC-004: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
ORC-005: ████████████████████ 100% (1/1 E2E tests passing)
```

## Journey Development Workflow

1. **Specification Phase**: Identify journeys and assign unique IDs (format: `DOMAIN-NNN`)
2. **Planning Phase**: Map journeys to user stories and implementation tasks
3. **Test Design Phase**: Design E2E tests for each journey step
4. **Implementation Phase**: Implement features and tag E2E tests with `@pytest.mark.journey("DOMAIN-NNN")`
5. **Review Phase**: Verify journey coverage and test status
6. **Maintenance**: Update journey docs when behavior changes

## Adding New Journeys

1. **Assign ID**: Get next sequential number for domain (e.g., `ORC-006`)
2. **Create file**: `DOMAIN-NNN-[descriptive-name].md`
3. **Document journey**: Follow template in constitution (Principle XI)
4. **Update registry**: Add row to table above
5. **Tag tests**: Add `@pytest.mark.journey("DOMAIN-NNN")` to E2E tests
6. **Verify coverage**: Run `pytest --co -m journey` to see journey-tagged tests

## Running Journey Tests

```bash
# Run all journey tests
pytest -m journey -v

# Run tests for specific journey
pytest -m "journey('ORC-001')" -v

# Generate journey coverage report
pytest -m journey --tb=short --junit-xml=journey-report.xml
```

## Journey Coverage Goals

- **P1 Journeys**: 100% E2E test coverage required before release
- **P2 Journeys**: 80% E2E test coverage recommended
- **P3 Journeys**: 50% E2E test coverage minimum

## Related Documentation

- [Constitution - Principle XI](../../.specify/memory/constitution.md#xi-documentation-and-user-journeys)
- [E2E Test Guide](../testing/e2e-tests.md) (future)
- [SDLC Workflow Reference](../../references/sdlc-workflow.md)
