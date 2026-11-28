from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "associations.json"


@dataclass(frozen=True)
class Association:
    identifier: str
    memory: Path
    cue: str
    matched: tuple[str, ...]


def find_association(message: str) -> Association | None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    lower = message.lower()
    matches: list[tuple[int, dict, tuple[str, ...]]] = []
    for item in config.get("associations", []):
        hit = tuple(trigger for trigger in item.get("triggers", []) if trigger.lower() in lower)
        memory = ROOT / item.get("memory", "")
        if hit and memory.is_file():
            matches.append((len(hit), item, hit))
    if not matches:
        return None
    _, item, hit = max(matches, key=lambda candidate: (candidate[0], candidate[1]["id"]))
    return Association(
        identifier=item["id"],
        memory=ROOT / item["memory"],
        cue=item["cue"],
        matched=hit,
    )


def render_association(association: Association | None) -> str:
    if association is None:
        return ""
    relative = association.memory.relative_to(ROOT).as_posix()
    return "\n".join(
        [
            "## Optional Spontaneous Association",
            "",
            "Use only if it naturally helps. Do not interrupt, repeat, or override the current topic.",
            "",
            f"- Cue: {association.cue}",
            f"- Matched: {', '.join(association.matched)}",
            f"- Source: `{relative}`",
        ]
    )
