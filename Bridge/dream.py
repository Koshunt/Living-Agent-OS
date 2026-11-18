#!/usr/bin/env python3
"""Nightly memory consolidation — pure-API dream (v0.2, backported from production).

Reads Brain/Today.md, distills the day into durable memory via an
OpenAI-compatible chat API, appends dated entries to Brain/Living/{year}.md
(plus Brain/Reflection.md only for genuine behavior-updates), archives the day,
resets Today.md, then commits and pushes.

Contract (same as the private deployment this was backported from):
- Distill only what the user actually wrote. Prefer fewer, accurate entries.
- Emotional content records only what the user expressed. Never infer.
- Append-only. Idempotent: a date already present is never written twice.
- Failure-safe: if the API call fails, Today.md is left untouched and the
  next night retries cleanly.

Configuration (environment variables):
- LIVINGOS_LLM_API_KEY   required, API key for the chat endpoint
- LIVINGOS_LLM_BASE_URL  optional, OpenAI-compatible chat/completions URL
- LIVINGOS_LLM_MODELS    optional, comma-separated fallback list

Usage:  dream.py            normal run (cron / Task Scheduler)
        dream.py --dry-run  print the plan, change nothing
"""
import datetime as dt
import json
import os
import platform
import re
import subprocess
import sys
import urllib.request

BRIDGE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BRIDGE)
sys.path.insert(0, os.path.join(BRIDGE, "..", "scripts"))

from bridge_core.core import resolve_home  # noqa: E402
from daily_rollover import fresh_today  # noqa: E402  — single Today skeleton source

LOG = os.path.join(BRIDGE, "dream.log")
DEFAULT_API = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
MODELS = [m.strip() for m in os.environ.get(
    "LIVINGOS_LLM_MODELS", "glm-5.3-flash,glm-5.3"
).split(",") if m.strip()]

PLACEHOLDER = re.compile(
    r"None yet|Do not infer|Start from what is true|short-lived working memory|^- $"
)

def log(msg: str) -> None:
    line = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    # File only, no print: dream.sh already redirects stdout/stderr here.
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def read(path: str, tail: int | None = None) -> str:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return ""
    if tail:
        return "\n".join(text.rstrip().splitlines()[-tail:])
    return text


def has_content(today_text: str) -> bool:
    """Only real substance (beyond headings/placeholders) is worth a dream."""
    body = "\n".join(
        ln for ln in today_text.splitlines()
        if not PLACEHOLDER.search(ln) and ln.strip() and not ln.startswith("#")
    )
    return len(body.strip()) > 20


def call_llm(prompt: str, per_model_retries: int = 3) -> dict:
    """Try each model in order before giving up.

    thinking must stay disabled: reasoning models burn max_tokens on hidden
    reasoning and return empty content (the root cause of a 9-failure night
    in the production deployment).
    """
    key = os.environ.get("LIVINGOS_LLM_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "LIVINGOS_LLM_API_KEY is not set. Export it before dreaming."
        )
    api = os.environ.get("LIVINGOS_LLM_BASE_URL", DEFAULT_API).strip()
    body_base = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4000,
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
    }
    for model in MODELS:
        body = json.dumps({**body_base, "model": model}).encode()
        for attempt in range(1, per_model_retries + 1):
            req = urllib.request.Request(
                api, data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {key}"},
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read())
                content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
                m = re.search(r"\{.*\}", content, re.DOTALL)
                if m:
                    parsed = json.loads(m.group(0))
                    if any(parsed.get(k) for k in ("living", "reflection")):
                        return parsed
                log(f"warn {model} attempt {attempt}: no valid JSON: {content[:60]!r}")
            except Exception as exc:
                log(f"warn {model} attempt {attempt}: {exc}")
    raise SystemExit(
        f"all models failed ({', '.join(MODELS)}); Today.md untouched, retry tomorrow"
    )


PROMPT = """You are the memory consolidation process of a Living Agent OS, running at night.
Distill Today.md into durable memory.

Rules:
- Discard trivial noise. Fewer but accurate beats many but vague.
- "living" entries: facts, decisions, small growth moments the user actually wrote.
- "reflection" entries: only genuine lessons phrased as behavior updates, not shame.
  If the day taught nothing reusable, return an empty array.
- Never invent. Never infer emotions the user did not express.
- Output JSON only, no extra text:
{{"living": ["..."], "reflection": ["..."]}}
Each entry is one concise bullet.

## Today.md (to distill)
{today}

## Tail of Brain/Living/{year}.md (for tone and prior memories)
{living_tail}

## Tail of Brain/Reflection.md (for tone)
{reflection_tail}"""


def append_dated(path: str, date: str, entries: list[str],
                 file_header: str | None = None) -> bool:
    """Append a dated section. Idempotent: skip if the date already exists.

    Matches daily_rollover.py's archive format: files under Living/ start
    with a '# {year}' title, dated sections are preceded by a blank line.
    """
    if entries and f"## {date}" in read(path):
        log(f"skip {os.path.basename(path)}: {date} section already present")
        return False
    if file_header and not os.path.exists(path):
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"# {file_header}\n")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"\n\n## {date}: Nightly Dream\n\n")
        for entry in entries:
            fh.write(f"- {str(entry).strip()}\n")
    return True


def main() -> int:
    dry = "--dry-run" in sys.argv
    home = resolve_home()
    brain = os.path.join(str(home), "Brain")
    today_path = os.path.join(brain, "Today.md")

    # Dreamer host guard, Python side (dream.sh has the same guard for cron;
    # this one covers Windows Task Scheduler runs that call dream.py directly).
    configured = (os.environ.get("LIVINGOS_DREAM_HOST") or "").strip()
    if not configured:
        cfg = os.path.join(BRIDGE, "config.json")
        try:
            configured = json.load(open(cfg, encoding="utf-8")).get("dream_host", "")
        except Exception:
            configured = ""
    configured = str(configured).split(".")[0].strip().lower()
    host = platform.uname().node.split(".")[0].strip().lower()
    if configured and host != configured:
        log(f"not the dreamer host ({host} != {configured}); skipping")
        return 0

    # Multi-machine sync: fold in what other machines pushed first.
    try:
        subprocess.run(["git", "pull", "--rebase", "-q"], cwd=str(home),
                       check=True, timeout=120)
    except Exception as exc:
        log(f"warn git pull failed ({exc}); continuing on local copy")

    today_text = read(today_path)
    if not today_text or not has_content(today_text):
        log("Today.md holds only placeholders; nothing to dream")
        return 0

    # 日期基准 (2026-11-18): 凌晨做梦蒸馏"昨天" = 运行日-1, 日期一律真实日历
    dream_date = f"{(dt.date.today() - dt.timedelta(days=1)):%Y-%m-%d}"
    m = re.search(r"Date:\s*(\d{4}-\d{2}-\d{2})", today_text)
    today_is_legacy = bool(m and m.group(1) == dream_date)
    year = dream_date[:4]
    living_path = os.path.join(brain, "Living", f"{year}.md")
    reflection_path = os.path.join(brain, "Reflection.md")

    parsed = call_llm(PROMPT.format(
        today=today_text,
        year=year,
        living_tail=read(living_path, tail=40),
        reflection_tail=read(reflection_path, tail=30),
    ))
    living = [e for e in (parsed.get("living") or []) if str(e).strip()]
    reflection = [e for e in (parsed.get("reflection") or []) if str(e).strip()]
    log(f"distilled: living {len(living)}, reflection {len(reflection)}")

    if dry:
        print(json.dumps(parsed, ensure_ascii=False, indent=1))
        return 0

    os.makedirs(os.path.join(brain, "Living"), exist_ok=True)
    append_dated(living_path, dream_date, living, file_header=year)
    if reflection:
        append_dated(reflection_path, dream_date, reflection)

    # Archive the day, reset Today.md for tomorrow.
    with open(os.path.join(brain, "Living", f"Today-{dream_date}.md"), "w",
              encoding="utf-8") as fh:
        fh.write(today_text)
    if today_is_legacy:
        with open(today_path, "w", encoding="utf-8") as fh:
            fh.write(fresh_today(f"{dt.date.today():%Y-%m-%d}"))

    try:
        subprocess.run(["git", "add", "-A"], cwd=str(home), check=True, timeout=60)
        subprocess.run(
            ["git", "commit", "-qm", f"dream: {dream_date} distilled "
             f"{len(living) + len(reflection)} entries"],
            cwd=str(home), check=True, timeout=60)
        subprocess.run(["git", "push", "-q"], cwd=str(home), check=True, timeout=120)
        log("done: archive written, Today.md reset, git pushed")
    except Exception as exc:
        log(f"warn git incomplete ({exc}); local commit will push next night")

    return 0


if __name__ == "__main__":
    sys.exit(main())
