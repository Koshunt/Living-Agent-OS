from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


FILES_TO_REPLACE = [
    ROOT / "Brain" / "Immutable" / "Identity.md",
    ROOT / "Brain" / "Letters" / "WelcomeHome.md",
]


def replace_placeholders(agent_name: str, user_name: str) -> None:
    for path in FILES_TO_REPLACE:
        text = path.read_text(encoding="utf-8")
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


def set_wake_words(agent_name: str, raw: str) -> None:
    words = [item.strip() for item in raw.replace("，", ",").replace("、", ",").split(",") if item.strip()]
    if not words:
        words = [agent_name]
    config_path = ROOT / "Bridge" / "config.json"
    example_path = ROOT / "Bridge" / "config.example.json"
    data = {}
    source = config_path if config_path.is_file() else example_path
    if source.is_file():
        data = json.loads(source.read_text(encoding="utf-8"))
    data["wake_words"] = words
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wake words: {', '.join(words)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a Living Agent OS template.")
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--user-name", required=True)
    parser.add_argument("--wake-words", default="", help="Comma-separated wake words, e.g. 小灰,Xiaohui")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    replace_placeholders(args.agent_name, args.user_name)
    add_first_living_entry(args.agent_name, args.user_name)
    set_wake_words(args.agent_name, args.wake_words)
    print(f"Initialized agent {args.agent_name!r} for user {args.user_name!r}.")
    print("Next: powershell -ExecutionPolicy Bypass -File scripts\\wake_agent.ps1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
