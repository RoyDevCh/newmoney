#!/usr/bin/env python3
"""Final editorial pass for monetization packs before publishing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

CONTENT_WS = Path.home() / ".openclaw" / "workspace-content"
if str(CONTENT_WS) not in sys.path:
    sys.path.insert(0, str(CONTENT_WS))

from content_autotune_runner import (
    PLATFORM_BRIEFS,
    build_publisher_review_prompt,
    extract_json,
    fallback_review,
    generate_asset_prompts,
    run_agent,
    sanitize_draft,
)
from content_quality_gate import score_one


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def review_map(pack: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    reviews = pack.get("publisher_review", {}).get("platform_reviews", [])
    mapping: Dict[str, Dict[str, Any]] = {}
    for item in reviews:
        if isinstance(item, dict):
            platform = str(item.get("platform", "")).strip()
            if platform:
                mapping[platform] = item
    return mapping


def build_final_refine_prompt(topic: str, draft: Dict[str, Any], review: Dict[str, Any]) -> str:
    platform = str(draft.get("platform", "")).strip()
    brief = PLATFORM_BRIEFS.get(platform, {})
    weak_point = review.get("weak_point", "")
    fix_now = review.get("fix_now", "")
    return (
        "只输出JSON对象。你是平台主编，负责发布前最后一轮精修。"
        f"主题={topic}，平台={platform}，当前稿件={json.dumps(draft, ensure_ascii=False)}。"
        f"编辑部意见：weak_point={weak_point}；fix_now={fix_now}。"
        "目标：让文案更像真人写的专业内容，而不是提示词拼装。"
        "硬要求："
        "1) 保留转化力，但去掉模板味；"
        "2) 少用重复的'按实测环境/按公开评测'，改成更自然的证据表达；"
        "3) 严禁收益承诺、虚假社会背书、伪官方语气；"
        "4) 结论必须明确，执行动作必须具体；"
        f"5) 语气={brief.get('voice','')}; CTA={brief.get('conversion','')};"
        f"6) 正文长度保持在{brief.get('body_range','平台要求')}；"
        "7) 输出字段platform,title,hook,body,cta,tags。"
    )


def rescore(drafts: List[Dict[str, Any]], min_score: float) -> List[Dict[str, Any]]:
    rows = []
    for draft in drafts:
        s = score_one(draft, min_score)
        rows.append(
            {
                "platform": draft.get("platform", ""),
                "score": s.total_score,
                "pass": s.pass_gate,
                "issues": s.issues,
                "subscores": s.subscores,
            }
        )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-score", type=float, default=85.0)
    args = ap.parse_args()

    pack = load_pack(Path(args.input))
    topic = str(pack.get("topic", "")).strip()
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    rmap = review_map(pack)

    refined: List[Dict[str, Any]] = []
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        review = rmap.get(platform, {})
        current = draft
        if review:
            try:
                payload = run_agent("content", build_final_refine_prompt(topic, draft, review), timeout=260)
                obj = extract_json(payload)
                if isinstance(obj, dict):
                    current = obj
            except Exception:
                current = draft
        refined.append(sanitize_draft(topic, current))

    scores = rescore(refined, args.min_score)
    try:
        publisher_review = extract_json(run_agent("publisher", build_publisher_review_prompt(topic, refined), timeout=240))
    except Exception:
        publisher_review = fallback_review(refined, args.min_score)
    assets = generate_asset_prompts(topic, refined)

    out_payload = {
        **pack,
        "drafts": refined,
        "scores": scores,
        "publisher_review": publisher_review,
        "assets": assets,
        "final_review_applied": True,
    }
    Path(args.output).write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "scores": scores}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
