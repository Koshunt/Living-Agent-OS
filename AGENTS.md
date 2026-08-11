# Agent OS Multi-Machine Rules

## Shared And Local State

- `main` is the shared memory and source-of-truth branch.
- Machine branches are temporary setup or transfer branches only.
- Shared memory, reusable scripts, documentation, and configuration examples may merge to `main` after review.
- Keep `Bridge/config.json`, local Python paths, proxy settings, secrets, and absolute paths local or ignored.

## Safe Synchronization

1. Fetch before comparing branches.
2. Do not pull or merge blindly with a dirty worktree.
3. Merge daily memory files manually when both sides changed them.
4. Do not replace `Brain/Today.md` unless the replacement is clearly newer.
5. Run `agent_verify` after maintenance.
6. Commit only after the user approves the final state; push only after separate user approval.

## Durable Memory

- Create a reviewable proposal before changing durable memory.
- Apply it only after explicit user confirmation.
- Keep project and temporary work details in `Brain/Today.md` unless they change durable behavior or judgment.
