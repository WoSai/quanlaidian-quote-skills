"""quote.py render_profit() 单测：利润评估区块汇总/逐项金额格式正确。"""

import importlib.util
import json
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_QUOTE_PATH = _ROOT / "scripts" / "quote.py"
_spec = importlib.util.spec_from_file_location("quote", _QUOTE_PATH)
quote = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quote)

_FIXTURE = _ROOT / "tests" / "fixtures" / "quote_config_sample.json"


class RenderProfit(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        self.out = quote.render_profit(self.data)

    def test_heading_marks_internal(self):
        self.assertIn("报价利润评估（内部）", self.out)

    def test_summary_amounts_with_thousands_separator(self):
        self.assertIn("报价总额：¥19,655", self.out)
        self.assertIn("成本总额：¥3,780", self.out)
        self.assertIn("利润总额：¥15,875", self.out)
        self.assertIn("利润率：81%", self.out)

    def test_item_row_present(self):
        self.assertIn("| 正餐连锁营销旗舰版 | 5 ", self.out)
        self.assertIn("¥19,655", self.out)

    def test_missing_financials_returns_empty(self):
        self.assertEqual(quote.render_profit({}), "")
        self.assertEqual(quote.render_profit(None), "")


if __name__ == "__main__":
    unittest.main()
