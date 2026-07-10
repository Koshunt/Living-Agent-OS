from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.]{20,}"),
    re.compile(r"(?i)aws[_-]?(access[_-]?key|secret[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{20,}"),
    re.compile(r"(?i)mysql://[^\s]+:[^\s]+@[^\s]+"),
    re.compile(r"(?i)postgres(ql)?://[^\s]+:[^\s]+@[^\s]+"),
    re.compile(r"(?i)mongodb(\+srv)?://[^\s]+:[^\s]+@[^\s]+"),
    re.compile(r"(?i)redis://[^\s]+:[^\s]+@[^\s]+"),
]

PRIVATE_TERMS: list[str] = [
    "Nathaniel",
    "Koshunt",
    "D:\\WZY",
    "D:/WZY",
]

SKIP_PARTS = {".git", "dist", "__pycache__", "node_modules"}


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in {".md", ".py", ".ps1", ".yaml", ".yml", ".txt", ".json", ".gitignore"} or path.name in {"LICENSE", "SECURITY.md"}:
            files.append(path)
    return files


def scan_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(ROOT)

    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            issues.append(f"  Possible secret: {rel}")
            break

    for term in PRIVATE_TERMS:
        if term in text:
            issues.append(f"  Personal info: {rel} (contains '{term}')")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check for secrets and personal info before publishing.")
    parser.add_argument("--skip", action="store_true", help="Skip this check")
    parser.add_argument("--exclude-personal", action="store_true", help="Only check for secrets, skip personal info check")
    args = parser.parse_args()

    if args.skip:
        print("Publish check skipped by user.")
        return 0

    all_issues: list[str] = []
    for path in iter_text_files():
        issues = scan_file(path)
        if args.exclude_personal:
            issues = [i for i in issues if "Personal info" not in i]
        all_issues.extend(issues)

    if all_issues:
        print("Publish check found issues:")
        for issue in all_issues:
            print(issue)
        print("\nTo skip this check: python scripts\\check_before_publish.py --skip")
        print("To ignore personal info: python scripts\\check_before_publish.py --exclude-personal")
        return 1

    print("Publish check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
