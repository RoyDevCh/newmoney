#!/usr/bin/env python3
"""Attach platform monetization plans and readiness to publish packs."""

from __future__ import annotations

from typing import Any, Dict, List


PLATFORM_PLANS: Dict[str, Dict[str, Any]] = {
    "知乎": {
        "primary_paths": ["知乎好物/商品卡", "工具清单资料包", "咨询清单或服务线索"],
        "best_content_formats": ["选购指南", "红黑榜", "流程拆解", "场景问答"],
        "offer": "工具清单、对比表、避坑清单、咨询清单",
        "cta": "评论关键词领取清单，或引导查看商品卡",
        "proof": "结构化对比、适用人群、明确不适合谁",
        "kpi": ["收藏率", "评论关键词率", "商品卡点击率"],
        "risk_controls": ["避免虚假测评", "避免绝对化结论", "减少空泛行业判断"],
        "monetization_stage": "高信任转化",
        "threshold_signals": ["分成口径不固定，更适合作为后台或签约口径理解。", "更适合深度问答、专业科普、长文和结构化清单。"],
    },
    "小红书": {
        "primary_paths": ["店铺商品转化", "数字产品", "轻咨询或私信线索", "蒲公英商单"],
        "best_content_formats": ["收藏清单", "前后对比", "模板展示", "轻教程"],
        "offer": "模板包、清单卡、轻咨询、低客单数字产品",
        "cta": "收藏加评论关键词领取，优先做轻量动作",
        "proof": "强场景图、真实使用细节、低门槛操作感",
        "kpi": ["收藏率", "评论或私信关键词率", "店铺点击率"],
        "risk_controls": ["避免过强专家口吻", "避免硬广感", "视觉审美必须过关"],
        "monetization_stage": "视觉驱动转化",
        "threshold_signals": ["商单与店铺门槛会随平台策略变化。", "优先先做收藏和私信线索，再承接更重的商业动作。"],
    },
    "抖音": {
        "primary_paths": ["橱窗/联盟带货", "直播承接", "评论关键词资料", "星图商单"],
        "best_content_formats": ["错误纠正", "三步解决", "强对比演示", "低成本试错"],
        "offer": "商品清单、工具组合、直播承接、评论区关键词资料",
        "cta": "主页、橱窗、评论关键词三选一，不要并发多个CTA",
        "proof": "首屏结论、镜头内可视化动作、口播节奏",
        "kpi": ["3秒完播率", "主页点击率", "商品点击率", "直播承接率"],
        "risk_controls": ["避免长句", "避免虚构收益", "避免过多空话"],
        "monetization_stage": "短流量导购",
        "threshold_signals": ["先验证停留和主页点击，再推进更重的带货动作。"],
    },
    "西瓜视频": {
        "primary_paths": ["中长视频流量收益", "系列内容导流", "商品卡或头条体系联动", "知识型资料包"],
        "best_content_formats": ["3到8分钟横屏母体视频", "案例拆解", "流程教程", "系列合集"],
        "offer": "完整清单、横屏系列、资料包、头条联动阅读",
        "cta": "收藏本集并查看简介清单，承接系列下一条",
        "proof": "横屏完整叙事、步骤演示、案例或测试环境说明",
        "kpi": ["平均观看时长", "完播率", "收藏率", "系列追更率"],
        "risk_controls": ["避免短视频式强催促", "避免空镜堆砌", "封面和标题要一致"],
        "monetization_stage": "母体内容沉淀",
        "threshold_signals": ["适合做横屏母体内容，不宜硬套固定RPM。"],
    },
    "B站": {
        "primary_paths": ["悬赏带货", "花火商单", "资源包转化", "充电计划"],
        "best_content_formats": ["横评", "流程演示", "实测结论", "资料包延展"],
        "offer": "完整清单、资源包、工具表、评论区置顶资料",
        "cta": "三连加评论关键词领取资料包",
        "proof": "测试上下文、对比证据、观看时长价值感",
        "kpi": ["平均观看时长", "三连率", "评论关键词率"],
        "risk_controls": ["避免空洞热血腔", "避免浅层listicle", "封面要有强对比点"],
        "monetization_stage": "长内容转化",
        "threshold_signals": ["先把栏目可信度做起来，再推进花火和资源包。"],
    },
    "微博": {
        "primary_paths": ["微任务商单", "广告共享计划", "单链接导流"],
        "best_content_formats": ["热点快评", "单视频博文", "图文清单", "热搜延伸"],
        "offer": "热点观点卡、同款清单、活动或商品导流",
        "cta": "评论互动加单链接导购，不要多跳转",
        "proof": "时效性、观点浓缩、明确标签",
        "kpi": ["互动率", "转评比", "单条链接点击率"],
        "risk_controls": ["避免同质化热点", "避免多链接分散", "注意广告规范"],
        "monetization_stage": "热点快反转化",
        "threshold_signals": ["更适合快反引流，不适合一条内容里塞过多动作。"],
    },
    "公众号": {
        "primary_paths": ["流量主", "文章内商品或服务转化", "资料包或私域咨询"],
        "best_content_formats": ["周报", "深度清单", "行业快报", "操作指南"],
        "offer": "订阅专栏、资料包、企业咨询清单",
        "cta": "文末引导关注系列或领取扩展资料",
        "proof": "来源链接、时间标记、结构完整",
        "kpi": ["打开率", "阅读完成率", "资料领取率"],
        "risk_controls": ["避免标题党过度", "避免信源不明", "注意长期搜索价值"],
        "monetization_stage": "沉淀型转化",
        "threshold_signals": ["更适合做深度内容和单一资料入口的长期沉淀。"],
    },
    "头条": {
        "primary_paths": ["图文流量收益", "商品卡带货", "专栏延展"],
        "best_content_formats": ["长图文故事", "热点解读", "避坑合集", "信息差整理"],
        "offer": "系列专题、工具合集、低门槛带货卡",
        "cta": "收藏关注系列更新，或查看相关商品卡",
        "proof": "多段转折、长文耐读性、强标题",
        "kpi": ["阅读时长", "读完率", "粉丝转化率"],
        "risk_controls": ["避免低质搬运感", "避免无来源猎奇", "避免段落过散"],
        "monetization_stage": "规模化图文收益",
        "threshold_signals": ["长图文先拿到稳定阅读，再考虑更重的带货动作。"],
    },
}

READINESS_RULES: Dict[str, Dict[str, str]] = {
    "知乎": {"current_focus": "沉淀", "next_focus": "带货", "why_now": "知乎先靠结构化深度内容做搜索和收藏，再承接商品卡和资料包。"},
    "小红书": {"current_focus": "流量", "next_focus": "带货", "why_now": "小红书先做收藏和私信线索，再推进店铺和商单更稳。"},
    "抖音": {"current_focus": "流量", "next_focus": "带货", "why_now": "先跑通停留和主页点击，再推进橱窗和直播承接。"},
    "西瓜视频": {"current_focus": "沉淀", "next_focus": "带货", "why_now": "西瓜适合做母体内容，先把观看时长和系列追更做起来。"},
    "B站": {"current_focus": "沉淀", "next_focus": "商单", "why_now": "B站先做可信栏目，再接花火和资源包。"},
    "微博": {"current_focus": "流量", "next_focus": "商单", "why_now": "微博适合热点快反和单链接导流，先做互动密度。"},
    "公众号": {"current_focus": "沉淀", "next_focus": "带货", "why_now": "公众号天然适合留存和复购，先做深度内容和资料包承接。"},
    "头条": {"current_focus": "流量", "next_focus": "带货", "why_now": "头条先靠长图文拿规模阅读，再承接商品卡和专栏。"},
}


def infer_plan(platform: str) -> Dict[str, Any]:
    return PLATFORM_PLANS.get(
        platform,
        {
            "primary_paths": ["内容分发", "咨询转化"],
            "best_content_formats": ["结构化内容"],
            "offer": "清单或资料包",
            "cta": "评论关键词领取",
            "proof": "明确场景和结论",
            "kpi": ["互动率", "转化率"],
            "risk_controls": ["避免夸大宣传"],
            "monetization_stage": "基础转化",
            "threshold_signals": ["具体门槛应以平台后台和最新规则为准。"],
        },
    )


def infer_readiness(platform: str, content_ready: bool) -> Dict[str, Any]:
    base = READINESS_RULES.get(
        platform,
        {"current_focus": "流量", "next_focus": "带货", "why_now": "当前先验证内容和互动，再推进更重的商业动作。"},
    )
    plan = infer_plan(platform)
    return {
        "current_focus": base["current_focus"],
        "next_focus": base["next_focus"],
        "why_now": base["why_now"],
        "content_ready": content_ready,
        "account_threshold_status": "unknown",
        "blocked_by": plan.get("threshold_signals", []),
        "best_offer_now": plan.get("offer", ""),
    }


def build_full_platform_matrix() -> Dict[str, Any]:
    return {platform: infer_plan(platform) for platform in PLATFORM_PLANS.keys()}


def build_platform_readiness(platforms: List[str], content_ready_platforms: List[str] | None = None) -> Dict[str, Any]:
    ready_set = set(content_ready_platforms or [])
    return {platform: infer_readiness(platform, content_ready=(platform in ready_set)) for platform in platforms}


def build_readiness_summary(platforms: List[str]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {"流量": [], "商单": [], "带货": [], "沉淀": []}
    for platform in platforms:
        current_focus = infer_readiness(platform, content_ready=False)["current_focus"]
        grouped.setdefault(current_focus, []).append(platform)
    return grouped


def attach_monetization_plans(pack: Dict[str, Any]) -> Dict[str, Any]:
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    platforms: List[str] = []
    plans: Dict[str, Any] = {}
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        if not platform:
            continue
        platforms.append(platform)
        plans[platform] = infer_plan(platform)
    pack["monetization_plans"] = plans
    pack["global_monetization_matrix"] = build_full_platform_matrix()
    pack["platform_readiness"] = build_platform_readiness(platforms, content_ready_platforms=platforms)
    return pack


def summarize_platforms(pack: Dict[str, Any]) -> List[str]:
    plans = pack.get("monetization_plans", {})
    return sorted([str(key) for key in plans.keys() if str(key).strip()])
