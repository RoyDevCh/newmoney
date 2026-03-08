#!/usr/bin/env python3
"""Content quality gate for multi-platform drafts.

Usage:
  py -3 content_quality_gate.py --input drafts.json --output report.json --min-score 78
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List


RISK_TERMS = {
    "100%",
    "绝对",
    "包赚",
    "内幕",
    "未证实",
    "听说",
    "爆料",
    "月入",
    "月赚",
    "收入翻倍",
    "躺赚",
    "被动收入",
}

PLATFORM_RULES = {
    "知乎": {"body_min": 450, "body_max": 1800, "emoji_max": 5},
    "小红书": {"body_min": 120, "body_max": 550, "emoji_max": 35},
    "抖音": {"body_min": 120, "body_max": 520, "emoji_max": 12},
    "B站": {"body_min": 280, "body_max": 1400, "emoji_max": 10},
    "bilibili": {"body_min": 280, "body_max": 1400, "emoji_max": 10},
    "微博": {"body_min": 120, "body_max": 420, "emoji_max": 12},
    "公众号": {"body_min": 550, "body_max": 2600, "emoji_max": 6},
    "头条": {"body_min": 800, "body_max": 2600, "emoji_max": 8},
}

MONETIZATION_BLOCKERS = {
    "missing_title",
    "missing_hook",
    "missing_body",
    "missing_cta",
    "body_maybe_truncated",
    "no_source_or_test_context",
    "body_too_short_for_platform",
    "cta_weak",
    "tags_insufficient",
    "earnings_claim",
    "unverified_social_proof",
}


@dataclass
class DraftScore:
    platform: str
    title: str
    total_score: float
    pass_gate: bool
    subscores: Dict[str, float]
    issues: List[str]
    rewrite_prompt: str


def monetization_ready(total_score: float, issues: List[str], min_score: float) -> bool:
    if total_score < min_score:
        return False
    return not any(issue in MONETIZATION_BLOCKERS for issue in issues)


def _is_emoji(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x1F300 <= cp <= 0x1F5FF
        or 0x1F600 <= cp <= 0x1F64F
        or 0x1F680 <= cp <= 0x1F6FF
        or 0x1F700 <= cp <= 0x1F77F
        or 0x1F780 <= cp <= 0x1F7FF
        or 0x1F800 <= cp <= 0x1F8FF
        or 0x1F900 <= cp <= 0x1F9FF
        or 0x1FA70 <= cp <= 0x1FAFF
        or 0x2600 <= cp <= 0x26FF
        or 0x2700 <= cp <= 0x27BF
    )


def _count_emoji(s: str) -> int:
    return sum(1 for ch in s if _is_emoji(ch))


def _contains_risk(s: str) -> List[str]:
    lowered = s.lower()
    hits = []
    for t in RISK_TERMS:
        if t.lower() in lowered:
            hits.append(t)
    return hits


def _sentence_count(text: str) -> int:
    return len([x for x in re.split(r"[。！？!?\n]", text) if x.strip()])


def _has_source_signal(text: str) -> bool:
    keys = ["来源", "实测", "测试环境", "官方", "链接", "benchmark", "review"]
    return any(k in text for k in keys)


def _has_earnings_claim(text: str) -> bool:
    patterns = [
        r"月入\s*\d",
        r"月赚\s*\d",
        r"日入\s*\d",
        r"收入翻倍",
        r"多赚\s*\d",
        r"\d+\s*[万千百]?\+?\s*元",
    ]
    return any(re.search(p, text) for p in patterns)


def _has_unverified_social_proof(text: str) -> bool:
    patterns = [
        r"服务\s*\d+\+?\s*家企业",
        r"累计学员\s*\d+\+?",
        r"\d+\+?\s*企业客户",
        r"\d+\+?\s*学员",
    ]
    return any(re.search(p, text) for p in patterns)


def _incomplete_tail(text: str) -> bool:
    tail = text.strip()[-4:]
    bad = ["更新，就", "总结：", "然后", "以及", "...", "……"]
    return any(x in tail for x in bad)


def _platform_rule(name: str) -> Dict[str, int]:
    return PLATFORM_RULES.get(name, {"body_min": 150, "body_max": 1200, "emoji_max": 12})


def score_one(item: Dict, min_score: float) -> DraftScore:
    platform = str(item.get("platform", "")).strip()
    title = str(item.get("title", "")).strip()
    hook = str(item.get("hook", "")).strip()
    body = str(item.get("body", "")).strip()
    cta = str(item.get("cta", "")).strip()
    tags = item.get("tags", [])

    issues: List[str] = []
    subs: Dict[str, float] = {}

    # 1) Completeness 20
    completeness = 20.0
    for field_name, value in [("title", title), ("hook", hook), ("body", body), ("cta", cta)]:
        if not value:
            completeness -= 5
            issues.append(f"missing_{field_name}")
    if _incomplete_tail(body):
        completeness -= 4
        issues.append("body_maybe_truncated")
    subs["completeness"] = max(completeness, 0.0)

    # 2) Hook strength 15
    hook_score = 15.0
    if len(hook) < 18:
        hook_score -= 6
        issues.append("hook_too_short")
    if len(hook) > 90:
        hook_score -= 3
        issues.append("hook_too_long")
    if not re.search(r"[0-9一二三四五六七八九十]", hook):
        hook_score -= 2
    if "？" not in hook and "!" not in hook and "！" not in hook:
        hook_score -= 2
    subs["hook"] = max(hook_score, 0.0)

    # 3) Specificity & credibility 20
    spec = 20.0
    nums = len(re.findall(r"\d+", body))
    if nums < 2:
        spec -= 6
        issues.append("low_specificity_numbers")
    if not _has_source_signal(body):
        spec -= 5
        issues.append("no_source_or_test_context")
    risk_hits = _contains_risk(title + "\n" + hook + "\n" + body)
    if risk_hits:
        spec -= min(8, len(risk_hits) * 2)
        issues.append("risky_terms:" + ",".join(risk_hits[:4]))
    if _has_earnings_claim(title + "\n" + hook + "\n" + body):
        spec -= 6
        issues.append("earnings_claim")
    if _has_unverified_social_proof(body):
        spec -= 4
        issues.append("unverified_social_proof")
    subs["specificity"] = max(spec, 0.0)

    # 4) Platform fit 20
    rule = _platform_rule(platform)
    pf = 20.0
    blen = len(body)
    if blen < rule["body_min"]:
        pf -= 8
        issues.append("body_too_short_for_platform")
    if blen > rule["body_max"]:
        pf -= 5
        issues.append("body_too_long_for_platform")
    ecount = _count_emoji(title + body)
    if ecount > rule["emoji_max"]:
        pf -= 3
        issues.append("too_many_emoji")
    if platform in {"抖音"} and _sentence_count(body) < 5:
        pf -= 4
        issues.append("douyin_rhythm_weak")
    subs["platform_fit"] = max(pf, 0.0)

    # 5) Conversion 15
    conv = 15.0
    if len(cta) < 8:
        conv -= 5
        issues.append("cta_weak")
    if not tags or len(tags) < 3:
        conv -= 3
        issues.append("tags_insufficient")
    if platform == "知乎" and ("评论" not in cta and "收藏" not in cta):
        conv -= 2
    if platform == "小红书" and ("收藏" not in cta and "关注" not in cta):
        conv -= 2
    if platform == "抖音" and ("主页" not in cta and "关注" not in cta):
        conv -= 2
    if platform == "微博" and ("评论" not in cta and "链接" not in cta):
        conv -= 2
    if platform == "公众号" and ("资料" not in cta and "领取" not in cta and "查看" not in cta):
        conv -= 2
    if platform == "头条" and ("收藏" not in cta and "关注" not in cta and "查看" not in cta):
        conv -= 2
    subs["conversion"] = max(conv, 0.0)

    # 6) Readability 10
    read = 10.0
    avg_sent_len = len(body) / max(_sentence_count(body), 1)
    if avg_sent_len > 42:
        read -= 4
        issues.append("sentences_too_long")
    if "\n" not in body:
        read -= 2
        issues.append("no_paragraph_breaks")
    subs["readability"] = max(read, 0.0)

    total = round(sum(subs.values()), 2)
    passed = monetization_ready(total, issues, min_score)

    rewrite_prompt = (
        f"你是一名资深{platform}商业内容主编。请重写下面稿件并修复这些问题：{';'.join(issues) if issues else '无'}。"
        "要求：1) 保留核心主题但去除不确定事实，所有具体数字必须标注来源或改为区间表达；"
        "2) 开头3秒/前50字必须有冲突或反常识；3) 每段一句核心结论，信息密度高；"
        "4) 结尾CTA明确且与平台行为一致；5) 输出JSON字段platform,title,hook,body,cta,tags。"
    )

    return DraftScore(
        platform=platform,
        title=title,
        total_score=total,
        pass_gate=passed,
        subscores=subs,
        issues=issues,
        rewrite_prompt=rewrite_prompt,
    )


def parse_drafts(path: Path) -> List[Dict]:
    raw = path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if isinstance(data, dict):
        if "drafts" in data and isinstance(data["drafts"], list):
            return data["drafts"]
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("Unsupported JSON format")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-score", type=float, default=78.0)
    args = ap.parse_args()

    drafts = parse_drafts(Path(args.input))
    results = [score_one(d, args.min_score) for d in drafts]

    avg = round(sum(r.total_score for r in results) / max(len(results), 1), 2)
    pass_count = sum(1 for r in results if r.pass_gate)

    payload = {
        "summary": {
            "count": len(results),
            "avg_score": avg,
            "pass_count": pass_count,
            "pass_rate": round(pass_count / max(len(results), 1), 4),
            "min_score": args.min_score,
        },
        "results": [asdict(r) for r in results],
    }

    out = Path(args.output)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


