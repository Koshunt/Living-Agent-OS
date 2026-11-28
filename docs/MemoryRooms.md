# Memory Rooms

Living OS keeps memory as plain Markdown files under `Brain/` and `MemoryPack/`. Rooms exist so a wake bundle never cuts one memory area in half.

## Contracts

`config/rooms.json` is the single source of truth for room size limits and load timing. Every room has:

- `title`: human-readable name
- `output`: generated bundle path
- `max_chars`: hard limit enforced by the wake reader
- `read_when`: when the agent should open it
- `files`: ordered source files

Default rooms:

| Room | When to open | Contents |
|---|---|---|
| `boot` | every wake | identity, voice, conversation policy, Today.md, core prompt |
| `operations` | before memory work | maintenance contract, memory policy, association policy |
| `story` | continuity questions | reflection, promises, living year, decision/continuity memory |

## Read

Call `<prefix>_read_room` with `boot`, `operations`, or `story`. The tool returns the room text plus truncation metadata. MCP resources `<prefix>://boot`, `<prefix>://today`, `<prefix>://operations`, `<prefix>://story` expose the same material directly.

## Write rules

- `Brain/Today.md` is short-lived working memory. `<prefix>_note_today` appends one timestamped line. `<prefix>_update_memory` writes one titled section. Both write only Today.md.
- Durable memory is proposal-only: `<prefix>_propose_memory` creates a reviewable proposal. Nothing changes until the user explicitly confirms and `<prefix>_apply_memory` is called.
- Nightly dream may append dated distillations to `Brain/Living/{year}.md` and `Brain/Reflection.md` under its own contract. It never rewrites history.
- If a room is full, propose a distillation. No script may silently summarize durable rooms.

## De-identification

This template contains no personal memory, private names, server addresses, credentials, or real user history. Replace placeholders through `scripts/init_agent.py` and keep local configuration in ignored files.
