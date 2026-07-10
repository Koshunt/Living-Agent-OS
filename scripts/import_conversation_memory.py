from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "workspace" / "imports" / "conversation_import_state.json"
PROPOSAL_DIR = ROOT / "workspace" / "imports" / "proposals"
PROPOSAL_JSON_DIR = ROOT / "workspace" / "imports" / "proposal_json"

MEMORY_SIGNALS = {
    "identity": ["who are you", "your name", "identity", "persona", "character", "你是谁", "名字", "身份"],
    "relationship": ["love", "friend", "together", "miss you", "care", "爱你", "陪", "关系", "亲爱的"],
    "correction": ["don't", "stop", "wrong", "fix", "correct", "not like", "repeat", "mechanical", "cold",
                    "不要", "不应该", "纠正", "不像", "重复", "机械", "冷"],
    "research": ["paper", "reviewer", "experiment", "hypothesis", "method", "result",
                 "论文", "审稿", "实验", "研究", "假设"],
    "coding": ["code", "script", "bug", "debug", "function", "variable",
               "代码", "脚本", "修复", "函数"],
    "career": ["job", "interview", "resume", "career", "company", "offer",
               "职业", "面试", "简历", "工作", "岗位"],
    "daily": ["tired", "happy", "sad", "today", "home", "morning", "night",
              "累", "开心", "难过", "今天", "早上", "晚上"],
    "operations": ["memory", "save", "remember", "update", "sync", "git",
                   "记忆", "保存", "同步", "更新"],
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def display_source(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"sources": {}}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_markdown_chat(text: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"##\s*(Prompt|Response|User|Assistant|Human|AI):\s*\n(?:[^\n]*\n)?\s*(.*?)(?=\n##\s*(?:Prompt|Response|User|Assistant|Human|AI):|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if matches:
        role_map = {"prompt": "user", "response": "assistant", "user": "user",
                    "assistant": "assistant", "human": "user", "ai": "assistant"}
        return [
            {"role": role_map.get(kind.lower(), "unknown"), "content": body.strip()}
            for kind, body in matches
            if body.strip()
        ]
    return []


def parse_plain_text(text: str) -> list[dict[str, str]]:
    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    return [{"role": "unknown", "content": block} for block in blocks]


def flatten_json_messages(value: Any) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if isinstance(value, list):
        for item in value:
            messages.extend(flatten_json_messages(item))
        return messages
    if isinstance(value, dict):
        role = value.get("role") or value.get("author") or value.get("speaker")
        content = value.get("content") or value.get("text") or value.get("message")
        if isinstance(content, list):
            content = "\n".join(str(part) for part in content)
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        if content and isinstance(content, str):
            messages.append({"role": str(role or "unknown"), "content": content.strip()})
            return messages
        for item in value.values():
            messages.extend(flatten_json_messages(item))
    return messages


def parse_source(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        messages = flatten_json_messages(data)
        if messages:
            return messages
    messages = parse_markdown_chat(text)
    if messages:
        return messages
    return parse_plain_text(text)


def message_id(message: dict[str, str]) -> str:
    return sha256_text(f"{message.get('role', '')}\n{message.get('content', '')}")


def detect_topics(content: str) -> list[str]:
    lower = content.lower()
    topics: list[str] = []
    for topic, keywords in MEMORY_SIGNALS.items():
        if any(keyword.lower() in lower for keyword in keywords):
            topics.append(topic)
    return topics


def compact(text: str, limit: int = 420) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3] + "..."


def suggested_target_key(topics: list[str]) -> str:
    if "correction" in topics:
        return "correction"
    if "research" in topics:
        return "living"
    if "career" in topics:
        return "living"
    if "relationship" in topics or "identity" in topics:
        return "living"
    return "living"


def suggested_target_desc(topics: list[str]) -> str:
    key = suggested_target_key(topics)
    targets = {
        "correction": "`MemoryPack/Memory/CorrectionLog.md` or `Brain/Reflection.md`",
        "living": "`Brain/Living/YYYY.md` or `Brain/Reflection.md`",
    }
    return targets.get(key, "`Brain/Living/YYYY.md`")


def candidate_entry(index: int, message: dict[str, str], topics: list[str]) -> dict[str, Any]:
    return {
        "index": index,
        "role": message["role"],
        "topics": topics,
        "content": compact(message["content"], limit=900),
        "suggested_target": suggested_target_key(topics),
        "suggested_target_description": suggested_target_desc(topics),
    }


def build_candidates(new_messages: list[dict[str, str]]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    topic_counts: dict[str, int] = {}
    candidates: list[dict[str, Any]] = []
    for index, message in enumerate(new_messages, start=1):
        topics = detect_topics(message["content"])
        for topic in topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        if topics:
            candidates.append(candidate_entry(index, message, topics))
    return topic_counts, candidates


def build_proposal(source: Path, new_messages: list[dict[str, str]], source_hash: str) -> str:
    now = datetime.now().isoformat(timespec="seconds")
    topic_counts, candidates = build_candidates(new_messages)

    lines = [
        "# Conversation Memory Import Proposal",
        "",
        f"Source: `{display_source(source)}`",
        f"Imported at: {now}",
        f"Source sha256: `{source_hash}`",
        f"New messages: {len(new_messages)}",
        "",
        "## Topic Counts",
        "",
    ]
    if topic_counts:
        for topic, count in sorted(topic_counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {topic}: {count}")
    else:
        lines.append("- No strong memory topics detected.")

    lines.extend([
        "",
        "## Candidate Durable Memories",
        "",
        "Review these before applying. Do not store temporary mood or unverified facts as permanent memory.",
        "For each promoted candidate, state what changed and how future behavior should differ.",
        "",
    ])

    if not candidates:
        lines.append("- No candidates detected.")
    else:
        for candidate in candidates[:50]:
            lines.extend([
                f"### Message {candidate['index']}: {candidate['role']}",
                "",
                f"Topics: {', '.join(candidate['topics'])}",
                "",
                compact(candidate["content"]),
                "",
                f"Suggested target: {candidate['suggested_target_description']}",
                "",
            ])

    lines.extend([
        "## Apply Manually",
        "",
        "Use:",
        "",
        "```powershell",
        "python scripts\\memory_manager.py living --title \"...\" --body \"...\" --source \"conversation import\"",
        "python scripts\\memory_manager.py correction --title \"...\" --body \"...\" --source \"conversation import\"",
        "```",
        "",
    ])
    return "\n".join(lines)


def build_proposal_json(source: Path, new_messages: list[dict[str, str]], source_hash: str) -> dict[str, Any]:
    topic_counts, candidates = build_candidates(new_messages)
    return {
        "source": display_source(source),
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "source_sha256": source_hash,
        "new_message_count": len(new_messages),
        "topic_counts": topic_counts,
        "candidates": candidates,
    }


def write_proposal(source: Path, proposal: str, proposal_json: dict[str, Any]) -> tuple[Path, Path]:
    PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)
    PROPOSAL_JSON_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", source.stem)[:80]
    output = PROPOSAL_DIR / f"{stamp}_{safe_name}.md"
    json_output = PROPOSAL_JSON_DIR / f"{stamp}_{safe_name}.json"
    output.write_text(proposal, encoding="utf-8")
    json_output.write_text(json.dumps(proposal_json, indent=2, ensure_ascii=False), encoding="utf-8")
    return output, json_output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import conversation files into memory proposals.")
    parser.add_argument("--input", type=Path, required=True, help="Conversation file: .md, .txt, or .json")
    parser.add_argument("--reset", action="store_true", help="Forget previous import state for this file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.input.resolve()
    if not source.exists():
        print(f"Input file not found: {source}")
        return 1

    messages = parse_source(source)
    ids = [message_id(message) for message in messages]
    text = source.read_text(encoding="utf-8", errors="replace")
    source_hash = sha256_text(text)

    state = load_state()
    key = str(source)
    source_state = state.setdefault("sources", {}).get(key, {})
    seen_ids = set() if args.reset else set(source_state.get("seen_message_ids", []))

    new_messages = [message for message, mid in zip(messages, ids) if mid not in seen_ids]
    if not new_messages:
        print("No new messages to import.")
        return 0

    proposal = build_proposal(source, new_messages, source_hash)
    proposal_json = build_proposal_json(source, new_messages, source_hash)
    output, json_output = write_proposal(source, proposal, proposal_json)

    state["sources"][key] = {
        "last_imported_at": datetime.now().isoformat(timespec="seconds"),
        "source_sha256": source_hash,
        "message_count": len(messages),
        "seen_message_ids": ids,
        "last_proposal": output.relative_to(ROOT).as_posix(),
        "last_proposal_json": json_output.relative_to(ROOT).as_posix(),
    }
    save_state(state)

    print(f"Parsed messages: {len(messages)}")
    print(f"New messages: {len(new_messages)}")
    print(f"Wrote {output.relative_to(ROOT)}")
    print(f"Wrote {json_output.relative_to(ROOT)}")
    print("Review the proposal before applying it to permanent memory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
