#!/usr/bin/env python3
"""update_notice.py — skill 升级后首次激活时生成升级提示横幅

机制：节点本地维护 `~/.cache/quanlaidian-quote-skills/last_notified_version`；
每次 skill 激活时（SKILL.md 工作流 step 1）调用本脚本：
- 若 VERSION 与 marker 一致，静默退出
- 若不一致，从 CHANGELOG.md 抽取当前版本条目，打印一段 Markdown 横幅供 skill
  原样插入本次回复首段；然后把 marker 更新为当前 VERSION，实现"每个版本只提
  示一次"。

零额外依赖，仅 Python 3 标准库。
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

CACHE_DIR = Path(os.environ.get(
    "SKILL_UPDATE_LOG_DIR",
    str(Path.home() / ".cache" / "quanlaidian-quote-skills"),
))
MARKER = CACHE_DIR / "last_notified_version"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def read_version(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def read_marker() -> str:
    try:
        return MARKER.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def write_marker(version: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(version + "\n", encoding="utf-8")


def extract_changelog_section(root: Path, version: str) -> str:
    """提取 CHANGELOG.md 中 `## <version>` 到下一个 `## ` 之间的正文"""
    try:
        text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    pattern = rf"^##\s+{re.escape(version)}\b.*?\n(.*?)(?=^##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL | re.MULTILINE)
    return m.group(1).strip() if m else ""


def main() -> int:
    root = repo_root()

    try:
        current = read_version(root)
    except OSError:
        return 0  # 读不到 VERSION 静默

    last = read_marker()

    if not last:
        # 首次运行或缓存被清，视为已告知，不打扰用户
        write_marker(current)
        return 0

    if current == last:
        return 0  # 无变化

    section = extract_changelog_section(root, current)

    print(f"📢 **全来店报价 skill 已升级至 v{current}**")
    if section:
        print()
        print(section)
    print()
    print("— 本次升级提示仅显示一次 —")

    write_marker(current)
    return 0


if __name__ == "__main__":
    sys.exit(main())
