"""quote.py render() 单测：确保三条签名链接原样、独占一行、无截断输出。"""

import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_QUOTE_PATH = Path(__file__).resolve().parent.parent / "scripts" / "quote.py"
_spec = importlib.util.spec_from_file_location("quote", _QUOTE_PATH)
quote = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quote)

PDF_URL = "https://private-resource.shouqianba.com/quanlaidian-quote/AbC/x-pdf.pdf?OSSAccessKeyId=LTAI5t9EporDudCHzZqJV5zz&Expires=1780153828&Signature=RsJMdu5jfAn1GOlh7EhhBtniPTg%3D"
XLSX_URL = "https://private-resource.shouqianba.com/quanlaidian-quote/AbC/x-xlsx.xlsx?OSSAccessKeyId=LTAI5t9EporDudCHzZqJV5zz&Expires=1780153828&Signature=x2rQsV1HZAFas7dbWU0Zx0y0s4%3D"
JSON_URL = "https://private-resource.shouqianba.com/quanlaidian-quote/AbC/x-json.json?OSSAccessKeyId=LTAI5t9EporDudCHzZqJV5zz&Expires=1780153828&Signature=%2B9K2DVkdhV3sqYmMHb6zIkykns8%3D"


def _result():
    return {
        "preview": {
            "brand": "一点点奶茶",
            "meal_type": "轻餐",
            "stores": 65,
            "package": "轻餐连锁营销全能版",
            "totals": {"final": 75900},
        },
        "files": {
            "pdf": {"url": PDF_URL},
            "xlsx": {"url": XLSX_URL},
            "json": {"url": JSON_URL},
        },
        "pricing_version": "large-segment-v1",
    }


class RenderLinks(unittest.TestCase):
    def setUp(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            quote.render(_result())
        self.out = buf.getvalue()
        self.lines = self.out.splitlines()

    def test_each_url_intact_and_on_its_own_line(self):
        for url in (PDF_URL, XLSX_URL, JSON_URL):
            self.assertIn(url, self.lines, f"完整 URL 必须原样独占一行: {url}")

    def test_no_truncation_marker(self):
        self.assertNotIn("…", self.out)  # …
        self.assertNotIn("...", self.out)

    def test_verbatim_warning_present(self):
        self.assertIn("SignatureDoesNotMatch", self.out)


if __name__ == "__main__":
    unittest.main()
