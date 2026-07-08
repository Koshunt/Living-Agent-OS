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
