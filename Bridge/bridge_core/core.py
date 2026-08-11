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

PROPOSAL_TARGETS = {
    "reflection": "Brain/Reflection.md",
    "continuity": "MemoryPack/Memory/ContinuityMemory.md",
    "correction": "MemoryPack/Memory/CorrectionLog.md",
    "decision": "MemoryPack/Memory/DecisionMemory.md",
    "knowledge": "MemoryPack/Knowledge/DomainKnowledge.md",
}
MEMORY_CONFIRMATIONS = {"确认", "确认写入", "确认写入长期记忆"}


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


def proposal_dir(home: Path) -> Path:
    directory = safe_path(home, "workspace/mcp_proposals")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def create_proposal(
    home: Path,
    title: str,
    change: str,
    future_effect: str,
    suggested_target: str,
    source_excerpt: str = "",
) -> dict[str, Any]:
    if suggested_target not in PROPOSAL_TARGETS:
        allowed = ", ".join(sorted(PROPOSAL_TARGETS))
        raise ValueError(f"Unknown target. Choose one of: {allowed}")
    now = datetime.now().astimezone()
    payload = {
        "title": title.strip(),
        "change": change.strip(),
        "future_effect": future_effect.strip(),
        "suggested_target": suggested_target,
        "target_file": PROPOSAL_TARGETS[suggested_target],
        "source_excerpt": source_excerpt.strip()[:4000],
        "created_at": now.isoformat(timespec="seconds"),
        "status": "awaiting user approval",
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload["sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    filename = now.strftime("%Y%m%d_%H%M%S_%f") + ".json"
    path = proposal_dir(home) / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"proposal": str(path), "details": payload}


def apply_proposal(home: Path, proposal_name: str, confirmation: str) -> dict[str, Any]:
    if confirmation.strip() not in MEMORY_CONFIRMATIONS:
        allowed = "、".join(sorted(MEMORY_CONFIRMATIONS))
        raise ValueError(f"Permanent memory update requires explicit confirmation: {allowed}")
    directory = proposal_dir(home).resolve()
    proposal = (directory / Path(proposal_name).name).resolve()
    if proposal.parent != directory or not proposal.is_file():
        raise FileNotFoundError("Proposal was not found in workspace/mcp_proposals.")
    payload = json.loads(proposal.read_text(encoding="utf-8"))
    if payload.get("status") != "awaiting user approval":
        raise ValueError("Proposal is not awaiting approval.")
    target_key = payload.get("suggested_target")
    if target_key not in PROPOSAL_TARGETS:
        raise ValueError("Proposal target is no longer allowed.")
    target = safe_path(home, PROPOSAL_TARGETS[target_key])
    block = (
        f"\n\n## {date.today().isoformat()}: {payload['title']}\n\n"
        "Source: reviewed Agent OS memory proposal\n\n"
        f"What changed:\n\n{payload['change']}\n\n"
        f"Future effect:\n\n{payload['future_effect']}\n"
    )
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(block)
    payload["status"] = "applied"
    payload["applied_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    proposal.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    generated = run_python(home, "update_memory.py")
    return {
        "updated": str(target),
        "proposal": str(proposal),
        "prompt_regenerated": generated.returncode == 0,
        "next_step": "Run agent_verify before committing. Commit and push still require user approval.",
    }


def verify(home: Path) -> dict[str, Any]:
    result = run_python(home, "verify_agent.py", timeout=300)
    return {
        "ok": result.returncode == 0,
        "stdout": result.stdout[-20_000:],
        "stderr": result.stderr[-8_000:],
    }


def as_json(value: Any) -> str:
    if isinstance(value, CommandResult):
        value = asdict(value)
    return json.dumps(value, ensure_ascii=False, indent=2)
