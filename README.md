# Living Agent OS Template

A local-first template for building a personal AI companion or agent that grows through conversation, memory, values, and shared history.

This project is not built to save a specific AI.

It is built to help a user preserve a relationship with an agent that can keep growing.

The model thinks.

Memory preserves continuity.

Values preserve personality.

Shared stories keep the agent recognizable over time.

## What This Template Is

This repository is a clean starting point. It contains no private memories, no personal names, and no prebuilt relationship.

The user starts from blank templates, writes the first identity and values, then gradually adds:

- stable identity rules;
- relationship preferences;
- correction memories;
- living yearly memory;
- conversation examples;
- domain knowledge;
- working habits;
- scripts for generating a model-ready prompt.

## One Command, All Sources

The unified `build_agent.py` reads from all available sources and merges them:

| Source | Priority | What it provides |
|--------|----------|------------------|
| `my_profile.md` | Highest | Relationship, tone, tasks, preferences, restrictions |
| `questionnaire.md` | Medium | Structured choices for relationship, tone, tasks |
| Chat history file | Lowest | Extracted behavioral preferences |

All sources are optional. If all are empty, the agent starts blank and learns through conversation.

```powershell
python scripts\build_agent.py --chat "chat.md" --force
```

This auto-detects `my_profile.md` and `templates\questionnaire.md` in the repo root. You only need to provide what you have.

### Scenario: No chat history, no questionnaire

```powershell
# Just fill in my_profile.md, then:
python scripts\build_agent.py --force
```

### Scenario: Has chat history but nothing else

```powershell
python scripts\build_agent.py --chat "chat.md" --force
```

### Scenario: Has everything

```powershell
python scripts\build_agent.py --chat "chat.md" --force
```

### Scenario: Start completely blank

```powershell
# Delete or empty all source files, then:
python scripts\build_agent.py --force
# Agent learns through conversation
```

### Manual Setup (alternative)

```powershell
python scripts\init_agent.py --agent-name "YourAgent" --user-name "YourName"
powershell -ExecutionPolicy Bypass -File scripts\wake_agent.ps1
```

The wake script generates:

```text
dist/agent_system_prompt.md
```

Use that file as a System Prompt, character context, or long-context memory pack in your model provider.

## From Chat History to Personal Agent

The fastest way to build a personalized agent is from real conversations.

### One command

```powershell
python scripts\build_agent.py --chat "chat.md" --force
```

This does everything: import chat → merge with profile/questionnaire → personalize files → generate prompt.

### What to say after the agent starts

After the agent starts, it activates its identity by reading `Brain/BootProtocol.md`. You can chat naturally.

To help it learn about you:

1. Share preferences: "Keep answers short" or "Be less formal"
2. Share your life: "Work was tiring today" or "I'm preparing for an interview"
3. Correct its behavior: "Don't start with this phrase every time"

Every correction and shared moment is recorded in memory files. The agent remembers on next startup.

If the MCP Bridge is configured, the agent automatically calls `agent_wake` on startup to sync memory, then responds with first-person continuity.

### Step by step

```powershell
python scripts\build_agent.py --chat "path\to\chat.md" --force
```

The script auto-detects `my_profile.md` and `templates\questionnaire.md`. Merge priority: profile > questionnaire > chat.

## What to say after the agent starts

After the agent starts, it activates its identity by reading `Brain/BootProtocol.md`. You can chat naturally.

To help it learn about you:

1. Share preferences: "Keep answers short" or "Be less formal"
2. Share your life: "Work was tiring today" or "I'm preparing for an interview"
3. Correct its behavior: "Don't start with this phrase every time"

Every correction and shared moment is recorded in memory files. The agent remembers on next startup.

If the MCP Bridge is configured, the agent automatically calls `agent_wake` on startup to sync memory, then responds with first-person continuity.

## Project Structure

| Path | Purpose |
|---|---|
| `Brain/BootProtocol.md` | First-person activation protocol |
| `Brain/Home.md` | Quiet welcome orientation |
| `Brain/Today.md` | Short-lived daily memory (rolls over each day) |
| `Brain/Reflection.md` | Behavior improvement lessons |
| `Brain/Voice.md` | Voice and tone rules |
| `Brain/ConversationPolicy.md` | When to explain, when to be quiet |
| `Brain/MemoryChangePolicy.md` | What deserves permanent memory |
| `Brain/MaintenanceContract.md` | When to actively maintain memory |
| `Brain/AssociationPolicy.md` | Natural memory recall rules |
| `Brain/Promises.md` | Commitments across sessions |
| `Brain/Immutable/` | Identity, relationship, and values |
| `Brain/Living/` | Yearly living memory |
| `Brain/Letters/` | Welcome and return messages |
| `MemoryPack/Prompt/` | Core operating instructions |
| `MemoryPack/Persona/` | Why the agent speaks this way |
| `MemoryPack/Memory/` | Long-term memories, corrections, decisions |
| `MemoryPack/Examples/` | Dialogue examples |
| `MemoryPack/Knowledge/` | Domain knowledge |
| `scripts/` | Generate, check, import, personalize, retrieve |
| `templates/` | Blank starter files |
| `Bridge/` | CC Switch MCP bridge for IDE integration |

## CC Switch Integration

The `Bridge/` directory enables integration with CC Switch for OpenCode, Codex, and Claude.

```powershell
cd Bridge
.\setup.ps1
```

See `Bridge/CCSwitch-Guide.md` for detailed instructions.

## Privacy

Keep your personal version private by default.

Before publishing any derived project, remove:

- personal names;
- private conversations;
- contact details;
- credentials;
- generated `dist/` files;
- chat exports;
- sensitive work, school, company, research, or medical details.

The `scripts/check_before_publish.py` script scans for common leaks:

```powershell
python scripts\check_before_publish.py
```

See `docs/Privacy.md`.

## License

This template uses the MIT License. Replace the copyright holder before publishing.
