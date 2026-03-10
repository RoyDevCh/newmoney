#!/usr/bin/env python3
"""Build a manual publish queue and notification pack from a content pack."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from production_strategy_config import build_strategy_matrix


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_json_optional(path_value: str) -> Dict[str, Any]:
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.exists():
        return {}
    return load_json(path)


def quality_map(quality: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = quality.get("results", []) or quality.get("scores", [])
    mapped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict):
            platform = str(row.get("platform", "")).strip()
            if platform:
                mapped[platform] = row
    return mapped


def asset_map(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    mapped: Dict[str, Dict[str, Any]] = {}
    for row in manifest.get("results", []):
        if isinstance(row, dict):
            platform = str(row.get("platform", "")).strip()
            if platform:
                mapped[platform] = row
    return mapped


def tts_map(tts_dir: Path) -> Dict[str, str]:
    if not tts_dir.exists():
        return {}
    result: Dict[str, str] = {}
    for file in tts_dir.iterdir():
        name = file.name.lower()
        if "douyin" in name:
            result["抖音"] = str(file)
        elif "xigua" in name:
            result["西瓜视频"] = str(file)
        elif "bilibili" in name:
            result["B站"] = str(file)
    return result


def join_lines(values: Any) -> str:
    if isinstance(values, list):
        return "\n".join(str(x) for x in values if str(x).strip())
    if isinstance(values, str):
        return values
    return ""


def material_slots_text(slots: Any) -> str:
    if not isinstance(slots, list) or not slots:
        return "当前没有额外图位建议。"
    lines: List[str] = []
    for idx, row in enumerate(slots, start=1):
        if not isinstance(row, dict):
            continue
        slot = str(row.get("slot", f"图位 {idx}")).strip()
        purpose = str(row.get("purpose", "")).strip()
        cue = str(row.get("cue", "")).strip()
        search_query = str(row.get("search_query", "")).strip()
        must_show = [str(x).strip() for x in row.get("must_show", []) if str(x).strip()]
        lines.append(f"{idx}. {slot} | 用途：{purpose or '未标注'}")
        if cue:
            lines.append(f"   画面要求：{cue}")
        if search_query:
            lines.append(f"   搜图词：{search_query}")
        if must_show:
            lines.append(f"   必须出现：{'、'.join(must_show)}")
    return "\n".join(lines) if lines else "当前没有额外图位建议。"


def reference_links_text(rows: Any) -> str:
    if not isinstance(rows, list) or not rows:
        return "当前没有直达入口。"
    lines: List[str] = []
    for idx, row in enumerate(rows[:8], start=1):
        if not isinstance(row, dict):
            continue
        label = str(row.get("label", f"入口 {idx}")).strip()
        query = str(row.get("query", "")).strip()
        url = str(row.get("url", "")).strip()
        lines.append(f"{idx}. {label} | 查询：{query}")
        if url:
            lines.append(f"   {url}")
    return "\n".join(lines) if lines else "当前没有直达入口。"


def reference_candidates_text(rows: Any) -> str:
    if not isinstance(rows, list) or not rows:
        return "当前没有自动抽到的页面预览图候选。"
    lines: List[str] = []
    for idx, row in enumerate(rows[:8], start=1):
        if not isinstance(row, dict):
            continue
        title = str(row.get("page_title", "")).strip() or "未命名页面"
        domain = str(row.get("source_domain", "")).strip()
        page_url = str(row.get("page_url", "")).strip()
        image_url = str(row.get("image_url", "")).strip()
        score = str(row.get("score", "")).strip()
        lines.append(f"{idx}. {title} | {domain} | score={score}")
        if page_url:
            lines.append(f"   页面：{page_url}")
        if image_url:
            lines.append(f"   图片：{image_url}")
    return "\n".join(lines) if lines else "当前没有自动抽到的页面预览图候选。"


def pick_manual_publish_items(pack: Dict[str, Any], quality: Dict[str, Any], manifest: Dict[str, Any], tts_files: Dict[str, str]) -> List[Dict[str, Any]]:
    strategies = build_strategy_matrix()
    qmap = quality_map(quality)
    amap = asset_map(manifest)
    vmap = pack.get("visual_templates", {}) if isinstance(pack, dict) else {}
    items: List[Dict[str, Any]] = []
    for draft in pack.get("drafts", []):
        if not isinstance(draft, dict):
            continue
        platform = str(draft.get("platform", "")).strip()
        strategy = strategies.get(platform, {})
        q = qmap.get(platform, {})
        a = amap.get(platform, {})
        vt = vmap.get(platform, {}) if isinstance(vmap, dict) else {}
        items.append(
            {
                "platform": platform,
                "title": draft.get("title", ""),
                "hook": draft.get("hook", ""),
                "body": draft.get("body", draft.get("content", "")),
                "cta": draft.get("cta", ""),
                "tags": draft.get("tags", []),
                "score": float(q.get("total_score", q.get("score", 0.0)) or 0.0),
                "pass": bool(q.get("pass_gate", q.get("pass", False))),
                "publish_windows": strategy.get("publish_windows", []),
                "recommended_publish_per_day": strategy.get("recommended_publish_per_day", 1),
                "recommended_produce_per_day": strategy.get("recommended_produce_per_day", 1),
                "primary_goal": strategy.get("primary_goal", ""),
                "post_type": strategy.get("post_type", ""),
                "manual_publish_priority": strategy.get("manual_publish_priority", 9),
                "notes": strategy.get("notes", ""),
                "cover_file": a.get("output_file", ""),
                "cover_strategy": a.get("cover_strategy", vt.get("image_strategy", "comfy_generated_ok")),
                "cover_strategy_reason": a.get("skip_reason", vt.get("image_strategy_reason", "")),
                "reference_search_queries": a.get("reference_search_queries", vt.get("reference_search_queries", [])),
                "cover_generation_state": a.get("engine", ""),
                "material_workflow": a.get("material_workflow", vt.get("material_workflow", "")),
                "cover_layout_brief": a.get("cover_layout_brief", vt.get("cover_layout_brief", "")),
                "source_priority": a.get("source_priority", vt.get("source_priority", [])),
                "manual_asset_checklist": a.get("manual_asset_checklist", vt.get("manual_asset_checklist", [])),
                "material_slots": a.get("material_slots", vt.get("material_slots", [])),
                "source_priority_text": join_lines(a.get("source_priority", vt.get("source_priority", []))),
                "manual_asset_checklist_text": join_lines(a.get("manual_asset_checklist", vt.get("manual_asset_checklist", []))),
                "material_slots_text": material_slots_text(a.get("material_slots", vt.get("material_slots", []))),
                "real_image_entrypoints": a.get("real_image_entrypoints", []),
                "real_image_candidates": a.get("real_image_candidates", []),
                "real_image_slot_plan": a.get("real_image_slot_plan", []),
                "real_image_provider_mode": a.get("real_image_provider_mode", ""),
                "real_image_errors": a.get("real_image_errors", []),
                "real_image_entrypoints_text": reference_links_text(a.get("real_image_entrypoints", [])),
                "real_image_candidates_text": reference_candidates_text(a.get("real_image_candidates", [])),
                "tts_file": tts_files.get(platform, ""),
            }
        )
    items.sort(key=lambda x: (x["manual_publish_priority"], -x["score"]))
    return items


def queue_summary(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "total_items": len(items),
        "ready_items": sum(1 for x in items if x.get("pass")),
        "top_priority_platforms": [x["platform"] for x in items[:3]],
    }


def build_markdown(queue: Dict[str, Any]) -> str:
    lines = [
        "# 今日手动发布队列",
        "",
        f"- 生成时间：{queue['generated_at']}",
        f"- 内容包：`{queue['source_pack']}`",
        f"- 可手动发布条数：`{queue['summary']['ready_items']}/{queue['summary']['total_items']}`",
        "",
        "## 建议顺序",
        "",
    ]
    for idx, item in enumerate(queue["items"], start=1):
        status = "READY" if item.get("pass") else "HOLD"
        lines.extend(
            [
                f"### {idx}. {item['platform']} [{status}]",
                f"- 标题：{item['title']}",
                f"- 分数：{item['score']}",
                f"- 目标：{item['primary_goal']}",
                f"- 建议发布时间段：{', '.join(item.get('publish_windows', []))}",
                f"- 建议日发布量：{item.get('recommended_publish_per_day')}",
                f"- 封面：`{item.get('cover_file', '')}`",
                f"- 图片策略：`{item.get('cover_strategy', '')}`",
                f"- 策略说明：{item.get('cover_strategy_reason', '')}",
                f"- 素材工作流：`{item.get('material_workflow', '')}`",
                f"- 图位建议：{item.get('cover_layout_brief', '')}",
                f"- 素材来源优先级：{', '.join(item.get('source_priority', []))}",
                f"- 参考搜图词：{', '.join(item.get('reference_search_queries', []))}",
                f"- 真实图抓取模式：{item.get('real_image_provider_mode', '')}",
                "- 素材清单：",
                item.get("material_slots_text", "当前没有额外图位建议。"),
                "- 真实图直达入口：",
                item.get("real_image_entrypoints_text", "当前没有直达入口。"),
                "- 自动抽取的页面预览图候选：",
                item.get("real_image_candidates_text", "当前没有自动抽到的页面预览图候选。"),
                "- 素材检查清单：",
                item.get("manual_asset_checklist_text", "当前没有额外检查清单。"),
                f"- TTS：`{item.get('tts_file', 'N/A')}`",
                f"- 操作提示：{item.get('notes', '')}",
                "- 手动发布动作：打开对应平台 -> 复制标题/正文/标签 -> 上传封面/视频 -> 发布后回填数据",
                "",
            ]
        )
    lines.extend(
        [
            "## 发布后回填",
            "",
            "- 当天 23:00 后回填首轮数据",
            "- 次日同一时间回填 24h 数据",
            "- 建议至少回填：曝光、阅读/播放、点赞、评论、收藏、转发、主页点击、商品点击、收益",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-pack", required=True)
    ap.add_argument("--input-quality", required=True)
    ap.add_argument("--input-assets", required=True)
    ap.add_argument("--tts-dir", required=True)
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    ap.add_argument("--generated-at", required=True)
    ap.add_argument("--latest-json")
    ap.add_argument("--latest-md")
    args = ap.parse_args()

    pack = load_json(Path(args.input_pack))
    quality = load_json(Path(args.input_quality))
    assets = load_json_optional(args.input_assets)
    items = pick_manual_publish_items(pack, quality, assets, tts_map(Path(args.tts_dir)))
    queue = {"generated_at": args.generated_at, "source_pack": args.input_pack, "summary": queue_summary(items), "items": items}
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(build_markdown(queue), encoding="utf-8")
    if args.latest_json:
        latest_json = Path(args.latest_json)
        latest_json.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_json, latest_json)
    if args.latest_md:
        latest_md = Path(args.latest_md)
        latest_md.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_md, latest_md)
    print(json.dumps({"output_json": args.output_json, "output_md": args.output_md}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
