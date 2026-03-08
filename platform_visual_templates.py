#!/usr/bin/env python3
"""Attach platform-specific visual template metadata to publish packs."""

from __future__ import annotations

from typing import Any, Dict


VISUAL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "知乎": {
        "aspect_ratio": "16:9",
        "safe_area": "left-title",
        "composition": "clean desk setup with one dominant focal object",
        "color_direction": "steel blue, graphite, off-white highlights",
        "typography_direction": "minimal headline, no sticker clutter",
        "cover_text_style": "专业结论型",
    },
    "小红书": {
        "aspect_ratio": "3:4",
        "safe_area": "center-top",
        "composition": "high-aesthetic lifestyle productivity scene",
        "color_direction": "warm neutral, cream, muted coral",
        "typography_direction": "soft magazine style with generous breathing room",
        "cover_text_style": "收藏清单型",
    },
    "抖音": {
        "aspect_ratio": "9:16",
        "safe_area": "center",
        "composition": "single large subject with bold contrast",
        "color_direction": "black, neon cyan, vivid red accents",
        "typography_direction": "short punchy hook, high contrast",
        "cover_text_style": "冲突纠错型",
    },
    "西瓜视频": {
        "aspect_ratio": "16:9",
        "safe_area": "left-center",
        "composition": "horizontal creator frame with layered evidence props",
        "color_direction": "deep amber, slate blue, warm tungsten",
        "typography_direction": "documentary headline and one proof cue",
        "cover_text_style": "母体内容长视频型",
    },
    "B站": {
        "aspect_ratio": "16:9",
        "safe_area": "right-title",
        "composition": "documentary tech frame with evidence props",
        "color_direction": "deep teal, tungsten, matte gray",
        "typography_direction": "strong headline with one proof cue",
        "cover_text_style": "实测结论型",
    },
    "微博": {
        "aspect_ratio": "4:3",
        "safe_area": "top-strip",
        "composition": "news-card style with one clear event cue",
        "color_direction": "clean white, crimson accent, dark text",
        "typography_direction": "headline strip and one supporting line",
        "cover_text_style": "热点快评型",
    },
    "公众号": {
        "aspect_ratio": "900:383",
        "safe_area": "center-left",
        "composition": "editorial banner with structured layout",
        "color_direction": "ink black, paper white, muted green",
        "typography_direction": "newsletter banner, restrained and readable",
        "cover_text_style": "深度指南型",
    },
    "头条": {
        "aspect_ratio": "3:2",
        "safe_area": "left-center",
        "composition": "attention-grabbing hero object with explanatory background",
        "color_direction": "amber, slate, high-key neutral",
        "typography_direction": "bold headline with one subhead",
        "cover_text_style": "长图文强标题型",
    },
}


def build_visual_templates(pack: Dict[str, Any]) -> Dict[str, Any]:
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    result: Dict[str, Any] = {}
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        if platform and platform in VISUAL_TEMPLATES:
            result[platform] = VISUAL_TEMPLATES[platform]
    return result


def attach_visual_templates(pack: Dict[str, Any]) -> Dict[str, Any]:
    pack["visual_templates"] = build_visual_templates(pack)
    return pack
