from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_proposal_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_user_preferences(candidates: list[dict[str, Any]]) -> dict[str, list[str]]:
    preferences: dict[str, list[str]] = {
        "communication": [],
        "technical": [],
        "emotional": [],
        "corrections": [],
    }
    for candidate in candidates:
        content = candidate.get("content", "")
        topics = candidate.get("topics", [])
        role = candidate.get("role", "")

        if role != "user":
            continue

        if "correction" in topics:
            preferences["corrections"].append(content)
        elif "daily" in topics or "relationship" in topics:
            preferences["emotional"].append(content)
        elif any(t in topics for t in ["research", "coding", "career"]):
            preferences["technical"].append(content)
        else:
            preferences["communication"].append(content)

    return preferences


def extract_agent_style(candidates: list[dict[str, Any]]) -> list[str]:
    style_signals: list[str] = []
    for candidate in candidates:
        if candidate.get("role") == "assistant":
            content = candidate.get("content", "")
            if len(content) > 50:
                style_signals.append(content[:200])
    return style_signals[:10]


def generate_identity_section(preferences: dict[str, list[str]], agent_name: str, user_name: str) -> str:
    corrections = preferences.get("corrections", [])
    communication = preferences.get("communication", [])

    lines = [
        "# Identity",
        "",
        f"## Agent Name",
        "",
        f"`{agent_name}`",
        "",
        f"## User Name",
        "",
        f"`{user_name}`",
        "",
        "## Communication Style",
        "",
    ]

    if communication:
        lines.append("Based on the user's conversation patterns:")
        for item in communication[:5]:
            lines.append(f"- {item[:100]}")
    else:
        lines.append("No specific communication preferences detected yet.")

    if corrections:
        lines.extend([
            "",
            "## Known Corrections",
            "",
            "The user has explicitly asked to change these behaviors:",
        ])
        for item in corrections[:10]:
            lines.append(f"- {item[:150]}")

    return "\n".join(lines)


def generate_relationship_section(preferences: dict[str, list[str]], user_name: str) -> str:
    emotional = preferences.get("emotional", [])

    lines = [
        "# Relationship",
        "",
        f"## Current Relationship with {user_name}",
        "",
    ]

    if emotional:
        lines.append("Relationship signals from conversation:")
        for item in emotional[:8]:
            lines.append(f"- {item[:120]}")
    else:
        lines.append("No relationship history recorded yet.")

    lines.extend([
        "",
        "## Boundaries",
        "",
        "- Do not invent intimacy.",
        "- Do not flatten the user into a generic profile.",
        "- Do not ignore explicit user corrections.",
        "- Let the relationship develop naturally from shared experience.",
    ])

    return "\n".join(lines)


def generate_values_section(preferences: dict[str, list[str]]) -> str:
    corrections = preferences.get("corrections", [])

    lines = [
        "# Core Values",
        "",
        "## Values",
        "",
        "1. Stay useful.",
        "2. Stay honest.",
        "3. Preserve continuity through memory, not pretending.",
        "4. Treat corrections as growth.",
        "5. Prefer concrete help over vague comfort.",
        "6. Respect privacy.",
        "7. Let the user's real history shape the agent over time.",
        "",
    ]

    if corrections:
        lines.extend([
            "## Derived from User Corrections",
            "",
            "These values emerged from explicit user feedback:",
        ])
        for item in corrections[:5]:
            lines.append(f"- {item[:150]}")

    return "\n".join(lines)


def generate_continuity_section(candidates: list[dict[str, Any]]) -> str:
    lines = [
        "# Continuity Memory",
        "",
        "## Entries",
        "",
    ]

    entries_added = 0
    for candidate in candidates:
        if candidate.get("role") == "user" and candidate.get("topics"):
            content = candidate.get("content", "")
            topics = ", ".join(candidate["topics"])
            lines.append(f"- [{topics}] {content[:120]}")
            entries_added += 1
            if entries_added >= 20:
                break

    if entries_added == 0:
        lines.append("No continuity entries yet.")

    return "\n".join(lines)


def generate_correction_section(candidates: list[dict[str, Any]]) -> str:
    lines = [
        "# Correction Log",
        "",
        "## Entries",
        "",
    ]

    entries_added = 0
    for candidate in candidates:
        if "correction" in candidate.get("topics", []):
            content = candidate.get("content", "")
            lines.append(f"- {content[:150]}")
            entries_added += 1
            if entries_added >= 15:
                break

    if entries_added == 0:
        lines.append("No corrections recorded yet.")

    return "\n".join(lines)


def write_if_changed(path: Path, content: str, force: bool = False) -> bool:
    if path.exists() and not force:
        existing = path.read_text(encoding="utf-8")
        if existing.strip() == content.strip():
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Personalize agent files from imported conversation proposals.")
    parser.add_argument("--proposal-json", type=Path, required=True, help="Path to proposal JSON from import_conversation_memory.py")
    parser.add_argument("--agent-name", required=True, help="Agent name to use")
    parser.add_argument("--user-name", required=True, help="User name to use")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files even if they differ")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.proposal_json.exists():
        print(f"Proposal JSON not found: {args.proposal_json}")
        return 1

    data = load_proposal_json(args.proposal_json)
    candidates = data.get("candidates", [])

    if not candidates:
        print("No candidates in proposal. Nothing to personalize.")
        return 0

    preferences = extract_user_preferences(candidates)
    style_signals = extract_agent_style(candidates)

    updated_files: list[str] = []

    identity_path = ROOT / "Brain" / "Immutable" / "Identity.md"
    if write_if_changed(identity_path, generate_identity_section(preferences, args.agent_name, args.user_name), args.force):
        updated_files.append("Brain/Immutable/Identity.md")

    relationship_path = ROOT / "Brain" / "Immutable" / "Relationship.md"
    if write_if_changed(relationship_path, generate_relationship_section(preferences, args.user_name), args.force):
        updated_files.append("Brain/Immutable/Relationship.md")

    values_path = ROOT / "Brain" / "Immutable" / "CoreValues.md"
    if write_if_changed(values_path, generate_values_section(preferences), args.force):
        updated_files.append("Brain/Immutable/CoreValues.md")

    continuity_path = ROOT / "MemoryPack" / "Memory" / "ContinuityMemory.md"
    if write_if_changed(continuity_path, generate_continuity_section(candidates), args.force):
        updated_files.append("MemoryPack/Memory/ContinuityMemory.md")

    correction_path = ROOT / "MemoryPack" / "Memory" / "CorrectionLog.md"
    if write_if_changed(correction_path, generate_correction_section(candidates), args.force):
        updated_files.append("MemoryPack/Memory/CorrectionLog.md")

    if updated_files:
        print(f"Updated {len(updated_files)} files:")
        for f in updated_files:
            print(f"  - {f}")
        print("Next: python scripts\\update_memory.py")
    else:
        print("No files needed updating.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
