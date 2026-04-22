#!/usr/bin/env bash
# install_cron.sh — 幂等安装每日 1:00 自更新 cron 行
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="${SKILL_UPDATE_LOG_DIR:-$HOME/.cache/quanlaidian-quote-skills}"
LOG_PATH="$LOG_DIR/update.log"
CRON_LINE="0 1 * * * cd $REPO_ROOT && python3 scripts/check_openclaw_update.py --apply >> $LOG_PATH 2>&1"

mkdir -p "$LOG_DIR"

EXISTING="$(crontab -l 2>/dev/null || true)"
FILTERED="$(printf '%s\n' "$EXISTING" | grep -v 'check_openclaw_update.py' || true)"

{
  [ -n "$FILTERED" ] && printf '%s\n' "$FILTERED"
  printf '%s\n' "$CRON_LINE"
} | crontab -

echo "[install_cron] installed:"
echo "  $CRON_LINE"
echo "[install_cron] log: $LOG_PATH"
echo "[install_cron] disable: crontab -e   # 删掉上面那一行"
