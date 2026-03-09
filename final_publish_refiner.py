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

from content_autotune_runner import (  # type: ignore
    BILI,
    DY,
    TT,
    WB,
    WX,
    XG,
    XHS,
    ZH,
    PLATFORM_BRIEFS,
    build_publisher_review_prompt,
    extract_json,
    fallback_review,
    generate_asset_prompts,
    run_agent,
    sanitize_draft,
)
from content_quality_gate import score_one  # type: ignore
from platform_monetization_mapper import attach_monetization_plans
from platform_visual_templates import attach_visual_templates
from publish_appendix_builder import build_appendices
from video_publish_pack_builder import build_video_publish_pack


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
        f"编辑意见：weak_point={weak_point}，fix_now={fix_now}。"
        "目标：让文案更像真实作者写的专业内容，而不是提示词拼装。"
        "硬要求："
        "1) 保留转化力，但去掉模板味。"
        "2) 让证据表达更自然，减少重复的固定口头禅。"
        "3) 严禁收益承诺、虚假社会背书、伪官方语气。"
        "4) 结论必须明确，执行动作必须具体。"
        f"5) 语气={brief.get('voice', '')}，CTA={brief.get('conversion', '')}。"
        f"6) 正文字数保持在{brief.get('body_range', '平台要求')}。"
        "7) 输出字段platform,title,hook,body,cta,tags。"
    )


def polish_xiaohongshu(draft: Dict[str, Any]) -> Dict[str, Any]:
    current = dict(draft)
    lines = [line.strip() for line in str(current.get("body", "")).splitlines() if line.strip()]
    if len(lines) < 4:
        body = [
            str(current.get("body", "")).strip(),
            "先别把工具堆满，先跑通一个最顺手的场景。",
            "按公开资料和测试环境的常见做法看，先做1个入口、3个动作、1个领取口更稳。",
        ]
        lines = [line for line in body if line]
    if not any("公开资料" in line or "测试环境" in line or "实测" in line or "来源" in line for line in lines):
        lines.insert(1, "按公开资料和测试环境的常见做法看，先把一个高频动作跑顺，再扩工具组合。")
    current["body"] = "\n".join(lines[:6])
    hook = str(current.get("hook", "")).strip()
    if hook and "先看结论" not in hook:
        current["hook"] = f"先看结论：{hook}"
    return current


def polish_weibo(draft: Dict[str, Any]) -> Dict[str, Any]:
    current = dict(draft)
    body = str(current.get("body", "")).replace("；", "，").replace("。", "。 ")
    sentences = [x.strip() for x in body.split("。") if x.strip()]
    if len(sentences) > 4:
        sentences = sentences[:4]
    current["body"] = "。\n".join(sentences) + ("。" if sentences else "")
    return current


def polish_short_video(draft: Dict[str, Any]) -> Dict[str, Any]:
    current = dict(draft)
    body = str(current.get("body", "")).replace("；", "。").replace("！", "。")
    lines = [x.strip() for x in body.split("。") if x.strip()]
    current["body"] = "\n".join(lines[:7])
    return current


def polish_long_form(draft: Dict[str, Any]) -> Dict[str, Any]:
    current = dict(draft)
    platform = str(current.get("platform", "")).strip()
    body = str(current.get("body", "")).strip()
    paragraphs = [p.strip() for p in body.split("\n") if p.strip()]

    if platform == ZH:
        required = [
            "适合谁：如果你现在最大的痛点是信息太多、落地太少，这类结构比空泛观点更有用。",
            "不适合谁：如果你只想一次性找个万能工具，而不愿意按步骤执行，这套方法帮助有限。",
            "常见误区：先买工具、后找场景；先堆素材、后做判断；先做复杂系统、后验证最小结果。",
            "可执行步骤：第一步定场景，第二步定判断标准，第三步只保留一个复盘指标。",
            "落地建议：把今天要做的动作写成清单，再决定哪些环节值得自动化。",
        ]
    elif platform == WX:
        required = [
            "适用场景：适合需要持续输出内容、需要把阅读变成资料领取和后续转化的人。",
            "不适用场景：如果你只是想写一篇纯观点型文章，这种结构会显得太重。",
            "常见误区：只看标题，不看承接；只给观点，不给动作；同时塞入多个CTA。",
            "执行顺序：先写结论，再写误区，再写步骤，最后只留一个资料入口。",
            "案例提示：哪怕只补一个真实使用场景，也比泛泛而谈更容易涨关注。",
        ]
    else:
        required = [
            "适用场景：适合做系列内容、做长图文沉淀、做清单型承接。",
            "常见误区：标题很猛，正文很空；段落很多，结论不清；动作太多，转化太散。",
            "执行顺序：先给总判断，再讲误区，再给步骤，最后只留一个动作。",
            "案例提示：补一个执行前后差异点，比补十句空观点更有效。",
        ]

    merged = paragraphs[:]
    for block in required:
        if all(block[:8] not in paragraph for paragraph in merged):
            merged.append(block)

    current["body"] = "\n\n".join(merged)
    return current


def editorial_structure_pass(draft: Dict[str, Any]) -> Dict[str, Any]:
    platform = str(draft.get("platform", "")).strip()
    current = dict(draft)
    if platform == XHS:
        return polish_xiaohongshu(current)
    if platform == WB:
        return polish_weibo(current)
    if platform in {DY, XG, BILI}:
        return polish_short_video(current)
    if platform in {ZH, WX, TT}:
        return polish_long_form(current)
    return current


def rescore(drafts: List[Dict[str, Any]], min_score: float) -> List[Dict[str, Any]]:
    rows = []
    for draft in drafts:
        score = score_one(draft, min_score)
        rows.append(
            {
                "platform": draft.get("platform", ""),
                "score": score.total_score,
                "pass": score.pass_gate,
                "issues": score.issues,
                "subscores": score.subscores,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-score", type=float, default=85.0)
    args = parser.parse_args()

    pack = load_pack(Path(args.input))
    topic = str(pack.get("topic", "")).strip()
    research = pack.get("research_context", {})
    feedback = pack.get("metrics_feedback", {})
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    review_mapping = review_map(pack)

    refined: List[Dict[str, Any]] = []
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        review = review_mapping.get(platform, {})
        current = draft
        if review:
            try:
                payload = run_agent("content", build_final_refine_prompt(topic, draft, review), timeout=260)
                obj = extract_json(payload)
                if isinstance(obj, dict):
                    current = obj
            except Exception:
                current = draft
        current = editorial_structure_pass(current)
        refined.append(sanitize_draft(topic, current, research=research, feedback=feedback))

    scores = rescore(refined, args.min_score)
    try:
        publisher_review = extract_json(
            run_agent("publisher", build_publisher_review_prompt(topic, refined), timeout=240)
        )
    except Exception:
        publisher_review = fallback_review(refined, args.min_score)
    assets = generate_asset_prompts(topic, refined)

    out_payload = {
        **pack,
        "drafts": refined,
        "scores": scores,
        "publisher_review": publisher_review,
        "assets": assets,
        "appendices": build_appendices({"topic": topic, "drafts": refined}),
        "final_review_applied": True,
    }
    out_payload = attach_monetization_plans(out_payload)
    out_payload = attach_visual_templates(out_payload)
    out_payload["video_publish_kits"] = build_video_publish_pack(out_payload)
    Path(args.output).write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "scores": scores}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
