# Dream And Sync — Nightly Consolidation And Multi-Machine Topology

Backported in v0.2 from a private deployment that has run this design daily
since 2026-08. What follows is the pattern as production hardened it.

## The dream: nightly memory consolidation

`Bridge/dream.py` runs once a night, unattended:

1. `git pull --rebase` — fold in what other machines pushed during the day
   (the remote `main` branch is the single source of truth).
2. Read the day's notes (see "Three-source merge" below). If empty, do nothing.
3. Distill through an OpenAI-compatible chat API:
   - `living` entries → appended to `Brain/Living/{year}.md` as a dated section
   - `reflection` entries → appended to `Brain/Reflection.md`, but only genuine
     lessons phrased as behavior updates
4. Archive the day, reset `Today.md`.
5. Commit and push.

### Enable or disable — and what it costs

The dream is **off by default**: set `"dream_enabled": true` in
`Bridge/config.json` (or env `LIVINGOS_DREAM_ENABLED=1`) to turn it on, flip
it back off at any time — a disabled dream makes **zero API calls**.

When enabled, a normal night costs **exactly one light chat-completion** (a
day with no notes exits before any call). The rollover resets cost nothing —
they are pure local file operations.

### Three-source merge

Since the rollover resets `Today.md` before the dream runs, the dream merges
three sources so nothing written during the day is missed:

1. `Brain/.backups/{yesterday}.md` — the rollover's full-day backup
2. the previous `Today-{yesterday}.md` archive, if any
3. `Today.md` itself, when it still holds yesterday's date (rollover never ran)

Room sections are **upserted**: re-distilling a date replaces that date's
`Nightly Dream` section instead of skipping, so notes added later still make
it in. A same-date `Daily Rollover` raw entry is never touched.

### The dream contract

This is the only automated writer allowed on durable files, under four rules:

- **Distill, never invent.** Only what the user actually wrote today.
- **Emotions are recorded, never inferred.**
- **Idempotent by date.** A date section already present is never written
  twice, so a crash mid-run cannot double-book memories.
- **Failure-safe.** If the API call fails, `Today.md` is left untouched and
  the next night retries cleanly.

Human/AI edits to durable memory still go through the proposal + confirmation
flow (`MemoryChangePolicy.md`); the dream does not replace that, it only
harvests what the day already produced.

### Setup

Linux (crontab — e.g. 03:17 nightly):

```
17 3 * * * /path/to/Living-Agent-OS/Bridge/dream.sh
```

Windows: Task Scheduler → daily task → `python Bridge\dream.py` with
`LIVINGOS_LLM_API_KEY` in the environment. The host guard lives in `dream.sh`
(Linux); on a single-machine setup you can call `dream.py` directly.

Environment variables:

| Variable | Meaning |
| --- | --- |
| `LIVINGOS_LLM_API_KEY` | required, key for the chat endpoint |
| `LIVINGOS_LLM_BASE_URL` | optional, OpenAI-compatible completions URL |
| `LIVINGOS_LLM_MODELS` | optional, comma-separated fallback chain |
| `LIVINGOS_DREAM_HOST` | optional, dreamer hostname (see below) |

## Multi-machine topology

Any number of machines can share one agent:

- **Remote `main` is the single source of truth.** Machine branches are for
  setup and transfer only.
- **Exactly one machine dreams.** Configure it via `LIVINGOS_DREAM_HOST` or
  `"dream_host"` in `Bridge/config.json`; `dream.sh` skips itself elsewhere.
  Two dreamers on the same night would race on `Today.md`.
- **Everyone else chats and pushes increments.** Frequent small pushes beat
  one giant end-of-week sync; the dreamer folds them in before distilling.
- The hostname guard compares the **suffix-stripped, lowercased** name
  (`host.example.local` → `host`). Suffixes have bitten a real deployment
  twice before this rule existed.

## Incremental sync

`Bridge/sync.sh` is the cron companion for non-dreamer machines (and a
safety net for the dreamer too):

```
0 * * * * /path/to/Living-Agent-OS/Bridge/sync.sh
```

It aborts any stale rebase left by a crashed pull, commits whatever changed
as `sync(host): auto`, then pulls with rebase and pushes. Quiet by design —
a failed run just retries on the next tick. Run it with `--dry-run` to see
what would go out. Mechanical `sync(host): auto` commits are the one
exception to the commit-approval rule in `AGENTS.md`; they carry only
Today-style increments, never reviewed code or durable-memory edits.

### Union merge for append-only logs

`Today.md`, `Living/{year}.md` and the daily archive files are append-only
logs written by several machines. Replace semantics on them is data loss.
`.gitattributes` therefore declares `merge=union` for these paths: when two
machines diverge, git keeps **both** sides' added lines. Caveats: identical
lines added on both sides may duplicate (harmless - the dream and room
parsers group by date section); deletions do not propagate (intended -
memory only shrinks via reviewed distillation, never via sync). The rollover
runs `git pull --rebase` before archiving so it always works on the merged
view, and snapshots `Today.md` before any reset as the last safety net.

## Retrieval

`agent_recall` (full-text over `Brain/**/*.md`, Latin words and CJK bigrams)
plus `agent_read_lines` (exact region) are how a session finds any memory
without reading every file. Plain scan, no index to go stale.


## Ops lessons (each one cost a real incident)

1. **Strip hostname suffixes before comparing.** `hostname` often returns
   `machine.local`; a guard that matches the short name only will silently
   pass on the wrong machine.
2. **Read tool output, not just exit codes.** A guard that prints `✓` and
   exits 0 can still have done nothing; verify the content of what a
   maintenance step claims.
3. **Disable thinking on reasoning models for structured jobs.** Hidden
   reasoning burns `max_tokens` and returns empty content. The production
   deployment lost nine consecutive nights to this before the flag was set.
4. **One failed dependency can poison a cache for a whole day.** When a
   fetch layer fails, do not cache the empty result; fail loudly instead.
5. **Prefer idempotent, append-only writes for anything unattended.** The
   dream may crash at any step; every step must be safe to redo.
6. **A shared mutable file needs a merge policy, not luck.** `Today.md` is
   written by every machine and rolled over locally; `pull --rebase` on two
   divergent versions is whole-file replacement, and notes written on one
   machine silently vanished when the other pushed a rolled-over template.
   Fix: `Brain/Today.md merge=union` in `.gitattributes` (append-only log
   semantics - additions from both sides survive, deletions are not
   expressed), plus the rollover snapshots before any reset.
7. **A reset without a snapshot is data loss with extra steps.** The
   rollover's undated/empty branch used to reset `Today.md` without writing
   `.backups/`; a stale `Date:` field plus that branch can swallow a whole
   day. Fix: every reset path snapshots first (`undated-{time}.md`), and
   `note_today` runs the rollover only after the snapshot safety net exists.
