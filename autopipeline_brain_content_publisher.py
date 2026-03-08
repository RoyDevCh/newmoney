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

from news_guard import check_topic
from platform_monetization_mapper import build_full_platform_matrix, build_readiness_summary

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

STABLE_TOPICS = [
    {
        "query": "\u6570\u7801\u88c5\u5907\u907f\u5751\u4e0e\u9009\u8d2d\u5efa\u8bae 2026",
        "priority": 1.0,
        "fit_platforms": [ZH, DY, XG, BILI, WB, TT],
    },
    {
        "query": "\u529e\u516c\u6548\u7387\u5de5\u5177\u6e05\u5355\u4e0e\u4fe1\u606f\u7ba1\u7406\u5de5\u4f5c\u6d41",
        "priority": 0.99,
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX, TT],
    },
    {
        "query": "\u5bb6\u7528\u5c0f\u7535\u5668\u771f\u5b9e\u4f7f\u7528\u573a\u666f\u4e0e\u907f\u5751\u6e05\u5355",
        "priority": 0.97,
        "fit_platforms": [ZH, XHS, DY, XG, BILI, TT],
    },
    {
        "query": "\u5185\u5bb9\u751f\u4ea7\u63d0\u6548\u4e0e\u53d8\u73b0\u6d41\u7a0b\u62c6\u89e3",
        "priority": 0.95,
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX],
    },
    {
        "query": "\u5546\u4e1a\u6848\u4f8b\u62c6\u89e3\u4e0e\u54c1\u724c\u589e\u957f\u590d\u76d8",
        "priority": 0.94,
        "fit_platforms": [ZH, DY, XG, BILI, WB, WX, TT],
    },
    {
        "query": "\u77e5\u8bc6\u7ba1\u7406\u4e0e\u4e2a\u4eba\u7cfb\u7edf\u642d\u5efa",
        "priority": 0.93,
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX],
    },
    {
        "query": "\u5386\u53f2\u4e8b\u4ef6\u91cc\u7684\u5546\u4e1a\u4e0e\u8ba4\u77e5\u542f\u53d1",
        "priority": 0.91,
        "fit_platforms": [ZH, XG, BILI, WB, WX, TT],
    },
    {
        "query": "AI\u5de5\u5177\u6e05\u5355\u4e0e\u6548\u7387\u5de5\u4f5c\u6d41",
        "priority": 0.9,
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WB, WX, TT],
    },
]


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
    best: Optional[Dict] = None
    for candidate in STABLE_TOPICS:
        q = candidate["query"]
        try:
            response = check_topic("http://127.0.0.1:8080", q)
            item = {
                "query": q,
                "confidence": response.confidence,
                "publishable": response.is_publishable,
                "reasons": response.reasons,
                "source": response.source,
                "priority": candidate["priority"],
                "fit_platforms": candidate["fit_platforms"],
            }
        except Exception as exc:
            item = {
                "query": q,
                "confidence": 0.0,
                "publishable": False,
                "reasons": [str(exc)],
                "source": "none",
                "priority": candidate["priority"],
                "fit_platforms": candidate["fit_platforms"],
            }
        item["stable_score"] = round(item["confidence"] * 0.7 + item["priority"] * 0.3, 4)
        if best is None or item["stable_score"] > best["stable_score"]:
            best = item

    return best or {
        "query": "\u5185\u5bb9\u751f\u4ea7\u63d0\u6548\u4e0e\u53d8\u73b0",
        "confidence": 0.0,
        "publishable": False,
        "reasons": ["fallback"],
        "source": "fallback",
        "priority": 0.8,
        "fit_platforms": [ZH, XHS, DY, BILI],
        "stable_score": 0.8,
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

    matrix = build_full_platform_matrix()
    readiness = build_readiness_summary(list(matrix.keys()))
    metrics_feedback = load_metrics_context(METRICS_LATEST)
    report["matrix_strategy"] = matrix
    report["readiness_strategy"] = readiness
    report["metrics_feedback"] = metrics_feedback

    mb_prompt = (
        f"\u57fa\u4e8e\u9009\u9898\u201c{topic}\u201d\uff0c\u5e73\u53f0\u53d8\u73b0\u77e9\u9635={json.dumps(matrix, ensure_ascii=False)}\u3002"
        f"\u9636\u6bb5\u5206\u7ec4={json.dumps(readiness, ensure_ascii=False)}\u3002"
        f"\u8fd1\u671f\u53cd\u9988={json.dumps(metrics_feedback, ensure_ascii=False)}\u3002"
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
