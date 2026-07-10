from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# ── Profile parser (my_profile.md) ──

def parse_profile_sections(text: str) -> dict[str, str]:
    """Parse sections from my_profile.md by ## headers."""
    sections: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


def read_profile(path: Path) -> dict[str, str]:
    """Read my_profile.md and return relevant fields."""
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    # Strip the header block before first ##
    sections = parse_profile_sections(raw)

    # Map Chinese headers to our internal keys
    mapping = {
        "关系": "relationship",
        "说话风格": "tone",
        "主要用途": "tasks",
        "偏好": "wants",
        "禁忌": "does_not_want",
        "其他": "extra",
    }

    result: dict[str, str] = {}
    for zh, en in mapping.items():
        if zh in sections:
            val = sections[zh].strip()
            # Remove placeholder parentheses content
            if val.startswith("（") and val.endswith("）"):
                val = ""
            elif "\n（" in val:
                val = val.split("\n", 1)[-1].strip()
                if val.endswith("）"):
                    val = val[:-1].strip()
            if val:
                result[en] = val

    return result


# ── Questionnaire parser ──

def parse_questionnaire(path: Path) -> dict[str, str | list[str]]:
    """Parse the questionnaire.md file."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")

    # Extract agent/user names from section 1
    section1 = re.search(r"## 1\. 基本信息.*?(?=## 2\.|\Z)", text, re.DOTALL)
    agent_name = ""
    user_name = ""
    if section1:
        s1 = section1.group(0)
        # Find agent name (first non-empty line after ## Agent Name or similar)
        name_lines = [l.strip() for l in s1.splitlines() if l.strip() and not l.startswith("#") and not l.startswith("(") and not l.startswith("（")]
        if len(name_lines) >= 1:
            agent_name = name_lines[0].strip("`\"' ")
        if len(name_lines) >= 2:
            user_name = name_lines[1].strip("`\"' ")

    # Extract checked items
    def checked_items(text: str, section: str) -> list[str]:
        pattern = re.compile(rf"##\s*{re.escape(section)}.*?(?=##\s|\Z)", re.DOTALL | re.IGNORECASE)
        m = pattern.search(text)
        if not m:
            return []
        items = []
        for line in m.group(0).splitlines():
            cm = re.match(r"\s*-\s*\[x\]\s*(.+)", line, re.IGNORECASE)
            if cm:
                items.append(cm.group(1).strip())
        return items

    # Extract free text sections
    def free_text(text: str, section: str) -> str:
        pattern = re.compile(rf"##\s*{re.escape(section)}.*?(?=##\s|\Z)", re.DOTALL | re.IGNORECASE)
        m = pattern.search(text)
        if not m:
            return ""
        body = m.group(0)
        lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("- ["):
                continue
            if stripped.startswith("**") and stripped.endswith("**"):
                continue
            if stripped.startswith("(") or stripped.startswith("（"):
                continue
            lines.append(stripped)
        return "\n".join(lines).strip()

    return {
        "agent_name": agent_name,
        "user_name": user_name,
        "relationship": checked_items(text, "2. 你想要什么样的关系？"),
        "tone": checked_items(text, "3. 你希望它怎么说话？"),
        "tasks": checked_items(text, "4. 你主要想让它帮你做什么？"),
        "wants": free_text(text, "5. 你有什么特别的偏好或禁忌？"),
        "does_not_want": "",
        "remember": free_text(text, "6. 你希望它记住你什么？"),
        "extra": free_text(text, "7. 补充说明"),
    }


# ── Chat history parser (reused from old script) ──

def detect_chat_format(path: Path) -> str:
    text = path.read_text(encoding="utf-8")[:5000]
    if re.search(r'"messages"\s*:\s*\[', text):
        return "json"
    if re.search(r"^\d{4}[-/]\d{2}[-/]\d{2}", text, re.MULTILINE):
        return "md_timestamp"
    if re.search(r"^(Human|Assistant|User|AI|System)\s*[:：]", text, re.MULTILINE):
        return "md_role"
    if re.search(r"^\*\*?(Human|Assistant|User|AI)\*?\*?\s*[:：]", text, re.MULTILINE):
        return "md_role"
    return "md_plain"


def parse_md_plain(path: Path) -> list[tuple[str, str]]:
    return [("unknown", line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_md_role(path: Path) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    current_role: str | None = None
    current_lines: list[str] = []
    role_pattern = re.compile(
        r"^\*?\*?(Human|User|Assistant|AI|System|小灰|Nathaniel)\*?\*?\s*[:：]",
        re.IGNORECASE,
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        m = role_pattern.match(line.strip())
        if m:
            if current_role:
                messages.append((current_role, "\n".join(current_lines).strip()))
            raw_role = m.group(1).lower()
            current_role = "user" if raw_role in ("human", "user", "nathaniel") else "assistant"
            content = role_pattern.sub("", line.strip()).strip()
            current_lines = [content] if content else []
        elif current_role and line.strip():
            current_lines.append(line.strip())
    if current_role:
        messages.append((current_role, "\n".join(current_lines).strip()))
    return messages


def parse_md_timestamp(path: Path) -> list[tuple[str, str]]:
    messages: list[tuple[str, str]] = []
    current_role: str | None = None
    current_lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        ts_match = re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}\s+(Human|User|Assistant|AI|System)\s*[:：]", line.strip(), re.IGNORECASE)
        if ts_match:
            if current_role:
                messages.append((current_role, "\n".join(current_lines).strip()))
            raw_role = ts_match.group(1).lower()
            current_role = "user" if raw_role in ("human", "user") else "assistant"
            content = re.sub(r"^\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}\s+\w+\s*[:：]\s*", "", line.strip()).strip()
            current_lines = [content] if content else []
        elif current_role and line.strip():
            current_lines.append(line.strip())
    if current_role:
        messages.append((current_role, "\n".join(current_lines).strip()))
    return messages


def parse_json(path: Path) -> list[tuple[str, str]]:
    import json
    data = json.loads(path.read_text(encoding="utf-8"))
    messages = data if isinstance(data, list) else data.get("messages", [])
    result: list[tuple[str, str]] = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"
            )
        if role and content:
            result.append((role, content.strip()))
    return result


def import_chat(path: Path) -> list[tuple[str, str]]:
    fmt = detect_chat_format(path)
    parsers = {"json": parse_json, "md_timestamp": parse_md_timestamp, "md_role": parse_md_role, "md_plain": parse_md_plain}
    return parsers[fmt](path)


def extract_preferences_from_chat(messages: list[tuple[str, str]], agent_name: str) -> dict[str, list[str]]:
    user_msgs = " ".join(content for role, content in messages if role == "user")

    wants: list[str] = []
    if any(w in user_msgs for w in ["简洁", "简短", "别废话", "short", "concise"]):
        wants.append("Prefer concise replies")
    if any(w in user_msgs for w in ["详细", "完整", "explain", "详细说"]):
        wants.append("Give detailed explanations")
    if any(w in user_msgs for w in ["代码", "code", "示例", "example"]):
        wants.append("Include code examples for technical questions")

    return {"wants": wants}


# ── Merge all sources ──

def merge_sources(
    profile: dict[str, str],
    questionnaire: dict[str, str | list[str]],
    chat_prefs: dict[str, list[str]],
    agent_name: str,
    user_name: str,
) -> dict[str, str | list[str]]:
    """Merge data from all 3 sources. Priority: profile > questionnaire > chat."""

    result: dict[str, str | list[str]] = {
        "agent_name": agent_name or str(questionnaire.get("agent_name", "")) or "Agent",
        "user_name": user_name or str(questionnaire.get("user_name", "")) or "User",
        "relationship": [],
        "tone": [],
        "tasks": [],
        "wants": "",
        "does_not_want": "",
        "remember": "",
        "extra": "",
    }

    # Relationship: profile > questionnaire
    if profile.get("relationship"):
        result["relationship"] = [profile["relationship"]]
    elif questionnaire.get("relationship"):
        result["relationship"] = questionnaire["relationship"]

    # Tone: profile > questionnaire
    if profile.get("tone"):
        result["tone"] = [profile["tone"]]
    elif questionnaire.get("tone"):
        result["tone"] = questionnaire["tone"]

    # Tasks: profile > questionnaire
    if profile.get("tasks"):
        result["tasks"] = [profile["tasks"]]
    elif questionnaire.get("tasks"):
        result["tasks"] = questionnaire["tasks"]

    # Wants: profile > questionnaire > chat
    if profile.get("wants"):
        result["wants"] = profile["wants"]
    elif questionnaire.get("wants"):
        result["wants"] = str(questionnaire["wants"])
    elif chat_prefs.get("wants"):
        result["wants"] = ", ".join(chat_prefs["wants"])

    # Does not want: profile > questionnaire
    if profile.get("does_not_want"):
        result["does_not_want"] = profile["does_not_want"]

    # Remember: profile > questionnaire
    if profile.get("extra"):
        result["remember"] = profile["extra"]
    elif questionnaire.get("remember"):
        result["remember"] = str(questionnaire["remember"])

    return result


# ── Generate files ──

def generate_identity(agent: str, user: str) -> str:
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


def generate_relationship(agent: str, user: str, data: dict[str, str | list[str]]) -> str:
    rel = data.get("relationship", [])
    rel_desc = ", ".join(rel) if isinstance(rel, list) else str(rel)
    lines = [
        "# Relationship",
        "",
        f"## Current Relationship with {user}",
        "",
        f"Relationship type: {rel_desc}" if rel_desc else "No relationship type specified yet. Let it develop through conversation.",
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
    tone = data.get("tone", [])
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

    if tone:
        lines.extend(["", "## Communication Style", ""])
        for t in tone:
            lines.append(f"- {t}")

    if tasks:
        lines.extend(["", "## Primary Tasks", ""])
        for task in tasks:
            lines.append(f"- {task}")

    if wants:
        lines.extend(["", "## User Preferences", "", wants.strip()])

    if does_not_want:
        lines.extend(["", "## User Restrictions", "", does_not_want.strip()])

    return "\n".join(lines)


def generate_continuity(data: dict[str, str | list[str]]) -> str:
    remember = data.get("remember", "")
    lines = ["# Continuity Memory", "", "## Entries", ""]
    if remember:
        lines.append(f"- {remember.strip()}")
    else:
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


# ── Main ──

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build agent from all available sources (profile, questionnaire, chat)."
    )
    parser.add_argument("--chat", type=Path, default=None, help="Chat history file (md/json)")
    parser.add_argument("--profile", type=Path, default=None, help="my_profile.md file")
    parser.add_argument("--questionnaire", type=Path, default=None, help="Filled questionnaire.md")
    parser.add_argument("--agent-name", default="", help="Agent name (overrides other sources)")
    parser.add_argument("--user-name", default="", help="User name (overrides other sources)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Auto-detect files in ROOT
    profile_path = args.profile or ROOT / "my_profile.md"
    questionnaire_path = args.questionnaire or ROOT / "templates" / "questionnaire.md"

    profile = read_profile(profile_path)
    questionnaire = parse_questionnaire(questionnaire_path) if questionnaire_path.exists() else {}

    # Chat import
    chat_prefs: dict[str, list[str]] = {}
    if args.chat and args.chat.exists():
        messages = import_chat(args.chat)
        agent_for_chat = args.agent_name or str(questionnaire.get("agent_name", "Agent"))
        chat_prefs = extract_preferences_from_chat(messages, agent_for_chat)
        print(f"Chat: imported {len(messages)} messages")
    else:
        print("Chat: none")

    # Profile
    if profile:
        print(f"Profile: loaded ({', '.join(profile.keys())})")
    else:
        print("Profile: none")

    # Questionnaire
    if questionnaire:
        print(f"Questionnaire: loaded")
    else:
        print("Questionnaire: none")

    # Merge
    data = merge_sources(profile, questionnaire, chat_prefs, args.agent_name, args.user_name)
    agent = data["agent_name"]
    user = data["user_name"]

    print(f"\nAgent: {agent}")
    print(f"User: {user}")

    # Write files
    updated: list[str] = []

    identity = ROOT / "Brain" / "Immutable" / "Identity.md"
    if write_if_needed(identity, generate_identity(agent, user), args.force):
        updated.append("Brain/Immutable/Identity.md")

    relationship = ROOT / "Brain" / "Immutable" / "Relationship.md"
    if write_if_needed(relationship, generate_relationship(agent, user, data), args.force):
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
