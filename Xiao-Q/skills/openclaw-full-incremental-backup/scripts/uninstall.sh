#!/bin/bash
# OpenClaw 全自动备份技能 — 卸载脚本
set -euo pipefail

echo "=== OpenClaw 全自动备份技能 - 卸载 ==="
echo ""

if [ "$(id -u)" -ne 0 ]; then
  echo "❌ 请使用 root 权限运行: sudo $0"
  exit 1
fi

echo "⚠️  此操作只删除技能本身，不删除备份数据"
echo "    备份数据保留在: /mnt/data3/openclaw-backup/"
echo ""

# 删除命令链接
rm -f /usr/local/bin/openclaw-backup
rm -f /usr/local/bin/openclaw-restore
rm -f /usr/local/bin/openclaw-backup-verify
echo "✅ 已删除命令链接"

# 删除定时任务
TEMP_CRON=$(mktemp)
crontab -l 2>/dev/null | grep -v "openclaw-backup" > "$TEMP_CRON" || true
crontab "$TEMP_CRON"
rm -f "$TEMP_CRON"
echo "✅ 已删除定时任务"

echo ""
echo "✅ 卸载完成"
echo "📁 备份数据仍保留在: /mnt/data3/openclaw-backup/"
echo "   如需删除，执行: sudo rm -rf /mnt/data3/openclaw-backup/"
