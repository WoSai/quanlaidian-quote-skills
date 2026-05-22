"""rules.py 单测：直接构造 payload 验三条规则与 shape 校验。"""

import unittest

from tests.rules import (
    auto_correct,
    classify_segment,
    is_payload_clean,
    validate_payload_shape,
)


def base(**overrides):
    form = {
        "客户品牌名称": "测试品牌",
        "餐饮类型": "正餐",
        "门店数量": 10,
        "门店套餐": "正餐连锁营销旗舰版",
        "门店增值模块": [],
        "总部模块": [],
    }
    form.update(overrides)
    return form


class AutoCorrectFlagshipExclusion(unittest.TestCase):
    def test_flagship_with_distribution_promotes_to_full_capability(self):
        form = base(门店套餐="正餐连锁营销旗舰版", 总部模块=["配送中心"])
        corrected, triggered = auto_correct(form)
        self.assertEqual(corrected["门店套餐"], "正餐连锁营销全能版")
        self.assertIn("供应链基础-门店点位", corrected["门店增值模块"])
        self.assertEqual(len(triggered), 2)

    def test_supply_chain_edition_with_distribution_promotes_to_full_capability(self):
        form = base(
            餐饮类型="轻餐",
            门店套餐="轻餐连锁供应链版",
            总部模块=["配送中心", "生产加工"],
        )
        corrected, triggered = auto_correct(form)
        self.assertEqual(corrected["门店套餐"], "轻餐连锁营销全能版")
        self.assertIn("供应链基础-门店点位", corrected["门店增值模块"])

    def test_flagship_without_hq_supply_chain_is_untouched(self):
        form = base(门店套餐="正餐连锁营销旗舰版", 总部模块=[])
        corrected, triggered = auto_correct(form)
        self.assertEqual(corrected, form)
        self.assertEqual(triggered, [])


class AutoCorrectStorePointInjection(unittest.TestCase):
    def test_distribution_requires_store_point(self):
        form = base(门店套餐="正餐连锁营销全能版", 总部模块=["配送中心"])
        corrected, triggered = auto_correct(form)
        self.assertEqual(corrected["门店增值模块"], ["供应链基础-门店点位"])
        self.assertEqual(triggered, ["为承接总部配送/生产加工自动追加供应链基础-门店点位"])

    def test_production_requires_store_point(self):
        form = base(门店套餐="正餐连锁营销全能版", 总部模块=["生产加工"])
        corrected, _ = auto_correct(form)
        self.assertIn("供应链基础-门店点位", corrected["门店增值模块"])

    def test_existing_store_point_is_not_duplicated(self):
        form = base(
            门店套餐="正餐连锁营销全能版",
            门店增值模块=["供应链基础-门店点位", "厨房KDS"],
            总部模块=["配送中心"],
        )
        corrected, triggered = auto_correct(form)
        self.assertEqual(
            corrected["门店增值模块"],
            ["供应链基础-门店点位", "厨房KDS"],
        )
        self.assertEqual(triggered, [])


class AutoCorrectNoneSentinels(unittest.TestCase):
    def test_none_hq_sentinel_clears_other_hq_modules(self):
        form = base(总部模块=["无总部模块", "配送中心"])
        corrected, triggered = auto_correct(form)
        self.assertEqual(corrected["总部模块"], [])
        self.assertIn("按『无总部模块』处理，其他勾选已忽略", triggered)

    def test_none_value_add_sentinel_clears_other_modules(self):
        form = base(门店增值模块=["无门店增值模块", "厨房KDS"])
        corrected, triggered = auto_correct(form)
        self.assertEqual(corrected["门店增值模块"], [])
        self.assertIn("按『无门店增值模块』处理，其他勾选已忽略", triggered)


class IsPayloadClean(unittest.TestCase):
    def test_clean_payload(self):
        self.assertTrue(is_payload_clean(base(门店套餐="正餐连锁营销旗舰版")))

    def test_violating_payload_is_not_clean(self):
        self.assertFalse(
            is_payload_clean(base(门店套餐="正餐连锁营销旗舰版", 总部模块=["配送中心"]))
        )


class ValidatePayloadShape(unittest.TestCase):
    def test_clean_payload_has_no_errors(self):
        self.assertEqual(validate_payload_shape(base()), [])

    def test_missing_required_keys(self):
        errors = validate_payload_shape({"客户品牌名称": "测试品牌"})
        self.assertTrue(any("缺字段" in e for e in errors))

    def test_invalid_meal_type(self):
        errors = validate_payload_shape(base(餐饮类型="火锅"))
        self.assertTrue(any("餐饮类型" in e for e in errors))

    def test_invalid_package_name(self):
        errors = validate_payload_shape(base(门店套餐="正餐连锁全能版"))
        self.assertTrue(any("门店套餐" in e for e in errors))

    def test_store_count_below_one(self):
        errors = validate_payload_shape(base(门店数量=0))
        self.assertTrue(any("门店数量" in e for e in errors))

    def test_store_count_above_three_hundred(self):
        errors = validate_payload_shape(base(门店数量=301))
        self.assertTrue(any("超过 300" in e for e in errors))


class ClassifySegment(unittest.TestCase):
    def test_small_segment(self):
        for n in (1, 5, 30):
            self.assertEqual(classify_segment(n), "small")

    def test_large_segment(self):
        for n in (31, 100, 200, 300):
            self.assertEqual(classify_segment(n), "large")

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            classify_segment(0)
        with self.assertRaises(ValueError):
            classify_segment(301)


if __name__ == "__main__":
    unittest.main()
