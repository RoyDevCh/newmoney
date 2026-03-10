#!/usr/bin/env python3
"""Generate monetization-ready drafts with research, rewrite, and quality loops."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urlparse

from content_quality_gate import DraftScore, score_one
from consumer_product_knowledge import (
    build_knowledge_lines,
    build_peer_compare_markdown,
    build_previous_gen_compare_markdown,
    build_review_dimensions_markdown,
    build_series_markdown_table,
    get_product_knowledge,
)
from content_formula_policy import (
    build_formula_prompt_hint,
    get_subformula_policy,
    infer_content_formula,
    infer_content_subformula,
)
from content_novelty_policy import build_global_novelty_context, build_platform_novelty_context, load_novelty_state
from local_search_client import local_search_health, search_bing_rss, search_local_searxng
from platform_direction_policy import build_platform_direction_brief, get_platform_direction
from zhihu_editorial_ufm import build_ufm_output_contract, build_ufm_prompt_rules

OPENCLAW_CMD = Path.home() / "AppData" / "Roaming" / "npm" / "openclaw.cmd"
NODE_BIN = Path("C:/Program Files/nodejs/node.exe")
OPENCLAW_ENTRY = Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "openclaw" / "openclaw.mjs"
ROOT_WORKSPACE = Path.home() / ".openclaw" / "workspace"

if str(ROOT_WORKSPACE) not in sys.path:
    sys.path.insert(0, str(ROOT_WORKSPACE))

ZH = "知乎"
XHS = "小红书"
WB = "微博"
WX = "公众号"
TT = "头条"
DY = "抖音"
XG = "西瓜视频"
BILI = "B站"

DEFAULT_PLATFORMS = [ZH, XHS, WB, WX, TT, DY, XG, BILI]

PLATFORM_BRIEFS: Dict[str, Dict[str, Any]] = {
    ZH: {
        "body_range": "1100-1800",
        "min_body": 1100,
        "voice": "理性、克制、结构清楚，像认真回答过很多问题的人",
        "conversion": "引导收藏、评论关键词、领取模板或对照表",
        "angle": "搜索型选购长文、预算分段、品牌对比、场景决策",
        "structure": ["先给直接答案", "拆预算分段", "拆使用场景", "讲品牌或型号差异", "给不推荐情况", "给结论清单"],
        "visual": "16:9 clean editorial cover, one realistic laptop, one notebook, one desk lamp",
    },
    XHS: {
        "body_range": "220-420",
        "min_body": 220,
        "voice": "像高质量博主在分享自己真用过的方法，少行话，强场景",
        "conversion": "引导收藏、评论关键词、领清单或模板",
        "angle": "收藏清单、前后对比、马上能做的轻教程",
        "structure": ["先给结论", "讲1个使用场景", "给3个小动作", "最后留收藏动作"],
        "visual": "3:4 soft magazine cover, tidy desk, realistic devices, natural lighting",
    },
    WB: {
        "body_range": "140-260",
        "min_body": 140,
        "voice": "快评感、信息密度高、动作单一",
        "conversion": "评论互动或单链接，不要多跳转",
        "angle": "热点快评、结论卡片、单清单",
        "structure": ["一句总判断", "三条证据", "一个动作"],
        "visual": "4:3 news-card cover, bold headline strip, realistic screen and keyboard",
    },
    WX: {
        "body_range": "1200-2200",
        "min_body": 1200,
        "voice": "像稳定更新的订阅型作者，讲清楚逻辑和执行细节",
        "conversion": "文末只保留一个资料入口或订阅动作",
        "angle": "方法论、清单、复盘、资料包承接",
        "structure": ["结论", "适用场景", "常见误区", "执行步骤", "案例", "资料入口"],
        "visual": "900x383 editorial banner, realistic desk setup, restrained typography",
    },
    TT: {
        "body_range": "1200-2200",
        "min_body": 1200,
        "voice": "信息流长文，标题要抓人，但正文要耐读",
        "conversion": "引导收藏、关注系列、查看置顶清单",
        "angle": "强标题长图文、误区清单、场景避坑",
        "structure": ["先给结论", "讲最常见误区", "给三步顺序", "补案例", "只留一个动作"],
        "visual": "3:2 high-clarity cover with one realistic hero object and readable headline area",
    },
    DY: {
        "body_range": "170-300",
        "min_body": 170,
        "voice": "口播感、短句、每句有动作",
        "conversion": "引导主页或评论关键词",
        "angle": "3秒Hook、纠错、三步解决",
        "structure": ["先打断错误认知", "给一结论", "给三步动作", "留一个动作"],
        "visual": "9:16 bold short-video cover, one large subject, strong contrast",
    },
    XG: {
        "body_range": "650-1100",
        "min_body": 650,
        "voice": "横屏解说感，证据和节奏都要稳",
        "conversion": "收藏本集、看简介清单、承接下一条",
        "angle": "3到8分钟母体视频、案例拆解、流程演示",
        "structure": ["先结论", "讲问题", "讲案例", "讲步骤", "讲下一步"],
        "visual": "16:9 documentary creator frame, realistic monitor and laptop, no warped hardware",
    },
    BILI: {
        "body_range": "550-900",
        "min_body": 550,
        "voice": "硬核但不装，像做过实测的人",
        "conversion": "三连、评论关键词、下期选题互动",
        "angle": "横评、流程演示、实测结论",
        "structure": ["先结论", "讲测试背景", "给对比", "给操作步骤", "留互动"],
        "visual": "16:9 documentary tech cover, realistic screen, realistic keyboard, no extra fingers",
    },
}

ARTICLE_PLATFORMS = {ZH, XHS, WB, WX, TT}
LONGFORM_PLATFORMS = {ZH, WX, TT}

CLAIM_REPLACEMENTS: List[Tuple[str, str]] = [
    (r"月入\s*\d+\+?", "效率提升更明显"),
    (r"月赚\s*\d+\+?", "转化效率更高"),
    (r"收入翻倍", "产能提升更明显"),
    (r"多赚\s*\d+\+?", "承接效率更高"),
    (r"服务\s*\d+\+?\s*家企业", "服务过多种企业场景"),
    (r"累计学员\s*\d+\+?", "有持续用户实践反馈"),
    (r"\d+\+?\s*企业客户", "多类企业场景"),
    (r"\d+\+?\s*学员", "多个真实使用场景"),
    (r"过去一年我实测了", "过去一年我系统整理了"),
    (r"我实测了", "我系统整理了"),
    (r"我亲测了", "我对比整理了"),
    (r"我测试了", "我对比整理了"),
    (r"我用过", "我重点看了"),
    (r"实测上百台", "整理上百份公开评测和用户反馈"),
    (r"实测百台", "整理上百份公开评测和用户反馈"),
    (r"实测\d+\+?款", "整理多份公开评测和用户反馈"),
    (r"全试了一遍", "系统整理了一遍"),
]

EMOJI_BROAD_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)


def run_agent(agent: str, prompt: str, timeout: int = 300) -> str:
    compact_prompt = re.sub(r"\s+", " ", prompt).strip()
    if NODE_BIN.exists() and OPENCLAW_ENTRY.exists():
        cmd: List[str] = [
            str(NODE_BIN),
            str(OPENCLAW_ENTRY),
            "agent",
            "--agent",
            agent,
            "--message",
            compact_prompt,
            "--timeout",
            str(timeout),
            "--json",
        ]
    else:
        cmd = [
            "cmd",
            "/c",
            str(OPENCLAW_CMD),
            "agent",
            "--agent",
            agent,
            "--message",
            compact_prompt,
            "--timeout",
            str(timeout),
            "--json",
        ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout + 80,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "").strip() or f"returncode={proc.returncode}")
    return unwrap_openclaw_payload((proc.stdout or "").strip())


def extract_json(text: str) -> Any:
    payload = (text or "").strip()
    if not payload:
        raise ValueError("empty text")
    try:
        return json.loads(payload)
    except Exception:
        pass

    match = re.search(r"```(?:json)?\s*(.*?)\s*```", payload, flags=re.S | re.I)
    candidate = match.group(1) if match else payload
    for left, right in [("[", "]"), ("{", "}")]:
        start = candidate.find(left)
        end = candidate.rfind(right)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except Exception:
                continue
    raise ValueError("could not extract json")


def unwrap_openclaw_payload(raw: str) -> str:
    data = extract_json(raw)
    if isinstance(data, dict):
        payloads = data.get("result", {}).get("payloads", [])
        if payloads and isinstance(payloads[0], dict):
            text = payloads[0].get("text")
            if isinstance(text, str):
                return text.strip()
    return raw.strip()


def normalize_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if "drafts" in data and isinstance(data["drafts"], list):
            return [x for x in data["drafts"] if isinstance(x, dict)]
        return [data]
    raise ValueError("unsupported json structure")


def load_metrics_feedback(path: str | None) -> Dict[str, Any]:
    if not path:
        return {"available": False, "platform_summary": {}, "suggestions": [], "strategy_overrides": {}}
    candidate = Path(path)
    if not candidate.exists():
        return {"available": False, "platform_summary": {}, "suggestions": [], "strategy_overrides": {}}
    try:
        data = json.loads(candidate.read_text(encoding="utf-8-sig"))
        return {
            "available": True,
            "platform_summary": data.get("platform_summary", {}),
            "suggestions": data.get("suggestions", []),
            "strategy_overrides": data.get("strategy_overrides", {}),
        }
    except Exception as exc:
        return {"available": False, "error": str(exc), "platform_summary": {}, "suggestions": [], "strategy_overrides": {}}


def _lazy_fallback_search_import() -> Any:
    try:
        from ddgs import DDGS  # type: ignore

        def _search(query: str, max_results: int = 5) -> Any:
            return list(DDGS().text(query, max_results=max_results))

        return _search
    except Exception:
        pass
    try:
        from duckduckgo_search import DDGS  # type: ignore

        def _search(query: str, max_results: int = 5) -> Any:
            return list(DDGS().text(query, max_results=max_results))

        return _search
    except Exception:
        pass
    try:
        from search import search as ddgs_search  # type: ignore

        return ddgs_search
    except Exception:
        return None


def _fallback_search(query: str, limit: int = 5) -> List[Dict[str, str]]:
    ddgs_search = _lazy_fallback_search_import()
    if ddgs_search:
        try:
            raw = ddgs_search(query, max_results=limit)
            rows = _normalize_search_rows(raw, query, engine="ddgs")
            if rows:
                return rows
        except Exception:
            pass

    try:
        bing_result = search_bing_rss(query, limit=limit)
        rows = bing_result.get("results", [])
        if rows:
            return rows
    except Exception:
        pass
    return []


def _published_freshness_bonus(value: str) -> int:
    raw = str(value or '').strip()
    if not raw:
        return 0
    try:
        parsed = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return 0
    age = datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)
    if age <= timedelta(days=7):
        return 2
    if age <= timedelta(days=30):
        return 1
    return 0


def _site_domain_from_query(query: str) -> str:
    match = re.search(r'site:([\w.-]+)', str(query or ''), flags=re.I)
    if not match:
        return ''
    return match.group(1).lower().strip()


def _normalize_search_rows(data: Any, query: str, engine: str = "") -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if isinstance(data, dict):
        candidates = data.get("results", [])
    elif isinstance(data, list):
        candidates = data
    else:
        candidates = []

    for item in candidates[:5]:
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
                "title": title[:120],
                "url": url[:240],
                "snippet": snippet[:220],
                "published": str(item.get("published", "") or item.get("published_date", "") or item.get("date", "")).strip(),
                "engine": str(item.get("engine", "")).strip() or engine,
            }
        )
    return rows


BLOCKED_RESEARCH_DOMAINS = {
    "npmjs.com",
    "pypi.org",
    "anaconda.org",
    "mvnrepository.com",
    "readthedocs.io",
    "docs.python.org",
    "developer.mozilla.org",
}

TRUSTED_RESEARCH_DOMAINS = {
    "zhihu.com",
    "xiaohongshu.com",
    "weibo.com",
    "toutiao.com",
    "ixigua.com",
    "bilibili.com",
    "mp.weixin.qq.com",
    "qq.com",
    "163.com",
    "36kr.com",
    "thepaper.cn",
    "smzdm.com",
    "zol.com.cn",
    "pconline.com.cn",
    "cheaa.com",
    "sina.com.cn",
}

TRUSTED_PLATFORM_DOMAINS = {
    "zhihu.com",
    "xiaohongshu.com",
    "weibo.com",
    "toutiao.com",
    "ixigua.com",
    "bilibili.com",
    "mp.weixin.qq.com",
}

TOPIC_STOPWORDS = {
    "2026",
    "指南",
    "清单",
    "避坑",
    "推荐",
    "实测",
    "公开",
    "评测",
    "对比",
    "经验",
    "总结",
    "怎么选",
    "怎么做",
}

BUYING_GUIDE_HINTS = {
    "推荐",
    "怎么选",
    "选购",
    "避坑",
    "哪个牌子",
    "预算",
    "对比",
    "型号",
}

ZHIHU_ANSWER_HINTS = {
    "如何",
    "为什么",
    "怎么理解",
    "怎么办",
    "值不值得",
    "有哪些",
    "是否",
    "有没有必要",
    "为什么说",
    "怎么看",
}

CONSUMER_TOPIC_HINTS = {
    "home_cleaning": ["清洁", "扫地", "洗地", "吸尘", "家居", "家务", "智能家居"],
    "pets": ["宠物", "猫", "狗", "露营", "训练", "陪伴"],
    "jewelry_style": ["珠宝", "配饰", "项链", "戒指", "耳饰", "穿搭", "男生佩戴"],
    "sports_outdoor": ["运动", "户外", "跑步", "力量训练", "网球", "徒步", "拳击", "健身"],
    "digital_gear": ["数码", "笔记本", "手机", "耳机", "显示器", "平板", "路由器", "显卡"],
}


def _topic_bucket(topic: str) -> str:
    current = str(topic or "").strip()
    for bucket, keywords in CONSUMER_TOPIC_HINTS.items():
        if any(keyword in current for keyword in keywords):
            return bucket
    if "AI" in current or "工具" in current or "效率" in current or "知识管理" in current:
        return "tech_ai"
    return "general"


def _focus_terms(topic: str) -> List[str]:
    current = str(topic or "").strip()
    latin_terms = [
        token.lower()
        for token in re.split(r"[^0-9A-Za-z.+-]+", current)
        if len(token.strip()) >= 3 and token.strip().lower() not in {item.lower() for item in TOPIC_STOPWORDS}
    ]
    cjk_terms = [
        token.strip()
        for token in re.findall(r"[\u4e00-\u9fff]{2,}", current)
        if token.strip() and token.strip() not in TOPIC_STOPWORDS
    ]
    terms: List[str] = []
    for item in cjk_terms + latin_terms + CONSUMER_TOPIC_HINTS.get(_topic_bucket(current), []):
        if item and item not in terms:
            terms.append(item)
    return terms[:12]


def _topic_keywords(topic: str) -> List[str]:
    current = str(topic or "").strip()
    seed = re.split(r"[\s,/|、，。:：()（）-]+", current)
    keywords = [item for item in seed if len(item) >= 2 and item not in TOPIC_STOPWORDS]
    bucket = _topic_bucket(current)
    keywords.extend(CONSUMER_TOPIC_HINTS.get(bucket, []))
    keywords.extend(_focus_terms(current))
    seen: List[str] = []
    for item in keywords:
        if item and item not in seen:
            seen.append(item)
    return seen[:12]


def is_buying_guide_topic(topic: str) -> bool:
    current = str(topic or "").strip()
    return any(hint in current for hint in BUYING_GUIDE_HINTS) or _topic_bucket(current) in {
        "home_cleaning",
        "digital_gear",
        "sports_outdoor",
        "jewelry_style",
        "pets",
    }


def infer_zhihu_format(topic: str) -> str:
    current = str(topic or "").strip()
    if not current:
        return "article"
    explicit_article_hints = {"推荐", "选购", "预算", "对比", "型号", "排行", "清单"}
    if any(hint in current for hint in ZHIHU_ANSWER_HINTS) or "?" in current or "？" in current:
        return "article" if any(hint in current for hint in explicit_article_hints) else "answer"
    if is_buying_guide_topic(current):
        return "article"
    return "article"


def _research_row_score(row: Dict[str, str], topic: str, platforms: Iterable[str]) -> int:
    title = str(row.get("title", "")).lower()
    snippet = str(row.get("snippet", "")).lower()
    url = str(row.get("url", "")).lower()
    query = str(row.get("query", "")).strip()
    text = " ".join([title, snippet, url])
    domain = _domain_from_url(url)
    bucket = _topic_bucket(topic)
    score = 0
    focus_terms = _focus_terms(topic)
    focus_hits = sum(1 for term in focus_terms if term.lower() in text)

    for keyword in _topic_keywords(topic):
        if keyword.lower() in text:
            score += 2

    if focus_hits:
        score += min(6, focus_hits * 3)

    if domain in TRUSTED_PLATFORM_DOMAINS:
        score += 2
    if domain in TRUSTED_RESEARCH_DOMAINS:
        score += 2
    if any(platform_domain in domain for platform_domain in TRUSTED_PLATFORM_DOMAINS):
        score += 1

    expected_site = _site_domain_from_query(query)
    if expected_site and expected_site in domain:
        score += 3
    if expected_site and domain and expected_site not in domain:
        score -= 2

    if bucket != "tech_ai" and domain in BLOCKED_RESEARCH_DOMAINS:
        score -= 6
    if bucket != "tech_ai" and any(bad in text for bad in ["npm search", "package", "api reference", "sdk", "developer docs"]):
        score -= 4
    if bucket != "tech_ai" and not focus_hits:
        score -= 5

    if "实测" in text or "评测" in text or "对比" in text or "清单" in text or "避坑" in text:
        score += 1
    if any(platform in text for platform in ["知乎", "小红书", "微博", "头条", "西瓜", "b站", "bilibili"]):
        score += 1

    score += _published_freshness_bonus(str(row.get("published", "")))
    return score


def _keep_research_row(row: Dict[str, str], topic: str, platforms: Iterable[str]) -> bool:
    text = " ".join(
        [
            str(row.get("title", "")).lower(),
            str(row.get("snippet", "")).lower(),
            str(row.get("url", "")).lower(),
        ]
    )
    focus_terms = _focus_terms(topic)
    focus_hits = sum(1 for term in focus_terms if term.lower() in text)
    expected_site = _site_domain_from_query(str(row.get("query", "")))
    domain = _domain_from_url(str(row.get("url", "")))
    if expected_site and domain and expected_site not in domain and focus_hits == 0:
        return False
    if _topic_bucket(topic) != "tech_ai" and focus_hits == 0:
        return False
    return _research_row_score(row, topic, platforms) >= 4


def build_research_queries(topic: str, platforms: Iterable[str]) -> List[str]:
    queries = [
        f"{topic} 2026 实测",
        f"{topic} 公开评测 选购 对比",
        f"{topic} 真实使用 经验 总结",
    ]
    platform_query_map = {
        ZH: f"{topic} site:zhihu.com",
        XHS: f"{topic} site:xiaohongshu.com",
        WB: f"{topic} site:weibo.com",
        WX: f"{topic} 微信公众号 资料 清单",
        TT: f"{topic} 头条 长文 经验",
        DY: f"{topic} site:douyin.com",
        XG: f"{topic} site:ixigua.com",
        BILI: f"{topic} site:bilibili.com",
    }
    for platform in platforms:
        if platform in platform_query_map:
            queries.append(platform_query_map[platform])
    seen: List[str] = []
    for item in queries:
        if item not in seen:
            seen.append(item)
    return seen[:8]


def gather_research_context(topic: str, platforms: List[str]) -> Dict[str, Any]:
    collected: List[Dict[str, str]] = []
    sources: List[str] = []
    local_status = local_search_health()
    query_plan = build_research_queries(topic, platforms)

    for query in query_plan:
        used_local = False
        if local_status.get("ok"):
            try:
                local_result = search_local_searxng(query, categories="general", limit=6)
                rows = local_result.get("results", [])
                if rows:
                    collected.extend(rows)
                    sources.append("local_searxng")
                    used_local = True
            except Exception:
                used_local = False
        if used_local:
            continue
        rows = _fallback_search(query, limit=5)
        if rows:
            collected.extend(rows)
            sources.append(str(rows[0].get("engine", "fallback")))

    deduped: List[Dict[str, str]] = []
    seen_keys = set()
    for row in sorted(collected, key=lambda item: _research_row_score(item, topic, platforms), reverse=True):
        key = (row.get("title", ""), row.get("url", ""))
        if key in seen_keys:
            continue
        if not _keep_research_row(row, topic, platforms):
            continue
        seen_keys.add(key)
        deduped.append(row)

    return {
        "available": bool(deduped),
        "sources": sorted(set(sources)),
        "results": deduped[:8],
        "query_plan": query_plan,
        "local_search": local_status,
    }


def _domain_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return "公开资料"
    if host.startswith("www."):
        host = host[4:]
    return host or "公开资料"


def research_evidence_lines(research: Dict[str, Any], limit: int = 3) -> List[str]:
    rows = research.get("results", []) if isinstance(research, dict) else []
    output: List[str] = []
    for idx, row in enumerate(rows[:limit], start=1):
        if not isinstance(row, dict):
            continue
        title = re.sub(r"\s+", " ", str(row.get("title", "")).strip())
        snippet = re.sub(r"\s+", " ", str(row.get("snippet", "")).strip())
        domain = _domain_from_url(str(row.get("url", "")).strip())
        if len(snippet) > 96:
            snippet = snippet[:96].rstrip("，。；;,. ") + "。"
        if not snippet:
            snippet = "这一方向被重复提及，说明它至少值得拿来做路线对照。"
        if title:
            output.append(f"资料线索{idx}：{domain} 的公开资料提到《{title}》，重点是{snippet}")
        else:
            output.append(f"资料线索{idx}：{domain} 的公开资料显示，{snippet}")
    return output


def feedback_tuning_lines(platform: str, feedback: Dict[str, Any]) -> List[str]:
    if not isinstance(feedback, dict):
        return []
    overrides = feedback.get("strategy_overrides", {}).get(platform, {})
    if not isinstance(overrides, dict):
        overrides = {}

    lines: List[str] = []
    if overrides.get("raise_depth"):
        lines.append("历史数据提示：这类内容的读完率偏低时，不要再加空观点，优先补案例、对照表和执行顺序。")
    if overrides.get("prefer_checklist"):
        lines.append("历史数据提示：收藏信号更强的稿子通常都有清单感，结尾最好留一个能直接照做的对照表。")
    if overrides.get("raise_specificity"):
        lines.append("历史数据提示：如果互动不够，优先把正文改成具体场景、具体动作、具体判断标准。")
    if overrides.get("tighten_cta"):
        lines.append("历史数据提示：CTA 只留一个动作，评论关键词、主页跳转和资料领取不要同时出现。")
    return lines[:3]


def first_research_hint(research: Dict[str, Any]) -> str:
    lines = research_evidence_lines(research, limit=1)
    return lines[0] if lines else "公开资料和测试环境里反复出现的共识是：先验证一个高频场景，再扩工具组合。"


def research_block(research: Dict[str, Any], limit: int = 2) -> str:
    lines = research_evidence_lines(research, limit=limit)
    return "\n\n".join(lines).strip()


def knowledge_evidence_lines(topic: str, limit: int = 5) -> List[str]:
    return build_knowledge_lines(topic, limit=limit)


def build_product_knowledge_blocks(topic: str) -> Dict[str, str]:
    data = get_product_knowledge(topic)
    if not data:
        return {}
    budget_rows = data.get("budget_bands", [])
    scenario_rows = data.get("scenarios", [])
    brand_rows = data.get("brand_positions", [])
    series_rows = data.get("series_guidance", [])
    avoid_rows = data.get("avoid", [])
    factor_rows = data.get("decision_factors", [])
    review_rows = data.get("review_dimensions", [])
    prev_rows = data.get("previous_gen_compare", [])
    peer_rows = data.get("peer_compare", [])
    budget_text = "\n".join(
        f"- {row.get('range', '')}：更适合{row.get('fit', '')}；重点看{row.get('watch', '')}"
        for row in budget_rows[:3]
    ).strip()
    scenario_text = "\n".join(f"- {row}" for row in scenario_rows[:3]).strip()
    brand_text = "\n".join(f"- {row}" for row in brand_rows[:4]).strip()
    series_text = "\n".join(f"- {row}" for row in series_rows[:4]).strip()
    avoid_text = "\n".join(f"- {row}" for row in avoid_rows[:3]).strip()
    factor_text = "、".join(factor_rows[:5]).strip()
    review_text = "\n".join(
        f"- {row.get('name', '')}：{row.get('why', '')}" for row in review_rows[:6] if isinstance(row, dict)
    ).strip()
    previous_gen_text = "\n".join(f"- {row}" for row in prev_rows[:4]).strip()
    peer_text = "\n".join(f"- {row}" for row in peer_rows[:4]).strip()
    return {
        "factors": factor_text,
        "budget": budget_text,
        "scenarios": scenario_text,
        "brands": brand_text,
        "series": series_text,
        "avoid": avoid_text,
        "review_dimensions": review_text,
        "previous_gen_compare": previous_gen_text,
        "peer_compare": peer_text,
    }


def build_single_product_rules(topic: str, platform: str) -> str:
    formula = infer_content_formula(topic, platform)
    if formula not in {"single_product_review", "launch_roundup"}:
        return ""
    subformula = infer_content_subformula(topic, platform)
    subpolicy = get_subformula_policy(subformula)
    subtype_label = str(subpolicy.get("label", "")).strip()
    subtype_must_have = "、".join(subpolicy.get("must_have", []))
    opening = str(subpolicy.get("opening", "")).strip()
    review_dimensions = build_review_dimensions_markdown(topic)
    previous_gen = build_previous_gen_compare_markdown(topic)
    peer_compare = build_peer_compare_markdown(topic)
    return (
        f"本次单品稿子模板={subtype_label}。"
        " 文章必须先给购买判断，再讲参数和背景。"
        " 必须主动区分三层：已确认信息、高概率成立、仍待验证。"
        " 任何涉及宣传口号、实验室口径、首发话术，都只能写成“公开宣传点”或“目前口径”，不能直接当成硬结论。"
        " 至少给出：证据口径说明、适合谁、不适合谁、现在买还是等等、仍需继续观察的点。"
        " 必须覆盖具体评测维度，不要只写抽象判断；至少覆盖 5 个产品维度。"
        " 如果这个品类存在上一代产品，必须单列“和上一代比真正变了什么”；如果没有清晰上一代，就必须单列“和同品类/同价位产品相比差异在哪”。"
        f" 子模板必须包含={subtype_must_have}。"
        f" 开篇要求={opening}"
        f" 评测维度参考={review_dimensions}"
        f" 上一代对比参考={previous_gen}"
        f" 同品类对比参考={peer_compare}"
    )


def build_evidence_writing_rules(topic: str, platform: str) -> str:
    formula = infer_content_formula(topic, platform)
    if formula not in {"single_product_review", "launch_roundup"}:
        return ""
    return (
        "证据写作规则："
        "1) 官方产品页、官方发布信息、规格页属于高优先级硬信息；"
        "2) 媒体上手、公开评测、拆解、跑分、长期追评可以作为补充证据，但必须说明口径；"
        "3) 社区讨论、电商评论只能作为问题雷达，不能直接当成事实；"
        "4) 如果证据还不够，只能写“倾向判断”或“目前看”，不能写成确定结论；"
        "5) 优先输出“这意味着什么”，不要只堆规格名词。"
    )


def build_novelty_prompt_context(platforms: List[str]) -> Dict[str, Any]:
    state = load_novelty_state()
    platform_rows = {platform: build_platform_novelty_context(platform, state, limit=6) for platform in platforms}
    return {
        "global": build_global_novelty_context(state, limit=10),
        "platforms": platform_rows,
    }


def select_best_drafts(drafts: List[Dict[str, Any]], platforms: List[str], min_score: float) -> List[Dict[str, Any]]:
    chosen: List[Dict[str, Any]] = []
    for platform in platforms:
        candidates = [d for d in drafts if str(d.get("platform", "")).strip() == platform]
        if not candidates:
            continue
        best = max(candidates, key=lambda d: score_one(d, min_score).total_score)
        chosen.append(best)
    return chosen


def summarize_feedback(feedback: Dict[str, Any]) -> str:
    if not feedback.get("available"):
        return "暂无有效历史反馈，默认优先做更厚、更具体、更可执行的版本。"
    notes: List[str] = []
    for item in feedback.get("suggestions", [])[:5]:
        if not isinstance(item, dict):
            continue
        platform = str(item.get("platform", "")).strip()
        directives = item.get("directives", [])
        plain_notes = item.get("notes", [])
        chosen = directives or plain_notes
        for note in chosen[:2]:
            notes.append(f"{platform}:{note}")
    return " | ".join(notes[:8]) if notes else "暂无明确反馈信号。"


def fallback_strategy(topic: str, platforms: List[str], feedback: Dict[str, Any], research: Dict[str, Any]) -> Dict[str, Any]:
    product_knowledge = get_product_knowledge(topic)
    formula = infer_content_formula(topic, ZH if ZH in platforms else "")
    proof_points = []
    for line in research_evidence_lines(research, limit=4):
        if line not in proof_points:
            proof_points.append(line)
    for line in knowledge_evidence_lines(topic, limit=4):
        if line not in proof_points:
            proof_points.append(line)
    if not proof_points:
        proof_points = [
            "先给判断标准，再给推荐清单。",
            "结论必须落到适合谁、不适合谁、怎么选。",
            "正文里至少给一个真实场景和一个对照判断。",
            "结尾只保留一个转化动作，不要多 CTA 并列。",
        ]
    must_have = [
        "首屏先下结论",
        "适合谁 / 不适合谁",
        "常见误区",
        "可执行步骤",
        "资料来源或测试环境说明",
    ]
    if is_buying_guide_topic(topic):
        must_have.extend(
            [
                "预算分段或价格带建议",
                "品牌 / 型号 / 品类差异",
                "明确推荐与不推荐的场景",
            ]
        )
    if product_knowledge:
        must_have.extend(["品牌定位判断", "至少一个预算带建议", "至少一个场景优先级判断"])
    if formula in {"single_product_review", "launch_roundup"}:
        must_have.extend(
            [
                "证据口径说明",
                "已确认信息 / 待验证信息分层",
                "适合谁 / 不适合谁",
                "现在买还是等等",
            ]
        )
    return {
        "audience": f"正在围绕{topic}做决策或准备发布相关内容、但不想被空话和泛推荐浪费时间的人",
        "pain_point": "信息太多但判断标准太少，看了很多推荐仍然不知道怎么选、怎么落地",
        "conversion_goal": "先促成收藏、评论或私信领取清单，再承接后续资料包、系列内容或商品决策",
        "offer": f"{topic} 对照清单 / 选购判断标准 / 可执行步骤",
        "platform_priority": platforms,
        "angle": "先判断、后推荐；先讲适合谁、再讲具体怎么做",
        "proof_points": proof_points[:4],
        "content_must_have": must_have,
        "feedback_hint": summarize_feedback(feedback),
        "product_knowledge": product_knowledge,
    }


def build_platform_rules(platforms: List[str]) -> str:
    chunks: List[str] = []
    for platform in platforms:
        brief = PLATFORM_BRIEFS.get(platform, {})
        structure = "、".join(brief.get("structure", []))
        direction = build_platform_direction_brief(platform)
        chunks.append(
            f"{platform}: 正文字数={brief.get('body_range','')}, 语气={brief.get('voice','')}, "
            f"转化={brief.get('conversion','')}, 角度={brief.get('angle','')}, 结构={structure}"
            + (f", 方向={direction}" if direction else "")
        )
    return " | ".join(chunks)


def build_strategy_prompt(topic: str, platforms: List[str], feedback: Dict[str, Any], research: Dict[str, Any]) -> str:
    buying_guide_rule = (
        "如果主题属于消费决策或选购推荐，content_must_have 里必须加入预算分段、品牌/型号差异、明确推荐与不推荐场景。"
        if is_buying_guide_topic(topic)
        else ""
    )
    zhihu_direction = build_platform_direction_brief(ZH) if ZH in platforms else ""
    product_knowledge = get_product_knowledge(topic)
    novelty = build_novelty_prompt_context(platforms)
    formula_hint = build_formula_prompt_hint(topic, ZH if ZH in platforms else "")
    evidence_rules = build_evidence_writing_rules(topic, ZH if ZH in platforms else "")
    single_product_rules = build_single_product_rules(topic, ZH if ZH in platforms else "")
    ufm_rules = build_ufm_prompt_rules(topic) if ZH in platforms else ""
    ufm_contract = build_ufm_output_contract(topic) if ZH in platforms else ""
    ufm_rules = build_ufm_prompt_rules(topic) if ZH in platforms else ""
    ufm_contract = build_ufm_output_contract(topic) if ZH in platforms else ""
    return (
        f"只输出JSON。主题={topic}，目标平台={','.join(platforms)}。"
        f"历史反馈={summarize_feedback(feedback)}。"
        f"研究资料={json.dumps(research, ensure_ascii=False)}。"
        f"产品知识={json.dumps(product_knowledge, ensure_ascii=False)}。"
        f"去重冷却={json.dumps(novelty, ensure_ascii=False)}。"
        f"内容母版={formula_hint}"
        f"{evidence_rules}"
        f"{single_product_rules}"
        f"{ufm_rules}"
        f"{ufm_contract}"
        "请给出今日可变现内容策略，字段："
        "audience,pain_point,conversion_goal,offer,platform_priority,angle,proof_points,content_must_have。"
        f"要求：proof_points至少4条；content_must_have至少5条；优先提升知乎、小红书、微博、公众号的含金量。"
        f"{buying_guide_rule}"
        f"{'知乎方向=' + zhihu_direction if zhihu_direction else ''}"
    )


def build_init_prompt(
    topic: str,
    platforms: List[str],
    strategy: Dict[str, Any],
    feedback: Dict[str, Any],
    research: Dict[str, Any],
) -> str:
    buying_guide_rules = (
        "9) 如果主题属于消费决策 / 选购推荐，长文必须包含预算分段、场景分层、品牌或型号差异、明确推荐与不推荐、结尾总结表。"
        "10) 这类选题不要只写方法论，必须像能承接搜索流量和购买决策的专栏文章。"
        if is_buying_guide_topic(topic)
        else ""
    )
    zhihu_policy = get_platform_direction(ZH) if ZH in platforms else {}
    zhihu_format = infer_zhihu_format(topic) if ZH in platforms else ""
    product_knowledge = get_product_knowledge(topic)
    novelty = build_novelty_prompt_context(platforms)
    formula_hint = build_formula_prompt_hint(topic, ZH if ZH in platforms else "")
    evidence_rules = build_evidence_writing_rules(topic, ZH if ZH in platforms else "")
    single_product_rules = build_single_product_rules(topic, ZH if ZH in platforms else "")
    zhihu_rule = (
        "11) 知乎优先做高决策成本科技消费，不要写成泛观点文。"
        "12) 知乎标题和首屏要覆盖搜索意图，正文要自然覆盖品牌词、型号词、预算词、场景词中的至少三类。"
        "13) 知乎的核心目标是收藏、搜索承接和后续转化，不是情绪共鸣。"
        if zhihu_policy
        else ""
    )
    zhihu_format_rule = (
        "14) 本次知乎稿件格式=专栏型长文，结构要像可承接搜索流量的专栏，不要写成零散问答。"
        if zhihu_format == "article"
        else "14) 本次知乎稿件格式=回答型长答，开头先直接回答问题，再给拆解、证据和边界条件。"
        if zhihu_format == "answer"
        else ""
    )
    return (
        f"只输出JSON数组。主题={topic}，平台={','.join(platforms)}，策略={json.dumps(strategy, ensure_ascii=False)}。"
        f"历史反馈={summarize_feedback(feedback)}。"
        f"可用研究资料={json.dumps(research, ensure_ascii=False)}。"
        f"产品知识={json.dumps(product_knowledge, ensure_ascii=False)}。"
        f"去重冷却={json.dumps(novelty, ensure_ascii=False)}。"
        f"内容母版={formula_hint}。"
        f"{evidence_rules}"
        f"{single_product_rules}"
        f"{ufm_rules}"
        f"{ufm_contract}"
        "为每个平台各生成1条能直接发布的稿件，字段必须是platform,title,hook,body,cta,tags。"
        "总要求："
        "1) 不要空话，不要模板味，不要像提示词拼装。"
        "2) 先下判断，再给证据，再给可执行动作。"
        "3) 如果用了数字，必须配合公开信息、实测环境、测试样本、公开评测等来源语气。"
        "4) 严禁收益承诺、虚假背书、伪官方口吻。"
        "5) 正文必须有信息增量，至少包含场景、误区、步骤、案例中的两项；长文平台至少包含四项。"
        f"6) 平台规则={build_platform_rules(platforms)}。"
        "7) 知乎和公众号不要只写观点，要给步骤、选择标准、适用和不适用人群。"
        "8) 小红书要像真实收藏笔记，微博要像快评，头条要像长图文，不能混写。"
        "9) 不要复用最近30天已经产出过的标题壳子、Hook 句式和相同核心卖点排序。"
        "10) 如果是单品评测汇总或新品发布判断，必须明确证据口径来自官方信息、媒体上手、公开评测、拆解资料或首批用户反馈，不能伪装成自己已经深度实测。"
        "补充要求A：单品稿必须同时包含一句话结论、适合谁、不适合谁、已确认信息、仍待验证信息。"
        "补充要求B：单品稿至少覆盖5个具体对比维度，例如健康功能、运动/GPS、外观材质、续航与充电、生态联动、佩戴舒适度。"
        "补充要求C：电子产品和汽车优先补‘和上一代比’，如果没有清晰上代，就补‘和同品类/同价位产品比’。"
        "补充要求D：对营销宣传点要写成“宣传点 / 当前口径 / 还需验证”，不要直接当成硬结论。"
        "补充要求E：知乎单品稿默认采用 L0 结论卡 + L1 可比矩阵 + L2 证据与方法附录的输出结构。"
        f"{buying_guide_rules}"
        f"{zhihu_rule}"
        f"{zhihu_format_rule}"
    )


def build_rewrite_prompt(
    topic: str,
    draft: Dict[str, Any],
    score: DraftScore,
    strategy: Dict[str, Any],
    feedback: Dict[str, Any],
    research: Dict[str, Any],
) -> str:
    platform = str(draft.get("platform", "")).strip()
    brief = PLATFORM_BRIEFS.get(platform, {})
    issues = ";".join(score.issues) if score.issues else "none"
    zhihu_format = infer_zhihu_format(topic) if platform == ZH else ""
    product_knowledge = get_product_knowledge(topic)
    novelty = build_platform_novelty_context(platform)
    formula_hint = build_formula_prompt_hint(topic, platform)
    evidence_rules = build_evidence_writing_rules(topic, platform)
    single_product_rules = build_single_product_rules(topic, platform)
    ufm_rules = build_ufm_prompt_rules(topic) if platform == ZH else ""
    ufm_contract = build_ufm_output_contract(topic) if platform == ZH else ""
    zhihu_rewrite_rule = (
        "知乎格式=专栏型长文，要像稳定吃搜索流量的决策专栏。"
        if zhihu_format == "article"
        else "知乎格式=回答型长答，要先直接回答问题，再补证据、边界条件和行动建议。"
        if zhihu_format == "answer"
        else ""
    )
    return (
        "只输出JSON对象。"
        f"主题={topic}，平台={platform}，当前稿件={json.dumps(draft, ensure_ascii=False)}。"
        f"问题={issues}。策略={json.dumps(strategy, ensure_ascii=False)}。"
        f"历史反馈={summarize_feedback(feedback)}。研究资料={json.dumps(research, ensure_ascii=False)}。产品知识={json.dumps(product_knowledge, ensure_ascii=False)}。去重冷却={json.dumps(novelty, ensure_ascii=False)}。内容母版={formula_hint}"
        f"{evidence_rules}"
        f"{single_product_rules}"
        f"{ufm_rules}"
        f"{ufm_contract}"
        "请重写到发布水准："
        "1) 更像真实编辑，不要像AI模板。"
        "2) 结论必须更明确，证据必须更具体，动作必须更可执行。"
        "3) 长文平台补充适合谁、不适合谁、常见误区、执行步骤；短平台补强第一屏冲击力。"
        "4) 删除空话、套话、绝对化结论、不可信承诺。"
        f"5) 正文字数保持在{brief.get('body_range', '平台要求')}。"
        f"6) 语气={brief.get('voice', '')}；CTA={brief.get('conversion', '')}。"
        "7) 不要复用最近已经产出过的标题结构、开头句式和结尾动作。"
        "8) 如果主题是单品评测汇总或新品发布判断，必须主动写清证据口径，不要伪装成亲测。"
        "9) 单品稿里要主动补上“已确认 / 待验证 / 适合谁 / 不适合谁 / 现在买还是等等”。"
        "10) 单品稿至少补足5个具体评测维度，并明确写出和上一代或同品类产品相比的差异。"
        "11) 如果是知乎单品稿，优先用 L0 结论卡 + L1 可比矩阵 + L2 证据与方法附录结构。"
        f"12) {zhihu_rewrite_rule}"
        "13) 输出字段只能是platform,title,hook,body,cta,tags。"
    )


def build_publisher_review_prompt(topic: str, drafts: List[Dict[str, Any]]) -> str:
    return (
        "只输出JSON对象。"
        f"请审校主题={topic}的稿件：{json.dumps(drafts, ensure_ascii=False)}。"
        "输出字段：verdict,platform_reviews,monetization_risks,next_actions。"
        "platform_reviews是数组，每项字段：platform,pass,strongest_selling_point,weak_point,fix_now。"
    )


def build_visual_prompt(topic: str, draft: Dict[str, Any]) -> str:
    platform = str(draft.get("platform", "")).strip()
    brief = PLATFORM_BRIEFS.get(platform, {})
    topic_bucket = _topic_bucket(topic)
    topic_visual_map = {
        "home_cleaning": "真实家居空间、阳光、地面材质、扫地机器人或清洁工具为单一主角，避免办公电脑场景。",
        "pets": "真实宠物生活场景，毛发细节自然，突出宠物和单一用品，不要扭曲肢体。",
        "jewelry_style": "高级配饰特写或穿搭局部，突出珠宝材质和轮廓，不要塑料感皮肤。",
        "sports_outdoor": "真实运动姿态和装备细节，强调人体结构正确，不要多肢体。",
        "digital_gear": "真实数码硬件工业设计线条，主体一件设备即可，接口和屏幕比例必须正确。",
        "tech_ai": "编辑部风格封面或数据可视化感，不要生成无关的扭曲电脑堆叠场景。",
        "general": "围绕主题选择单一主物体和一个辅助证据物，不要默认办公电脑场景。",
    }
    return (
        "只输出JSON对象。"
        f"主题={topic}，平台={platform}，稿件={json.dumps(draft, ensure_ascii=False)}。"
        f"视觉方向={brief.get('visual', 'clean editorial cover')}。"
        f"题材补充={topic_visual_map.get(topic_bucket, topic_visual_map['general'])}"
        "要求：主体真实，结构正确，禁止与主题无关的办公电脑乱入。"
        "如果主题不是数码设备，就不要把电脑当主角。"
        "避免扭曲笔记本、额外按键、融化边缘、畸形屏幕、错位透视、塑料感物体。"
        "输出字段：platform,prompt,negative_prompt,composition,aspect_ratio。"
    )


def optimize_draft(
    topic: str,
    draft: Dict[str, Any],
    strategy: Dict[str, Any],
    feedback: Dict[str, Any],
    research: Dict[str, Any],
    min_score: float,
    max_rewrite_rounds: int,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    current = draft
    score = score_one(current, min_score)
    rounds = 0
    while (not score.pass_gate or score.total_score < 92) and rounds < max_rewrite_rounds:
        rounds += 1
        rewritten = run_agent(
            "content",
            build_rewrite_prompt(topic, current, score, strategy, feedback, research),
            timeout=320,
        )
        obj = extract_json(rewritten)
        if isinstance(obj, list):
            obj = obj[0] if obj else {}
        if not isinstance(obj, dict):
            break
        current = obj
        score = score_one(current, min_score)

    return current, {
        "platform": current.get("platform", ""),
        "score": score.total_score,
        "pass": score.pass_gate,
        "issues": score.issues,
        "subscores": score.subscores,
        "rounds": rounds,
    }


def generate_asset_prompts(topic: str, drafts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assets: List[Dict[str, Any]] = []
    for draft in drafts:
        try:
            payload = run_agent("multimodal", build_visual_prompt(topic, draft), timeout=240)
            parsed = extract_json(payload)
            if isinstance(parsed, dict):
                assets.append(parsed)
            else:
                assets.append({"platform": draft.get("platform", ""), "error": "visual_prompt_not_dict"})
        except Exception as exc:
            assets.append({"platform": draft.get("platform", ""), "error": str(exc)})
    return assets


def fallback_draft(
    topic: str,
    platform: str,
    research: Dict[str, Any] | None = None,
    feedback: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    research = research or {}
    feedback = feedback or {}
    proof_lines = research_evidence_lines(research, limit=3)
    proof_block = research_block(research, limit=2)
    knowledge_lines = knowledge_evidence_lines(topic, limit=6)
    knowledge_block = "\n".join(knowledge_lines).strip()
    tuning_lines = feedback_tuning_lines(platform, feedback)
    tuning_block = "\n\n".join(tuning_lines).strip()
    short_hint = first_research_hint(research)

    if platform == ZH:
        zhihu_format = infer_zhihu_format(topic)
        if zhihu_format == "answer":
            body = (
                f"先回答问题：如果你在问“{topic}”，先别急着找一个万能结论，先把你的使用场景、预算边界和最在意的风险点说清楚。"
                "\n\n更稳的判断顺序是：先给结论，再给边界条件，再给证据，再给行动建议。"
                "\n\n真正让知乎回答有价值的，不是说得多，而是看完之后，读者能不能立刻知道自己该怎么判断。"
                "\n\n如果这个问题涉及消费决策，就优先把预算段、使用场景和品牌差异拆开。"
                "\n\n如果这个问题涉及方法或观点，就优先把适合谁、不适合谁、常见误区和执行顺序说清楚。"
            )
        else:
            body = (
                f"先给答案：看{topic}这类内容，先按预算段和使用场景做第一轮筛选，再看品牌和型号差异，比直接抄推荐更稳。"
                "\n\n这类专栏真正要解决的，不是把所有产品都讲一遍，而是让读者快速缩小决策范围。"
                "\n\n更有效的正文顺序是：先给直接答案，再拆预算分段，再拆使用场景，再讲品牌或型号差异，最后给不推荐情况和结论清单。"
                "\n\n如果一篇稿子只有泛泛的避坑和感受，没有预算段、场景段和结论表，读者通常收藏不了，也很难形成搜索承接。"
                "\n\n所以知乎长文要优先做成能被搜索、能被收藏、也能被后续转化承接的决策型内容。"
            )
        if proof_block:
            body += "\n\n" + proof_block
        if knowledge_block:
            body += "\n\n产品判断线索：\n" + knowledge_block
        body += (
            "\n\n来源说明：优先参考公开评测、公开资料、长期追评和多平台重复出现的用户反馈。"
            "\n\n执行提醒：正文里至少保留一个直接答案、一个选择标准、一个不推荐情况和一个结论清单。"
        )
        if tuning_block:
            body += "\n\n" + tuning_block
        return {
            "platform": ZH,
            "title": f"{topic}：不同需求的人到底应该怎么判断？" if infer_zhihu_format(topic) == "answer" else f"{topic}：不同预算和使用场景到底怎么选？",
            "hook": f"先回答问题：看{topic}，先定边界条件，再看结论。" if infer_zhihu_format(topic) == "answer" else f"先给答案：看{topic}，不要先被参数表带跑，先按预算、场景和品牌差异筛。",
            "body": body,
            "cta": "如果你要我把结论清单整理成表，评论区留“清单”。",
            "tags": [topic, "知乎长文", "决策指南"],
        }
    if platform == XHS:
        body_lines = [
            f"??????{topic}????",
            "????????????????????1??????????????",
            "??1???????",
            "??3?????????????",
            "?????1??????",
            "???????????7?????????????",
            "????????????????????????",
            f"?????????????????????{short_hint}",
            "?????????????????????????",
        ]
        if tuning_lines:
            body_lines.append(tuning_lines[0])
        return {
            "platform": XHS,
            "title": f"{topic}?????????????????",
            "hook": f"??????{topic}????1??????10???????",
            "body": "\n".join(body_lines),
            "cta": "????????????????????????",
            "tags": [topic, "????", "????"],
        }
    if platform == WB:
        body_parts = [
            f"???????{topic}??????????????????????????????????",
            "???????????????????????????",
            "?????????????????????????????????",
            f"????????????????{short_hint}",
        ]
        return {
            "platform": WB,
            "title": f"{topic}??????????????????",
            "hook": f"?{topic}????????????????????",
            "body": "\n".join(body_parts),
            "cta": "?????????????????",
            "tags": [topic, "??", "????"],
        }
    if platform == WX:
        body = (
            f"???????{topic}????????????????????????????????????????????????"
            "\n\n??????????????????????????????????"
            "\n\n????????????????????????????????????????"
            "\n\n?????????????????????????????????? CTA???????????????????"
            "\n\n???????????????????????????????????????????????????????????"
            "??????????????????????????????????????????????????????????????????????????????????"
            "\n\n???????????????????????????????????????????????????????"
            "?????????????????????????????????????????????????"
        )
        if proof_block:
            body += "\n\n??????????????????????????\n\n" + proof_block
        body += (
            "\n\n????????????????????????????????????????????????????????????????????"
            "\n\n????????7????????1?????? Hook??2??????3??????4???????5????????6?????? CTA??7???????????????"
            "\n\n??????????????????????????????????????????????"
        )
        if tuning_block:
            body += "\n\n" + tuning_block
        return {
            "platform": WX,
            "title": f"{topic}??????????????????????",
            "hook": f"????{topic}???????????????????????????",
            "body": body,
            "cta": "?????????????????????????????",
            "tags": [topic, "???", "????"],
        }
    if platform == TT:
        body = (
            f"?????{topic}???????????????????????????????????"
            "\n\n?????????????????????????????????????????????????????????"
            "\n\n??????????????????????????????????????????????"
            "\n\n???????????????????????????????????????????????????????"
            "\n\n??????????????????????????????????????????????????????????????????????????????????????????"
        )
        if proof_block:
            body += "\n\n????????????????????????????\n\n" + proof_block
        body += (
            "\n\n?????????????????????????????????"
            "?????????????????????????"
        )
        if tuning_block:
            body += "\n\n" + tuning_block
        return {
            "platform": TT,
            "title": f"{topic}??????????????????????",
            "hook": f"????{topic}???????????????????????????",
            "body": body,
            "cta": "????????????????????",
            "tags": [topic, "???", "????"],
        }
    if platform == DY:
        body = (
            "?????????????????????????????????\n"
            "?????????????????\n"
            "??????????????\n"
            "???????????????????\n"
            "????????????\n"
            f"{short_hint}"
        )
        return {
            "platform": DY,
            "title": f"{topic}??????",
            "hook": f"???????{topic}??????????",
            "body": body,
            "cta": "????????111???????????",
            "tags": [topic, "????", "????"],
        }
    if platform == XG:
        body = (
            f"???????{topic}?????????????????????????3?8??????????"
            "??????????????????????????????????????????????????????????"
            "\n\n?????????????????????????????????????????????????????????????????????????????????"
            "\n\n????????????????????????????????????????????????????????????????"
        )
        if proof_lines:
            body += "\n\n" + proof_lines[0]
        return {
            "platform": XG,
            "title": f"{topic}????????????????????",
            "hook": f"????{topic}????????????????????????????????",
            "body": body,
            "cta": "???????????????????????????",
            "tags": [topic, "????", "????"],
        }
    body = (
        f"?????{topic}???????????????????????????????????????????"
        "?????????????????????????????????????????????????"
        "\n\n???????????????????????????????????????????"
        "????????????????????????????"
    )
    if proof_lines:
        body += "\n\n" + proof_lines[0]
    return {
        "platform": BILI,
        "title": f"{topic}?????????????",
        "hook": f"????{topic}???????????????????????????????",
        "body": body,
        "cta": "???????????????????????????????",
        "tags": [topic, "????", "??"],
    }


def fallback_init_drafts(
    topic: str,
    platforms: List[str],
    research: Dict[str, Any] | None = None,
    feedback: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    return [fallback_draft(topic, platform, research=research, feedback=feedback) for platform in platforms]




def strip_visual_noise(text: str, keep_small: bool) -> str:
    current = (text or "").replace("\r", "").strip()
    current = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", current)
    if not keep_small:
        current = EMOJI_BROAD_RE.sub("", current)
    current = re.sub(r"[ \t]{2,}", " ", current)
    current = re.sub(r"\n{3,}", "\n\n", current)
    return current.strip()


def scrub_claims(text: str) -> str:
    current = text
    for pattern, replacement in CLAIM_REPLACEMENTS:
        current = re.sub(pattern, replacement, current)
    current = re.sub(
        r"过去一年我系统整理了([^，。\n]{6,120})，结合公开评测数据和真实使用场景",
        r"过去一年我系统整理了\1的公开评测、追评和用户反馈，结合真实使用场景",
        current,
    )
    current = re.sub(
        r"我对比整理了([^，。\n]{6,120})，结合公开评测数据和真实使用场景",
        r"我对比整理了\1的公开评测、追评和用户反馈，结合真实使用场景",
        current,
    )
    current = re.sub(
        r"实测(\d+\+?款)",
        r"整理\1公开评测和用户反馈",
        current,
    )
    current = re.sub(
        r"我把([^，。！？\n]{4,80})全试了一遍",
        r"我把\1的公开评测、追评和用户反馈系统整理了一遍",
        current,
    )
    current = re.sub(
        r"花了([^，。！？\n]{0,20})实测上百台([^，。！？\n]{2,80})后",
        r"花了\1整理上百份\2公开评测和用户反馈后",
        current,
    )
    return current


def ensure_source_signal(platform: str, body: str) -> str:
    keys = ["来源", "实测", "测试环境", "官方", "链接", "benchmark", "review"]
    if any(key in body for key in keys):
        return body
    if platform in {ZH, WX, TT, XHS, WB}:
        line = "来源说明：这里的判断优先参考公开资料、公开教程和测试环境里反复出现的做法。"
    else:
        line = "测试环境说明：这段内容优先参考公开教程、实测反馈和常见案例。"
    return (body.strip() + "\n\n" + line).strip()


def ensure_actionability_blocks(platform: str, body: str) -> str:
    if platform not in LONGFORM_PLATFORMS:
        return body
    markers = ["步骤", "误区", "适合谁", "不适合谁", "建议", "案例", "清单", "第一步", "第二步", "第三步"]
    count = sum(1 for marker in markers if marker in body)
    if count >= 3:
        return body
    addon = (
        "步骤清单：第一步先定场景，第二步定判断标准，第三步定资料入口。"
        "\n案例提醒：先把一个真实场景写透，再扩工具组合。"
        "\n执行建议：一轮只改标题、案例或结尾动作里的一个变量。"
    )
    return (body.strip() + "\n\n" + addon).strip()


def improve_readability_flow(body: str) -> str:
    paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
    rewritten: List[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= 42:
            rewritten.append(paragraph)
            continue
        pieces = [piece.strip() for piece in re.split(r"(?<=，)|(?<=；)|(?<=：)", paragraph) if piece.strip()]
        if len(pieces) <= 1:
            rewritten.append(paragraph)
            continue
        current = ""
        for piece in pieces:
            candidate = (current + piece).strip()
            if current and len(candidate) > 34:
                rewritten.append(current.strip())
                current = piece
            else:
                current = candidate
        if current:
            rewritten.append(current.strip())
    return "\n".join(rewritten).strip()


def dedupe_body_blocks(body: str) -> str:
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    seen = set()
    kept: List[str] = []
    for line in lines:
        key = re.sub(r"\s+", "", line)
        if len(key) >= 8 and key in seen:
            continue
        seen.add(key)
        kept.append(line)
    return "\n".join(kept).strip()


def strip_research_trace_lines(body: str) -> str:
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    blocked_prefixes = ("资料线索", "研究线索", "来源线索")
    kept: List[str] = []
    for line in lines:
        if line.startswith(blocked_prefixes):
            continue
        if re.match(r"^[\-•]\s*(资料线索|研究线索|来源线索)", line):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def normalize_case_story(body: str) -> str:
    current = body
    current = re.sub(r"【一个真实案例】", "【一个常见场景】", current)
    current = re.sub(r"【真实案例】", "【常见场景】", current)
    current = re.sub(
        r"我同事是([^，。\n]{4,80})，之前花(\d+)([^，。\n]{0,24})买了([^，。\n]{2,80})，结果[:：]?",
        r"常见场景之一是\1，之前在预算约\2\3的情况下买了\4，结果很容易遇到这些问题：",
        current,
    )
    current = re.sub(r"我是从\d{4}年开始研究[^。！？\n]{0,120}[。！？]?", "这类产品在公开评测和长期追评里反复暴露出同一批问题。", current)
    current = re.sub(r"我跟风买了", "很多人跟风买了", current)
    current = re.sub(r"后来按四步重新选了一遍", "后来按四步重新筛了一遍", current)
    current = re.sub(r"三个月后，他说现在", "按这套方法调整后三个月，常见反馈是", current)
    current = re.sub(r"三个月后，她说现在", "按这套方法调整后三个月，常见反馈是", current)
    current = re.sub(r"我家([^，。\n]{2,40})", r"家庭场景里\1", current)
    return current


def strip_meta_prefixes(text: str) -> str:
    current = text.strip()
    current = re.sub(r"^(Hook|HOOK)\s*[:：?？]\s*", "", current)
    current = re.sub(r"^(CTA)\s*[:：?？]\s*", "", current)
    current = re.sub(r"^(Tags?)\s*[:：?？]\s*", "", current)
    return current.strip()


def enforce_publish_safe_evidence(platform: str, key: str, text: str) -> str:
    current = strip_meta_prefixes(text)
    current = scrub_claims(current)
    current = re.sub(
        r"^实测(\d+\+?[款台篇份]?)[^，。！？\n]{0,40}后",
        r"整理\1公开评测和用户反馈后",
        current,
    )
    current = re.sub(
        r"^花了[^，。！？\n]{0,20}实测上百台([^，。！？\n]{2,80})后",
        r"整理上百份\1公开评测和用户反馈后",
        current,
    )
    current = re.sub(
        r"我把([^，。！？\n]{4,80})全试了一遍",
        r"我把\1的公开评测、追评和用户反馈系统整理了一遍",
        current,
    )
    current = re.sub(r"我从\d{4}年开始研究[^。！？\n]{0,120}[。！？]?", "过去几年公开评测和用户反馈里反复出现的问题是：", current)
    current = re.sub(r"\b亲测\b", "对比整理", current)
    if key == "body":
        current = strip_research_trace_lines(current)
        current = normalize_case_story(current)
    if key in {"title", "hook"}:
        current = current.replace("实测分享", "对比拆解")
    return current.strip()


def strip_generic_tail_blocks(platform: str, body: str) -> str:
    if platform != ZH:
        return body
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    has_specific_section = any(marker in body for marker in ["【这篇文章适合谁】", "【三个致命误区】", "【执行步骤】"])
    if not has_specific_section:
        return body
    blocked_prefixes = [
        "适合谁：如果你现在最大的痛点",
        "不适合谁：如果你只想一次性找个万能工具",
        "常见误区：先买工具、后找场景",
        "可执行步骤：第一步定场景",
        "落地建议：把今天要做的动作写成清单",
    ]
    kept = [line for line in lines if not any(line.startswith(prefix) for prefix in blocked_prefixes)]
    return "\n".join(kept).strip()


def has_placeholder_noise(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    return stripped.count("?") >= max(3, len(stripped) // 5)


def clean_meta_template(topic: str, platform: str) -> Dict[str, Any]:
    formula = infer_content_formula(topic, platform)
    if platform == ZH and formula == "single_product_review":
        return {
            "title": f"{topic}：基于公开资料、媒体上手和首批反馈，现在到底值不值得看？",
            "hook": f"先给结论：看{topic}这类单品内容，不要假装自己已经深度实测，先把公开信息、媒体上手和首批反馈拆清楚更重要。",
            "cta": "如果你要我把这款产品和同价位替代项再做一张对照表，评论区留“对照”。",
            "tags": [topic, "单品评测", "公开资料汇总"],
        }
    if platform == ZH and formula == "launch_roundup":
        return {
            "title": f"{topic}：发布后首轮信息汇总，这次最值得关注和最该谨慎看的是什么？",
            "hook": f"先给判断：看{topic}这类新品稿，重点不是复述发布会，而是拆出真正影响购买决策的变化。",
            "cta": "如果你要我把这次升级点和观望点整理成一张表，评论区留“清单”。",
            "tags": [topic, "新品发布", "首轮判断"],
        }
    if is_buying_guide_topic(topic):
        zhihu_format = infer_zhihu_format(topic)
        guide_map: Dict[str, Dict[str, Any]] = {
            ZH: {
                "title": f"{topic}：不同需求的人到底该怎么选？" if zhihu_format == "answer" else f"{topic}：不同预算、不同场景到底怎么选？",
                "hook": f"先回答问题：看{topic}，先定你的使用边界，再看推荐。" if zhihu_format == "answer" else f"先给答案：看{topic}这类内容，不要先被参数表带跑，先按预算、场景和品牌差异筛一轮。",
                "cta": "如果你要我把判断顺序和结论清单整理成一张表，评论区留“清单”。" if zhihu_format == "answer" else "如果你要我把预算段、场景段和品牌差异整理成一张表，评论区留“清单”。",
                "tags": [topic, "知乎回答", "决策判断"] if zhihu_format == "answer" else [topic, "选购指南", "品牌对比", "预算分段"],
            },
            WX: {
                "title": f"{topic}：普通家庭真正该看的不是参数，而是预算、场景和品牌差异",
                "hook": f"如果你正在看{topic}，先别急着刷排行榜，先把预算段、家庭场景和品牌差异分清楚。",
                "cta": "文末回复“清单”，领取预算段和使用场景对照表。",
                "tags": [topic, "选购指南", "品牌对比", "清单"],
            },
            TT: {
                "title": f"{topic}：预算、品牌、场景一次讲清，别再乱买了",
                "hook": f"很多人做{topic}只看宣传页参数，最后买回家才发现根本不适合自己。",
                "cta": "先收藏这篇，要预算和场景对照表再看评论区置顶。",
                "tags": [topic, "选购指南", "品牌对比"],
            },
        }
        if platform in guide_map:
            return guide_map[platform]
    mapping: Dict[str, Dict[str, Any]] = {
        ZH: {
            "title": f"{topic}别再只堆工具了：真正能长期用下去的是这套判断标准",
            "hook": f"做{topic}最容易踩坑的，不是工具不够多，而是你根本没有判断标准。",
            "cta": "如果你要我把这套判断标准整理成对照表，评论区留“清单”，我把快用版发你。",
            "tags": [topic, "经验拆解", "效率提升"],
        },
        XHS: {
            "title": f"{topic}别再做复杂了｜先把这份快用清单跑顺",
            "hook": f"先看结论：做{topic}，先跑顺1个场景，比堆10个工具更有用。",
            "cta": "收藏这条，评论区留“清单”，我把快用版结构发你。",
            "tags": [topic, "收藏清单", "效率工具"],
        },
        WB: {
            "title": f"{topic}别再凭感觉做了，这里给你一版快用判断",
            "hook": f"做{topic}最容易翻车的，不是没工具，而是顺序反了。",
            "cta": "评论区留“清单”，我把快用版发你。",
            "tags": [topic, "快评", "内容变现"],
        },
        WX: {
            "title": f"{topic}怎么做成能涨关注的深度稿：先把承接结构搭起来",
            "hook": f"如果你做{topic}只追阅读量，不管承接，大概率是流量有了，关注却接不住。",
            "cta": "文末回复“资料”，领取这套可直接套用的文章结构和清单模板。",
            "tags": [topic, "资料包", "内容策略"],
        },
        TT: {
            "title": f"{topic}别再乱做了：真正能拿结果的，是这套长图文结构",
            "hook": f"很多人做{topic}越写越长却越没人看，问题不是内容少，而是结构顺序错了。",
            "cta": "先收藏这篇，要对照版清单再看评论区置顶。",
            "tags": [topic, "长图文", "避坑指南"],
        },
        DY: {
            "title": f"{topic}别再做复杂了",
            "hook": f"别再踩坑了，做{topic}，你第一步就做反了。",
            "cta": "关注我，评论区扣111，我把快用版清单发你。",
            "tags": [topic, "效率提升", "工具组合"],
        },
        XG: {
            "title": f"{topic}别再碎片化做了：更稳的是这条横屏母体结构",
            "hook": f"很多人做{topic}越做越累，不是内容少，而是没有一条真正能承载完整信息的母体视频。",
            "cta": "先收藏本集，按简介里的结构把你的第一条母体视频搭起来。",
            "tags": [topic, "横屏视频", "实测演示"],
        },
        BILI: {
            "title": f"{topic}完整拆解：为什么你越做越乱",
            "hook": f"如果你做{topic}总觉得内容很多却留不住人，问题往往不是信息不够，而是顺序错了。",
            "cta": "如果你觉得有帮助，一键三连，评论区留“模板”，我把整理版发你。",
            "tags": [topic, "实测分享", "教程"],
        },
    }
    return mapping.get(platform, {"title": topic, "hook": "", "cta": "", "tags": [topic]})


def clean_blueprint_blocks(topic: str, platform: str) -> List[str]:
    formula = infer_content_formula(topic, platform)
    if platform == ZH and formula == "single_product_review":
        return [
            f"先给结论：写{topic}这种单品稿，先写清楚信息来源来自官方资料、媒体上手和首批公开反馈，不要伪装成亲测。",
            "文章骨架：第一段给总体判断，第二段讲这款产品最值得关注的变化，第三段讲适合谁，第四段讲不适合谁，第五段讲目前仍然不确定或需要再观察的点。",
            "必须回答：它解决了什么问题、相比同价位替代项强在哪、现在适不适合买、哪些结论还需要继续观察。",
            "结尾要明确：建议现在买、继续观望，还是只推荐给特定人群。",
        ]
    if platform == ZH and formula == "launch_roundup":
        return [
            f"先给结论：写{topic}这类新品发布稿，重点不是复述发布会，而是拆出真正影响购买决策的变化。",
            "文章骨架：第一段讲发布会后的总体判断，第二段讲升级点，第三段讲争议点，第四段讲适合谁，第五段讲建议现在买还是等等。",
            "必须回答：这次到底升级了什么、哪些升级是实质性的、哪些仍然要等真实评测、哪些用户会真正受益。",
            "结尾必须明确：是值得马上关注、可以观望，还是只适合部分人群。",
        ]
    if is_buying_guide_topic(topic) and platform == ZH:
        kb = build_product_knowledge_blocks(topic)
        if infer_zhihu_format(topic) == "answer":
            return [
                f"先回答问题：如果你在问“{topic}”，先把预算、家庭场景和最在意的风险点说清楚，再看推荐。",
                "回答骨架：第一段直接回答，第二段给判断边界，第三段拆预算和场景，第四段讲品牌或型号差异，第五段给不推荐情况和结论清单。",
                f"必须回答：什么人适合、什么人不适合、最容易误判的点是什么、看完后第一步该做什么。核心判断维度={kb.get('factors', '预算、场景、品牌、长期成本')}。",
                "回答要像高赞长答，不要像营销专栏。重点是直接解答问题，而不是泛泛铺垫。",
            ]
        return [
            f"先给答案：做{topic}这类选购题，先按预算和家庭场景筛，再看品牌和型号差异，不要先被参数表带跑。",
            "文章骨架：第一段给直接结论，第二段拆预算分段，第三段讲家庭场景，第四段讲品牌或型号差异，第五段给不推荐情况和总结表。",
            f"必须回答：不同预算带适合谁、不同使用场景优先看什么、不同品牌或系列差异是什么。核心判断维度={kb.get('factors', '预算、场景、品牌、长期成本')}。",
            "必须有推荐和不推荐：不是所有人都适合同一台机器，正文里要明确什么人该看什么、什么人不该买什么。",
            "结尾要有一张总结表或结论清单，让读者看完能直接缩小决策范围。",
        ]
    if is_buying_guide_topic(topic) and platform == WX:
        return [
            f"这篇{topic}不是泛泛聊方法，而是要帮读者缩短购买决策路径。",
            "正文顺序：先给直接答案，再拆预算带，再拆家庭场景，再补品牌差异和不推荐情况。",
            "中段必须出现预算段、场景段、品牌段三块内容，不然读者看完仍然无法决策。",
            "文末只保留一个资料入口，例如预算和场景对照表。",
        ]
    if is_buying_guide_topic(topic) and platform == TT:
        return [
            f"{topic}这类内容想拿阅读量，前几段就要把预算、品牌、适合谁说清楚。",
            "真正能留住人的不是空泛避坑，而是看完就知道自己该排除哪些型号。",
            "正文里必须有预算分层、品牌差异、适用场景和不推荐情况。",
            "结尾要有一句明确判断和一张结论清单。",
        ]
    if platform == ZH:
        return [
            f"适合谁：如果你正在围绕{topic}做内容，但信息很多、落地很少，这类结构会更适合你。",
            "不适合谁：如果你只想找一个万能模板，而不愿意按自己的场景拆步骤，这套方法帮助有限。",
            "常见误区：先买工具、后定场景；先堆资料、后做判断；先做复杂系统、后验证最小结果。",
            "可执行步骤：第一步定场景，第二步定判断标准，第三步只保留一个复盘指标。",
            "落地建议：把今天要做的动作写成清单，再决定哪些环节值得自动化。",
        ]
    if platform == XHS:
        return [
            f"别一上来就把{topic}做复杂。",
            "先做一版今天就能用的小清单，比讲一堆概念更容易被收藏。",
            "按公开资料和测试环境的常见做法看，先锁定1个场景、3个动作、1个领取入口，这样更稳。",
        ]
    if platform == WB:
        return [
            f"围绕{topic}做内容，最容易翻车的不是没热点，而是把动作做复杂了。",
            "更稳的顺序是先给结论，再给三条证据，最后只留一个互动动作。",
            "如果一条微博里同时塞链接、主页、私信和商品卡，点击会被明显分散。",
        ]
    if platform == WX:
        return [
            f"适用场景：如果你想把{topic}做成能持续转化的公众号内容，文章必须承担解释、筛选和承接三层任务。",
            "常见误区：只讲观点，不给动作；一篇文章同时塞多个 CTA；标题很猛，正文却没有细节支撑。",
            "执行顺序：先用前200字下判断，再讲三个最常见误区，中段给三步执行顺序，尾段只保留一个资料入口。",
            "案例补强：哪怕只补一个真实使用场景，也会比纯观点更容易获得关注。",
        ]
    if platform == TT:
        return [
            f"{topic}这类内容在头条真正拿结果，靠的是长文耐读性，不是靠标题单点拉点击。",
            "前3段必须把总判断、最常见误区和执行顺序说清楚，不然阅读时长起不来。",
            "更稳的结构是1个总判断、3个误区、3步执行、1个对照清单、1个动作。",
            "如果你能补一个小案例，读者会更容易从阅读进入收藏。",
        ]
    return [
        f"围绕{topic}这类内容，最有效的不是堆信息，而是让用户跟得上你的步骤。",
        "先讲结论，再讲证据，再给动作，整体转化会稳得多。",
    ]


def remove_placeholder_paragraphs(text: str) -> str:
    kept: List[str] = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if has_placeholder_noise(line):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def ensure_lead_block(topic: str, platform: str, body: str) -> str:
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    if not lines:
        return body
    first = lines[0]
    if first.startswith("资料线索") or ".com" in first or ".net" in first:
        lead = "\n".join(clean_blueprint_blocks(topic, platform)[:2]).strip()
        if lead:
            return (lead + "\n\n" + body).strip()
    return body


def ensure_zhihu_frontload(topic: str, platform: str, body: str) -> str:
    if platform != ZH:
        return body
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    if not lines:
        return body
    head = "\n".join(lines[:4])
    if is_buying_guide_topic(topic):
        required = [
            f"先给答案：看{topic}这类内容，先按预算段和使用场景做第一轮筛选，再看品牌和型号差异，效率最高。",
            "适合谁：预算明确、希望缩小决策范围、愿意花几分钟读完一篇再决定的人。",
            "不适合谁：只想找一个万能答案、完全不做家庭场景判断的人。",
        ]
    else:
        required = [
            f"先给结论：如果你在做{topic}，先看判断标准和适合人群，再看具体型号或工具清单，通常比直接抄推荐更不容易踩坑。",
            "适合谁：预算有限、想少走弯路、需要一篇文章就完成初筛的人最适合先按这套顺序看。",
            "不适合谁：只想找一个万能答案、不愿意自己做最后一轮取舍的人，任何推荐清单都帮不了你到底。",
        ]
    missing = [line for line in required if line[:6] not in head]
    if not missing:
        return body
    return ("\n\n".join(missing) + "\n\n" + body.strip()).strip()


def ensure_zhihu_high_value_structure(topic: str, platform: str, body: str) -> str:
    if platform != ZH or not is_buying_guide_topic(topic):
        return body
    knowledge_lines = knowledge_evidence_lines(topic, limit=8)
    kb = build_product_knowledge_blocks(topic)
    series_table = build_series_markdown_table(topic)
    if infer_zhihu_format(topic) == "answer":
        required_blocks = [
            (
                "一、先给直接回答",
                f"一、先给直接回答\n如果你在问“{topic}”，更稳的做法不是先找唯一推荐，而是先按预算、使用场景和主要风险点做一轮排除。",
            ),
            (
                "二、边界条件先说清",
                "二、边界条件先说清\n预算不同、户型不同、是否养宠、是否愿意维护，这些边界条件会直接决定答案是否成立。",
            ),
            (
                "三、再看品牌和型号差异",
                "三、再看品牌和型号差异\n品牌解决的是长期信任和售后，型号解决的是具体能力和是否适合你。",
            ),
            (
                "四、系列怎么缩圈",
                f"四、系列怎么缩圈\n{kb.get('series', '- 先按品牌定位缩到系列，再看具体型号。')}",
            ),
            (
                "五、哪些情况别盲买",
                f"五、哪些情况别盲买\n{kb.get('avoid', '- 如果你只看参数宣传、不看长期成本和使用边界，很容易买到不适合自己的型号。')}",
            ),
            (
                "六、最后给结论清单",
                "六、最后给结论清单\n- 先定预算\n- 再定场景\n- 然后看品牌\n- 再缩到系列\n- 最后只留下一个最适合自己的候选",
            ),
        ]
        if kb.get("budget"):
            required_blocks[1] = ("二、边界条件先说清", f"二、边界条件先说清\n{kb.get('budget')}")
        if kb.get("brands"):
            required_blocks[2] = ("三、再看品牌和型号差异", f"三、再看品牌和型号差异\n{kb.get('brands')}")
        current = body.strip()
        for marker, block in required_blocks:
            if marker not in current:
                current = (current + "\n\n" + block).strip()
        if series_table and "| 品牌 | 系列 |" not in current:
            current = (current + "\n\n系列对照表\n" + series_table).strip()
        if knowledge_lines and "品牌定位参考" not in current:
            current = (current + "\n\n品牌定位参考\n" + "\n".join(f"- {line}" for line in knowledge_lines[:4])).strip()
        return current
    required_blocks = [
        (
            "一、先按预算段缩小范围",
            f"一、先按预算段缩小范围\n{kb.get('budget', '- 先按价格带分层，再看每个价格带最值得保留的能力。')}",
        ),
        (
            "二、再按使用场景筛",
            f"二、再按使用场景筛\n{kb.get('scenarios', '- 先按使用场景分类，再看每个场景最重要的能力。')}",
        ),
        (
            "三、品牌和型号差异怎么看",
            f"三、品牌和型号差异怎么看\n{kb.get('brands', '- 先看品牌定位，再看同价位型号差异。品牌解决信任问题，型号解决适配问题。')}",
        ),
        (
            "四、系列怎么缩圈",
            f"四、系列怎么缩圈\n{kb.get('series', '- 先按品牌定位缩到系列，再看具体型号。')}",
        ),
        (
            "五、哪些情况不建议买",
            f"五、哪些情况不建议买\n{kb.get('avoid', '- 如果你只看参数、不看长期成本和场景边界，这类购买大概率会后悔。')}",
        ),
        (
            "最后给一张结论清单",
            "最后给一张结论清单\n- 先定预算\n- 再定场景\n- 然后看品牌\n- 再缩到系列\n- 最后才看具体型号\n- 只保留一个最适合你的备选清单",
        ),
    ]
    current = body.strip()
    for marker, block in required_blocks:
        if marker not in current:
            current = (current + "\n\n" + block).strip()
    if series_table and "| 品牌 | 系列 |" not in current:
        current = (current + "\n\n系列对照表\n" + series_table).strip()
    if knowledge_lines and "品牌定位参考" not in current:
        current = (current + "\n\n品牌定位参考\n" + "\n".join(f"- {line}" for line in knowledge_lines[:5])).strip()
    return current


def compress_zhihu_repeat_blocks(topic: str, platform: str, body: str) -> str:
    if platform != ZH:
        return body
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    deduped: List[str] = []
    seen = set()
    noisy_prefixes = ("先给答案：", "必须回答：", "文章骨架：", "回答骨架：")
    for line in lines:
        key = line
        if key in seen:
            continue
        if any(line.startswith(prefix) for prefix in noisy_prefixes) and any(existing.startswith(prefix) for prefix in noisy_prefixes for existing in deduped):
            if line in deduped:
                continue
        seen.add(key)
        deduped.append(line)
    text = "\n".join(deduped).strip()
    text = re.sub(r"(?:\n)?必须回答：\n(?:必须回答：\n)+", "\n必须回答：\n", text)
    text = re.sub(r"(?:\n)?先给答案：\n(?:先给答案：\n)+", "\n先给答案：\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def ensure_tag_density(topic: str, platform: str, tags: Iterable[Any]) -> List[str]:
    cleaned = [strip_visual_noise(scrub_claims(str(tag)), keep_small=True) for tag in tags if str(tag).strip()]
    fallback_map = {
        ZH: [topic, "选购指南", "品牌对比", "预算分段"] if is_buying_guide_topic(topic) else [topic, "经验拆解", "效率提升"],
        XHS: [topic, "收藏清单", "效率工具"],
        WB: [topic, "快评", "内容变现"],
        WX: [topic, "资料包", "内容策略"],
        TT: [topic, "长图文", "避坑指南"],
        DY: [topic, "效率提升", "工具组合"],
        XG: [topic, "横屏视频", "实测演示"],
        BILI: [topic, "实测分享", "教程"],
    }
    for tag in fallback_map.get(platform, [topic]):
        if tag not in cleaned:
            cleaned.append(tag)
    return cleaned[:6]


def article_blueprint(
    topic: str,
    platform: str,
    research: Dict[str, Any] | None = None,
    feedback: Dict[str, Any] | None = None,
) -> List[str]:
    research = research or {}
    feedback = feedback or {}
    proof_lines = research_evidence_lines(research, limit=2)
    tuning_lines = feedback_tuning_lines(platform, feedback)

    if platform == ZH:
        blocks = [
            f"???????{topic}????????????????????????????????",
            "??????????????????????????????",
            "?????????????????????????????????????????????????????",
            "????????????3???????????????????",
            "???????????????????????????????????",
        ]
    elif platform == XHS:
        blocks = [
            f"??????{topic}????",
            "???????????????????????????",
            "????????????????????1????3????1?????????????",
        ]
    elif platform == WB:
        blocks = [
            f"??{topic}??????????????????????????",
            "?????????????????????????????",
            "????????????????????????????????",
        ]
    elif platform == WX:
        blocks = [
            f"?????{topic}??????????????????????",
            "?????????????????????????????????????",
            "???????????????????????????????????",
            "???????????????????????????????????",
            "????????????????????????????",
        ]
    elif platform == TT:
        blocks = [
            f"{topic}?????????????????????????????????",
            "?3????????????????????????????????",
            "??????1?????3????3????1??????1????",
            "?????????????????????????",
        ]
    else:
        blocks = [
            f"??{topic}????????????????????????????",
            "?????????????????????????????",
            "?????????????????????????????????",
        ]

    blocks.extend(proof_lines)
    blocks.extend(tuning_lines)
    return blocks


def extend_body_if_needed(
    platform: str,
    topic: str,
    body: str,
    research: Dict[str, Any] | None = None,
    feedback: Dict[str, Any] | None = None,
) -> str:
    current = body.strip()
    minimum = int(PLATFORM_BRIEFS.get(platform, {}).get("min_body", 0))
    if len(current) >= minimum:
        return current

    blocks = clean_blueprint_blocks(topic, platform)
    blocks.extend(research_evidence_lines(research or {}, limit=2))
    blocks.extend(feedback_tuning_lines(platform, feedback or {}))
    idx = 0
    while len(current) < minimum and blocks:
        current = (current + "\n\n" + blocks[idx % len(blocks)]).strip()
        idx += 1
        if idx > 14:
            break
    return current


def sanitize_draft(
    topic: str,
    draft: Dict[str, Any],
    research: Dict[str, Any] | None = None,
    feedback: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    platform = str(draft.get("platform", "")).strip()
    zhihu_format = infer_zhihu_format(topic) if platform == ZH else ""
    keep_small = platform in {XHS, DY}
    cleaned = dict(draft)
    meta = clean_meta_template(topic, platform)

    for key in ["title", "hook", "body", "cta"]:
        value = str(cleaned.get(key, "")).strip()
        value = enforce_publish_safe_evidence(platform, key, value)
        value = strip_visual_noise(value, keep_small=keep_small)
        if key == "body":
            value = remove_placeholder_paragraphs(value)
        elif has_placeholder_noise(value):
            value = str(meta.get(key, "")).strip()
        cleaned[key] = value

    cleaned["body"] = extend_body_if_needed(
        platform,
        topic,
        str(cleaned.get("body", "")),
        research=research,
        feedback=feedback,
    )
    cleaned["body"] = ensure_lead_block(topic, platform, str(cleaned.get("body", "")))
    cleaned["body"] = ensure_zhihu_frontload(topic, platform, str(cleaned.get("body", "")))
    cleaned["body"] = ensure_zhihu_high_value_structure(topic, platform, str(cleaned.get("body", "")))
    cleaned["body"] = ensure_source_signal(platform, str(cleaned.get("body", "")))
    cleaned["body"] = ensure_actionability_blocks(platform, str(cleaned.get("body", "")))
    cleaned["body"] = improve_readability_flow(str(cleaned.get("body", "")))
    cleaned["body"] = dedupe_body_blocks(str(cleaned.get("body", "")))
    cleaned["body"] = compress_zhihu_repeat_blocks(topic, platform, str(cleaned.get("body", "")))
    cleaned["body"] = strip_generic_tail_blocks(platform, str(cleaned.get("body", "")))
    if len(str(cleaned.get("body", ""))) < int(PLATFORM_BRIEFS.get(platform, {}).get("min_body", 0)):
        cleaned["body"] = extend_body_if_needed(
            platform,
            topic,
            str(cleaned.get("body", "")),
            research=research,
            feedback=feedback,
        )
        cleaned["body"] = compress_zhihu_repeat_blocks(topic, platform, str(cleaned.get("body", "")))
    cleaned["body"] = enforce_publish_safe_evidence(platform, "body", str(cleaned.get("body", "")))
    tags = cleaned.get("tags", [])
    if not isinstance(tags, list) or any(has_placeholder_noise(str(tag)) for tag in tags):
        tags = meta.get("tags", [topic])
    cleaned["tags"] = ensure_tag_density(topic, platform, tags)
    if zhihu_format:
        cleaned["zhihu_format"] = zhihu_format
    return cleaned




def fallback_review(drafts: List[Dict[str, Any]], min_score: float) -> Dict[str, Any]:
    rows = []
    for draft in drafts:
        scored = score_one(draft, min_score)
        rows.append(
            {
                "platform": draft.get("platform", ""),
                "pass": scored.pass_gate,
                "strongest_selling_point": "结构与转化动作可用" if scored.total_score >= min_score else "需要继续补强",
                "weak_point": ",".join(scored.issues[:3]) or "none",
                "fix_now": "补证据、补结构、收紧CTA",
            }
        )
    return {
        "verdict": "fallback_review",
        "platform_reviews": rows,
        "monetization_risks": [],
        "next_actions": [
            "continue_rewrite_for_failed_platforms",
            "generate_cover_assets",
            "manual_editorial_spot_check_before_publish",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic")
    parser.add_argument("--topic-file")
    parser.add_argument("--platforms", nargs="+", default=DEFAULT_PLATFORMS)
    parser.add_argument("--metrics-file")
    parser.add_argument("--min-score", type=float, default=85.0)
    parser.add_argument("--max-rewrite-rounds", type=int, default=3)
    parser.add_argument("--out", default="autotuned_drafts.json")
    args = parser.parse_args()

    if args.topic_file:
        topic = Path(args.topic_file).read_text(encoding="utf-8-sig").strip()
    else:
        topic = (args.topic or "").strip()
    if not topic:
        raise SystemExit("missing topic: use --topic or --topic-file")

    feedback = load_metrics_feedback(args.metrics_file)
    research = gather_research_context(topic, args.platforms)
    try:
        strategy = extract_json(
            run_agent("main-brain", build_strategy_prompt(topic, args.platforms, feedback, research), timeout=220)
        )
        if not isinstance(strategy, dict):
            raise ValueError("strategy_not_dict")
    except Exception:
        strategy = fallback_strategy(topic, args.platforms, feedback, research)
    try:
        raw = run_agent("content", build_init_prompt(topic, args.platforms, strategy, feedback, research), timeout=420)
        base_drafts = normalize_list(extract_json(raw))
    except Exception:
        base_drafts = fallback_init_drafts(topic, args.platforms, research=research, feedback=feedback)
    drafts = select_best_drafts(base_drafts, args.platforms, args.min_score)
    if len(drafts) < len(args.platforms):
        existing = {str(d.get("platform", "")).strip() for d in drafts}
        for draft in fallback_init_drafts(topic, args.platforms, research=research, feedback=feedback):
            platform = str(draft.get("platform", "")).strip()
            if platform not in existing:
                drafts.append(draft)
                existing.add(platform)

    final_drafts: List[Dict[str, Any]] = []
    score_log: List[Dict[str, Any]] = []

    for draft in drafts:
        final, score_row = optimize_draft(
            topic=topic,
            draft=draft,
            strategy=strategy,
            feedback=feedback,
            research=research,
            min_score=args.min_score,
            max_rewrite_rounds=args.max_rewrite_rounds,
        )
        final = sanitize_draft(topic, final, research=research, feedback=feedback)
        rescored = score_one(final, args.min_score)
        score_log.append(
            {
                "platform": final.get("platform", ""),
                "score": rescored.total_score,
                "pass": rescored.pass_gate,
                "issues": rescored.issues,
                "subscores": rescored.subscores,
                "rounds": score_row["rounds"],
            }
        )
        final_drafts.append(final)

    try:
        publisher_review = extract_json(run_agent("publisher", build_publisher_review_prompt(topic, final_drafts), timeout=260))
    except Exception:
        publisher_review = fallback_review(final_drafts, args.min_score)

    assets = generate_asset_prompts(topic, final_drafts)
    payload = {
        "topic": topic,
        "strategy": strategy,
        "research_context": research,
        "metrics_feedback": feedback,
        "drafts": final_drafts,
        "scores": score_log,
        "publisher_review": publisher_review,
        "assets": assets,
    }

    out = Path(args.out)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "scores": score_log}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
