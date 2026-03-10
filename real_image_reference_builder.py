#!/usr/bin/env python3
"""Build real-image search entrypoints and page-level preview candidates."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import quote, urljoin, urlparse

import requests


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36 OpenClawAssetBot/1.0"
)

SEARCH_TARGETS: List[Dict[str, str]] = [
    {"label": "Bing 图片", "url": "https://www.bing.com/images/search?q={q}"},
    {"label": "京东搜索", "url": "https://search.jd.com/Search?keyword={q}"},
    {"label": "淘宝搜索", "url": "https://s.taobao.com/search?q={q}"},
    {"label": "B站搜索", "url": "https://search.bilibili.com/all?keyword={q}"},
    {"label": "小红书搜索", "url": "https://www.xiaohongshu.com/search_result?keyword={q}"},
    {"label": "知乎搜索", "url": "https://www.zhihu.com/search?type=content&q={q}"},
]

DOMAIN_HINTS: Dict[str, List[str]] = {
    "品牌官方图": [],
    "品牌官方场景图": [],
    "品牌官方佩戴图": [],
    "京东/天猫详情页实拍": ["jd.com", "tmall.com", "taobao.com"],
    "电商详情页细节图": ["jd.com", "tmall.com", "taobao.com"],
    "测评频道实拍": ["bilibili.com", "zhihu.com"],
    "B站/小红书测评实拍": ["bilibili.com", "xiaohongshu.com"],
    "宠物博主测评实拍": ["xiaohongshu.com", "bilibili.com"],
    "真实用户实拍": ["xiaohongshu.com", "weibo.com"],
    "高质量买家秀": ["xiaohongshu.com", "taobao.com"],
    "真实训练实拍": ["xiaohongshu.com", "bilibili.com"],
    "测评视频截图": ["bilibili.com", "ixigua.com", "douyin.com"],
}

HIGH_WATERMARK_RISK_DOMAINS = {
    "xiaohongshu.com",
    "www.xiaohongshu.com",
    "weibo.com",
    "www.weibo.com",
    "m.weibo.cn",
    "bilibili.com",
    "www.bilibili.com",
    "douyin.com",
    "www.douyin.com",
    "ixigua.com",
    "www.ixigua.com",
}

MEDIUM_WATERMARK_RISK_DOMAINS = {
    "jd.com",
    "www.jd.com",
    "search.jd.com",
    "taobao.com",
    "www.taobao.com",
    "tmall.com",
    "www.tmall.com",
}

WATERMARK_HINTS = [
    "watermark",
    "logo",
    "qrcode",
    "qr",
    "stamp",
    "xiaohongshu",
    "bilibili",
    "douyin",
    "weibo",
]

SAFE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _normalize_image_url(image_url: str, page_url: str) -> str:
    current = html.unescape((image_url or "").strip())
    if not current:
        return ""
    if current.startswith("//"):
        return "https:" + current
    if current.startswith("http://") or current.startswith("https://"):
        return current
    return urljoin(page_url, current)


def build_search_entrypoints(queries: Iterable[str], source_priority: Iterable[str]) -> List[Dict[str, str]]:
    cleaned_queries = [str(x).strip() for x in queries if str(x).strip()]
    cleaned_sources = [str(x).strip() for x in source_priority if str(x).strip()]
    rows: List[Dict[str, str]] = []
    seen = set()
    for query in cleaned_queries[:4]:
        for target in SEARCH_TARGETS:
            key = (target["label"], query)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "label": target["label"],
                    "query": query,
                    "url": target["url"].format(q=quote(query)),
                    "source_priority": " / ".join(cleaned_sources[:3]),
                }
            )
    return rows


def extract_image_candidates_from_page(page_url: str, timeout_sec: int = 15) -> List[Dict[str, Any]]:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
    response = requests.get(page_url, headers=headers, timeout=timeout_sec)
    response.raise_for_status()
    body = response.text
    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.I | re.S)
    title = html.unescape(title_match.group(1)).strip() if title_match else ""
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+itemprop=["\']image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>',
    ]
    candidates: List[Dict[str, Any]] = []
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, body, flags=re.I):
            raw_url = match.group(1)
            image_url = _normalize_image_url(raw_url, page_url)
            if not image_url or image_url in seen:
                continue
            seen.add(image_url)
            candidates.append(
                {
                    "page_url": page_url,
                    "page_title": title[:180],
                    "image_url": image_url,
                    "source_domain": _domain(page_url),
                }
            )
            if len(candidates) >= 6:
                return candidates
    return candidates


def score_candidate(candidate: Dict[str, Any], preferred_domains: Iterable[str]) -> int:
    score = 0
    domain = str(candidate.get("source_domain", "")).lower()
    image_url = str(candidate.get("image_url", "")).lower()
    title = str(candidate.get("page_title", "")).lower()
    page_url = str(candidate.get("page_url", "")).lower()
    for hint in preferred_domains:
        if hint and hint in domain:
            score += 30
        if hint and hint in image_url:
            score += 10
    if image_url.startswith("https://"):
        score += 10
    if any(token in title for token in ["评测", "开箱", "实拍", "使用", "官方"]):
        score += 8
    if any(token in image_url for token in [".jpg", ".jpeg", ".png", ".webp"]):
        score += 5
    path = urlparse(page_url).path.strip("/")
    if not path:
        score -= 12
    return score


def detect_watermark_risk(candidate: Dict[str, Any]) -> Dict[str, Any]:
    domain = str(candidate.get("source_domain", "")).lower().strip()
    image_url = str(candidate.get("image_url", "")).lower().strip()
    page_url = str(candidate.get("page_url", "")).lower().strip()
    title = str(candidate.get("page_title", "")).lower().strip()
    joined = " ".join([domain, image_url, page_url, title])
    reasons: List[str] = []
    score = 0

    if any(domain == risky or domain.endswith("." + risky) for risky in HIGH_WATERMARK_RISK_DOMAINS):
        score += 80
        reasons.append("high-risk social/video domain")
    elif any(domain == risky or domain.endswith("." + risky) for risky in MEDIUM_WATERMARK_RISK_DOMAINS):
        score += 25
        reasons.append("medium-risk ecommerce domain")

    for hint in WATERMARK_HINTS:
        if hint in joined:
            score += 20
            reasons.append(f"hint:{hint}")

    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix and suffix not in SAFE_IMAGE_EXTENSIONS:
        score += 10
        reasons.append("non-standard image extension")

    accepted = score < 40
    if accepted:
        policy = "usable_without_watermark_removal"
    else:
        policy = "reject_instead_of_removing_watermark"
    return {
        "watermark_risk_score": score,
        "watermark_risk_reasons": reasons,
        "accepted": accepted,
        "usage_policy": policy,
    }


def preferred_domains_from_priority(source_priority: Iterable[str]) -> List[str]:
    rows: List[str] = []
    for label in source_priority:
        rows.extend(DOMAIN_HINTS.get(str(label).strip(), []))
    seen: List[str] = []
    for row in rows:
        if row and row not in seen:
            seen.append(row)
    return seen


def build_real_image_reference_bundle(
    *,
    topic: str,
    platform: str,
    reference_queries: Iterable[str],
    source_priority: Iterable[str],
    material_slots: Iterable[Dict[str, Any]],
    research_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    queries = [str(x).strip() for x in reference_queries if str(x).strip()]
    priorities = [str(x).strip() for x in source_priority if str(x).strip()]
    slots = [x for x in material_slots if isinstance(x, dict)]
    research_rows = research_context.get("results", []) if isinstance(research_context, dict) else []
    page_urls: List[str] = []
    for row in research_rows:
        if not isinstance(row, dict):
            continue
        url = str(row.get("url", "")).strip()
        if url and url not in page_urls:
            page_urls.append(url)
    preferred_domains = preferred_domains_from_priority(priorities)
    raw_candidates: List[Dict[str, Any]] = []
    errors: List[str] = []
    for url in page_urls[:8]:
        try:
            raw_candidates.extend(extract_image_candidates_from_page(url))
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for row in raw_candidates:
        key = str(row.get("image_url", "")).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        scored = dict(row)
        scored["score"] = score_candidate(scored, preferred_domains)
        scored.update(detect_watermark_risk(scored))
        deduped.append(scored)
    deduped.sort(
        key=lambda x: (
            bool(x.get("accepted", False)),
            -int(x.get("watermark_risk_score", 0)),
            int(x.get("score", 0)),
            str(x.get("page_title", "")),
        ),
        reverse=True,
    )
    accepted_candidates = [row for row in deduped if row.get("accepted")]
    rejected_candidates = [row for row in deduped if not row.get("accepted")]
    slot_plan: List[Dict[str, Any]] = []
    for idx, slot in enumerate(slots, start=1):
        query = str(slot.get("search_query", "")).strip() or (queries[min(idx - 1, len(queries) - 1)] if queries else topic)
        slot_plan.append(
            {
                "slot": str(slot.get("slot", f"图位 {idx}")).strip(),
                "purpose": str(slot.get("purpose", "")).strip(),
                "search_query": query,
                "search_links": build_search_entrypoints([query], priorities)[:4],
            }
        )
    return {
        "topic": topic,
        "platform": platform,
        "provider_mode": "page_preview_and_search_entrypoints",
        "image_policy": {
            "watermark_removal_allowed": False,
            "selection_rule": "Only use accepted candidates that are usable without watermark removal.",
        },
        "preferred_domains": preferred_domains,
        "search_entrypoints": build_search_entrypoints(queries, priorities),
        "page_preview_candidates": accepted_candidates[:10],
        "rejected_candidates": rejected_candidates[:10],
        "slot_plan": slot_plan,
        "errors": errors[:8],
    }


def _demo() -> None:
    sample = build_real_image_reference_bundle(
        topic="扫地机器人选购避坑",
        platform="知乎",
        reference_queries=["扫地机器人 实拍", "扫地机器人 开箱", "扫地机器人 评测"],
        source_priority=["品牌官方图", "京东/天猫详情页实拍", "B站/小红书测评实拍"],
        material_slots=[
            {"slot": "封面主图", "purpose": "建立可信度", "search_query": "扫地机器人 机身 实拍"},
            {"slot": "正文细节图", "purpose": "支撑观点", "search_query": "扫地机器人 刷头 细节"},
        ],
        research_context={"results": [{"url": "https://www.jd.com/"}, {"url": "https://www.bilibili.com/"}]},
    )
    print(json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _demo()
