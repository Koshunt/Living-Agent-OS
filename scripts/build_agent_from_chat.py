from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(description: str, command: list[str]) -> bool:
    print(f"\n{'='*50}")
    print(f"  {description}")
    print(f"{'='*50}")
    result = subprocess.run(
        command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=False,
        timeout=300,
    )
    if result.returncode != 0:
        print(f"\nFailed: {description}")
        return False
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-command pipeline: chat file → personalized agent.",
        epilog="Example: python scripts\\build_agent_from_chat.py --input chat.md --agent-name MyBot --user-name Alice",
    )
    parser.add_argument("--input", type=Path, required=True, help="Chat file: .md, .txt, or .json")
    parser.add_argument("--agent-name", required=True, help="Name for the agent")
    parser.add_argument("--user-name", required=True, help="Name for the user")
    parser.add_argument("--reset", action="store_true", help="Re-import all messages (ignore previous state)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing personalized files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.input.exists():
        print(f"Input file not found: {args.input}")
        return 1

    print(f"\nBuilding personalized agent from: {args.input}")
    print(f"Agent name: {args.agent_name}")
    print(f"User name: {args.user_name}")

    # Step 1: Import chat
    import_cmd = [
        sys.executable, "scripts/import_conversation_memory.py",
        "--input", str(args.input),
    ]
    if args.reset:
        import_cmd.append("--reset")

    if not run_step("Step 1/4: Importing chat history", import_cmd):
        return 1

    # Find the latest proposal JSON
    proposal_dir = ROOT / "workspace" / "imports" / "proposal_json"
    if not proposal_dir.exists():
        print("No proposals generated.")
        return 1

    proposal_files = sorted(proposal_dir.glob("*.json"), key=lambda p: p.name, reverse=True)
    if not proposal_files:
        print("No proposal JSON found.")
        return 1

    latest_proposal = proposal_files[0]
    print(f"  Using proposal: {latest_proposal.name}")

    # Step 2: Personalize agent files
    personalize_cmd = [
        sys.executable, "scripts/personalize_agent.py",
        "--proposal-json", str(latest_proposal),
        "--agent-name", args.agent_name,
        "--user-name", args.user_name,
    ]
    if args.force:
        personalize_cmd.append("--force")

    if not run_step("Step 2/4: Personalizing agent files", personalize_cmd):
        return 1

    # Step 3: Regenerate prompt
    if not run_step("Step 3/4: Regenerating prompt", [sys.executable, "scripts/update_memory.py"]):
        return 1

    # Step 4: Verify
    if not run_step("Step 4/4: Running verification", [sys.executable, "scripts/check_memory_pack.py"]):
        return 1

    print(f"\n{'='*50}")
    print(f"  Done! Agent '{args.agent_name}' is ready.")
    print(f"{'='*50}")
    print(f"\nGenerated prompt: dist/agent_system_prompt.md")
    print(f"\nNext steps:")
    print(f"  1. Review Brain/Immutable/ files for accuracy")
    print(f"  2. Add more memories with memory_manager.py")
    print(f"  3. Use the prompt in your model provider")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
