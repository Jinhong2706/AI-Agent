# 纠错日志 — 模板

> 首次使用时将此模板复制到 `~/self-improving/corrections.md`。
> 保留最近 N 条纠错（基于 config.json 中的层级配置）。
> 旧条目评估晋升或移动到 `corrections-pending.md`。
> 有关溢出处理程序，参见 `corrections-pending.md`。

## 日志格式

```markdown
## YYYY-MM-DD HH:MM — [类型]

- **纠错：** "用户说的"
- **上下文：** 发生在哪里
- **计数：** N（用于晋升跟踪，重复时递增）
- **状态：** pending（待处理）| confirmed（已确认）| promoted（已晋升）| archived（已归档）

类型类别：
- format（格式）：代码风格、格式、空格
- technical（技术）：技术决策、架构、工具
- communication（沟通）：回复风格、语气、长度
- project（项目）：项目特定模式
- domain（领域）：领域特定模式
```

## 条目示例

```markdown
## 2026-05-25 14:32 — format（格式）

- **纠错：** "使用2个空格缩进，不是4个"
- **上下文：** 编辑TypeScript文件
- **计数：** 1
- **状态：** pending（待处理）
```

## 状态流程

```
pending（待处理）→ （3次+确认后）→ confirmed（已确认）→ promoted to memory.md
pending（待处理）→ （30天未使用）→ archived（已归档）
```
