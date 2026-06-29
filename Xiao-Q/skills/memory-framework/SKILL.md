# Memory Framework - 记忆系统框架

**版本：** v1.0  
**定位：** 通用记忆系统框架，基于OpenClaw改良  
**适用：** 个人AI助手、团队协作，知识管理

---

## 核心特性

- L1/L2/L3 三层记忆分层
- WAL Protocol - 决策先记后答
- Working Buffer - 上下文缓冲
- learnings系统 - 错误记录与复盘
- 每日复盘 - 持续优化

---

## 目录结构

```
memory-framework/
├── README.md
├── SKILL.md
├── manifest.json
├── brain/
│   ├── plan.md
│   ├── tasks/
│   │   ├── active.md
│   │   └── daily/
│   ├── me/
│   │   ├── identity.md
│   │   └── learned.md
│   ├── decisions/
│   ├── projects/
│   └── inbox.md
├── learnings/
│   ├── errors.json
│   └── recoveries.json
└── docs/
    ├── QUICK-START.md
    └── TEMPLATES.md
```

---

## 快速开始

1. 编辑 brain/me/identity.md - 填入你的身份
2. 编辑 brain/plan.md - 填入你的目标
3. 编辑 brain/tasks/active.md - 填入当前任务

---

## 规则速查

| 场景 | 操作 |
|------|------|
| 用户纠正 | SESSION-STATE.md |
| 重大决定 | SESSION-STATE.md |
| 犯错 | learnings/errors.json |
| 上下文60% | working-buffer.md |
| 每天结束 | brain/tasks/daily/ |

---

## 版本

- v1.0 - 初始版本

---

**基于OpenClaw改良**
