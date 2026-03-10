#!/usr/bin/env python3
"""Quality-gated production pipeline for supervised multi-platform publishing.

Flow:
1) topic selection (stability-first)
2) main-brain strategy
3) content generation + rewrite
4) final refine
5) matrix expansion (all platforms)
6) low-score repair
7) long-form guard (wechat/toutiao)
8) quality gate + specificity boost + recheck
9) tts generation
10) optional asset generation
11) manual publish queue
12) optional publisher dry run
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from content_novelty_policy import build_global_novelty_context, load_novelty_state, record_generated_pack
from news_guard import check_topic
from platform_monetization_mapper import build_full_platform_matrix, build_readiness_summary
from platform_direction_policy import build_platform_direction_context
from vertical_content_policy import pick_next_topic, record_selected_topic

ROOT = Path.home() / ".openclaw"
WS = ROOT / "workspace"
WS_CONTENT = ROOT / "workspace-content"
REPORT_DIR = WS / "reports"
METRICS_LATEST = WS_CONTENT / "metrics_analysis_latest.json"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
OPENCLAW = str(Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd")

ZH = "\u77e5\u4e4e"
XHS = "\u5c0f\u7ea2\u4e66"
DY = "\u6296\u97f3"
XG = "\u897f\u74dc\u89c6\u9891"
BILI = "B\u7ad9"
WB = "\u5fae\u535a"
WX = "\u516c\u4f17\u53f7"
TT = "\u5934\u6761"

def run_cmd(cmd: List[str], timeout: int = 600) -> Dict:
    started = time.time()
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
        "cmd": cmd,
        "stdout": (p.stdout or "").strip(),
        "stderr": (p.stderr or "").strip(),
        "duration_sec": round(time.time() - started, 2),
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
    except Exception as exc:
        return {
            "available": False,
            "error": str(exc),
            "platform_summary": {},
            "suggestions": [],
        }


def better_quality(candidate: Dict, baseline: Dict) -> bool:
    c = candidate.get("summary", {})
    b = baseline.get("summary", {})
    candidate_pass = int(c.get("pass_count", 0))
    baseline_pass = int(b.get("pass_count", 0))
    if candidate_pass != baseline_pass:
        return candidate_pass > baseline_pass
    return float(c.get("avg_score", 0.0)) >= float(b.get("avg_score", 0.0))


def select_topic() -> Dict:
    base = pick_next_topic()
    q = str(base.get("query", "")).strip()
    try:
        response = check_topic("http://127.0.0.1:8080", q)
        item = {
            **base,
            "confidence": response.confidence,
            "publishable": response.is_publishable,
            "reasons": response.reasons,
            "source": response.source,
        }
    except Exception as exc:
        item = {
            **base,
            "confidence": 0.0,
            "publishable": False,
            "reasons": [str(exc)],
            "source": "none",
        }
    confidence_bonus = min(float(item.get("confidence", 0.0)), 0.15)
    publishable_bonus = 0.08 if item.get("publishable") else 0.0
    rotation_score = float(item.get("rotation_score", float(item.get("priority", 0.8))))
    item["stable_score"] = round(rotation_score + confidence_bonus + publishable_bonus, 4)
    return item or {
        "query": "\u667a\u80fd\u5bb6\u5c45\u4e0e\u6570\u7801\u6d88\u8d39\u907f\u5751\u6307\u5357",
        "confidence": 0.0,
        "publishable": False,
        "reasons": ["fallback"],
        "source": "fallback",
        "priority": 0.8,
        "rotation_score": 0.8,
        "stable_score": 0.8,
        "fit_platforms": [ZH, XHS, DY, BILI, XG],
        "lane": "\u79d1\u6280\u6d88\u8d39",
        "sublane": "\u667a\u80fd\u5bb6\u5c45",
        "product_family": "\u6cdb\u79d1\u6280\u9009\u8d2d",
        "video_derivatives": [BILI, XG],
    }


def latest_asset_manifest(default_dir: Path) -> Optional[Path]:
    files = sorted(default_dir.glob("asset_manifest_daily_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def require_file(step_key: str, report: Dict, path: Path) -> bool:
    if path.exists():
        return True
    report[step_key]["ok"] = False
    report[step_key]["missing_file"] = str(path)
    if not report[step_key].get("stderr"):
        report[step_key]["stderr"] = f"missing expected file: {path}"
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-publisher", action="store_true")
    parser.add_argument("--skip-assets", action="store_true")
    args = parser.parse_args()

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    report: Dict[str, Dict] = {
        "time": now,
        "topic": {},
        "topic_policy": {},
        "platform_direction": {},
        "novelty_context": {},
        "matrix_strategy": {},
        "readiness_strategy": {},
        "metrics_feedback": {},
        "main_brain": {},
        "autotune": {},
        "final_refine": {},
        "matrix_expand": {},
        "repair": {},
        "longform_guard": {},
        "quality_gate": {},
        "specificity_boost": {},
        "quality_recheck": {},
        "tts_render": {},
        "asset_render": {},
        "manual_publish_queue": {},
        "publisher": {},
    }

    topic_info = select_topic()
    topic = topic_info["query"]
    report["topic"] = topic_info
    report["topic_policy"] = {
        "primary_vertical": topic_info.get("primary_vertical", ""),
        "primary_audience": topic_info.get("primary_audience", ""),
        "lane": topic_info.get("lane", ""),
        "sublane": topic_info.get("sublane", ""),
        "product_family": topic_info.get("product_family", ""),
        "video_derivatives": topic_info.get("video_derivatives", []),
        "rotation_reasons": topic_info.get("rotation_reasons", []),
        "cross_format_plan": topic_info.get("cross_format_plan", {}),
    }
    record_selected_topic(topic_info, now)

    matrix = build_full_platform_matrix()
    readiness = build_readiness_summary(list(matrix.keys()))
    platform_direction = build_platform_direction_context(list(matrix.keys()))
    novelty_state = load_novelty_state()
    novelty_context = build_global_novelty_context(novelty_state)
    metrics_feedback = load_metrics_context(METRICS_LATEST)
    report["platform_direction"] = platform_direction
    report["novelty_context"] = novelty_context
    report["matrix_strategy"] = matrix
    report["readiness_strategy"] = readiness
    report["metrics_feedback"] = metrics_feedback

    mb_prompt = (
        f"\u57fa\u4e8e\u9009\u9898\u201c{topic}\u201d\uff0c\u5e73\u53f0\u53d8\u73b0\u77e9\u9635={json.dumps(matrix, ensure_ascii=False)}\u3002"
        f"\u9636\u6bb5\u5206\u7ec4={json.dumps(readiness, ensure_ascii=False)}\u3002"
        f"\u8fd1\u671f\u53cd\u9988={json.dumps(metrics_feedback, ensure_ascii=False)}\u3002"
        f"\u8d5b\u9053\u89c4\u5219={json.dumps(report['topic_policy'], ensure_ascii=False)}\u3002"
        f"\u5e73\u53f0\u65b9\u5411={json.dumps(platform_direction, ensure_ascii=False)}\u3002"
        f"\u53bb\u91cd\u4e0e\u51b7\u5374={json.dumps(novelty_context, ensure_ascii=False)}\u3002"
        "\u8bf7\u7ed9\u51fa\u4eca\u65e5\u53d1\u5e03\u7b56\u7565\uff0c\u53ea\u8f93\u51faJSON\uff0c\u5b57\u6bb5:"
        "audience,platform_priority,conversion_goal,platform_roles,guardrails"
    )
    report["main_brain"] = run_agent("main-brain", mb_prompt, 220)

    raw_out_file = WS_CONTENT / f"daily_pack_raw_{now}.json"
    out_file = WS_CONTENT / f"daily_pack_{now}.json"
    topic_file = WS_CONTENT / f"topic_{now}.txt"
    topic_file.write_text(topic, encoding="utf-8")

    report["autotune"] = run_cmd(
        [
            "py",
            "-3",
            str(WS_CONTENT / "content_autotune_runner.py"),
            "--topic-file",
            str(topic_file),
            "--metrics-file",
            str(METRICS_LATEST),
            "--min-score",
            "85",
            "--max-rewrite-rounds",
            "3",
            "--out",
            str(raw_out_file),
        ],
        timeout=1400,
    )
    require_file("autotune", report, raw_out_file)

    report["final_refine"] = run_cmd(
        [
            "py",
            "-3",
            str(WS / "final_publish_refiner.py"),
            "--input",
            str(raw_out_file),
            "--output",
            str(out_file),
            "--min-score",
            "85",
        ],
        timeout=1000,
    )
    require_file("final_refine", report, out_file)

    report["matrix_expand"] = run_cmd(
        [
            "py",
            "-3",
            str(WS / "matrix_pack_expander.py"),
            "--input",
            str(out_file),
            "--output",
            str(out_file),
            "--min-score",
            "85",
        ],
        timeout=1200,
    )

    report["repair"] = run_cmd(
        [
            "py",
            "-3",
            str(WS / "low_score_repair_runner.py"),
            "--input",
            str(out_file),
            "--output",
            str(out_file),
            "--min-score",
            "85",
        ],
        timeout=1200,
    )

    report["longform_guard"] = run_cmd(
        [
            "py",
            "-3",
            str(WS / "longform_guard_runner.py"),
            "--input",
            str(out_file),
            "--output",
            str(out_file),
            "--min-score",
            "85",
        ],
        timeout=300,
    )

    q_report = WS_CONTENT / f"quality_{now}.json"
    report["quality_gate"] = run_cmd(
        [
            "py",
            "-3",
            str(WS_CONTENT / "content_quality_gate.py"),
            "--input",
            str(out_file),
            "--output",
            str(q_report),
            "--min-score",
            "85",
        ],
        timeout=300,
    )
    require_file("quality_gate", report, q_report)

    boosted_out_file = WS_CONTENT / f"daily_pack_{now}_boosted.json"
    if out_file.exists():
        shutil.copyfile(out_file, boosted_out_file)

    report["specificity_boost"] = run_cmd(
        [
            "py",
            "-3",
            str(WS / "specificity_boost_runner.py"),
            "--input",
            str(boosted_out_file),
            "--output",
            str(boosted_out_file),
            "--min-score",
            "85",
        ],
        timeout=300,
    )

    q_recheck_report = WS_CONTENT / f"quality_{now}_recheck.json"
    report["quality_recheck"] = run_cmd(
        [
            "py",
            "-3",
            str(WS_CONTENT / "content_quality_gate.py"),
            "--input",
            str(boosted_out_file),
            "--output",
            str(q_recheck_report),
            "--min-score",
            "85",
        ],
        timeout=300,
    )

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
    except Exception as exc:
        report["specificity_boost"]["promoted"] = False
        report["specificity_boost"]["reason"] = f"comparison_failed:{exc}"
        if q_report.exists():
            shutil.copyfile(q_report, q_recheck_report)

    tts_dir = WS_CONTENT / f"tts_{now}"
    report["tts_render"] = run_cmd(
        [
            "py",
            "-3",
            str(WS / "tts_render_windows.py"),
            "--input",
            str(out_file),
            "--output-dir",
            str(tts_dir),
        ],
        timeout=900,
    )

    if args.skip_assets:
        report["asset_render"] = {"ok": True, "skipped": True, "reason": "skip_assets"}
        asset_manifest = latest_asset_manifest(WS_CONTENT)
    else:
        asset_manifest = WS_CONTENT / f"asset_manifest_daily_{now}.json"
        report["asset_render"] = run_cmd(
            [
                "py",
                "-3",
                str(WS / "generate_pack_assets.py"),
                "--input",
                str(out_file),
                "--max-images",
                "8",
                "--boot-comfy",
                "--low-memory",
                "--quality-preset",
                "balanced",
                "--manifest-out",
                str(asset_manifest),
            ],
            timeout=2600,
        )
        if not asset_manifest.exists():
            asset_manifest = latest_asset_manifest(WS_CONTENT)

    queue_json = WS_CONTENT / f"manual_publish_queue_{now}.json"
    queue_md = WS_CONTENT / f"manual_publish_queue_{now}.md"
    latest_queue_json = WS_CONTENT / "manual_publish_queue_latest.json"
    latest_queue_md = WS_CONTENT / "manual_publish_queue_latest.md"
    queue_args = [
        "py",
        "-3",
        str(WS / "manual_publish_queue_builder.py"),
        "--input-pack",
        str(out_file),
        "--input-quality",
        str(q_recheck_report),
        "--input-assets",
        str(asset_manifest) if asset_manifest else "",
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
    report["manual_publish_queue"] = run_cmd(queue_args, timeout=300)

    if args.skip_publisher:
        report["publisher"] = {"ok": True, "skipped": True, "reason": "skip_publisher"}
    else:
        pub_msg = (
            f"\u8bf7\u8bfb\u53d6\u6587\u4ef6{out_file}\uff0c\u9009\u62e9{ZH}\u548c{XHS}\u9ad8\u5206\u7a3f\u5404\u4e00\u6761\u6267\u884c\u53d1\u5e03\u9884\u68c0\u3002"
            "\u8fd4\u56de\u6267\u884c\u72b6\u6001\u3001URL\u6216\u622a\u56fe\u8def\u5f84\u3001\u5931\u8d25\u539f\u56e0\u3002"
        )
        report["publisher"] = run_agent("publisher", pub_msg, 600)

    try:
        payload = load_json(out_file)
        record_generated_pack(payload, now, topic_info=topic_info, state=novelty_state)
    except Exception as exc:
        report["novelty_context"]["record_error"] = str(exc)

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
                "asset_manifest": str(asset_manifest) if asset_manifest else "",
                "manual_publish_queue": str(queue_md),
                "manual_publish_queue_latest": str(latest_queue_md),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
