#!/usr/bin/env python3
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
    return {
        "title": f"{topic}工具清单与红黑榜附件",
        "usage_note": "适合放在正文后半段或评论区置顶，增强可信度与收藏价值。",
        "comparison_table_markdown": table,
        "red_flags": ["功能承诺很多但免费体验极弱的工具或方案", "没有明确适用场景却直接卖高价套餐的内容", "输出看起来顺滑但事实错误率高的方案"],
        "save_cta": "如果你要完整版本，可以在评论区留关键词再补充细分场景版。",
    }


def bilibili_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {
        "title": f"{topic}视频补充资料包",
        "usage_note": "适合做视频简介、评论区置顶或口播结尾的资料补充。",
        "bullet_points": [f"{row['tool']}：适合{row['best_for']}；优势是{row['strength']}；注意{row['watch_out']}。" for row in rows],
        "resource_pack": ["一页版工具选择表", "执行顺序模板", "适用与不适用人群清单"],
        "comment_cta": "评论区留关键词，可继续引导到资料包或后续选题。",
    }


def xigua_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {
        "title": f"{topic}横屏视频补充附件",
        "usage_note": "适合放在视频简介和评论区，用于承接完整清单、流程图和系列下一条。",
        "bullet_points": [
            f"先看{rows[0]['tool']}，因为它更适合{rows[0]['best_for']}。",
            f"再看{rows[1]['tool']}，重点优势是{rows[1]['strength']}。",
            f"如果你要少踩坑，记住{rows[2]['watch_out']}。",
        ],
        "resource_pack": ["横屏长视频分镜清单", "3到8分钟母体结构", "评论区承接关键词模板"],
        "comment_cta": "收藏这条，下一步按简介里的清单顺序执行。",
    }


def xiaohongshu_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {
        "title": f"{topic}收藏型清单",
        "usage_note": "适合做图二、图三文案或评论区补充。",
        "quick_list": [f"{row['tool']}：{row['best_for']}" for row in rows[:4]],
        "save_reason": "让读者一眼知道先试哪一个，不需要看完长文才行动。",
    }


def douyin_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=2)
    return {
        "title": f"{topic}口播补充提示卡",
        "usage_note": "适合做口播提词器备注或评论区清单。",
        "spoken_beats": [
            f"第一类，{rows[0]['tool']}，适合{rows[0]['best_for']}。",
            f"第二类，{rows[1]['tool']}，重点看{rows[1]['strength']}。",
            "别一上来就买最贵的，先把一个场景跑通。",
        ],
        "comment_keyword": "工具清单",
    }


def weibo_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=2)
    return {
        "title": f"{topic}微博快反补充卡",
        "usage_note": "适合置顶评论或单条长图文补充说明。",
        "fast_points": [f"{rows[0]['tool']}适合{rows[0]['best_for']}", f"{rows[1]['tool']}更适合{rows[1]['strength']}"] ,
        "comment_cta": "评论区留关键词，可继续领取完整清单。",
    }


def wechat_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {
        "title": f"{topic}公众号延伸阅读附件",
        "usage_note": "适合放在正文末尾，作为领取资料或系列阅读承接。",
        "sections": ["本期适合谁", "工具对照", "执行顺序建议", "不适合直接照抄的人群提醒"],
        "resource_pack": [row['tool'] for row in rows],
        "article_cta": "回复关键词领取清单版附件。",
    }


def toutiao_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {
        "title": f"{topic}头条长图文附录",
        "usage_note": "适合放在正文末尾，承接收藏、关注和下一篇阅读。",
        "list_points": [f"{row['tool']}：适合{row['best_for']}，注意{row['watch_out']}。" for row in rows],
        "follow_cta": "先收藏这篇，下一篇继续拆具体场景。",
    }


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
