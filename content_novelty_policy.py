#!/usr/bin/env python3
"""Novelty and cooldown policy for repeated content suppression."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path.home() / ".openclaw"
WS_CONTENT = ROOT / "workspace-content"
NOVELTY_STATE = WS_CONTENT / "content_novelty_history.json"


def _default_state() -> Dict[str, Any]:
    return {"items": [], "last_updated_at": ""}


def load_novelty_state() -> Dict[str, Any]:
    if not NOVELTY_STATE.exists():
        return _default_state()
    try:
        data = json.loads(NOVELTY_STATE.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and isinstance(data.get("items", []), list):
            return data
    except Exception:
        pass
    return _default_state()


def save_novelty_state(state: Dict[str, Any]) -> None:
    NOVELTY_STATE.parent.mkdir(parents=True, exist_ok=True)
    NOVELTY_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _norm(text: str) -> str:
    current = str(text or "").strip().lower()
    current = re.sub(r"[^\w\u4e00-\u9fff]+", " ", current)
    current = re.sub(r"\s+", " ", current).strip()
    return current


def _tokens(text: str) -> List[str]:
    current = _norm(text)
    chunks = [x for x in re.split(r"\s+", current) if len(x) >= 2]
    seen: List[str] = []
    for chunk in chunks:
        if chunk not in seen:
            seen.append(chunk)
    return seen


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa = set(a)
    sb = set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _parse_time(value: str) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        return None


def _recent_items(state: Dict[str, Any], days: int = 45) -> List[Dict[str, Any]]:
    cutoff = datetime.now() - timedelta(days=days)
    rows: List[Dict[str, Any]] = []
    for row in state.get("items", []):
        if not isinstance(row, dict):
            continue
        dt = _parse_time(str(row.get("generated_at", "")))
        if dt and dt >= cutoff:
            rows.append(row)
    return rows


def score_topic_novelty(candidate: Dict[str, Any], state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state = state or load_novelty_state()
    items = _recent_items(state, days=45)
    query = str(candidate.get("query", "")).strip()
    lane = str(candidate.get("lane", "")).strip()
    sublane = str(candidate.get("sublane", "")).strip()
    family = str(candidate.get("product_family", "")).strip()
    score = 0.0
    reasons: List[str] = []
    query_tokens = _tokens(query)

    for idx, row in enumerate(items[:24], start=1):
        if family and family == str(row.get("product_family", "")).strip():
            score -= 0.22 / min(idx, 4)
            reasons.append(f"最近内容已覆盖 {family}，进入冷却")
        if sublane and sublane == str(row.get("sublane", "")).strip():
            score -= 0.10 / min(idx, 4)
            reasons.append(f"最近内容已覆盖同子赛道 {sublane}")
        if lane and lane == str(row.get("lane", "")).strip():
            score -= 0.03 / min(idx, 5)
        row_tokens = _tokens(str(row.get("topic", "")))
        sim = _jaccard(query_tokens, row_tokens)
        if sim >= 0.65:
            score -= 0.18 / min(idx, 4)
            reasons.append("最近已有高相似选题")
    return {
        **candidate,
        "novelty_score": round(score, 4),
        "novelty_reasons": reasons[:6],
    }


def build_platform_novelty_context(platform: str, state: Dict[str, Any] | None = None, limit: int = 8) -> Dict[str, Any]:
    state = state or load_novelty_state()
    rows = [row for row in _recent_items(state, days=30) if str(row.get("platform", "")).strip() == str(platform or "").strip()]
    titles: List[str] = []
    topics: List[str] = []
    for row in rows:
        title = str(row.get("title", "")).strip()
        topic = str(row.get("topic", "")).strip()
        if title and title not in titles:
            titles.append(title)
        if topic and topic not in topics:
            topics.append(topic)
    return {
        "recent_titles": titles[:limit],
        "recent_topics": topics[:limit],
    }


def build_global_novelty_context(state: Dict[str, Any] | None = None, limit: int = 12) -> Dict[str, Any]:
    state = state or load_novelty_state()
    rows = _recent_items(state, days=30)
    topics: List[str] = []
    families: List[str] = []
    for row in rows:
        topic = str(row.get("topic", "")).strip()
        family = str(row.get("product_family", "")).strip()
        if topic and topic not in topics:
            topics.append(topic)
        if family and family not in families:
            families.append(family)
    return {"recent_topics": topics[:limit], "recent_families": families[:limit]}


def record_generated_pack(
    payload: Dict[str, Any],
    generated_at: str,
    topic_info: Dict[str, Any] | None = None,
    state: Dict[str, Any] | None = None,
) -> None:
    state = state or load_novelty_state()
    items = list(state.get("items", []))
    topic = str(payload.get("topic", "")).strip()
    topic_info = topic_info or {}
    for draft in payload.get("drafts", []):
        if not isinstance(draft, dict):
            continue
        items.insert(
            0,
            {
                "generated_at": generated_at,
                "topic": topic,
                "platform": str(draft.get("platform", "")).strip(),
                "title": str(draft.get("title", "")).strip(),
                "lane": str(topic_info.get("lane", "")).strip(),
                "sublane": str(topic_info.get("sublane", "")).strip(),
                "product_family": str(topic_info.get("product_family", "")).strip(),
            },
        )
    state["items"] = items[:300]
    state["last_updated_at"] = generated_at
    save_novelty_state(state)
