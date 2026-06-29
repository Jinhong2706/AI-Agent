#!/bin/bash
# 恢复最新备份脚本
#
# 用法：./restore.sh
#
# 注意：恢复前会自动将当前 .openclaw 目录备份到
#       .openclaw.pre-restore-YYYYMMDD-HHMMSS/，无需手动备份

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="$(dirname "$SCRIPT_DIR")"

# 加载配置
if [ -f "$INSTALL_ROOT/config.env" ]; then
    source "$INSTALL_ROOT/config.env"
fi

LOG_FILE="${BACKUP_ROOT:-"$INSTALL_ROOT"}/backup.log"

python3 "$SCRIPT_DIR/openclaw_backup.py" restore 2>&1 | tee -a "$LOG_FILE"
