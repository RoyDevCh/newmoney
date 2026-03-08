#!/usr/bin/env python3
"""Ingest daily platform metrics and generate optimization suggestions."""

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
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
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
        posts = len(items)
        summary[platform] = {
            "posts": posts,
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
            "engagement_rate": round((likes + comments + favorites + shares) / max(views, 1.0), 4),
            "follow_rate": round(follows / max(views, 1.0), 4),
            "profile_ctr": round(profile_clicks / max(views, 1.0), 4),
            "product_ctr": round(product_clicks / max(views, 1.0), 4),
        }
    return summary


def suggestions(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for platform, row in summary.items():
        notes: List[str] = []
        if row["engagement_rate"] < 0.03:
            notes.append("标题和 hook 需要更强，优先重写前 50 字和封面。")
        if row["follow_rate"] < 0.005:
            notes.append("涨粉承接偏弱，CTA 需要更明确，简介区和主页入口要统一。")
        if row["product_ctr"] < 0.01 and row["profile_ctr"] > 0.02:
            notes.append("内容能拉点击但带货承接弱，优先优化商品清单或落地页。")
        if row["favorites"] > row["likes"] * 1.5:
            notes.append("收藏驱动强，适合继续做清单、模板、资料包。")
        if row["revenue"] <= 0 and row["views"] > 0:
            notes.append("已经开始有流量但还没变现，优先补 CTA、资料包和商品卡承接。")
        output.append({"platform": platform, "notes": notes or ["数据正常，继续按当前节奏迭代。"]})
    return output


def build_markdown(summary: Dict[str, Any], suggestions_rows: List[Dict[str, Any]]) -> str:
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
                f"- 收益：{row['revenue']}",
                "",
            ]
        )
    lines.append("## 优化建议")
    lines.append("")
    for row in suggestions_rows:
        lines.append(f"### {row['platform']}")
        for note in row["notes"]:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    ap.add_argument("--latest-json")
    ap.add_argument("--latest-md")
    args = ap.parse_args()

    rows = load_rows(Path(args.input))
    summary = platform_rollup(rows)
    advice = suggestions(summary)
    payload = {
        "input": args.input,
        "expected_columns": EXPECTED_COLUMNS,
        "platform_summary": summary,
        "suggestions": advice,
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
