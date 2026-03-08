#!/usr/bin/env python3
"""Build publish-ready appendices such as tables, lists, and CTAs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


AI_TOOL_CATALOG = [
    {
        "tool": "文心一言",
        "best_for": "中文写作、提纲整理、基础办公问答",
        "strength": "中文理解和通用办公表达较稳",
        "watch_out": "复杂长任务时需要人工拆解需求",
        "pricing_note": "先从免费能力试用",
    },
    {
        "tool": "Kimi",
        "best_for": "长文档归纳、资料对读、信息汇总",
        "strength": "长文本处理体验较好",
        "watch_out": "摘要结果仍要人工复核事实点",
        "pricing_note": "适合先验证长文档场景",
    },
    {
        "tool": "通义千问",
        "best_for": "多轮任务推进、通用办公协作",
        "strength": "多任务衔接和稳定性较均衡",
        "watch_out": "复杂输出最好给明确模板",
        "pricing_note": "先跑固定模板流程更稳",
    },
    {
        "tool": "秘塔 AI",
        "best_for": "检索、资料收集、网页信息整合",
        "strength": "搜集和归纳效率较高",
        "watch_out": "引用内容要回到原来源复核",
        "pricing_note": "适合做前置检索层",
    },
    {
        "tool": "讯飞星火",
        "best_for": "语音转写、会议纪要、口语整理",
        "strength": "音频转文字场景适配度高",
        "watch_out": "专有名词与数字信息要二次检查",
        "pricing_note": "优先用于会议和访谈整理",
    },
]


def load_pack(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def tool_rows_for_topic(topic: str) -> List[Dict[str, str]]:
    topic = topic.strip()
    if any(key in topic for key in ["AI办公", "AI工具", "办公自动化", "效率", "内容创作"]):
        return AI_TOOL_CATALOG
    if len(topic) < 4 or "?" in topic or "？" in topic:
        return AI_TOOL_CATALOG
    return [
        {
            "tool": "待补充",
            "best_for": "围绕当前主题补充工具表",
            "strength": "可作为清单附件",
            "watch_out": "发布前需人工确认",
            "pricing_note": "先从免费方案试错",
        }
    ]


def ensure_rows(rows: List[Dict[str, str]], minimum: int = 2) -> List[Dict[str, str]]:
    if not rows:
        rows = AI_TOOL_CATALOG[:]
    while len(rows) < minimum:
        rows = rows + AI_TOOL_CATALOG[: minimum - len(rows)]
    return rows[: max(minimum, len(rows))]


def zhihu_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    table = "\n".join(
        [
            "| 工具 | 适合场景 | 优势 | 使用提醒 | 成本建议 |",
            "| --- | --- | --- | --- | --- |",
            *[
                f"| {r['tool']} | {r['best_for']} | {r['strength']} | {r['watch_out']} | {r['pricing_note']} |"
                for r in rows
            ],
        ]
    )
    return {
        "title": f"{topic}工具清单与红黑榜附件",
        "usage_note": "适合放在正文后半段或评论区置顶，增强可信度与收藏价值。",
        "comparison_table_markdown": table,
        "red_flags": [
            "功能承诺很多但免费体验极弱的工具",
            "没有明确适用场景却直接卖年费套餐的工具",
            "输出看起来顺滑但事实错误率高的工具",
        ],
        "save_cta": "如果你要完整版清单，可在评论区留“清单”，再按需补充细分场景版。",
    }


def bilibili_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {
        "title": f"{topic}视频补充资料包",
        "usage_note": "适合做视频简介、评论区置顶或口播结尾的资料补充。",
        "bullet_points": [
            f"{row['tool']}：适合{row['best_for']}；优势是{row['strength']}；注意{row['watch_out']}。"
            for row in rows
        ],
        "resource_pack": [
            "一页版工具选择表",
            "办公自动化场景模板清单",
            "新手上手顺序建议",
        ],
        "comment_cta": "评论区留“工具表”，可继续引导到资料包或后续选题。",
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
        "fast_points": [
            f"{rows[0]['tool']}适合{rows[0]['best_for']}",
            f"{rows[1]['tool']}更适合{rows[1]['strength']}",
        ],
        "comment_cta": "评论区留“表格”，可继续领取完整版清单。",
    }


def wechat_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {
        "title": f"{topic}公众号延伸阅读附件",
        "usage_note": "适合放在正文末尾，作为领取资料或系列阅读的承接。",
        "sections": [
            "本期适合谁",
            "推荐工具对照",
            "执行顺序建议",
            "不适合直接照抄的人群提醒",
        ],
        "resource_pack": [row["tool"] for row in rows],
        "article_cta": "回复“资料”领取清单版附件。",
    }


def toutiao_appendix(topic: str) -> Dict[str, Any]:
    rows = ensure_rows(tool_rows_for_topic(topic), minimum=3)
    return {
        "title": f"{topic}头条长图文附录",
        "usage_note": "适合放在正文末尾，承接收藏、关注和下一篇阅读。",
        "list_points": [
            f"{row['tool']}：适合{row['best_for']}，注意{row['watch_out']}" for row in rows
        ],
        "follow_cta": "先收藏这篇，下一篇继续拆具体场景。",
    }


def build_appendices(pack: Dict[str, Any]) -> Dict[str, Any]:
    topic = str(pack.get("topic", "")).strip()
    return {
        "zhihu": zhihu_appendix(topic),
        "bilibili": bilibili_appendix(topic),
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
