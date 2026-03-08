#!/usr/bin/env python3
"""Quality-gated pipeline: main-brain -> content -> refine -> expand -> repair -> recheck."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from news_guard import check_topic
from platform_monetization_mapper import build_full_platform_matrix, build_readiness_summary

ROOT = Path.home() / ".openclaw"
WS = ROOT / "workspace"
WS_CONTENT = ROOT / "workspace-content"
REPORT_DIR = WS / "reports"
METRICS_LATEST = WS_CONTENT / "metrics_analysis_latest.json"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
OPENCLAW = str(Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd")

STABLE_TOPICS = [
    {
        "query": "数码装备避坑与选购建议 2026",
        "priority": 1.0,
        "fit_platforms": ["知乎", "抖音", "西瓜视频", "B站", "微博", "头条"],
    },
    {
        "query": "办公效率工具清单与信息管理工作流",
        "priority": 0.99,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "公众号", "头条"],
    },
    {
        "query": "家用小电器真实使用场景与避坑清单",
        "priority": 0.97,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "头条"],
    },
    {
        "query": "内容生产提效与变现流程拆解",
        "priority": 0.95,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "公众号"],
    },
    {
        "query": "商业案例拆解与品牌增长复盘",
        "priority": 0.94,
        "fit_platforms": ["知乎", "抖音", "西瓜视频", "B站", "微博", "公众号", "头条"],
    },
    {
        "query": "知识管理与个人系统搭建",
        "priority": 0.93,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "公众号"],
    },
    {
        "query": "历史事件里的商业与认知启发",
        "priority": 0.91,
        "fit_platforms": ["知乎", "西瓜视频", "B站", "微博", "公众号", "头条"],
    },
    {
        "query": "AI工具清单与效率工作流",
        "priority": 0.9,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "微博", "公众号", "头条"],
    },
]


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
    return run_cmd(
        ["cmd", "/c", OPENCLAW, "agent", "--agent", agent, "-m", message, "--timeout", str(timeout_sec)],
        timeout=timeout_sec + 120,
    )


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_metrics_context(path: Path) -> Dict:
    if not path.exists():
        return {"available": False, "platform_summary": {}, "suggestions": []}
    try:
        data = load_json(path)
        return {
            "available": True,
            "platform_summary": data.get("platform_summary", {}),
            "suggestions": data.get("suggestions", []),
        }
    except Exception as e:
        return {"available": False, "error": str(e), "platform_summary": {}, "suggestions": []}


def better_quality(candidate: Dict, baseline: Dict) -> bool:
    c = candidate.get("summary", {})
    b = baseline.get("summary", {})
    candidate_pass = int(c.get("pass_count", 0))
    baseline_pass = int(b.get("pass_count", 0))
    if candidate_pass != baseline_pass:
        return candidate_pass > baseline_pass
    return float(c.get("avg_score", 0.0)) >= float(b.get("avg_score", 0.0))


def select_topic() -> Dict:
    best = None
    for candidate in STABLE_TOPICS:
        q = candidate["query"]
        try:
            r = check_topic("http://127.0.0.1:8080", q)
            item = {
                "query": q,
                "confidence": r.confidence,
                "publishable": r.is_publishable,
                "reasons": r.reasons,
                "source": r.source,
                "priority": candidate["priority"],
                "fit_platforms": candidate["fit_platforms"],
            }
        except Exception as e:
            item = {
                "query": q,
                "confidence": 0.0,
                "publishable": False,
                "reasons": [str(e)],
                "source": "none",
                "priority": candidate["priority"],
                "fit_platforms": candidate["fit_platforms"],
            }
        item["stable_score"] = round(item["confidence"] * 0.7 + item["priority"] * 0.3, 4)
        if best is None or item["stable_score"] > best["stable_score"]:
            best = item
    return best or {
        "query": "AI内容创作提效与变现",
        "confidence": 0.0,
        "publishable": False,
        "reasons": ["fallback"],
        "source": "fallback",
        "priority": 0.8,
        "fit_platforms": ["知乎", "小红书", "抖音", "B站"],
        "stable_score": 0.8,
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-publisher", action="store_true")
    ap.add_argument("--skip-assets", action="store_true")
    args = ap.parse_args()

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "time": now,
        "topic": {},
        "matrix_strategy": {},
        "readiness_strategy": {},
        "metrics_feedback": {},
        "main_brain": {},
        "autotune": {},
        "final_refine": {},
        "matrix_expand": {},
        "repair": {},
        "quality_gate": {},
        "specificity_boost": {},
        "quality_recheck": {},
        "tts_render": {},
        "asset_render": {},
        "manual_publish_queue": {},
        "publisher": {},
    }

    topic_info = select_topic()
    topic = topic_info["query"] if topic_info.get("stable_score", 0) > 0 else "AI内容创作提效与变现"
    report["topic"] = topic_info

    matrix = build_full_platform_matrix()
    readiness = build_readiness_summary(list(matrix.keys()))
    metrics_feedback = load_metrics_context(METRICS_LATEST)
    report["matrix_strategy"] = matrix
    report["readiness_strategy"] = readiness
    report["metrics_feedback"] = metrics_feedback
    mb_prompt = (
        f"基于选题“{topic}”、以下平台变现矩阵{json.dumps(matrix, ensure_ascii=False)}"
        f"以及当前阶段分组{json.dumps(readiness, ensure_ascii=False)}、"
        f"最近一轮平台数据反馈{json.dumps(metrics_feedback, ensure_ascii=False)}，"
        "给出今日分发策略：目标受众、平台优先级、转化动作、平台分工。"
        "只输出简洁JSON，字段: audience,platform_priority,conversion_goal,platform_roles"
    )
    report["main_brain"] = run_agent("main-brain", mb_prompt, 220)

    raw_out_file = WS_CONTENT / f"daily_pack_raw_{now}.json"
    out_file = WS_CONTENT / f"daily_pack_{now}.json"
    topic_file = WS_CONTENT / f"topic_{now}.txt"
    topic_file.write_text(topic, encoding="utf-8")
    tune_cmd = [
        "py",
        "-3",
        str(WS_CONTENT / "content_autotune_runner.py"),
        "--topic-file",
        str(topic_file),
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

    expand_cmd = [
        "py",
        "-3",
        str(WS / "matrix_pack_expander.py"),
        "--input",
        str(out_file),
        "--output",
        str(out_file),
        "--min-score",
        "85",
    ]
    report["matrix_expand"] = run_cmd(expand_cmd, timeout=1200)

    repair_cmd = [
        "py",
        "-3",
        str(WS / "low_score_repair_runner.py"),
        "--input",
        str(out_file),
        "--output",
        str(out_file),
        "--min-score",
        "85",
    ]
    report["repair"] = run_cmd(repair_cmd, timeout=1200)

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

    boosted_out_file = WS_CONTENT / f"daily_pack_{now}_boosted.json"
    shutil.copyfile(out_file, boosted_out_file)
    boost_cmd = [
        "py",
        "-3",
        str(WS / "specificity_boost_runner.py"),
        "--input",
        str(boosted_out_file),
        "--output",
        str(boosted_out_file),
        "--min-score",
        "85",
    ]
    report["specificity_boost"] = run_cmd(boost_cmd, timeout=300)

    q_recheck_report = WS_CONTENT / f"quality_{now}_recheck.json"
    q_recheck_cmd = [
        "py",
        "-3",
        str(WS_CONTENT / "content_quality_gate.py"),
        "--input",
        str(boosted_out_file),
        "--output",
        str(q_recheck_report),
        "--min-score",
        "85",
    ]
    report["quality_recheck"] = run_cmd(q_recheck_cmd, timeout=300)
    try:
        base_quality = load_json(q_report)
        candidate_quality = load_json(q_recheck_report)
        if better_quality(candidate_quality, base_quality):
            shutil.copyfile(boosted_out_file, out_file)
            report["specificity_boost"]["promoted"] = True
            report["specificity_boost"]["reason"] = "candidate_not_worse"
        else:
            report["specificity_boost"]["promoted"] = False
            report["specificity_boost"]["reason"] = "candidate_worse_than_baseline"
            shutil.copyfile(q_report, q_recheck_report)
    except Exception as e:
        report["specificity_boost"]["promoted"] = False
        report["specificity_boost"]["reason"] = f"comparison_failed:{e}"
        shutil.copyfile(q_report, q_recheck_report)

    tts_dir = WS_CONTENT / f"tts_{now}"
    tts_cmd = [
        "py",
        "-3",
        str(WS / "tts_render_windows.py"),
        "--input",
        str(out_file),
        "--output-dir",
        str(tts_dir),
    ]
    report["tts_render"] = run_cmd(tts_cmd, timeout=900)

    if args.skip_assets:
        report["asset_render"] = {"ok": True, "skipped": True, "reason": "skip_assets"}
    else:
        asset_manifest = WS_CONTENT / f"asset_manifest_daily_{now}.json"
        asset_cmd = [
            "py",
            "-3",
            str(WS / "generate_pack_assets.py"),
            "--input",
            str(out_file),
            "--max-images",
            "7",
            "--boot-comfy",
            "--low-memory",
            "--quality-preset",
            "balanced",
            "--manifest-out",
            str(asset_manifest),
        ]
        report["asset_render"] = run_cmd(asset_cmd, timeout=2400)

    queue_json = WS_CONTENT / f"manual_publish_queue_{now}.json"
    queue_md = WS_CONTENT / f"manual_publish_queue_{now}.md"
    latest_queue_json = WS_CONTENT / "manual_publish_queue_latest.json"
    latest_queue_md = WS_CONTENT / "manual_publish_queue_latest.md"
    queue_cmd = [
        "py",
        "-3",
        str(WS / "manual_publish_queue_builder.py"),
        "--input-pack",
        str(out_file),
        "--input-quality",
        str(q_recheck_report),
        "--input-assets",
        str(WS_CONTENT / f"asset_manifest_daily_{now}.json") if not args.skip_assets else str(WS_CONTENT / f"asset_manifest_daily_20260308_205355.json"),
        "--tts-dir",
        str(tts_dir),
        "--output-json",
        str(queue_json),
        "--output-md",
        str(queue_md),
        "--latest-json",
        str(latest_queue_json),
        "--latest-md",
        str(latest_queue_md),
        "--generated-at",
        now,
    ]
    report["manual_publish_queue"] = run_cmd(queue_cmd, timeout=300)

    if args.skip_publisher:
        report["publisher"] = {"ok": True, "skipped": True, "reason": "skip_publisher"}
    else:
        pub_msg = (
            f"请读取文件 {out_file}。从中选择知乎和小红书各1条高分稿，执行测试发布（或草稿保存），"
            "返回每个平台的执行状态、URL/截图路径、失败原因（若有）。"
        )
        report["publisher"] = run_agent("publisher", pub_msg, 600)

    rpt = REPORT_DIR / f"pipeline_autorun_{now}.json"
    rpt.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(rpt),
                "topic": topic,
                "pack": str(out_file),
                "quality": str(q_report),
                "quality_recheck": str(q_recheck_report),
                "manual_publish_queue": str(queue_md),
                "manual_publish_queue_latest": str(latest_queue_md),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
