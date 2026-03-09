#!/usr/bin/env python3
"""Ingest platform metrics and generate structured optimization directives."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


EXPECTED_COLUMNS = [
    "date",
    "platform",
    "content_id",
    "title",
    "impressions",
    "views",
    "likes",
    "comments",
    "favorites",
    "shares",
    "follows",
    "profile_clicks",
    "product_clicks",
    "revenue",
    "avg_watch_sec",
    "read_complete_rate",
]


def load_rows(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        raise ValueError("JSON metrics input must be a list of objects")

    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(dict(row))
    return rows


def fnum(value: Any) -> float:
    try:
        if value in ("", None):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def platform_rollup(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("platform", "")).strip()].append(row)

    summary: Dict[str, Any] = {}
    for platform, items in grouped.items():
        impressions = sum(fnum(x.get("impressions")) for x in items)
        views = sum(fnum(x.get("views")) for x in items)
        likes = sum(fnum(x.get("likes")) for x in items)
        comments = sum(fnum(x.get("comments")) for x in items)
        favorites = sum(fnum(x.get("favorites")) for x in items)
        shares = sum(fnum(x.get("shares")) for x in items)
        follows = sum(fnum(x.get("follows")) for x in items)
        profile_clicks = sum(fnum(x.get("profile_clicks")) for x in items)
        product_clicks = sum(fnum(x.get("product_clicks")) for x in items)
        revenue = sum(fnum(x.get("revenue")) for x in items)
        avg_watch = sum(fnum(x.get("avg_watch_sec")) for x in items) / max(len(items), 1)
        avg_complete = sum(fnum(x.get("read_complete_rate")) for x in items) / max(len(items), 1)

        summary[platform] = {
            "posts": len(items),
            "impressions": impressions,
            "views": views,
            "likes": likes,
            "comments": comments,
            "favorites": favorites,
            "shares": shares,
            "follows": follows,
            "profile_clicks": profile_clicks,
            "product_clicks": product_clicks,
            "revenue": revenue,
            "avg_watch_sec": round(avg_watch, 2),
            "read_complete_rate": round(avg_complete, 4),
            "engagement_rate": round((likes + comments + favorites + shares) / max(views, 1.0), 4),
            "follow_rate": round(follows / max(views, 1.0), 4),
            "profile_ctr": round(profile_clicks / max(views, 1.0), 4),
            "product_ctr": round(product_clicks / max(views, 1.0), 4),
        }
    return summary


def build_directives(platform: str, row: Dict[str, Any]) -> Dict[str, Any]:
    directives: List[str] = []
    experiments: List[str] = []
    overrides: Dict[str, Any] = {
        "prefer_checklist": False,
        "raise_specificity": False,
        "raise_depth": False,
        "tighten_cta": False,
        "raise_visual_clarity": False,
    }

    if row["engagement_rate"] < 0.035:
        directives.append("标题和前50字需要更强的冲突点或错误纠正感。")
        overrides["raise_specificity"] = True
        experiments.append("下个周期优先改标题和Hook，不改主体框架。")

    if row["follow_rate"] < 0.006:
        directives.append("关注承接偏弱，CTA要收敛成单动作，不要同时引导主页、评论和链接。")
        overrides["tighten_cta"] = True
        experiments.append("下个周期统一改成单一资料入口或单一评论关键词。")

    if row["favorites"] > row["likes"] * 1.3:
        directives.append("收藏信号高，继续做清单、模板、对照表和步骤化内容。")
        overrides["prefer_checklist"] = True
        experiments.append("增加收藏型标题和对照表格式。")

    if row["read_complete_rate"] and row["read_complete_rate"] < 0.2:
        directives.append("正文读完率偏低，需要更短段落、更清晰的小标题和更早的结论。")
        overrides["raise_depth"] = True
        experiments.append("将长文改成结论-误区-步骤-案例四段结构。")

    if row["avg_watch_sec"] and row["avg_watch_sec"] < 12:
        directives.append("前屏停留偏弱，首屏视觉和第一句要更直接。")
        overrides["raise_visual_clarity"] = True

    if row["revenue"] <= 0 and row["views"] > 0:
        directives.append("已有流量但承接不足，优先优化资料包、商品卡和清单型落地页。")
        overrides["tighten_cta"] = True

    if not directives:
        directives.append("当前数据稳定，保持结构，只做轻量A/B测试。")
        experiments.append("保留现有框架，只迭代标题和封面。")

    return {
        "platform": platform,
        "notes": directives,
        "directives": directives,
        "next_experiments": experiments or ["保持当前节奏，轻量测试标题与封面。"],
        "strategy_override": overrides,
    }


def suggestions(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [build_directives(platform, row) for platform, row in summary.items()]


def strategy_overrides(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for row in rows:
        platform = str(row.get("platform", "")).strip()
        if platform:
            output[platform] = row.get("strategy_override", {})
    return output


def build_markdown(summary: Dict[str, Any], advice_rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# 每日数据回灌分析",
        "",
        "## 平台汇总",
        "",
    ]
    for platform, row in summary.items():
        lines.extend(
            [
                f"### {platform}",
                f"- 发布数：{row['posts']}",
                f"- 播放/阅读：{int(row['views'])}",
                f"- 互动率：{row['engagement_rate']}",
                f"- 涨粉率：{row['follow_rate']}",
                f"- 主页点击率：{row['profile_ctr']}",
                f"- 商品点击率：{row['product_ctr']}",
                f"- 完读/完播率：{row['read_complete_rate']}",
                f"- 平均停留/观看秒数：{row['avg_watch_sec']}",
                f"- 收益：{row['revenue']}",
                "",
            ]
        )

    lines.append("## 自动优化建议")
    lines.append("")
    for row in advice_rows:
        lines.append(f"### {row['platform']}")
        for note in row["directives"]:
            lines.append(f"- {note}")
        for experiment in row["next_experiments"]:
            lines.append(f"- 下个测试：{experiment}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--latest-json")
    parser.add_argument("--latest-md")
    args = parser.parse_args()

    rows = load_rows(Path(args.input))
    summary = platform_rollup(rows)
    advice = suggestions(summary)
    payload = {
        "input": args.input,
        "expected_columns": EXPECTED_COLUMNS,
        "platform_summary": summary,
        "suggestions": advice,
        "strategy_overrides": strategy_overrides(advice),
    }

    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(build_markdown(summary, advice), encoding="utf-8")

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
