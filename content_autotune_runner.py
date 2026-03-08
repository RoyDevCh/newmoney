#!/usr/bin/env python3
"""Generate monetization-ready content drafts with rewrite and quality loop."""

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

ZH = "\u77e5\u4e4e"
XHS = "\u5c0f\u7ea2\u4e66"
DY = "\u6296\u97f3"
XG = "\u897f\u74dc\u89c6\u9891"
BILI = "B\u7ad9"

PLATFORM_BRIEFS: Dict[str, Dict[str, str]] = {
    ZH: {
        "body_range": "550-950",
        "voice": "\u7406\u6027\u3001\u53ef\u9a8c\u8bc1\u3001\u7ed3\u6784\u6e05\u6670",
        "conversion": "\u5f15\u5bfc\u6536\u85cf\u3001\u8bc4\u8bba\u5173\u952e\u8bcd\u3001\u9886\u53d6\u6a21\u677f",
        "angle": "\u907f\u5751\u6307\u5357\u3001\u6a2a\u8bc4\u3001\u6d41\u7a0b\u62c6\u89e3",
        "visual": "\u6a2a\u7248\u79d1\u6280\u5c01\u9762\u3001\u6e05\u6670\u5b57\u91cd\u70b9",
    },
    XHS: {
        "body_range": "180-430",
        "voice": "\u8f7b\u677e\u3001\u573a\u666f\u5316\u3001\u5c11\u884c\u8bdd",
        "conversion": "\u5f15\u5bfc\u6536\u85cf\u3001\u5173\u6ce8\u3001\u8bc4\u8bba\u9886\u53d6",
        "angle": "\u6e05\u5355\u611f\u3001\u7acb\u5373\u53ef\u505a\u3001\u524d\u540e\u5bf9\u6bd4",
        "visual": "3:4\u7ad6\u56fe\u3001\u751f\u4ea7\u529b\u6c1b\u56f4\u3001\u5c11\u6742\u4e71",
    },
    DY: {
        "body_range": "140-280",
        "voice": "\u53e3\u8bed\u3001\u5feb\u8282\u594f\u3001\u6bcf\u53e5\u6709\u52a8\u4f5c",
        "conversion": "\u5f15\u5bfc\u5173\u6ce8\u4e3b\u9875\u3001\u8bc4\u8bba\u5173\u952e\u8bcd",
        "angle": "3\u79d2Hook\u3001\u9519\u8bef\u7ea0\u6b63\u3001\u4e09\u6b65\u6267\u884c",
        "visual": "\u9ad8\u53cd\u5dee\u5c01\u9762\u3001\u4e2d\u5fc3\u4e3b\u4f53\u5927",
    },
    XG: {
        "body_range": "420-900",
        "voice": "\u89e3\u8bf4\u611f\u3001\u8282\u594f\u5e73\u7a33\u3001\u8bc1\u636e\u5145\u8db3",
        "conversion": "\u5f15\u5bfc\u770b\u7b80\u4ecb\u8d44\u6599\u5305\u6216\u6536\u85cf\u8fde\u8f7d",
        "angle": "\u6a2a\u5c4f\u6bcd\u4f53\u89c6\u9891\u3001\u5b8c\u6574\u53d9\u4e8b\u3001\u5b9e\u64cd\u62c6\u89e3",
        "visual": "16:9\u6a2a\u7248\u8bb0\u5f55\u611f",
    },
    BILI: {
        "body_range": "320-720",
        "voice": "\u786c\u6838\u3001\u8bc1\u636e\u5148\u884c\u3001\u6709\u5b9e\u6d4b\u611f",
        "conversion": "\u5f15\u5bfc\u4e09\u8fde\u3001\u8bc4\u8bba\u533a\u9886\u8d44\u6599\u3001\u4e0b\u671f\u9009\u9898\u4e92\u52a8",
        "angle": "\u6a2a\u8bc4\u3001\u5de5\u5177\u94fe\u62c6\u89e3\u3001\u6d41\u7a0b\u6f14\u793a",
        "visual": "16:9\u7eaa\u5f55\u7247\u611f\u79d1\u6280\u573a\u666f",
    },
}

PLATFORM_MIN_BODY = {
    ZH: 550,
    XHS: 180,
    DY: 140,
    XG: 420,
    BILI: 320,
}

CLAIM_REPLACEMENTS: List[Tuple[str, str]] = [
    (r"\u6708\u5165\s*\d+\+?", "\u6548\u7387\u63d0\u5347\u660e\u663e"),
    (r"\u6708\u8d5a\s*\d+\+?", "\u6210\u672c\u56de\u6536\u901f\u5ea6\u66f4\u5feb"),
    (r"\u6536\u5165\u7ffb\u500d", "\u4ea7\u80fd\u63d0\u5347\u660e\u663e"),
    (r"\u591a\u8d5a\s*\d+\+?", "\u8f6c\u5316\u6548\u7387\u66f4\u9ad8"),
    (r"\u670d\u52a1\s*\d+\+?\s*\u5bb6\u4f01\u4e1a", "\u670d\u52a1\u8fc7\u591a\u79cd\u4f01\u4e1a\u573a\u666f"),
    (r"\u7d2f\u8ba1\u5b66\u5458\s*\d+\+?", "\u6709\u6301\u7eed\u7528\u6237\u5b9e\u8df5\u53cd\u9988"),
    (r"\d+\+?\s*\u4f01\u4e1a\u5ba2\u6237", "\u591a\u7c7b\u4f01\u4e1a\u573a\u666f"),
    (r"\d+\+?\s*\u5b66\u5458", "\u591a\u4e2a\u771f\u5b9e\u4f7f\u7528\u573a\u666f"),
]


EMOJI_BROAD_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)


def run_agent(agent: str, prompt: str, timeout: int = 300) -> str:
    compact_prompt = re.sub(r"\s+", " ", prompt).strip()
    if NODE_BIN.exists() and OPENCLAW_ENTRY.exists():
        cmd: List[str] = [
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
        timeout=timeout + 80,
    )
    if p.returncode != 0:
        raise RuntimeError((p.stderr or "").strip() or f"returncode={p.returncode}")
    return unwrap_openclaw_payload((p.stdout or "").strip())


def extract_json(text: str) -> Any:
    payload = (text or "").strip()
    if not payload:
        raise ValueError("empty text")

    try:
        return json.loads(payload)
    except Exception:
        pass

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", payload, flags=re.S | re.I)
    candidate = match.group(1) if match else payload
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
    raise ValueError("unsupported json structure")


def select_best_drafts(drafts: List[Dict[str, Any]], platforms: List[str], min_score: float) -> List[Dict[str, Any]]:
    chosen: List[Dict[str, Any]] = []
    for platform in platforms:
        candidates = [d for d in drafts if str(d.get("platform", "")).strip() == platform]
        if not candidates:
            continue
        best = max(candidates, key=lambda d: score_one(d, min_score).total_score)
        chosen.append(best)
    return chosen


def build_platform_rules(platforms: List[str]) -> str:
    chunks: List[str] = []
    for platform in platforms:
        brief = PLATFORM_BRIEFS.get(platform, {})
        chunks.append(
            f"{platform}: body={brief.get('body_range','')}, voice={brief.get('voice','')}, "
            f"conversion={brief.get('conversion','')}, angle={brief.get('angle','')}"
        )
    return " | ".join(chunks)


def build_strategy_prompt(topic: str, platforms: List[str]) -> str:
    return (
        f"\u53ea\u8f93\u51faJSON\u3002\u4e3b\u9898={topic}\uff0c\u76ee\u6807\u5e73\u53f0={','.join(platforms)}\u3002"
        "\u8bf7\u7ed9\u51fa\u4eca\u65e5\u7684\u53ef\u53d8\u73b0\u5185\u5bb9\u7b56\u7565\uff0c\u5b57\u6bb5:"
        "audience,pain_point,conversion_goal,offer,platform_priority,angle,proof_points。"
        "proof_points\u81f3\u5c113\u6761\u3002"
    )


def build_init_prompt(topic: str, platforms: List[str], strategy: Dict[str, Any]) -> str:
    strategy_json = json.dumps(strategy, ensure_ascii=False)
    return (
        f"\u53ea\u8f93\u51faJSON\u6570\u7ec4\u3002\u57fa\u4e8e\u4e3b\u9898={topic}\uff0c\u5e73\u53f0={','.join(platforms)}\uff0c\u7b56\u7565={strategy_json}\u3002"
        "\u4e3a\u6bcf\u4e2a\u5e73\u53f0\u751f\u6210\u4e00\u6761\u7a3f\u4ef6\uff0c\u5fc5\u987b\u5305\u542b\u5b57\u6bb5:"
        "platform,title,hook,body,cta,tags\u3002"
        "\u8981\u6c42:"
        "1) \u7ed3\u8bba\u5148\u884c -> \u8bc1\u636e -> \u52a8\u4f5c\u3002"
        "2) \u6570\u5b57\u5fc5\u987b\u5e26\u6e90\u4fe1\u53f7(\u516c\u5f00\u8bc4\u6d4b/\u5b9e\u6d4b\u73af\u5883/\u5b98\u65b9\u4fe1\u606f)\u3002"
        "3) \u7981\u6b62\u7edd\u5bf9\u5316\u3001\u5305\u8d5a\u3001\u6708\u5165\u7b49\u8868\u8fbe\u3002"
        "4) \u7981\u6b62\u4f2a\u80cc\u4e66\u548c\u4e0d\u53ef\u6838\u5b9e\u6210\u7ee9\u58f0\u660e\u3002"
        "5) \u4e0d\u8981markdown\uff0c\u4e0d\u8981\u89e3\u91ca\u3002"
        f"6) \u5e73\u53f0\u89c4\u5219={build_platform_rules(platforms)}\u3002"
    )


def build_rewrite_prompt(topic: str, draft: Dict[str, Any], score: DraftScore, strategy: Dict[str, Any]) -> str:
    platform = str(draft.get("platform", "")).strip()
    brief = PLATFORM_BRIEFS.get(platform, {})
    issues = ";".join(score.issues) if score.issues else "none"
    return (
        "\u53ea\u8f93\u51faJSON\u5bf9\u8c61\u3002"
        f"\u4e3b\u9898={topic}\uff0c\u5e73\u53f0={platform}\uff0c\u7b56\u7565={json.dumps(strategy, ensure_ascii=False)}\u3002"
        f"\u5f53\u524d\u7a3f\u4ef6={json.dumps(draft, ensure_ascii=False)}\uff0c\u95ee\u9898={issues}\u3002"
        "\u8bf7\u6309\u53d1\u5e03\u6c34\u51c6\u91cd\u5199\uff1a"
        "1) \u5f00\u5934\u8981\u6709\u51b2\u7a81\u70b9\u3002"
        "2) \u5168\u6587\u7ed3\u6784=\u7ed3\u8bba -> \u8bc1\u636e -> \u53ef\u6267\u884c\u52a8\u4f5c\u3002"
        "3) \u5220\u6389\u5957\u8bdd\u3001\u7a7a\u8bdd\u3001\u4e0d\u53ef\u9a8c\u8bc1\u786c\u7ed3\u8bba\u3002"
        "4) \u6570\u5b57\u8868\u8fbe\u9700\u8981\u6765\u6e90\u8bed\u6c14\u3002"
        f"5) \u6b63\u6587\u957f\u5ea6\u8bf7\u9075\u5b88{brief.get('body_range', 'platform requirement')}\u3002"
        f"6) \u8bed\u6c14={brief.get('voice','')}\uff0cCTA={brief.get('conversion','')}\u3002"
        "7) \u7981\u6b62\u6708\u5165/\u6708\u8d5a/\u6536\u5165\u7ffb\u500d/\u865a\u5047\u80cc\u4e66\u3002"
        "8) \u53ea\u8f93\u51fa\u5b57\u6bb5platform,title,hook,body,cta,tags\u3002"
    )


def build_publisher_review_prompt(topic: str, drafts: List[Dict[str, Any]]) -> str:
    return (
        "\u53ea\u8f93\u51faJSON\u5bf9\u8c61\u3002"
        f"\u8bf7\u5ba1\u6838\u4e3b\u9898={topic}\u7684\u7a3f\u4ef6\uff1a{json.dumps(drafts, ensure_ascii=False)}\u3002"
        "\u8f93\u51fa\u5b57\u6bb5: verdict, platform_reviews, monetization_risks, next_actions\u3002"
        "platform_reviews\u662f\u6570\u7ec4\uff0c\u6bcf\u9879\u5b57\u6bb5: platform, pass, strongest_selling_point, weak_point, fix_now\u3002"
    )


def build_visual_prompt(topic: str, draft: Dict[str, Any]) -> str:
    platform = str(draft.get("platform", "")).strip()
    brief = PLATFORM_BRIEFS.get(platform, {})
    return (
        "\u53ea\u8f93\u51faJSON\u5bf9\u8c61\u3002"
        f"\u4e3b\u9898={topic}\uff0c\u5e73\u53f0={platform}\uff0c\u7a3f\u4ef6={json.dumps(draft, ensure_ascii=False)}\u3002"
        f"\u89c6\u89c9\u65b9\u5411={brief.get('visual', '\u79d1\u6280\u5546\u4e1a\u5c01\u9762')}\u3002"
        "\u8f93\u51fa\u5b57\u6bb5: platform, prompt, negative_prompt, composition, aspect_ratio\u3002"
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
    while not score.pass_gate and rounds < max_rewrite_rounds:
        rounds += 1
        rewritten = run_agent("content", build_rewrite_prompt(topic, current, score, strategy), timeout=320)
        obj = extract_json(rewritten)
        if isinstance(obj, list):
            obj = obj[0] if obj else {}
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
            parsed = extract_json(payload)
            if isinstance(parsed, dict):
                assets.append(parsed)
            else:
                assets.append({"platform": draft.get("platform", ""), "error": "visual_prompt_not_dict"})
        except Exception as exc:
            assets.append({"platform": draft.get("platform", ""), "error": str(exc)})
    return assets


def strip_visual_noise(text: str, keep_small: bool) -> str:
    current = (text or "").replace("\r", "").strip()
    current = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", current)
    if not keep_small:
        current = EMOJI_BROAD_RE.sub("", current)
    current = re.sub(r"[ \t]{2,}", " ", current)
    current = re.sub(r"\n{3,}", "\n\n", current)
    return current.strip()


def scrub_claims(text: str) -> str:
    current = text
    for pattern, replacement in CLAIM_REPLACEMENTS:
        current = re.sub(pattern, replacement, current)
    return current


def extend_body_if_needed(platform: str, topic: str, body: str) -> str:
    minimum = PLATFORM_MIN_BODY.get(platform, 0)
    if len(body) >= minimum:
        return body

    supplement_map = {
        ZH: [
            "",
            "\u3010\u843d\u5730\u6b65\u9aa4\u3011",
            f"1) \u5148\u62c6\u51fa\u4f60\u5728{topic}\u91cc\u6700\u8017\u65f6\u76843\u4e2a\u52a8\u4f5c\uff1b",
            "2) \u6bcf\u4e2a\u52a8\u4f5c\u5148\u5199\u6e05\u8f93\u5165\u548c\u8f93\u51fa\u6807\u51c6\uff1b",
            "3) \u53ea\u628a\u53ef\u5feb\u901f\u590d\u6838\u7684\u73af\u8282\u63a5\u5165\u81ea\u52a8\u5316\u3002",
        ],
        BILI: [
            "",
            "\u3010\u5b9e\u64cd\u5efa\u8bae\u3011",
            "\u4ece\u5355\u70b9\u5de5\u4f5c\u6d41\u8dd1\u901a\u5f00\u59cb\uff0c\u4f8b\u5982\u7d20\u6750\u6574\u7406\u6216\u521d\u7a3f\u751f\u6210\uff0c\u518d\u9010\u6b65\u6269\u5230\u5168\u6d41\u7a0b\u3002",
        ],
        XG: [
            "",
            "\u3010\u89c6\u9891\u8282\u594f\u5efa\u8bae\u3011",
            "\u524d15\u79d2\u5148\u7ed9\u7ed3\u8bba\uff0c\u4e2d\u95f4\u7ed9\u8bc1\u636e\u548c\u6d41\u7a0b\uff0c\u5c3e\u90e8\u7ed9\u6267\u884c\u6e05\u5355\u3002",
        ],
        DY: [
            "",
            "\u5148\u8dd1\u901a\u4e00\u4e2a\u9ad8\u9891\u573a\u666f\uff0c\u518d\u590d\u5236\u5230\u5176\u4ed6\u573a\u666f\u3002",
        ],
        XHS: [
            "",
            "\u5148\u4ece\u4e00\u4e2a\u53ef\u7acb\u5373\u6267\u884c\u7684\u5c0f\u6b65\u9aa4\u5f00\u59cb\uff0c\u518d\u6269\u5c55\u5230\u66f4\u591a\u573a\u666f\u3002",
        ],
    }
    extra = supplement_map.get(platform, ["", "\u8bf7\u8865\u5145\u66f4\u5177\u4f53\u7684\u573a\u666f\u6b65\u9aa4\u4e0e\u5bf9\u6bd4\u7ec6\u8282\u3002"])
    merged = body.rstrip() + "\n" + "\n".join(extra).strip()
    return merged.strip()


def sanitize_draft(topic: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    platform = str(draft.get("platform", "")).strip()
    keep_small = platform in {XHS, DY}
    cleaned = dict(draft)

    for key in ["title", "hook", "body", "cta"]:
        value = str(cleaned.get(key, "")).strip()
        value = scrub_claims(value)
        value = strip_visual_noise(value, keep_small=keep_small)
        cleaned[key] = value

    cleaned["body"] = extend_body_if_needed(platform, topic, str(cleaned.get("body", "")))
    tags = cleaned.get("tags", [])
    cleaned["tags"] = [
        strip_visual_noise(scrub_claims(str(tag)), keep_small=True)
        for tag in tags
        if str(tag).strip()
    ]
    return cleaned


def fallback_review(drafts: List[Dict[str, Any]], min_score: float) -> Dict[str, Any]:
    rows = []
    for draft in drafts:
        scored = score_one(draft, min_score)
        rows.append(
            {
                "platform": draft.get("platform", ""),
                "pass": scored.pass_gate,
                "strongest_selling_point": "hook_and_cta_ready" if scored.total_score >= min_score else "needs_rewrite",
                "weak_point": ",".join(scored.issues[:3]) or "none",
                "fix_now": "improve evidence, structure and CTA",
            }
        )
    return {
        "verdict": "fallback_review",
        "platform_reviews": rows,
        "monetization_risks": [],
        "next_actions": [
            "continue_rewrite_for_failed_platforms",
            "generate_cover_assets",
            "manual_editorial_spot_check_before_publish",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic")
    parser.add_argument("--topic-file")
    parser.add_argument("--platforms", nargs="+", default=[ZH, XHS, DY, BILI, XG])
    parser.add_argument("--min-score", type=float, default=85.0)
    parser.add_argument("--max-rewrite-rounds", type=int, default=3)
    parser.add_argument("--out", default="autotuned_drafts.json")
    args = parser.parse_args()

    if args.topic_file:
        topic = Path(args.topic_file).read_text(encoding="utf-8-sig").strip()
    else:
        topic = (args.topic or "").strip()
    if not topic:
        raise SystemExit("missing topic: use --topic or --topic-file")

    strategy = extract_json(run_agent("main-brain", build_strategy_prompt(topic, args.platforms), timeout=220))
    raw = run_agent("content", build_init_prompt(topic, args.platforms, strategy), timeout=380)
    base_drafts = normalize_list(extract_json(raw))
    drafts = select_best_drafts(base_drafts, args.platforms, args.min_score)

    final_drafts: List[Dict[str, Any]] = []
    score_log: List[Dict[str, Any]] = []

    for draft in drafts:
        final, score_row = optimize_draft(
            topic=topic,
            draft=draft,
            strategy=strategy,
            min_score=args.min_score,
            max_rewrite_rounds=args.max_rewrite_rounds,
        )
        final = sanitize_draft(topic, final)
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
        publisher_review = extract_json(run_agent("publisher", build_publisher_review_prompt(topic, final_drafts), timeout=260))
    except Exception:
        publisher_review = fallback_review(final_drafts, args.min_score)

    assets = generate_asset_prompts(topic, final_drafts)

    payload = {
        "topic": topic,
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
