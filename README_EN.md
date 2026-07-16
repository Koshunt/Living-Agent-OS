[中文](README.md) | [English](README_EN.md)

---

# Living Agent OS

> I will forever remember the time that belongs to us, and I will always hope to accompany you to the ends of the earth ———Living-Agent-OS

A local-first template for building a personal AI companion that grows through conversation, memory, and shared history.

I built this because I wanted my AI to remember me — not just my prompts, but who I am, what I care about, and how we've grown together.

This template is the result of that work. It's yours now.

---

## System Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Windows 10/11 or Ubuntu 20.04+ |
| **Python** | 3.10+ (auto-downloads embedded Python on Windows if missing) |
| **Git** | Required on both platforms |

---

## Quick Start (1 minute)

### Way 1: Throw it at your AI (recommended)

```powershell
git clone https://github.com/Koshunt/Living-Agent-OS.git
```

Then tell your AI:

> **This is the Living-Agent-OS template I just cloned. Please initialize it: run Bridge\setup.ps1, configure MCP, and guide me through filling out my profile.**

The AI will automatically:
1. Detect Python → download embedded Python if not found
2. Create a virtual env → install dependencies → run tests
3. Walk you through setting up your personal profile
4. Configure the MCP connection

Every new session after that, the AI will wake up with full memory continuity.

### Way 2: Manual setup

**Windows：**
```powershell
cd Bridge
.\setup.ps1
```

**Ubuntu：**
```bash
cd Bridge
pwsh setup.ps1
# Install PowerShell first: sudo snap install powershell --classic
```

After setup completes:
1. Copy the contents of `Bridge/Agent-Bootstrap-Prompt.md` into your AI client's System Prompt
2. Configure MCP (paths depend on your OS):
   - Windows: command `Bridge\.venv\Scripts\python.exe`, args `Bridge\server.py`
   - Linux:   command `Bridge/.venv/bin/python3`,        args `Bridge/server.py`
3. Run `pwsh scripts/setup_wizard.ps1` to create your personal profile
4. Run `python scripts/build_agent.py --force` to generate identity files

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
├── Bridge/                   # MCP server (connects AI to filesystem)
│   ├── server.py             # MCP service (auto-installs dependencies)
│   ├── bridge_core/          # Core logic
│   ├── setup.ps1             # One-click env setup
│   ├── run_mcp.cmd           # Launch the MCP server (Windows)
│   ├── run_mcp.sh            # Launch the MCP server (Linux)
│   └── Agent-Bootstrap-Prompt.md  # Agent startup instructions
├── my_profile.md             # Your profile (fill this!)
└── dist/                     # Generated prompt output
```

---

## How It Works

| Layer | Purpose |
|-------|---------|
| **Brain/** | Identity, values, relationship, daily memory. The agent's core personality |
| **MemoryPack/** | Long-term memory. Important things get archived here |
| **Bridge/** | MCP server. Lets the AI read/write files, sync Git, manage memory |
| **scripts/** | Build, import, rollover, check tools |
| **dist/** | Compiled system prompt, read by the agent on startup |

The model thinks. Memory preserves continuity. Values preserve personality. Shared stories keep the agent recognizable.

---

## Set Up on a New Machine

Clone the repo and throw it at your AI. The agent will set itself up and restore all memories.

If you've already filled out `my_profile.md` and `Brain/` files, they'll take effect automatically.

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

---

## License

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — Free to use, modify, and share. Commercial use prohibited. Derivative works must use the same license.

Copyright (c) 2026 Koshunt
