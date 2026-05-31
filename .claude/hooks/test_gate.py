#!/usr/bin/env python3
"""PostToolUse 钩子：编辑业务规则文件后自动跑离线测试套件。

CLAUDE.md 要求"改业务规则要同步 tests/、改 SKILL.md 决策树跑回归",但这条原本
只靠自觉。本钩子把它变成强制——动了 SKILL.md / tests/ 就立刻跑一遍,失败时以退出码 2
把测试输出回灌给 agent,堵住"没跑测试就交卷"。

非业务文件、改到本仓库以外、或内部异常一律放行(退出 0):宁可漏拦,不可误伤正常编辑。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def _is_business_file(rel: str) -> bool:
    if rel == "SKILL.md":
        return True
    if rel.startswith("tests/") and rel.endswith(".py"):
        return True
    if rel.startswith("tests/scenarios/"):
        return True
    return False


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0

    file_path = (event.get("tool_input") or {}).get("file_path")
    if not file_path:
        return 0

    root = _repo_root().resolve()
    try:
        rel = Path(file_path).resolve().relative_to(root).as_posix()
    except ValueError:
        return 0

    if not _is_business_file(rel):
        return 0

    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "tests"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return 0

    sys.stderr.write(
        f"[test-gate] 改了 {rel} 后离线测试未通过，先修测试再继续：\n"
        + (proc.stderr or proc.stdout)
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
