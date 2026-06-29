#!/bin/bash
# 检查斗鱼主播开播状态（使用官方JSON接口）
# 用法: ./check_room.sh <房间号>
# 输出: JSON格式 {"room_id":"12345","nickname":"xxx","title":"xxx","is_live":true/false,"cate":"xxx"}

ROOM_ID="$1"

if [ -z "$ROOM_ID" ]; then
  echo '{"error":"缺少房间号"}'
  exit 1
fi

# 用python脚本查询（更可靠）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/douyu_room_status.py" "$ROOM_ID"
