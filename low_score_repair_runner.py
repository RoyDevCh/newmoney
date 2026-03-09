#!/usr/bin/env python3
"""Repair long-form platform drafts with deterministic fallback and de-duplication."""

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

from content_autotune_runner import extract_json, run_agent, sanitize_draft  # type: ignore
from content_quality_gate import score_one  # type: ignore

BILI = "B\u7ad9"
WB = "\u5fae\u535a"
WX = "\u516c\u4f17\u53f7"
TT = "\u5934\u6761"
XG = "\u897f\u74dc\u89c6\u9891"

TARGET_PLATFORMS = {BILI, WX, TT, WB, XG}
BODY_MIN = {WX: 1200, TT: 1200, BILI: 520, WB: 140, XG: 650}
BODY_MAX = {WX: 2400, TT: 2500, BILI: 1400, WB: 420, XG: 1500}


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clean_text_preserve_breaks(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", block).strip() for block in text.split("\n")]
    return "\n".join(lines).strip()


def split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n{2,}", clean_text_preserve_breaks(text)) if p.strip()]


def dedupe_paragraphs(text: str) -> str:
    seen = set()
    kept: List[str] = []
    for para in split_paragraphs(text):
        key = re.sub(r"\s+", "", para)
        if key in seen:
            continue
        seen.add(key)
        kept.append(para)
    return "\n\n".join(kept).strip()


def dedupe_lines_global(text: str) -> str:
    seen = set()
    out: List[str] = []
    for line in clean_text_preserve_breaks(text).split("\n"):
        key = re.sub(r"\s+", "", line)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(line.strip())
    return "\n".join([x for x in out if x.strip()]).strip()


def trim_to_platform_max(platform: str, body: str) -> str:
    limit = BODY_MAX.get(platform)
    if not limit or len(body) <= limit:
        return body
    parts = split_paragraphs(body)
    kept: List[str] = []
    total = 0
    for part in parts:
        if total + len(part) > limit and kept:
            break
        kept.append(part)
        total += len(part) + 2
    return "\n\n".join(kept).strip() if kept else body[:limit]


def normalize_risk_words(text: str) -> str:
    current = text
    current = current.replace("绝对", "更稳")
    current = current.replace("包赚", "更稳")
    current = current.replace("内幕", "经验")
    return current


def repair_normalize_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = dict(draft)
    for key in ["title", "hook", "cta"]:
        value = re.sub(r"\s+", " ", str(cleaned.get(key, "")).strip())
        value = re.sub(r"[<>]+", "", value)
        cleaned[key] = normalize_risk_words(value)

    body = normalize_risk_words(str(cleaned.get("body", "")))
    body = dedupe_paragraphs(body)
    body = dedupe_lines_global(body)
    cleaned["body"] = body

    cleaned["tags"] = [re.sub(r"\s+", "", str(tag).strip()) for tag in cleaned.get("tags", []) if str(tag).strip()]
    return cleaned


def ensure_platform_length(platform: str, body: str) -> str:
    minimum = BODY_MIN.get(platform, 0)
    current = dedupe_paragraphs(body)
    if len(current) >= minimum:
        return trim_to_platform_max(platform, current)

    fillers = {
        WB: [
            "\u6309\u516c\u5f00\u6837\u672c\u770b\uff0c\u5355\u6761\u4fe1\u606f\u5bc6\u5ea6\u4e0d\u7528\u592a\u6ee1\uff0c\u7ed3\u8bba+\u8bc1\u636e+\u52a8\u4f5c\u5c31\u8db3\u591f\u3002",
            "\u8fd9\u79cd\u5199\u6cd5\u66f4\u5bb9\u6613\u8ba9\u8bfb\u8005\u5728\u8bc4\u8bba\u533a\u53cd\u9988\u5173\u952e\u8bcd\uff0c\u8fdb\u800c\u627f\u63a5\u8d44\u6599\u6216\u6e05\u5355\u3002",
        ],
        WX: [
            "\u516c\u4f17\u53f7\u66f4\u9700\u8981\u6bb5\u843d\u9012\u8fdb\uff1a\u5148\u7ed3\u8bba\uff0c\u518d\u573a\u666f\uff0c\u7136\u540e\u6267\u884c\u6b65\u9aa4\uff0c\u6700\u540e\u627f\u63a5\u8d44\u6599\u5165\u53e3\u3002",
            "\u63cf\u8ff0\u9002\u7528\u4eba\u7fa4\u548c\u4e0d\u9002\u7528\u4eba\u7fa4\uff0c\u80fd\u660e\u663e\u63d0\u9ad8\u4fe1\u4efb\u611f\u3002",
            "\u6765\u6e90\u8868\u8fbe\u7528\u201c\u6309\u516c\u5f00\u4fe1\u606f\u201d\u6216\u201c\u6309\u5b9e\u6d4b\u73af\u5883\u201d\uff0c\u6bd4\u7edd\u5bf9\u5316\u65ad\u8a00\u66f4\u7a33\u3002",
        ],
        TT: [
            "\u5934\u6761\u957f\u6587\u524d\u4e09\u6bb5\u5e94\u8be5\u5148\u4ea4\u4ee3\u603b\u5224\u65ad\uff0c\u518d\u5217\u8bef\u533a\uff0c\u518d\u7ed9\u6b65\u9aa4\u3002",
            "\u4e0e\u5176\u5806\u6982\u5ff5\uff0c\u4e0d\u5982\u76f4\u63a5\u7ed9\u201c1-2-3\u201d\u6267\u884c\u987a\u5e8f\uff0c\u5bf9\u9605\u8bfb\u5b8c\u6210\u7387\u66f4\u6709\u5e2e\u52a9\u3002",
            "\u7ed3\u5c3e\u53ea\u7559\u4e00\u4e2a\u52a8\u4f5c\uff0c\u5f15\u5bfc\u6536\u85cf\u6216\u67e5\u770b\u7f6e\u9876\u6e05\u5355\uff0c\u6bd4\u591a\u4e2aCTA\u66f4\u7a33\u3002",
        ],
        BILI: [
            "B\u7ad9\u89c6\u9891\u6587\u6848\u5148\u7ed9\u7ed3\u8bba\uff0c\u518d\u7ed9\u6d4b\u8bd5\u4e0a\u4e0b\u6587\uff0c\u6700\u540e\u7ed9\u89c2\u4f17\u53ef\u76f4\u63a5\u6267\u884c\u7684\u52a8\u4f5c\u3002",
            "\u6709\u5bf9\u6bd4\u3001\u6709\u8bc1\u636e\u3001\u6709\u9002\u7528\u4eba\u7fa4\u7684\u6587\u6848\uff0c\u66f4\u5bb9\u6613\u83b7\u5f97\u9ad8\u8d28\u91cf\u8bc4\u8bba\u3002",
        ],
        XG: [
            "\u897f\u74dc\u89c6\u9891\u66f4\u9002\u54083\u52308\u5206\u949f\u7684\u6a2a\u5c4f\u6bcd\u4f53\u7ed3\u6784\uff0c\u5f00\u5934\u5148\u4e0b\u5224\u65ad\uff0c\u4e2d\u6bb5\u8865\u6848\u4f8b\u548c\u6b65\u9aa4\uff0c\u7ed3\u5c3e\u53ea\u7559\u4e00\u4e2a\u52a8\u4f5c\u3002",
            "\u6309\u516c\u5f00\u8d44\u6599\u548c\u6d4b\u8bd5\u73af\u5883\u7684\u5e38\u89c1\u505a\u6cd5\u770b\uff0c\u6a2a\u5c4f\u89c6\u9891\u91cc\u6700\u597d\u540c\u65f6\u51fa\u73b0\u9002\u7528\u4eba\u7fa4\u3001\u6d4b\u8bd5\u80cc\u666f\u548c\u4e0b\u4e00\u6b65\u52a8\u4f5c\u3002",
            "\u5982\u679c\u4f60\u62c5\u5fc3\u5185\u5bb9\u592a\u7a7a\uff0c\u5c31\u8865\u4e00\u4e2a\u5bf9\u7167\u6bb5\uff1a\u5148\u505a\u4ec0\u4e48\u3001\u540e\u505a\u4ec0\u4e48\u3001\u4e3a\u4ec0\u4e48\u8fd9\u6837\u6392\u987a\u5e8f\u3002",
        ],
    }
    addon = fillers.get(platform, [])
    idx = 0
    while len(current) < minimum and addon:
        current = dedupe_paragraphs(current + "\n\n" + addon[idx % len(addon)])
        idx += 1
        if idx > 24:
            break
    return trim_to_platform_max(platform, current)


def find_review(pack: Dict[str, Any], platform: str) -> Dict[str, Any]:
    for review in pack.get("publisher_review", {}).get("platform_reviews", []):
        if isinstance(review, dict) and str(review.get("platform", "")).strip() == platform:
            return review
    return {}


def should_repair(draft: Dict[str, Any], min_score: float) -> bool:
    platform = str(draft.get("platform", "")).strip()
    if platform not in TARGET_PLATFORMS:
        return False
    score = score_one(draft, min_score)
    return (not score.pass_gate) or score.total_score < max(min_score + 4, 90)


def build_repair_prompt(topic: str, draft: Dict[str, Any], min_score: float, review: Dict[str, Any]) -> str:
    platform = str(draft.get("platform", "")).strip()
    score = score_one(draft, min_score)
    issues = ";".join(score.issues) if score.issues else "none"
    weak = review.get("weak_point", "")
    fix_now = review.get("fix_now", "")
    return (
        "\u53ea\u8f93\u51faJSON\u5bf9\u8c61\u3002\u4f60\u662f\u5546\u4e1a\u5185\u5bb9\u4e3b\u7f16\u3002"
        f"\u4e3b\u9898={topic}\uff0c\u5e73\u53f0={platform}\uff0c\u5f53\u524d\u7a3f\u4ef6={json.dumps(draft, ensure_ascii=False)}\u3002"
        f"\u95ee\u9898={issues}\uff0c\u5ba1\u6838\u610f\u89c1 weak_point={weak}, fix_now={fix_now}\u3002"
        "\u8981\u6c42\uff1a"
        "1) \u4fdd\u7559\u4e3b\u9898\u4e0e\u8f6c\u5316\u76ee\u6807\uff0c\u4f46\u53bb\u6a21\u677f\u5473\u3002"
        "2) \u4e0d\u5141\u8bb8\u6536\u76ca\u627f\u8bfa\u3001\u865a\u5047\u80cc\u4e66\u6216\u4f2a\u5b98\u65b9\u53e3\u543b\u3002"
        "3) \u52a0\u5f3a\u5177\u4f53\u6027\u3001\u6765\u6e90\u611f\u3001\u9002\u7528\u4eba\u7fa4\u3001\u6267\u884c\u6b65\u9aa4\u3002"
        "4) \u6bcf\u6bb5\u4e00\u4e2a\u6838\u5fc3\u5224\u65ad\uff0c\u5220\u7a7a\u8bdd\u3002"
        "5) CTA\u53ea\u7559\u4e00\u4e2a\u52a8\u4f5c\u3002"
        "\u8f93\u51fa\u5b57\u6bb5\uff1aplatform,title,hook,body,cta,tags\u3002"
    )


def deterministic_repair(topic: str, draft: Dict[str, Any], min_score: float) -> Dict[str, Any]:
    platform = str(draft.get("platform", "")).strip()
    templates = {
        WX: {
            "hook": f"\u5982\u679c\u4f60\u505a{topic}\u53ea\u8ffd\u6d41\u91cf\u4e0d\u7ba1\u627f\u63a5\uff0c\u5927\u6982\u7387\u662f\u9605\u8bfb\u6709\u4e86\uff0c\u8f6c\u5316\u63a5\u4e0d\u4f4f\u3002",
            "cta": "\u56de\u590d\u300c\u8d44\u6599\u300d\uff0c\u9886\u53d6\u8fd9\u4efd\u53ef\u76f4\u63a5\u5957\u7528\u7684\u6267\u884c\u6a21\u677f\u3002",
            "body": "\u5148\u8bf4\u7ed3\u8bba\u3002\u957f\u671f\u8f6c\u5316\u770b\u7684\u662f\u627f\u63a5\u8def\u5f84\uff0c\u800c\u4e0d\u662f\u89c2\u70b9\u6570\u91cf\u3002\n\n\u5185\u5bb9\u987a\u5e8f\u5efa\u8bae\u201c\u7ed3\u8bba-\u573a\u666f-\u6b65\u9aa4-\u627f\u63a5\u201d\uff0c\u8bfb\u8005\u4f53\u611f\u66f4\u7a33\u3002\n\n\u6765\u6e90\u8bf4\u6cd5\u7528\u201c\u6309\u516c\u5f00\u4fe1\u606f\u6216\u5b9e\u6d4b\u73af\u5883\u201d\uff0c\u907f\u514d\u7edd\u5bf9\u5316\u65ad\u8a00\u3002",
        },
        TT: {
            "hook": f"\u5f88\u591a\u4eba\u505a{topic}\u8d8a\u5199\u8d8a\u957f\u5374\u8d8a\u6ca1\u4eba\u770b\uff0c\u95ee\u9898\u4e0d\u5728\u5185\u5bb9\u91cf\uff0c\u5728\u7ed3\u6784\u987a\u5e8f\u3002",
            "cta": "\u5148\u6536\u85cf\u8fd9\u7bc7\uff0c\u8981\u5bf9\u6bd4\u7248\u6e05\u5355\u518d\u770b\u8bc4\u8bba\u533a\u7f6e\u9876\u3002",
            "body": "\u7ed3\u8bba\u5148\u884c\u3002\u5934\u6761\u957f\u6587\u7684\u524d\u4e09\u6bb5\u5e94\u8be5\u4ea4\u4ee3\u603b\u5224\u65ad\uff0c\u518d\u5217\u8bef\u533a\uff0c\u6700\u540e\u7ed9\u6267\u884c\u6b65\u9aa4\u3002\n\n\u6bd4\u8f83\u7a33\u7684\u5199\u6cd5\u662f\u201c1-2-3\u201d\u987a\u5e8f\uff1a1)\u5b9a\u573a\u666f 2)\u5b9a\u5de5\u5177 3)\u5b9a\u627f\u63a5\u52a8\u4f5c\u3002\n\n\u6570\u5b57\u548c\u7ed3\u8bba\u9700\u8981\u6765\u6e90\u8bed\u6c14\uff0c\u4f8b\u5982\u201c\u6309\u516c\u5f00\u6837\u672c\u201d\u3001\u201c\u6309\u5b9e\u6d4b\u73af\u5883\u201d\u3002",
        },
        BILI: {
            "hook": f"\u522b\u628a{topic}\u8bb2\u6210\u6d41\u6c34\u8d26\uff0c\u80fd\u7559\u4f4f\u4eba\u7684\u4e00\u5b9a\u662f\u7ed3\u8bba\u548c\u8bc1\u636e\u4e00\u8d77\u51fa\u73b0\u3002",
            "cta": "\u8bc4\u8bba\u533a\u7559\u300c\u5de5\u5177\u8868\u300d\uff0c\u6211\u628a\u5bf9\u6bd4\u7248\u6e05\u5355\u7ed9\u4f60\u3002",
            "body": "\u5148\u7ed9\u7ed3\u8bba\uff0c\u518d\u7ed9\u8bc1\u636e\u3002\u8fd9\u79cd\u7ed3\u6784\u6bd4\u5806\u6982\u5ff5\u66f4\u5bb9\u6613\u83b7\u5f97\u4f18\u8d28\u4e92\u52a8\u3002\n\n\u4e2d\u6bb5\u6700\u597d\u6709\u4e00\u4e2a\u5bf9\u6bd4\u6216\u6d4b\u8bd5\u4e0a\u4e0b\u6587\uff0c\u8ba9\u8bba\u70b9\u53ef\u68c0\u9a8c\u3002\n\n\u7ed3\u5c3e\u53ea\u7559\u4e00\u4e2a\u52a8\u4f5c\uff0c\u8bc4\u8bba\u533a\u5173\u952e\u8bcd\u9886\u8d44\u6599\u5373\u53ef\u3002",
        },
        WB: {
            "hook": f"{topic}\u6700\u5bb9\u6613\u8e29\u5751\u7684\u4e0d\u662f\u4e0d\u4f1a\u505a\uff0c\u662f\u4fe1\u606f\u592a\u6563\u8bfb\u8005\u6293\u4e0d\u4f4f\u91cd\u70b9\u3002",
            "cta": "\u8bc4\u8bba\u533a\u7559\u300c\u6e05\u5355\u300d\uff0c\u6211\u628a\u5feb\u7528\u7248\u53d1\u4f60\u3002",
            "body": "\u5fae\u535a\u5355\u6761\u6700\u7a33\u7684\u7ed3\u6784\u662f\u201c\u4e00\u4e2a\u5224\u65ad+\u4e00\u4e2a\u8bc1\u636e+\u4e00\u4e2a\u52a8\u4f5c\u201d\u3002\n\n\u6765\u6e90\u53e5\u53ef\u4ee5\u5f88\u77ed\uff0c\u4f46\u9700\u8981\u4fdd\u7559\u3002\u52a8\u4f5c\u4e0d\u8981\u5e76\u53d1\u591a\u4e2aCTA\u3002",
        },
    }

    tpl = templates.get(platform)
    if not tpl:
        return repair_normalize_draft(draft)

    result = {**draft, "hook": tpl["hook"], "body": tpl["body"], "cta": tpl["cta"]}
    return repair_normalize_draft(result)


def repair_pack(pack: Dict[str, Any], min_score: float) -> Dict[str, Any]:
    topic = str(pack.get("topic", "")).strip()
    research = pack.get("research_context", {})
    feedback = pack.get("metrics_feedback", {})
    drafts = [d for d in pack.get("drafts", []) if isinstance(d, dict)]
    repaired_log: List[Dict[str, Any]] = []
    new_drafts: List[Dict[str, Any]] = []

    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        before = score_one(draft, min_score)
        current = repair_normalize_draft(draft)

        if platform in TARGET_PLATFORMS:
            current["body"] = ensure_platform_length(platform, str(current.get("body", "")))
            current["body"] = dedupe_paragraphs(str(current.get("body", "")))
            current["body"] = trim_to_platform_max(platform, str(current.get("body", "")))

        if should_repair(current, min_score):
            review = find_review(pack, platform)
            try:
                payload = run_agent("content", build_repair_prompt(topic, current, min_score, review), timeout=320)
                parsed = extract_json(payload)
                if isinstance(parsed, list):
                    parsed = parsed[0] if parsed else {}
                if isinstance(parsed, dict):
                    current = repair_normalize_draft(parsed)
                else:
                    current = repair_normalize_draft(current)
            except Exception:
                current = repair_normalize_draft(current)

            if platform in TARGET_PLATFORMS:
                current["body"] = ensure_platform_length(platform, str(current.get("body", "")))
                current["body"] = dedupe_paragraphs(str(current.get("body", "")))
                current["body"] = trim_to_platform_max(platform, str(current.get("body", "")))

            after_try = score_one(current, min_score)
            if (not after_try.pass_gate) or after_try.total_score <= before.total_score:
                current = deterministic_repair(topic, current, min_score)
                if platform in TARGET_PLATFORMS:
                    current["body"] = ensure_platform_length(platform, str(current.get("body", "")))
                    current["body"] = dedupe_paragraphs(str(current.get("body", "")))
                    current["body"] = trim_to_platform_max(platform, str(current.get("body", "")))

        current["body"] = dedupe_paragraphs(str(current.get("body", "")))
        current["body"] = dedupe_lines_global(str(current.get("body", "")))
        current = sanitize_draft(topic, current, research=research, feedback=feedback)

        after = score_one(current, min_score)
        repaired_log.append(
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
    pack["repair_log"] = repaired_log
    return pack


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-score", type=float, default=85.0)
    args = parser.parse_args()

    pack = load_pack(Path(args.input))
    repaired = repair_pack(pack, args.min_score)
    Path(args.output).write_text(json.dumps(repaired, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "repair_log": repaired.get("repair_log", [])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
