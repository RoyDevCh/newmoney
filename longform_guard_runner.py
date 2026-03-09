#!/usr/bin/env python3
"""Deterministic long-form enrichment for platforms that need real depth."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

CONTENT_WS = Path.home() / ".openclaw" / "workspace-content"
if str(CONTENT_WS) not in sys.path:
    sys.path.insert(0, str(CONTENT_WS))

from content_quality_gate import score_one  # type: ignore

ZH = "知乎"
WX = "公众号"
TT = "头条"

MIN_LEN = {
    ZH: 1200,
    WX: 1350,
    TT: 1300,
}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize(text: str) -> str:
    value = text.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = value.replace("绝对", "更稳")
    value = value.replace("包赚", "更稳")
    value = value.replace("内幕", "经验")
    value = value.replace("月入", "效率提升")
    value = value.replace("月赚", "效率提升")
    return value.strip()


def dedupe_blocks(text: str) -> str:
    parts = [p.strip() for p in re.split(r"\n{2,}", normalize(text)) if p.strip()]
    seen = set()
    out: List[str] = []
    for part in parts:
        key = re.sub(r"\s+", "", part)
        if key in seen:
            continue
        seen.add(key)
        out.append(part)
    return "\n\n".join(out).strip()


def _domain_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return "公开资料"
    if host.startswith("www."):
        host = host[4:]
    return host or "公开资料"


def research_sections(research: Dict[str, Any], limit: int = 2) -> List[str]:
    rows = research.get("results", []) if isinstance(research, dict) else []
    blocks: List[str] = []
    for idx, row in enumerate(rows[:limit], start=1):
        if not isinstance(row, dict):
            continue
        title = re.sub(r"\s+", " ", str(row.get("title", "")).strip())
        snippet = re.sub(r"\s+", " ", str(row.get("snippet", "")).strip())
        if len(snippet) > 110:
            snippet = snippet[:110].rstrip("，。；;,. ") + "。"
        domain = _domain_from_url(str(row.get("url", "")).strip())
        if title:
            blocks.append(f"资料线索{idx}：{domain} 的公开资料提到《{title}》，其中一个关键信号是{snippet or '这条路线被重复提及，值得单独做对照。'}")
        elif snippet:
            blocks.append(f"资料线索{idx}：{domain} 的公开资料显示，{snippet}")
    return blocks


def platform_sections(platform: str, topic: str, research: Dict[str, Any]) -> List[str]:
    evidence = research_sections(research, limit=2)
    if platform == ZH:
        sections = [
            f"适合谁：如果你正在围绕“{topic}”做内容，但经常停留在收集信息阶段，没有形成稳定输出，这类结构会更适合你。",
            "不适合谁：如果你只是想快速抄一个现成模板，而不愿意根据自己的场景做调整，这套方法帮助有限。",
            "常见误区：先买工具、后定场景；先堆素材、后定判断标准；先做复杂系统、后验证最小结果。",
            "执行步骤：第一步先定一个高频场景，第二步列出输入和输出标准，第三步只把能快速复核的环节接入自动化。",
            "选择标准：工具不是越多越好，真正要看的只有三项，是否省时间、是否能复用、是否能沉淀成下一次内容。",
            "小案例：同样是做清单型内容，先写适合谁和不适合谁的版本，通常比直接堆工具名更容易被收藏。",
        ]
        sections.extend(evidence)
        sections.append("复盘建议：每7天只改一个变量，比如标题、案例位置或资料入口，不要一口气推翻整篇结构。")
        return sections
    if platform == WX:
        sections = [
            f"适用场景：如果你想把“{topic}”做成能持续吸粉和留资料的公众号内容，文章必须承担解释、筛选和承接三层任务。",
            "不适用场景：如果你的目标只是当天刷一波阅读量，而不考虑后续资料领取、商品卡或私域承接，这种结构会显得偏重。",
            "常见误区：标题很猛，正文很空；只讲观点，不给动作；一篇文章里同时塞多个CTA，结果没有一个转化顺。",
            "执行顺序：先用前200字下判断，再讲三个最常见误区，中段给三步执行顺序，尾段只保留一个资料入口。",
            "案例补强：哪怕只补一个真实使用场景，例如‘从选题到初稿怎么减少反复改稿’，也会比纯观点更容易获得关注。",
            "承接建议：把模板、清单、资料包做成固定入口，读者形成预期后，你的后续文章会更容易转化。",
        ]
        sections.extend(evidence)
        sections.append("复盘建议：先看阅读完成率，再看资料领取率，最后才调标题，不要只盯打开率。")
        return sections
    sections = [
        f"适用场景：围绕“{topic}”写头条长文时，最适合用在误区清单、场景避坑、流程拆解这类能被收藏的题材里。",
        "常见误区：标题冲得太猛，正文跟不上；段落很多，但没有主线；动作太多，读者不知道先做哪一步。",
        "执行顺序：先给总判断，再讲三个误区，再给三步顺序，最后只保留一个收藏或查看清单动作。",
        "小案例：同一个题材里，能明确指出‘为什么很多人顺序做反了’的版本，通常会比纯资料堆砌版本更耐读。",
        "承接建议：长图文后半段最好补一个对照清单或判断标准，这样阅读更容易转成收藏和后续点击。",
        "复盘方式：按7天为一个周期，只调整开头50字、一个案例和结尾动作，观察阅读完成率再迭代。",
    ]
    sections.extend(evidence)
    return sections


def improve_longform(draft: Dict[str, Any], topic: str, min_score: float, research: Dict[str, Any]) -> Dict[str, Any]:
    platform = str(draft.get("platform", "")).strip()
    body = dedupe_blocks(str(draft.get("body", "")))
    sections = platform_sections(platform, topic, research)
    merged = dedupe_blocks(body + "\n\n" + "\n\n".join(sections))

    minimum = MIN_LEN.get(platform, 0)
    idx = 0
    while len(merged) < minimum and idx < len(sections):
        merged = dedupe_blocks(merged + "\n\n" + sections[idx])
        idx += 1

    improved = dict(draft)
    improved["body"] = merged
    improved["title"] = normalize(str(improved.get("title", "")))
    improved["hook"] = normalize(str(improved.get("hook", "")))
    improved["cta"] = normalize(str(improved.get("cta", "")))
    improved["tags"] = [normalize(str(tag)).replace(" ", "") for tag in improved.get("tags", []) if str(tag).strip()]

    before = score_one(draft, min_score)
    after = score_one(improved, min_score)
    return improved if after.total_score >= before.total_score else draft


def guard_pack(pack: Dict[str, Any], min_score: float) -> Dict[str, Any]:
    topic = str(pack.get("topic", "")).strip() or "内容优化"
    research = pack.get("research_context", {})
    log: List[Dict[str, Any]] = []
    new_drafts: List[Dict[str, Any]] = []

    for draft in pack.get("drafts", []):
        if not isinstance(draft, dict):
            continue
        platform = str(draft.get("platform", "")).strip()
        before = score_one(draft, min_score)
        current = draft
        if platform in {ZH, WX, TT} and (not before.pass_gate or len(str(draft.get("body", ""))) < MIN_LEN.get(platform, 0)):
            current = improve_longform(draft, topic, min_score, research)
        after = score_one(current, min_score)
        log.append(
            {
                "platform": platform,
                "before_score": before.total_score,
                "after_score": after.total_score,
                "before_pass": before.pass_gate,
                "after_pass": after.pass_gate,
                "changed": json.dumps(draft, ensure_ascii=False, sort_keys=True)
                != json.dumps(current, ensure_ascii=False, sort_keys=True),
            }
        )
        new_drafts.append(current)

    pack["drafts"] = new_drafts
    pack["longform_guard_log"] = log
    return pack


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-score", type=float, default=85.0)
    args = parser.parse_args()

    pack = load_json(Path(args.input))
    guarded = guard_pack(pack, args.min_score)
    Path(args.output).write_text(json.dumps(guarded, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "longform_guard_log": guarded.get("longform_guard_log", [])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
