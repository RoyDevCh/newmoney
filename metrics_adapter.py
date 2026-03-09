#!/usr/bin/env python3
"""Normalize platform export files into the shared metrics schema."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List, Tuple


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


ALIASES = {
    "date": ["date", "日期", "发布时间", "publish_date"],
    "platform": ["platform", "平台", "source_platform"],
    "content_id": ["content_id", "作品id", "内容id", "post_id", "item_id", "id"],
    "title": ["title", "标题", "内容标题", "post_title"],
    "impressions": ["impressions", "曝光", "展示量", "impression", "shows"],
    "views": ["views", "播放", "阅读", "阅读量", "播放量", "view_count"],
    "likes": ["likes", "点赞", "赞"],
    "comments": ["comments", "评论", "评论数"],
    "favorites": ["favorites", "收藏", "收藏数", "fav"],
    "shares": ["shares", "转发", "分享", "分享数"],
    "follows": ["follows", "新增粉丝", "涨粉", "follow_gain"],
    "profile_clicks": ["profile_clicks", "主页点击", "主页访问", "主页访问量"],
    "product_clicks": ["product_clicks", "商品点击", "链接点击", "卡片点击", "私信点击"],
    "revenue": ["revenue", "收益", "成交金额", "gmv", "sales"],
    "avg_watch_sec": ["avg_watch_sec", "平均观看时长", "平均停留时长", "avg_duration"],
    "read_complete_rate": ["read_complete_rate", "完读率", "完播率", "complete_rate"],
}


def _normalize_key(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "").replace("_", "")


NORMALIZED_ALIAS = {
    canonical: {_normalize_key(canonical), *(_normalize_key(alias) for alias in aliases)}
    for canonical, aliases in ALIASES.items()
}


def _load_rows(filename: str, payload: bytes) -> List[Dict[str, Any]]:
    text = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "utf-16"):
        try:
            text = payload.decode(encoding)
            break
        except Exception:
            continue
    if text is None:
        text = payload.decode("utf-8-sig", errors="replace")

    if filename.lower().endswith(".json"):
        data = json.loads(text)
        if isinstance(data, dict):
            if isinstance(data.get("rows"), list):
                return [row for row in data["rows"] if isinstance(row, dict)]
            if isinstance(data.get("data"), list):
                return [row for row in data["data"] if isinstance(row, dict)]
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        raise ValueError("JSON input must be a list or contain a data/rows list")

    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def adapt_metrics_payload(filename: str, payload: bytes, default_platform: str = "") -> Tuple[bytes, Dict[str, Any]]:
    rows = _load_rows(filename, payload)
    adapted: List[Dict[str, Any]] = []
    matched_columns: Dict[str, str] = {}

    for row in rows:
        adapted_row: Dict[str, Any] = {}
        source_map = {_normalize_key(k): v for k, v in row.items()}
        for canonical in EXPECTED_COLUMNS:
            value = ""
            for alias in NORMALIZED_ALIAS[canonical]:
                if alias in source_map:
                    value = source_map[alias]
                    matched_columns.setdefault(canonical, alias)
                    break
            adapted_row[canonical] = value
        if default_platform and not str(adapted_row["platform"]).strip():
            adapted_row["platform"] = default_platform
        adapted.append(adapted_row)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPECTED_COLUMNS)
    writer.writeheader()
    writer.writerows(adapted)
    summary = {
        "rows_in": len(rows),
        "rows_out": len(adapted),
        "matched_columns": matched_columns,
        "missing_columns": [col for col in EXPECTED_COLUMNS if col not in matched_columns and col != "platform"],
    }
    return output.getvalue().encode("utf-8"), summary
