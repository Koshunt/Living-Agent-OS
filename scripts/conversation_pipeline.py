from __future__ import annotations

import argparse
from pathlib import Path

from retriever import ROOT, retrieve_paths


def build_context(message: str) -> str:
    parts = [
        "# Living Agent OS Conversation Context",
        "",
        "Current user message:",
        "",
        message,
        "",
        "Selected memory files:",
        "",
    ]
    for path in retrieve_paths(message):
        parts.extend(
            [
                "---",
                "",
                f"## {path.relative_to(ROOT).as_posix()}",
                "",
                path.read_text(encoding="utf-8").strip(),
                "",
            ]
        )
    return "\n".join(parts).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a small context bundle for the current message.")
    parser.add_argument("message", nargs="*", help="Current user message.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "conversation_context.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    message = " ".join(args.message).strip()
    if not message:
        print("Provide a current user message.")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_context(message), encoding="utf-8")
    print(f"Wrote {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
