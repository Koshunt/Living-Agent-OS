from __future__ import annotations

import re
from datetime import date
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
    year_path = ROOT / "Brain" / "Living" / f"{entry_date[:4]}.md"
    year_path.parent.mkdir(parents=True, exist_ok=True)
    if not year_path.exists():
        year_path.write_text(f"# {entry_date[:4]}\n", encoding="utf-8")
    with year_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"\n\n## {entry_date}: Daily Rollover\n\n")
        handle.write(text.strip() + "\n")
    return year_path


def rollover(current_date: str | None = None) -> tuple[bool, str]:
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
        action = "reset undated or empty state"
    TODAY_PATH.write_text(fresh_today(today), encoding="utf-8", newline="\n")
    return True, action


def main() -> int:
    changed, action = rollover()
    print(f"Today memory: {action}" if changed else "Today memory: current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
