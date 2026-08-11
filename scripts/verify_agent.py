from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> int:
    result = subprocess.run(command, cwd=ROOT, check=False)
    return result.returncode


def main() -> int:
    checks = [
        [sys.executable, "scripts/check_memory_pack.py"],
        [sys.executable, "-m", "compileall", "-q", "Bridge"],
        [sys.executable, "-m", "unittest", "discover", "-s", "Bridge", "-p", "test_*.py"],
    ]
    for command in checks:
        if run(command) != 0:
            return 1
    print("Agent OS verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
