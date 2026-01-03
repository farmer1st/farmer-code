# WT-002: Initialize Plans Folder Structure

**Actor**: Developer or AI Agent
**Goal**: Set up specification folder structure for a feature
**Preconditions**: Worktree exists for the feature
**Priority**: P1

## Steps

1. **Request plans initialization**
   - Expected outcome: `.plans/{issue}/` directory created
   - System behavior: Creates folder structure with template files

2. **Verify folder structure**
   - Expected outcome: All required files exist
   - System behavior: Returns PlansFolder model with paths to:
     - `.plans/{issue}/README.md`
     - `.plans/{issue}/spec.md`
     - `.plans/{issue}/plan.md`
     - `.plans/{issue}/tasks.md`

3. **Templates populated with metadata**
   - Expected outcome: Files contain issue number and feature title
   - System behavior: README.md has correct header and links

## Success Criteria

- Plans folder created in under 1 second
- All 4 template files present
- Files contain correct issue metadata
- Idempotent (can be called multiple times safely)

## E2E Test Coverage

- Test file: `tests/e2e/test_worktree_e2e.py`
- Journey marker: `@pytest.mark.journey("WT-002")`
- Covered steps: 1, 2, 3
- Test status: `test_init_plans_e2e`

## Related Journeys

- [WT-001](./WT-001-create-worktree.md): Create worktree before initializing plans
- [WT-003](./WT-003-commit-push.md): Commit plans after editing
