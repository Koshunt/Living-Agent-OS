# Changelog

## v0.2 — 2026-11-17 (backported from a production deployment)

- [feature] `Bridge/dream.py` + `Bridge/dream.sh`: nightly pure-API memory consolidation — distill `Today.md` into `Brain/Living/{year}.md` and `Brain/Reflection.md`, archive the day, reset `Today.md`, commit and push. Idempotent by date, failure-safe, per-model retry chain.
- [feature] `agent_note_today` MCP tool: append one timestamped line to `Brain/Today.md` (direct write — Today is ephemeral; durable memory still requires proposal + confirmation).
- [feature] `agent_recall` + `agent_read_lines` MCP tools: full-text memory search over `Brain/**/*.md` (Latin word-boundary + CJK bigram scoring) and exact-region reading.
- [feature] `Bridge/sync.sh`: incremental cron sync (stale-rebase abort, host-tagged auto commit, pull --rebase, push).
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
