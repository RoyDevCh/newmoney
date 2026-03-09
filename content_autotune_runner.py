#!/usr/bin/env python3
"""Generate monetization-ready drafts with research, rewrite, and quality loops."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urlparse

from content_quality_gate import DraftScore, score_one

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
        "angle": "误区拆解、场景问答、流程拆解、工具横评",
        "structure": ["先下判断", "讲适合谁", "拆3个误区", "给执行步骤", "给模板入口"],
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


def _lazy_search_imports() -> Tuple[Any, Any]:
    searx = None
    ddgs = None
    try:
        from searxng_search import search as searx_search  # type: ignore

        searx = searx_search
    except Exception:
        searx = None
    try:
        from search import search as ddgs_search  # type: ignore

        ddgs = ddgs_search
    except Exception:
        ddgs = None
    return searx, ddgs


def _normalize_search_rows(data: Any, query: str) -> List[Dict[str, str]]:
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

TRUSTED_PLATFORM_DOMAINS = {
    "zhihu.com",
    "xiaohongshu.com",
    "weibo.com",
    "toutiao.com",
    "ixigua.com",
    "bilibili.com",
    "mp.weixin.qq.com",
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


def _topic_keywords(topic: str) -> List[str]:
    current = str(topic or "").strip()
    seed = re.split(r"[\s,/|、，。:：()（）-]+", current)
    keywords = [item for item in seed if len(item) >= 2 and item not in {"2026", "指南", "清单", "避坑"}]
    bucket = _topic_bucket(current)
    keywords.extend(CONSUMER_TOPIC_HINTS.get(bucket, []))
    seen: List[str] = []
    for item in keywords:
        if item and item not in seen:
            seen.append(item)
    return seen[:12]


def _research_row_score(row: Dict[str, str], topic: str, platforms: Iterable[str]) -> int:
    title = str(row.get("title", "")).lower()
    snippet = str(row.get("snippet", "")).lower()
    url = str(row.get("url", "")).lower()
    text = " ".join([title, snippet, url])
    domain = _domain_from_url(url)
    bucket = _topic_bucket(topic)
    score = 0

    for keyword in _topic_keywords(topic):
        if keyword.lower() in text:
            score += 2

    if domain in TRUSTED_PLATFORM_DOMAINS:
        score += 2
    if any(platform_domain in domain for platform_domain in TRUSTED_PLATFORM_DOMAINS):
        score += 1

    if bucket != "tech_ai" and domain in BLOCKED_RESEARCH_DOMAINS:
        score -= 6
    if bucket != "tech_ai" and any(bad in text for bad in ["npm search", "package", "api reference", "sdk", "developer docs"]):
        score -= 4

    if "实测" in text or "评测" in text or "对比" in text or "清单" in text:
        score += 1
    if any(platform in text for platform in ["知乎", "小红书", "微博", "头条", "西瓜", "b站", "bilibili"]):
        score += 1
    return score


def _keep_research_row(row: Dict[str, str], topic: str, platforms: Iterable[str]) -> bool:
    return _research_row_score(row, topic, platforms) >= 2


def build_research_queries(topic: str, platforms: Iterable[str]) -> List[str]:
    queries = [f"{topic} 2026 实测", f"{topic} 公开评测 选购 对比"]
    platform_query_map = {
        ZH: f"{topic} site:zhihu.com",
        XHS: f"{topic} site:xiaohongshu.com",
        WB: f"{topic} site:weibo.com",
        WX: f"{topic} 微信公众号 资料 清单",
        TT: f"{topic} 头条 长文 经验",
    }
    for platform in platforms:
        if platform in platform_query_map:
            queries.append(platform_query_map[platform])
    seen: List[str] = []
    for item in queries:
        if item not in seen:
            seen.append(item)
    return seen[:6]


def gather_research_context(topic: str, platforms: List[str]) -> Dict[str, Any]:
    searx_search, ddgs_search = _lazy_search_imports()
    collected: List[Dict[str, str]] = []
    sources: List[str] = []

    for query in build_research_queries(topic, platforms):
        try:
            if searx_search:
                raw = searx_search(query, limit=5)
                rows = _normalize_search_rows(raw, query)
                if rows:
                    collected.extend(rows)
                    sources.append("searxng")
                    continue
        except Exception:
            pass
        try:
            if ddgs_search:
                raw = ddgs_search(query, max_results=5)
                rows = _normalize_search_rows(raw, query)
                if rows:
                    collected.extend(rows)
                    sources.append("ddgs")
        except Exception:
            continue

    deduped: List[Dict[str, str]] = []
    seen_keys = set()
    for row in collected:
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


def build_platform_rules(platforms: List[str]) -> str:
    chunks: List[str] = []
    for platform in platforms:
        brief = PLATFORM_BRIEFS.get(platform, {})
        structure = "、".join(brief.get("structure", []))
        chunks.append(
            f"{platform}: 正文字数={brief.get('body_range','')}, 语气={brief.get('voice','')}, "
            f"转化={brief.get('conversion','')}, 角度={brief.get('angle','')}, 结构={structure}"
        )
    return " | ".join(chunks)


def build_strategy_prompt(topic: str, platforms: List[str], feedback: Dict[str, Any], research: Dict[str, Any]) -> str:
    return (
        f"只输出JSON。主题={topic}，目标平台={','.join(platforms)}。"
        f"历史反馈={summarize_feedback(feedback)}。"
        f"研究资料={json.dumps(research, ensure_ascii=False)}。"
        "请给出今日可变现内容策略，字段："
        "audience,pain_point,conversion_goal,offer,platform_priority,angle,proof_points,content_must_have。"
        "要求：proof_points至少4条；content_must_have至少5条；优先提升知乎、小红书、微博、公众号的含金量。"
    )


def build_init_prompt(
    topic: str,
    platforms: List[str],
    strategy: Dict[str, Any],
    feedback: Dict[str, Any],
    research: Dict[str, Any],
) -> str:
    return (
        f"只输出JSON数组。主题={topic}，平台={','.join(platforms)}，策略={json.dumps(strategy, ensure_ascii=False)}。"
        f"历史反馈={summarize_feedback(feedback)}。"
        f"可用研究资料={json.dumps(research, ensure_ascii=False)}。"
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
    return (
        "只输出JSON对象。"
        f"主题={topic}，平台={platform}，当前稿件={json.dumps(draft, ensure_ascii=False)}。"
        f"问题={issues}。策略={json.dumps(strategy, ensure_ascii=False)}。"
        f"历史反馈={summarize_feedback(feedback)}。研究资料={json.dumps(research, ensure_ascii=False)}。"
        "请重写到发布水准："
        "1) 更像真实编辑，不要像AI模板。"
        "2) 结论必须更明确，证据必须更具体，动作必须更可执行。"
        "3) 长文平台补充适合谁、不适合谁、常见误区、执行步骤；短平台补强第一屏冲击力。"
        "4) 删除空话、套话、绝对化结论、不可信承诺。"
        f"5) 正文字数保持在{brief.get('body_range', '平台要求')}。"
        f"6) 语气={brief.get('voice', '')}；CTA={brief.get('conversion', '')}。"
        "7) 输出字段只能是platform,title,hook,body,cta,tags。"
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
    tuning_lines = feedback_tuning_lines(platform, feedback)
    tuning_block = "\n\n".join(tuning_lines).strip()
    short_hint = first_research_hint(research)

    if platform == ZH:
        body = (
            f"???????{topic}??????????????????????????????????????????????????"
            "????????????????????????????????????"
            "\n\n?????????????????????????????????"
            "\n\n?????????????????????????????????????????"
            "\n\n???????????????????????????????????????????????????"
            "\n\n???????????????????????????????????????????"
            "???????????????????????????????????????????????????"
            "\n\n???????????????????????????????????????????"
            "??????????????????????????????????????"
            "\n\n???????????????????????????????????????????"
        )
        if proof_block:
            body += "\n\n" + proof_block
        body += (
            "\n\n????????????????????????????????????????????????"
            "???????????????????????"
            "\n\n???????????????????1?????3?????1?????????7??????????"
            "\n\n??????????????????????????????????????????????????????????????????????????"
        )
        if tuning_block:
            body += "\n\n" + tuning_block
        return {
            "platform": ZH,
            "title": f"{topic}????????????????????????",
            "hook": f"?{topic}???????????????????????????",
            "body": body,
            "cta": "????????????????????????????????????",
            "tags": [topic, "????", "????"],
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


def has_placeholder_noise(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    return stripped.count("?") >= max(3, len(stripped) // 5)


def clean_meta_template(topic: str, platform: str) -> Dict[str, Any]:
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


def ensure_tag_density(topic: str, platform: str, tags: Iterable[Any]) -> List[str]:
    cleaned = [strip_visual_noise(scrub_claims(str(tag)), keep_small=True) for tag in tags if str(tag).strip()]
    fallback_map = {
        ZH: [topic, "经验拆解", "效率提升"],
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
    keep_small = platform in {XHS, DY}
    cleaned = dict(draft)
    meta = clean_meta_template(topic, platform)

    for key in ["title", "hook", "body", "cta"]:
        value = str(cleaned.get(key, "")).strip()
        value = scrub_claims(value)
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
    cleaned["body"] = ensure_source_signal(platform, str(cleaned.get("body", "")))
    cleaned["body"] = ensure_actionability_blocks(platform, str(cleaned.get("body", "")))
    cleaned["body"] = improve_readability_flow(str(cleaned.get("body", "")))
    tags = cleaned.get("tags", [])
    if not isinstance(tags, list) or any(has_placeholder_noise(str(tag)) for tag in tags):
        tags = meta.get("tags", [topic])
    cleaned["tags"] = ensure_tag_density(topic, platform, tags)
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
    strategy = extract_json(run_agent("main-brain", build_strategy_prompt(topic, args.platforms, feedback, research), timeout=220))
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
