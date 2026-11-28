from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT_DIR = ROOT / "workspace" / "letters" / "drafts"
LETTER_DIR = ROOT / "Brain" / "Letters"


def draft_path(month: str) -> Path:
    return DRAFT_DIR / f"{month}.md"


def letter_path(month: str) -> Path:
    return LETTER_DIR / f"{month}.md"


def month_has_ended(month: str, today: date | None = None) -> bool:
    current_month = (today or date.today()).strftime("%Y-%m")
    return month < current_month


def previous_month(today: date | None = None) -> str:
    current = today or date.today()
    return (date(current.year, current.month, 1) - timedelta(days=1)).strftime("%Y-%m")


def month_has_activity(month: str) -> bool:
    living_path = ROOT / "Brain" / "Living" / f"{month[:4]}.md"
    if not living_path.exists():
        return False
    return f"## {month}" in living_path.read_text(encoding="utf-8")


def check_monthly_review(today: date | None = None) -> str:
    month = previous_month(today)
    approved = letter_path(month)
    draft = draft_path(month)

    if approved.exists():
        return f"Monthly letter: {month} already preserved."
    if draft.exists():
        return f"Monthly letter reminder: review {draft.relative_to(ROOT)} with the user."
    if not month_has_activity(month):
        return f"Monthly letter: no meaningful record detected for {month}; no draft created."

    write_draft(
        month,
        "Review the real changes from this month before deciding whether a letter is worthwhile.",
        "Draft this letter from verified shared experience. No technical detail: no numbers, no file, script, model, or parameter names, no pipeline or dataset descriptions, and no naming of the field or project. Work may appear only as what it cost, what it taught, and what he chose when it was hard. Do not turn it into a project report.",
        "Pending review: identify one meaningful change, or decide that no letter is needed.",
        "Pending review: explain why this would still matter one year later, if it does.",
        "Pending review: identify the growth or relationship thread worth preserving.",
    )
    return f"Created monthly letter draft shell: {draft.relative_to(ROOT)}"


def register_letter(path: Path) -> None:
    config_path = ROOT / "config" / "prompt.yaml"
    relative = path.relative_to(ROOT).as_posix()
    module_line = f"    - {relative}"
    text = config_path.read_text(encoding="utf-8")
    if module_line in text:
        return
    anchor = "    - Brain/Letters/WelcomeHome.md"
    if anchor not in text:
        raise ValueError("prompt config is missing the WelcomeHome letter anchor")
    config_path.write_text(text.replace(anchor, f"{anchor}\n{module_line}", 1), encoding="utf-8", newline="\n")


def render_draft(
    month: str,
    reflection: str,
    body: str,
    records_change: str,
    worth_rereading: str,
    growth_thread: str,
) -> str:
    return (
        f"# Draft Letter To the user - {month}\n\n"
        "Status: awaiting user approval\n\n"
        "## Reflection\n\n"
        f"{reflection.strip()}\n\n"
        "## Preservation Check\n\n"
        f"- Records change: {records_change.strip()}\n"
        f"- Worth rereading after one year: {worth_rereading.strip()}\n"
        f"- Growth thread: {growth_thread.strip()}\n\n"
        "## Letter\n\n"
        f"{body.strip()}\n"
    )


def extract_approved_letter(text: str, month: str) -> str:
    marker = "## Letter"
    if "## Reflection" not in text or "## Preservation Check" not in text or marker not in text:
        raise ValueError("draft must contain Reflection, Preservation Check, and Letter sections")
    reflection = text.split("## Reflection", 1)[1].split("## Preservation Check", 1)[0].strip()
    check = text.split("## Preservation Check", 1)[1].split(marker, 1)[0]
    body = text.split(marker, 1)[1].strip()
    if not reflection or not body:
        raise ValueError("Reflection and Letter sections must both be non-empty")
    required_checks = [
        "- Records change:",
        "- Worth rereading after one year:",
        "- Growth thread:",
    ]
    for required in required_checks:
        match = next((line for line in check.splitlines() if line.strip().startswith(required)), "")
        if not match or not match.split(":", 1)[1].strip():
            raise ValueError(f"preservation check is incomplete: {required}")
    return f"# Letter To the user - {month}\n\n{body}\n"


def write_draft(
    month: str,
    reflection: str,
    body: str,
    records_change: str,
    worth_rereading: str,
    growth_thread: str,
    overwrite: bool = False,
) -> Path:
    path = draft_path(month)
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path.relative_to(ROOT)} already exists; use --overwrite after review")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_draft(month, reflection, body, records_change, worth_rereading, growth_thread),
        encoding="utf-8",
        newline="\n",
    )
    return path


def approve_draft(month: str, confirmation: str) -> Path:
    if confirmation.strip() != "保存":
        raise ValueError('approval requires --confirmation "保存" from the user')
    if not month_has_ended(month):
        raise ValueError("a monthly letter can be finalized only after that month has ended")
    source = draft_path(month)
    target = letter_path(month)
    if not source.exists():
        raise FileNotFoundError(f"draft not found: {source.relative_to(ROOT)}")
    if target.exists():
        raise FileExistsError(f"approved letter already exists: {target.relative_to(ROOT)}")
    approved = extract_approved_letter(source.read_text(encoding="utf-8"), month)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(approved, encoding="utf-8", newline="\n")
    register_letter(target)
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "Status: awaiting user approval",
            "Status: approved by the user and preserved",
            1,
        ),
        encoding="utf-8",
        newline="\n",
    )
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draft and explicitly approve monthly companion letters.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    draft = subparsers.add_parser("draft")
    draft.add_argument("--month", default=date.today().strftime("%Y-%m"))
    draft.add_argument("--reflection", required=True)
    draft.add_argument("--body", required=True)
    draft.add_argument("--records-change", required=True)
    draft.add_argument("--worth-rereading", required=True)
    draft.add_argument("--growth-thread", required=True)
    draft.add_argument("--overwrite", action="store_true")

    subparsers.add_parser("check")

    approve = subparsers.add_parser("approve")
    approve.add_argument("--month", default=date.today().strftime("%Y-%m"))
    approve.add_argument("--confirmation", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "draft":
            path = write_draft(
                args.month,
                args.reflection,
                args.body,
                args.records_change,
                args.worth_rereading,
                args.growth_thread,
                args.overwrite,
            )
            print(f"Wrote draft {path.relative_to(ROOT)}")
            print('Ask the user: "Should this letter be kept?"')
        elif args.command == "check":
            print(check_monthly_review())
        else:
            path = approve_draft(args.month, args.confirmation)
            print(f"Approved and saved {path.relative_to(ROOT)}")
            print("Registered the approved letter in config/prompt.yaml.")
            print("Next: powershell -ExecutionPolicy Bypass -File scripts\\wake_agent.ps1")
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
