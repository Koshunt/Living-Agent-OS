from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(label: str, args: list[str]) -> None:
    print(f"\n[{label}] {' '.join(args)}")
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    print("Living Agent OS wake sequence")
    print(f"Project: {ROOT}")
    run("generate", [PYTHON, "scripts/update_memory.py"])
    run("check", [PYTHON, "scripts/check_memory_pack.py"])
    output = ROOT / "dist" / "agent_system_prompt.md"
    print("\nWake file ready:")
    print(output)
    print("\nUse this file as a System Prompt or long-context memory pack.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
