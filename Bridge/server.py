from __future__ import annotations

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
    as_json,
    build_context,
    git_state,
    read_text,
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


class VerifyInput(StrictInput):
    pass


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
    """
    return as_json(wake(resolve_home(), auto_sync=params.auto_sync))


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
