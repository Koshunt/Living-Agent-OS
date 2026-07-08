from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGETS = {
    "continuity": ROOT / "MemoryPack" / "Memory" / "ContinuityMemory.md",
    "correction": ROOT / "MemoryPack" / "Memory" / "CorrectionLog.md",
    "decision": ROOT / "MemoryPack" / "Memory" / "DecisionMemory.md",
    "living": ROOT / "Brain" / "Living" / "2026.md",
}


@dataclass(frozen=True)
class MemoryCandidate:
    category: str
    title: str
    body: str
    source: str = "manual"


def choose_target(category: str) -> Path:
    try:
        return TARGETS[category]
    except KeyError as error:
        allowed = ", ".join(sorted(TARGETS))
        raise SystemExit(f"Unknown category {category!r}. Use one of: {allowed}") from error


def append_memory(candidate: MemoryCandidate, entry_date: str | None = None) -> Path:
    target = choose_target(candidate.category)
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = entry_date or date.today().isoformat()
    entry = (
        "\n\n"
        f"## {stamp}: {candidate.title.strip()}\n\n"
        f"Source: {candidate.source.strip()}\n\n"
        f"{candidate.body.strip()}\n"
    )
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(entry)
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append a categorized memory entry.")
    parser.add_argument("category", choices=sorted(TARGETS))
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--source", default="manual")
    parser.add_argument("--date")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = append_memory(
        MemoryCandidate(
            category=args.category,
            title=args.title,
            body=args.body,
            source=args.source,
        ),
        entry_date=args.date,
    )
    print(f"Updated {target.relative_to(ROOT)}")
    print("Next: powershell -ExecutionPolicy Bypass -File scripts\\wake_agent.ps1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
