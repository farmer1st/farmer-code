# User Journeys

Complete list of all user journeys for Farmer Code orchestrator.

## Journey Domains

| Domain | Description |
|--------|-------------|
| **ORC** | Orchestrator - AI agent workflow orchestration and SDLC management |
| **WT**  | Worktree - Git worktree and branch management for isolated development |
| **AH**  | Agent Hub - Central coordination layer for agent interactions (legacy) |
| **BRN** | Baron PM Agent - Product management agent for speckit workflows |
| **SVC** | Services Architecture - Microservices-based agent orchestration |
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
| [AH-001](./AH-001-route-question.md) | Route Question to Expert Agent | P1 | ✅ Implemented | ✅ 100% | 3/3 passing |
| [AH-002](./AH-002-session-management.md) | Maintain Conversation Sessions | P1 | ✅ Implemented | ✅ 100% | 6/6 passing |
| [AH-003](./AH-003-confidence-escalation.md) | Validate Confidence and Escalate | P2 | ✅ Implemented | ✅ 100% | 5/5 passing |
| [AH-004](./AH-004-pending-escalation.md) | Track Pending Escalations | P2 | ✅ Implemented | ✅ 100% | 6/6 passing |
| [AH-005](./AH-005-audit-logging.md) | Audit Trail Logging | P3 | ✅ Implemented | ✅ 100% | 5/5 passing |
| [BRN-001](./BRN-001-create-specification.md) | Create Feature Specification | P1 | ✅ Implemented | ✅ 100% | 6/6 passing |
| [BRN-002](./BRN-002-generate-plan.md) | Generate Implementation Plan | P1 | ✅ Implemented | ✅ 100% | 7/7 passing |
| [BRN-003](./BRN-003-generate-tasks.md) | Generate Task List | P1 | ✅ Implemented | ✅ 100% | 7/7 passing |
| BRN-004 | Handle Pending Escalations | P2 | 📋 Planned | ⏳ 0% | 0/0 tests |
| BRN-005 | Expert Consultation Flow | P2 | 📋 Planned | ⏳ 0% | 0/0 tests |
| BRN-006 | Constitution Compliance | P2 | 📋 Planned | ⏳ 0% | 0/0 tests |
| SVC-001 | Orchestrator Workflow Execution | P1 | ✅ Implemented | ✅ 100% | 3/3 passing |
| SVC-002 | Expert Agent Consultation | P1 | ✅ Implemented | ✅ 100% | 5/5 passing |
| SVC-003 | Human Review Escalation | P1 | ✅ Implemented | ✅ 100% | 4/4 passing |
| SVC-004 | Multi-Turn Session | P2 | ✅ Implemented | ✅ 100% | 6/6 passing |
| SVC-005 | Stateless Agent Invocation | P1 | ✅ Implemented | ✅ 100% | 8/8 passing |
| SVC-006 | Local Development Setup | P2 | ✅ Implemented | ✅ 100% | 2/2 passing |
| SVC-007 | Audit Log Query | P3 | ✅ Implemented | ✅ 100% | 5/5 passing |

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
| AH-001 | Route Question to Expert Agent | ✅ Implemented | 100% |
| AH-002 | Maintain Conversation Sessions | ✅ Implemented | 100% |
| BRN-001 | Create Feature Specification | ✅ Implemented | 100% |
| BRN-002 | Generate Implementation Plan | ✅ Implemented | 100% |
| BRN-003 | Generate Task List | ✅ Implemented | 100% |
| SVC-001 | Orchestrator Workflow Execution | ✅ Implemented | 100% |
| SVC-002 | Expert Agent Consultation | ✅ Implemented | 100% |
| SVC-003 | Human Review Escalation | ✅ Implemented | 100% |
| SVC-005 | Stateless Agent Invocation | ✅ Implemented | 100% |

**P1 Coverage**: 13/13 implemented (100%)

### P2 Journeys (Important - Post-MVP)
| ID | Name | Status | Coverage |
|----|------|--------|----------|
| ORC-002 | Agent Provides Feedback via Comment | 📋 Planned | 0% |
| ORC-003 | Progress Issue Through Workflow Phases | 📋 Planned | 0% |
| WT-003 | Commit and Push Feature Changes | ✅ Implemented | 100% |
| WT-004 | Cleanup Worktree After Feature Completion | ✅ Implemented | 100% |
| AH-003 | Validate Confidence and Escalate | ✅ Implemented | 100% |
| AH-004 | Track Pending Escalations | ✅ Implemented | 100% |
| BRN-004 | Handle Pending Escalations | 📋 Planned | 0% |
| BRN-005 | Expert Consultation Flow | 📋 Planned | 0% |
| BRN-006 | Constitution Compliance | 📋 Planned | 0% |
| SVC-004 | Multi-Turn Session | ✅ Implemented | 100% |
| SVC-006 | Local Development Setup | ✅ Implemented | 100% |

**P2 Coverage**: 6/11 implemented (55%)

### P3 Journeys (Nice to Have)
| ID | Name | Status | Coverage |
|----|------|--------|----------|
| ORC-004 | Link Pull Request to Feature Issue | 📋 Planned | 0% |
| AH-005 | Audit Trail Logging | ✅ Implemented | 100% |
| SVC-007 | Audit Log Query | ✅ Implemented | 100% |

**P3 Coverage**: 2/3 implemented (67%)

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
AH-001:  ████████████████████ 100% (3/3 E2E tests passing)
AH-002:  ████████████████████ 100% (6/6 E2E tests passing)
AH-003:  ████████████████████ 100% (5/5 E2E tests passing)
AH-004:  ████████████████████ 100% (6/6 E2E tests passing)
AH-005:  ████████████████████ 100% (5/5 E2E tests passing)
BRN-001: ████████████████████ 100% (6/6 E2E tests passing)
BRN-002: ████████████████████ 100% (7/7 E2E tests passing)
BRN-003: ████████████████████ 100% (7/7 E2E tests passing)
BRN-004: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
BRN-005: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
BRN-006: ░░░░░░░░░░░░░░░░░░░░   0% (not yet implemented)
SVC-001: ████████████████████ 100% (3/3 E2E tests passing)
SVC-002: ████████████████████ 100% (5/5 E2E tests passing)
SVC-003: ████████████████████ 100% (4/4 E2E tests passing)
SVC-004: ████████████████████ 100% (6/6 E2E tests passing)
SVC-005: ████████████████████ 100% (8/8 E2E tests passing)
SVC-006: ████████████████████ 100% (2/2 E2E tests passing)
SVC-007: ████████████████████ 100% (5/5 E2E tests passing)

Total: 21/27 journeys implemented (78%)
P1 Journeys: 13/13 implemented (100%) ✅
P2 Journeys: 6/11 implemented (55%)
P3 Journeys: 2/3 implemented (67%)
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

### Feature 005: Agent Hub

| User Story | Journeys | Status |
|------------|----------|--------|
| US1: Route Questions to Experts | AH-001 | ✅ Implemented |
| US2: Maintain Conversation Sessions | AH-002 | ✅ Implemented |
| US3: Validate Confidence and Escalate | AH-003 | ✅ Implemented |
| US4: Track Pending Escalations | AH-004 | ✅ Implemented |
| US5: Audit Trail Logging | AH-005 | ✅ Implemented |

### Feature 006: Baron PM Agent

| User Story | Journeys | Status |
|------------|----------|--------|
| US1: Create Feature Specification | BRN-001 | ✅ Implemented |
| US2: Generate Implementation Plan | BRN-002 | ✅ Implemented |
| US3: Generate Task List | BRN-003 | ✅ Implemented |
| US4: Handle Pending Escalations | BRN-004 | 📋 Planned |
| US5: Expert Consultation Flow | BRN-005 | 📋 Planned |
| US6: Constitution Compliance | BRN-006 | 📋 Planned |

### Feature 008: Services Architecture

| User Story | Journeys | Status |
|------------|----------|--------|
| US1: Orchestrator Workflow Execution | SVC-001 | ✅ Implemented |
| US2: Expert Agent Consultation | SVC-002 | ✅ Implemented |
| US3: Human Review Escalation | SVC-003 | ✅ Implemented |
| US4: Multi-Turn Session | SVC-004 | ✅ Implemented |
| US5: Stateless Agent Invocation | SVC-005 | ✅ Implemented |
| US6: Local Development Setup | SVC-006 | ✅ Implemented |
| US7: Audit Log Query | SVC-007 | ✅ Implemented |

### Future Features

| Feature | Journeys | Status |
|---------|----------|--------|
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
**By**: Feature 008 Services Architecture - All User Stories Complete (P1 MVP)
**Next Review**: After implementing Baron P2 features (US4-6)
