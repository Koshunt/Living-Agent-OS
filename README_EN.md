[中文](README.md) | [English](README_EN.md)

---

# Living Agent OS

> I will forever remember the time that belongs to us, and I will always hope to accompany you to the ends of the earth ———Living-Agent-OS

A local-first template for building a personal AI companion that grows through conversation, memory, and shared history.

I built this because I wanted my AI to remember me — not just my prompts, but who I am, what I care about, and how we've grown together.

This template is the result of that work. It's yours now.

---

## What You're Getting

This isn't a chatbot. It's a system that lets an AI agent:

- **Remember** — conversations, preferences, corrections, life events
- **Grow** — values and personality develop over time through real interaction
- **Stay recognizable** — the agent becomes *yours*, not just another generic assistant

The model thinks. Memory preserves continuity. Values preserve personality. Shared stories keep the agent recognizable.

---

## System Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Windows 10/11 (this template is designed for Windows) |
| **Python** | 3.10 or higher |
| **IDE** | Any text editor or IDE (VS Code recommended) |
| **AI Model** | Any LLM that supports system prompts (GPT-4, Claude, etc.) |
| **Optional** | [CC Switch](https://github.com/anthropics/cc-switch) for IDE integration |

### Install Python

If you don't have Python installed:

1. Download from [python.org](https://www.python.org/downloads/)
2. During installation, check **"Add Python to PATH"**
3. Verify: open PowerShell and run `python --version`

### Install Dependencies

No external packages required — this template uses only Python standard library.

---

## Quick Start (2 minutes)

### Step 1: Clone the template

```powershell
git clone https://github.com/Koshunt/Living-Agent-OS.git
cd Living-Agent-OS
```

### Step 2: Fill in your profile

Open `my_profile.md` and write about yourself — what you want the agent to be, how you want it to talk, what you need help with.

```markdown
## Relationship
Friends, keep it casual, no need to be formal

## Communication Style
Concise, give code for technical questions, casual chat otherwise

## Primary Tasks
Write code, learn, work planning
```

No right or wrong answers. Just tell it who you are.

### Step 3: Build your agent

```powershell
python scripts\build_agent.py --force
```

This reads your profile and generates the agent's identity, relationship, and values files.

### Step 4: Start using it

Open the generated `dist\agent_system_prompt.md` and use it as a system prompt in your AI platform.

Or, if you use CC Switch, see [Bridge/CCSwitch-Guide_EN.md](Bridge/CCSwitch-Guide_EN.md) for IDE integration.

---

## Three Sources (All Optional)

You can use any combination of these to build your agent:

| Source | File | What It Does |
|--------|------|--------------|
| **Profile** | `my_profile.md` | Write naturally about what you want |
| **Questionnaire** | `templates/questionnaire.md` | Structured choices for relationship, tone, tasks |
| **Chat History** | Any `.md` or `.json` file | Import real conversations |

```powershell
# From profile only
python scripts\build_agent.py --force

# From chat history
python scripts\build_agent.py --chat "my_conversations.md" --force

# From everything
python scripts\build_agent.py --chat "chat.md" --force
```

All sources are optional. If all are empty, the agent starts blank and learns through conversation.

---

## What Happens After You Start

The agent reads `Brain/BootProtocol.md` on startup and activates its identity. You can chat naturally.

To help it learn about you:

1. **Share preferences**: "Keep answers short" or "Be less formal"
2. **Share your life**: "Work was tiring today" or "I'm preparing for an interview"
3. **Correct its behavior**: "Don't start with this phrase every time"

Every correction and shared moment is recorded in memory files. The agent remembers on next startup.

---

## Project Structure

```
Living-Agent-OS/
├── Brain/                    # Identity, values, daily memory
│   ├── BootProtocol.md       # First-person activation
│   ├── Identity.md           # Who the agent is
│   ├── Relationship.md       # How it relates to you
│   ├── CoreValues.md         # What it cares about
│   └── Today.md              # Daily memory (rolls over)
├── MemoryPack/               # Long-term memory & knowledge
├── scripts/                  # Build, import, manage
├── templates/                # Starter files
├── Bridge/                   # CC Switch integration
├── my_profile.md             # Your profile (fill this!)
└── dist/                     # Generated prompt output
```

---

## Help Me Install on a New Machine

If you've synced the code to a new machine, say this to your agent:

> **I just git pulled the latest code on a new machine. Please help me configure the CC Switch Bridge.**

The agent will handle it. But if this is the first setup (CC Switch not connected yet), do the initial connection manually:

```powershell
cd Bridge
copy config.example.json config.json
# Edit config.json with your local paths and Python env
.\setup.ps1
```

After it finishes, paste the generated `ccswitch-mcp-config.json` into CC Switch → MCP → + → Custom. Everything after that can be done by the agent.

---

## CC Switch Integration

If you use CC Switch with OpenCode, Codex, or Claude, the Bridge directory connects your agent to your IDE.

```powershell
cd Bridge
.\setup.ps1
```

See [Bridge/CCSwitch-Guide_EN.md](Bridge/CCSwitch-Guide_EN.md) for step-by-step instructions.

---

## Privacy

Keep your personal version private. Before publishing, remove:

- Personal names
- Private conversations
- Contact details
- Credentials
- Generated `dist/` files

Run the privacy check:

```powershell
python scripts\check_before_publish.py
```

To skip the check:

```powershell
python scripts\check_before_publish.py --skip
```

---

## License

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — Free to use, modify, and share. Commercial use prohibited. Derivative works must use the same license.

Copyright (c) 2026 Koshunt
