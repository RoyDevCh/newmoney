from pathlib import Path
import textwrap, re
root = Path(r'C:\Users\Roy\Documents\New project')

files = {}

files['production_strategy_config.py'] = '''#!/usr/bin/env python3
"""Production and publish strategy baselines for the content system."""

from __future__ import annotations

from typing import Any, Dict


PLATFORM_STRATEGY: Dict[str, Dict[str, Any]] = {
    "知乎": {
        "recommended_publish_per_day": 1,
        "recommended_produce_per_day": 2,
        "publish_windows": ["12:00-13:30", "20:00-22:00"],
        "primary_goal": "high-trust conversion",
        "post_type": "long-form answer/article",
        "manual_publish_priority": 1,
        "notes": "优先发高证据感稿件，同一天不要连续发多个高度相似选题。",
    },
    "小红书": {
        "recommended_publish_per_day": 2,
        "recommended_produce_per_day": 3,
        "publish_windows": ["11:30-13:00", "19:00-22:30"],
        "primary_goal": "save-driven growth",
        "post_type": "visual note",
        "manual_publish_priority": 2,
        "notes": "优先发收藏型清单和模板展示，图比字更重要。",
    },
    "抖音": {
        "recommended_publish_per_day": 2,
        "recommended_produce_per_day": 3,
        "publish_windows": ["12:00-13:30", "19:00-22:30"],
        "primary_goal": "traffic and profile clicks",
        "post_type": "short video",
        "manual_publish_priority": 2,
        "notes": "先保稳定节奏，不建议一开始堆太多条。",
    },
    "西瓜视频": {
        "recommended_publish_per_day": 1,
        "recommended_produce_per_day": 1,
        "publish_windows": ["12:00-14:00", "19:30-22:00"],
        "primary_goal": "watch time and compound traffic",
        "post_type": "horizontal mid-length video",
        "manual_publish_priority": 1,
        "notes": "西瓜更适合3到8分钟横屏母体视频，优先做完整信息密度，不要短平快硬塞。",
    },
    "B站": {
        "recommended_publish_per_day": 1,
        "recommended_produce_per_day": 1,
        "publish_windows": ["18:30-21:30"],
        "primary_goal": "trust and watch time",
        "post_type": "video",
        "manual_publish_priority": 1,
        "notes": "B站看单条价值，不适合高频堆量。",
    },
    "微博": {
        "recommended_publish_per_day": 2,
        "recommended_produce_per_day": 3,
        "publish_windows": ["10:00-12:00", "18:00-21:00"],
        "primary_goal": "hot-topic reach",
        "post_type": "quick reaction post",
        "manual_publish_priority": 3,
        "notes": "允许快反，但动作必须单一，避免多链路导流。",
    },
    "公众号": {
        "recommended_publish_per_day": 1,
        "recommended_produce_per_day": 1,
        "publish_windows": ["08:00-09:30", "20:00-22:00"],
        "primary_goal": "retention and lead capture",
        "post_type": "deep article",
        "manual_publish_priority": 1,
        "notes": "先做稳定深度稿，不建议日发多篇。",
    },
    "头条": {
        "recommended_publish_per_day": 2,
        "recommended_produce_per_day": 3,
        "publish_windows": ["09:00-11:00", "18:00-20:30"],
        "primary_goal": "reading scale and flow income",
        "post_type": "long graphic article",
        "manual_publish_priority": 2,
        "notes": "长图文可以一天两篇，但题材不要高度重复。",
    },
}


def build_strategy_matrix() -> Dict[str, Dict[str, Any]]:
    return {key: value.copy() for key, value in PLATFORM_STRATEGY.items()}
'''

files['platform_visual_templates.py'] = '''#!/usr/bin/env python3
"""Attach platform-specific visual template metadata to publish packs."""

from __future__ import annotations

from typing import Any, Dict


VISUAL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "知乎": {
        "aspect_ratio": "16:9",
        "safe_area": "left-title",
        "composition": "clean desk setup with one dominant focal object",
        "color_direction": "steel blue, graphite, off-white highlights",
        "typography_direction": "minimal headline, no sticker clutter",
        "cover_text_style": "专业结论型",
    },
    "小红书": {
        "aspect_ratio": "3:4",
        "safe_area": "center-top",
        "composition": "high-aesthetic lifestyle productivity scene",
        "color_direction": "warm neutral, cream, muted coral",
        "typography_direction": "soft magazine style with generous breathing room",
        "cover_text_style": "收藏清单型",
    },
    "抖音": {
        "aspect_ratio": "9:16",
        "safe_area": "center",
        "composition": "single large subject with bold contrast",
        "color_direction": "black, neon cyan, vivid red accents",
        "typography_direction": "short punchy hook, high contrast",
        "cover_text_style": "冲突纠错型",
    },
    "西瓜视频": {
        "aspect_ratio": "16:9",
        "safe_area": "left-center",
        "composition": "horizontal creator frame with layered evidence props",
        "color_direction": "deep amber, slate blue, warm tungsten",
        "typography_direction": "documentary headline and one proof cue",
        "cover_text_style": "母体内容长视频型",
    },
    "B站": {
        "aspect_ratio": "16:9",
        "safe_area": "right-title",
        "composition": "documentary tech frame with evidence props",
        "color_direction": "deep teal, tungsten, matte gray",
        "typography_direction": "strong headline with one proof cue",
        "cover_text_style": "实测结论型",
    },
    "微博": {
        "aspect_ratio": "4:3",
        "safe_area": "top-strip",
        "composition": "news-card style with one clear event cue",
        "color_direction": "clean white, crimson accent, dark text",
        "typography_direction": "headline strip and one supporting line",
        "cover_text_style": "热点快评型",
    },
    "公众号": {
        "aspect_ratio": "900:383",
        "safe_area": "center-left",
        "composition": "editorial banner with structured layout",
        "color_direction": "ink black, paper white, muted green",
        "typography_direction": "newsletter banner, restrained and readable",
        "cover_text_style": "深度指南型",
    },
    "头条": {
        "aspect_ratio": "3:2",
        "safe_area": "left-center",
        "composition": "attention-grabbing hero object with explanatory background",
        "color_direction": "amber, slate, high-key neutral",
        "typography_direction": "bold headline with one subhead",
        "cover_text_style": "长图文强标题型",
    },
}


def build_visual_templates(pack: Dict[str, Any]) -> Dict[str, Any]:
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    result: Dict[str, Any] = {}
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        if platform and platform in VISUAL_TEMPLATES:
            result[platform] = VISUAL_TEMPLATES[platform]
    return result


def attach_visual_templates(pack: Dict[str, Any]) -> Dict[str, Any]:
    pack["visual_templates"] = build_visual_templates(pack)
    return pack
'''

files['video_publish_pack_builder.py'] = '''#!/usr/bin/env python3
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
'''

files['tts_render_windows.py'] = '''#!/usr/bin/env python3
"""Render TTS audio files for video publish kits on Windows via System.Speech."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


VOICE_BY_PLATFORM = {
    "douyin": "Microsoft Yunxi Desktop",
    "xigua": "Microsoft Xiaoxiao Desktop",
    "bilibili": "Microsoft Yunyang Desktop",
}

RATE_BY_PLATFORM = {"douyin": 1, "xigua": -1, "bilibili": -1}


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def render_one(text: str, out_path: Path, voice_name: str, rate: int) -> None:
    escaped_text = text.replace("'", "''")
    escaped_voice = voice_name.replace("'", "''")
    ps = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {{
  $voice = $synth.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Name -like '*{escaped_voice}*' }} | Select-Object -First 1
  if ($voice) {{ $synth.SelectVoice($voice.VoiceInfo.Name) }}
  $synth.Rate = {rate}
  $synth.SetOutputToWaveFile('{str(out_path).replace("'", "''")}')
  $synth.Speak('{escaped_text}')
}} finally {{
  $synth.Dispose()
}}
"""
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True, timeout=300)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    pack = load_pack(Path(args.input))
    kits = pack.get("video_publish_kits", {})
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []
    for key in ["douyin", "xigua", "bilibili"]:
        kit = kits.get(key, {})
        script = str(kit.get("tts_script", "")).strip()
        if not script:
            continue
        out_path = out_dir / f"{key}_tts.wav"
        render_one(script, out_path, voice_name=VOICE_BY_PLATFORM.get(key, ""), rate=RATE_BY_PLATFORM.get(key, 0))
        results.append({"platform": key, "output_file": str(out_path), "exists": out_path.exists(), "size_mb": round(out_path.stat().st_size / (1024 * 1024), 2) if out_path.exists() else 0.0})

    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''

# truncated here intentionally; remaining files written by second script
for name, content in files.items():
    (root / name).write_text(textwrap.dedent(content), encoding='utf-8')
(metrics_dir := root / 'metrics_templates').mkdir(exist_ok=True)
(metrics_dir / 'xigua_template.csv').write_text('date,platform,content_id,title,impressions,views,likes,comments,favorites,shares,follows,profile_clicks,product_clicks,revenue,avg_watch_sec,read_complete_rate\n', encoding='utf-8')

ap = root / 'autopipeline_brain_content_publisher.py'
text = ap.read_text(encoding='utf-8')
new_block = '''STABLE_TOPICS = [
    {
        "query": "数码装备避坑与选购建议 2026",
        "priority": 1.0,
        "fit_platforms": ["知乎", "抖音", "西瓜视频", "B站", "微博", "头条"],
    },
    {
        "query": "办公效率工具清单与信息管理工作流",
        "priority": 0.99,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "公众号", "头条"],
    },
    {
        "query": "家用小电器真实使用场景与避坑清单",
        "priority": 0.97,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "头条"],
    },
    {
        "query": "内容生产提效与变现流程拆解",
        "priority": 0.95,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "公众号"],
    },
    {
        "query": "商业案例拆解与品牌增长复盘",
        "priority": 0.94,
        "fit_platforms": ["知乎", "抖音", "西瓜视频", "B站", "微博", "公众号", "头条"],
    },
    {
        "query": "知识管理与个人系统搭建",
        "priority": 0.93,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "公众号"],
    },
    {
        "query": "历史事件里的商业与认知启发",
        "priority": 0.91,
        "fit_platforms": ["知乎", "西瓜视频", "B站", "微博", "公众号", "头条"],
    },
    {
        "query": "AI工具清单与效率工作流",
        "priority": 0.9,
        "fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站", "微博", "公众号", "头条"],
    },
]
'''
text = re.sub(r'STABLE_TOPICS = \[(?s).*?\]\n\n\ndef run_cmd', new_block + '\n\ndef run_cmd', text, count=1)
text = text.replace('return best or {\n        "query": "AI内容创作提效与变现",', 'return best or {\n        "query": "办公效率工具清单与信息管理工作流",')
text = text.replace('"fit_platforms": ["知乎", "小红书", "抖音", "B站"],', '"fit_platforms": ["知乎", "小红书", "抖音", "西瓜视频", "B站"],')
ap.write_text(text, encoding='utf-8')
