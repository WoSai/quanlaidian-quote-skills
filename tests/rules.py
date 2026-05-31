"""SKILL.md 中三条 payload 自动修正规则的可执行实现。

来源：SKILL.md `卡片答案 → API 字段修正映射` 与
`套餐默认决策树`。这里只把"已经在 agent 决策树里
写明的修正动作"复刻成纯函数，供测试断言使用——客户端 quote.py
不调用它，规则的权威执行点仍是 agent + 后端 API。

规则编号与触发文案对齐 SKILL.md 原文，方便测试失败时反查。
"""

from __future__ import annotations
import copy

FLAGSHIP_OR_SUPPLY_PACKAGES = {
    "轻餐连锁营销旗舰版",
    "轻餐连锁供应链版",
    "正餐连锁营销旗舰版",
    "正餐连锁供应链版",
}

FULL_CAPABILITY_PACKAGE_BY_MEAL_TYPE = {
    "轻餐": "轻餐连锁营销全能版",
    "正餐": "正餐连锁营销全能版",
}

HQ_SUPPLY_CHAIN_MODULES = {"配送中心", "生产加工"}
STORE_POINT_MODULE = "供应链基础-门店点位"

NONE_SENTINELS_HQ = {"无", "无总部模块"}
NONE_SENTINELS_VALUE_ADD = {"无", "无门店增值模块"}


def auto_correct(form: dict) -> tuple[dict, list[str]]:
    """对 form 执行 SKILL.md 三条修正规则。

    返回 (修正后 payload, 触发的规则文案列表)。规则文案与 SKILL.md
    `卡片答案 → API 字段修正映射` 摘要标注口径一致，便于在报价单摘要里展示。
    """
    corrected = copy.deepcopy(form)
    triggered: list[str] = []

    hq = list(corrected.get("总部模块", []))
    if any(s in hq for s in NONE_SENTINELS_HQ) and len(hq) > 1:
        corrected["总部模块"] = []
        hq = []
        triggered.append("按『无总部模块』处理，其他勾选已忽略")

    value_adds = list(corrected.get("门店增值模块", []))
    if any(s in value_adds for s in NONE_SENTINELS_VALUE_ADD) and len(value_adds) > 1:
        corrected["门店增值模块"] = []
        value_adds = []
        triggered.append("按『无门店增值模块』处理，其他勾选已忽略")

    has_supply_chain_hq = any(m in HQ_SUPPLY_CHAIN_MODULES for m in hq)
    package = corrected.get("门店套餐", "")
    meal_type = corrected.get("餐饮类型", "")

    if has_supply_chain_hq and package in FLAGSHIP_OR_SUPPLY_PACKAGES:
        replacement = FULL_CAPABILITY_PACKAGE_BY_MEAL_TYPE.get(meal_type)
        if replacement is None:
            raise ValueError(
                f"无法为餐饮类型 {meal_type!r} 解析全能版套餐；"
                "payload 须含『轻餐』或『正餐』"
            )
        corrected["门店套餐"] = replacement
        triggered.append("为承接总部配送/生产加工自动修正套餐为全能版")

    if has_supply_chain_hq and STORE_POINT_MODULE not in corrected.get("门店增值模块", []):
        corrected["门店增值模块"] = list(corrected.get("门店增值模块", [])) + [STORE_POINT_MODULE]
        triggered.append("为承接总部配送/生产加工自动追加供应链基础-门店点位")

    return corrected, triggered


def is_payload_clean(form: dict) -> bool:
    """若 payload 已经满足全部规则、auto_correct 不会改动则返回 True。"""
    _, triggered = auto_correct(form)
    return not triggered


REQUIRED_KEYS = {"客户品牌名称", "餐饮类型", "门店数量", "门店套餐", "门店增值模块", "总部模块"}
VALID_MEAL_TYPES = {"轻餐", "正餐"}
VALID_PACKAGES = {
    "轻餐连锁标准版", "轻餐连锁营销基础版", "轻餐连锁营销全能版",
    "轻餐连锁营销旗舰版", "轻餐连锁供应链版",
    "正餐连锁标准版", "正餐连锁营销基础版", "正餐连锁营销全能版",
    "正餐连锁营销旗舰版", "正餐连锁供应链版",
}


def validate_payload_shape(form: dict) -> list[str]:
    """校验 payload 字段齐全、类型正确、枚举值合法。返回错误列表。"""
    errors: list[str] = []

    missing = REQUIRED_KEYS - form.keys()
    if missing:
        errors.append(f"缺字段: {sorted(missing)}")
        return errors

    if form["餐饮类型"] not in VALID_MEAL_TYPES:
        errors.append(f"餐饮类型不合法: {form['餐饮类型']!r}")

    if not isinstance(form["门店数量"], int) or form["门店数量"] < 1:
        errors.append(f"门店数量必须为 >=1 的整数，实际: {form['门店数量']!r}")

    if form["门店数量"] > 300:
        errors.append(f"门店数量超过 300 上限: {form['门店数量']}")

    if form["门店套餐"] not in VALID_PACKAGES:
        errors.append(f"门店套餐不合法: {form['门店套餐']!r}")

    for key in ("门店增值模块", "总部模块"):
        if not isinstance(form[key], list):
            errors.append(f"{key} 必须为列表，实际: {type(form[key]).__name__}")

    return errors


def classify_segment(store_count: int) -> str:
    """1–30 走 small-segment-v2.3；31–300 走 large-segment-v1。"""
    if store_count < 1:
        raise ValueError(f"门店数 {store_count} 非法")
    if store_count <= 30:
        return "small"
    if store_count <= 300:
        return "large"
    raise ValueError(f"门店数 {store_count} 超出 300 上限")
