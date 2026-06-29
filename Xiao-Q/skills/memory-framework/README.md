# Memory Framework - 记忆系统框架

**版本：** v1.0  
**定位：** 基于OpenClaw改良的通用记忆系统  
**作者：** 元神

---

## 特性

- L1/L2/L3 三层记忆分层
- WAL Protocol - 决策先记后答
- Working Buffer - 上下文缓冲
- learnings系统 - 错误记录与复盘
- 每日复盘 - 持续优化
- 通用框架 - 不含私密信息

---

## 安装

skillhub install memory-framework

---

## 目录结构

```
memory-framework/
├── brain/
│   ├── plan.md
│   ├── tasks/
│   ├── me/
│   ├── decisions/
│   ├── projects/
│   └── inbox.md
├── learnings/
│   ├── errors.json
│   └── recoveries.json
└── docs/
```

---

## 规则速查

| 场景 | 操作 |
|------|------|
| 用户纠正 | SESSION-STATE.md |
| 重大决定 | SESSION-STATE.md |
| 犯错 | learnings/errors.json |
| 上下文60% | working-buffer.md |

---

## 更新日志

### v1.0 (2026-04-08)
- 初始版本

---

**基于OpenClaw改良**
