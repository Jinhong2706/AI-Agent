# Memory Framework - 模板说明

**版本：** v1.0

---

## 📝 模板清单

| 文件 | 用途 | 必须填写 |
|------|------|---------|
| brain/me/identity.md | 身份设定 | ✅ |
| brain/plan.md | 人生方向 | ✅ |
| brain/tasks/active.md | 当前任务 | ✅ |
| brain/tasks/daily/TEMPLATE.md | 每日计划 | ⬜ |
| brain/me/learned.md | 教训记录 | ⬜ |
| brain/inbox.md | 待办事项 | ⬜ |
| learnings/errors.json | 错误记录 | ⬜ |
| learnings/recoveries.json | 恢复记录 | ⬜ |

---

## 📄 各模板说明

### brain/me/identity.md（必须）

```markdown
# IDENTITY.md - 身份设定

- **Name：** AI助手名字
- **Creature：** AI助手类型
- **Vibe：** 风格
- **Emoji：** emoji
```

### brain/plan.md（必须）

```markdown
# Plan - 人生/项目方向

## 核心使命
[核心目标]

## 终极目标 🎯
[长期目标]

## 里程碑
| 目标 | 时间 | 状态 |
```

### brain/tasks/active.md（必须）

```markdown
## 🔴 紧急
- [ ]

## 🟡 进行中
- [ ]

## 🟢 计划中
- [ ]
```

---

## 🔧 JSON模板

### learnings/errors.json

```json
{
  "id": "err-XXX",
  "timestamp": "YYYY-MM-DDTHH:MM:SS",
  "error_type": "错误类型",
  "error_message": "错误描述",
  "context": {
    "situation": "场景",
    "my_claim": "我的判断",
    "actual_fact": "实际"
  },
  "root_cause": "根本原因",
  "resolution": "解决方法",
  "status": "recorded"
}
```

### learnings/recoveries.json

```json
{
  "id": "rec-XXX",
  "timestamp": "YYYY-MM-DDTHH:MM:SS",
  "issue": "问题",
  "root_cause": "原因",
  "solution": "方案",
  "outcome": "结果",
  "status": "resolved"
}
```

---

## 📁 目录说明

```
brain/
├── decisions/          ← 决策存档（YYYY-MM-DD-slug.md）
├── projects/          ← 项目状态
└── inbox.md           ← 待办事项（超过7条归档）
```

---

## ⚠️ 注意事项

1. **不要直接修改别人的identity.md** - 每个AI助手独立
2. **错误记录要真实** - 不要美化，记录教训
3. **定期复盘** - 每周更新learned.md
4. **SESSION-STATE.md是临时的** - 处理完要删除

---

**更多用法：查看 QUICK-START.md**
