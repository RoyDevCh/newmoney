#!/usr/bin/env python3
"""Production and publish strategy baselines for the content system."""

from __future__ import annotations

from typing import Any, Dict


PLATFORM_STRATEGY: Dict[str, Dict[str, Any]] = {
    "知乎": {
        "recommended_publish_per_day": 1,
        "recommended_produce_per_day": 2,
        "publish_windows": ["12:00-13:30", "20:00-22:00"],
        "primary_goal": "high-trust conversion",
        "post_type": "long-form answer/article",
        "manual_publish_priority": 1,
        "notes": "优先发高证据感稿件，同一天不要连续发多个高度相似选题。",
    },
    "小红书": {
        "recommended_publish_per_day": 2,
        "recommended_produce_per_day": 3,
        "publish_windows": ["11:30-13:00", "19:00-22:30"],
        "primary_goal": "save-driven growth",
        "post_type": "visual note",
        "manual_publish_priority": 2,
        "notes": "优先发收藏型清单和模板展示，图比字更重要。",
    },
    "抖音": {
        "recommended_publish_per_day": 2,
        "recommended_produce_per_day": 3,
        "publish_windows": ["12:00-13:30", "19:00-22:30"],
        "primary_goal": "traffic and profile clicks",
        "post_type": "short video",
        "manual_publish_priority": 2,
        "notes": "先保稳定节奏，不建议一开始堆太多条。",
    },
    "西瓜视频": {
        "recommended_publish_per_day": 1,
        "recommended_produce_per_day": 1,
        "publish_windows": ["12:00-14:00", "19:30-22:00"],
        "primary_goal": "watch time and compound traffic",
        "post_type": "horizontal mid-length video",
        "manual_publish_priority": 1,
        "notes": "西瓜更适合3到8分钟横屏母体视频，优先做完整信息密度。",
    },
    "B站": {
        "recommended_publish_per_day": 1,
        "recommended_produce_per_day": 1,
        "publish_windows": ["18:30-21:30"],
        "primary_goal": "trust and watch time",
        "post_type": "video",
        "manual_publish_priority": 1,
        "notes": "B站看单条价值，不适合高频堆量。",
    },
    "微博": {
        "recommended_publish_per_day": 2,
        "recommended_produce_per_day": 3,
        "publish_windows": ["10:00-12:00", "18:00-21:00"],
        "primary_goal": "hot-topic reach",
        "post_type": "quick reaction post",
        "manual_publish_priority": 3,
        "notes": "允许快反，但动作必须单一，避免多链路导流。",
    },
    "公众号": {
        "recommended_publish_per_day": 1,
        "recommended_produce_per_day": 1,
        "publish_windows": ["08:00-09:30", "20:00-22:00"],
        "primary_goal": "retention and lead capture",
        "post_type": "deep article",
        "manual_publish_priority": 1,
        "notes": "先做稳定深度稿，不建议日发多篇。",
    },
    "头条": {
        "recommended_publish_per_day": 2,
        "recommended_produce_per_day": 3,
        "publish_windows": ["09:00-11:00", "18:00-20:30"],
        "primary_goal": "reading scale and flow income",
        "post_type": "long graphic article",
        "manual_publish_priority": 2,
        "notes": "长图文可以一天两篇，但题材不要高度重复。",
    },
}


def build_strategy_matrix() -> Dict[str, Dict[str, Any]]:
    return {key: value.copy() for key, value in PLATFORM_STRATEGY.items()}
