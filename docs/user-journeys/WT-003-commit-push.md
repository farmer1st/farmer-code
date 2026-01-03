# WT-003: Commit and Push Feature Changes

**Actor**: Developer or AI Agent
**Goal**: Save and share feature work with the team
**Preconditions**: Worktree exists with uncommitted changes
**Priority**: P2

## Steps

1. **Commit changes in worktree**
   - Expected outcome: All changes committed with message
   - System behavior:
     - Stages all modified and new files
     - Creates commit with provided message
     - Returns CommitResult with SHA and file count

2. **Push to remote**
   - Expected outcome: Branch pushed to origin
   - System behavior:
     - Sets upstream on first push (`-u origin`)
     - Returns OperationResult with success status

3. **Verify remote sync**
   - Expected outcome: Local and remote branches aligned
   - System behavior: Branch shows as up-to-date with origin

## Success Criteria

- Commit created with correct message format
- All changes included in commit
- Push completes without force
- Branch trackable on remote

## E2E Test Coverage

- Test file: `tests/e2e/test_worktree_e2e.py`
- Journey marker: `@pytest.mark.journey("WT-003")`
- Covered steps: 1, 2, 3
- Test status: `test_commit_and_push_e2e`

## Related Journeys

- [WT-002](./WT-002-init-plans.md): Initialize plans before committing
- [WT-004](./WT-004-cleanup-worktree.md): Cleanup after push and merge
