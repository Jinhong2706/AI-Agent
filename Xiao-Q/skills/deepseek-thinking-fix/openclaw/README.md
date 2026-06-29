# DeepSeek Thinking Fix — OpenClaw 移植版

OpenClaw 用户通常不需要这个插件——因为 OpenClaw 在 v2026.4.24~4.27 已经通过自带的 DeepSeek provider 插件修复了此问题。

**但是**，以下情况可能需要：
1. 仍在使用 v2026.4.24 之前的旧版 OpenClaw
2. 通过自定义 provider 使用 DeepSeek（而不是官方 bundled provider）
3. 使用 OpenRouter / Venice 等第三方中转时 thinking 控制参数出问题
4. 想对比 OpenClaw 和 Hermes 的修复方式

## 安装

```bash
openclaw plugin install deepseek-thinking-fix
```

## 与 OpenClaw 原生修复的对比

| 维度 | OpenClaw 原生修复 | 本插件 |
|------|-----------------|--------|
| 版本要求 | v2026.4.24+ | 无版本限制 |
| 官方支持 | ✅ bundled provider | ❌ 第三方 |
| 维护 | OpenClaw 团队 | 社区 |
| 适用范围 | 仅官方的 DeepSeek provider | 任何配置 |

## 建议

**如果你是 OpenClaw 用户且版本 >= v2026.4.24，不需要安装本插件。**
直接用官方自带的修复即可。
