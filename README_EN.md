[中文](README.md) | [English](README_EN.md)

---

# Living Agent OS

> I will forever remember the time that belongs to us, and I will always hope to accompany you to the ends of the earth ———Living-Agent-OS

A local-first template for building a personal AI companion that grows through conversation, memory, and shared history.

I built this because I wanted my AI to remember me — not just my prompts, but who I am, what I care about, and how we've grown together.

This template is the result of that work. It's yours now.

---

## New in v0.2 (2026-11)

- **Nightly dream**: `Bridge/dream.py` distills `Today.md` into durable memory (`Brain/Living/{year}.md` and `Reflection.md`), archives the day, resets, and pushes — idempotent, failure-safe, with a per-model retry chain. **Off by default**: enable with `"dream_enabled": true` in `config.json`; when on, one light API call per night, empty nights cost nothing, flip off anytime. See `docs/DreamAndSync.md`.
- **Handover note**: new MCP tool `agent_note_today` appends one timestamped line to `Today.md` (Today is ephemeral working memory, so it writes directly; durable memory still goes through proposal + confirmation).
- **Memory retrieval**: `agent_recall` full-text search over `Brain/` (Latin word-boundary + CJK bigram scoring) and `agent_read_lines` to open the exact hit region — remember anything without reading every file.
- **Incremental sync**: `Bridge/sync.sh` cron companion (host-tagged auto commit → pull --rebase → push), pairing with the dreamer guard to complete the multi-machine topology.
- **Multi-machine topology**: remote `main` is the single source of truth; exactly one machine dreams (`dream_host`), the rest chat and push increments.
- v0.2 patterns were backported from a production deployment running daily since 2026-08.

## System Requirements

| Requirement | Details |
|-------------|---------|
| **OS** | Windows 10/11 or Ubuntu 20.04+ |
| **Python** | 3.10+ (auto-downloads embedded Python on Windows if missing) |
| **Git** | Required on both platforms |

---

## Quick Start (1 minute)

### Way 1: Throw it at your AI (recommended)

```bash
git clone https://github.com/Koshunt/Living-Agent-OS.git
```

In China:

```bash
git clone https://atomgit.com/na_th_an/Living-Agent-OS.git
```

Then tell your AI (replace the bracketed parts):

> **This is the Living-Agent-OS template I just cloned. Please set it up:**
> **1. Run `Bridge/setup.ps1` (use `Bridge/setup.sh` on Linux) and configure MCP.**
> **2. Guide me through `my_profile.md`.**
> **3. Initialize the identity with `python scripts/init_agent.py --agent-name "<companion>" --user-name "<what to call me>" --wake-words "<Chinese name,English name>" --tool-prefix <ascii-prefix>`.**
> **4. Regenerate the prompt and add `Bridge/Agent-Bootstrap-Prompt.md` to my AI client's System Prompt.**

The AI will automatically:
1. Detect Python → download embedded Python if not found
2. Create a virtual env → install dependencies → run tests
3. Walk you through setting up your personal profile
4. Configure the MCP connection and write the companion name, your name, bilingual wake words, and the MCP tool prefix

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
bash setup.sh
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
│   ├── Immutable/            # Identity / Relationship / CoreValues
│   ├── Promises.md           # Promises
│   ├── Home.md / Voice.md    # Homecoming and voice
│   ├── Today.md              # Daily memory (rolls over)
│   └── Living/YYYY.md        # Yearly long-term memory (history is never rewritten)
├── MemoryPack/               # Long-term memory, persona, knowledge
├── config/prompt.yaml        # System-prompt assembly list
├── scripts/                  # init_agent / rename_agent / update_memory, etc.
├── templates/                # Starter files
├── Bridge/                   # MCP server (connects AI to filesystem)
│   ├── server.py             # MCP service (tool names follow tool_prefix)
│   ├── bridge_core/          # Core logic
│   ├── config.example.json   # Sample: tool_prefix / wake_words / dream
│   ├── setup.ps1 / setup.sh  # One-click env setup
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

### Tool names follow your companion

Set `"tool_prefix": "xiaohui"` in `Bridge/config.json` (default: `agent`), and the MCP tools become `xiaohui_wake`, `xiaohui_note_today`, and so on. Setup can do it too: `python scripts/init_agent.py --agent-name 小灰 --user-name Nathaniel --tool-prefix xiaohui`. Regenerate the prompt and restart the MCP server; no code changes needed.

### Rename your companion

You can rename an already-initialized home; no reinstall needed.

**Ask the AI to do it:**

> **Rename my companion. Read the current name from `Brain/Immutable/Identity.md`, then run:**
> **`python scripts/rename_agent.py --new-name "<new name>" --user-name "<what to call me>" --wake-words "<new name,English name>" --tool-prefix <ascii-prefix>`**
> **It updates identity and instruction files, writes `Bridge/config.json`, and regenerates the prompt. Historical names in `Brain/Living` and archives are left untouched. Restart MCP afterwards.**

**Or run it yourself:**

```bash
python scripts/rename_agent.py --new-name 阿灰 --user-name Nathaniel --wake-words "阿灰,Ahui" --tool-prefix ahui
```

Restart MCP / open a new session for the regenerated prompt to take effect.

### Chinese and English wake words

`wake_words` in `Bridge/config.json` is an array; mix languages freely:

```json
"wake_words": ["小灰", "Xiaohui", "xiao hui"]
```

Any of these names wakes the same companion when the generated prompt is in use. During setup you can also pass `--wake-words "小灰,Xiaohui" --tool-prefix xiaohui` to `scripts/init_agent.py`.

## Set Up on a New Machine

Clone the repo and throw it at your AI. The agent will set itself up and restore all memories.

If you've already filled out `my_profile.md` and `Brain/` files, they'll take effect automatically.

---

## Memory And Publication Safety

- Keep short-lived work in `Brain/Today.md`.
- For durable memory, use `agent_propose_memory`, show the proposed target, and apply it only after the user explicitly confirms with `确认`, `确认写入`, or `确认写入长期记忆`.
- Run `agent_verify` after memory maintenance.
- Commit only after user approval; push only after separate user approval.
- For a local pre-push secret/path check, install the Git hook once:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_git_hooks.ps1
```

```bash
sh scripts/install_git_hooks.sh
```

Multi-machine synchronization rules are in `AGENTS.md`.

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
