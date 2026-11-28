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
5. Run `<tool_prefix>_verify` after maintenance (`agent_verify` only when the prefix is left at its default).
6. Commit only after the user approves the final state; push only after separate user approval. Exception: scheduled `Bridge/sync.sh` runs may commit and push mechanical `sync(host): auto` increments (Today-style content only, never code or durable-memory changes).

## Durable Memory

- Create a reviewable proposal before changing durable memory.
- Apply it only after explicit user confirmation.
- Keep project and temporary work details in `Brain/Today.md` unless they change durable behavior or judgment.
- Exception — the nightly dream (`Bridge/dream.py`): it may append dated entries to `Brain/Living/{year}.md` and `Brain/Reflection.md` under its own contract (distill-only-what-was-written, never infer, idempotent by date, failure-safe). It harvests the day; it never rewrites history. See `docs/DreamAndSync.md`.
