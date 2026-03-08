#!/usr/bin/env python3
"""Generate monetization-grade content packs with strategy, QA, and asset prompts.

Example:
  py -3 content_autotune_runner.py --topic "AI办公自动化提效" --platforms 知乎 小红书 抖音 B站
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

from content_quality_gate import DraftScore, score_one

OPENCLAW_CMD = Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd"
NODE_BIN = Path("C:/Program Files/nodejs/node.exe")
OPENCLAW_ENTRY = Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "openclaw" / "openclaw.mjs"

PLATFORM_BRIEFS = {
    "知乎": {
        "body_range": "550-900字",
        "voice": "理性、专业、像懂行业的答主",
        "conversion": "评论/收藏/私信关键词领取清单",
        "angle": "结构化拆解、红黑榜、避坑指南、ROI分析",
        "visual": "横版可信赖科技封面，留足标题空间，避免花哨emoji",
    },
    "小红书": {
        "body_range": "180-420字",
        "voice": "清爽、具体、有生活场景，不装专家",
        "conversion": "收藏/关注/评论关键词",
        "angle": "清单式、真实体验、低门槛立刻可做",
        "visual": "3:4高级感生产力场景，干净桌面，强氛围光线",
    },
    "抖音": {
        "body_range": "140-260字",
        "voice": "口语、快节奏、每句一个点",
        "conversion": "关注/主页/评论关键词",
        "angle": "三秒冲突、错法纠正、一步步可执行动作",
        "visual": "高反差首帧，中心主体大，适合短视频封面",
    },
    "B站": {
        "body_range": "320-700字",
        "voice": "证据先行、带实测感、像硬核UP主脚本",
        "conversion": "三连/评论区领取资源/下期选题互动",
        "angle": "横评、流程演示、案例拆解、效率实验",
        "visual": "横版纪录片感科技场景，细节多但不杂乱",
    },
}

PLATFORM_MIN_BODY = {
    "知乎": 550,
    "小红书": 180,
    "抖音": 140,
    "B站": 320,
}


def run_agent(agent: str, prompt: str, timeout: int = 300) -> str:
    compact_prompt = re.sub(r"\s+", " ", prompt).strip()
    cmd: List[str]
    if NODE_BIN.exists() and OPENCLAW_ENTRY.exists():
        cmd = [
            str(NODE_BIN),
            str(OPENCLAW_ENTRY),
            "agent",
            "--agent",
            agent,
            "--message",
            compact_prompt,
            "--timeout",
            str(timeout),
            "--json",
        ]
    else:
        cmd = [
            "cmd",
            "/c",
            str(OPENCLAW_CMD),
            "agent",
            "--agent",
            agent,
            "--message",
            compact_prompt,
            "--timeout",
            str(timeout),
            "--json",
        ]
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout + 60,
    )
    if p.returncode != 0:
        raise RuntimeError((p.stderr or "").strip() or f"returncode={p.returncode}")
    return unwrap_openclaw_payload((p.stdout or "").strip())


def extract_json(text: str) -> Any:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty text")
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.S | re.I)
    candidate = match.group(1) if match else text
    for left, right in [("[", "]"), ("{", "}")]:
        start = candidate.find(left)
        end = candidate.rfind(right)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except Exception:
                continue
    raise ValueError("could not extract json")


def unwrap_openclaw_payload(raw: str) -> str:
    data = extract_json(raw)
    if isinstance(data, dict):
        payloads = data.get("result", {}).get("payloads", [])
        if payloads and isinstance(payloads[0], dict):
            text = payloads[0].get("text")
            if isinstance(text, str):
                return text.strip()
    return raw.strip()


def normalize_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if "drafts" in data and isinstance(data["drafts"], list):
            return [x for x in data["drafts"] if isinstance(x, dict)]
        return [data]
    raise ValueError("Unsupported json structure")


def select_best_drafts(drafts: List[Dict[str, Any]], platforms: List[str], min_score: float) -> List[Dict[str, Any]]:
    best: List[Dict[str, Any]] = []
    for platform in platforms:
        candidates = [d for d in drafts if str(d.get("platform", "")).strip() == platform]
        if not candidates:
            continue
        chosen = max(candidates, key=lambda d: score_one(d, min_score).total_score)
        best.append(chosen)
    return best


def build_strategy_prompt(topic: str, platforms: List[str]) -> str:
    return (
        f"只输出JSON对象。主题={topic}，目标平台={'、'.join(platforms)}。"
        "给出一套能赚钱但不过度营销的内容策略，字段：audience, pain_point, conversion_goal, offer, "
        "platform_priority, angle, proof_points。proof_points必须是3项数组。"
    )


def build_platform_rules(platforms: List[str]) -> str:
    blocks = []
    for platform in platforms:
        brief = PLATFORM_BRIEFS.get(platform, {})
        blocks.append(
            f"{platform}: 正文{brief.get('body_range','')}; 语气={brief.get('voice','')}; "
            f"转化={brief.get('conversion','')}; 角度={brief.get('angle','')}"
        )
    return " | ".join(blocks)


def build_init_prompt(topic: str, platforms: List[str], strategy: Dict[str, Any]) -> str:
    strategy_json = json.dumps(strategy, ensure_ascii=False)
    return (
        f"只输出JSON数组。基于主题“{topic}”和策略{strategy_json}，为{'、'.join(platforms)}各生成且仅生成1条内容。"
        "每个平台字段必须包含platform,title,hook,body,cta,tags。"
        "要求："
        "1) 先给结论或冲突，再给证据，再给动作；"
        "2) 出现数字时必须使用按公开评测/按实测环境/按官方信息的表达；"
        "3) 去掉绝对化、内幕、包赚、月入、收入翻倍等高风险词；"
        "4) 不要虚构学员人数、企业服务数、收益数字；"
        "5) 转化方式优先用工具清单、模板包、咨询清单、资源包，而不是直接收益承诺；"
        "4) 不要输出markdown，不要解释；"
        f"6) 平台细则：{build_platform_rules(platforms)}。"
    )


def build_rewrite_prompt(topic: str, draft: Dict[str, Any], score: DraftScore, strategy: Dict[str, Any]) -> str:
    platform = str(draft.get("platform", "")).strip()
    brief = PLATFORM_BRIEFS.get(platform, {})
    return (
        "只输出JSON对象。你是能把内容改到可转化水平的平台增长编辑。"
        f"主题={topic}，平台={platform}，策略={json.dumps(strategy, ensure_ascii=False)}，"
        f"当前稿件={json.dumps(draft, ensure_ascii=False)}，问题={';'.join(score.issues) or '无'}。"
        "重写要求："
        "1) 前50字必须有冲突点或反常识；"
        "2) 正文结构只能是结论->证据->执行动作；"
        "3) 删除所有空话、套话、未经验证的硬结论；"
        "4) 数字必须加来源语气；"
        f"5) 正文长度遵守{brief.get('body_range','平台要求')}；"
        f"6) 语气={brief.get('voice','')}; CTA={brief.get('conversion','')};"
        "7) 严禁出现月入、月赚、收入翻倍、服务多少企业、累计多少学员等不可核实背书；"
        "8) 输出字段platform,title,hook,body,cta,tags。"
    )


def build_publisher_review_prompt(topic: str, drafts: List[Dict[str, Any]]) -> str:
    return (
        "只输出JSON对象。你是商业内容审核编辑。"
        f"主题={topic}，请审核这些稿件是否具备'能赚钱'的发布条件：{json.dumps(drafts, ensure_ascii=False)}。"
        "输出字段：verdict, platform_reviews, monetization_risks, next_actions。"
        "其中 platform_reviews 必须是数组，每项字段：platform, pass, strongest_selling_point, weak_point, fix_now。"
    )


def build_visual_prompt(topic: str, draft: Dict[str, Any]) -> str:
    platform = str(draft.get("platform", "")).strip()
    brief = PLATFORM_BRIEFS.get(platform, {})
    return (
        "只输出JSON对象。基于以下内容生成一个高质量封面/首图提示词包。"
        f"主题={topic}，平台={platform}，稿件={json.dumps(draft, ensure_ascii=False)}。"
        f"视觉方向={brief.get('visual','科技商业内容封面')}。"
        "字段：platform, prompt, negative_prompt, composition, aspect_ratio。"
    )


def optimize_draft(
    topic: str,
    draft: Dict[str, Any],
    strategy: Dict[str, Any],
    min_score: float,
    max_rewrite_rounds: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    current = draft
    score = score_one(current, min_score)
    rounds = 0

    while (not score.pass_gate) and rounds < max_rewrite_rounds:
        rounds += 1
        rewritten = run_agent("content", build_rewrite_prompt(topic, current, score, strategy), timeout=300)
        obj = extract_json(rewritten)
        if isinstance(obj, list):
            obj = obj[0]
        if not isinstance(obj, dict):
            break
        current = obj
        score = score_one(current, min_score)

    return current, {
        "platform": current.get("platform", ""),
        "score": score.total_score,
        "pass": score.pass_gate,
        "issues": score.issues,
        "subscores": score.subscores,
        "rounds": rounds,
    }


def generate_asset_prompts(topic: str, drafts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assets: List[Dict[str, Any]] = []
    for draft in drafts:
        try:
            payload = run_agent("multimodal", build_visual_prompt(topic, draft), timeout=240)
            asset = extract_json(payload)
            if isinstance(asset, dict):
                assets.append(asset)
        except Exception as exc:
            assets.append(
                {
                    "platform": draft.get("platform", ""),
                    "error": str(exc),
                }
            )
    return assets


def strip_visual_noise(text: str, keep_small: bool) -> str:
    cleaned = re.sub(r"[⭐✨🔥💰🚀📈📌✅❌💡👉👈🎯🎬🎥🎨🧠💻📊📎📍📣😍🥹😊😎🤖🎁]+", "", text)
    if not keep_small:
        cleaned = re.sub(r"[0-9]\ufe0f?\u20e3", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def scrub_claims(text: str) -> str:
    replacements = [
        (r"月入\s*\d+\+?", "效率提升明显"),
        (r"月赚\s*\d+\+?", "更容易承接项目"),
        (r"收入翻倍", "产能提升明显"),
        (r"多赚\s*\d+\+?", "更容易提高接单效率"),
        (r"服务\s*\d+\+?\s*家企业", "服务过不同团队场景"),
        (r"累计学员\s*\d+\+?", "有持续实践反馈"),
        (r"\d+\+?\s*企业客户", "不同企业场景"),
        (r"\d+\+?\s*学员", "不同使用者"),
    ]
    current = text
    for pattern, replacement in replacements:
        current = re.sub(pattern, replacement, current)
    return current


def extend_body_if_needed(platform: str, topic: str, body: str) -> str:
    minimum = PLATFORM_MIN_BODY.get(platform, 0)
    if len(body) >= minimum:
        return body

    extra = []
    if platform == "知乎":
        extra = [
            "",
            "【适合谁先上手】",
            f"如果你当前处理的是重复性的{topic}相关工作，优先从资料整理、初稿生成、信息归纳这类低风险环节开始，不要一上来就把判断类工作全部交给模型。",
            "",
            "【落地清单】",
            "第一步，先列出一周内最耗时的3个重复动作；第二步，给每个动作准备固定输入模板；第三步，只在能快速人工复核的环节接入AI；第四步，每周复盘一次节省下来的时间有没有真正转化成更高价值产出。",
            "",
            "【常见误区】",
            "很多人失败不是因为工具不行，而是没有先定义产出标准，也没有把提示词、素材来源、复核动作做成固定流程。流程没定住，工具越多反而越乱。",
        ]
    elif platform == "B站":
        extra = [
            "",
            "【补充建议】",
            "真正想把这套流程用起来，建议先从单点工作流做起，例如会议纪要、文案初稿或信息检索，不要一口气接太多模块，否则维护成本会反噬效率。",
        ]
    elif platform == "抖音":
        extra = [
            "",
            "记住，先做一个场景跑通，再复制到第二个场景。",
        ]
    elif platform == "小红书":
        extra = [
            "",
            "先把一个小动作用顺，再扩到更多场景，体感会很明显。",
        ]

    merged = body.rstrip() + "\n" + "\n".join(extra).strip()
    return merged.strip()


def sanitize_draft(topic: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    platform = str(draft.get("platform", "")).strip()
    keep_small = platform in {"小红书", "抖音"}
    cleaned = dict(draft)
    for key in ["title", "hook", "body", "cta"]:
        value = str(cleaned.get(key, "")).strip()
        value = scrub_claims(value)
        value = strip_visual_noise(value, keep_small=keep_small)
        cleaned[key] = value
    cleaned["body"] = extend_body_if_needed(platform, topic, str(cleaned.get("body", "")))
    cleaned["tags"] = [strip_visual_noise(scrub_claims(str(x)), keep_small=True) for x in cleaned.get("tags", []) if str(x).strip()]
    return cleaned


def fallback_review(drafts: List[Dict[str, Any]], min_score: float) -> Dict[str, Any]:
    reviews = []
    for draft in drafts:
        s = score_one(draft, min_score)
        reviews.append(
            {
                "platform": draft.get("platform", ""),
                "pass": s.pass_gate,
                "strongest_selling_point": "hook+cta基本成型" if s.total_score >= min_score else "需要继续重写",
                "weak_point": ",".join(s.issues[:3]) or "none",
                "fix_now": "优化证据、结构和转化动作",
            }
        )
    return {
        "verdict": "fallback_review",
        "platform_reviews": reviews,
        "monetization_risks": [],
        "next_actions": ["继续优化未过线平台", "补封面素材", "发布前再做一次人工抽查"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--platforms", nargs="+", default=["知乎", "小红书", "抖音", "B站"])
    ap.add_argument("--min-score", type=float, default=85.0)
    ap.add_argument("--max-rewrite-rounds", type=int, default=3)
    ap.add_argument("--out", default="autotuned_drafts.json")
    args = ap.parse_args()

    strategy = extract_json(run_agent("main-brain", build_strategy_prompt(args.topic, args.platforms), timeout=220))
    raw = run_agent("content", build_init_prompt(args.topic, args.platforms, strategy), timeout=360)
    drafts = select_best_drafts(normalize_list(extract_json(raw)), args.platforms, args.min_score)

    final_drafts: List[Dict[str, Any]] = []
    score_log: List[Dict[str, Any]] = []
    for draft in drafts:
        final, score_row = optimize_draft(
            topic=args.topic,
            draft=draft,
            strategy=strategy,
            min_score=args.min_score,
            max_rewrite_rounds=args.max_rewrite_rounds,
        )
        final = sanitize_draft(args.topic, final)
        rescored = score_one(final, args.min_score)
        score_row = {
            "platform": final.get("platform", ""),
            "score": rescored.total_score,
            "pass": rescored.pass_gate,
            "issues": rescored.issues,
            "subscores": rescored.subscores,
            "rounds": score_row["rounds"],
        }
        final_drafts.append(final)
        score_log.append(score_row)

    try:
        publisher_review = extract_json(run_agent("publisher", build_publisher_review_prompt(args.topic, final_drafts), timeout=240))
    except Exception:
        publisher_review = fallback_review(final_drafts, args.min_score)

    assets = generate_asset_prompts(args.topic, final_drafts)

    payload = {
        "topic": args.topic,
        "strategy": strategy,
        "drafts": final_drafts,
        "scores": score_log,
        "publisher_review": publisher_review,
        "assets": assets,
    }

    out = Path(args.out)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "scores": score_log}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
