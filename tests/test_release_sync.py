"""发布同步契约：VERSION 必须与 .release-please-manifest.json 一致。

VERSION 现由 release-please 的 extra-files 自动同步（行内 x-release-please-version
注解定位），本测试守住「manifest 与 VERSION 不漂移」这条 CI 红线。
"""

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class ReleaseSyncTest(unittest.TestCase):
    def test_version_matches_manifest(self):
        # VERSION 带 release-please 注解（`1.6.0 # x-release-please-version`），只取语义版本号。
        version = re.search(
            r"\d+\.\d+\.\d+",
            (REPO_ROOT / "VERSION").read_text(encoding="utf-8"),
        ).group(0)
        manifest = json.loads(
            (REPO_ROOT / ".release-please-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            version,
            manifest["."],
            f"VERSION={version!r} 与 .release-please-manifest.json['.']={manifest['.']!r} 不一致；"
            "合并 release PR 后请把版本号抄进 VERSION。",
        )


if __name__ == "__main__":
    unittest.main()
