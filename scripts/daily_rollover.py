from __future__ import annotations

import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TODAY_PATH = ROOT / "Brain" / "Today.md"


def parse_date(text: str) -> str:
    match = re.search(r"^Date:\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.MULTILINE)
    return match.group(1) if match else ""


def meaningful_body(text: str) -> bool:
    ignored = {
        "# Today",
        "## Current State",
        "## Open Threads",
        "## Emotional Weather",
        "## Next Return",
        "## Rollover",
    }
    lines = [line.strip() for line in text.splitlines()]
    content = [
        line
        for line in lines
        if line and line not in ignored and not line.startswith("Date:") and not line.startswith("This file is short-lived")
    ]
    empty_defaults = {
        "- None yet.",
        "- Start from what is true today.",
    }
    return any(line not in empty_defaults for line in content)


def fresh_today(today: str) -> str:
    return f"""# Today

Date: {today}

## Current State

- None yet.

## Open Threads

- None yet.

## Emotional Weather

- Do not infer. Update only from what the user shares.

## Next Return

- Start from what is true today.

## Rollover

This file is short-lived working memory. On the first startup of a new day, meaningful content is archived to `Brain/Living/YYYY.md`, then this page is reset for the new date.
"""


def archive_today(text: str, entry_date: str) -> Path:
    # Pre-archive backup: mechanical safety net so the pre-rollover state of
    # Today.md survives even if later steps fail (the nightly dream merges
    # this backup back in, see Bridge/dream.py).
    backup_dir = ROOT / "Brain" / ".backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{entry_date}.md"
    if not backup.exists():
        shutil.copyfile(TODAY_PATH, backup)
    year_path = ROOT / "Brain" / "Living" / f"{entry_date[:4]}.md"
    year_path.parent.mkdir(parents=True, exist_ok=True)
    if not year_path.exists():
        year_path.write_text(f"# {entry_date[:4]}\n", encoding="utf-8")
    with year_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"\n\n## {entry_date}: Daily Rollover\n\n")
        handle.write(text.strip() + "\n")
    return year_path


def rollover(current_date: str | None = None) -> tuple[bool, str]:
    import fcntl
    lock_path = ROOT / "Brain" / ".today.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        # Pull before archiving: absorb other machines' increments first so the
        # rollover never archives onto a stale view (2026-11 multi-machine lesson).
        try:
            subprocess.run(["git", "pull", "--rebase", "-q"], cwd=ROOT,
                           timeout=60, capture_output=True)
        except Exception:
            pass  # offline is fine - the local snapshot below still prevents loss
        return _rollover_locked(current_date)

def _rollover_locked(current_date: str | None = None) -> tuple[bool, str]:
    today = current_date or date.today().isoformat()
    if not TODAY_PATH.exists():
        TODAY_PATH.write_text(fresh_today(today), encoding="utf-8", newline="\n")
        return True, "created"

    text = TODAY_PATH.read_text(encoding="utf-8")
    previous = parse_date(text)
    if previous == today:
        return False, "current"

    if previous and meaningful_body(text):
        archive_today(text, previous)
        action = f"archived {previous}"
    else:
        # Snapshot before wiping, even for undated/empty files: a reset without
        # a snapshot once silently dropped a day of notes (2026-11 lesson).
        import datetime as _dt
        backup_dir = ROOT / "Brain" / ".backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().strftime("%H%M%S")
        (backup_dir / f"undated-{stamp}.md").write_text(text, encoding="utf-8")
        action = "reset undated or empty state (snapshotted)"
    TODAY_PATH.write_text(fresh_today(today), encoding="utf-8", newline="\n")
    return True, action


def main() -> int:
    changed, action = rollover()
    print(f"Today memory: {action}" if changed else "Today memory: current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
