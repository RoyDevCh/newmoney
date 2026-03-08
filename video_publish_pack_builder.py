#!/usr/bin/env python3
"""Build video-ready publish kits for Douyin, Xigua, and Bilibili drafts."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List


def sentence_chunks(text: str, limit: int) -> List[str]:
    raw = re.split(r"[。！？!?\n]+", text)
    chunks = [x.strip(" ，、；：") for x in raw if x.strip(" ，、；：")]
    return chunks[:limit]


def shorten(text: str, length: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= length:
        return text
    return text[: max(0, length - 1)] + "…"


def build_timeline(shot_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    timeline = []
    cursor = 0
    for item in shot_list:
        start = cursor
        end = cursor + int(item["duration_sec"])
        timeline.append({"shot": item["shot"], "start_sec": start, "end_sec": end, "subtitle": item["subtitle"]})
        cursor = end
    return timeline


def join_tts_script(segments: List[str]) -> str:
    return "\n".join([seg.strip() for seg in segments if seg.strip()])


def build_shots(segments: List[str], visuals: List[str], first_duration: int, rest_duration: int, subtitle_limit: int) -> List[Dict[str, Any]]:
    shot_list = []
    for idx, seg in enumerate(segments, start=1):
        shot_list.append(
            {
                "shot": idx,
                "duration_sec": first_duration if idx == 1 else rest_duration,
                "visual": visuals[min(idx - 1, len(visuals) - 1)],
                "voiceover": seg,
                "subtitle": shorten(seg, subtitle_limit),
            }
        )
    return shot_list


def douyin_kit(topic: str, draft: Dict[str, Any], appendix: Dict[str, Any]) -> Dict[str, Any]:
    body = str(draft.get("body", "")).strip()
    hook = str(draft.get("hook", "")).strip()
    cta = str(draft.get("cta", "")).strip()
    beats = sentence_chunks(" ".join([hook, body, cta]), 6)
    spoken_beats = appendix.get("spoken_beats", []) if isinstance(appendix, dict) else []
    visuals = ["高对比科技桌面主画面", "工具操作特写", "前后对比字幕卡", "三步流程信息卡", "结果页或模板页", "评论区关键词结尾卡"]
    shot_list = build_shots(beats, visuals, first_duration=4, rest_duration=5, subtitle_limit=18)
    return {
        "platform": "抖音",
        "topic": topic,
        "cover_text": shorten(str(draft.get("title", "")).strip() or hook, 16),
        "opening_hook": shorten(hook or body, 26),
        "voice_segments": beats,
        "tts_script": join_tts_script(beats),
        "shot_list": shot_list,
        "subtitle_timeline": build_timeline(shot_list),
        "comment_cta": appendix.get("comment_keyword", "工具清单") if isinstance(appendix, dict) else "工具清单",
        "edit_notes": ["首屏2秒内给结论，不铺垫背景。", "字幕每行控制在12字左右，保持高密度。", "第二镜头前必须出现一处明确对比。", "结尾CTA只保留一个动作，避免分散。"],
        "appendix_beats": spoken_beats,
    }


def xigua_kit(topic: str, draft: Dict[str, Any], appendix: Dict[str, Any]) -> Dict[str, Any]:
    body = str(draft.get("body", "")).strip()
    hook = str(draft.get("hook", "")).strip()
    cta = str(draft.get("cta", "")).strip()
    bullet_points = appendix.get("bullet_points", []) if isinstance(appendix, dict) else []
    base_sections = sentence_chunks(" ".join([hook, body, cta]), 12)
    if bullet_points:
        base_sections = (base_sections[:4] + [str(x).strip() for x in bullet_points if str(x).strip()][:4] + base_sections[4:])[:12]
    sections = base_sections[:12] or [shorten(body or hook or topic, 80)]
    visuals = ["横屏开场封面与结论字幕", "问题背景说明画面", "测试环境或案例卡片", "核心误区对比表", "第一步操作演示", "第二步操作演示", "第三步操作演示", "结果前后对照", "适用人群说明", "不适用人群提醒", "资料包或清单展示", "结尾行动引导卡"]
    shot_list = build_shots(sections, visuals, first_duration=14, rest_duration=18, subtitle_limit=26)
    return {
        "platform": "西瓜视频",
        "topic": topic,
        "cover_text": shorten(str(draft.get("title", "")).strip() or hook, 18),
        "opening_hook": shorten(hook or body, 34),
        "voice_segments": sections,
        "tts_script": join_tts_script(sections),
        "shot_list": shot_list,
        "subtitle_timeline": build_timeline(shot_list),
        "description_bullets": bullet_points,
        "resource_pack": appendix.get("resource_pack", []) if isinstance(appendix, dict) else [],
        "edit_notes": ["西瓜优先做3到8分钟横屏母体视频，不要照搬短视频剪法。", "前30秒完成结论、问题、适用人群三件事。", "中段必须有对比表、步骤演示或案例拆解。", "结尾引导收藏或看系列下一条，不要多动作并发。"],
    }


def bilibili_kit(topic: str, draft: Dict[str, Any], appendix: Dict[str, Any]) -> Dict[str, Any]:
    body = str(draft.get("body", "")).strip()
    hook = str(draft.get("hook", "")).strip()
    cta = str(draft.get("cta", "")).strip()
    sections = sentence_chunks(" ".join([hook, body, cta]), 8)
    bullets = appendix.get("bullet_points", []) if isinstance(appendix, dict) else []
    visual_styles = ["冷静科技场景全景", "界面操作中景", "对比表特写", "流程拆解卡片", "结果展示镜头", "资源包展示镜头", "评论区置顶引导卡", "结尾封面回收镜头"]
    shot_list = build_shots(sections, visual_styles, first_duration=6, rest_duration=7, subtitle_limit=22)
    return {
        "platform": "B站",
        "topic": topic,
        "cover_text": shorten(str(draft.get("title", "")).strip() or hook, 20),
        "opening_hook": shorten(hook or body, 32),
        "voice_segments": sections,
        "tts_script": join_tts_script(sections),
        "shot_list": shot_list,
        "subtitle_timeline": build_timeline(shot_list),
        "description_bullets": bullets,
        "resource_pack": appendix.get("resource_pack", []) if isinstance(appendix, dict) else [],
        "edit_notes": ["前三镜头完成结论、证据、适用人群三件事。", "口播可以更稳，但每6到8秒要切一次镜头。", "对比表放在中段，首屏只保留一个关键判断。", "简介区挂资料包，不要在正文里堆太多下载指令。"],
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
        elif platform == "西瓜视频":
            output["xigua"] = xigua_kit(topic, draft, appendices.get("xigua", {}))
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
