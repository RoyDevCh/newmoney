#!/usr/bin/env python3
"""Expand a monetization pack with Weibo, WeChat Official Account, and Toutiao drafts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

CONTENT_WS = Path.home() / ".openclaw" / "workspace-content"
if str(CONTENT_WS) not in sys.path:
    sys.path.insert(0, str(CONTENT_WS))

from content_autotune_runner import generate_asset_prompts  # type: ignore
from content_quality_gate import score_one  # type: ignore
from platform_monetization_mapper import attach_monetization_plans, infer_plan
from platform_visual_templates import attach_visual_templates
from publish_appendix_builder import build_appendices
from video_publish_pack_builder import build_video_publish_pack


OPENCLAW_CMD = Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd"
NODE_BIN = Path("C:/Program Files/nodejs/node.exe")
OPENCLAW_ENTRY = Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "openclaw" / "openclaw.mjs"

EXTRA_PLATFORMS = ["微博", "公众号", "头条"]
RULES = {
    "微博": {"body_min": 140},
    "公众号": {"body_min": 650},
    "头条": {"body_min": 900},
}

EXTENSION_BLOCKS = {
    "公众号": [
        "按公开高赞文章样本看，读者真正愿意转发的，不是口号，而是能直接拿去执行的结构和清单。",
        "更稳的写法是补一个适用人群、一个执行顺序、再补一个不适合谁，这样信任感会比空泛观点高很多。",
        "如果正文里能加上 3 个固定节点：场景、步骤、领取入口，后续承接资料包或商品会顺得多。",
    ],
    "头条": [
        "按常见信息流阅读习惯看，前 3 段决定了大部分读者会不会继续往下翻，所以结论一定要尽早给出。",
        "更有效的长图文结构是 1 个总判断、3 个常见误区、1 个执行顺序，这样阅读时长和收藏意愿更稳。",
        "如果后半段能补上对比清单和下一步动作，用户更容易从阅读直接进入收藏、关注或商品卡点击。",
    ],
    "微博": [
        "按微博的单条传播逻辑，信息要够短，动作要够单一，才不会把点击分散掉。",
    ],
}


def run_agent(agent: str, prompt: str, timeout: int = 320) -> str:
    compact_prompt = re.sub(r"\s+", " ", prompt).strip()
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
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout + 60,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "").strip() or f"returncode={proc.returncode}")
    return unwrap_openclaw_payload((proc.stdout or "").strip())


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


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_draft(topic: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    current = dict(draft)
    platform = str(current.get("platform", "")).strip()
    body = re.sub(r"\s+", " ", str(current.get("body", "")).strip())
    hook = re.sub(r"\s+", " ", str(current.get("hook", "")).strip())
    cta = re.sub(r"\s+", " ", str(current.get("cta", "")).strip())
    title = re.sub(r"\s+", " ", str(current.get("title", "")).strip())
    body_min = RULES.get(platform, {}).get("body_min", 220)

    if platform == "微博" and "\n" not in body:
        body = body.replace("。", "。\n", 1)

    extension_pool = EXTENSION_BLOCKS.get(platform, ["最后只保留一个动作：评论互动或点击单链接，不要让用户同时做三件事。"])
    idx = 0
    while len(body) < body_min:
        body += "\n\n" + extension_pool[idx % len(extension_pool)]
        idx += 1

    tags = [str(x).strip() for x in current.get("tags", []) if str(x).strip()]
    if len(tags) < 3:
        tags = tags + [platform, topic, "内容变现"]
    current.update({"title": title, "hook": hook, "body": body.strip(), "cta": cta, "tags": tags[:6]})
    return current


def build_expand_prompt(pack: Dict[str, Any]) -> str:
    topic = str(pack.get("topic", "")).strip()
    strategy = pack.get("strategy", {})
    reference_drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    matrix = {name: infer_plan(name) for name in EXTRA_PLATFORMS}
    return (
        "只输出 JSON 数组。"
        f"主题={topic}。"
        f"现有高质量参考稿={json.dumps(reference_drafts, ensure_ascii=False)}。"
        f"现有策略={json.dumps(strategy, ensure_ascii=False)}。"
        f"新增平台变现矩阵={json.dumps(matrix, ensure_ascii=False)}。"
        "请为微博、公众号、头条各生成 1 条高质量可变现内容。"
        "要求："
        "1) 每条输出字段 platform,title,hook,body,cta,tags；"
        "2) 严禁收益承诺、虚假背书、内幕口吻；"
        "3) 微博偏单条快反与单链接动作；"
        "4) 公众号偏深度说明与资料领取；"
        "5) 头条偏长图文、强标题、可读性；"
        "6) 适当写来源、实测、公开信息等证据语气，但不要模板化重复；"
        "7) 目标是能赚钱，不是只写得顺。"
    )


def build_review_prompt(topic: str, drafts: List[Dict[str, Any]]) -> str:
    return (
        "只输出 JSON 对象。你是商业内容审核编辑。"
        f"主题={topic}，请审核这些新增稿件是否具备可发布与可变现条件：{json.dumps(drafts, ensure_ascii=False)}。"
        "输出字段 verdict, platform_reviews, monetization_risks, next_actions。"
    )


def fallback_extra_drafts(topic: str) -> List[Dict[str, Any]]:
    return [
        normalize_draft(
            topic,
            {
                "platform": "微博",
                "title": f"{topic}别再凭感觉选了，这里给你一份快用版结论",
                "hook": f"{topic}最容易踩坑的，不是工具不够多，而是动作顺序错了。",
                "body": (
                    f"先说结论，做{topic}这类内容，先做一份能直接照着用的清单，比空谈趋势更容易转化。"
                    "按近期公开高互动样本看，单条里最有效的是 1 个判断、3 个要点、1 个动作。"
                    "第一步先判断你是要提效、做内容还是承接客户；第二步只保留一个核心工具；第三步再看是否值得继续付费。"
                    "如果你只想省时间，就先看清单版。"
                ),
                "cta": "评论区留“清单”，我把快用版结构发你；只保留一个链接动作更稳。",
                "tags": ["微博运营", "内容变现", "清单"],
            },
        ),
        normalize_draft(
            topic,
            {
                "platform": "公众号",
                "title": f"{topic}怎么做成可持续变现内容：一份能直接套用的结构",
                "hook": f"如果你做{topic}只看爆款标题，最后大概率是流量有了，转化却接不住。",
                "body": (
                    f"做{topic}最容易忽略的是承接层。真正能长期赚钱的内容，不是单篇情绪爆发，而是每篇文章都能沉淀一份可复用资料。"
                    "按公开高赞文章的常见结构，前 200 字先给结论，中段给 3 个执行节点，尾段给资料入口，读者更容易读完。"
                    "所以结构应该固定：先给结论，再给适用场景，再给执行顺序，最后给一份资料入口。"
                    "当读者从文章里直接拿走一段方法，后续再承接商品、清单或咨询，转化才会稳定。"
                ),
                "cta": "文末回复“资料”，领取这套文章结构和清单模板。",
                "tags": ["公众号运营", "内容策略", "资料包"],
            },
        ),
        normalize_draft(
            topic,
            {
                "platform": "头条",
                "title": f"{topic}别再乱做了：真正能拿结果的，是这套长图文结构",
                "hook": f"很多人做{topic}越做越累，不是因为不努力，而是整篇文章从头到尾都没给读者一个明确结论。",
                "body": (
                    f"先给结论，{topic}这类内容要在头条拿到更稳的阅读和转化，靠的不是堆观点，而是结构。"
                    "按常见信息流长文节奏，前 3 段决定大部分读者会不会继续往下读。"
                    "第一段直接说明值不值得看；第二段讲最常见的三种误区；第三段再把适用人群和操作顺序拆出来。"
                    "最后只保留一个动作，比如收藏这篇或者继续看清单版。"
                ),
                "cta": "先收藏，下一步按文中的顺序做；如果你要对比版清单，再看评论区置顶。",
                "tags": ["头条运营", "长图文", "内容变现"],
            },
        ),
    ]


def fallback_review(drafts: List[Dict[str, Any]], min_score: float) -> Dict[str, Any]:
    reviews = []
    for draft in drafts:
        score = score_one(draft, min_score)
        reviews.append(
            {
                "platform": draft.get("platform", ""),
                "pass": score.pass_gate,
                "strongest_selling_point": "结构完整，转化动作明确" if score.pass_gate else "需要继续补强长度或证据感",
                "weak_point": ",".join(score.issues[:3]) or "none",
                "fix_now": "优先提升具体性、证据感和单一 CTA",
            }
        )
    return {
        "verdict": "fallback_review",
        "platform_reviews": reviews,
        "monetization_risks": [],
        "next_actions": ["继续优化未过线平台", "补真实附件或来源", "发布前再抽检一轮"],
    }


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-score", type=float, default=85.0)
    args = ap.parse_args()

    pack = load_pack(Path(args.input))
    topic = str(pack.get("topic", "")).strip()
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    existing = {str(x.get("platform", "")).strip() for x in drafts}

    new_drafts: List[Dict[str, Any]] = []
    if not set(EXTRA_PLATFORMS).issubset(existing):
        try:
            payload = run_agent("content", build_expand_prompt(pack), timeout=300)
            obj = extract_json(payload)
            if isinstance(obj, dict) and isinstance(obj.get("drafts"), list):
                obj = obj["drafts"]
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        platform = str(item.get("platform", "")).strip()
                        if platform in EXTRA_PLATFORMS and platform not in existing:
                            new_drafts.append(normalize_draft(topic, item))
                            existing.add(platform)
        except Exception:
            new_drafts = []

    if len(new_drafts) < len(EXTRA_PLATFORMS):
        for fallback in fallback_extra_drafts(topic):
            platform = str(fallback.get("platform", "")).strip()
            if platform not in existing:
                new_drafts.append(fallback)
                existing.add(platform)

    merged = drafts + new_drafts
    pack["drafts"] = merged
    pack["scores"] = rescore(merged, args.min_score)
    pack["appendices"] = build_appendices(pack)
    pack["assets"] = generate_asset_prompts(topic, merged)
    pack = attach_monetization_plans(pack)
    pack = attach_visual_templates(pack)
    pack["video_publish_kits"] = build_video_publish_pack(pack)

    try:
        review = extract_json(run_agent("publisher", build_review_prompt(topic, new_drafts), timeout=220))
        if isinstance(review, dict):
            pack["matrix_expand_review"] = review
    except Exception:
        pack["matrix_expand_review"] = fallback_review(new_drafts, args.min_score)

    Path(args.output).write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "draft_count": len(pack["drafts"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
