from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PARTS = {"dist", "__pycache__", ".pytest_cache", "secrets", "local"}
BLOCKED_SUFFIXES = {".env", ".key", ".pem", ".pfx", ".p12", ".pyc", ".zip", ".log"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY"),
]
TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".ps1", ".yml", ".yaml", ".toml", ".ini", ".cfg"}


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    failures: list[str] = []
    try:
        files = set(git_lines("ls-files")) | set(git_lines("diff", "--cached", "--name-only"))
    except subprocess.CalledProcessError as error:
        print(error.stderr)
        return 2
    for relative in sorted(files):
        path = ROOT / relative
        parts = set(Path(relative).parts)
        if parts & BLOCKED_PARTS or path.suffix.lower() in BLOCKED_SUFFIXES:
            failures.append(f"blocked path: {relative}")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in SECRET_PATTERNS):
                failures.append(f"possible secret at {relative}:{line_number}")
    if failures:
        print("Agent OS pre-push security check failed.")
        print("\n".join(f"- {item}" for item in failures))
        return 1
    print("Agent OS pre-push security check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
