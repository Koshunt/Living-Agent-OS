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

## Quick Start

```powershell
python scripts\init_agent.py --agent-name "YourAgent" --user-name "User"
powershell -ExecutionPolicy Bypass -File scripts\wake_agent.ps1
```

The wake script generates:

```text
dist/agent_system_prompt.md
```

Use that file as a System Prompt, character context, or long-context memory pack in your model provider.

## Project Structure

| Path | Purpose |
|---|---|
| `Brain/Immutable/` | Identity, relationship, and values that should not be casually overwritten |
| `Brain/Living/` | Yearly living memory that grows over time |
| `Brain/Letters/` | Welcome, handoff, and return messages |
| `MemoryPack/Prompt/` | Core operating instructions |
| `MemoryPack/Persona/` | Why the agent speaks and behaves this way |
| `MemoryPack/Memory/` | Long-term memories, corrections, decisions, and timelines |
| `MemoryPack/Examples/` | Dialogue examples for tone and behavior |
| `MemoryPack/Knowledge/` | User-specific domain knowledge |
| `scripts/` | Generate, check, export, retrieve, and append memory |
| `templates/` | Blank starter files for new agents |

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

See `docs/Privacy.md`.

## License

This template uses the MIT License. Replace the copyright holder before publishing.
