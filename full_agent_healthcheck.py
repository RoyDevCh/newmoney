#!/usr/bin/env python3
"""Healthcheck all agents with functional prompts."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

OPENCLAW = str(Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd")
OUT = Path.home() / ".openclaw" / "workspace" / "reports"
OUT.mkdir(parents=True, exist_ok=True)

AGENTS = [
    ("main", "输出今日系统状态摘要（3条）"),
    ("main-brain", "给出今天的自动化执行优先级（3条）"),
    ("content", "生成一句高信息密度的知乎标题，主题AI自动化"),
    ("multimodal", "给出一条ComfyUI图像prompt和negative prompt"),
    ("publisher", "说明当前可测试发布的平台和前置条件"),
    ("monitor", "输出系统监控关键指标清单（5项）"),
    ("tasks", "输出今日待执行任务列表（3项）"),
]


def run(agent: str, msg: str):
    st = time.time()
    p = subprocess.run(
        ["cmd", "/c", OPENCLAW, "agent", "--agent", agent, "-m", msg, "--timeout", "180"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    return {
        "agent": agent,
        "ok": p.returncode == 0,
        "rc": p.returncode,
        "duration_sec": round(time.time() - st, 2),
        "stdout": (p.stdout or "").strip()[:1200],
        "stderr": (p.stderr or "").strip()[:600],
    }


def main():
    results = [run(a, m) for a, m in AGENTS]
    out = OUT / f"agent_health_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(out), "ok": [r['agent'] for r in results if r['ok']]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
