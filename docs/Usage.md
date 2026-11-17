# Usage

## Initialize

```powershell
python scripts\init_agent.py --agent-name "YourAgent" --user-name "User"
```

## Wake

```powershell
powershell -ExecutionPolicy Bypass -File scripts\wake_agent.ps1
```

This generates:

```text
dist/agent_system_prompt.md
```

Use that generated file as a System Prompt or long-context memory pack.

## Add Memory

```powershell
python scripts\memory_manager.py living --title "First useful correction" --body "The user prefers direct, practical answers." --source "chat"
```

Categories:

- `continuity`
- `correction`
- `decision`
- `living`

## Build A Focused Context

```powershell
python scripts\conversation_pipeline.py "I need help debugging my project"
```

This writes:

```text
dist/conversation_context.md
```

## Export

```powershell
python scripts\export_memory_pack.py
```

This creates a portable zip under `dist/`.

## Nightly Dream And Multi-Machine Sync

Run the nightly consolidation and the hourly incremental sync from cron (or Task Scheduler):

```bash
17 3 * * * /path/to/Living-Agent-OS/Bridge/dream.sh
0 * * * * /path/to/Living-Agent-OS/Bridge/sync.sh
```

The dream distills `Brain/Today.md` into durable memory; the sync pushes increments from every other machine. Exactly one machine should dream — configure it via `dream_host`. Full contract, topology, and ops lessons: `docs/DreamAndSync.md`.

## Recall

During a session, call the `agent_recall` MCP tool for full-text search over `Brain/` (Latin and Chinese), then `agent_read_lines` to open an exact hit region. No index to maintain — it scans directly.
