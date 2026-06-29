# 待处理纠错区 — 操作手册

> 本文件存储 `corrections.md` 超出限制时的过剩纠错。
> 此处的条目处于观察期（14天），然后评估归档/丢弃。
> 此处的条目仍累积计数以进行晋升跟踪。

## 文件位置

```
~/self-improving/
├── corrections.md           # 主要缓冲区：200条（默认）
├── corrections-pending.md  # 待处理区：100-500条（基于层级）
└── archive/                # 最终归档
```

## 触发条件

| 条件 | 动作 |
|-----------|--------|
| corrections.md 达到 200 条 | 如果 corrections-pending.md 不存在则创建 |
| corrections-pending.md 也满了 | 首先归档最旧的条目 |

## 操作流程

### 添加新条目时（corrections.md 已满）

```
1. 检查 corrections-pending.md 是否存在
2. 如果是 → 附加新条目到 corrections-pending.md，带时间戳
3. 如果否 → 创建 corrections-pending.md，移动最旧的非晋升条目
4. 待处理中的条目格式：与 corrections.md 相同 + pending_since 日期
5. 设置 pending_since = 今天
6. 如果找到重复则增加计数
```

### 每日观察检查（通过心跳）

```
1. 读取 corrections-pending.md
2. 对于每个条目：
   a. 计算 days_since_pending = 今天 - pending_since
   b. 如果 days_since_pending >= 14 且计数 < 3：
      - 评估：晋升到 memory.md 或归档到 archive/
      - 如果计数 >= 3 但未确认：保留在待处理（仍然有效）
   c. 如果 days_since_pending >= 30 且计数 < 3：
      - 归档到 archive/，原因："timeout_without_promotion"（超时未晋升）
3. 更新 corrections-pending.md
```

### 条目再次被纠错时（计数增加）

```
1. 在 corrections.md 和 corrections-pending.md 中搜索重复
2. 如果在 corrections-pending.md 中找到：
   - 增加计数
   - 更新时间戳
   - 重置 pending_since = 今天（重新开始14天观察）
3. 如果计数 >= 3：
   - 提示用户确认
   - 如果确认 → 晋升到 memory.md，从待处理中移除
```

## 待处理区中的条目格式

```markdown
## YYYY-MM-DD HH:MM — [类型]

**纠错(Correction)：** "用户说的"
**上下文(Context)：** 发生在哪里
**计数(Count)：** N（在所有区域累积）
**待处理自(Pending since)：** YYYY-MM-DD
**原始区域(Original zone)：** corrections.md

### 晋升跟踪
- [ ] 第1次出现
- [ ] 第2次出现
- [x] 第3次出现 → 等待确认
```

## 观察期规则

| 在待处理区天数 | 计数 < 3 | 计数 >= 3 |
|-----------------|-----------|------------|
| 0-13天 | 继续观察 | 提示确认 |
| 14-29天 | 评估归档 | 保留（等待确认） |
| 30+天 | 归档："timeout"（超时） | 保留直到确认/归档 |

## 晋升到热层

当用户确认待处理条目时：

```
1. 在 memory.md（热层）中创建条目
2. 包含来源引用："Promoted from corrections-pending.md:entry-date"
3. 从 corrections-pending.md 中移除条目
4. 如果跟踪历史，更新归档记录中的计数
5. 在 heartbeat-state.md 中记录晋升
```

## 归档格式

```markdown
## 已归档：YYYY-MM-DD

### 原始条目（来自 corrections-pending.md）
- **纠错(Correction)：** "..."
- **上下文(Context)：** "..."
- **计数(Count)：** N
- **待处理自(Pending since)：** YYYY-MM-DD
- **在待处理区天数：** X

**原因(Reason)：** timeout_without_promotion（超时未晋升）| manual_archive（手动归档）| superseded（已取代）

**来源文件(Source file)：** corrections-pending.md
```

## 配置

编辑 `~/self-improving/config.json` 调整待处理区大小：

```json
{
  "tier": "high",
  "limits": {
    "corrections": 500,
    "pending": 300,
    "pendingObservationDays": 14,
    "pendingTimeoutDays": 30
  }
}
```

## 快速参考

| 命令 | 动作 |
|---------|--------|
| 检查待处理计数 | `grep -c "Pending since" corrections-pending.md` |
| 列出 >14 天的条目 | 搜索 "Pending since" >14天前 |
| 强制晋升 | 将条目移动到 memory.md，更新为 "promoted" |
| 强制归档 | 移动到 archive/，记录原因 |

## 安全规则

1. **永远不要直接删除** 条目 — 总是归档并附带原因
2. **始终保留计数** — 它代表学习历史
3. **始终包含 pending_since** — 观察逻辑需要
4. **始终在计数 >= 3 时提示** 确认
5. **永远不要未经确认就晋升** — 即使计数 >= 3
