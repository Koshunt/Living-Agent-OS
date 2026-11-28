"""Forgetting-curve memory tiering for Brain/Living.

Implements a Ebbinghaus-inspired recall-cost model:
  Tier 0 (hot):    full entries in Living/YYYY.md, recalled every wake.
  Tier 1 (warm):   body moved to Archive/YYYY-full.md, one-line index left behind.
  Tier 2 (cold):   only the index line remains in the warm file listing.

Reinforcement resets the curve: when an archived memory is recalled
(memory_strength.py reinforce <date>), its entry is promoted back toward hot.

Exempt memories never decay: promises, corrections, milestones, stamped
emotional moments. Marked inline with `<!-- keep -->` or listed in
EXEMPT_PATTERNS below.

Usage:
    python scripts/memory_strength.py status            # show tiers
    python scripts/memory_strength.py apply [--dry-run] # move expired bodies
    python scripts/memory_strength.py reinforce DATE    # recall = reset curve
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVING_DIR = ROOT / "Brain" / "Living"
ARCHIVE_DIR = ROOT / "Brain" / "Archive"

# Tier thresholds (days since last reinforcement)
HOT_DAYS = 14
WARM_DAYS = 45          # after this: body -> Archive
REINFORCE_LOG = ROOT / "Brain" / ".memory-strength.json"

# Memories that never decay. `<!-- keep -->` inside an entry wins outright.
EXEMPT_MARK = "<!-- keep -->"
EXEMPT_PATTERNS = (
    r"承诺|promise",
    r"纠正|correction",
    r"里程碑|milestone",
    r"第一次|first time|初雪|生日",
)

SECTION_RE = re.compile(r"^(## \d{4}-\d{2}-\d{2}[^\n]*)$", re.MULTILINE)


def _load_reinforcements() -> dict[str, str]:
    if REINFORCE_LOG.exists():
        import json
        return json.loads(REINFORCE_LOG.read_text(encoding="utf-8"))
    return {}


def _save_reinforcements(data: dict[str, str]) -> None:
    import json
    REINFORCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    REINFORCE_LOG.write_text(json.dumps(data, indent=2), encoding="utf-8")


def last_reinforced(entry_date: str, reinforced: dict[str, str]) -> str:
    """Most recent of (entry date, any later reinforcement)."""
    return max(entry_date, reinforced.get(entry_date, ""), key=str)


def age_days(entry_date: str, reinforced: dict[str, str], today: date) -> int:
    effective = last_reinforced(entry_date, reinforced) or entry_date
    d0 = date.fromisoformat(effective[:10])
    return max(0, (today - d0).days)


def tier_of(days: int) -> int:
    if days <= HOT_DAYS:
        return 0
    if days <= WARM_DAYS:
        return 1
    return 2


def split_sections(text: str) -> list[tuple[str, str]]:
    """Return [(section header line including '## ', body)] preserving order."""
    matches = list(SECTION_RE.finditer(text))
    sections = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((m.group(1).strip(), text[m.start():end].rstrip() + "\n"))
    return sections


def is_exempt(body: str) -> bool:
    if EXEMPT_MARK in body:
        return True
    low = body.lower()
    return any(re.search(p, low) for p in EXEMPT_PATTERNS)


def collect_status(today: date | None = None) -> list[dict]:
    today = today or date.today()
    reinforced = _load_reinforcements()
    out = []
    for year_file in sorted(LIVING_DIR.glob("20*.md")):
        text = year_file.read_text(encoding="utf-8")
        for header, body in split_sections(text):
            m = re.match(r"## (\d{4}-\d{2}-\d{2})", header)
            if not m:
                continue
            entry_date = m.group(1)
            days = age_days(entry_date, reinforced, today)
            exempt = is_exempt(body)
            tier = 0 if exempt else tier_of(days)
            out.append({
                "date": entry_date,
                "header": header,
                "tier": tier,
                "days": days,
                "exempt": exempt,
                "file": year_file,
                "body": body,
            })
    return out


def cmd_status() -> int:
    entries = collect_status()
    counts = {0: 0, 1: 0, 2: 0}
    for e in entries:
        counts[e["tier"]] += 1
    print(f"Living memory strength — hot:{counts[0]}  warm:{counts[1]}  cold:{counts[2]}  "
          f"(exempt included in hot)\n")
    for e in entries:
        flag = "[keep]" if e["exempt"] else ""
        print(f"  T{e['tier']} {e['date']}  {e['days']:>3}d  {flag} {e['header'][3:][:60]}")
    return 0


def cmd_apply(dry_run: bool = False) -> int:
    today = date.today()
    entries = collect_status(today)
    to_cool = [e for e in entries if not e["exempt"] and e["tier"] >= 1]
    if not to_cool:
        print("Nothing to cool — all entries hot or exempt.")
        return 0

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    moved = 0
    for e in to_cool:
        year_file: Path = e["file"]
        text = year_file.read_text(encoding="utf-8")
        body = e["body"]
        slimmed_header = f"{e['header'][:10]} [温] 已归档 → Archive/{year_file.stem}-full.md"
        new_body = (
            f"{slimmed_header}\n\n"
            f"- {e['date']} 的详细内容已按遗忘曲线归档。回忆到此条时运行：\n"
            f"  `python scripts/memory_strength.py reinforce {e['date']}` 可将其升回热层。\n"
        )
        text = text.replace(body, new_body + "\n")

        archive_file = ARCHIVE_DIR / f"{year_file.stem}-full.md"
        archive_file.parent.mkdir(parents=True, exist_ok=True)
        with archive_file.open("a", encoding="utf-8", newline="\n") as h:
            if archive_file.stat().st_size == 0:
                h.write(f"# {year_file.stem} cold archive\n")
            h.write("\n" + body)

        if not dry_run:
            year_file.write_text(text, encoding="utf-8", newline="\n")
        moved += 1
        print(f"cooled {e['date']} ({e['days']}d) -> Archive/{archive_file.name}")

    print(f"\n{'[dry-run] would move' if dry_run else 'moved'} {moved} entr"
          f"{'y' if moved == 1 else 'ies'} to cold archive.")
    return 0


def cmd_reinforce(entry_date: str) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    reinforced = _load_reinforcements()
    # Reinforcing the latest matching entry resets the whole day's curve;
    # store per-date, keep newest timestamp.
    prev = reinforced.get(entry_date)
    if prev and prev > now:
        now = prev
    reinforced[entry_date] = now
    _save_reinforcements(reinforced)
    print(f"reinforced {entry_date} at {now}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    ap_apply = sub.add_parser("apply")
    ap_apply.add_argument("--dry-run", action="store_true")
    ap_re = sub.add_parser("reinforce")
    ap_re.add_argument("date")
    args = ap.parse_args(argv)

    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "apply":
        return cmd_apply(dry_run=args.dry_run)
    if args.cmd == "reinforce":
        return cmd_reinforce(args.date)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
