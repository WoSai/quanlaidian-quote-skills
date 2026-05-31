"""发布同步契约：VERSION 必须与 .release-please-manifest.json 一致。

合并 release PR 后需手工把版本号抄进 VERSION(节点自更新脚本直读 VERSION)。
这条原先只在 CLAUDE.md 口头约束、漏抄不报错——本测试把它变成离线套件里的 CI 红线。
"""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class ReleaseSyncTest(unittest.TestCase):
    def test_version_matches_manifest(self):
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
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
