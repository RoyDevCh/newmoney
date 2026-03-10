#!/usr/bin/env python3
"""Vertical topic focus and rotation rules for content production."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from content_novelty_policy import score_topic_novelty


ZH = "知乎"
XHS = "小红书"
DY = "抖音"
XG = "西瓜视频"
BILI = "B站"
WB = "微博"
WX = "公众号"
TT = "头条"

ROOT = Path.home() / ".openclaw"
WS_CONTENT = ROOT / "workspace-content"
ROTATION_STATE = WS_CONTENT / "topic_rotation_state.json"

PRIMARY_VERTICAL = "科技消费"
PRIMARY_AUDIENCE = "关注智能家居、智能穿戴、数码设备、网络服务与汽车智能化的高决策成本消费用户"

TOPIC_POOL: List[Dict[str, Any]] = [
    {
        "query": "2026 扫地机器人推荐与预算分段选购指南",
        "priority": 1.0,
        "lane": PRIMARY_VERTICAL,
        "sublane": "智能家居",
        "product_family": "扫地机器人",
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX, TT, WB],
        "video_derivatives": [BILI, XG],
        "article_style": "搜索流量型选购指南",
    },
    {
        "query": "2026 洗地机选购避坑与家庭场景推荐",
        "priority": 0.99,
        "lane": PRIMARY_VERTICAL,
        "sublane": "智能家居",
        "product_family": "洗地机",
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX, TT, WB],
        "video_derivatives": [BILI, XG],
        "article_style": "搜索流量型选购指南",
    },
    {
        "query": "2026 智能门锁怎么选：不同家庭场景安装与避坑指南",
        "priority": 0.985,
        "lane": PRIMARY_VERTICAL,
        "sublane": "智能家居",
        "product_family": "智能门锁",
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX, TT, WB],
        "video_derivatives": [BILI, XG],
        "article_style": "场景导向型决策文",
    },
    {
        "query": "2026 路由器推荐：租房、小户型、大户型分别怎么选",
        "priority": 0.98,
        "lane": PRIMARY_VERTICAL,
        "sublane": "数码网络",
        "product_family": "路由器",
        "fit_platforms": [ZH, DY, XG, BILI, WX, TT, WB],
        "video_derivatives": [BILI, XG],
        "article_style": "预算与场景分层选购文",
    },
    {
        "query": "2026 开放式耳机推荐：通勤、运动、办公分别怎么选",
        "priority": 0.975,
        "lane": PRIMARY_VERTICAL,
        "sublane": "智能穿戴",
        "product_family": "开放式耳机",
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX, WB, TT],
        "video_derivatives": [BILI, XG],
        "article_style": "品类教育 + 型号推荐",
    },
    {
        "query": "2026 智能手表怎么选：苹果、华为、佳明不同人群购买建议",
        "priority": 0.972,
        "lane": PRIMARY_VERTICAL,
        "sublane": "智能穿戴",
        "product_family": "智能手表",
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX, WB, TT],
        "video_derivatives": [BILI, XG],
        "article_style": "品牌分层型选购文",
    },
    {
        "query": "Apple Watch Series 11 值不值得买：公开资料、媒体上手与首批反馈汇总",
        "priority": 0.969,
        "lane": PRIMARY_VERTICAL,
        "sublane": "智能穿戴",
        "product_family": "智能手表",
        "fit_platforms": [ZH, WX, WB, XG, BILI],
        "video_derivatives": [BILI, XG],
        "article_style": "单品评测汇总",
    },
    {
        "query": "2026 行车记录仪推荐与安装避坑：新手司机怎么选",
        "priority": 0.968,
        "lane": PRIMARY_VERTICAL,
        "sublane": "汽车智能化",
        "product_family": "行车记录仪",
        "fit_platforms": [ZH, DY, XG, BILI, WX, TT, WB],
        "video_derivatives": [BILI, XG],
        "article_style": "场景刚需型选购文",
    },
    {
        "query": "2026 家用充电桩选购与安装流程避坑指南",
        "priority": 0.962,
        "lane": PRIMARY_VERTICAL,
        "sublane": "汽车智能化",
        "product_family": "家用充电桩",
        "fit_platforms": [ZH, DY, XG, BILI, WX, TT],
        "video_derivatives": [BILI, XG],
        "article_style": "流程说明 + 决策建议",
    },
    {
        "query": "2026 智能投影仪推荐：客厅、卧室、租房场景怎么选",
        "priority": 0.958,
        "lane": PRIMARY_VERTICAL,
        "sublane": "家庭影音",
        "product_family": "投影仪",
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX, TT, WB],
        "video_derivatives": [BILI, XG],
        "article_style": "场景分层型选购文",
    },
    {
        "query": "华为路由 X1 值不值得买：官方信息、媒体上手与家庭场景判断",
        "priority": 0.956,
        "lane": PRIMARY_VERTICAL,
        "sublane": "数码网络",
        "product_family": "路由器",
        "fit_platforms": [ZH, WX, WB, XG, BILI],
        "video_derivatives": [BILI, XG],
        "article_style": "单品评测汇总",
    },
    {
        "query": "2026 空气净化器怎么选：过敏家庭和养宠家庭重点看什么",
        "priority": 0.952,
        "lane": PRIMARY_VERTICAL,
        "sublane": "智能家居",
        "product_family": "空气净化器",
        "fit_platforms": [ZH, XHS, DY, XG, BILI, WX, TT],
        "video_derivatives": [BILI, XG],
        "article_style": "需求场景型选购文",
    },
]


def _default_state() -> Dict[str, Any]:
    return {"recent_topics": [], "last_selected_at": ""}


def load_rotation_state() -> Dict[str, Any]:
    if not ROTATION_STATE.exists():
        return _default_state()
    try:
        return json.loads(ROTATION_STATE.read_text(encoding="utf-8-sig"))
    except Exception:
        return _default_state()


def save_rotation_state(state: Dict[str, Any]) -> None:
    ROTATION_STATE.parent.mkdir(parents=True, exist_ok=True)
    ROTATION_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _recent_rows(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = state.get("recent_topics", [])
    return [row for row in rows if isinstance(row, dict)]


def score_topic_rotation(candidate: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    product_family = str(candidate.get("product_family", "")).strip()
    sublane = str(candidate.get("sublane", "")).strip()
    recent = _recent_rows(state)[:6]
    score = float(candidate.get("priority", 0.0))
    reasons: List[str] = []

    if recent:
        last = recent[0]
        if product_family and product_family == str(last.get("product_family", "")).strip():
            score -= 0.42
            reasons.append("与上一次同一产品族，强制大幅降权")
        if sublane and sublane == str(last.get("sublane", "")).strip():
            score -= 0.12
            reasons.append("与上一次同一子赛道，轻度降权")

    for idx, row in enumerate(recent[:3], start=1):
        if product_family and product_family == str(row.get("product_family", "")).strip():
            score -= 0.10 / idx
            reasons.append(f"最近 {idx} 次出现过同类产品，继续降权")
        if sublane and sublane == str(row.get("sublane", "")).strip():
            score -= 0.05 / idx
            reasons.append(f"最近 {idx} 次出现过同子赛道，保持轮换")

    if candidate.get("video_derivatives"):
        score += 0.03
        reasons.append("长文可直接复用成长视频母体，加分")

    return {
        **candidate,
        "rotation_score": round(score, 4),
        "rotation_reasons": reasons or ["默认得分"],
    }


def pick_next_topic() -> Dict[str, Any]:
    state = load_rotation_state()
    scored = []
    for candidate in TOPIC_POOL:
        row = score_topic_rotation(candidate, state)
        row = score_topic_novelty(row)
        row["rotation_score"] = round(float(row.get("rotation_score", 0.0)) + float(row.get("novelty_score", 0.0)), 4)
        scored.append(row)
    scored.sort(key=lambda row: float(row.get("rotation_score", 0.0)), reverse=True)
    chosen = dict(scored[0]) if scored else {}
    chosen["primary_vertical"] = PRIMARY_VERTICAL
    chosen["primary_audience"] = PRIMARY_AUDIENCE
    chosen["cross_format_plan"] = {
        "long_article": True,
        "xigua_long_video": XG in chosen.get("video_derivatives", []),
        "bilibili_long_video": BILI in chosen.get("video_derivatives", []),
    }
    return chosen


def record_selected_topic(topic_info: Dict[str, Any], selected_at: str) -> None:
    state = load_rotation_state()
    recent = _recent_rows(state)
    recent.insert(
        0,
        {
            "query": str(topic_info.get("query", "")).strip(),
            "lane": str(topic_info.get("lane", "")).strip(),
            "sublane": str(topic_info.get("sublane", "")).strip(),
            "product_family": str(topic_info.get("product_family", "")).strip(),
            "selected_at": selected_at,
        },
    )
    state["recent_topics"] = recent[:12]
    state["last_selected_at"] = selected_at
    save_rotation_state(state)
