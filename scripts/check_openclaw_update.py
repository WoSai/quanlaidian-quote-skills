#!/usr/bin/env python3
"""check_openclaw_update.py — OpenClaw 节点日更自检脚本

对比本地 VERSION 与 GitHub main 分支的 VERSION，较旧则执行 git pull --ff-only。
零额外依赖，仅用 Python 3 标准库。

用法：
    python3 scripts/check_openclaw_update.py            # 只检查
    python3 scripts/check_openclaw_update.py --apply    # 有新版本则拉取
"""
import argparse, os, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

REPO      = os.environ.get("SKILL_REPO", "jasonshao/quanlaidian-quote-skills")
REMOTE_URL = f"https://raw.githubusercontent.com/{REPO}/main/VERSION"


def repo_root() -> Path:
    env_dir = os.environ.get("SKILL_LOCAL_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    script_dir = Path(__file__).resolve().parent
    try:
        out = subprocess.check_output(
            ["git", "-C", str(script_dir), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        )
        return Path(out.decode().strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return script_dir.parent


def read_local(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def fetch_remote() -> str:
    with urllib.request.urlopen(REMOTE_URL, timeout=15) as resp:
        return resp.read().decode("utf-8").strip()


def parse(v: str):
    return tuple(int(x) for x in v.split("."))


def git_pull(root: Path) -> int:
    print(f"[update] pulling latest from origin/main in {root}", file=sys.stderr)
    r = subprocess.run(
        ["git", "-C", str(root), "fetch", "origin", "main", "--quiet"],
    )
    if r.returncode != 0:
        print("[update] git fetch failed", file=sys.stderr)
        return r.returncode
    r = subprocess.run(
        ["git", "-C", str(root), "pull", "--ff-only", "origin", "main"],
    )
    if r.returncode != 0:
        print("[update] git pull --ff-only failed; resolve manually", file=sys.stderr)
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="有新版本时执行 git pull --ff-only")
    args = ap.parse_args()

    root = repo_root()
    local = read_local(root)

    try:
        remote = fetch_remote()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"[update] network error: {e}", file=sys.stderr)
        return 0

    try:
        needs_update = parse(remote) > parse(local)
    except ValueError:
        print(f"[update] unparsable version local={local!r} remote={remote!r}",
              file=sys.stderr)
        return 0

    print(f"local={local} remote={remote} "
          f"update={'yes' if needs_update else 'no'}")

    if needs_update and args.apply:
        return git_pull(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
