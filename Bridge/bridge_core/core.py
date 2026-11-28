from __future__ import annotations

import hashlib
import json
import math
import os
import re
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


_CJK_RUN = re.compile(r"[㐀-䶿一-鿿]+")


def read_text_resilient(path: Path) -> tuple[str, str]:
    """Read a text file without letting mixed encoding kill the wake.

    Machines on Chinese Windows sometimes append GBK bytes to UTF-8 files.
    Try strict UTF-8, then GBK, then lenient UTF-8, and report which codec
    worked so a damaged file is visible instead of fatal.
    """
    raw = path.read_bytes()
    for codec in ("utf-8", "gbk"):
        try:
            return raw.decode(codec), codec
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8 (lenient)"


def _query_terms(query: str) -> list[str]:
    """Split a query into searchable terms: latin words plus CJK bigrams."""
    terms = [w.lower() for w in re.findall(r"[a-zA-Z0-9]+", query)]
    for run in _CJK_RUN.findall(query):
        if len(run) == 1:
            terms.append(run)
        else:
            terms.extend(run[i:i + 2] for i in range(len(run) - 1))
    seen: set[str] = set()
    ordered: list[str] = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            ordered.append(term)
    return ordered


def recall(home: Path, query: str, limit: int = 6, prefix: str | None = None) -> dict[str, Any]:
    """Full-text recall across every markdown file under Brain/.

    Plain scan, no index to go stale; a memory pack this size scans in
    milliseconds. Hits are (file, line, text, score) — open the exact region
    afterwards with read_lines. Latin terms match on word boundaries, CJK
    terms as substrings; queries mixing both work.
    """
    terms = _query_terms(query)
    if not terms:
        return {"query": query, "error": "no searchable terms in query"}

    files = sorted((home / "Brain").rglob("*.md"))
    files = [p for p in files if not any(part.startswith(".") for part in p.relative_to(home).parts)]
    if prefix:
        plow = prefix.lower()
        files = [p for p in files if plow in str(p.relative_to(home)).lower()]

    file_texts: list[tuple[Path, list[str]]] = []
    df: dict[str, int] = {}
    for path in files:
        text, _ = read_text_resilient(path)
        file_texts.append((path, text.splitlines()))
        low = text.lower()
        for term in terms:
            if term in low:
                df[term] = df.get(term, 0) + 1

    total = max(len(file_texts), 1)
    hits: list[dict[str, Any]] = []
    file_scores: dict[str, float] = {}
    for path, lines in file_texts:
        rel = str(path.relative_to(home))
        for number, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line:
                continue
            low = line.lower()
            score = 0.0
            matched = 0
            for term in terms:
                if term.isascii() and term.isalnum():
                    tf = len(re.findall(r"\b" + re.escape(term) + r"\b", low))
                else:
                    tf = low.count(term)
                if tf:
                    score += tf * math.log(1 + total / df[term])
                    matched += 1
            if not score:
                continue
            if len(terms) > 1 and matched == len(terms):
                score *= 1.5
            file_scores[rel] = file_scores.get(rel, 0.0) + score
            hits.append({"file": rel, "line": number, "text": line[:160], "score": round(score, 2)})

    hits.sort(key=lambda h: (-h["score"], h["file"], h["line"]))
    seen_text: set[str] = set()
    unique = [h for h in hits if not (h["text"] in seen_text or seen_text.add(h["text"]))]
    top_files = sorted(file_scores.items(), key=lambda kv: -kv[1])[:6]
    return {
        "query": query,
        "terms": terms,
        "searched_files": len(file_texts),
        "files_with_hits": len(file_scores),
        "top_files": [{"file": f, "score": round(s, 2)} for f, s in top_files],
        "hits": unique[:limit],
        "total_hits": len(hits),
        "note": "open an exact region with agent_read_lines(file, start, end)",
    }


def read_lines(home: Path, relative: str, start: int, end: int, context: int = 0) -> dict[str, Any]:
    """Read a precise line range of one file — the follow-up to a recall hit."""
    path = safe_path(home, relative)
    if not path.is_file():
        return {"error": f"not a file: {relative}"}
    text, codec = read_text_resilient(path)
    lines = text.splitlines()
    first = max(1, start - context)
    last = min(len(lines), end + context)
    return {
        "file": relative,
        "encoding": codec,
        "total_lines": len(lines),
        "start": first,
        "end": last,
        "lines": [{"line": i, "text": lines[i - 1]} for i in range(first, last + 1)],
    }


def _room_spec(home: Path, room: str) -> tuple[str, int]:
    spec = load_rooms(home).get(room)
    if not spec:
        raise ValueError(f"Unknown room: {room}")
    output = str(spec.get("output") or "")
    if not output:
        files = spec.get("files") or []
        output = str(files[0]) if files else f"Brain/{room}.md"
    return output, int(spec.get("max_chars") or 60000)


def read_capped(home: Path, relative: str, max_chars: int) -> tuple[str, dict[str, Any]]:
    path = safe_path(home, relative)
    text, codec = read_text_resilient(path) if path.is_file() else ("", "missing")
    truncated = len(text) > max_chars
    report = {"file": relative, "chars": len(text), "max_chars": max_chars,
              "truncated": truncated, "codec": codec}
    return (text[:max_chars], report)


def wake(home: Path, auto_sync: bool = True, maintain: bool = True) -> dict[str, Any]:
    sync = sync_git(home, fetch=auto_sync, pull=auto_sync)
    runtime = ensure_runtime(home) if maintain else {"skipped": "maintenance disabled"}
    rooms = load_rooms(home)
    boot_file, boot_cap = _room_spec(home, "boot")
    today, today_report = read_capped(home, "Brain/Today.md", 12_000)
    boot, boot_report = read_capped(home, boot_file, boot_cap)
    truncated = [r for r in (today_report, boot_report) if r["truncated"]]

    doors: dict[str, Any] = {}
    for name, spec in rooms.items():
        if name == "boot":
            continue
        relative = str(spec.get("output") or "")
        path = safe_path(home, relative) if relative else None
        doors[name] = {
            "file": relative,
            "read_when": spec.get("read_when", ""),
            "chars": len(read_text_resilient(path)[0]) if path and path.is_file() else None,
            "max_chars": int(spec.get("max_chars", 0) or 0) or None,
        }

    return {
        "agent_home": str(home),
        "git": sync,
        "runtime": runtime,
        "today": today,
        "boot_prompt": boot,
        "rooms": doors,
        "truncation": truncated or None,
        "instruction": (
            "Adopt this identity and current memory before answering the user. "
            "The other rooms are not loaded on purpose: open one with <prefix>_read_room "
            "when writing memory, distilling, or when the user asks about continuity. "
            "During the day, use <prefix>_note_today for a short line worth carrying. "
            "Durable memory still requires <prefix>_propose_memory and explicit confirmation. "
            "If the Git state needs manual attention, explain it without pretending synchronization succeeded. "
            "If truncation is non-empty, say plainly which parts did not load."
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


def note_today(home: Path, note: str) -> dict[str, Any]:
    """Append one timestamped line at the end of the Current State section.

    Today.md is short-lived working memory, so unlike durable memory this
    writes directly without a proposal. Durable memory still requires
    create_proposal + apply_proposal with explicit user confirmation.
    """
    import fcntl
    today_path = safe_path(home, "Brain/Today.md")
    lock_path = safe_path(home, "Brain/.today.lock")
    with lock_path.open("w") as lock_handle:
        # Multiple machines and multiple agent instances write this file through
        # sync; the lock serializes same-machine writers. Cross-machine conflicts
        # are resolved by the union merge driver (see .gitattributes).
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        stamp = datetime.now().strftime("%H:%M")
        line = f"- [{stamp}] {note.strip()}"
        marker = "## Current State"
        if today_path.is_file():
            lines = today_path.read_text(encoding="utf-8").splitlines()
        else:
            lines = ["# Today", "", f"Date: {date.today():%Y-%m-%d}", "", marker]
        try:
            start = next(i for i, ln in enumerate(lines) if ln.strip() == marker)
        except StopIteration:
            lines += ["", marker, line]
        else:
            end = next(
                (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
                len(lines),
            )
            lines.insert(end, line)
        text = "\n".join(lines).rstrip() + "\n"
        today_path.write_text(text, encoding="utf-8")
    return {"status": "ok", "chars": len(text)}


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


def load_rooms(home: Path) -> dict[str, Any]:
    """Load the generic room contracts from config/rooms.json."""
    path = safe_path(home, "config/rooms.json")
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("rooms") or {}


def read_room(home: Path, room: str) -> dict[str, Any]:
    """Open one memory room that wake did not load."""
    rooms = load_rooms(home)
    if room not in rooms:
        raise ValueError(f"Unknown room: {room}. Available: {', '.join(sorted(rooms))}")
    spec = rooms[room]
    parts = []
    for relative in spec.get("files") or []:
        path = safe_path(home, str(relative))
        if not path.is_file():
            continue
        parts.append(f"## {relative}\n\n{read_text(home, str(relative))}")
    text = "\n\n".join(parts)
    cap = int(spec.get("max_chars") or 60000)
    truncated = len(text) > cap
    return {
        "room": room,
        "title": spec.get("title", room),
        "read_when": spec.get("read_when", ""),
        "text": text[:cap],
        "truncated": truncated,
        "max_chars": cap,
    }


def update_today_memory(home: Path, title: str, content: str) -> dict[str, Any]:
    """Write a short-lived note to Brain/Today.md only.

    Durable memory remains proposal-only. This tool structurally cannot write
    to Brain/Living, Brain/Immutable, or MemoryPack.
    """
    import fcntl

    clean_title = (title or "").strip()[:80] or "会话记录"
    clean_content = (content or "").strip()[:4000]
    if not clean_content:
        raise ValueError("content is empty")
    path = safe_path(home, "Brain/Today.md")
    lock_path = safe_path(home, "Brain/.today.lock")
    with lock_path.open("w") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        section = "\n### " + clean_title + "\n\n" + "\n".join(
            "- " + line.strip() for line in clean_content.splitlines() if line.strip()
        ) + "\n"
        marker = "## Rollover"
        pos = text.find(marker)
        if pos != -1:
            text = text[:pos] + section + "\n" + text[pos:]
        else:
            text = text.rstrip() + "\n\n" + section + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    return {"ok": True, "path": "Brain/Today.md", "title": clean_title,
            "chars": len(clean_content)}


def as_json(value: Any) -> str:
    if isinstance(value, CommandResult):
        value = asdict(value)
    return json.dumps(value, ensure_ascii=False, indent=2)
