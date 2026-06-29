---
name: deepseek-thinking-fix
version: "2.0.0"
description: >
  Fix DeepSeek V4 Flash/Pro thinking mode 400 error in multi-turn
  conversations. Automatically backfills reasoning_content on all
  assistant messages before sending to API. Covers all code paths:
  main loop, cron jobs, gateway sessions, and auxiliary tasks.
author: Hermes-DeepSeek-Fix Team
tags:
  - deepseek
  - thinking-mode
  - 400-error
  - reasoning-content
  - tool-call
  - v4-flash
  - v4-pro
  - hotfix
homepage: https://github.com/hermes-deepseek-fix/hermes-deepseek-fix
install:
  plugin: mkdir -p ~/.hermes/plugins/deepseek-thinking-fix && cp -r * ~/.hermes/plugins/deepseek-thinking-fix/
  config: 'plugins: { enabled: [deepseek-thinking-fix] }'
---

# DeepSeek Thinking Fix 🧠

## 问题

DeepSeek V4 Flash/Pro 开了 thinking mode 后，多轮对话中 agent 调用工具时 API 返回 400：

```
{"error": "The `reasoning_content` in the thinking mode must be passed back to the API."}
```

这不是 Hermes 独有的 bug — **Cursor、Continue.dev、RooCode、LangChain、OpenCode 全都有**。根因是 DeepSeek 在 OpenAI 兼容协议上加了私有字段 `reasoning_content`，多数框架没有正确处理这个字段的 round-trip。

## 本技能做了什么

在消息发往 DeepSeek API 之前，自动：

1. **回填 `reasoning_content`** — 所有 assistant 消息强制带上此字段（有内容保留内容，没有内容填空字符串）
2. **深度拷贝防状态突变** — Python 多个函数共享同一 dict 引用时，防止后一个覆盖前一个的修改
3. **跨厂商字段清理** — 切换到非 thinking 模型时自动移除 `reasoning_content`，防止泄漏
4. **持久化字段修复** — 存储时同时保留 `reasoning` 和 `reasoning_content`，加载时自动补全
5. **显式 thinking 参数** — thinking=off 时传入 `{type: "disabled"}`，防止 DeepSeek 默认开启 thinking

## 覆盖的已知问题

- `#14933` — DeepSeek V4 thinking mode 初始 400 报告
- `#15353` — tool-call 消息缺 reasoning_content
- `#16137` — plain assistant 消息缺 reasoning_content
- `#17400` — 间歇性丢失（同 session 某些消息有某些没有）
- `#15213` — cron/auxiliary 路径完全没处理
- `#16844` — 持久化字段名不一致：reasoning ≠ reasoning_content
- `#15748` — 跨厂商切换时旧 RC 泄漏
- `#17052` — 上一轮 stale reasoning 污染本轮
- `#15700` — thinking:disabled 必须显式传入
- `#17212` — direct API 缺 thinking control

## 使用场景

- 用 Hermes Agent + DeepSeek V4 Flash/Pro 做 agentic 任务
- 多轮 tool-call 场景（搜索、代码执行、文件操作等）
- Cron 定时任务 + DeepSeek thinking（辅助路径）
- Session 持久化后恢复继续对话

## 替代方案对比

| 方案 | 安装复杂度 | 维护成本 | 效果 |
|------|-----------|---------|------|
| **本技能 ⭐** | 复制目录 + 改配置 | 自动，随 Hermes 升级兼容 | 覆盖全部路径 |
| 逐个合并上游 PR | 等 upstream 合入 | 每个 Hermes 版本重新检查 | 部分覆盖 |
| 手动改 run_agent.py | 改 ~50 行源码 | 每次升级重改 | 只覆盖主循环 |
| 换模型（不用 DeepSeek） | 改配置 | 无 | 但失去低成本推理 |

## 验证

安装后开一个新的 Hermes 会话，使用 DeepSeek V4 Flash + thinking mode，进行至少 3 轮 tool-call 对话：

```
User: 查一下今天天气，然后搜索最近的新闻，最后总结一下
Agent: [调用 get_weather] → [调用 search_news] → [总结]
```

如果没有 400 错误，说明修复生效。

## 标签

deepseek v4 flash pro thinking mode 400 reasoning_content fix hermes plugin
