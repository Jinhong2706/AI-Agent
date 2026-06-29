#!/bin/bash
# 轮询所有监控的主播，检测到开播后输出提醒
# 依赖: check_room.sh 需在同级目录
# 数据文件: ./monitored_rooms.json ./last_status.json

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECK_SCRIPT="$SCRIPT_DIR/check_room.sh"
MONITOR_FILE="$SCRIPT_DIR/../monitored_rooms.json"
LAST_FILE="$SCRIPT_DIR/../last_status.json"

# 初始化文件
[ ! -f "$MONITOR_FILE" ] && echo '{"rooms":[]}' > "$MONITOR_FILE"
[ ! -f "$LAST_FILE" ] && echo '{}' > "$LAST_FILE"

# 读取监控列表
ROOMS=$(cat "$MONITOR_FILE" | grep -o '"room_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ROOMS" ]; then
  echo "监控列表为空，无需轮询"
  exit 0
fi

# 读取上次状态
LAST_STATUS=$(cat "$LAST_FILE")

# 遍历每个房间
for ROOM_ID in $ROOMS; do
  # 查询当前状态
  RESULT=$("$CHECK_SCRIPT" "$ROOM_ID")
  IS_LIVE=$(echo "$RESULT" | grep -o '"is_live":[^,}]*' | cut -d':' -f2 | tr -d ' ')
  NICKNAME=$(echo "$RESULT" | grep -o '"nickname":"[^"]*"' | cut -d'"' -f4)
  TITLE=$(echo "$RESULT" | grep -o '"title":"[^"]*"' | cut -d'"' -f4)
  CATE=$(echo "$RESULT" | grep -o '"cate":"[^"]*"' | cut -d'"' -f4)
  URL=$(echo "$RESULT" | grep -o '"url":"[^"]*"' | cut -d'"' -f4)

  # 读取上次状态
  LAST_WAS_LIVE=$(echo "$LAST_STATUS" | grep -o "\"$ROOM_ID\"[^{]*{\"is_live\":[^,}]*" | grep -o 'is_live":[^,}]*' | cut -d':' -f2 | tr -d ' ')

  # 状态变化检测：上次off/不存在 → 本次on = 触发开播提醒
  if [ "$IS_LIVE" = "true" ] && [ "$LAST_WAS_LIVE" != "true" ]; then
    echo "NOTIFY:$ROOM_ID:$NICKNAME:$TITLE:$CATE:$URL"
  fi

  # 更新状态（用简单方式：重写整个文件）
  # 用jq更可靠，但避免依赖，用python处理
  python3 -c "
import json, sys
last = json.load(open('$LAST_FILE'))
room = '$ROOM_ID'
last[room] = {'is_live': '$IS_LIVE' == 'true', 'checked_at': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
json.dump(last, open('$LAST_FILE','w'), ensure_ascii=False, indent=2)
" 2>/dev/null || true

  echo "CHECKED:$ROOM_ID:$IS_LIVE:$NICKNAME"
done
