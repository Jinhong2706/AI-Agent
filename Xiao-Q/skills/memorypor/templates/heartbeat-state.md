# 心跳状态 — 模板

> 首次使用时将此模板复制到 `~/self-improving/heartbeat-state.md`。
> 仅存储轻量级运行标记和维护笔记。
> 永远不要将其变成另一个记忆日志。

```markdown
# 自我改进心跳状态

last_heartbeat_started_at: never
last_reviewed_change_at: never
last_heartbeat_result: never

## 最近操作
- 尚无
```

## 字段

| 字段 | 用途 | 更新时机 |
|-------|---------|---------------|
| `last_heartbeat_started_at` | 心跳开始时间 | 每次运行开始时 |
| `last_reviewed_change_at` | 上次干净文件审查时间 | 成功审查后 |
| `last_heartbeat_result` | HEARTBEAT_OK 或 HEARTBEAT_ACTION | 完成后 |
| `last_actions` | 简要操作笔记 | 仅在 HEARTBEAT_ACTION 时 |

## 规则

1. 在每次心跳开始时更新 `last_heartbeat_started_at`
2. 仅在干净审查后更新 `last_reviewed_change_at`
3. 保持 `last_actions` 简短且事实
4. 永远不要将此文件变成另一个记忆日志
5. 如果心跳失败，记录错误但保留之前状态
