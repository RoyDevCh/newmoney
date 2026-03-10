#!/usr/bin/env python3
"""Platform-specific direction policy used to anchor topic and content quality."""

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


PLATFORM_DIRECTIONS: Dict[str, Dict[str, Any]] = {
    ZH: {
        "primary_direction": "高决策成本科技消费",
        "secondary_direction": "高专业信任的搜索型长文与回答",
        "audience": "高净值、强决策需求、愿意阅读长文做消费判断的人群",
        "goal": "沉淀可转化的高信任受众，而不是泛流量",
        "core_lanes": [
            "数码与家电",
            "汽车与出行",
            "网络服务与开发者工具",
            "智能家居",
            "智能穿戴",
        ],
        "topic_constraints": [
            "优先高决策成本、高客单价、高试错风险的科技消费题材",
            "优先能自然覆盖品牌词、型号词、预算词、场景词的题材",
            "优先能沉淀搜索流量和收藏的长文",
            "尽量避免时政、泛情绪、娱乐八卦、无明确决策价值的话题",
        ],
        "content_archetypes": [
            "搜索型选购长文",
            "品牌与型号对比",
            "预算段与场景段决策文",
            "高价值问题回答",
            "长期使用与避坑白皮书",
        ],
        "preferred_formats": ["article", "answer"],
        "must_have": [
            "首屏直接答案",
            "预算分段",
            "家庭或使用场景分层",
            "品牌或型号差异",
            "明确推荐与不推荐",
            "表格、清单或结论块",
            "来源说明、评测口径或公开资料信号",
            "单一清晰的结尾动作",
        ],
        "quality_signals": [
            "标题覆盖核心搜索词",
            "正文里有可执行判断标准",
            "信息密度高于普通经验贴",
            "收藏价值强于情绪价值",
            "逻辑严密，尽量避免反对票触发点",
        ],
        "search_intent_patterns": [
            "2026 XX 推荐",
            "XX 怎么选",
            "XX 哪个牌子好",
            "XX 值不值得买",
            "XX 预算怎么分",
            "XX 和 XX 怎么选",
        ],
        "monetization_paths": [
            "知乎好物",
            "商品卡 / CPS",
            "资料表与清单承接",
            "系列专栏沉淀后再做高客单转化",
        ],
        "video_repurpose": {
            "eligible": True,
            "target_platforms": [BILI, XG],
            "angle": "把长文里的预算分段、场景推荐、品牌差异改造成 5-10 分钟横屏讲解视频",
        },
    }
}


def get_platform_direction(platform: str) -> Dict[str, Any]:
    return dict(PLATFORM_DIRECTIONS.get(str(platform or "").strip(), {}))


def build_platform_direction_brief(platform: str) -> str:
    policy = get_platform_direction(platform)
    if not policy:
        return ""
    must_have = "、".join(policy.get("must_have", []))
    lanes = "、".join(policy.get("core_lanes", []))
    return (
        f"方向={policy.get('primary_direction', '')}; "
        f"目标={policy.get('goal', '')}; "
        f"赛道={lanes}; "
        f"必须包含={must_have}"
    )


def build_platform_direction_context(platforms: List[str]) -> Dict[str, Dict[str, Any]]:
    return {platform: get_platform_direction(platform) for platform in platforms if get_platform_direction(platform)}
