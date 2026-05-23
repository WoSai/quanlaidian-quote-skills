"""契约测试：OpenClaw 表单的「无…模块」哨兵项须声明为互斥首项。"""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FORM_FILES = {
    "schema": REPO_ROOT / "references" / "openclaw_form_schema.json",
    "config": REPO_ROOT / "references" / "openclaw_form_config.json",
}

EXPECTED_NONE_OPTION = {
    "门店增值模块": "无门店增值模块",
    "总部模块": "无总部模块",
}


def iter_fields(form: dict):
    if "fields" in form:
        yield from form["fields"]
    for section in form.get("sections", []):
        yield from section.get("fields", [])


def fields_by_key(form: dict) -> dict:
    return {f["key"]: f for f in iter_fields(form) if "key" in f}


class FormNoneOptionExclusive(unittest.TestCase):
    def test_none_option_declared_and_exclusive(self):
        for name, path in FORM_FILES.items():
            form = json.loads(path.read_text(encoding="utf-8"))
            by_key = fields_by_key(form)
            for field_key, expected_value in EXPECTED_NONE_OPTION.items():
                with self.subTest(file=name, field=field_key):
                    self.assertIn(field_key, by_key)
                    none_option = by_key[field_key].get("none_option")
                    self.assertIsInstance(none_option, dict)
                    self.assertEqual(none_option.get("value"), expected_value)
                    self.assertIs(none_option.get("exclusive"), True)


if __name__ == "__main__":
    unittest.main()
