from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def memory_files() -> list[Path]:
    files: list[Path] = []
    for base in (ROOT / "Brain", ROOT / "MemoryPack"):
        if base.is_dir():
            files.extend(sorted(base.rglob("*.md")))
    return files


def replace_placeholders(agent_name: str, user_name: str) -> None:
    """身份和用户名字要覆盖整个记忆库，而不只是 Identity/WelcomeHome。"""
    for path in memory_files():
        text = path.read_text(encoding="utf-8")
        if "{{AGENT_NAME}}" not in text and "{{USER_NAME}}" not in text:
            continue
        text = text.replace("{{AGENT_NAME}}", agent_name)
        text = text.replace("{{USER_NAME}}", user_name)
        path.write_text(text, encoding="utf-8")


def add_first_living_entry(agent_name: str, user_name: str) -> None:
    target = ROOT / "Brain" / "Living" / f"{date.today().year}.md"
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            f"# Living Memory {date.today().year}\n\n## Entries\n\n",
            encoding="utf-8",
        )

    entry = (
        f"\n## {date.today().isoformat()}: Initial setup\n\n"
        "Source: init_agent.py\n\n"
        f"{user_name} initialized {agent_name} from the Living Agent OS Template.\n"
    )
    text = target.read_text(encoding="utf-8")
    if "Initial setup" not in text:
        target.write_text(text.rstrip() + "\n" + entry, encoding="utf-8")


def default_tool_prefix(agent_name: str) -> str:
    slug = re.sub(r"[^a-z0-9_]+", "_", agent_name.strip().lower()).strip("_")[:32]
    return slug or "agent"


def write_bridge_config(agent_name: str, wake_raw: str, tool_prefix_raw: str) -> None:
    words = [item.strip() for item in wake_raw.replace("，", ",").replace("、", ",").split(",") if item.strip()]
    if not words:
        words = [agent_name]
    prefix = re.sub(r"[^a-z0-9_]+", "_", (tool_prefix_raw or default_tool_prefix(agent_name)).strip().lower()).strip("_")[:32] or "agent"
    config_path = ROOT / "Bridge" / "config.json"
    example_path = ROOT / "Bridge" / "config.example.json"
    data = {}
    source = config_path if config_path.is_file() else example_path
    if source.is_file():
        data = json.loads(source.read_text(encoding="utf-8"))
    data["wake_words"] = words
    data["tool_prefix"] = prefix
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wake words: {', '.join(words)}")
    print(f"Tool prefix: {prefix} (tools: {prefix}_wake, {prefix}_note_today, ...)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a Living Agent OS template.")
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--user-name", required=True)
    parser.add_argument("--wake-words", default="", help="Comma-separated wake words, e.g. 小灰,Xiaohui")
    parser.add_argument("--tool-prefix", default="", help="MCP tool prefix, e.g. xiaohui. Defaults to the agent name if it is ASCII.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    replace_placeholders(args.agent_name, args.user_name)
    add_first_living_entry(args.agent_name, args.user_name)
    write_bridge_config(args.agent_name, args.wake_words, args.tool_prefix)
    print(f"Initialized agent {args.agent_name!r} for user {args.user_name!r}.")
    print("Next: powershell -ExecutionPolicy Bypass -File scripts\\wake_agent.ps1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
