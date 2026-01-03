# WT-001: Create Worktree for Feature Development

**Actor**: Developer or AI Agent
**Goal**: Create an isolated development environment for a new feature
**Preconditions**: Git repository exists with a main branch
**Priority**: P1

## Steps

1. **Initialize worktree service**
   - Expected outcome: Service connects to repository
   - System behavior: Validates git is available and path is a repository

2. **Request new worktree creation**
   - Expected outcome: Branch created from main, worktree in sibling directory
   - System behavior:
     - Creates branch `{issue_number}-{feature_name}`
     - Creates worktree at `../{repo}-{issue_number}-{feature_name}/`
     - Returns Worktree model with path, branch, commit info

3. **Verify worktree is ready**
   - Expected outcome: Directory exists with checked out branch
   - System behavior: Worktree is on the new feature branch

## Success Criteria

- Worktree created in under 2 seconds
- Branch correctly based on main branch
- Worktree path follows naming convention
- No interference with main repository

## E2E Test Coverage

- Test file: `tests/e2e/test_worktree_e2e.py`
- Journey marker: `@pytest.mark.journey("WT-001")`
- Covered steps: 1, 2, 3
- Test status: `test_create_worktree_e2e`

## Related Journeys

- [WT-002](./WT-002-init-plans.md): Initialize plans folder after worktree creation
- [WT-004](./WT-004-cleanup-worktree.md): Cleanup worktree after feature completion
