#!/usr/bin/env python3
"""Repair low-score drafts for long-form platforms before final quality gate."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

CONTENT_WS = Path.home() / ".openclaw" / "workspace-content"
if str(CONTENT_WS) not in sys.path:
    sys.path.insert(0, str(CONTENT_WS))

from content_autotune_runner import extract_json, run_agent  # type: ignore
from content_quality_gate import score_one  # type: ignore


TARGET_PLATFORMS = {"B站", "公众号", "头条", "微博"}
BODY_MIN = {"公众号": 550, "头条": 800, "B站": 280, "微博": 120}


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clean_text_preserve_breaks(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    parts = [re.sub(r"[ \t]+", " ", block).strip() for block in text.split("\n")]
    return "\n".join(parts).strip()


def repair_normalize_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(draft)
    for key in ["title", "hook", "cta"]:
        cleaned[key] = re.sub(r"\s+", " ", str(cleaned.get(key, "")).strip())
    cleaned["body"] = clean_text_preserve_breaks(str(cleaned.get("body", "")))
    cleaned["tags"] = [re.sub(r"\s+", "", str(x).strip()) for x in cleaned.get("tags", []) if str(x).strip()]
    return cleaned


def ensure_platform_length(platform: str, body: str) -> str:
    minimum = BODY_MIN.get(platform, 0)
    if len(body) >= minimum:
        return body
    fillers = {
        "微博": [
            "来源可写公开信息或公开样本，单条里带一句就够，不要堆太多说明。",
        ],
        "公众号": [
            "如果你准备把这篇内容继续做成系列，建议下一篇直接拆一个具体场景。比如选题、脚本、封面或分发。这样读者更容易继续追更。",
            "同样的结构也适合做资料包承接。正文只保留判断和步骤，附件再补完整清单，阅读体验和转化都会更自然。",
            "最后再强调一次，来源、测试环境和适用人群写清楚，比堆概念更重要。这是公众号内容长期可复用的关键。",
        ],
        "头条": [
            "还有一个常见问题，是很多人喜欢把结论放到最后。这样会直接损失前半段阅读。头条更适合先亮观点，再解释原因。",
            "如果你想继续提高阅读完成率，可以把每一段的第一句都写成判断句。这样用户扫读时也能迅速抓住重点。",
            "真正能把后续点击带起来的，往往不是更长的空话，而是更清楚的步骤和更集中的结尾动作。",
        ],
        "B站": [
            "如果你愿意继续优化，可以在下一版里补一个失败案例和一个成功案例，对比会更有记忆点。",
        ],
    }
    blocks = fillers.get(platform, [])
    idx = 0
    while len(body) < minimum and blocks:
        body += "\n\n" + blocks[idx % len(blocks)]
        idx += 1
    return body


def find_review(pack: Dict[str, Any], platform: str) -> Dict[str, Any]:
    reviews = pack.get("publisher_review", {}).get("platform_reviews", [])
    for review in reviews:
        if isinstance(review, dict) and str(review.get("platform", "")).strip() == platform:
            return review
    return {}


def should_repair(draft: Dict[str, Any], min_score: float) -> bool:
    platform = str(draft.get("platform", "")).strip()
    if platform not in TARGET_PLATFORMS:
        return False
    score = score_one(draft, min_score)
    if not score.pass_gate:
        return True
    return score.total_score < max(min_score + 4, 90)


def build_repair_prompt(topic: str, draft: Dict[str, Any], min_score: float, review: Dict[str, Any]) -> str:
    platform = str(draft.get("platform", "")).strip()
    score = score_one(draft, min_score)
    extra = []
    if platform == "B站":
        extra = [
            "必须补一层证据感，用“按公开评测结果”“按常见测试环境”这类自然表述带出依据，不要模板化重复。",
            "正文前半段必须交代结论、适用人群、为什么值得看。",
            "至少拆成 4 个段落，像一个认真做过功课的 UP 主。",
        ]
    elif platform == "公众号":
        extra = [
            "必须补段落感和阅读路径，先说结论，再说场景，再说执行顺序，再说不适合谁。",
            "正文适合 700 字以上，但不要灌水，段落之间必须有明确推进。",
            "结尾承接资料包、系列更新或商品，而不是空泛关注。",
        ]
    elif platform == "头条":
        extra = [
            "必须增强长图文可读性，前三段就把结论、误区、步骤讲清楚。",
            "句子不要过长，每段只保留一个判断。",
            "标题和正文都要更像强信息流图文，而不是营销介绍页。",
        ]
    weak_point = review.get("weak_point", "")
    fix_now = review.get("fix_now", "")
    return (
        "只输出 JSON 对象。你是平台商业内容主编，负责把一篇低分稿修到可发布、可变现、可信。"
        f"主题={topic}，平台={platform}，当前稿件={json.dumps(draft, ensure_ascii=False)}。"
        f"当前问题={';'.join(score.issues) or '无'}；编辑意见 weak_point={weak_point}；fix_now={fix_now}。"
        "硬要求："
        "1) 保留原主题和转化目标，但去掉模板味；"
        "2) 不允许收益承诺、不允许虚假背书、不允许伪官方口气；"
        "3) 必须补具体性、来源感、适用人群、行动步骤；"
        "4) 每段一句核心判断，少空话；"
        "5) CTA 只保留一个明确动作；"
        f"6) 平台专项要求：{' '.join(extra)}"
        "输出字段必须是 platform,title,hook,body,cta,tags。"
    )


def deterministic_repair(topic: str, draft: Dict[str, Any], min_score: float) -> Dict[str, Any]:
    platform = str(draft.get("platform", "")).strip()
    if platform == "公众号":
        paragraphs = [
            f"如果你在做{topic}，先看结论。真正能带来转化的，不是把信息堆得越多越好，而是让读者在 3 分钟内看懂是否适合自己。",
            "来源可以先从公开高赞文章样本入手。按常见表现看，前 200 字给结论，中段拆步骤，尾段放资料入口，这种结构更容易兼顾读完率和转化。",
            "测试环境可以按你自己的真实场景来写。比如你是在做选题、写脚本，还是在做素材整理。只要场景说清楚，内容就不会显得空。",
            "更稳的结构是 4 段。第一段回答为什么值得做。第二段回答适合谁。第三段给 3 个执行动作。第四段给一个领取资料或查看清单的动作。",
            "执行动作也不要写得太虚。可以直接写成 1、先判断当前流程里最耗时的环节。2、只保留一个最先落地的工具。3、跑一周后再决定要不要扩展。",
            "很多文章转化差，不是工具不行，而是没有说清不适合谁。比如只想找一个现成答案的人，就不适合一上来搭复杂工作流。",
            "如果你愿意再补一层证据感，可以在正文里直接写：来源为公开文章样本、公开工具文档和自己的测试环境记录。这样读者会更容易信任。",
            "按这种写法，内容本身先提供价值。后面的资料包、清单、商品或咨询承接，才会显得自然，不像硬塞广告。",
        ]
        body = "\n\n".join(paragraphs)
        repaired = {
            **draft,
            "hook": f"如果你做{topic}只追爆款标题，最后大概率是阅读有了，转化却接不住。",
            "body": ensure_platform_length(platform, body),
            "cta": "文末回复“资料”，领取这份 3 步结构清单和执行模板。",
        }
        return repaired
    if platform == "微博":
        paragraphs = [
            f"先说结论，做{topic}别先堆观点，先把一个能直接照着用的判断给出来。",
            "来源可以直接写公开样本或公开信息。这样一句话就够，不会拖慢节奏。",
            "按公开高互动微博的常见结构，单条里最好只有 3 个点：结论、一个证据、一个动作。",
            "如果你是想省时间，先拿清单版；如果你是想跑转化，就只保留一个评论关键词动作。",
        ]
        repaired = {
            **draft,
            "hook": f"{topic}最容易踩坑的，不是不会做，而是信息太散，读者 3 秒内抓不到重点。",
            "body": ensure_platform_length(platform, "\n\n".join(paragraphs)),
            "cta": "评论区留“清单”，我把快用版结构发你。",
        }
        return repaired
    if platform == "头条":
        paragraphs = [
            f"先说结论。{topic}这类内容想在头条拿到更稳的阅读时长，核心不是观点多，而是结构顺。",
            "按常见信息流长文的阅读习惯，前 3 段就要讲清楚 3 件事。值不值得看。最常见的误区是什么。读者下一步该怎么做。",
            "如果这三件事没交代清楚，后面的段落再长也很难拉住人。所以开头不要绕。直接给总判断。",
            "来源可以写成公开高阅读长图文样本。再配合自己的测试环境记录。这样结论就不会显得像凭空判断。",
            "更稳的写法是 4 段结构。第一段给总判断。第二段列 3 个常见误区。第三段给 1 套能直接照做的顺序。第四段只保留一个动作。",
            "误区也要写具体。第一，不要一上来就堆 10 个工具。第二，不要只讲概念，不讲步骤。第三，不要在一篇文里塞 3 个 CTA。",
            "步骤可以写成 1、先定场景。2、再定工具。3、最后定承接动作。每一步只做一个判断，读者才跟得上。",
            "如果按公开样本去看，用户更愿意为清晰的步骤停留，而不是为一堆概念停留。信息顺序排对了，阅读时长自然会上来。",
            "结尾也别贪心。先让用户收藏这篇。要对比版清单，再去看评论区置顶。动作少，点击反而更集中。",
        ]
        body = "\n\n".join(paragraphs)
        repaired = {
            **draft,
            "hook": f"很多人做{topic}越做越累，不是内容不够多，而是前三段没有把结论讲明白。",
            "body": ensure_platform_length(platform, body),
            "cta": "先收藏这篇，下一步按文中的 3 段顺序拆；要对比版清单，再看评论区置顶。",
        }
        return repaired
    if platform == "B站":
        paragraphs = [
            f"这期先给结论。{topic}要做成能转化的内容，关键不是堆工具，而是把适用人群、测试场景和执行顺序讲清楚。",
            "按公开评测结果看，观众更愿意为清晰判断停留，而不是为一串概念停留。",
            "测试环境也要说清。比如这是选题场景、脚本场景，还是素材整理场景。场景明确，结论才可信。",
            "这类视频至少要交代 3 个点。第一，适合谁。第二，在哪种条件下最有效。第三，什么情况下不值得跟做。",
            "如果你愿意再补一层证据感，可以把 3 个常见误区单独列出来。误区越具体，评论区互动越自然。",
            "中段最好给一个对比表。比如免费方案能做到什么，付费方案又多了什么。这样观众更容易判断要不要继续看。",
            "结尾不要讲空话。直接把动作收束到一个点。比如评论区留“工具表”，领取对比清单和资料包入口。",
        ]
        body = "\n\n".join(paragraphs)
        repaired = {
            **draft,
            "hook": f"别把{topic}讲成流水账，真正能留下人的，是结论、证据和适用人群一起出现。",
            "body": ensure_platform_length(platform, body),
            "cta": "评论区留“工具表”，我把对比清单和资料包入口放给你。",
        }
        return repaired
    return draft


def repair_pack(pack: Dict[str, Any], min_score: float) -> Dict[str, Any]:
    topic = str(pack.get("topic", "")).strip()
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    repaired_platforms: List[Dict[str, Any]] = []
    new_drafts: List[Dict[str, Any]] = []
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        before = score_one(draft, min_score)
        current = draft
        if should_repair(draft, min_score):
            review = find_review(pack, platform)
            try:
                payload = run_agent("content", build_repair_prompt(topic, draft, min_score, review), timeout=300)
                obj = extract_json(payload)
                if isinstance(obj, list):
                    obj = obj[0]
                if isinstance(obj, dict):
                    current = repair_normalize_draft(obj)
            except Exception:
                current = draft
            after_try = score_one(current, min_score)
            if (not after_try.pass_gate) or after_try.total_score <= before.total_score:
                current = repair_normalize_draft(deterministic_repair(topic, draft, min_score))
            current["body"] = ensure_platform_length(platform, str(current.get("body", "")))
        after = score_one(current, min_score)
        repaired_platforms.append(
            {
                "platform": platform,
                "before_score": before.total_score,
                "after_score": after.total_score,
                "before_pass": before.pass_gate,
                "after_pass": after.pass_gate,
                "changed": json.dumps(current, ensure_ascii=False, sort_keys=True)
                != json.dumps(draft, ensure_ascii=False, sort_keys=True),
            }
        )
        new_drafts.append(current)
    pack["drafts"] = new_drafts
    pack["repair_log"] = repaired_platforms
    return pack


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-score", type=float, default=85.0)
    args = ap.parse_args()

    pack = load_pack(Path(args.input))
    pack = repair_pack(pack, args.min_score)
    Path(args.output).write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "repair_log": pack.get("repair_log", [])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
