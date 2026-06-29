# 心跳规则

使用心跳保持 `~/self-improving/` 有序，不产生混乱或丢失数据。

## 真实来源

保持工作区 `HEARTBEAT.md` 代码段最小化。
将本文件视为自我改进心跳行为的稳定契约。
仅将可变的运行状态存储在 `~/self-improving/heartbeat-state.md` 中。

## 每次心跳开始时

1. 确保 `~/self-improving/heartbeat-state.md` 存在。
2. 立即以 ISO 8601 格式写入 `last_heartbeat_started_at`。
3. 读取之前的 `last_reviewed_change_at`。
4. 扫描 `~/self-improving/` 中在该时刻之后变更的文件，排除 `heartbeat-state.md` 本身。

## 如果没有变更

- 设置 `last_heartbeat_result: HEARTBEAT_OK`
- 如果保留操作日志，附加简短的"无实质性变更"注释
- 返回 `HEARTBEAT_OK`

## 如果有变更

仅进行保守的组织：

- 如果计数或文件引用漂移，刷新 `index.md`
- 通过合并重复项或总结重复条目来压缩过大文件
- 仅在目标明确无误时将明显放错位置的笔记移动到正确的命名空间
- 完全保留已确认规则和明确纠错
- 仅在审查干净完成后更新 `last_reviewed_change_at`

## 安全规则

- 大多数心跳运行应该什么都不做
- 优先使用追加、总结或索引修复，而非大规模重写
- 永远不要删除数据、清空文件或覆盖不确定的文本
- 永远不要重新组织 `~/self-improving/` 外的文件
- 如果范围模糊，将文件保持不变，并记录建议的后续行动

## 状态字段

保持 `~/self-improving/heartbeat-state.md` 简单：

- `last_heartbeat_started_at`
- `last_reviewed_change_at`
- `last_heartbeat_result`
- `last_actions`

## 行为标准

心跳的存在是为了保持记忆系统整洁和可信赖。
如果没有规则明显违反，不要做任何事情。
