from pathlib import Path
import textwrap
root = Path(r'C:\Users\Roy\Documents\New project')

files = {}
files['publish_appendix_builder.py'] = '''#!/usr/bin/env python3
"""Build publish-ready appendices such as tables, lists, and CTAs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


GENERAL_CATALOG = [
    {"tool": "对比清单", "best_for": "选购决策、工具筛选、方案比价", "strength": "能直接降低读者决策成本", "watch_out": "要写清适用人群和不适用人群", "pricing_note": "先用免费版本验证需求"},
    {"tool": "执行模板", "best_for": "流程复用、内容制作、项目推进", "strength": "可以直接复制使用，收藏率高", "watch_out": "模板一定要有使用场景说明", "pricing_note": "适合低客单数字产品"},
    {"tool": "资源包", "best_for": "系列内容承接、评论区关键词领取", "strength": "兼顾转化和留存", "watch_out": "不要堆太多无关文件", "pricing_note": "适合做资料包或轻咨询入口"},
]

AI_TOOL_CATALOG = [
    {"tool": "文心一言", "best_for": "中文写作、提纲整理、基础办公问答", "strength": "中文理解和通用办公表达较稳", "watch_out": "复杂长任务时需要人工拆解需求", "pricing_note": "先从免费能力试用"},
    {"tool": "Kimi", "best_for": "长文档归纳、资料对读、信息汇总", "strength": "长文处理体验较好", "watch_out": "摘要结果仍要人工复核事实点", "pricing_note": "适合先验证长文档场景"},
    {"tool": "通义千问", "best_for": "多轮任务推进、通用办公协作", "strength": "多任务衔接和稳定性较均衡", "watch_out": "复杂输出最好给明确模板", "pricing_note": "先跑固定模板流程更稳"},
]


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def tool_rows_for_topic(topic: str) -> List[Dict[str, str]]:
    topic_lower = topic.strip().lower()
    if any(key in topic_lower for key in ["ai", "工作流", "自动化", "内容创作"]):
        return AI_TOOL_CATALOG
    return GENERAL_CATALOG


def ensure_rows(rows: List[Dict[str, str]], minimum: int = 2) -> List[Dict[str, str]]:
    seed = rows or GENERAL_CATALOG
    while len(seed) < minimum:
        seed = seed + GENERAL_CATALOG[: minimum - len(seed)]
    return seed[: max(minimum, len(seed))]


def zhihu_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    table = "\n".join([
        "| 项目 | 适合场景 | 优势 | 使用提醒 | 成本建议 |",
        "| --- | --- | --- | --- | --- |",
        *[f"| {r['tool']} | {r['best_for']} | {r['strength']} | {r['watch_out']} | {r['pricing_note']} |" for r in rows],
    ])
    return {"title": f"{topic}工具清单与红黑榜附件", "usage_note": "适合放在正文后半段或评论区置顶，增强可信度与收藏价值。", "comparison_table_markdown": table, "red_flags": ["功能承诺很多但免费体验极弱的工具或方案", "没有明确适用场景却直接卖高价套餐的内容", "输出看起来顺滑但事实错误率高的方案"], "save_cta": "如果你要完整版本，可以在评论区留关键词再补充细分场景版。"}


def bilibili_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {"title": f"{topic}视频补充资料包", "usage_note": "适合做视频简介、评论区置顶或口播结尾的资料补充。", "bullet_points": [f"{row['tool']}：适合{row['best_for']}；优势是{row['strength']}；注意{row['watch_out']}。" for row in rows], "resource_pack": ["一页版工具选择表", "执行顺序模板", "适用与不适用人群清单"], "comment_cta": "评论区留关键词，可继续引导到资料包或后续选题。"}


def xigua_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {"title": f"{topic}横屏视频补充附件", "usage_note": "适合放在视频简介和评论区，用于承接完整清单、流程图和系列下一条。", "bullet_points": [f"先看{rows[0]['tool']}，因为它更适合{rows[0]['best_for']}。", f"再看{rows[1]['tool']}，重点优势是{rows[1]['strength']}。", f"如果你要少踩坑，记住{rows[2]['watch_out']}。"], "resource_pack": ["横屏长视频分镜清单", "3到8分钟母体结构", "评论区承接关键词模板"], "comment_cta": "收藏这条，下一步按简介里的清单顺序执行。"}


def xiaohongshu_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {"title": f"{topic}收藏型清单", "usage_note": "适合做图二、图三文案或评论区补充。", "quick_list": [f"{row['tool']}：{row['best_for']}" for row in rows[:4]], "save_reason": "让读者一眼知道先试哪一个，不需要看完长文才行动。"}


def douyin_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=2)
    return {"title": f"{topic}口播补充提示卡", "usage_note": "适合做口播提词器备注或评论区清单。", "spoken_beats": [f"第一类，{rows[0]['tool']}，适合{rows[0]['best_for']}。", f"第二类，{rows[1]['tool']}，重点看{rows[1]['strength']}。", "别一上来就买最贵的，先把一个场景跑通。"], "comment_keyword": "工具清单"}


def weibo_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=2)
    return {"title": f"{topic}微博快反补充卡", "usage_note": "适合置顶评论或单条长图文补充说明。", "fast_points": [f"{rows[0]['tool']}适合{rows[0]['best_for']}", f"{rows[1]['tool']}更适合{rows[1]['strength']}"] , "comment_cta": "评论区留关键词，可继续领取完整清单。"}


def wechat_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {"title": f"{topic}公众号延伸阅读附件", "usage_note": "适合放在正文末尾，作为领取资料或系列阅读承接。", "sections": ["本期适合谁", "工具对照", "执行顺序建议", "不适合直接照抄的人群提醒"], "resource_pack": [row['tool'] for row in rows], "article_cta": "回复关键词领取清单版附件。"}


def toutiao_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {"title": f"{topic}头条长图文附录", "usage_note": "适合放在正文末尾，承接收藏、关注和下一篇阅读。", "list_points": [f"{row['tool']}：适合{row['best_for']}，注意{row['watch_out']}。" for row in rows], "follow_cta": "先收藏这篇，下一篇继续拆具体场景。"}


def build_appendices(pack: Dict[str, Any]) -> Dict[str, Any]:
    topic = str(pack.get("topic", "")).strip()
    return {
        "zhihu": zhihu_appendix(topic),
        "bilibili": bilibili_appendix(topic),
        "xigua": xigua_appendix(topic),
        "xiaohongshu": xiaohongshu_appendix(topic),
        "douyin": douyin_appendix(topic),
        "weibo": weibo_appendix(topic),
        "wechat_official": wechat_appendix(topic),
        "toutiao": toutiao_appendix(topic),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    pack = load_pack(Path(args.input))
    pack["appendices"] = build_appendices(pack)
    Path(args.output).write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": args.output, "appendix_keys": list(pack["appendices"].keys())}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''

files['manual_publish_queue_builder.py'] = '''#!/usr/bin/env python3
"""Build a manual publish queue and notification pack from a content pack."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from production_strategy_config import build_strategy_matrix


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def quality_map(quality: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = quality.get("results", []) or quality.get("scores", [])
    mapped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if isinstance(row, dict):
            platform = str(row.get("platform", "")).strip()
            if platform:
                mapped[platform] = row
    return mapped


def asset_map(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    mapped: Dict[str, Dict[str, Any]] = {}
    for row in manifest.get("results", []):
        if isinstance(row, dict):
            platform = str(row.get("platform", "")).strip()
            if platform:
                mapped[platform] = row
    return mapped


def tts_map(tts_dir: Path) -> Dict[str, str]:
    if not tts_dir.exists():
        return {}
    result: Dict[str, str] = {}
    for file in tts_dir.iterdir():
        name = file.name.lower()
        if "douyin" in name:
            result["抖音"] = str(file)
        elif "xigua" in name:
            result["西瓜视频"] = str(file)
        elif "bilibili" in name:
            result["B站"] = str(file)
    return result


def pick_manual_publish_items(pack: Dict[str, Any], quality: Dict[str, Any], manifest: Dict[str, Any], tts_files: Dict[str, str]) -> List[Dict[str, Any]]:
    strategies = build_strategy_matrix()
    qmap = quality_map(quality)
    amap = asset_map(manifest)
    items: List[Dict[str, Any]] = []
    for draft in pack.get("drafts", []):
        if not isinstance(draft, dict):
            continue
        platform = str(draft.get("platform", "")).strip()
        strategy = strategies.get(platform, {})
        q = qmap.get(platform, {})
        a = amap.get(platform, {})
        items.append({
            "platform": platform,
            "title": draft.get("title", ""),
            "hook": draft.get("hook", ""),
            "body": draft.get("body", draft.get("content", "")),
            "cta": draft.get("cta", ""),
            "tags": draft.get("tags", []),
            "score": float(q.get("total_score", q.get("score", 0.0)) or 0.0),
            "pass": bool(q.get("pass_gate", q.get("pass", False))),
            "publish_windows": strategy.get("publish_windows", []),
            "recommended_publish_per_day": strategy.get("recommended_publish_per_day", 1),
            "recommended_produce_per_day": strategy.get("recommended_produce_per_day", 1),
            "primary_goal": strategy.get("primary_goal", ""),
            "post_type": strategy.get("post_type", ""),
            "manual_publish_priority": strategy.get("manual_publish_priority", 9),
            "notes": strategy.get("notes", ""),
            "cover_file": a.get("output_file", ""),
            "tts_file": tts_files.get(platform, ""),
        })
    items.sort(key=lambda x: (x["manual_publish_priority"], -x["score"]))
    return items


def queue_summary(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"total_items": len(items), "ready_items": sum(1 for x in items if x.get("pass")), "top_priority_platforms": [x["platform"] for x in items[:3]]}


def build_markdown(queue: Dict[str, Any]) -> str:
    lines = ["# 今日手动发布队列", "", f"- 生成时间：{queue['generated_at']}", f"- 内容包：`{queue['source_pack']}`", f"- 可手动发布条数：`{queue['summary']['ready_items']}/{queue['summary']['total_items']}`", "", "## 建议顺序", ""]
    for idx, item in enumerate(queue["items"], start=1):
        status = "READY" if item.get("pass") else "HOLD"
        lines.extend([f"### {idx}. {item['platform']} [{status}]", f"- 标题：{item['title']}", f"- 分数：{item['score']}", f"- 目标：{item['primary_goal']}", f"- 建议发布时间段：{', '.join(item.get('publish_windows', []))}", f"- 建议日发布量：{item.get('recommended_publish_per_day')}", f"- 封面：`{item.get('cover_file', '')}`", f"- TTS：`{item.get('tts_file', 'N/A')}`", f"- 操作提示：{item.get('notes', '')}", "- 手动发布动作：打开对应平台 -> 复制标题/正文/标签 -> 上传封面/视频 -> 发布后回填数据", ""])
    lines.extend(["## 发布后回填", "", "- 当天 23:00 后回填首轮数据", "- 次日同一时间回填 24h 数据", "- 建议至少回填：曝光、阅读/播放、点赞、评论、收藏、转发、主页点击、商品点击、收益", ""])
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-pack", required=True)
    ap.add_argument("--input-quality", required=True)
    ap.add_argument("--input-assets", required=True)
    ap.add_argument("--tts-dir", required=True)
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    ap.add_argument("--generated-at", required=True)
    ap.add_argument("--latest-json")
    ap.add_argument("--latest-md")
    args = ap.parse_args()

    pack = load_json(Path(args.input_pack))
    quality = load_json(Path(args.input_quality))
    assets = load_json(Path(args.input_assets))
    items = pick_manual_publish_items(pack, quality, assets, tts_map(Path(args.tts_dir)))
    queue = {"generated_at": args.generated_at, "source_pack": args.input_pack, "summary": queue_summary(items), "items": items}
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    output_md.write_text(build_markdown(queue), encoding="utf-8")
    if args.latest_json:
        latest_json = Path(args.latest_json)
        latest_json.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_json, latest_json)
    if args.latest_md:
        latest_md = Path(args.latest_md)
        latest_md.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_md, latest_md)
    print(json.dumps({"output_json": args.output_json, "output_md": args.output_md}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''

files['platform_monetization_mapper.py'] = Path(root / 'platform_monetization_mapper.py').read_text(encoding='utf-8')
files['platform_monetization_mapper.py'] = '''#!/usr/bin/env python3
"""Attach platform monetization plans and readiness to publish packs."""

from __future__ import annotations

from typing import Any, Dict, List


PLATFORM_PLANS: Dict[str, Dict[str, Any]] = {
    "知乎": {"primary_paths": ["知乎好物/商品卡", "工具清单资料包", "咨询清单或服务线索"], "best_content_formats": ["选购指南", "红黑榜", "流程拆解", "场景问答"], "offer": "工具清单、对比表、避坑清单、咨询清单", "cta": "评论关键词领取清单，或引导查看商品卡", "proof": "结构化对比、适用人群、明确不适合谁", "kpi": ["收藏率", "评论关键词率", "商品卡点击率"], "risk_controls": ["避免虚假测评", "避免绝对化结论", "减少空泛行业判断"], "monetization_stage": "高信任转化", "threshold_signals": ["付费咨询、盐选、带货等分成口径并不固定，更适合作为后台或签约口径理解。", "更适合深度问答、专业科普、长文和结构化清单内容。"]},
    "小红书": {"primary_paths": ["店铺商品转化", "数字产品", "轻咨询或私信线索", "蒲公英商单"], "best_content_formats": ["收藏清单", "前后对比", "模板展示", "轻教程"], "offer": "模板包、清单卡、轻咨询、低客单数字产品", "cta": "收藏加评论关键词领取，优先做轻量动作", "proof": "强场景图、真实使用细节、低门槛操作感", "kpi": ["收藏率", "评论或私信关键词率", "店铺点击率"], "risk_controls": ["避免过强专家口吻", "避免硬广感", "视觉审美必须过关"], "monetization_stage": "视觉驱动转化", "threshold_signals": ["蒲公英博主侧常见显性门槛是专业号认证、5000+粉丝、无违规。", "商家侧技术服务费按类目和政策口径波动，不适合写成固定费率。"]},
    "抖音": {"primary_paths": ["橱窗/联盟带货", "直播承接", "评论关键词资料", "星图商单"], "best_content_formats": ["错误纠正", "三步解决", "强对比演示", "低成本试错"], "offer": "商品清单、工具组合、直播承接、评论区关键词资料", "cta": "主页、橱窗、评论关键词三选一，不要并发多个CTA", "proof": "首屏结论、镜头内可视化动作、口播节奏", "kpi": ["3秒完播率", "主页点击率", "商品点击率", "直播承接率"], "risk_controls": ["避免长句", "避免虚构收益", "避免过多空话"], "monetization_stage": "短流量导购", "threshold_signals": ["实名认证后可申请基础带货权限，1000粉以下通常只有橱窗权限。", "1000粉后通常才能进一步开直播间和短视频带货权限。", "星图个人达人常见平台服务费口径约5%，MCN对公常见口径约3%。"]},
    "西瓜视频": {"primary_paths": ["中长视频流量收益", "系列内容导流", "商品卡或头条体系联动", "知识型资料包"], "best_content_formats": ["3到8分钟横屏母体视频", "案例拆解", "流程教程", "系列合集"], "offer": "完整清单、横屏系列、资料包、头条联动阅读", "cta": "收藏本集并查看简介清单，承接系列下一条", "proof": "横屏完整叙事、步骤演示、案例或测试环境说明", "kpi": ["平均观看时长", "完播率", "收藏率", "系列追更率"], "risk_controls": ["避免短视频式强硬催促", "避免空镜堆砌", "封面和标题要一致"], "monetization_stage": "母体内容沉淀", "threshold_signals": ["西瓜更适合作为中长视频母体平台，支持16:9横版、高分辨率和定时发布。", "头条加西瓜体系的商品卡和收益口径会随账号状态与政策变化，不宜硬写固定RPM。"]},
    "B站": {"primary_paths": ["悬赏带货", "花火商单", "资源包转化", "充电计划"], "best_content_formats": ["横评", "流程演示", "实测结论", "资料包延展"], "offer": "完整清单、资源包、工具表、评论区置顶资料", "cta": "三连加评论关键词领取资料包", "proof": "测试上下文、对比证据、观看时长价值感", "kpi": ["平均观看时长", "三连率", "评论关键词率"], "risk_controls": ["避免空洞热血腔", "避免浅层listicle", "封面要有强对比点"], "monetization_stage": "长内容转化", "threshold_signals": ["花火常见入驻信号是实名、18岁以上、1万粉以上、近30天有原创发布。", "还要满足电磁力、创作分和信用分等平台侧评估要求。"]},
    "微博": {"primary_paths": ["微任务商单", "广告共享计划", "单链接导流"], "best_content_formats": ["热点快评", "单视频博文", "图文清单", "热搜延伸"], "offer": "热点观点卡、同款清单、活动或商品导流", "cta": "评论互动加单链接导购，不要多跳转", "proof": "时效性、观点浓缩、明确标签", "kpi": ["互动率", "转评比", "单条链接点击率"], "risk_controls": ["避免同质化热点", "避免多链接分散", "注意广告规范"], "monetization_stage": "热点快反转化", "threshold_signals": ["V+订阅型内容常见结算口径是3:7，博主侧常见分成7。", "微博问答围观收入常见有10%平台分成口径，iOS还可能受苹果渠道费影响。"]},
    "公众号": {"primary_paths": ["流量主", "文章内商品或服务转化", "资料包或私域咨询"], "best_content_formats": ["周报", "深度清单", "行业快报", "操作指南"], "offer": "订阅专栏、资料包、企业咨询清单", "cta": "文末引导关注系列或领取扩展资料", "proof": "来源链接、时间标记、结构完整", "kpi": ["打开率", "阅读完成率", "资料领取率"], "risk_controls": ["避免标题党过度", "避免信源不明", "注意长期搜索价值"], "monetization_stage": "沉淀型转化", "threshold_signals": ["流量主针对原创文章的广告分成常见口径约70%，开通门槛已降到500粉。", "微信文章目前支持挂更多商品链接，适合做沉淀后转化。"]},
    "头条": {"primary_paths": ["图文流量收益", "商品卡带货", "专栏延展"], "best_content_formats": ["长图文故事", "热点解读", "避坑合集", "信息差整理"], "offer": "系列专题、工具合集、低门槛带货卡", "cta": "收藏关注系列更新，或查看相关商品卡", "proof": "多段转折、长文耐读性、强标题", "kpi": ["阅读时长", "读完率", "粉丝转化率"], "risk_controls": ["避免低质搬运感", "避免无来源猎奇", "避免段落过散"], "monetization_stage": "规模化图文收益", "threshold_signals": ["商品卡常见开通信号是头条+西瓜总粉过1万、信用分100并通过审核。", "视频或图文收益口径会综合播放、互动、时长和广告价值，不宜硬套固定RPM。"]},
}

READINESS_RULES: Dict[str, Dict[str, str]] = {
    "知乎": {"current_focus": "沉淀", "next_focus": "带货", "why_now": "知乎更适合先做可搜索、可收藏的专业内容，再承接商品卡和清单转化。"},
    "小红书": {"current_focus": "流量", "next_focus": "带货", "why_now": "小红书先验证视觉和收藏率，再承接店铺、模板包和商单更稳。"},
    "抖音": {"current_focus": "流量", "next_focus": "带货", "why_now": "抖音先跑停留和主页点击，跑顺之后再接橱窗、评论关键词和直播。"},
    "西瓜视频": {"current_focus": "沉淀", "next_focus": "带货", "why_now": "西瓜更适合做母体内容和系列沉淀，先把观看时长和系列追更做起来。"},
    "B站": {"current_focus": "沉淀", "next_focus": "商单", "why_now": "B站先做系列感和证据密度，形成可信栏目后更适合花火和资源包转化。"},
    "微博": {"current_focus": "流量", "next_focus": "商单", "why_now": "微博更适合热点快反和单链路导流，先做互动密度再接微任务或广告共享。"},
    "公众号": {"current_focus": "沉淀", "next_focus": "带货", "why_now": "公众号天然适合留存和复访，先做深度内容和资料包，再接商品和服务。"},
    "头条": {"current_focus": "流量", "next_focus": "带货", "why_now": "头条先靠长图文拿规模阅读，再用商品卡和栏目延展承接收益。"},
}


def infer_plan(platform: str) -> Dict[str, Any]:
    return PLATFORM_PLANS.get(platform, {"primary_paths": ["内容分发", "咨询转化"], "best_content_formats": ["结构化内容"], "offer": "清单或资料包", "cta": "评论关键词领取", "proof": "明确场景和结论", "kpi": ["互动率", "转化率"], "risk_controls": ["避免夸大宣传"], "monetization_stage": "基础转化", "threshold_signals": ["具体门槛应以平台后台和最新规则为准。"]})


def infer_readiness(platform: str, content_ready: bool) -> Dict[str, Any]:
    base = READINESS_RULES.get(platform, {"current_focus": "流量", "next_focus": "带货", "why_now": "当前先验证内容和互动，再推进更重的商业动作。"})
    plan = infer_plan(platform)
    return {"current_focus": base["current_focus"], "next_focus": base["next_focus"], "why_now": base["why_now"], "content_ready": content_ready, "account_threshold_status": "unknown", "blocked_by": plan.get("threshold_signals", []), "best_offer_now": plan.get("offer", "")}


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
    return sorted([str(k) for k in plans.keys() if str(k).strip()])
'''

for name, content in files.items():
    (root / name).write_text(textwrap.dedent(content), encoding='utf-8')
