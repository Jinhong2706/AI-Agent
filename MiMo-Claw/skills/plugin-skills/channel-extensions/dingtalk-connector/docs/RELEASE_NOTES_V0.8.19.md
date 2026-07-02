# Release Notes - v0.8.19

## 🎉 新版本亮点 / Highlights

本次版本新增 **DING 消息** 和 **钉钉文档** 两大能力，并新增 **多 Agent 配置文档**（`MULTI_AGENT_SETUP.md`），帮助用户快速完成多 Agent 部署。

This release adds **DING messaging** and **DingTalk Document** capabilities, and includes a new **Multi-Agent setup guide** (`MULTI_AGENT_SETUP.md`) for quick multi-Agent deployment.

## ✨ 新增 / Added

- **🔔 DING 消息 / DING Messaging**
  支持向用户/群发送强提醒 DING（应用内/短信/电话），用户授权后即可使用。
  Send urgent DING reminders (in-app / SMS / phone call) to users or groups; available after user authorization.

- **📄 钉钉文档 / DingTalk Document**
  支持创建、追加、搜索、列举钉钉文档，用户授权后即可使用。
  Create, append, search, and list DingTalk documents; available after user authorization.

- **📝 日志 / Reports**
  支持提交日报/周报、查询历史日志记录，用户授权后即可使用。
  Submit daily/weekly reports and query historical logs; available after user authorization.

- **插件重复加载检测 / Duplicate plugin load detection**
  全局 Symbol 自检同一 plugin id 多路径加载，防止 stream 回调冲突。
  Detects duplicate plugin loads via global Symbol, preventing stream callback conflicts.

## 🐛 修复 / Fixes

- AI Card QPS 限流不再误报用户错误，改为 warn 日志 / QPS throttle no longer sends error to user
- AI Card 令牌桶新增串行化锁，修复并发击穿 / Token bucket serialization lock fixes concurrency bypass
- 多 Agent 配置检测改为 OR 条件，放宽触发保护 / Multi-Agent detection relaxed to OR condition
- CLI 提示文案统一中英文混合 / CLI prompts unified to bilingual format

## ✅ 改进 / Improvements

- 新增多 Agent 配置文档 `docs/MULTI_AGENT_SETUP.md` / Added multi-Agent setup guide `docs/MULTI_AGENT_SETUP.md`
- DWS CLI 升级提示 / DWS CLI upgrade prompt during install
- 消息上下文透传 `BotChatbotUserId` / `BotChatbotCorpId` / BotIdentity context passthrough
- reply-dispatcher 支持 text/markdown 降级发送 + 裸别名检测 / text/markdown fallback with bare alias detection

## 📥 安装升级 / Installation & Upgrade

```bash
npx openclaw@latest add @dingtalk-real-ai/dingtalk-connector
```

或指定版本：
```bash
npx openclaw@latest add @dingtalk-real-ai/dingtalk-connector@0.8.19
```

## 🔗 相关链接 / Related Links

- [完整变更日志](https://github.com/DingTalk-Real-AI/dingtalk-openclaw-connector/blob/main/CHANGELOG.md)
- [使用文档](https://github.com/DingTalk-Real-AI/dingtalk-openclaw-connector/blob/main/README.md)
- [故障排查](https://github.com/DingTalk-Real-AI/dingtalk-openclaw-connector/blob/main/docs/TROUBLESHOOTING.md)

---

**发布日期 / Release Date**：2026-04-25
**版本号 / Version**：v0.8.19
**兼容性 / Compatibility**：OpenClaw Gateway 2026.4.9+
