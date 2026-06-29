#!/bin/bash
#
# OpenClaw 全自动备份系统 v2.0 安装脚本
# ================================
#
# 用法:
#   ./install.sh [BACKUP_ROOT]
#
#   BACKUP_ROOT: 备份存储根目录（可选，不填则交互式输入）
#
# 示例:
#   ./install.sh /mnt/data3/openclaw-backup
#   ./install.sh /opt/openclaw-backups
#
# 安装步骤:
#   1. 收集参数（目录路径、OpenClaw 家目录）
#   2. 复制文件到目标目录
#   3. 生成 config.env 配置文件
#   4. 设置脚本可执行权限
#   5. 注册 cron 定时任务
#   6. 首次执行全量备份
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"  # install.sh 在 skill/ 目录下，skill root 是 parent

echo "=============================================="
echo "  OpenClaw 全自动备份系统 v2.0 安装向导"
echo "=============================================="
echo ""

# ============== 1. 确定备份根目录 ==============
if [ -n "$1" ]; then
    BACKUP_ROOT="$1"
elif [ -f "$SCRIPT_DIR/config.env" ]; then
    # 如果已有 config.env，读取默认值
    BACKUP_ROOT=$(grep "^BACKUP_ROOT=" "$SCRIPT_DIR/config.env" 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
fi

if [ -z "$BACKUP_ROOT" ]; then
    read -p "请输入备份存储目录路径（如 /mnt/data3/openclaw-backup）: " BACKUP_ROOT
fi

BACKUP_ROOT="$(eval echo "$BACKUP_ROOT")"  # 解析 ~ 等路径

if [ "$BACKUP_ROOT" = "" ]; then
    echo "❌ 错误：备份目录不能为空"
    exit 1
fi

# ============== 2. 确定 OpenClaw 家目录 ==============
if [ -f "$SCRIPT_DIR/config.env" ]; then
    OPENCLAW_HOME=$(grep "^OPENCLAW_HOME=" "$SCRIPT_DIR/config.env" 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
fi

if [ -z "$OPENCLAW_HOME" ]; then
    read -p "请输入 OpenClaw 家目录路径（默认: /root/.openclaw）: " INPUT_HOME
    OPENCLAW_HOME="${INPUT_HOME:-/root/.openclaw}"
fi

OPENCLAW_HOME="$(eval echo "$OPENCLAW_HOME")"

if [ ! -d "$OPENCLAW_HOME" ]; then
    echo "⚠️  警告：$OPENCLAW_HOME 目录不存在，继续安装（可在部署时指定正确路径）"
fi

# ============== 3. 复制文件到目标目录 ==============
echo ""
echo "📦 开始安装..."
echo "   备份目录: $BACKUP_ROOT"
echo "   OpenClaw: $OPENCLAW_HOME"

# 如果目标目录已存在，询问是否覆盖 config
if [ -d "$BACKUP_ROOT" ]; then
    if [ -f "$BACKUP_ROOT/config.env" ]; then
        echo "⚠️  目标目录已有配置文件，是否更新？（将保留已有备份文件）"
        read -p "   更新 config.env？[y/N]: " UPDATE_CONF
        if [ "$UPDATE_CONF" != "y" ] && [ "$UPDATE_CONF" != "Y" ]; then
            echo "✅ 安装已取消"
            exit 0
        fi
    fi
else
    mkdir -p "$BACKUP_ROOT"
fi

# 复制脚本文件
mkdir -p "$BACKUP_ROOT/scripts"
cp "$SCRIPT_DIR/scripts/openclaw_backup.py" "$BACKUP_ROOT/scripts/"
cp "$SCRIPT_DIR/scripts/backup.sh" "$BACKUP_ROOT/scripts/"
cp "$SCRIPT_DIR/scripts/restore.sh" "$BACKUP_ROOT/scripts/"

# 创建必要目录
mkdir -p "$BACKUP_ROOT/full"
mkdir -p "$BACKUP_ROOT/incremental"
mkdir -p "$BACKUP_ROOT/snapshots"

echo "   文件已复制到: $BACKUP_ROOT/"

# ============== 4. 生成 config.env ==============
cat > "$BACKUP_ROOT/config.env" << EOF
# OpenClaw 备份系统配置文件
# 此文件由 install.sh 自动生成，修改后需重启备份任务
# =========================================

# OpenClaw 家目录（被备份的目录）
OPENCLAW_HOME="$OPENCLAW_HOME"

# 备份存储根目录
BACKUP_ROOT="$BACKUP_ROOT"
EOF

echo "   config.env 已生成"

# ============== 5. 设置可执行权限 ==============
chmod +x "$BACKUP_ROOT/scripts/openclaw_backup.py"
chmod +x "$BACKUP_ROOT/scripts/backup.sh"
chmod +x "$BACKUP_ROOT/scripts/restore.sh"

echo "   脚本权限已设置"

# ============== 6. 注册 cron 任务 ==============
echo ""
echo "⏰ 注册定时任务..."

CRON_BACKUP_FULL="59 23 * * 6 $BACKUP_ROOT/scripts/backup.sh >> $BACKUP_ROOT/backup.log 2>&1"
CRON_BACKUP_INCR="59 23 * * 1-5 $BACKUP_ROOT/scripts/backup.sh >> $BACKUP_ROOT/backup.log 2>&1"

# 去掉旧备份任务，保留其他任务
crontab -l 2>/dev/null | grep -v "openclaw-backup\|openclaw_backup" > /tmp/crontab.tmp || true

# 添加新备份任务
cat >> /tmp/crontab.tmp << EOF

# OpenClaw 全自动备份系统 v2.0
# 周六 23:59 全量备份
$CRON_BACKUP_FULL
# 周一至周五 23:59 增量备份
$CRON_BACKUP_INCR
EOF

crontab /tmp/crontab.tmp
rm -f /tmp/crontab.tmp

echo "   cron 任务已注册:"
echo "   - 周六 23:59 全量备份"
echo "   - 周一至周五 23:59 增量备份"

# ============== 7. 首次备份 ==============
echo ""
echo "🚀 首次全量备份（可能需要几分钟）..."
echo "   首次运行将自动判断为全量备份，后续按策略增量..."

cd "$BACKUP_ROOT/scripts"
if python3 openclaw_backup.py backup --force 2>&1 | tee -a "$BACKUP_ROOT/backup.log"; then
    echo ""
    echo "=============================================="
    echo "  ✅ 安装完成！"
    echo "=============================================="
    echo ""
    echo "📋 备份目录结构:"
    echo "   $BACKUP_ROOT/"
    echo "   ├── config.env          # 配置文件（可编辑）"
    echo "   ├── full/               # 全量备份"
    echo "   ├── incremental/        # 增量备份"
    echo "   ├── snapshots/          # 快照文件"
    echo "   ├── backup.log          # 备份日志"
    echo "   └── scripts/"
    echo "       ├── openclaw_backup.py  # 主程序"
    echo "       ├── backup.sh           # 备份入口"
    echo "       └── restore.sh          # 恢复入口"
    echo ""
    echo "📖 常用命令:"
    echo "   $BACKUP_ROOT/scripts/backup.sh          # 手动执行备份"
    echo "   $BACKUP_ROOT/scripts/restore.sh         # 恢复最新备份"
    echo "   python3 $BACKUP_ROOT/scripts/openclaw_backup.py list   # 查看备份"
    echo ""
    echo "🗑️  卸载方法:"
    echo "   crontab -l | grep -v openclaw-backup > /tmp/cron.tmp && crontab /tmp/cron.tmp"
    echo "   rm -rf $BACKUP_ROOT"
    echo ""
else
    echo ""
    echo "⚠️  首次备份失败，请检查日志:"
    echo "   $BACKUP_ROOT/backup.log"
    echo "   常见原因: OpenClaw 目录路径不正确"
    echo ""
    echo "   修复方法: 编辑 $BACKUP_ROOT/config.env"
    echo "   然后重新运行: $BACKUP_ROOT/scripts/backup.sh --force"
fi
