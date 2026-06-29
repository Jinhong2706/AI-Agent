# Agent Browser

Agent Browser 是一个独立的浏览器自动化 CLI 工具。

## 安装

```bash
npm install -g agent-browser
# 或者
brew install agent-browser

# 下载 Chrome binary
agent-browser install
```

## 环境变量（可选）

```bash
# 启用 headed 模式调试
AGENT_BROWSER_HEADED=1

# 设置超时（毫秒）
AGENT_BROWSER_DEFAULT_TIMEOUT=25000

# 内容边界保护
AGENT_BROWSER_CONTENT_BOUNDARIES=1
```

## 安装 Skill

```bash
# 从 ClawHub 安装
openclaw skill install agent-browser
```

## 能力

- 完整浏览器自动化
- 动态页面渲染（JavaScript/SPA）
- 表单填写与交互
- 截图（含标注模式）
- 数据提取
- 多页面并行

## 验证

```bash
agent-browser --help
```

## 注意

浏览器启动较慢（3-8秒），适合需要交互或动态渲染的场景，不适合简单文本搜索。
