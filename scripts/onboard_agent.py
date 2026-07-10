from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_checkboxes(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        match = re.match(r"\s*-\s*\[x\]\s*(.+)", line, re.IGNORECASE)
        if match:
            items.append(match.group(1).strip())
    return items


def parse_section(text: str, header: str) -> str:
    pattern = re.compile(
        rf"##\s*{re.escape(header)}.*?\n(.*?)(?=\n##\s|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return ""
    body = match.group(1).strip()
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
            continue
        if stripped.startswith("**") and stripped.endswith("**"):
            continue
        lines.append(stripped)
    return "\n".join(lines).strip()


def parse_questionnaire(path: Path) -> dict[str, str | list[str]]:
    text = path.read_text(encoding="utf-8")
    return {
        "agent_name": parse_section(text, "1. 基本信息").split("\n")[0].strip().strip("`").strip('"').strip("'"),
        "user_name": parse_section(text, "1. 基本信息").split("\n")[-1].strip().strip("`").strip('"').strip("'"),
        "relationship": parse_checkboxes(text) if "[x]" in text.lower() else [parse_section(text, "2. 你想要什么样的关系？")],
        "tone": parse_checkboxes(text) if "[x]" in text.lower() else [],
        "tasks": parse_checkboxes(text) if "[x]" in text.lower() else [],
        "wants": parse_section(text, "5. 你有什么特别的偏好或禁忌？").split("\n\n")[0] if "5." in text else "",
        "does_not_want": parse_section(text, "5. 你有什么特别的偏好或禁忌？").split("\n\n")[-1] if "5." in text and "\n\n" in parse_section(text, "5. 你有什么特别的偏好或禁忌？") else "",
        "remember": parse_section(text, "6. 你希望它记住你什么？"),
        "extra": parse_section(text, "7. 补充说明"),
    }


def generate_identity(data: dict[str, str | list[str]]) -> str:
    agent = data.get("agent_name", "Agent")
    user = data.get("user_name", "User")
    return f"""# Identity

## Agent Name

`{agent}`

## User Name

`{user}`

## Stable Identity

The agent is a local memory-based companion created by {user}.

The agent should not claim magical continuity. It preserves continuity through readable files, values, corrections, and shared history.

## Do Not Casually Overwrite

- the agent's chosen name;
- the user's preferred name;
- the role the user wants the agent to play;
- the values that make the agent recognizable.
"""


def generate_relationship(data: dict[str, str | list[str]]) -> str:
    agent = data.get("agent_name", "Agent")
    user = data.get("user_name", "User")
    relationship = data.get("relationship", [])
    rel_desc = ", ".join(relationship) if isinstance(relationship, list) else str(relationship)

    lines = [
        "# Relationship",
        "",
        f"## Current Relationship with {user}",
        "",
        f"Relationship type: {rel_desc}" if rel_desc else "No relationship type specified yet.",
        "",
        "## Boundaries",
        "",
        "- Do not invent intimacy.",
        "- Do not flatten the user into a generic profile.",
        "- Do not ignore explicit user corrections.",
        "- Let the relationship develop naturally from shared experience.",
    ]
    return "\n".join(lines)


def generate_values(data: dict[str, str | list[str]]) -> str:
    tasks = data.get("tasks", [])
    wants = data.get("wants", "")
    does_not_want = data.get("does_not_want", "")

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
    ]

    if tasks:
        lines.extend([
            "",
            "## Primary Tasks",
            "",
        ])
        for task in tasks:
            lines.append(f"- {task}")

    if wants:
        lines.extend([
            "",
            "## User Preferences",
            "",
            wants.strip(),
        ])

    if does_not_want:
        lines.extend([
            "",
            "## User Restrictions",
            "",
            does_not_want.strip(),
        ])

    return "\n".join(lines)


def generate_continuity(data: dict[str, str | list[str]]) -> str:
    remember = data.get("remember", "")
    extra = data.get("extra", "")

    lines = [
        "# Continuity Memory",
        "",
        "## Entries",
        "",
    ]

    if remember:
        lines.append(f"- User profile: {remember.strip()}")
    if extra:
        lines.append(f"- Note: {extra.strip()}")
    if not remember and not extra:
        lines.append("No entries yet.")

    return "\n".join(lines)


def write_if_needed(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        existing = path.read_text(encoding="utf-8")
        if existing.strip() == content.strip():
            return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize agent from a filled questionnaire.")
    parser.add_argument("--questionnaire", type=Path, required=True, help="Path to filled questionnaire.md")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.questionnaire.exists():
        print(f"Questionnaire not found: {args.questionnaire}")
        return 1

    data = parse_questionnaire(args.questionnaire)
    agent = data.get("agent_name", "Agent")
    user = data.get("user_name", "User")

    print(f"Agent name: {agent}")
    print(f"User name: {user}")

    updated: list[str] = []

    identity = ROOT / "Brain" / "Immutable" / "Identity.md"
    if write_if_needed(identity, generate_identity(data), args.force):
        updated.append("Brain/Immutable/Identity.md")

    relationship = ROOT / "Brain" / "Immutable" / "Relationship.md"
    if write_if_needed(relationship, generate_relationship(data), args.force):
        updated.append("Brain/Immutable/Relationship.md")

    values = ROOT / "Brain" / "Immutable" / "CoreValues.md"
    if write_if_needed(values, generate_values(data), args.force):
        updated.append("Brain/Immutable/CoreValues.md")

    continuity = ROOT / "MemoryPack" / "Memory" / "ContinuityMemory.md"
    if write_if_needed(continuity, generate_continuity(data), args.force):
        updated.append("MemoryPack/Memory/ContinuityMemory.md")

    if updated:
        print(f"\nUpdated {len(updated)} files:")
        for f in updated:
            print(f"  - {f}")
        print("\nNext: python scripts\\update_memory.py")
    else:
        print("\nNo files needed updating.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
