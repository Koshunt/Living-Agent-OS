from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
GENERATED = DIST / "agent_system_prompt.md"
MANIFEST = DIST / "agent_memory_pack_manifest.json"
ARCHIVE = DIST / "LivingAgentOS-MemoryPack.zip"

INCLUDE_ROOTS = ["MemoryPack", "Brain", "config", "docs", "scripts", "templates"]
INCLUDE_FILES = ["README.md", "SECURITY.md", "LICENSE", ".gitignore"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files() -> list[Path]:
    files: list[Path] = []
    for relative_root in INCLUDE_ROOTS:
        root = ROOT / relative_root
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                files.append(path)
    for relative_file in INCLUDE_FILES:
        path = ROOT / relative_file
        if path.exists() and path.is_file():
            files.append(path)
    if GENERATED.exists():
        files.append(GENERATED)
    return sorted(set(files), key=lambda item: item.relative_to(ROOT).as_posix())


def build_manifest(files: list[Path]) -> dict[str, object]:
    return {
        "name": "Living Agent OS Template Memory Pack",
        "version": "template-v0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "continuity_rule": "Do not invent history. Preserve continuity through recorded memory, values, corrections, and examples.",
        "generated_prompt": GENERATED.relative_to(ROOT).as_posix(),
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    files = iter_files()
    manifest = build_manifest(files)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(MANIFEST, MANIFEST.relative_to(ROOT).as_posix())
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")
    print(f"Wrote {ARCHIVE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
