# WT-004: Cleanup Worktree After Feature Completion

**Actor**: Developer or AI Agent
**Goal**: Remove worktree and branch after feature is merged
**Preconditions**: Feature merged to main, worktree no longer needed
**Priority**: P2

## Steps

1. **Remove worktree directory**
   - Expected outcome: Worktree directory deleted, git metadata cleaned
   - System behavior:
     - Runs `git worktree remove`
     - Deletes the sibling directory
     - Returns OperationResult with success

2. **Delete local branch**
   - Expected outcome: Feature branch removed from local
   - System behavior:
     - Runs `git branch -d` (or `-D` if force)
     - Validates branch is merged before deletion

3. **Delete remote branch (optional)**
   - Expected outcome: Feature branch removed from origin
   - System behavior:
     - Runs `git push origin --delete`
     - Returns OperationResult with status

## Success Criteria

- Worktree directory completely removed
- No orphaned git worktree references
- Branch deleted locally (and optionally remotely)
- No data loss if uncommitted changes exist (error raised)

## E2E Test Coverage

- Test file: `tests/e2e/test_worktree_e2e.py`
- Journey marker: `@pytest.mark.journey("WT-004")`
- Covered steps: 1, 2
- Test status: `test_remove_worktree_e2e`

## Related Journeys

- [WT-001](./WT-001-create-worktree.md): Create worktree (inverse operation)
- [WT-003](./WT-003-commit-push.md): Ensure changes pushed before cleanup
