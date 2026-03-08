#!/usr/bin/env python3
"""Attach platform-specific monetization plans to publish packs."""

from __future__ import annotations

from typing import Any, Dict, List


PLATFORM_PLANS: Dict[str, Dict[str, Any]] = {
    "知乎": {
        "primary_paths": ["知+自选卡片点击收益", "知乎好物/商品卡", "知学堂或咨询清单转化"],
        "best_content_formats": ["红黑榜", "选购指南", "流程拆解", "场景问答"],
        "offer": "工具清单、对比表、避坑清单、咨询清单",
        "cta": "评论关键词领取清单，或引导查看商品卡",
        "proof": "结构化对比、适用人群、明确不适合谁",
        "kpi": ["收藏率", "评论关键词率", "卡片点击率"],
        "risk_controls": ["避免虚假测评", "避免绝对化结论", "少用空泛行业判断"],
    },
    "小红书": {
        "primary_paths": ["店铺/商品转化", "蒲公英商单", "小程序或服务咨询"],
        "best_content_formats": ["收藏清单", "前后对比", "低成本提升", "模板展示"],
        "offer": "模板包、清单卡、轻咨询、低客单数字产品",
        "cta": "收藏+评论关键词领取，优先做轻量动作",
        "proof": "强场景图、真实使用细节、低门槛操作感",
        "kpi": ["收藏率", "私信/评论关键词率", "点击店铺率"],
        "risk_controls": ["避免过强专家口吻", "避免像硬广", "图片审美必须过关"],
    },
    "抖音": {
        "primary_paths": ["精选联盟/橱窗带货", "直播承接", "星图商单"],
        "best_content_formats": ["错误纠正", "三步解决", "强对比演示", "低成本试错"],
        "offer": "商品清单、工具组合、直播承接、评论区关键词资料",
        "cta": "主页/橱窗/评论关键词三选一，不要多 CTA 并发",
        "proof": "首屏结论、镜头内可视化动作、口播节奏",
        "kpi": ["3秒完播率", "主页点击率", "商品点击率"],
        "risk_controls": ["避免长句", "避免虚构收益", "避免口播过多空词"],
    },
    "B站": {
        "primary_paths": ["悬赏带货", "花火商单", "充电计划/资源包"],
        "best_content_formats": ["横评", "流程演示", "实测结论", "资料包延展"],
        "offer": "完整清单、资源包、工具表、评论区置顶资料",
        "cta": "三连+评论关键词领取资源包",
        "proof": "测试上下文、对比证据、时长价值感",
        "kpi": ["平均观看时长", "三连率", "评论区关键词率"],
        "risk_controls": ["避免空洞热血腔", "避免浅层 listicle", "封面要有强对比点"],
    },
    "公众号": {
        "primary_paths": ["流量主", "文章内商品/服务转化", "私域咨询"],
        "best_content_formats": ["周报", "深度清单", "行业快报", "操作指南"],
        "offer": "订阅专栏、资料包、企业咨询清单",
        "cta": "文末引导关注系列或领取扩展资料",
        "proof": "来源链接、时间标记、结构完整",
        "kpi": ["打开率", "阅读完成率", "资料领取率"],
        "risk_controls": ["避免标题党过度", "避免信源不明", "注意长期搜索价值"],
    },
    "头条": {
        "primary_paths": ["图文流量收益", "商品卡/带货", "专栏延展"],
        "best_content_formats": ["长图文故事", "热点解读", "避坑合集", "信息差整理"],
        "offer": "系列专题、工具合集、低门槛带货卡",
        "cta": "收藏关注系列更新，或查看相关商品卡",
        "proof": "多段转折、长文耐读性、强标题",
        "kpi": ["阅读时长", "读完率", "粉丝转化率"],
        "risk_controls": ["避免低质搬运感", "避免无来源猎奇", "避免段落过散"],
    },
    "微博": {
        "primary_paths": ["微任务商单", "广告共享计划", "小店/外部电商导购"],
        "best_content_formats": ["热点快评", "单视频博文", "清单式图文", "热搜延伸"],
        "offer": "热点观点卡、同款清单、活动或商品导流",
        "cta": "评论互动+单链接导购，不要多跳转",
        "proof": "时效性、观点浓缩、明确标签",
        "kpi": ["互动率", "转评比", "单条链接点击率"],
        "risk_controls": ["避免同质化热点", "避免多链接分散", "注意广告规范"],
    },
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
        },
    )


def attach_monetization_plans(pack: Dict[str, Any]) -> Dict[str, Any]:
    drafts = [x for x in pack.get("drafts", []) if isinstance(x, dict)]
    plans: Dict[str, Any] = {}
    for draft in drafts:
        platform = str(draft.get("platform", "")).strip()
        plans[platform] = infer_plan(platform)
    pack["monetization_plans"] = plans
    return pack


def summarize_platforms(pack: Dict[str, Any]) -> List[str]:
    plans = pack.get("monetization_plans", {})
    return sorted([str(k) for k in plans.keys()])
