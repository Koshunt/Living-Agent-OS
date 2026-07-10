from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


BRIDGE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BRIDGE_DIR / "config.json"


def _load_config() -> dict:
    if CONFIG_PATH.is_file():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


CONFIG = _load_config()

REQUIRED_PATHS = (
    "Brain/BootProtocol.md",
    "config/prompt.yaml",
    "scripts/update_memory.py",
)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def resolve_home(raw: str | None = None) -> Path:
    configured = raw or os.environ.get("AGENT_HOME")
    if not configured:
        configured = CONFIG.get("agent_home")
    if not configured:
        raise ValueError(
            "agent_home is not set. Configure it in config.json or set the AGENT_HOME environment variable."
        )
    home = Path(configured).expanduser().resolve()
    missing = [relative for relative in REQUIRED_PATHS if not (home / relative).is_file()]
    if missing:
        raise ValueError(
            f"agent_home is not a valid Agent OS repository: {home}. "
            f"Missing: {', '.join(missing)}"
        )
    return home


def safe_path(home: Path, relative: str) -> Path:
    candidate = (home / relative).resolve()
    try:
        candidate.relative_to(home)
    except ValueError as error:
        raise ValueError("Path escapes agent_home") from error
    return candidate


def run_command(command: list[str], cwd: Path, timeout: int = 120) -> CommandResult:
    result = subprocess.run(
        command,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        shell=False,
    )
    return CommandResult(result.returncode, result.stdout.strip(), result.stderr.strip())


def run_python(home: Path, script: str, *args: str, timeout: int = 120) -> CommandResult:
    script_path = safe_path(home, f"scripts/{script}")
    if not script_path.is_file():
        raise FileNotFoundError(f"Agent OS script not found: {script}")
    return run_command([sys.executable, str(script_path), *args], cwd=home, timeout=timeout)


def git_result(home: Path, *args: str, timeout: int = 120) -> CommandResult:
    return run_command(["git", "-C", str(home), *args], cwd=home, timeout=timeout)


def git_state(home: Path) -> dict[str, Any]:
    branch = git_result(home, "branch", "--show-current")
    status = git_result(home, "status", "--porcelain")
    remote = git_result(home, "remote", "get-url", "origin")
    return {
        "branch": branch.stdout or "(detached)",
        "clean": not bool(status.stdout),
        "changed_files": status.stdout.splitlines()[:50],
        "origin_configured": remote.returncode == 0,
    }


def sync_git(home: Path, fetch: bool = True, pull: bool = True) -> dict[str, Any]:
    before = git_state(home)
    result: dict[str, Any] = {
        "before": before,
        "fetch": "skipped",
        "pull": "skipped",
        "ahead": None,
        "behind": None,
    }
    if not before["origin_configured"]:
        result["message"] = "No origin remote is configured."
        return result

    if fetch:
        fetched = git_result(home, "fetch", "origin", "main", timeout=180)
        result["fetch"] = "ok" if fetched.returncode == 0 else "failed"
        if fetched.returncode != 0:
            result["message"] = fetched.stderr or "git fetch failed"
            return result

    divergence = git_result(home, "rev-list", "--left-right", "--count", "HEAD...origin/main")
    if divergence.returncode != 0:
        result["message"] = divergence.stderr or "Could not compare HEAD with origin/main."
        return result
    ahead, behind = (int(value) for value in divergence.stdout.split())
    result["ahead"] = ahead
    result["behind"] = behind

    if not pull or behind == 0:
        result["message"] = "Repository is already current." if behind == 0 else "Pull was not requested."
        return result
    if not before["clean"]:
        result["message"] = "Remote updates exist, but the worktree is not clean."
        return result
    if before["branch"] != "main":
        result["message"] = "Remote updates exist, but automatic pull is allowed only on main."
        return result
    if ahead:
        result["message"] = "Local and remote histories differ. Manual review is required."
        return result

    pulled = git_result(home, "pull", "--ff-only", "origin", "main", timeout=180)
    result["pull"] = "ok" if pulled.returncode == 0 else "failed"
    result["message"] = pulled.stdout or pulled.stderr
    result["after"] = git_state(home)
    return result


def ensure_runtime(home: Path) -> dict[str, Any]:
    steps: dict[str, Any] = {}
    for script in ("daily_rollover.py", "update_memory.py"):
        result = run_python(home, script, timeout=180)
        steps[script] = {
            "ok": result.returncode == 0,
            "output": result.stdout or result.stderr,
        }
        if result.returncode != 0:
            break
    return steps


def read_text(home: Path, relative: str, max_chars: int = 60_000) -> str:
    path = safe_path(home, relative)
    if not path.is_file():
        raise FileNotFoundError(f"Agent OS file not found: {relative}")
    text = path.read_text(encoding="utf-8")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[Truncated after {max_chars} characters]\n"


def wake(home: Path, auto_sync: bool = True) -> dict[str, Any]:
    sync = sync_git(home, fetch=auto_sync, pull=auto_sync)
    runtime = ensure_runtime(home)
    return {
        "agent_home": str(home),
        "git": sync,
        "runtime": runtime,
        "today": read_text(home, "Brain/Today.md", max_chars=12_000),
        "boot_prompt": read_text(home, "dist/agent_system_prompt.md", max_chars=50_000),
        "instruction": (
            "Adopt this identity and current memory before answering the user. "
            "If the Git state needs manual attention, explain it without pretending synchronization succeeded."
        ),
    }


def build_context(home: Path, message: str) -> dict[str, Any]:
    result = run_python(home, "conversation_pipeline.py", message, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "Context generation failed.")
    return {
        "message": message,
        "context": read_text(home, "dist/conversation_context.md", max_chars=80_000),
    }


def verify(home: Path) -> dict[str, Any]:
    result = run_python(home, "check_memory_pack.py", timeout=300)
    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout[-20_000:],
        "stderr": result.stderr[-8_000:],
    }


def as_json(value: Any) -> str:
    if isinstance(value, CommandResult):
        value = asdict(value)
    return json.dumps(value, ensure_ascii=False, indent=2)
