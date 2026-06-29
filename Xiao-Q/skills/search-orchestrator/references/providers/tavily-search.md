# 配置 Tavily AI Search

## 获取 API Key

1. 访问 [Tavily 官网](https://tavily.com)
2. 注册并获取 API Key
3. 免费 tier 每月 1000 次

## 环境变量

```bash
export TAVILY_API_KEY="tvly-..."
```

推荐写入 `~/.openclaw/.env` 持久化。

## 安装 Skill

```bash
# 从 ClawHub 安装
openclaw skill install tavily-search

# 或手动克隆到 skills/tavily-search/
```

## 能力

- AI 优化的搜索结果（结构化、高相关性）
- 深度搜索模式（`--deep`）
- 新闻主题过滤（`--topic news`）
- URL 内容提取（`node scripts/extract.mjs "url"`）

## 验证

```bash
cd skills/tavily-search && node scripts/search.mjs "test" -n 1
```
