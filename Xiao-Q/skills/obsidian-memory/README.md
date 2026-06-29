# obsidian-memory · WorkBuddy 长期记忆 Skill

让 WorkBuddy 拥有跨会话持久记忆，每次启动自动从 Obsidian 读取上下文，任务结束主动写回更新。

---

## 功能

- **启动自动加载**：打开 WorkBuddy 自动读取个人偏好和近期任务记录
- **触发词写回**：说 `任务完成` / `/记一下` / `/记录` / `/更新记忆` 立即写入 Obsidian
- **每周记忆审计**：说 `/审计记忆` 清理冲突条目和已完结项目，AI 列出建议后你确认再执行
- **精准读取**：只加载当前任务相关文件，不全量塞入上下文

---

## 安装后需要做的两件事

### 1. 在 Obsidian 创建记忆目录

在你的 Vault 根目录新建：

```
你的Vault/
└── _agent-memory/
    ├── profile.md          ← 从本 Skill 的 templates/ 复制
    ├── session-log.md      ← 从本 Skill 的 templates/ 复制
    ├── audit-log.md        ← 新建空文件
    └── projects/
        └── archive/        ← 新建空文件夹
```

### 2. 配置路径

在 WorkBuddy 配置目录（Windows：`%USERPROFILE%\.workbuddy\`，Mac：`~/.workbuddy/`）新建 `SOUL.md`，写入：

```
# 配置
OBSIDIAN_MEMORY_PATH: 你的_agent-memory完整路径
```

示例：
```
OBSIDIAN_MEMORY_PATH: D:\obsidian\vault\_agent-memory
```

---

## 触发词速查

| 触发词 | 作用 |
|--------|------|
| `任务完成` | 整个任务结束，全量写回 |
| `/记一下` | 随时记录当前关键信息 |
| `/记录` | 同上 |
| `/更新记忆` | 同上 |
| `/审计记忆` | 触发记忆审计，清理过期内容 |

---

## 记忆文件说明

| 文件 | 内容 |
|------|------|
| `profile.md` | 个人偏好、写作风格、开发习惯 |
| `projects/{名称}.md` | 项目状态、决策记录、下次起点 |
| `session-log.md` | 最近 10 条任务摘要 |
| `audit-log.md` | 审计历史记录 |

所有文件均为普通 Markdown，可在 Obsidian 中直接查看和编辑。

---

GitHub：https://github.com/GDPLAY/obsidian-memory
