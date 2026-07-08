from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
]

PRIVATE_TERMS: list[str] = []

SKIP_PARTS = {".git", "dist", "__pycache__"}


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in {".md", ".py", ".ps1", ".yaml", ".yml", ".txt", ".gitignore"} or path.name in {"LICENSE", "SECURITY.md"}:
            files.append(path)
    return files


def main() -> int:
    failures: list[str] = []
    for path in iter_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"Possible secret in {path.relative_to(ROOT)}")
                break
        for term in PRIVATE_TERMS:
            if term in text:
                failures.append(f"Private source term {term!r} in {path.relative_to(ROOT)}")

    if failures:
        print("Publish check failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Publish check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
