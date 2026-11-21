#!/usr/bin/env python3
"""CC PreCompact hook: 压缩前把 transcript 指针写进本 OS 的 Today.md。
settings.json: hooks.PreCompact → command: python3 <本文件>
路径按脚本自身位置推导, 任意宿主/任意克隆位置通用。"""
import json, sys, os, fcntl, datetime

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
trigger = data.get("trigger", "auto")
tp = data.get("transcript_path", "?")

brain_today = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Brain", "Today.md")
if not os.path.exists(brain_today):
    sys.exit(0)  # 不在本 OS 的克隆里, 静默退出

now = datetime.datetime.now().strftime("%m-%d %H:%M")
entry = f"- {now} ⚠ 会话上下文已压缩({trigger})。压缩会丢细节——需要本次会话的完整细节时, 读 transcript: {tp}\n"
marker = "## Rollover"
lock = os.path.join(os.path.dirname(brain_today), ".today.lock")
with open(lock, "w") as lf:
    fcntl.flock(lf, fcntl.LOCK_EX)
    cur = open(brain_today, encoding="utf-8").read()
    if marker in cur:
        cur = cur.replace(marker, entry + marker, 1)
    else:
        cur = cur.rstrip("\n") + "\n" + entry
    open(brain_today, "w", encoding="utf-8").write(cur)
