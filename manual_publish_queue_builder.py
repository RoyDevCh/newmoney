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


def pick_manual_publish_items(pack: Dict[str, Any], quality: Dict[str, Any], manifest: Dict[str, Any], tts_files: Dict[str, str]) -> List[Dict[str, Any]]:
    strategies = build_strategy_matrix()
    qmap = quality_map(quality)
    amap = asset_map(manifest)
    items: List[Dict[str, Any]] = []
    for draft in pack.get("drafts", []):
        if not isinstance(draft, dict):
            continue
        platform = str(draft.get("platform", "")).strip()
        strategy = strategies.get(platform, {})
        q = qmap.get(platform, {})
        a = amap.get(platform, {})
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
    assets = load_json(Path(args.input_assets))
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
