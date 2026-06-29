#!/bin/bash
#
# OpenClaw 全自动备份系统 v2.0 卸载脚本
#
# 用法: ./uninstall.sh
#
# 此脚本会：
#   1. 从 crontab 中移除备份定时任务
#   2. 删除备份目录（可选）
#   3. 保留最新备份包（建议确认后再删除）
#

echo "=============================================="
echo "  OpenClaw 全自动备份系统 v2.0 卸载"
echo "=============================================="
echo ""

# ============== 1. 从 cron 移除任务 ==============
echo "🔧 移除 cron 定时任务..."
CRONTAB_BEFORE=$(crontab -l 2>/dev/null || echo "")
crontab -l 2>/dev/null | grep -v "openclaw-backup\|openclaw_backup" > /tmp/crontab_clean.tmp || true
crontab /tmp/crontab_clean.tmp 2>/dev/null
rm -f /tmp/crontab_clean.tmp
echo "   ✅ cron 任务已移除"

# ============== 2. 询问是否删除备份目录 ==============
echo ""
echo "⚠️  备份目录是否需要删除？"
echo "   如需保留备份包，请先手动复制到其他位置"
read -p "   删除备份目录及所有备份文件？[y/N]: " DEL_DIR

if [ "$DEL_DIR" = "y" ] || [ "$DEL_DIR" = "Y" ]; then
    echo ""
    echo "请手动执行删除（以防误删重要数据）:"
    echo "   1. 查看备份目录: ls /mnt/data3/openclaw-backup/"
    echo "   2. 确认后删除:   rm -rf /mnt/data3/openclaw-backup/"
    echo ""
    echo "   如需删除，请替换为你的实际备份目录路径"
else
    echo "   备份目录已保留"
fi

echo ""
echo "✅ 卸载完成"
echo ""
echo "📋 已移除内容:"
echo "   - cron 定时任务（每日23:59备份）"
echo ""
echo "📋 保留内容:"
echo "   - 备份目录及备份文件（如未手动删除）"
echo ""
