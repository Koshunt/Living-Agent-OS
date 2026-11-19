# Changelog

## Unreleased

- [fix] `daily_rollover.py`: the undated/empty reset branch now snapshots `Today.md` (`undated-{time}.md`) before wiping - a stale `Date:` field plus that branch could silently drop a whole day of notes.
- [fix] `agent_note_today` and the rollover take a file lock (`Brain/.today.lock`); multiple agent instances on one machine no longer overwrite each other's notes.
- [fix] The rollover pulls before archiving, so it never archives onto a stale view of `Living/{year}.md`.
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
