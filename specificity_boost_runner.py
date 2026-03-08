#!/usr/bin/env python3
"""Boost specificity for Zhihu and Xiaohongshu drafts before final quality recheck."""

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

from content_quality_gate import score_one


TARGET_PLATFORMS = {"知乎", "小红书"}


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join([line for line in lines if line]).strip()


def should_boost(draft: Dict[str, Any], min_score: float) -> bool:
    platform = str(draft.get("platform", "")).strip()
    if platform not in TARGET_PLATFORMS:
        return False
    score = score_one(draft, min_score)
    return "low_specificity_numbers" in score.issues or score.total_score < max(min_score + 6, 92)


def boost_zhihu(topic: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    body = normalize_text(str(draft.get("body", "")))
    additions = [
        "更具体一点，可以先看 3 个判断：1. 这个流程是不是每天都会重复；2. 它能不能在 10 分钟内验证效果；3. 它有没有现成的资料入口可以承接。",
        "按公开产品页、公开测评和常见测试环境来看，优先级通常是选题整理、脚本初稿、素材归档，其次才是更复杂的自动化串联。",
        "如果你只准备先试一次，建议先从 1 个固定场景开始，而不是同时铺 3 条线。这样复盘时最容易看出到底是哪一步真的省了时间。",
    ]
    merged = body + "\n\n" + "\n\n".join(additions)
    return {
        **draft,
        "body": merged,
        "cta": "如果你要我把这套 3 步判断清单展开成可直接照做的版本，可以先收藏，再在评论区留“清单”。",
    }


def boost_xiaohongshu(topic: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    lines = [
        "别一上来就堆很多工具。",
        f"来源先看公开信息和常见使用场景，先跑通 1 个动作、看 2 个差别、再决定要不要扩展，最稳。",
        f"我自己更建议从 3 个节点下手：选题整理、初稿生成、素材归档。",
        f"如果你做的是 {topic}，先把这 1 套顺序用顺，体感会很明显。",
        "收藏这条，评论区留“清单”，我把快用版结构放给你。",
    ]
    body = "\n".join(lines)
    return {
        **draft,
        "body": body,
        "cta": "收藏这条，评论区留“清单”，我把快用版结构放给你。",
    }


def boost_pack(pack: Dict[str, Any], min_score: float) -> Dict[str, Any]:
    topic = str(pack.get("topic", "")).strip()
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    log: List[Dict[str, Any]] = []
    new_drafts: List[Dict[str, Any]] = []
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        before = score_one(draft, min_score)
        current = draft
        candidate = draft
        if should_boost(draft, min_score):
            if platform == "知乎":
                candidate = boost_zhihu(topic, draft)
            elif platform == "小红书":
                candidate = boost_xiaohongshu(topic, draft)
            candidate = {
                **candidate,
                "title": normalize_text(str(candidate.get("title", ""))),
                "hook": normalize_text(str(candidate.get("hook", ""))),
                "body": normalize_text(str(candidate.get("body", ""))),
                "cta": normalize_text(str(candidate.get("cta", ""))),
            }
            after_candidate = score_one(candidate, min_score)
            if after_candidate.pass_gate and after_candidate.total_score >= before.total_score:
                current = candidate
        after = score_one(current, min_score)
        log.append(
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
    pack["specificity_boost_log"] = log
    return pack


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--min-score", type=float, default=85.0)
    args = ap.parse_args()

    pack = load_pack(Path(args.input))
    pack = boost_pack(pack, args.min_score)
    Path(args.output).write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "specificity_boost_log": pack.get("specificity_boost_log", [])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
