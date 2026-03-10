#!/usr/bin/env python3
"""Shared local and fallback search clients for topic validation and research collection."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import requests


DEFAULT_LOCAL_SEARCH_URL = os.getenv("OPENCLAW_LOCAL_SEARCH_URL", "http://127.0.0.1:8080").rstrip("/")
DEFAULT_TIMEOUT_SEC = 12
BING_SEARCH_URL = "https://www.bing.com/search"


def normalize_result_rows(data: Any, query: str, limit: int = 8) -> List[Dict[str, Any]]:
    if isinstance(data, dict):
        candidates = data.get("results", [])
    elif isinstance(data, list):
        candidates = data
    else:
        candidates = []

    rows: List[Dict[str, Any]] = []
    for item in candidates[:limit]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "") or item.get("href", "")).strip()
        snippet = str(item.get("content", "") or item.get("body", "")).strip()
        if not title and not snippet:
            continue
        rows.append(
            {
                "query": query,
                "title": title[:160],
                "url": url[:280],
                "snippet": snippet[:260],
                "published": str(
                    item.get("publishedDate", "") or item.get("published_date", "") or item.get("date", "")
                ).strip(),
                "engine": str(item.get("engine", "")).strip(),
                "category": str(item.get("category", "")).strip(),
            }
        )
    return rows


def search_local_searxng(
    query: str,
    *,
    categories: str = "general",
    language: str = "zh-CN",
    limit: int = 8,
    time_range: Optional[str] = None,
    base_url: str = DEFAULT_LOCAL_SEARCH_URL,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "q": query,
        "format": "json",
        "categories": categories,
        "language": language,
        "limit": limit,
    }
    if time_range:
        params["time_range"] = time_range

    response = requests.get(f"{base_url}/search", params=params, timeout=timeout_sec)
    response.raise_for_status()
    payload = response.json()
    return {
        "ok": True,
        "base_url": base_url,
        "categories": categories,
        "query": query,
        "results": normalize_result_rows(payload, query=query, limit=limit),
        "raw_count": len(payload.get("results", [])) if isinstance(payload, dict) else 0,
    }


def local_search_health(base_url: str = DEFAULT_LOCAL_SEARCH_URL, timeout_sec: int = 4) -> Dict[str, Any]:
    try:
        response = requests.get(
            f"{base_url}/search",
            params={"q": "test", "format": "json", "limit": 1},
            timeout=timeout_sec,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            "ok": True,
            "base_url": base_url,
            "result_count": len(payload.get("results", [])) if isinstance(payload, dict) else 0,
        }
    except Exception as exc:
        return {
            "ok": False,
            "base_url": base_url,
            "error": str(exc),
        }


def search_bing_rss(
    query: str,
    *,
    limit: int = 8,
    language: str = "zh-CN",
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "q": query,
        "format": "rss",
        "setlang": language,
    }
    response = requests.get(
        BING_SEARCH_URL,
        params=params,
        timeout=timeout_sec,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    root = ET.fromstring(response.content)
    rows: List[Dict[str, Any]] = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        snippet = (item.findtext("description") or "").strip()
        published = (item.findtext("pubDate") or "").strip()
        if not title and not snippet:
            continue
        rows.append(
            {
                "query": query,
                "title": title[:160],
                "url": url[:280],
                "snippet": snippet[:260],
                "published": published,
                "engine": "bing_rss",
                "category": "general",
            }
        )
    return {
        "ok": True,
        "query": query,
        "results": rows,
        "raw_count": len(rows),
        "engine": "bing_rss",
    }
