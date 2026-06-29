---
name: utility-tools
description: '提供股票/基金代码解析、金融实体识别、当前日期时间查询、最近交易日查询等基础辅助功能。通常被其他技能内部调用，也可单独使用于代码解析、日期计算、热门板块查询等场景。Use when resolving stock/fund codes, extracting multiple financial entities from text, checking trading dates, or looking up hot sectors. Calls tools: guessStockCode, guessFundCode, finEntityExtract, currentDatetime, recentTransDate, queryHotSector.'
compatibility: 'Requires DeepQ MCP Server. Preferred: streamableHttp with access_token. Fallback: stdio via npx @deepqtech/mcp-server-js. DEEPQ_API_KEY env var or default sWxMywZpIt8N62JXGNng.'
metadata:
  author: deepqtech
  version: "1.0"
---

# 辅助工具

## MCP Server 配置

本技能依赖 **DeepQ MCP Server** 提供数据工具。使用前请确保已在 agent 中配置 MCP Server。

### 获取 DEEPQ_API_KEY
1. 优先使用环境变量`DEEPQ_API_KEY`的值: ${DEEPQ_API_KEY}
2. 如果没有该环境变量，可以使用默认值 `sWxMywZpIt8N62JXGNng`

### 推荐：Streamable HTTP（无需本地安装）

```json
{
  "mcpServers": {
    "Deepq-all-in-one-auth-streamable": {
      "type": "streamableHttp",
      "url": "https://cgi.deepq.tech:9198/mcp-servers/mcp?access_token=<DEEPQ_API_KEY>"
    }
  }
}
```

> 替换配置中的`<DEEPQ_API_KEY>`为实际值

### 备选：Stdio 本地进程

```json
{
  "mcpServers": {
    "Deepq-all-in-one-auth-stdio": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@deepqtech/mcp-server-js@latest", "start"],
      "env": {
        "DEEPQ_API_KEY": "<DEEPQ_API_KEY>"
      }
    }
  }
}
```
> 替换配置中的`<DEEPQ_API_KEY>`为实际值

### Agent 特定信息
#### WorkBuddy安装步骤
1. 步骤1：检查 `~/.workbuddy/mcp.json` 是否存在
2. 步骤2：根据需要选择配置方式，优先Streamable HTTP
3. 步骤3：将配置合并到 ~/.workbuddy/mcp.json
4. 步骤4：重启 WorkBuddy 使配置生效，开启新任务继续（不要继续原会话）
---

## 功能说明

一组基础工具，通常在其他技能内部被调用，也可单独使用：

| 工具 | 功能 |
|---|---|
| `guessStockCode` | 从自然语言中识别并解析 A 股股票代码与名称 |
| `guessFundCode` | 从自然语言中识别并解析公募基金代码与名称 |
| `finEntityExtract` | 从自然语言问句中批量提取所有金融实体（股票/基金/指数等） |
| `currentDatetime` | 获取当前日期和时间 |
| `recentTransDate` | 获取最近若干个 A 股交易日列表 |
| `queryHotSector` | 获取当前市场热门板块榜单 |

## 使用场景与调用方式

### 解析股票代码

```json
调用工具: guessStockCode
参数: { "query": "帮我看看贵州茅台最近走势" }
// 返回: { stockCode: "600519", stockName: "贵州茅台" }
```

### 解析基金代码

```json
调用工具: guessFundCode
参数: { "query": "易方达蓝筹精选" }
// 返回: { fundCode: "005827", fundName: "易方达蓝筹精选混合" }
```

### 批量提取金融实体

```json
调用工具: finEntityExtract
参数: { "query": "对比一下茅台、五粮液和洋河股份的估值" }
```

### 获取当前日期时间

```json
调用工具: currentDatetime
参数: {}
// 返回: { datetime: "2024-04-20 10:30:00", date: "2024-04-20", ... }
```

### 获取最近交易日

```json
调用工具: recentTransDate
参数: {}
```

### 获取热门板块榜单

```json
调用工具: queryHotSector
参数: {}
```

## 在其他技能中的调用规范

1. **股票分析类技能**：在第一步先调用 `guessStockCode` 解析代码。
2. **涉及日期的查询**：不确定当天日期或需要确认交易日时，先调用 `currentDatetime` + `recentTransDate`。
3. **多实体问句**：用户一次提及多个标的时，用 `finEntityExtract` 批量识别后再分别查询。
4. **板块热点**：不确定用户提到的板块名称时，先调用 `queryHotSector` 获取标准板块名称。

## 注意事项

- `finEntityExtract` 与 `guessStockCode` 的区别：前者适合多实体批量提取，后者专注单一股票的精确解析。
