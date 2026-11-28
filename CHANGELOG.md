# Changelog

## Unreleased

- [feature] Backfill the production room model with generic, de-identified defaults: `config/rooms.json` (boot/operations/story contracts), `<prefix>_read_room` tool and resources, `<prefix>_update_memory` (Today.md only).
- [feature] De-identified extension modules: `association_engine.py` + generic `config/associations.json` wired into `get_context`, `memory_strength.py`, `monthly_letter.py`; dream gains generic `AGENT_LLM_*` chain aliases and nightly RecallIndex rebuild.
- [docs] AGENTS.md uses `<tool_prefix>_verify` so custom-prefix deployments do not refer to a nonexistent tool; merged duplicate Unreleased sections.
- Bridge: server.py 支持 AGENT_MCP_TRANSPORT/HOST/PORT 环境变量切换远程传输(streamable-http), 默认 stdio 不变
- scripts: 新增 precompact_note.py — CC PreCompact 钩子, 上下文压缩前把 transcript 指针写进 Today.md(路径按脚本位置自推导, 任意克隆通用)
- BootProtocol: 新增"上下文压缩恢复"协议(钩子指针 / recall 纪律 / 归档检索)
- start_session 引导: 增加"找不到凭证/路径/决定先查记忆再问人"的检索纪律


- [fix] `daily_rollover.py`: the undated/empty reset branch now snapshots `Today.md` (`undated-{time}.md`) before wiping - a stale `Date:` field plus that branch could silently drop a whole day of notes.
- [fix] `agent_note_today` and the rollover take a file lock (`Brain/.today.lock`); multiple agent instances on one machine no longer overwrite each other's notes.
- [fix] The rollover pulls before archiving, so it never archives onto a stale view of `Living/{year}.md`.
- [feature] `scripts/rename_agent.py`: rename an initialized companion without reinstalling — updates identity/instruction files, wake words and tool prefix, regenerates the prompt, and leaves `Brain/Living` / archive history untouched.
- [fix] `init_agent.py` now also overwrites the template's literal `TestAgent` / `TestUser` placeholders and the Identity fields, so a fresh clone really adopts the requested name.
- [docs] Restore guide now leads with copying the old agent folder and giving the AI a reconnect prompt; explains that `.venv` is machine-specific and must be rebuilt, and that MCP is a local stdio entry per machine.
- [docs] README quick start now passes name, user, bilingual wake words and tool prefix to the agent; new "rename your companion" section is copy-paste ready.
- [fix] `init_agent.py` now replaces `{{AGENT_NAME}}` / `{{USER_NAME}}` across every Markdown file under `Brain/` and `MemoryPack/`, not just Identity and WelcomeHome (BootProtocol previously kept raw placeholders).
- [feature] `init_agent.py --tool-prefix companion` writes `tool_prefix` during setup; unset prefixes default to an ASCII slug of the agent name, else `agent`.
- [feature] Bilingual wake words: `wake_words` in `Bridge/config.json` accepts any mix of Chinese/English names (e.g. `["Companion","companion"]`); the generated system prompt tells the companion that every listed name wakes the same identity. `init_agent.py --wake-words "Companion,companion"` writes it during setup.
- [feature] Custom MCP tool prefix: `tool_prefix` in `Bridge/config.json` (default `agent`) renames `agent_*` tools to `<prefix>_*` (e.g. `companion_wake`); the generated system prompt is substituted to match.
- [feature] Union merge for append-only memory logs via `.gitattributes` (`Brain/Today.md`, `Brain/Living/20*.md`): cross-machine sync keeps both sides' additions instead of whole-file replacement. Docs: `docs/DreamAndSync.md` (union subsection + ops lessons 6-7).

## v0.2 — 2026-11-17 (backported from a production deployment)

- [feature] `Bridge/dream.py` + `Bridge/dream.sh`: nightly pure-API memory consolidation — distill `Today.md` into `Brain/Living/{year}.md` and `Brain/Reflection.md`, archive the day, reset `Today.md`, commit and push. Idempotent by date, failure-safe, per-model retry chain.
- [fix] Dream dates follow the real calendar: the 凌晨 (early-morning) run distills **yesterday** (run date − 1) regardless of the stale `Date:` field in `Today.md`, and only resets `Today.md` when it still holds yesterday's content — a 凌晨 note written after midnight stays with its own calendar day.
- [fix] Three-source merge: the dream distills the rollover's full-day backup (`Brain/.backups/{yesterday}.md` — written by `daily_rollover.py` before its reset) plus the previous archive plus any legacy `Today.md`, so notes written during the day are distilled even though the rollover resets `Today.md` before the dream runs. Room sections are upserted (re-distill replaces) instead of skip-if-exists, and never touch a same-date `Daily Rollover` raw entry.
- [feature] `agent_note_today` MCP tool: append one timestamped line to `Brain/Today.md` (direct write — Today is ephemeral; durable memory still requires proposal + confirmation).
- [feature] `agent_recall` + `agent_read_lines` MCP tools: full-text memory search over `Brain/**/*.md` (Latin word-boundary + CJK bigram scoring) and exact-region reading.
- [feature] `Bridge/sync.sh`: incremental cron sync (stale-rebase abort, host-tagged auto commit, pull --rebase, push).
- [feature] Dream on/off switch: `dream_enabled` in `config.json` (env `LIVINGOS_DREAM_ENABLED` overrides), **off by default** — a disabled dream makes zero API calls; when on, one light chat-completion per night, empty days exit before any call.
- [feature] Dreamer host guard: consolidation runs on exactly one machine, configured via `LIVINGOS_DREAM_HOST` / `config.json:dream_host`, suffix-stripped hostname comparison.
- [fix] Privacy hardening — the template now passes its own publish check for the first time:
  - `scripts/build_agent.py`: chat-role parser genericized (residual personal names removed from the published regex and role mapping)
  - `templates/questionnaire.md`: example agent names genericized
  - `scripts/check_before_publish.py`: skip self-scan (deny-list terms live in its own source), skip virtualenv directories (site-packages regex literals are false positives), drop the public account handle from private terms (it appears in the repo's own attribution), and add the previously missed private term to the guard list
- [docs] `docs/DreamAndSync.md`: multi-machine topology, incremental sync, retrieval, the dream contract, and five ops lessons taken from real incidents in the source deployment.
- [config] `config.example.json`: added `dream_host` and LLM environment hints.

The production deployment this was backported from has evolved the original
template since 2026-08 (nightly distillation instead of manual wake, multi-machine
single-source-of-truth sync, hardened guards). v0.2 brings those patterns back
into the public template.
