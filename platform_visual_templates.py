#!/usr/bin/env python3
"""Attach platform- and topic-specific visual template metadata to publish packs."""

from __future__ import annotations

from typing import Any, Dict, List


ZH = "知乎"
XHS = "小红书"
DY = "抖音"
XG = "西瓜视频"
BILI = "B站"
WB = "微博"
WX = "公众号"
TT = "头条"


VISUAL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    ZH: {
        "aspect_ratio": "16:9",
        "safe_area": "left-title",
        "composition": "editorial cover with one clear hero object and one proof cue",
        "color_direction": "graphite, steel blue, off-white highlights",
        "typography_direction": "minimal editorial headline, no sticker clutter",
        "cover_text_style": "professional editorial",
        "negative_prompt": "warped hardware, twisted keyboard, extra screen, extra keys, melted edges, bad perspective",
        "model_hint": "flux_schnell",
    },
    XHS: {
        "aspect_ratio": "3:4",
        "safe_area": "center-top",
        "composition": "high-aesthetic lifestyle scene with one realistic focal product",
        "color_direction": "warm neutral, cream, muted coral",
        "typography_direction": "soft magazine style with generous breathing room",
        "cover_text_style": "save-worthy checklist",
        "negative_prompt": "distorted object, extra fingers, broken screen, cluttered desk, low detail",
        "model_hint": "flux_schnell",
    },
    DY: {
        "aspect_ratio": "9:16",
        "safe_area": "center",
        "composition": "single large subject with bold contrast and clear title zone",
        "color_direction": "black, neon cyan, vivid red accents",
        "typography_direction": "short punchy hook, high contrast",
        "cover_text_style": "conflict-first short video",
        "negative_prompt": "warped hardware, duplicated subject, messy background, unreadable text",
        "model_hint": "flux_schnell",
    },
    XG: {
        "aspect_ratio": "16:9",
        "safe_area": "left-center",
        "composition": "horizontal documentary frame with layered evidence props",
        "color_direction": "deep amber, slate blue, warm tungsten",
        "typography_direction": "documentary headline and one proof cue",
        "cover_text_style": "documentary long video",
        "negative_prompt": "twisted monitor, deformed keyboard, extra monitor, blurred hands, broken geometry",
        "model_hint": "flux_schnell",
    },
    BILI: {
        "aspect_ratio": "16:9",
        "safe_area": "right-title",
        "composition": "documentary frame with strong hero object and clean title block",
        "color_direction": "deep teal, tungsten, matte gray",
        "typography_direction": "strong headline with one proof cue",
        "cover_text_style": "tested-result cover",
        "negative_prompt": "warped hardware, distorted mouse, extra fingers, messy cables, broken perspective",
        "model_hint": "flux_schnell",
    },
    WB: {
        "aspect_ratio": "4:3",
        "safe_area": "top-strip",
        "composition": "news-card style with one clear event cue",
        "color_direction": "clean white, crimson accent, dark text",
        "typography_direction": "headline strip and one supporting line",
        "cover_text_style": "fast opinion card",
        "negative_prompt": "deformed subject, crooked typography, low detail, chaotic composition",
        "model_hint": "flux_schnell",
    },
    WX: {
        "aspect_ratio": "900:383",
        "safe_area": "center-left",
        "composition": "editorial banner with structured layout and one proof object",
        "color_direction": "ink black, paper white, muted green",
        "typography_direction": "newsletter banner, restrained and readable",
        "cover_text_style": "deep guide",
        "negative_prompt": "warped object, stretched screen, cluttered layout, low-detail props",
        "model_hint": "flux_schnell",
    },
    TT: {
        "aspect_ratio": "3:2",
        "safe_area": "left-center",
        "composition": "attention-grabbing hero object with explanatory background",
        "color_direction": "amber, slate, high-key neutral",
        "typography_direction": "bold headline with one subhead",
        "cover_text_style": "longform attention cover",
        "negative_prompt": "warped hardware, extra subject, broken edges, bad perspective, low detail",
        "model_hint": "flux_schnell",
    },
}


TOPIC_VISUAL_THEMES: List[Dict[str, Any]] = [
    {
        "name": "home_cleaning",
        "keywords": ["清洁", "扫地", "洗地", "吸尘", "智能家居", "家务", "家居"],
        "subject_direction": "sunlit modern apartment, realistic robot vacuum or cleaning tool, visible floor texture, one believable hero product, no people blocking the subject",
        "palette": "cream, oak wood, soft sunlight, clean white",
        "negative_prompt": "warped furniture, floating dust storm, extra device, melted wheels, fake plastic texture",
        "image_strategy": "real_reference_preferred",
        "image_strategy_reason": "家清与家电避坑内容更依赖真实外观、细节和尺寸感，真实图更利于转化。",
    },
    {
        "name": "pets",
        "keywords": ["宠物", "猫", "狗", "训犬", "训猫", "陪伴"],
        "subject_direction": "realistic pet lifestyle scene, one pet and one gear item, outdoor or bright home environment, natural fur texture, candid photography feel",
        "palette": "grass green, sky blue, warm beige",
        "negative_prompt": "extra limbs, duplicated pet, melted fur, deformed nose, uncanny eyes",
        "image_strategy": "real_reference_preferred",
        "image_strategy_reason": "宠物用品和场景图需要真实可信，AI 容易在毛发和肢体上露出破绽。",
    },
    {
        "name": "jewelry_style",
        "keywords": ["珠宝", "配饰", "项链", "戒指", "耳饰", "手链", "穿搭", "男生佩戴"],
        "subject_direction": "premium fashion still life or realistic model crop, sharp accessory details, luxury editorial lighting, clean composition, no plastic skin",
        "palette": "charcoal, pearl white, silver, champagne",
        "negative_prompt": "deformed fingers, fake gems, extra jewelry pieces, wax skin, plastic shine",
        "image_strategy": "real_reference_preferred",
        "image_strategy_reason": "配饰类内容看重材质、光泽和佩戴效果，真实拍摄更容易建立信任。",
    },
    {
        "name": "sports_outdoor",
        "keywords": ["运动", "户外", "跑步", "力量训练", "网球", "徒步", "搏击", "健身"],
        "subject_direction": "dynamic but realistic sports scene, one athlete and one gear focus, clean motion freeze, believable anatomy, no exaggerated muscles",
        "palette": "sun orange, cobalt, graphite",
        "negative_prompt": "broken anatomy, extra limbs, fused shoes, smeared background, fake motion blur",
        "image_strategy": "real_reference_preferred",
        "image_strategy_reason": "运动装备内容更适合真实穿戴和真实动作，AI 在人体结构上不够稳定。",
    },
    {
        "name": "digital_gear",
        "keywords": ["数码", "耳机", "笔记本", "手机", "平板", "显示器", "路由器", "显卡"],
        "subject_direction": "clean product photo scene, one realistic device as hero object, precise industrial design lines, tidy desk or neutral studio background",
        "palette": "graphite, titanium, cool white",
        "negative_prompt": "warped laptop, twisted keyboard, extra screen, extra buttons, impossible ports",
        "image_strategy": "real_reference_preferred",
        "image_strategy_reason": "数码好物推荐直接看外形、接口和做工，真实参考图比 AI 图更能支撑购买决策。",
    },
]


REAL_REFERENCE_BUCKETS = {
    "home_cleaning",
    "pets",
    "jewelry_style",
    "sports_outdoor",
    "digital_gear",
}


def _default_theme() -> Dict[str, Any]:
    return {
        "theme_name": "editorial_general",
        "subject_direction": "realistic editorial scene aligned with the topic, one dominant hero object, believable textures, clean framing",
        "topic_palette": "neutral editorial palette with one accent color",
        "topic_negative_prompt": "extra objects, warped perspective, plastic texture, melted edges",
        "image_strategy": "comfy_generated_ok",
        "image_strategy_reason": "这类题材更偏概念表达或方法论，ComfyUI 生成封面可以接受。",
    }


def infer_topic_theme(topic: str) -> Dict[str, Any]:
    current = str(topic or "").strip()
    for theme in TOPIC_VISUAL_THEMES:
        if any(keyword in current for keyword in theme["keywords"]):
            return {
                "theme_name": theme["name"],
                "subject_direction": theme["subject_direction"],
                "topic_palette": theme["palette"],
                "topic_negative_prompt": theme["negative_prompt"],
                "image_strategy": theme["image_strategy"],
                "image_strategy_reason": theme["image_strategy_reason"],
            }
    if "AI" in current or "工具" in current or "效率" in current or "知识管理" in current:
        fallback = _default_theme()
        fallback["theme_name"] = "tech_ai"
        fallback["subject_direction"] = "editorial concept scene, one clean focal object, subtle abstract support elements, no warped consumer hardware"
        fallback["topic_palette"] = "slate, off-white, muted cyan"
        return fallback
    return _default_theme()


def build_reference_search_queries(topic: str, bucket: str, platform: str) -> List[str]:
    current = str(topic or "").strip()
    base = [
        f"{current} 实拍",
        f"{current} 评测",
        f"{current} 对比",
    ]
    if bucket in REAL_REFERENCE_BUCKETS:
        base.extend(
            [
                f"{current} 开箱",
                f"{current} 使用场景",
            ]
        )
    if platform == XHS:
        base.append(f"{current} 小红书 实拍")
    elif platform == ZH:
        base.append(f"{current} 知乎 评测")
    elif platform == WB:
        base.append(f"{current} 微博 实拍")
    elif platform == BILI:
        base.append(f"{current} B站 实拍")
    elif platform == XG:
        base.append(f"{current} 西瓜视频 横屏评测")
    seen: List[str] = []
    for query in base:
        if query not in seen:
            seen.append(query)
    return seen[:5]


def build_visual_templates(pack: Dict[str, Any]) -> Dict[str, Any]:
    drafts = [row for row in pack.get("drafts", []) if isinstance(row, dict)]
    topic = str(pack.get("topic", "")).strip()
    theme = infer_topic_theme(topic)
    result: Dict[str, Any] = {}
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        if not platform or platform not in VISUAL_TEMPLATES:
            continue
        merged = dict(VISUAL_TEMPLATES[platform])
        merged.update(theme)
        merged["topic"] = topic
        merged["reference_search_queries"] = build_reference_search_queries(
            topic=topic,
            bucket=str(theme.get("theme_name", "")),
            platform=platform,
        )
        merged["cover_workflow"] = (
            "use_real_reference_first"
            if merged.get("image_strategy") == "real_reference_preferred"
            else "allow_comfy_generation"
        )
        result[platform] = merged
    return result


def attach_visual_templates(pack: Dict[str, Any]) -> Dict[str, Any]:
    pack["visual_templates"] = build_visual_templates(pack)
    return pack
