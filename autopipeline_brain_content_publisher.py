#!/usr/bin/env python3
"""Quality-gated pipeline: main-brain -> content -> publisher."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from news_guard import check_topic

ROOT = Path.home() / ".openclaw"
WS = ROOT / "workspace"
WS_CONTENT = ROOT / "workspace-content"
REPORT_DIR = WS / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
OPENCLAW = str(Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd")


def run_cmd(cmd: List[str], timeout: int = 600) -> Dict:
    st = time.time()
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return {
        "ok": p.returncode == 0,
        "rc": p.returncode,
        "stdout": (p.stdout or "").strip(),
        "stderr": (p.stderr or "").strip(),
        "duration_sec": round(time.time() - st, 2),
    }


def run_agent(agent: str, message: str, timeout_sec: int = 240) -> Dict:
    return run_cmd(["cmd", "/c", OPENCLAW, "agent", "--agent", agent, "-m", message, "--timeout", str(timeout_sec)], timeout=timeout_sec + 120)


def select_topic() -> Dict:
    candidates = [
        "AIGC 创作效率 工具",
        "显卡装机避坑 2026",
        "短视频起号方法",
        "AI办公自动化",
    ]
    best = None
    for q in candidates:
        try:
            r = check_topic("http://127.0.0.1:8080", q)
            item = {
                "query": q,
                "confidence": r.confidence,
                "publishable": r.is_publishable,
                "reasons": r.reasons,
                "source": r.source,
            }
        except Exception as e:
            item = {"query": q, "confidence": 0.0, "publishable": False, "reasons": [str(e)], "source": "none"}
        if best is None or item["confidence"] > best["confidence"]:
            best = item
    return best or {"query": "AI内容创作实战", "confidence": 0.0, "publishable": False, "reasons": ["fallback"], "source": "fallback"}


def main() -> None:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "time": now,
        "topic": {},
        "main_brain": {},
        "autotune": {},
        "final_refine": {},
        "quality_gate": {},
        "publisher": {},
    }

    topic_info = select_topic()
    topic = topic_info["query"] if topic_info.get("confidence", 0) > 0 else "AI内容创作提效与变现"
    report["topic"] = topic_info

    mb_prompt = (
        f"基于选题“{topic}”，给出今日分发策略：目标受众、平台优先级、转化动作。"
        "只输出简洁JSON，字段: audience,platform_priority,conversion_goal"
    )
    report["main_brain"] = run_agent("main-brain", mb_prompt, 220)

    raw_out_file = WS_CONTENT / f"daily_pack_raw_{now}.json"
    out_file = WS_CONTENT / f"daily_pack_{now}.json"
    tune_cmd = [
        "py",
        "-3",
        str(WS_CONTENT / "content_autotune_runner.py"),
        "--topic",
        topic.replace(" ", "_"),
        "--min-score",
        "85",
        "--max-rewrite-rounds",
        "3",
        "--out",
        str(raw_out_file),
    ]
    report["autotune"] = run_cmd(tune_cmd, timeout=1200)

    refine_cmd = [
        "py",
        "-3",
        str(WS / "final_publish_refiner.py"),
        "--input",
        str(raw_out_file),
        "--output",
        str(out_file),
        "--min-score",
        "85",
    ]
    report["final_refine"] = run_cmd(refine_cmd, timeout=900)

    q_report = WS_CONTENT / f"quality_{now}.json"
    q_cmd = [
        "py",
        "-3",
        str(WS_CONTENT / "content_quality_gate.py"),
        "--input",
        str(out_file),
        "--output",
        str(q_report),
        "--min-score",
        "85",
    ]
    report["quality_gate"] = run_cmd(q_cmd, timeout=300)

    pub_msg = (
        f"请读取文件 {out_file}。从中选择知乎和小红书各1条高分稿，执行测试发布（或草稿保存），"
        "返回每个平台的执行状态、URL/截图路径、失败原因（若有）。"
    )
    report["publisher"] = run_agent("publisher", pub_msg, 600)

    rpt = REPORT_DIR / f"pipeline_autorun_{now}.json"
    rpt.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(rpt), "topic": topic, "pack": str(out_file), "quality": str(q_report)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
