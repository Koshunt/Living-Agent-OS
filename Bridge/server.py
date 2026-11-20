from __future__ import annotations

import json

import importlib
import subprocess
import sys
from pathlib import Path


def _bootstrap_deps() -> None:
    """Auto-install missing dependencies when server first starts."""
    missing = []
    for mod in ("mcp", "pydantic"):
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return
    req_file = Path(__file__).resolve().parent / "requirements.txt"
    cmd = (
        [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--quiet", "--no-warn-script-location"]
        if req_file.is_file()
        else [sys.executable, "-m", "pip", "install", *missing, "--quiet", "--no-warn-script-location"]
    )
    try:
        subprocess.check_call(cmd, timeout=120)
    except subprocess.TimeoutExpired:
        print("pip install timed out. Run Bridge/setup.ps1 manually.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError:
        print("pip install failed. Run Bridge/setup.ps1 manually.", file=sys.stderr)
        sys.exit(1)


_bootstrap_deps()

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from bridge_core.core import (
    apply_proposal,
    as_json,
    build_context,
    create_proposal,
    git_state,
    note_today,
    read_lines,
    read_text,
    recall,
    resolve_home,
    sync_git,
    verify,
    wake,
)


mcp = FastMCP("agent_mcp")


class StrictInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class WakeInput(StrictInput):
    auto_sync: bool = Field(
        default=True,
        description="Fetch origin/main and pull only when the main worktree is clean and fast-forwardable.",
    )


class ContextInput(StrictInput):
    message: str = Field(
        ...,
        min_length=1,
        max_length=20_000,
        description="User's current message used to retrieve focused agent memory.",
    )


class StatusInput(StrictInput):
    fetch_remote: bool = Field(
        default=False,
        description="Whether to fetch origin/main before reporting ahead/behind state.",
    )


class ProposalInput(StrictInput):
    title: str = Field(..., min_length=1, max_length=200)
    change: str = Field(..., min_length=1, max_length=8000)
    future_effect: str = Field(..., min_length=1, max_length=8000)
    suggested_target: str = Field(..., description="reflection, continuity, correction, decision, or knowledge")
    source_excerpt: str = Field(default="", max_length=4000)


class ApplyProposalInput(StrictInput):
    proposal_name: str = Field(..., min_length=1, max_length=260)
    confirmation: str = Field(..., description='Explicit user confirmation: "确认", "确认写入", or "确认写入长期记忆".')


class VerifyInput(StrictInput):
    pass


class NoteInput(StrictInput):
    note: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="One Today.md line: what happened, a decision, or a loose end.",
    )


class RecallInput(StrictInput):
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Free text to search for. Latin words and CJK both work.",
    )
    limit: int = Field(default=6, ge=1, le=30, description="Max hits returned.")
    prefix: str = Field(
        default="",
        max_length=200,
        description="Restrict search to files whose relative path contains this.",
    )


class ReadLinesInput(StrictInput):
    file: str = Field(..., min_length=1, max_length=300, description="Relative path from the Agent OS home.")
    start: int = Field(..., ge=1, description="First line to read (1-based).")
    end: int = Field(..., ge=1, description="Last line to read (inclusive).")
    context: int = Field(default=0, ge=0, le=50, description="Extra lines of context on each side.")


@mcp.tool(
    name="agent_ping",
    annotations=ToolAnnotations(
        title="Check Agent MCP Health",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def agent_ping() -> str:
    """Return a minimal health response without reading files or running commands."""
    return '{"ok": true, "server": "agent_mcp"}'


@mcp.tool(
    name="agent_wake",
    annotations=ToolAnnotations(
        title="Wake Agent And Load Current Memory",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
def agent_wake(params: WakeInput) -> str:
    """Wake the agent at the start of a session.

    Safely checks GitHub, fast-forward pulls only when allowed, rolls daily memory,
    regenerates runtime bundles, and returns the current boot and Today context.
    It never commits, pushes, resolves conflicts, or overwrites a dirty worktree.
    The response carries server_time (NTP-synced local clock) so every session
    starts with an authoritative timestamp at zero extra cost.
    """
    result = json.loads(as_json(wake(resolve_home(), auto_sync=params.auto_sync)))
    from datetime import datetime
    now = datetime.now().astimezone()
    result["server_time"] = {
        "iso": now.isoformat(timespec="seconds"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday_en": "Mon Tue Wed Thu Fri Sat Sun".split()[now.weekday()],
        "weekday_zh": "周" + "一二三四五六日"[now.weekday()],
        "unix": int(now.timestamp()),
        "tz": now.strftime("%z"),
        "note": "server local time, NTP-synced"
    }
    return as_json(result)


@mcp.tool(
    name="agent_note_today",
    annotations=ToolAnnotations(
        title="Append One Line To Today Working Memory",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def agent_note_today(params: NoteInput) -> str:
    """Append one timestamped line to Brain/Today.md (short-lived working memory).

    Writes directly without a proposal: Today.md is ephemeral and reset daily.
    Durable memory still requires agent_propose_memory + explicit confirmation.
    """
    return as_json(note_today(resolve_home(), params.note))


@mcp.tool(
    name="agent_recall",
    annotations=ToolAnnotations(
        title="Search All Memory At Once",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def agent_recall(params: RecallInput) -> str:
    """Full-text search over every markdown file under Brain/ (Latin and CJK).

    Use whenever a detail feels fuzzy, a file is too long to read whole, or
    the user asks about the past. Hits are (file, line, text, score); open
    the exact region next with agent_read_lines. If results are weak, retry
    with synonyms, entity names, or time hints — stored wording may differ.
    """
    return as_json(recall(resolve_home(), params.query, params.limit, params.prefix or None))


@mcp.tool(
    name="agent_read_lines",
    annotations=ToolAnnotations(
        title="Read An Exact Region",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def agent_read_lines(params: ReadLinesInput) -> str:
    """Open the precise lines a recall hit pointed at, with optional context."""
    return as_json(read_lines(resolve_home(), params.file, params.start, params.end, params.context))


@mcp.tool(
    name="agent_get_context",
    annotations=ToolAnnotations(
        title="Retrieve Focused Agent Context",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def agent_get_context(params: ContextInput) -> str:
    """Generate and return focused agent memory for the user's current message."""
    return as_json(build_context(resolve_home(), params.message))


@mcp.tool(
    name="agent_git_status",
    annotations=ToolAnnotations(
        title="Check Agent OS Git Status",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
def agent_git_status(params: StatusInput) -> str:
    """Report local Git state and optionally fetch remote divergence without pulling."""
    home = resolve_home()
    if params.fetch_remote:
        return as_json(sync_git(home, fetch=True, pull=False))
    return as_json(git_state(home))


@mcp.tool(
    name="agent_time",
    annotations=ToolAnnotations(
        title="Current Server Time",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def agent_time() -> str:
    """Current server local time (NTP-synced).

    Call this BEFORE stating any specific time in conversation - never guess
    timestamps from context. Zero-cost clock: ISO date/time, weekday, unix ts."""

    from datetime import datetime
    now = datetime.now().astimezone()
    wd_en = "Mon Tue Wed Thu Fri Sat Sun".split()[now.weekday()]
    wd_zh = "周" + "一二三四五六日"[now.weekday()]
    return as_json({
        "iso": now.isoformat(timespec="seconds"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday_en": wd_en,
        "weekday_zh": wd_zh,
        "unix": int(now.timestamp()),
        "tz": now.strftime("%z"),
        "note": "server local time, NTP-synced"
    })


@mcp.tool(
    name="agent_propose_memory",
    annotations=ToolAnnotations(title="Create A Reviewable Memory Proposal", readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
)
def agent_propose_memory(params: ProposalInput) -> str:
    """Create an ignored local proposal without changing durable memory."""
    return as_json(create_proposal(resolve_home(), params.title, params.change, params.future_effect, params.suggested_target, params.source_excerpt))


@mcp.tool(
    name="agent_apply_memory",
    annotations=ToolAnnotations(title="Apply An Approved Memory Proposal", readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False),
)
def agent_apply_memory(params: ApplyProposalInput) -> str:
    """Apply one proposal only after explicit user confirmation."""
    return as_json(apply_proposal(resolve_home(), params.proposal_name, params.confirmation))


@mcp.tool(
    name="agent_verify",
    annotations=ToolAnnotations(
        title="Verify Agent OS",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def agent_verify(params: VerifyInput) -> str:
    """Run the complete Agent OS check suite after maintenance."""
    return as_json(verify(resolve_home()))


@mcp.resource("agent://boot")
def agent_boot_resource() -> str:
    """Return the latest generated agent system prompt."""
    return read_text(resolve_home(), "dist/agent_system_prompt.md", max_chars=50_000)


@mcp.resource("agent://today")
def agent_today_resource() -> str:
    """Return current short-lived Today memory."""
    return read_text(resolve_home(), "Brain/Today.md", max_chars=12_000)


@mcp.prompt(name="agent_start_session")
def agent_start_session(message: str = "") -> str:
    """Guide an MCP client through agent session activation."""
    current = message.strip() or "(User has not sent the first message yet.)"
    return (
        "Call agent_wake before answering the user. Adopt the returned boot and Today "
        "context as first-person continuity. Then call agent_get_context with this message:\n\n"
        f"{current}\n\n"
        "Do not describe the agent as an external persona. If synchronization is blocked, say so honestly."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
