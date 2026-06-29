# Memory Framework - 快速开始

**版本：** v1.0

---

## 第一步：初始化

### 1.1 填写身份

编辑 `brain/me/identity.md`：

```markdown
# IDENTITY.md - 身份设定

- **Name：** 你的AI助手名字
- **Creature：** AI助手类型
- **Vibe：** 风格描述
- **Emoji：** 🎯
```

### 1.2 填写目标

编辑 `brain/plan.md`：

```markdown
# Plan - 人生方向

## 核心使命
你的核心目标是什么？

## 终极目标 🎯
长期目标

## 里程碑
| 目标 | 时间 | 状态 |
```

### 1.3 填写任务

编辑 `brain/tasks/active.md`：

```markdown
## 🔴 紧急
- [ ]

## 🟡 进行中
- [ ]

## 🟢 计划中
- [ ]
```

---

## 第二步：理解规则

### WAL Protocol（必须遵守）

```
用户纠正/决定 → 先写SESSION-STATE.md → 再回复
```

**触发场景：**
- "不是X，是Y"
- "用X，不用Y"
- 重大决定
- 偏好设置

### Working Buffer Protocol

```
上下文>60% → 启用working-buffer.md → 记录每条消息
```

---

## 第三步：日常使用

### 每日开始

```
1. 读 brain/plan.md - 今日方向
2. 读 brain/tasks/daily/YYYY-MM-DD.md - 今日任务
3. 检查 inbox.md - 待处理事项
```

### 每日结束

```
1. 更新今日任务完成情况
2. 记录学到的新教训（learned.md）
3. 归档 inbox.md（超过7条）
```

### 犯错时

```
1. 写 learnings/errors.json
2. 分析根本原因
3. 写 brain/me/learned.md
4. 更新 brain/tasks/active.md
```

---

## 第四步：进阶使用

### 决策存档

重大决策 → `brain/decisions/YYYY-MM-DD-slug.md`

### 项目追踪

项目状态 → `brain/projects/`

### 每日复盘

每日记录 → `brain/tasks/daily/YYYY-MM-DD.md`

---

## 模板位置

| 模板 | 位置 |
|------|------|
| 每日计划 | `brain/tasks/daily/TEMPLATE.md` |
| 错误记录 | `learnings/errors.json` |
| 恢复记录 | `learnings/recoveries.json` |

---

## 常见问题

**Q: SESSION-STATE.md是什么？**  
A: 记录用户纠正和重大决定的临时文件，处理后删除。

**Q: 什么时候更新MEMORY.md？**  
A: 每周或每月一次，将重要内容从brain/提炼到MEMORY.md。

**Q: inbox.md超过7条怎么办？**  
A: 归档旧条目到brain/decisions/或brain/projects/。

---

**有问题？查看 SKILL.md 或提交Issue**
