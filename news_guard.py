#!/usr/bin/env python3
"""News freshness and credibility guard with fallback search sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
import xml.etree.ElementTree as ET

import requests

from local_search_client import search_bing_rss, search_local_searxng


TRUSTED_DOMAINS = {
    "openai.com",
    "thepaper.cn",
    "xinhuanet.com",
    "36kr.com",
    "zhihu.com",
    "qq.com",
    "163.com",
    "gov.cn",
    "nature.com",
    "arxiv.org",
    "reuters.com",
    "bloomberg.com",
    "bbc.com",
}

SUSPICIOUS_WORDS = {
    "震惊",
    "内部消息",
    "听说",
    "未证实",
    "爆料",
    "100%",
    "保真",
    "天价",
}


@dataclass
class NewsCheckResult:
    query: str
    confidence: float
    is_publishable: bool
    reasons: List[str]
    trusted_hits: int
    recent_hits: int
    sampled_titles: List[str]
    source: str = ""


def _domain_from_url(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _unwrap_bing_url(url: str) -> str:
    try:
        q = parse_qs(urlparse(url).query)
        target = q.get("url", [""])[0]
        if target:
            return unquote(target)
    except Exception:
        pass
    return url


def _parse_time(value: str):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def fetch_news_searxng(searxng_url: str, query: str, limit: int = 12) -> List[Dict]:
    try:
        primary = search_local_searxng(
            query,
            categories="news",
            language="zh-CN",
            limit=limit,
            time_range="day",
            base_url=searxng_url.rstrip('/'),
            timeout_sec=20,
        )
        rows = primary.get("results", [])
        if rows:
            return rows
        fallback = search_local_searxng(
            query,
            categories="general",
            language="zh-CN",
            limit=limit,
            time_range="month",
            base_url=searxng_url.rstrip('/'),
            timeout_sec=20,
        )
        rows = fallback.get("results", [])
        if rows:
            return rows
    except Exception:
        pass
    fallback_bing = search_bing_rss(query, limit=limit)
    return fallback_bing.get("results", [])


def fetch_news_bing_rss(query: str, limit: int = 12) -> List[Dict]:
    url = f"https://www.bing.com/news/search?q={quote_plus(query)}&format=rss"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    items = []
    for item in root.findall("./channel/item")[:limit]:
        raw_link = (item.findtext("link") or "").strip()
        link = _unwrap_bing_url(raw_link)
        items.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "url": link,
                "publishedDate": (item.findtext("pubDate") or "").strip(),
                "content": (item.findtext("description") or "").strip(),
            }
        )
    return items


def fetch_news(searxng_url: str, query: str, limit: int = 12) -> tuple[list[dict], str]:
    try:
        return fetch_news_searxng(searxng_url, query, limit), "searxng"
    except Exception:
        pass
    return fetch_news_bing_rss(query, limit), "bing_rss"


def evaluate_news(query: str, items: List[Dict], now: datetime | None = None) -> NewsCheckResult:
    now = now or datetime.now(timezone.utc)
    recent_window = now - timedelta(hours=72)

    trusted_domains = set()
    recent_hits = 0
    reasons: List[str] = []
    sampled_titles: List[str] = []
    suspicious_hits = 0

    for item in items:
        title = str(item.get("title", "")).strip()
        if title:
            sampled_titles.append(title[:120])
        url = str(item.get("url", "")).strip()
        domain = _domain_from_url(url)
        if any(domain == d or domain.endswith(f".{d}") for d in TRUSTED_DOMAINS):
            trusted_domains.add(domain)

        pub_raw = item.get("publishedDate") or item.get("published_date") or item.get("date")
        pub_dt = _parse_time(str(pub_raw))
        if pub_dt and pub_dt >= recent_window:
            recent_hits += 1

        lowered = (title + " " + str(item.get("content", ""))).lower()
        if any(w.lower() in lowered for w in SUSPICIOUS_WORDS):
            suspicious_hits += 1

    trusted_hits = len(trusted_domains)
    confidence = 0.0
    confidence += min(trusted_hits / 3.0, 1.0) * 0.55
    confidence += min(recent_hits / max(len(items), 1), 1.0) * 0.30
    confidence -= min(suspicious_hits / max(len(items), 1), 1.0) * 0.25
    confidence = max(0.0, min(confidence, 1.0))

    if trusted_hits < 2:
        reasons.append("trusted_sources_lt_2")
    if recent_hits == 0:
        reasons.append("no_recent_item_72h")
    if suspicious_hits > max(1, len(items) // 4):
        reasons.append("too_many_suspicious_markers")

    is_publishable = confidence >= 0.65 and trusted_hits >= 2 and recent_hits >= 1
    if not is_publishable and not reasons:
        reasons.append("confidence_below_threshold")

    return NewsCheckResult(
        query=query,
        confidence=round(confidence, 4),
        is_publishable=is_publishable,
        reasons=reasons,
        trusted_hits=trusted_hits,
        recent_hits=recent_hits,
        sampled_titles=sampled_titles[:6],
    )


def check_topic(searxng_url: str, query: str) -> NewsCheckResult:
    items, source = fetch_news(searxng_url, query)
    result = evaluate_news(query=query, items=items)
    result.source = source
    return result


if __name__ == "__main__":
    import json
    import sys

    q = " ".join(sys.argv[1:]).strip() or "OpenAI 最新发布"
    result = check_topic("http://127.0.0.1:8080", q)
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
