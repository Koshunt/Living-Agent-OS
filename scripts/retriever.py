from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CORE_FILES = [
    "Brain/Immutable/Identity.md",
    "Brain/Immutable/Relationship.md",
    "Brain/Immutable/CoreValues.md",
    "MemoryPack/Persona/Voice.md",
    "MemoryPack/Persona/DialoguePrinciples.md",
]

TOPIC_FILES = {
    "work": ["MemoryPack/Knowledge/DomainKnowledge.md", "MemoryPack/Memory/DecisionMemory.md"],
    "memory": ["MemoryPack/Memory/ContinuityMemory.md", "MemoryPack/Memory/CorrectionLog.md"],
    "daily": ["Brain/Living/2026.md", "MemoryPack/Examples/StyleAnchors.md"],
}

KEYWORDS = {
    "work": ["work", "project", "code", "paper", "study", "job", "debug"],
    "memory": ["remember", "memory", "correction", "change", "store"],
    "daily": ["tired", "happy", "sad", "today", "home", "talk"],
}


def infer_topics(message: str) -> list[str]:
    lower = message.lower()
    topics: list[str] = []
    for topic, keywords in KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            topics.append(topic)
    return topics or ["daily"]


def retrieve_paths(message: str) -> list[Path]:
    paths = [ROOT / item for item in CORE_FILES]
    for topic in infer_topics(message):
        paths.extend(ROOT / item for item in TOPIC_FILES.get(topic, []))

    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in paths:
        if path not in seen and path.exists():
            seen.add(path)
            ordered.append(path)
    return ordered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select relevant memory files for a message.")
    parser.add_argument("message", nargs="*", help="Current user message.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    message = " ".join(args.message).strip()
    for path in retrieve_paths(message):
        print(path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
