from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_CONFIG = ROOT / "config" / "prompt.yaml"
OUTPUT = ROOT / "dist" / "agent_system_prompt.md"


def config_value(key: str, default: str) -> str:
    prefix = f"{key}:"
    for raw_line in PROMPT_CONFIG.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return default


def read_registered_modules() -> list[Path]:
    modules: list[Path] = []
    in_modules = False

    for raw_line in PROMPT_CONFIG.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()

        if stripped == "modules:":
            in_modules = True
            continue

        if not in_modules:
            continue

        if stripped.startswith("- "):
            modules.append(ROOT / stripped[2:].strip())
        elif stripped and not raw_line.startswith(" "):
            break

    return modules


def section_title(path: Path) -> str:
    relative = path.relative_to(ROOT).with_suffix("")
    return " / ".join(relative.parts)


def read_section(path: Path) -> str:
    if not path.exists():
        return f"_Missing file: {path.relative_to(ROOT)}_"
    return path.read_text(encoding="utf-8").strip()


def build_prompt() -> str:
    title = config_value("title", "Living Agent OS Memory Pack")
    parts = [
        f"# {title}",
        "",
        "This file is generated from local Markdown memory files.",
        "Use it as a System Prompt or long-context memory pack.",
        "",
        "Continuity rule: do not invent history. Preserve continuity through recorded memory, values, corrections, and examples.",
        "",
    ]

    for path in read_registered_modules():
        parts.extend(
            [
                "---",
                "",
                f"## {section_title(path)}",
                "",
                read_section(path),
                "",
            ]
        )

    return "\n".join(parts).strip() + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_prompt(), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
