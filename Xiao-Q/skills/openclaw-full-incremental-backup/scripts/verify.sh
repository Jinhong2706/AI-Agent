#!/bin/bash
# OpenClaw 备份校验脚本
set -euo pipefail

CONFIG_FILE="$HOME/.config/openclaw-backup/.backup-config"
if [ -f "$CONFIG_FILE" ]; then
  source "$CONFIG_FILE"
else
  echo "❌ 未找到配置文件: $CONFIG_FILE" >&2
  exit 1
fi

: "${BACKUP_ROOT:?}" ; : "${BACKUP_NAME:?}"

FULL_DIR="${BACKUP_ROOT}/${BACKUP_NAME}/full"
INCR_DIR="${BACKUP_ROOT}/${BACKUP_NAME}/incremental"
LOG_FILE="${BACKUP_ROOT}/${BACKUP_NAME}/verify.log"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

log()  { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"; }
log_w(){ echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1" >> "$LOG_FILE"; }
log_e(){ echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"; echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1" >> "$LOG_FILE"; }

echo "" > "$LOG_FILE"
log "=== 校验开始 ==="

total=0; passed=0; failed=0; skipped=0

for dir in "$FULL_DIR" "$INCR_DIR"; do
  log "--- $(basename "$dir") ---"
  for f in "$dir"/*.tar.gz; do
    [ -f "$f" ] || continue
    total=$((total + 1))
    name=$(basename "$f")
    if [ -f "${f}.sha256" ]; then
      if sha256sum --check "${f}.sha256" --status 2>/dev/null; then
        log "  ✅ $name"; passed=$((passed + 1))
      else
        log_e "  ❌ $name — SHA256 不匹配"; failed=$((failed + 1))
      fi
    else
      if tar -tzf "$f" >/dev/null 2>&1; then
        log_w "  ⚠️  $name — 无校验（已测试可解压）"; skipped=$((skipped + 1))
      else
        log_e "  ❌ $name — 压缩包损坏"; failed=$((failed + 1))
      fi
    fi
  done
done

echo "" | tee -a "$LOG_FILE"
log "结果: 总计=$total 通过=$passed 失败=$failed 无校验=$skipped"
[ "$failed" -eq 0 ] && log "✅ 所有备份完整" || log_e "⚠️  $failed 个损坏！"
echo ""
