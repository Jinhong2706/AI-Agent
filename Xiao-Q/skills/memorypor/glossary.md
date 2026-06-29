# 术语表 — 统一术语

> 本文件为自我改进技能定义一致的术语。
> 所有其他文件应使用以下规范形式引用这些术语。

## 核心概念

| 术语 | 规范形式 | 避免使用的别名 | 定义 |
|------|---------------|-----------------|------------|
| 热存储 | **热层(HOT)** | hot tier, hot layer, hot storage | 始终加载的记忆层（memory.md） |
| 温存储 | **温层(WARM)** | warm tier, warm layer | 按需加载的层（projects/, domains/） |
| 冷存储 | **冷层(COLD)** | cold tier, cold layer, archive | 已归档的层（archive/） |
| 纠错 | **correction** | correction log entry, correction record | 用户明确纠正代理行为的反馈 |
| 晋升 | **promote** | promoted, promotion | 将条目从纠错移动到热层记忆 |
| 降级 | **demote** | demoted, demotion | 将条目从热层移动到温层/冷层 |
| 待处理区 | **corrections-pending.md** | pending, pending zone, observation zone | 纠错的溢出缓冲区 |

## 层级术语

```
┌─────────────────────────────────────────────────────────────┐
│                        热层 (memory.md)                      │
│  始终加载。≤200行（高频≤400行）。                             │
│  已确认的偏好和永久规则。                                      │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ promote（晋升）（3次+确认后）
                              │
┌─────────────────────────────────────────────────────────────┐
│           温层 (projects/, domains/)                          │
│  按上下文匹配加载。每文件≤500行。                             │
│  项目特定和领域特定的模式。                                    │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ demote（降级）（30天未使用）
                              │
┌─────────────────────────────────────────────────────────────┐
│                  冷层 (archive/)                             │
│  按明确查询加载。无限。                                        │
│  衰减的模式、非活动项目。                                     │
└─────────────────────────────────────────────────────────────┘
```

## 状态

| 状态 | 定义 | 转换 |
|--------|------------|-------------|
| **tentative（试探性）** | 单次出现，观察重复 | → emerging（出现中） |
| **emerging（出现中）** | 2次出现，可能是模式 | → pending（待确认）或 archive（归档） |
| **pending（待确认）** | 3次出现，等待确认 | → confirmed（已确认）或 archive（归档） |
| **confirmed（已确认）** | 用户批准，永久规则 | →（永不自动降级） |
| **archived（已归档）** | 90+天非活动，为参考保留 | →（可恢复） |

## 动作动词（一致使用）

| 动作 | 规范动词 | 避免 |
|--------|---------------|------|
| 移动到热层 | **promote（晋升）** | graduate, elevate, graduate to hot |
| 移动到温层/冷层 | **demote（降级）** | downgrade, lower |
| 添加新条目 | **log（记录）** | record, add, append |
| 永久移除 | **delete（删除）** | remove, erase, destroy |
| 移动到归档 | **archive（归档）** | move to cold, cold-store |
| 用户批准规则 | **confirm（确认）** | approve, validate, accept |
| 用户拒绝规则 | **reject（拒绝）** | deny, dismiss, refuse |

## 文件名（规范）

| 文件 | 用途 |
|------|---------|
| `memory.md` | 热层 — 已确认的偏好 |
| `corrections.md` | 主要纠错日志 |
| `corrections-pending.md` | 溢出待处理区 |
| `index.md` | 带行数的主题索引 |
| `heartbeat-state.md` | 心跳运行标记 |
| `config.json` | 容量配置 |
| `archive/` | 冷存储目录 |

## 命令别名（标准化）

| 用户请求 | 规范命令 | 实现 |
|--------------|-------------------|----------------|
| "你对X了解多少？" | `/memory query X` | 搜索所有层级 |
| "显示我的记忆" | `/memory show` | 显示 memory.md |
| "显示[项目]模式" | `/memory project <name>` | 加载项目命名空间 |
| "忘记X" | `/memory forget X` | 从所有层级移除 |
| "记忆统计" | `/memory stats` | 显示层级统计 |
| "导出记忆" | `/memory export` | 生成ZIP存档 |
| "导入记忆" | `/memory import <file>` | 从存档恢复 |

## 术语映射（中英对照）

| 中文 | English（规范） |
|---------|---------------------|
| 晋升 | promote |
| 降级 | demote |
| 待观察区 | pending zone |
| 热存储 | HOT |
| 冷存储 | COLD |
| 确认 | confirm |
| 归档 | archive |
| 压缩 | compress |
| 合并 | merge |

## 术语表维护

更新术语时：
1. 首先更新此术语表
2. 在所有其他文件中搜索旧术语
3. 用规范形式替换
4. 在 CHANGELOG.md 中记录破坏性变更

## 反模式

- **永远不要使用**：graduate（使用 promote），downgrade（使用 demote）
- **永远不要使用**：hot layer（使用 HOT tier 或 HOT）
- **永远不要使用**：cold storage 作为动词（使用 archive）
- **永远不要混合**：同一概念的中英文术语
