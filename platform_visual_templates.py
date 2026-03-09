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


REAL_IMAGE_SOURCE_PRIORITY: Dict[str, List[str]] = {
    "home_cleaning": ["品牌官方图", "京东/天猫详情页实拍", "B站/小红书测评实拍"],
    "pets": ["真实用户实拍", "品牌官方场景图", "宠物博主测评实拍"],
    "jewelry_style": ["品牌官方佩戴图", "真实上身图", "高质量买家秀"],
    "sports_outdoor": ["品牌官方运动场景图", "真实训练实拍", "测评视频截图"],
    "digital_gear": ["品牌官方产品图", "测评频道实拍", "电商详情页细节图"],
}


BUCKET_MATERIAL_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "home_cleaning": {
        "must_show": ["真实外观比例", "地面/家具场景", "关键刷头或结构细节"],
        "avoid": ["过度磨皮", "假阳光滤镜", "完全看不出尺寸关系的抠图"],
        "query_suffixes": ["机身 实拍", "刷头 细节", "家庭 使用场景", "开箱"],
    },
    "pets": {
        "must_show": ["宠物与用品同框", "真实毛发和环境", "使用姿态自然"],
        "avoid": ["AI 宠物脸", "过度摆拍", "肢体比例失真"],
        "query_suffixes": ["宠物 实拍", "使用场景", "开箱", "上身 效果"],
    },
    "jewelry_style": {
        "must_show": ["材质纹理", "佩戴效果", "尺寸与肤色对比"],
        "avoid": ["塑料感高光", "夸张磨皮", "过曝导致看不清细节"],
        "query_suffixes": ["佩戴 实拍", "细节 图", "上身 效果", "开箱"],
    },
    "sports_outdoor": {
        "must_show": ["真人使用动作", "装备上身比例", "真实环境"],
        "avoid": ["摆拍但看不出功能", "动作失真", "过度 AI 感滤镜"],
        "query_suffixes": ["上身 实拍", "训练 场景", "细节 图", "评测"],
    },
    "digital_gear": {
        "must_show": ["接口/按键/边框", "真实桌面比例", "屏幕或机身细节"],
        "avoid": ["扭曲外壳", "接口数量错误", "AI 生成的假 logo 和假按键"],
        "query_suffixes": ["官方 图", "接口 实拍", "桌面 实拍", "开箱 评测"],
    },
}


PLATFORM_REAL_IMAGE_LAYOUTS: Dict[str, Dict[str, Any]] = {
    ZH: {
        "cover_layout_brief": "用一张横版主图完成首屏信任建立。左侧或中左留标题区，主体必须清楚，最好带一个证据点，例如接口、刷头、佩戴细节或对比对象。",
        "material_slots": [
            {"slot": "封面主图", "purpose": "建立可信度", "orientation": "横版 16:9", "cue": "主体完整可辨认，避免过度文字遮挡"},
            {"slot": "正文细节图", "purpose": "支撑观点", "orientation": "横版或方图", "cue": "补一张关键细节或使用场景图"},
        ],
    },
    XHS: {
        "cover_layout_brief": "首图必须像真实笔记。优先 3:4 竖图，保留顶部标题区，主体靠中下，环境干净，避免像商品详情页截图。",
        "material_slots": [
            {"slot": "首图主图", "purpose": "停留与收藏", "orientation": "竖版 3:4", "cue": "一张高颜值真实场景图，主题物清晰"},
            {"slot": "细节补图", "purpose": "提升保存率", "orientation": "竖版或方图", "cue": "近景细节或前后对比"},
            {"slot": "使用场景图", "purpose": "增强代入", "orientation": "竖版", "cue": "真实使用环境，不要硬广摆拍"},
        ],
    },
    WB: {
        "cover_layout_brief": "微博优先一张能快速说明结论的卡片图。图里只保留一个主物体和一个证据点，避免信息堆叠。",
        "material_slots": [
            {"slot": "快评主图", "purpose": "快速表达判断", "orientation": "横版 4:3", "cue": "主体加一个细节点，便于读图即懂"},
        ],
    },
    WX: {
        "cover_layout_brief": "公众号头图以横版 banner 为主，用一张主图做信任建立，文字区不要压住关键细节。",
        "material_slots": [
            {"slot": "头图", "purpose": "文章开场信任", "orientation": "横版 900:383", "cue": "主体完整，左中留标题位"},
            {"slot": "正文证据图", "purpose": "承接步骤和案例", "orientation": "横版或方图", "cue": "对应文中某个结论的实拍图"},
        ],
    },
    TT: {
        "cover_layout_brief": "头条封面可以更直接，但不能廉价。建议一张主图加一个副证据物，标题区在左侧。",
        "material_slots": [
            {"slot": "封面主图", "purpose": "拉点击", "orientation": "横版 3:2", "cue": "主体明显，背景简洁"},
            {"slot": "正文场景图", "purpose": "提升读完率", "orientation": "横版或方图", "cue": "使用场景或前后对比"},
        ],
    },
    DY: {
        "cover_layout_brief": "短视频封面优先真实截帧或真实场景图。首屏只强调一个冲突点，不要过多文案。",
        "material_slots": [
            {"slot": "封面关键帧", "purpose": "首屏停留", "orientation": "竖版 9:16", "cue": "主体大且清晰，表意强"},
            {"slot": "中段证据帧", "purpose": "视频中段支撑", "orientation": "竖版", "cue": "接口、细节、对比或使用结果"},
        ],
    },
    XG: {
        "cover_layout_brief": "西瓜优先横版真实主图，最好来自视频关键帧或同主题实拍图。封面要看起来像真实评测，不像 AI 海报。",
        "material_slots": [
            {"slot": "横版封面", "purpose": "长视频点击", "orientation": "横版 16:9", "cue": "主体 + 证据点 + 标题留白"},
            {"slot": "中段场景帧", "purpose": "支撑信息密度", "orientation": "横版", "cue": "真实使用场景或对比镜头"},
            {"slot": "结论证据帧", "purpose": "增强可信度", "orientation": "横版", "cue": "细节 close-up 或参数对比截图"},
        ],
    },
    BILI: {
        "cover_layout_brief": "B站封面要像测评频道缩略图。横版主图清楚，标题块单独留位，最好加一个真实细节或实测证据。",
        "material_slots": [
            {"slot": "封面缩略图", "purpose": "建立评测感", "orientation": "横版 16:9", "cue": "主体清楚，标题区分离"},
            {"slot": "细节证据帧", "purpose": "增强可信度", "orientation": "横版", "cue": "接口、做工、测试结果或对比对象"},
            {"slot": "场景帧", "purpose": "保持观看", "orientation": "横版", "cue": "真实桌面/家庭/运动场景"},
        ],
    },
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


def build_manual_asset_checklist(bucket: str, platform: str) -> List[str]:
    guidance = BUCKET_MATERIAL_GUIDANCE.get(bucket, {})
    must_show = guidance.get("must_show", [])
    avoid = guidance.get("avoid", [])
    checklist: List[str] = [
        "先确认图片里的主体与标题说的是同一类产品或场景，不要拿相似款硬替。",
        "优先选自然光或正常室内光的真实图，避免过重滤镜和过度锐化。",
        "封面文字不要盖住决定信任的关键细节，例如接口、刷头、材质纹理或佩戴位置。",
    ]
    if must_show:
        checklist.append(f"本题材必须看得见：{'、'.join(must_show)}。")
    if avoid:
        checklist.append(f"本题材不要用：{'、'.join(avoid)}。")
    if platform in {DY, XG, BILI}:
        checklist.append("视频封面优先真实视频截帧，其次才是静态实拍图。")
    return checklist


def build_material_slots(topic: str, bucket: str, platform: str, image_strategy: str) -> List[Dict[str, Any]]:
    if image_strategy != "real_reference_preferred":
        return []
    layout = PLATFORM_REAL_IMAGE_LAYOUTS.get(platform, {})
    slots = layout.get("material_slots", [])
    guidance = BUCKET_MATERIAL_GUIDANCE.get(bucket, {})
    suffixes = guidance.get("query_suffixes", [])
    must_show = guidance.get("must_show", [])
    avoid = guidance.get("avoid", [])
    result: List[Dict[str, Any]] = []
    for index, slot in enumerate(slots):
        suffix = suffixes[min(index, len(suffixes) - 1)] if suffixes else "实拍"
        result.append(
            {
                **slot,
                "search_query": f"{topic} {suffix}".strip(),
                "must_show": must_show,
                "avoid": avoid,
            }
        )
    return result


def build_cover_layout_brief(platform: str, image_strategy: str) -> str:
    if image_strategy != "real_reference_preferred":
        return "当前题材允许直接使用 ComfyUI 封面，先保证画面主题明确，再保证标题区干净可读。"
    return PLATFORM_REAL_IMAGE_LAYOUTS.get(platform, {}).get(
        "cover_layout_brief",
        "优先用一张真实主图建立信任，再补一张细节或场景图支撑正文。",
    )


def build_source_priority(bucket: str, image_strategy: str) -> List[str]:
    if image_strategy != "real_reference_preferred":
        return ["ComfyUI 主生成", "必要时人工替换为更贴题的参考图"]
    return REAL_IMAGE_SOURCE_PRIORITY.get(bucket, ["品牌官方图", "真实测评图", "电商详情图"])


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
        bucket = str(theme.get("theme_name", "")).strip()
        image_strategy = str(merged.get("image_strategy", "comfy_generated_ok")).strip() or "comfy_generated_ok"
        merged["topic"] = topic
        merged["reference_search_queries"] = build_reference_search_queries(
            topic=topic,
            bucket=bucket,
            platform=platform,
        )
        merged["cover_workflow"] = (
            "use_real_reference_first"
            if image_strategy == "real_reference_preferred"
            else "allow_comfy_generation"
        )
        merged["material_workflow"] = (
            "manual_real_image_curation"
            if image_strategy == "real_reference_preferred"
            else "comfy_generation"
        )
        merged["cover_layout_brief"] = build_cover_layout_brief(platform, image_strategy)
        merged["source_priority"] = build_source_priority(bucket, image_strategy)
        merged["manual_asset_checklist"] = build_manual_asset_checklist(bucket, platform)
        merged["material_slots"] = build_material_slots(
            topic=topic,
            bucket=bucket,
            platform=platform,
            image_strategy=image_strategy,
        )
        result[platform] = merged
    return result


def attach_visual_templates(pack: Dict[str, Any]) -> Dict[str, Any]:
    pack["visual_templates"] = build_visual_templates(pack)
    return pack
