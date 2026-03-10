#!/usr/bin/env python3
"""Content formula selection and prompt hints for diversified long-form production."""

from __future__ import annotations

from typing import Any, Dict


ZH = "知乎"


FORMULAS: Dict[str, Dict[str, Any]] = {
    "search_buying_guide": {
        "label": "搜索型选购指南",
        "goal": "承接搜索流量、收藏和商品决策",
        "must_have": ["预算分段", "场景分层", "品牌/系列差异", "不推荐情况", "结论清单"],
    },
    "single_product_review": {
        "label": "单品文章",
        "goal": "围绕单一产品或单一系列做公开资料汇总、观点验证和决策判断",
        "must_have": ["先给结论", "证据口径", "适合谁", "不适合谁", "已确认信息", "待验证信息", "现在买还是等等"],
    },
    "launch_roundup": {
        "label": "新品发布首轮判断",
        "goal": "抓新品发布后的关注窗口，快速沉淀搜索和讨论",
        "must_have": ["发布信息概览", "最值得关注的升级点", "最需要谨慎看的地方", "适合谁", "建议现在买还是等等"],
    },
    "answer_decision": {
        "label": "回答型长答",
        "goal": "直接回答高价值问题，拿赞同、收藏和后续信任",
        "must_have": ["直接回答", "边界条件", "证据和拆解", "例外情况", "行动建议"],
    },
}


SINGLE_PRODUCT_SUBFORMULAS: Dict[str, Dict[str, Any]] = {
    "quick_verdict": {
        "label": "快速结论型「值不值」",
        "goal": "优先解决用户的即时购买判断",
        "must_have": ["一句话结论", "三条最关键理由", "适合谁", "不适合谁", "现在买还是等等"],
        "opening": "首屏三段内必须回答值不值得买，不要先铺背景。",
    },
    "marketing_myth_check": {
        "label": "数据验证型「营销打假」",
        "goal": "拆掉营销口号，把宣传点还原成可验证信息",
        "must_have": ["宣传点是什么", "证据能证实什么", "证据不能证实什么", "真实影响到谁", "待验证项"],
        "opening": "开头先点名最容易被带偏的宣传点，再给证据口径。",
    },
    "scenario_simulation": {
        "label": "体验分层型「买前模拟」",
        "goal": "让不同人群在买前完成自我匹配",
        "must_have": ["用户画像分层", "通勤/运动/家庭等场景判断", "容易买错的人群", "替代选择"],
        "opening": "首屏先告诉读者这款产品更像给哪类人准备的。",
    },
    "engineering_deep_dive": {
        "label": "工程硬核型「拆解 + 跑分」",
        "goal": "围绕架构、拆解、跑分、散热或安全细节建立专业信任",
        "must_have": ["测试或拆解口径", "核心结构变化", "数据与场景解释", "哪些结论仍需长期验证"],
        "opening": "开头先说清测试条件或资料来源，再下判断。",
    },
    "car_launch_manual": {
        "label": "汽车发布专用「上市说明书」",
        "goal": "围绕新车上市信息、参数口径和场景判断做首轮购买建议",
        "must_have": ["上市信息", "续航/补能/智驾口径", "适合谁", "风险点", "建议现在订还是等等"],
        "opening": "开头先给购车判断，再讲参数，不要把文章写成发布会纪要。",
    },
}


def infer_content_formula(topic: str, platform: str = "") -> str:
    current = str(topic or "").strip()
    if platform and platform != ZH:
        return "search_buying_guide"
    if any(hint in current for hint in ["发布", "首发", "发布会", "发布后", "首轮判断", "首批上手"]):
        return "launch_roundup"
    if any(hint in current for hint in ["评测", "值不值得买", "上手", "能买吗", "首批反馈", "体验汇总"]):
        return "single_product_review"
    if any(hint in current for hint in ["如何", "为什么", "怎么看", "有没有必要", "怎么理解", "是否"]):
        return "answer_decision"
    return "search_buying_guide"


def infer_content_subformula(topic: str, platform: str = "") -> str:
    formula = infer_content_formula(topic, platform)
    current = str(topic or "").strip()
    if formula not in {"single_product_review", "launch_roundup"}:
        return ""
    if any(hint in current for hint in ["汽车", "新车", "EV", "纯电", "增程", "插混", "智驾", "上市"]):
        return "car_launch_manual"
    if any(hint in current for hint in ["营销", "打假", "宣传", "吹过", "噱头", "智商税", "虚标", "参数党"]):
        return "marketing_myth_check"
    if any(hint in current for hint in ["拆解", "跑分", "散热", "工程", "架构", "传感器", "AEB", "刹车", "影像测试"]):
        return "engineering_deep_dive"
    if any(hint in current for hint in ["适合谁", "怎么选", "买前", "女生", "学生", "通勤", "运动", "家庭", "场景"]):
        return "scenario_simulation"
    return "quick_verdict"


def get_formula_policy(formula: str) -> Dict[str, Any]:
    return dict(FORMULAS.get(formula, FORMULAS["search_buying_guide"]))


def get_subformula_policy(subformula: str) -> Dict[str, Any]:
    return dict(SINGLE_PRODUCT_SUBFORMULAS.get(subformula, {}))


def build_formula_prompt_hint(topic: str, platform: str = "") -> str:
    formula = infer_content_formula(topic, platform)
    policy = get_formula_policy(formula)
    must_have = "、".join(policy.get("must_have", []))
    base = f"内容母版={policy.get('label', '')}; 目标={policy.get('goal', '')}; 必须包含={must_have}。"
    if formula in {"single_product_review", "launch_roundup"}:
        subformula = infer_content_subformula(topic, platform)
        subpolicy = get_subformula_policy(subformula)
        if subpolicy:
            submust = "、".join(subpolicy.get("must_have", []))
            base += (
                f" 单品子模板={subpolicy.get('label', '')}; 子模板目标={subpolicy.get('goal', '')}; "
                f"子模板必须包含={submust}。开篇要求={subpolicy.get('opening', '')}"
            )
        base += (
            " 严禁伪装成自己亲手实测，必须明确使用公开发布信息、媒体上手、公开评测、拆解资料、"
            "首批用户反馈等证据口径。结论必须区分“已确认”“高概率成立”“仍待验证”三层。"
        )
    return base
