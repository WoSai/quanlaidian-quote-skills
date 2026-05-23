"""场景回归测试：跑 `tests/scenarios/*` 下所有 fixture。

离线模式（默认）：
  - 单文件 fixture：auto_correct(payload) 应零规则触发，payload 字段合法。
  - 翻车目录 fixture：auto_correct(initial.payload) 应严格等于 corrected.payload。

Live 模式（`QUOTE_TEST_LIVE=1` 触发，需 `QUOTE_API_URL` + `QUOTE_API_TOKEN`）：
  - 用 corrected/单文件 payload 调 API，要求 200 + final_price 命中（除非 expected.price_baseline_only）。
  - 翻车 initial.json 也送 API 一遍，要求 4xx（证明规则在后端确实兜底）。
"""

from __future__ import annotations
import json
import os
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from tests.rules import auto_correct, classify_segment, validate_payload_shape

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
LIVE = os.environ.get("QUOTE_TEST_LIVE") == "1"
API_URL = os.environ.get("QUOTE_API_URL")
API_TOKEN = os.environ.get("QUOTE_API_TOKEN")


def _call_api(payload: dict) -> tuple[int, dict | str]:
    """调用 beta API。返回 (HTTP 状态码, JSON 或错误文本)。"""
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def _assert_segment_consistent(test_case, payload, expected):
    """门店数推导出的 segment 必须与 expected.segment 对齐。"""
    derived = classify_segment(payload["门店数量"])
    test_case.assertEqual(
        derived,
        expected["segment"],
        f"门店数 {payload['门店数量']} 推得 segment={derived}，与 fixture 标注的 {expected['segment']} 不一致",
    )


def _live_assert_price(test_case, payload, expected):
    status, body = _call_api(payload)
    test_case.assertEqual(
        status, 200,
        f"corrected payload 应该被 API 接受，实际 {status}：{body}",
    )
    actual_price = body["preview"]["totals"]["final"]
    if expected.get("price_baseline_only"):
        return
    test_case.assertEqual(
        actual_price,
        expected["final_price"],
        f"final_price 与 fixture 期望不一致：fixture={expected['final_price']}, API={actual_price}",
    )


def _live_assert_rejected(test_case, payload):
    status, body = _call_api(payload)
    test_case.assertGreaterEqual(
        status, 400,
        f"翻车 initial payload 应被 API 拒绝，实际 {status}：{body}",
    )
    test_case.assertLess(status, 500, f"期望 4xx，实际 5xx：{body}")


def _make_single_file_test(path: Path):
    def test(self):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        payload = fixture["payload"]
        expected = fixture["expected"]

        shape_errors = validate_payload_shape(payload)
        self.assertEqual(shape_errors, [], f"payload shape 校验失败：{shape_errors}")

        corrected, triggered = auto_correct(payload)
        self.assertEqual(
            triggered, [],
            f"一次性通过场景不应触发任何规则修正，实际触发：{triggered}",
        )
        self.assertEqual(corrected, payload, "payload 修正前后应完全一致")

        _assert_segment_consistent(self, payload, expected)

        if LIVE:
            self.assertIsNotNone(API_URL, "QUOTE_TEST_LIVE=1 时必须设 QUOTE_API_URL")
            self.assertIsNotNone(API_TOKEN, "QUOTE_TEST_LIVE=1 时必须设 QUOTE_API_TOKEN")
            _live_assert_price(self, payload, expected)

    return test


def _make_paired_dir_test(dir_path: Path):
    def test(self):
        initial = json.loads((dir_path / "initial.json").read_text(encoding="utf-8"))
        corrected_fixture = json.loads((dir_path / "corrected.json").read_text(encoding="utf-8"))
        initial_payload = initial["payload"]
        corrected_payload = corrected_fixture["payload"]
        expected = corrected_fixture["expected"]

        shape_errors = validate_payload_shape(corrected_payload)
        self.assertEqual(shape_errors, [], f"corrected payload shape 校验失败：{shape_errors}")

        auto_corrected, triggered = auto_correct(initial_payload)
        self.assertNotEqual(
            triggered, [],
            "翻车场景应至少触发一条规则修正",
        )
        self.assertEqual(
            auto_corrected,
            corrected_payload,
            "auto_correct(initial.payload) 应严格等于 corrected.payload",
        )

        re_corrected, re_triggered = auto_correct(corrected_payload)
        self.assertEqual(re_triggered, [], "corrected payload 不应再触发任何规则")
        self.assertEqual(re_corrected, corrected_payload, "auto_correct 应满足幂等性")

        _assert_segment_consistent(self, corrected_payload, expected)

        if LIVE:
            self.assertIsNotNone(API_URL, "QUOTE_TEST_LIVE=1 时必须设 QUOTE_API_URL")
            self.assertIsNotNone(API_TOKEN, "QUOTE_TEST_LIVE=1 时必须设 QUOTE_API_TOKEN")
            _live_assert_price(self, corrected_payload, expected)
            _live_assert_rejected(self, initial_payload)

    return test


class ScenarioTests(unittest.TestCase):
    """场景测试容器；具体测试方法在模块加载时动态注入。"""


def _attach_tests():
    for entry in sorted(SCENARIOS_DIR.iterdir()):
        if entry.is_file() and entry.suffix == ".json":
            setattr(ScenarioTests, f"test_{entry.stem}", _make_single_file_test(entry))
        elif entry.is_dir():
            setattr(ScenarioTests, f"test_{entry.name}", _make_paired_dir_test(entry))


_attach_tests()


if __name__ == "__main__":
    unittest.main()
