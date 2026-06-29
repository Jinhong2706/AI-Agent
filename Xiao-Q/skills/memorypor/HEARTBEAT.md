## 自我改进检查

此技能提供用于记忆维护的自我改进心跳。
使用以下代码段与工作区 HEARTBEAT.md 集成。

### 集成代码段

添加到您的工作区 `HEARTBEAT.md`：

```markdown
## 自我改进检查

- 读取 `<skill-path>/heartbeat-rules.md`
- 执行：`bash <skill-path>/scripts/heartbeat.sh`
- 如果是 HEARTBEAT_OK → 继续
- 如果是 HEARTBEAT_ACTION → 审查建议的更改
- 使用 `~/self-improving/heartbeat-state.md` 获取上次运行标记
```

将 `<skill-path>` 替换为实际技能路径。

### 可执行心跳脚本

对于自动化心跳，使用提供的脚本：

```bash
#!/bin/bash
# 自我改进心跳 — 可执行脚本
# 位置：<skill-path>/scripts/heartbeat.sh

SELF_IMPROVING_DIR="$HOME/self-improving"
STATE_FILE="$SELF_IMPROVING_DIR/heartbeat-state.md"
CONFIG_FILE="$SELF_IMPROVING_DIR/config.json"

# 读取配置限制
CORRECTIONS_LIMIT=$(jq -r '.limits.corrections // 200' "$CONFIG_FILE" 2>/dev/null || echo 200)
PENDING_LIMIT=$(jq -r '.limits.pending // 100' "$CONFIG_FILE" 2>/dev/null || echo 100)
OBSERVATION_DAYS=$(jq -r '.limits.pendingObservationDays // 14' "$CONFIG_FILE" 2>/dev/null || echo 14)
TIMEOUT_DAYS=$(jq -r '.limits.pendingTimeoutDays // 30' "$CONFIG_FILE" 2>/dev/null || echo 30)

# 1. 更新心跳开始时间
echo "last_heartbeat_started_at: $(date -Iseconds)" > "$STATE_FILE.tmp"
echo "last_reviewed_change_at: $(grep 'last_reviewed_change_at:' "$STATE_FILE" | cut -d: -f2- | tr -d ' ')" >> "$STATE_FILE.tmp"

# 2. 检查自上次审查以来的变更
LAST_REVIEWED=$(grep 'last_reviewed_change_at:' "$STATE_FILE" | cut -d: -f2- | tr -d ' ')
if [ -z "$LAST_REVIEWED" ] || [ "$LAST_REVIEWED" = "never" ]; then
    # 首次运行 — 扫描所有文件
    CHANGED_FILES=$(find "$SELF_IMPROVING_DIR" -type f -name "*.md" -o -name "*.json" 2>/dev/null)
else
    CHANGED_FILES=$(find "$SELF_IMPROVING_DIR" -type f \( -name "*.md" -o -name "*.json" \) -newer "$STATE_FILE" 2>/dev/null | grep -v "heartbeat-state.md")
fi

# 3. 如果没有变更，返回 OK
if [ -z "$CHANGED_FILES" ]; then
    echo "last_heartbeat_result: HEARTBEAT_OK" >> "$STATE_FILE.tmp"
    echo "## Last actions" >> "$STATE_FILE.tmp"
    echo "- no material change" >> "$STATE_FILE.tmp"
    mv "$STATE_FILE.tmp" "$STATE_FILE"
    echo "HEARTBEAT_OK"
    exit 0
fi

# 4. 如果有变更，执行保守组织
echo "last_heartbeat_result: HEARTBEAT_ACTION" >> "$STATE_FILE.tmp"
echo "## Last actions" >> "$STATE_FILE.tmp"

# 检查 corrections.md 大小
CORRECTIONS_COUNT=$(grep -c "## 2" "$SELF_IMPROVING_DIR/corrections.md" 2>/dev/null || echo 0)
if [ "$CORRECTIONS_COUNT" -ge "$CORRECTIONS_LIMIT" ]; then
    echo "- corrections.md 接近限制 ($CORRECTIONS_COUNT/$CORRECTIONS_LIMIT)" >> "$STATE_FILE.tmp"
    echo "- 考虑晋升条目或检查 corrections-pending.md 溢出处理"
fi

# 检查 corrections-pending.md 的观察候选
if [ -f "$SELF_IMPROVING_DIR/corrections-pending.md" ]; then
    # 检查是否有过期超过 OBSERVATION_DAYS 的条目
    OBSERVATION_CANDIDATES=$(grep -c "Pending since:" "$SELF_IMPROVING_DIR/corrections-pending.md" 2>/dev/null || echo 0)
    if [ "$OBSERVATION_CANDIDATES" -gt 0 ]; then
        echo "- $OBSERVATION_CANDIDATES 个条目在待处理区需要观察" >> "$STATE_FILE.tmp"
    fi
fi

# 检查 memory.md 大小
MEMORY_LINES=$(wc -l < "$SELF_IMPROVING_DIR/memory.md" 2>/dev/null || echo 0)
if [ "$MEMORY_LINES" -ge 180 ]; then
    echo "- memory.md 接近限制 ($MEMORY_LINES 行)" >> "$STATE_FILE.tmp"
    echo "- 考虑压缩或晋升审查"
fi

# 更新 last_reviewed_change_at
echo "last_reviewed_change_at: $(date -Iseconds)" >> "$STATE_FILE.tmp"
mv "$STATE_FILE.tmp" "$STATE_FILE"

echo "HEARTBEAT_ACTION"
echo "在 $STATE_FILE 审查建议的操作"
exit 0
```

### 快速心跳（内联）

对于最小集成，添加此内联脚本：

```bash
# 快速自我改进心跳（单行）
# 检查记忆维护需求，输出 HEARTBEAT_OK 或 HEARTBEAT_ACTION

SELF_IMPROVING_DIR="$HOME/self-improving"
STATE_FILE="$SELF_IMPROVING_DIR/heartbeat-state.md"
CONFIG_FILE="$SELF_IMPROVING_DIR/config.json"

CORRECTIONS_LIMIT=$(jq -r '.limits.corrections // 200' "$CONFIG_FILE" 2>/dev/null || echo 200)
CORRECTIONS_COUNT=$(grep -c "^## " "$SELF_IMPROVING_DIR/corrections.md" 2>/dev/null || echo 0)
MEMORY_LINES=$(wc -l < "$SELF_IMPROVING_DIR/memory.md" 2>/dev/null || echo 0)

if [ "$CORRECTIONS_COUNT" -lt "$CORRECTIONS_LIMIT" ] && [ "$MEMORY_LINES" -lt 180 ]; then
    echo "HEARTBEAT_OK"
else
    echo "HEARTBEAT_ACTION: corrections=$CORRECTIONS_COUNT/$CORRECTIONS_LIMIT, memory=${MEMORY_LINES}lines"
fi
```

### 心跳规则参考

有关完整心跳规则，参见 `heartbeat-rules.md`：

1. **开始**：立即写入 `last_heartbeat_started_at`
2. **扫描**：检查 `last_reviewed_change_at` 之后变更的文件
3. **如果没有变更**：返回 `HEARTBEAT_OK`
4. **如果有变更**：仅执行保守的组织
5. **更新**：仅在干净审查后设置 `last_reviewed_change_at`

### 状态字段

`~/self-improving/heartbeat-state.md` 跟踪：
- `last_heartbeat_started_at` — 心跳开始时间
- `last_reviewed_change_at` — 上次文件审查时间戳
- `last_heartbeat_result` — OK 或 ACTION
- `last_actions` — 所采取操作的简要笔记

### 安全规则

1. 大多数心跳运行应该什么都不做
2. 优先使用追加、总结或索引修复，而非大规模重写
3. 永远不要删除数据或覆盖不确定的文本
4. 如果范围模糊，将文件保持不变
5. 记录建议的后续行动，而非做不确定的更改
