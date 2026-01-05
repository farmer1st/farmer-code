# User Journeys

Complete list of all user journeys for FarmCode orchestrator.

## Journey Domains

| Domain | Description |
|--------|-------------|
| **ORC** | Orchestrator - AI agent workflow orchestration and SDLC management |
| **WT**  | Worktree - Git worktree and branch management for isolated development |
| **KR**  | Knowledge Router - Question routing, validation, and escalation (legacy) |
| **AH**  | Agent Hub - Central coordination layer for agent interactions (replaces KR) |
| **GH**  | GitHub - Direct GitHub integration operations (future) |
| **UI**  | User Interface - Web/TUI user interactions (future) |

## All Journeys

| Journey ID | Name | Priority | Status | Test Coverage | E2E Tests |
|------------|------|----------|--------|---------------|-----------|
| [ORC-001](./ORC-001-create-issue.md) | Create Issue for New Feature Request | P1 | ✅ Implemented | ✅ 100% | 1/1 passing |
| [ORC-002](./ORC-002-agent-feedback.md) | Agent Provides Feedback via Comment | P2 | 📋 Planned | ⏳ 0% | 0/0 tests |
| [ORC-003](./ORC-003-workflow-progression.md) | Progress Issue Through Workflow Phases | P2 | 📋 Planned | ⏳ 0% | 0/0 tests |
| [ORC-004](./ORC-004-link-pull-request.md) | Link Pull Request to Feature Issue | P3 | 📋 Planned | ⏳ 0% | 0/0 tests |
| [ORC-005](./ORC-005-full-sdlc-workflow.md) | Complete 8-Phase SDLC Workflow | P1 | ✅ Implemented | ✅ 100% | 1/1 passing |
| [WT-001](./WT-001-create-worktree.md) | Create Worktree for Feature Development | P1 | ✅ Implemented | ✅ 100% | 1/1 passing |
| [WT-002](./WT-002-init-plans.md) | Initialize Plans Folder Structure | P1 | ✅ Implemented | ✅ 100% | 1/1 passing |
| [WT-003](./WT-003-commit-push.md) | Commit and Push Feature Changes | P2 | ✅ Implemented | ✅ 100% | 1/1 passing |
| [WT-004](./WT-004-cleanup-worktree.md) | Cleanup Worktree After Feature Completion | P2 | ✅ Implemented | ✅ 100% | 1/1 passing |
| [KR-001](./KR-001-route-question.md) | Route Question to Knowledge Agent | P1 | ✅ Implemented | ✅ 100% | 2/2 passing |
| [KR-002](./KR-002-validate-confidence.md) | Validate Answer Confidence | P1 | ✅ Implemented | ✅ 100% | 3/3 passing |
| [KR-003](./KR-003-escalate-human.md) | Escalate Low-Confidence to Human | P1 | ✅ Implemented | ✅ 100% | 5/5 passing |
| [KR-004](./KR-004-log-qa.md) | Log Q&A Exchange for Retrospectives | P1 | ✅ Implemented | ✅ 100% | 4/4 passing |
| [AH-001](./AH-001-route-question.md) | Route Question to Expert Agent | P1 | ✅ Implemented | ✅ 100% | 3/3 passing |
| [AH-002](./AH-002-session-management.md) | Maintain Conversation Sessions | P1 | ✅ Implemented | ✅ 100% | 6/6 passing |
| [AH-003](./AH-003-confidence-escalation.md) | Validate Confidence and Escalate | P2 | ✅ Implemented | ✅ 100% | 5/5 passing |
| [AH-004](./AH-004-pending-escalation.md) | Track Pending Escalations | P2 | ✅ Implemented | ✅ 100% | 6/6 passing |
| [AH-005](./AH-005-audit-logging.md) | Audit Trail Logging | P3 | ✅ Implemented | ✅ 100% | 5/5 passing |
| KR-005 | Dispatch Execution Tasks to Specialists | P2 | 📋 Planned | ⏳ 0% | 0/0 tests |
| KR-006 | Configure Routing Rules | P2 | 📋 Planned | ⏳ 0% | 0/0 tests |
| KR-007 | Generate Retrospective Report | P2 | 📋 Planned | ⏳ 0% | 0/0 tests |
| KR-008 | Handle Agent Unavailability | P3 | 📋 Planned | ⏳ 0% | 0/0 tests |

## Status Legend

- ✅ **Implemented**: Fully implemented with passing tests
- 🚧 **In Progress**: Currently being developed
- 📋 **Planned**: Designed but not yet implemented
- ⏸️ **Paused**: Development temporarily halted
- ❌ **Deprecated**: No longer supported

## Coverage by Priority

### P1 Journeys (Critical - Required for MVP)
| ID | Name | Status | Coverage |
|----|------|--------|----------|
| ORC-001 | Create Issue for New Feature Request | ✅ Implemented | 100% |
| ORC-005 | Complete 8-Phase SDLC Workflow | ✅ Implemented | 100% (partial) |
| WT-001 | Create Worktree for Feature Development | ✅ Implemented | 100% |
| WT-002 | Initialize Plans Folder Structure | ✅ Implemented | 100% |
| KR-001 | Route Question to Knowledge Agent | ✅ Implemented | 100% |
| KR-002 | Validate Answer Confidence | ✅ Implemented | 100% |
| KR-003 | Escalate Low-Confidence to Human | ✅ Implemented | 100% |
| KR-004 | Log Q&A Exchange for Retrospectives | ✅ Implemented | 100% |
| AH-001 | Route Question to Expert Agent | ✅ Implemented | 100% |
| AH-002 | Maintain Conversation Sessions | ✅ Implemented | 100% |

**P1 Coverage**: 10/10 implemented (100%)

### P2 Journeys (Important - Post-MVP)
| ID | Name | Status | Coverage |
|----|------|--------|----------|
| ORC-002 | Agent Provides Feedback via Comment | 📋 Planned | 0% |
| ORC-003 | Progress Issue Through Workflow Phases | 📋 Planned | 0% |
| WT-003 | Commit and Push Feature Changes | ✅ Implemented | 100% |
| WT-004 | Cleanup Worktree After Feature Completion | ✅ Implemented | 100% |
| AH-003 | Validate Confidence and Escalate | ✅ Implemented | 100% |
| AH-004 | Track Pending Escalations | ✅ Implemented | 100% |
| KR-005 | Dispatch Execution Tasks to Specialists | 📋 Planned | 0% |
| KR-006 | Configure Routing Rules | 📋 Planned | 0% |
| KR-007 | Generate Retrospective Report | 📋 Planned | 0% |

**P2 Coverage**: 4/9 implemented (44%)

### P3 Journeys (Nice to Have)
| ID | Name | Status | Coverage |
|----|------|--------|----------|
| ORC-004 | Link Pull Request to Feature Issue | 📋 Planned | 0% |
| KR-008 | Handle Agent Unavailability | 📋 Planned | 0% |

**P3 Coverage**: 1/2 implemented (50%)

## Test Coverage Visualization

```
Overall Journey Coverage:
ORC-001: ████████████████████ 100% (1/1 E2E tests passing)
ORC-002: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
ORC-003: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
ORC-004: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
ORC-005: ████████████████████ 100% (1/1 E2E tests passing)
WT-001:  ████████████████████ 100% (1/1 E2E tests passing)
WT-002:  ████████████████████ 100% (1/1 E2E tests passing)
WT-003:  ████████████████████ 100% (1/1 E2E tests passing)
WT-004:  ████████████████████ 100% (1/1 E2E tests passing)
KR-001:  ████████████████████ 100% (2/2 E2E tests passing)
KR-002:  ████████████████████ 100% (3/3 E2E tests passing)
KR-003:  ████████████████████ 100% (5/5 E2E tests passing)
KR-004:  ████████████████████ 100% (4/4 E2E tests passing)
AH-001:  ████████████████████ 100% (3/3 E2E tests passing)
AH-002:  ████████████████████ 100% (6/6 E2E tests passing)
AH-003:  ████████████████████ 100% (5/5 E2E tests passing)
AH-004:  ████████████████████ 100% (6/6 E2E tests passing)
AH-005:  ████████████████████ 100% (5/5 E2E tests passing)
KR-005:  ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
KR-006:  ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
KR-007:  ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
KR-008:  ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)

Total: 15/22 journeys implemented (68%)
P1 Journeys: 10/10 implemented (100%) ✅
P2 Journeys: 4/9 implemented (44%)
P3 Journeys: 1/2 implemented (50%)
```

## Journeys by Feature

### Feature 001: GitHub Integration Core

| User Story | Journeys | Status |
|------------|----------|--------|
| US1: Create and Track Issues | ORC-001 | ✅ Implemented |
| US2: Capture Agent Feedback | ORC-002 | 📋 Planned |
| US3: Manage Workflow State | ORC-003 | 📋 Planned |
| US4: Link PRs to Issues | ORC-004 | 📋 Planned |
| All Stories Combined | ORC-005 | ✅ Partial |

### Feature 002: Git Worktree Manager

| User Story | Journeys | Status |
|------------|----------|--------|
| US1: Create Worktree | WT-001 | ✅ Implemented |
| US2: Manage Plans Folder | WT-002 | ✅ Implemented |
| US3: Commit and Push Changes | WT-003 | ✅ Implemented |
| US4: Cleanup Worktree | WT-004 | ✅ Implemented |

### Feature 003: Orchestrator State Machine

| User Story | Journeys | Status |
|------------|----------|--------|
| US1-3: State Machine Phases | ORC-005 | ✅ Implemented |

### Feature 004: Knowledge Router

| User Story | Journeys | Status |
|------------|----------|--------|
| US1: Route Questions | KR-001 | ✅ Implemented |
| US2: Validate Answers | KR-002 | ✅ Implemented |
| US3: Escalate to Human | KR-003 | ✅ Implemented |
| US4: Log Q&A | KR-004 | ✅ Implemented |
| US5: Dispatch Execution | KR-005 | 📋 Planned |
| US6: Configure Routing | KR-006 | 📋 Planned |
| US7: Retrospective Report | KR-007 | 📋 Planned |
| US8: Handle Unavailability | KR-008 | 📋 Planned |

### Feature 005: Agent Hub Refactor

| User Story | Journeys | Status |
|------------|----------|--------|
| US1: Route Questions to Experts | AH-001 | ✅ Implemented |
| US2: Maintain Conversation Sessions | AH-002 | ✅ Implemented |
| US3: Validate Confidence and Escalate | AH-003 | ✅ Implemented |
| US4: Track Pending Escalations | AH-004 | ✅ Implemented |
| US5: Audit Trail Logging | AH-005 | ✅ Implemented |

### Future Features

| Feature | Journeys | Status |
|---------|----------|--------|
| Feature 006: Baron PM Agent | TBD | 🔮 Not yet planned |
| Feature 007: TUI Interface | UI-001 to UI-010 | 🔮 Not yet planned |

## Running Journey Tests

```bash
# Run all journey-tagged tests
pytest -m journey -v

# Run specific journey
pytest -m "journey('ORC-001')" -v

# Generate journey coverage report (automatically shown at end of test run)
pytest -m journey

# See which tests are tagged with journeys
pytest --co -m journey
```

## Journey Coverage Goals

**Release Criteria:**
- **v1.0 (MVP)**: All P1 journeys 100% tested ✅ **ACHIEVED**
- **v1.1**: 80%+ of P2 journeys tested
- **v1.2**: All P2 journeys 100% tested
- **v2.0**: All P3 journeys tested

**Current Status**: v1.0 MVP ready (P1 journeys complete)

## Related Documentation

- [Journey Documentation Guide](./README.md) - How to write and maintain journey docs
- [Constitution - Principle XI](../../.specify/memory/constitution.md#xi-documentation-and-user-journeys) - Journey standards
- [E2E Test Guide](../testing/e2e-tests.md) - How to write journey tests (future)
- [SDLC Workflow Reference](../../references/sdlc-workflow.md) - The 8-phase workflow

## Last Updated

**Date**: 2026-01-05
**By**: Agent Hub Refactor (Feature 005) - User Stories 1-5 Complete
**Next Review**: After implementing Feature 005 MCP Server (Phase 8)
