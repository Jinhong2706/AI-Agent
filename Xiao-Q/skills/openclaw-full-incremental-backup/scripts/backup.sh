#!/bin/bash
# 备份入口脚本
# 使用说明：此脚本由 cron 自动调用，或手动执行 ./backup.sh
#
# 用法：
#   ./backup.sh              # 执行备份（增量或全量，由脚本自动判断）
#   ./backup.sh --force      # 强制执行（跳过锁检查）
#   ./backup.sh restore      # 恢复最新备份
#   ./backup.sh verify       # 验证备份完整性
#   ./backup.sh list         # 查看备份列表
#   ./backup.sh clean         # 清理过期备份

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="$(dirname "$SCRIPT_DIR")"

# 加载配置
if [ -f "$INSTALL_ROOT/config.env" ]; then
    source "$INSTALL_ROOT/config.env"
fi

# 设置日志输出
LOG_FILE="${BACKUP_ROOT:-"$INSTALL_ROOT"}/backup.log"

python3 "$SCRIPT_DIR/openclaw_backup.py" "$@" 2>&1 | tee -a "$LOG_FILE"
