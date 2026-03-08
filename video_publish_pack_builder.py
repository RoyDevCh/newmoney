#!/usr/bin/env python3
"""Build video-ready publish kits for Douyin and Bilibili drafts."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List


def sentence_chunks(text: str, limit: int) -> List[str]:
    raw = re.split(r"[。！？!?；;\n]+", text)
    chunks = [x.strip(" ，,") for x in raw if x.strip(" ，,")]
    if not chunks:
        return []
    return chunks[:limit]


def shorten(text: str, length: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= length:
        return text
    return text[: max(0, length - 1)] + "…"


def douyin_kit(topic: str, draft: Dict[str, Any], appendix: Dict[str, Any]) -> Dict[str, Any]:
    body = str(draft.get("body", "")).strip()
    hook = str(draft.get("hook", "")).strip()
    cta = str(draft.get("cta", "")).strip()
    beats = sentence_chunks(" ".join([hook, body, cta]), 6)
    spoken_beats = appendix.get("spoken_beats", []) if isinstance(appendix, dict) else []
    shot_list = []
    for idx, beat in enumerate(beats, start=1):
        shot_list.append(
            {
                "shot": idx,
                "duration_sec": 4 if idx == 1 else 5,
                "visual": [
                    "高对比度科技办公桌面",
                    "工具操作特写",
                    "前后对比字幕卡",
                    "清单式信息卡",
                    "结果页或模板页",
                    "评论区引导结束卡",
                ][min(idx - 1, 5)],
                "voiceover": beat,
                "subtitle": shorten(beat, 18),
            }
        )
    timeline = []
    cursor = 0
    for item in shot_list:
        start = cursor
        end = cursor + int(item["duration_sec"])
        timeline.append(
            {
                "shot": item["shot"],
                "start_sec": start,
                "end_sec": end,
                "subtitle": item["subtitle"],
            }
        )
        cursor = end
    return {
        "platform": "抖音",
        "topic": topic,
        "cover_text": shorten(str(draft.get("title", "")).strip() or hook, 16),
        "opening_hook": shorten(hook or body, 26),
        "voice_segments": beats,
        "shot_list": shot_list,
        "comment_cta": appendix.get("comment_keyword", "工具清单") if isinstance(appendix, dict) else "工具清单",
        "subtitle_timeline": timeline,
        "edit_notes": [
            "首屏 2 秒内给结论，不铺垫背景。",
            "字幕每行控制在 12 字左右，保持高密度。",
            "第二镜头前必须出现一处明确对比。",
            "结尾 CTA 只保留一个动作，避免分散。",
        ],
        "appendix_beats": spoken_beats,
    }


def bilibili_kit(topic: str, draft: Dict[str, Any], appendix: Dict[str, Any]) -> Dict[str, Any]:
    body = str(draft.get("body", "")).strip()
    hook = str(draft.get("hook", "")).strip()
    cta = str(draft.get("cta", "")).strip()
    sections = sentence_chunks(" ".join([hook, body, cta]), 8)
    bullets = appendix.get("bullet_points", []) if isinstance(appendix, dict) else []
    shot_list = []
    visual_styles = [
        "冷静科技场景全景",
        "界面操作中景",
        "对比表特写",
        "流程拆解卡片",
        "结果展示镜头",
        "资源包展示镜头",
        "评论区置顶引导卡",
        "结尾封面回收镜头",
    ]
    for idx, section in enumerate(sections, start=1):
        shot_list.append(
            {
                "shot": idx,
                "duration_sec": 6 if idx <= 2 else 7,
                "visual": visual_styles[min(idx - 1, len(visual_styles) - 1)],
                "voiceover": section,
                "subtitle": shorten(section, 22),
            }
        )
    timeline = []
    cursor = 0
    for item in shot_list:
        start = cursor
        end = cursor + int(item["duration_sec"])
        timeline.append(
            {
                "shot": item["shot"],
                "start_sec": start,
                "end_sec": end,
                "subtitle": item["subtitle"],
            }
        )
        cursor = end
    return {
        "platform": "B站",
        "topic": topic,
        "cover_text": shorten(str(draft.get("title", "")).strip() or hook, 20),
        "opening_hook": shorten(hook or body, 32),
        "voice_segments": sections,
        "shot_list": shot_list,
        "description_bullets": bullets,
        "resource_pack": appendix.get("resource_pack", []) if isinstance(appendix, dict) else [],
        "subtitle_timeline": timeline,
        "edit_notes": [
            "前三镜头必须完成结论、证据、适用人群三件事。",
            "口播可以更稳，但每 6 到 8 秒要切一次镜头。",
            "把对比表留给中段，首屏只保留一个关键判断。",
            "简介区挂资料包，不要在正文里塞太多下载指令。",
        ],
    }


def build_video_publish_pack(pack: Dict[str, Any]) -> Dict[str, Any]:
    topic = str(pack.get("topic", "")).strip()
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    appendices = pack.get("appendices", {})
    output: Dict[str, Any] = {}
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        if platform == "抖音":
            output["douyin"] = douyin_kit(topic, draft, appendices.get("douyin", {}))
        elif platform == "B站":
            output["bilibili"] = bilibili_kit(topic, draft, appendices.get("bilibili", {}))
    return output


def main() -> None:
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    pack = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    pack["video_publish_kits"] = build_video_publish_pack(pack)
    Path(args.output).write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "keys": list(pack["video_publish_kits"].keys())}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
