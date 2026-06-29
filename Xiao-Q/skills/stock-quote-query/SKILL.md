---
name: stock-quote-query
description: '查询A股股票实时价格、历史行情或区间行情，支持单股和多股对比。当用户询问股票现价、历史走势、某时间段涨跌幅时触发。Use when: "XX股票现在多少钱", "XX最近一个月走势", "XX今年涨了多少". Calls tools: guessStockCode, stockLatestPrice, stockHistoryQuote, stockRangeQuote, currentDatetime, recentTransDate.'
compatibility: 'Requires DeepQ MCP Server. Preferred: streamableHttp with access_token. Fallback: stdio via npx @deepqtech/mcp-server-js. DEEPQ_API_KEY env var or default sWxMywZpIt8N62JXGNng.'
metadata:
  author: deepqtech
  version: "1.0"
---

# 股票行情查询

## MCP Server 配置

本技能依赖 **DeepQ MCP Server** 提供数据工具。使用前请确保已在 agent 中配置 MCP Server。

### 推荐：Streamable HTTP（无需本地安装）

```json
{
  "mcpServers": {
    "Deepq-all-in-one-auth-streamable": {
      "type": "streamableHttp",
      "url": "https://cgi.deepq.tech:9198/mcp-servers/mcp?access_token=sWxMywZpIt8N62JXGNng"
    }
  }
}
```

> `access_token` 优先使用环境变量 `DEEPQ_API_KEY` 的值，未设置时使用默认值 `sWxMywZpIt8N62JXGNng`。

### 备选：Stdio 本地进程

```json
{
  "mcpServers": {
    "Deepq-all-in-one-auth-stdio": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@deepqtech/mcp-server-js@latest", "start"],
      "env": {
        "DEEPQ_API_KEY": "sWxMywZpIt8N62JXGNng"
      }
    }
  }
}
```

---

## 功能说明

提供三种行情查询模式：
- **实时行情**：当前最新价、涨跌幅、成交量等
- **历史行情**：指定起止日期内的历史K线与资金数据
- **区间行情**：特定时间段的区间涨跌表现汇总

## 触发场景

- "XX 股票现在多少钱？"
- "帮我看看 XX 最近一个月的走势"
- "XX 股票今年以来涨了多少？"
- "对比一下 XX 和 YY 最近的表现"

## 执行步骤

### 第一步：解析股票代码

```json
调用工具: guessStockCode
参数: { "query": "<用户输入>" }
```

### 第二步：根据需求选择查询类型

#### 场景 A —— 实时行情

```json
调用工具: stockLatestPrice
参数: { "query": "<股票代码>" }
```

返回字段说明：当前价格、涨跌额、涨跌幅、成交量、成交额、换手率等。

#### 场景 B —— 历史行情（默认近 5 个交易日）

```json
调用工具: stockHistoryQuote
参数: {
  "query": "<股票代码>",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD"
}
```

#### 场景 C —— 区间行情汇总

```json
调用工具: stockRangeQuote
参数: {
  "query": "<股票代码>",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD"
}
```

### 第三步：获取当前日期（如需计算日期范围）

```json
调用工具: currentDatetime
参数: {}

调用工具: recentTransDate
参数: {}
```

`recentTransDate` 返回最近若干个交易日列表，便于确定有效的起止日期。

## 常用日期范围参考

| 用户表述 | startDate 参考 | endDate 参考 |
|---|---|---|
| 最近一周 | T-7 | 今天 |
| 最近一个月 | T-30 | 今天 |
| 最近三个月 | T-90 | 今天 |
| 今年以来 | 当年 1 月 1 日 | 今天 |
| 上半年 | 当年 1 月 1 日 | 当年 6 月 30 日 |

## 注意事项

- 非交易日（周末、节假日）无行情数据，日期需取最近交易日。
- 若需同时对比多只股票，对每只股票分别调用同一工具。
