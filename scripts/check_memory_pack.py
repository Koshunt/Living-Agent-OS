from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT_CONFIG = ROOT / "config" / "prompt.yaml"
GENERATED = ROOT / "dist" / "agent_system_prompt.md"


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


def folder_metrics(relative_folder: str) -> dict[str, int]:
    folder = ROOT / relative_folder
    if not folder.exists():
        return {"files": 0, "bytes": 0, "nonspace_chars": 0, "words": 0}
    files = sorted(folder.rglob("*.md"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)
    return {
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "nonspace_chars": sum(1 for char in text if not char.isspace()),
        "words": len(text.split()),
    }


def main() -> int:
    failures: list[str] = []

    if not PROMPT_CONFIG.exists():
        failures.append("Missing config/prompt.yaml")
        modules: list[Path] = []
    else:
        modules = read_registered_modules()

    if not modules:
        failures.append("No modules registered in config/prompt.yaml")

    for module in modules:
        if not module.exists():
            failures.append(f"Registered module is missing: {module.relative_to(ROOT)}")
        elif module.stat().st_size == 0:
            failures.append(f"Registered module is empty: {module.relative_to(ROOT)}")

    if not GENERATED.exists():
        failures.append("Generated prompt is missing: dist/agent_system_prompt.md")
    else:
        text = GENERATED.read_text(encoding="utf-8")
        if "_Missing file:" in text:
            failures.append("Generated prompt contains missing-file markers")
        if "Continuity rule" not in text:
            failures.append("Generated prompt is missing the continuity rule")

    print("Living Agent OS Check")
    print(f"Registered modules: {len(modules)}")
    if GENERATED.exists():
        print(f"Generated prompt size: {GENERATED.stat().st_size} bytes")

    for folder in ["MemoryPack/Prompt", "MemoryPack/Persona", "MemoryPack/Memory", "MemoryPack/Examples", "MemoryPack/Knowledge", "Brain"]:
        metrics = folder_metrics(folder)
        print(
            f"{folder}: {metrics['files']} files, {metrics['bytes']} bytes, "
            f"{metrics['nonspace_chars']} non-space chars, {metrics['words']} words"
        )

    if failures:
        print("\nFAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
