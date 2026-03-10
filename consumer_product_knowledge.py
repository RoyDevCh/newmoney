#!/usr/bin/env python3
"""Lightweight product knowledge scaffolding for high-decision tech content."""

from __future__ import annotations

from typing import Any, Dict, List


PRODUCT_KNOWLEDGE: Dict[str, Dict[str, Any]] = {
    "扫地机器人": {
        "decision_factors": ["避障稳定性", "毛发缠绕处理", "基站维护成本", "大户型续航", "拖地后的返工率"],
        "budget_bands": [
            {"range": "1500-2500", "fit": "小户型、租房、基础清洁", "watch": "看路径稳定和基础避障，不要只看吸力"},
            {"range": "2500-3500", "fit": "普通家庭、养宠、想更省心", "watch": "重点看防缠绕、基站维护、拖地稳定性"},
            {"range": "3500+", "fit": "大户型、重度养宠、追求更少返工", "watch": "重点看复杂场景稳定性和长期维护成本"},
        ],
        "brand_positions": [
            "石头：通常更容易和稳定、路径规划、综合均衡联系在一起",
            "追觅：更容易和功能堆料、清洁能力、参数竞争联系在一起",
            "科沃斯：品牌认知强，但更需要看具体代际和型号口碑分化",
            "云鲸：更容易和拖地、省心、基站体验联系在一起，但要看是否适合你的清洁偏好",
        ],
        "scenarios": [
            "养宠家庭：优先看防缠绕、滚刷维护、边角返工率",
            "大户型：优先看建图稳定、断点续扫、长时间任务表现",
            "有娃家庭：优先看拖地后的即时干爽和餐椅区域清洁",
        ],
        "avoid": [
            "不要只看吸力数字",
            "不要忽略耗材和维护时间成本",
            "不要把所有需求都压在一台机器上",
        ],
        "keywords": ["扫地机器人推荐", "石头 追觅 科沃斯 云鲸", "预算分段", "养宠家庭", "大户型"],
    },
    "智能手表": {
        "decision_factors": ["系统生态", "续航", "运动数据和GPS", "健康监测", "佩戴舒适度"],
        "review_dimensions": [
            {"name": "健康功能", "why": "不是只看功能数量，而是看哪些功能真正会长期用到、哪些只是发布会卖点"},
            {"name": "运动与 GPS", "why": "决定跑步、骑行、健身记录是否靠谱，也决定它更像日常表还是训练表"},
            {"name": "外观与材质", "why": "外观、材质、表壳厚度和重量会直接影响日常佩戴意愿"},
            {"name": "续航与充电节奏", "why": "很多人最终弃戴手表，不是因为功能少，而是因为充电和佩戴节奏太烦"},
            {"name": "系统生态与联动", "why": "Apple、华为、Garmin 的真正差异，很多时候不在单点功能，而在整套体系"},
            {"name": "佩戴舒适度", "why": "尺寸、厚度、重量和表带适配度决定你会不会愿意每天戴"},
        ],
        "previous_gen_compare": [
            "和上一代比，先看健康功能是新增、补强还是只是口径更新。",
            "和上一代比，要单独看外观材质、厚度、重量、边框和耐用性，而不是只看功能列表。",
            "和上一代比，续航、充电节奏和日常佩戴习惯是否真的改善，通常比单个新功能更重要。",
        ],
        "peer_compare": [
            "同品类横向对比时，Apple 更偏生态联动和日常完整体验，华为更偏续航与安卓兼容，Garmin 更偏训练与路线能力。",
            "同价位对比时，优先比较健康功能、运动记录、材质和重量、续航节奏、生态限制，不要只比较单个参数。",
        ],
        "budget_bands": [
            {"range": "1000-2000", "fit": "入门记录、轻运动、基础通知", "watch": "看续航和基础体验，不要被参数清单带偏"},
            {"range": "2000-3000", "fit": "大多数通勤和健身用户", "watch": "看生态协同、健康功能和长期佩戴体验"},
            {"range": "3000+", "fit": "重度运动、苹果生态、专业训练", "watch": "看生态闭环、专业运动数据和长期稳定性"},
        ],
        "brand_positions": [
            "苹果：更适合已经深度在 iPhone 生态里的用户，强项是系统联动和日常体验",
            "华为：更适合看重续航、健康功能和安卓兼容性的用户",
            "佳明：更适合跑步、骑行、铁三等训练导向更强的人群",
            "小米 / OPPO / vivo：更适合预算敏感、想先满足基础记录和通知的人群",
        ],
        "series_guidance": [
            "苹果体系：Apple Watch SE 3 更适合预算敏感、想先满足基础智能体验的人；Series 11 更适合多数 iPhone 用户的日常佩戴和健康记录；Ultra 3 更适合户外、训练和高预算人群。",
            "华为体系：WATCH 5 更偏旗舰日常智能体验；WATCH GT 6 / GT 6 Pro 更偏续航、健康和通勤健身兼顾；WATCH GT Runner 2 更偏跑步和训练导向。",
            "佳明体系：Forerunner 265 更适合多数跑步入门到进阶用户；Forerunner 570 更适合想要更新一代训练体验的人；Forerunner 970 更适合更重度训练和路线地图需求的人。",
        ],
        "series_matrix": [
            {
                "brand": "Apple",
                "series": "Apple Watch SE 3",
                "fit": "预算敏感、第一次买、主要看通知和基础健康记录的 iPhone 用户",
                "not_fit": "重度训练和高预算人群",
                "focus": "基础智能体验、苹果生态入门",
            },
            {
                "brand": "Apple",
                "series": "Apple Watch Series 11",
                "fit": "多数 iPhone 用户、通勤 + 健身 + 健康记录",
                "not_fit": "安卓用户、只看长续航的人",
                "focus": "均衡主力款、生态联动",
            },
            {
                "brand": "Apple",
                "series": "Apple Watch Ultra 3",
                "fit": "户外、训练、高预算用户",
                "not_fit": "只想买基础智能表的人",
                "focus": "更强训练和户外场景",
            },
            {
                "brand": "HUAWEI",
                "series": "WATCH 5",
                "fit": "偏旗舰日常智能体验、看重健康功能的人",
                "not_fit": "只想低预算入门的人",
                "focus": "旗舰感、健康和日常体验",
            },
            {
                "brand": "HUAWEI",
                "series": "WATCH GT 6 / GT 6 Pro",
                "fit": "通勤 + 健身均衡、看重续航的人",
                "not_fit": "只看专业训练指标的人",
                "focus": "续航、健康、综合均衡",
            },
            {
                "brand": "HUAWEI",
                "series": "WATCH GT Runner 2",
                "fit": "偏跑步和训练导向的安卓用户",
                "not_fit": "只看通知和日常佩戴的人",
                "focus": "跑步训练导向",
            },
            {
                "brand": "Garmin",
                "series": "Forerunner 265",
                "fit": "多数跑步入门到进阶用户",
                "not_fit": "只想买通勤型智能表的人",
                "focus": "跑步主力入门到进阶",
            },
            {
                "brand": "Garmin",
                "series": "Forerunner 570",
                "fit": "想升级训练体验的跑者",
                "not_fit": "只想基础运动记录的人",
                "focus": "训练体验升级",
            },
            {
                "brand": "Garmin",
                "series": "Forerunner 970",
                "fit": "高预算、重度训练和地图路线需求用户",
                "not_fit": "通勤和轻运动为主的人",
                "focus": "高端训练与路线能力",
            },
        ],
        "shortlist": [
            {
                "name": "Apple Watch SE 3",
                "for": "iPhone 用户、第一次买、预算更敏感",
                "why": "先满足苹果生态里的基础智能体验，不必一上来就冲高端",
            },
            {
                "name": "Apple Watch Series 11",
                "for": "多数 iPhone 用户、通勤和健身都要兼顾",
                "why": "均衡主力款，适合大多数不想纠结的人",
            },
            {
                "name": "Apple Watch Ultra 3",
                "for": "户外、训练、高预算用户",
                "why": "更适合明确会用到更强训练和户外能力的人",
            },
            {
                "name": "HUAWEI WATCH GT 6 / GT 6 Pro",
                "for": "安卓用户、看重续航和健康、想日常佩戴更省心",
                "why": "在通勤、健康和续航之间更容易拿到平衡",
            },
            {
                "name": "HUAWEI WATCH 5",
                "for": "想要旗舰感和更完整日常体验的安卓用户",
                "why": "更偏旗舰日常智能体验，而不是纯训练工具",
            },
            {
                "name": "Garmin Forerunner 265",
                "for": "跑步入门到进阶用户",
                "why": "训练导向足够明确，但没有一上来就重到高端",
            },
            {
                "name": "Garmin Forerunner 570 / 970",
                "for": "更重度训练、路线和恢复数据需求更强的人",
                "why": "更适合已经明确知道自己需要训练能力的人",
            },
        ],
        "official_sources": [
            "https://www.apple.com/apple-watch-se-3/",
            "https://www.apple.com/apple-watch-series-11/",
            "https://www.apple.com/apple-watch-ultra-3/",
            "https://consumer.huawei.com/cn/wearables/watch-5/",
            "https://consumer.huawei.com/cn/wearables/watch-gt6",
            "https://consumer.huawei.com/cn/wearables/watch-gt6-pro/",
            "https://consumer.huawei.com/ee/wearables/watch-gt-runner-2/",
            "https://ph.garmin.com/news/press-release/news-2025-jun-forerunner-570-970/",
            "https://static.garmin.com/pumac/Forerunner%20265-265S_DoC-UK.pdf",
        ],
        "scenarios": [
            "通勤办公：优先看消息通知、支付、续航和佩戴舒适度",
            "健身跑步：优先看GPS稳定、心率数据、训练计划和恢复指标",
            "苹果生态：先看和 iPhone / AirPods / 健康数据的协同深度",
        ],
        "avoid": [
            "不要只看功能表，不看你用的是 iPhone 还是安卓",
            "不要把专业运动表和日常智能表放在一个标准里硬比",
            "不要忽略表盘尺寸、重量和长期佩戴舒适度",
        ],
        "keywords": ["智能手表怎么选", "苹果 华为 佳明", "运动手表", "通勤", "预算分段"],
    },
    "路由器": {
        "decision_factors": ["户型覆盖", "多设备稳定性", "回程方式", "运营商宽带匹配", "管理门槛"],
        "review_dimensions": [
            {"name": "覆盖与户型匹配", "why": "单路由够不够、需不需要 Mesh，决定实际体验上限"},
            {"name": "多设备稳定性", "why": "真正的家庭体验往往坏在设备一多就掉速、掉线或卡顿"},
            {"name": "接口与回程", "why": "2.5G / 10G 口、回程方式、NAS 需求会决定是否值得上高规格"},
            {"name": "管理体验", "why": "普通家庭和高阶用户对路由器的要求，很多时候差在可玩性和易用性"},
        ],
        "previous_gen_compare": [
            "和上一代比，先看 Wi-Fi 标准、接口规格、芯片代际和长时间稳定性是否真的升级。",
            "和上一代比，要看是不是只是从参数表升级成营销升级，而不是家庭真实体验升级。",
        ],
        "peer_compare": [
            "同品类对比时，优先比较覆盖、稳定性、回程、接口和管理体验。",
            "同价位对比时，不要只比理论速率，要比家庭真实环境下的组网价值。",
        ],
        "budget_bands": [
            {"range": "200-400", "fit": "租房、小户型、设备不多", "watch": "先看稳定和设置是否简单"},
            {"range": "400-800", "fit": "普通家庭、多设备", "watch": "看多设备并发、信号覆盖和管理能力"},
            {"range": "800+", "fit": "大户型、NAS、重度游戏或智能家居设备多", "watch": "看Mesh、回程方式和长期稳定性"},
        ],
        "brand_positions": [
            "华硕 / 网件：更容易和高阶玩家、可玩性、管理能力联系在一起",
            "TP-Link / 小米：更适合多数普通家庭，关键是具体价位段和稳定性",
            "中兴 / 华为：更适合关注运营商环境兼容和大厂生态的人群",
        ],
        "series_guidance": [
            "华硕体系：RT-BE82U / RT-BE86U 更适合多数高需求家庭；RT-BE88U 更适合高带宽、多网口、重度玩家和 NAS 用户。",
            "华为体系：路由 X1 更适合更看重设计和 Wi-Fi 7 日常体验的人；路由 BE7 更偏旗舰单路由；凌霄子母路由 Q7 更适合大户型和多房间覆盖。",
            "TP-Link 体系：TL-7DR6450 / TL-7DR7250 这类易展 Wi-Fi 7 路由更适合普通家庭到大户型；K75 / K82 这类套装更适合直接做全屋 Mesh。",
            "小米体系：BE6500 / BE6500 Pro 更适合预算敏感、想要 Wi-Fi 7 和智能家居联动的用户。",
        ],
        "series_matrix": [
            {
                "brand": "ASUS",
                "series": "RT-BE82U / RT-BE86U",
                "fit": "对稳定性、功能完整度和可玩性有要求的家庭用户",
                "not_fit": "只想低预算够用的人",
                "focus": "高阶家庭主路由、AiMesh、功能完整",
            },
            {
                "brand": "ASUS",
                "series": "RT-BE88U",
                "fit": "大带宽、NAS、多网口、重度玩家",
                "not_fit": "普通百兆到千兆宽带的轻度用户",
                "focus": "10G / 2.5G 接口、多设备和高负载",
            },
            {
                "brand": "HUAWEI",
                "series": "路由 X1 / X1 Pro",
                "fit": "看重 Wi-Fi 7 日常体验、设计和华为生态的人",
                "not_fit": "更看重高阶可玩性的人",
                "focus": "华为生态、日常体验、家用易用性",
            },
            {
                "brand": "HUAWEI",
                "series": "路由 BE7",
                "fit": "想买旗舰单路由、宽带更高、设备更多的家庭",
                "not_fit": "更适合直接上子母路由的大户型",
                "focus": "Wi-Fi 7 旗舰单路由",
            },
            {
                "brand": "HUAWEI",
                "series": "凌霄子母路由 Q7",
                "fit": "大户型、多房间、对全屋覆盖更敏感的家庭",
                "not_fit": "小户型单路由需求",
                "focus": "分布式组网、覆盖优先",
            },
            {
                "brand": "TP-Link",
                "series": "TL-7DR6450 / TL-7DR7250",
                "fit": "多数普通家庭到大户型用户",
                "not_fit": "追求极高可玩性的玩家",
                "focus": "家用 Wi-Fi 7、易展 Mesh、性价比",
            },
            {
                "brand": "TP-Link",
                "series": "K75 / K82 易展套装",
                "fit": "想一步到位做全屋覆盖的人",
                "not_fit": "只需要单路由的小户型",
                "focus": "套装化 Mesh、全屋覆盖",
            },
            {
                "brand": "Xiaomi",
                "series": "BE6500 / BE6500 Pro",
                "fit": "预算敏感、想要 Wi-Fi 7 和智能家居联动的家庭",
                "not_fit": "重度 NAS 或高带宽多网口用户",
                "focus": "价格友好、米家联动、Wi-Fi 7 入门",
            },
        ],
        "shortlist": [
            {
                "name": "TP-Link TL-7DR6450 / TL-7DR7250",
                "for": "多数普通家庭到大户型用户",
                "why": "更容易在价格、覆盖和易展组网上拿到平衡",
            },
            {
                "name": "华为路由 X1 / BE7",
                "for": "看重华为生态和家用易用性的用户",
                "why": "更偏家用日常体验，不需要折腾太多设置",
            },
            {
                "name": "华为凌霄子母路由 Q7",
                "for": "大户型、多房间、墙体复杂的家庭",
                "why": "比单路由更适合先解决覆盖问题",
            },
            {
                "name": "华硕 RT-BE82U / RT-BE86U",
                "for": "对稳定性和可玩性要求更高的家庭",
                "why": "功能完整，更适合高需求主路由场景",
            },
            {
                "name": "华硕 RT-BE88U",
                "for": "NAS、多网口、高带宽和重度玩家",
                "why": "更适合明确知道自己需要高接口规格的人",
            },
            {
                "name": "小米 BE6500 / BE6500 Pro",
                "for": "预算敏感、想做 Wi-Fi 7 入门和米家联动的人",
                "why": "更适合把预算留给全屋设备，而不是全压在主路由上",
            },
        ],
        "official_sources": [
            "https://www.asus.com.cn/networking-iot-servers/wifi-routers/asus-wifi-routers/rt-be82u/",
            "https://www.asus.com.cn/networking-iot-servers/wifi-routers/asus-wifi-routers/rt-be86u/",
            "https://www.asus.com.cn/networking-iot-servers/wifi-routers/asus-gaming-routers/rt-be88u/",
            "https://consumer.huawei.com/cn/routers/x1/",
            "https://consumer.huawei.com/cn/routers/be7/",
            "https://consumer.huawei.com/cn/routers/q7-ethernet-cable/",
            "https://www.tp-link.com.cn/product_4142.html",
            "https://www.tp-link.com.cn/product_3627.html",
            "https://www.tp-link.com.cn/product_3461.html",
            "https://www.tp-link.com.cn/m/product_4162.html",
            "https://www.mi.com/xiaomi-routers/6500pro",
            "https://www.mi.com/xiaomi-routers/be-6500",
        ],
        "scenarios": [
            "租房：先看设置简单和性价比，不必一上来就追高端规格",
            "大户型：优先看 Mesh 方案和回程方式",
            "智能家居设备多：优先看多设备在线稳定性和长时间运行表现",
        ],
        "avoid": [
            "不要只看理论速率",
            "不要忽略户型和墙体结构",
            "不要买了高规格却没有匹配的宽带和终端",
        ],
        "keywords": ["路由器推荐", "租房", "大户型", "Mesh", "多设备"],
    },
    "开放式耳机": {
        "decision_factors": ["佩戴稳固性", "漏音控制", "通勤安全感", "运动舒适度", "麦克风表现"],
        "budget_bands": [
            {"range": "300-600", "fit": "尝鲜、轻运动、日常通勤", "watch": "看佩戴和漏音，不要期待完全替代入耳式"},
            {"range": "600-1000", "fit": "通勤 + 运动双需求", "watch": "看声音表现、舒适度和麦克风"},
            {"range": "1000+", "fit": "对舒适度和声音完成度要求更高的人", "watch": "看长时间佩戴、连接稳定性和场景匹配"},
        ],
        "brand_positions": [
            "韶音：更容易和运动场景、安全感、成熟佩戴联系在一起",
            "华为 / 漫步者 / 倍思等：更适合通勤与轻运动结合场景",
        ],
        "scenarios": [
            "通勤：优先看安全感、麦克风和连接稳定",
            "运动：优先看佩戴稳固、防汗和长时间舒适度",
            "办公室：优先看漏音控制和长时间不压耳",
        ],
        "avoid": [
            "不要拿开放式和降噪入耳式做单维度对比",
            "不要忽略漏音和安静环境使用限制",
        ],
        "keywords": ["开放式耳机推荐", "通勤", "运动", "办公", "漏音"],
    },
}


def infer_product_family(topic: str) -> str:
    current = str(topic or "").strip()
    for family in PRODUCT_KNOWLEDGE:
        if family in current:
            return family
    return ""


def get_product_knowledge(topic: str) -> Dict[str, Any]:
    family = infer_product_family(topic)
    if not family:
        return {}
    data = dict(PRODUCT_KNOWLEDGE.get(family, {}))
    data["product_family"] = family
    return data


def build_knowledge_lines(topic: str, limit: int = 10) -> List[str]:
    data = get_product_knowledge(topic)
    if not data:
        return []
    lines: List[str] = []
    family = data.get("product_family", "")
    factors = data.get("decision_factors", [])
    if factors:
        lines.append(f"{family}核心判断维度：{'、'.join(factors[:5])}")
    for row in data.get("budget_bands", [])[:3]:
        lines.append(f"预算带：{row.get('range', '')} 更适合 {row.get('fit', '')}；筛选时重点看 {row.get('watch', '')}")
    for row in data.get("brand_positions", [])[:3]:
        lines.append(f"品牌定位：{row}")
    for row in data.get("series_guidance", [])[:3]:
        lines.append(f"系列建议：{row}")
    for row in data.get("scenarios", [])[:2]:
        lines.append(f"场景建议：{row}")
    for row in data.get("avoid", [])[:2]:
        lines.append(f"避坑提醒：{row}")
    return lines[:limit]


def build_series_markdown_table(topic: str) -> str:
    data = get_product_knowledge(topic)
    rows = data.get("series_matrix", []) if data else []
    if not rows:
        return ""
    lines = [
        "| 品牌 | 系列 | 更适合谁 | 不太适合谁 | 你主要该看什么 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('brand', '')} | {row.get('series', '')} | {row.get('fit', '')} | {row.get('not_fit', '')} | {row.get('focus', '')} |"
        )
    return "\n".join(lines)


def build_shortlist_markdown(topic: str) -> str:
    data = get_product_knowledge(topic)
    rows = data.get("shortlist", []) if data else []
    if not rows:
        return ""
    lines: List[str] = []
    for row in rows:
        lines.append(f"- `{row.get('name', '')}`：更适合{row.get('for', '')}；理由是{row.get('why', '')}")
    return "\n".join(lines)


def build_sources_markdown(topic: str) -> str:
    data = get_product_knowledge(topic)
    rows = data.get("official_sources", []) if data else []
    if not rows:
        return ""
    return "\n".join(f"- {row}" for row in rows)


def build_review_dimensions_markdown(topic: str) -> str:
    data = get_product_knowledge(topic)
    rows = data.get("review_dimensions", []) if data else []
    if not rows:
        return ""
    lines = [
        "| 评测维度 | 为什么要看 |",
        "| --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row.get('name', '')} | {row.get('why', '')} |")
    return "\n".join(lines)


def build_previous_gen_compare_markdown(topic: str) -> str:
    data = get_product_knowledge(topic)
    rows = data.get("previous_gen_compare", []) if data else []
    if not rows:
        return ""
    return "\n".join(f"- {row}" for row in rows)


def build_peer_compare_markdown(topic: str) -> str:
    data = get_product_knowledge(topic)
    rows = data.get("peer_compare", []) if data else []
    if not rows:
        return ""
    return "\n".join(f"- {row}" for row in rows)
