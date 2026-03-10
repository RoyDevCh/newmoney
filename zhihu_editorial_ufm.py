#!/usr/bin/env python3
"""Unified Field Model rules for Zhihu single-product editorial content."""

from __future__ import annotations

from typing import Any, Dict, List

from consumer_product_knowledge import infer_product_family


SOURCE_TIERS: List[str] = [
    "Tier 1：厂商官网 / 官方规格页 / 官方新闻稿 / 发布会稿",
    "Tier 2：监管 / 国家标准 / 机构结果页",
    "Tier 3：权威中文媒体的有方法披露评测",
    "Tier 4：KOL / B站 / 知乎上手，仅作信号证据",
    "Tier 5：基准数据库，只作趋势信号",
    "Tier 6：社区口碑，只作问题雷达",
]


EVIDENCE_DENSITY_RULES: Dict[str, Dict[str, int]] = {
    "short": {"hard_facts_min": 6, "tier12_min": 2, "domains_min": 3},
    "medium": {"hard_facts_min": 14, "tier12_min": 6, "domains_min": 4},
    "long": {"hard_facts_min": 25, "tier12_min": 10, "domains_min": 5},
}


WEARABLE_UFM = {
    "mandatory_dimensions": [
        "健康功能边界",
        "定位精度与运动场景",
        "续航分场景",
        "佩戴材料与舒适度",
        "外观材质与耐用性",
        "生态联动与系统边界",
    ],
    "must_compare": [
        "与上一代相比，哪些是实质升级，哪些只是口径变化",
        "与同品类产品相比，Apple / 华为 / Garmin 的核心价值边界在哪里",
        "健康与运动功能哪些能长期用，哪些更像发布期卖点",
    ],
}


ROUTER_UFM = {
    "mandatory_dimensions": [
        "覆盖与户型匹配",
        "多设备稳定性",
        "接口与回程",
        "管理体验",
        "功耗与长期运行",
    ],
    "must_compare": [
        "与上一代或同系列相比，是真升级还是参数表升级",
        "与同价位竞品相比，覆盖、稳定性、回程和接口哪项更值钱",
    ],
}


DEFAULT_UFM = {
    "mandatory_dimensions": [
        "核心规格",
        "真实使用场景",
        "关键短板",
        "上一代或竞品对比",
        "证据口径与待验证项",
    ],
    "must_compare": [
        "至少给一个上一代对比或同品类对比",
    ],
}


def _family_policy(topic: str) -> Dict[str, Any]:
    family = infer_product_family(topic)
    if family == "智能手表":
        return WEARABLE_UFM
    if family == "路由器":
        return ROUTER_UFM
    return DEFAULT_UFM


def build_ufm_prompt_rules(topic: str) -> str:
    policy = _family_policy(topic)
    dims = "、".join(policy.get("mandatory_dimensions", []))
    compares = "；".join(policy.get("must_compare", []))
    tiers = "；".join(SOURCE_TIERS)
    medium = EVIDENCE_DENSITY_RULES["medium"]
    return (
        "统一方法论要求：采用“三账本、两条链、三层输出”。"
        " 三账本=事实账本、方法账本、信号账本；"
        " 两条链=证据链、口径链；"
        " 三层输出=L0结论卡、L1可比矩阵、L2证据与方法附录。"
        f" 本品类强制评测维度={dims}。"
        f" 强制对比要求={compares}。"
        f" 证据来源分层={tiers}。"
        f" 中文 1200-1600 字单品稿建议至少包含 {medium['hard_facts_min']} 条硬事实字段，"
        f"其中 Tier1/2 不少于 {medium['tier12_min']} 条，且覆盖不少于 {medium['domains_min']} 个域名来源。"
        " 任何测试、续航、快充、定位、运动表现结论，都必须带条件或明确写成‘当前口径 / 待验证’。"
    )


def build_ufm_output_contract(topic: str) -> str:
    policy = _family_policy(topic)
    dims = policy.get("mandatory_dimensions", [])
    return (
        "输出结构契约："
        "L0=一句话判词 + 适合/不适合人群 + 风险提示；"
        "L1=至少一张可比矩阵表，包含对比维度、Series 11 判断、上代或竞品参考、当前结论等级；"
        "L2=来源说明、证据口径、待验证项。"
        f" 文中必须显式覆盖这些维度：{'、'.join(dims)}。"
    )
