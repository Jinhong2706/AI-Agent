# 配置 MiniMax Token Plan

## 获取 API Key

1. 访问 [MiniMax 平台](https://platform.minimaxi.com/subscribe/token-plan) (中国大陆)
   或 [MiniMax 国际站](https://platform.minimax.io/subscribe/token-plan) (全球)
2. 订阅 Token Plan 并获取 API Key

## 环境变量

```bash
# 中国大陆
export MINIMAX_API_KEY="sk-..."
export MINIMAX_API_HOST="https://api.minimaxi.com"

# 全球
export MINIMAX_API_KEY="sk-..."
export MINIMAX_API_HOST="https://api.minimax.io"
```

推荐写入 `~/.openclaw/.env` 持久化。

## 安装 Skill

```bash
# 从 ClawHub 安装
openclaw skill install minimax-token-plan-tool

# 或手动克隆到 skills/minimax-token-plan-tool/
```

## 能力

- Web 搜索（中英文）
- 图片理解（`understand_image`）
- Token Plan 余额查询（`remains`）

## 验证

```bash
cd skills/minimax-token-plan-tool && node minimax_token_plan_tool.js web_search "测试"
```
