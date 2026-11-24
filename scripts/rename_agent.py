from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "Brain" / "Immutable" / "Identity.md"
CONFIG = ROOT / "Bridge" / "config.json"
CONFIG_EXAMPLE = ROOT / "Bridge" / "config.example.json"

# 只改“说明书/身份”文件；Brain/Living 与 Brain/Archive 是历史，不改写。
INSTRUCTION_GLOBS = [
    "Brain/*.md",
    "Brain/Immutable/*.md",
    "Brain/Letters/*.md",
    "MemoryPack/Persona/*.md",
    "MemoryPack/Prompt/*.md",
]


def read_identity_field(name: str) -> str:
    if not IDENTITY.is_file():
        return ""
    lines = IDENTITY.read_text(encoding="utf-8").splitlines()
    in_section = False
    for raw in lines:
        if raw.strip().lower() == f"## {name}".lower():
            in_section = True
            continue
        if in_section:
            if raw.startswith("## "):
                break
            text = raw.strip().strip("`").strip()
            if text:
                return text
    return ""


def write_identity_field(name: str, value: str) -> None:
    text = IDENTITY.read_text(encoding="utf-8")
    pattern = re.compile(rf"(##\s*{re.escape(name)}\s*\n\n)([^\n]*)", re.IGNORECASE)
    replacement = rf"\g<1>`{value}`"
    new_text, count = pattern.subn(replacement, text, count=1)
    if count == 0:
        new_text = text.rstrip() + f"\n\n## {name}\n\n`{value}`\n"
    IDENTITY.write_text(new_text, encoding="utf-8")


def instruction_files() -> list[Path]:
    files: list[Path] = []
    for pattern in INSTRUCTION_GLOBS:
        files.extend(sorted(ROOT.glob(pattern)))
    return [path for path in dict.fromkeys(files) if path.is_file()]


def replace_in_instructions(old: str, new: str, dry_run: bool) -> list[Path]:
    if not old or not new or old == new:
        return []
    changed: list[Path] = []
    for path in instruction_files():
        text = path.read_text(encoding="utf-8")
        if old not in text:
            continue
        changed.append(path)
        if not dry_run:
            path.write_text(text.replace(old, new), encoding="utf-8")
    return changed


def parse_wake_words(raw: str) -> list[str]:
    return [item.strip() for item in raw.replace("，", ",").replace("、", ",").split(",") if item.strip()]


def update_config(old_agent: str, new_agent: str, wake_raw: str, tool_prefix: str, dry_run: bool) -> None:
    source = CONFIG if CONFIG.is_file() else CONFIG_EXAMPLE
    data = json.loads(source.read_text(encoding="utf-8")) if source.is_file() else {}

    words = parse_wake_words(wake_raw) if wake_raw else list(data.get("wake_words") or [])
    if not words:
        words = [new_agent]
    elif old_agent:
        words = [new_agent if word == old_agent else word for word in words]
        if new_agent not in words:
            words.insert(0, new_agent)
    data["wake_words"] = words

    if tool_prefix:
        prefix = re.sub(r"[^a-z0-9_]+", "_", tool_prefix.strip().lower()).strip("_")[:32]
        if prefix:
            data["tool_prefix"] = prefix

    if not dry_run:
        CONFIG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def regenerate_prompt(dry_run: bool) -> None:
    if dry_run:
        return
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "update_memory.py")])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rename the companion in a Living Agent OS home.")
    parser.add_argument("--new-name", required=True, help="New companion name, e.g. 阿灰")
    parser.add_argument("--old-name", default="", help="Current name; read from Identity.md when omitted")
    parser.add_argument("--user-name", default="", help="New user display name (optional)")
    parser.add_argument("--old-user-name", default="", help="Current user name; read from Identity.md when omitted")
    parser.add_argument("--wake-words", default="", help="Comma-separated wake words; other languages welcome")
    parser.add_argument("--tool-prefix", default="", help="New MCP tool prefix, e.g. ahui")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    old_agent = args.old_name.strip() or read_identity_field("Agent Name")
    old_user = args.old_user_name.strip() or read_identity_field("User Name")
    new_agent = args.new_name.strip()
    if not old_agent:
        print("Cannot determine the current agent name. Pass --old-name.", file=sys.stderr)
        return 1

    changed = replace_in_instructions(old_agent, new_agent, args.dry_run)
    if args.user_name.strip() and old_user and args.user_name.strip() != old_user:
        changed += replace_in_instructions(old_user, args.user_name.strip(), args.dry_run)

    if not args.dry_run:
        write_identity_field("Agent Name", new_agent)
        if args.user_name.strip():
            write_identity_field("User Name", args.user_name.strip())
    update_config(old_agent, new_agent, args.wake_words, args.tool_prefix, args.dry_run)
    regenerate_prompt(args.dry_run)

    action = "Would rename" if args.dry_run else "Renamed"
    print(f"{action}: {old_agent} -> {new_agent}")
    for path in changed:
        print(f"  {path.relative_to(ROOT)}")
    print("Restart the MCP server / open a new session to load the regenerated prompt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
