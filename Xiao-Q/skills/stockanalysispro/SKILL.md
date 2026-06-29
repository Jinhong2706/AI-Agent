---
name: "stock-lianghuafenxi-tdx"
description: "双趋势共振量化选股系统，基于GMMA+一目均衡图+ADX+流动性过滤，输出S/A/B/C四级信号与动态止损。支持通达信本地数据和CSV数据扫描。当用户需要量化选股、趋势分析、双趋势共振扫描、股票筛选时调用此技能。"
---

# 双趋势共振量化选股系统

基于GMMA+一目均衡图+ADX+流动性过滤的三层架构量化选股系统，支持QClaw智能体调用。

## 功能特性

- ✅ GMMA顾比均线多头排列检测
- ✅ 一目均衡图云层分析（9-26-52标准参数）
- ✅ ADX趋势强度过滤（无TA-Lib依赖）
- ✅ 流动性前置过滤（默认1亿门槛）
- ✅ S/A/B/C四级信号评级
- ✅ 动态止损位计算
- ✅ 通达信本地数据扫描
- ✅ CSV数据扫描
- ✅ 批量分析支持
- ✅ 自动过滤科创板和北交所

## 系统架构

**核心逻辑**：流动性(>1亿) → ADX(>20) → 技术形态(GMMA+Ichimoku)
**输出**：S/A/B/C四级信号 + 动态止损位
**数据要求**：60日+前复权K线（OHLCV+Amount）

## API接口

### 分析单只股票

**调用方式**：
```python
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "analyze",
    "code": "600519"
})
```

**返回数据格式**：
```json
{
    "success": true,
    "data": {
        "code": "600519",
        "name": "贵州茅台",
        "signal": "A级",
        "desc": "🟢 推荐",
        "score": 80,
        "position": "10%",
        "stop_loss": 1680.50,
        "risk_pct": 3.25,
        "close": 1736.80,
        "adx": 32.5,
        "gmma_disp": "3.25%",
        "above_cloud": true,
        "tk_bull": true,
        "details": [
            "GMMA多头排列+30",
            "GMMA离散度3.25%>2%+10",
            "价格在云层上方+20",
            "转换线>基准线+15",
            "ADX=32.5 30-40中趋势+15"
        ],
        "date": "2026-04-11"
    },
    "count": 1,
    "message": "分析完成: 600519 A级"
}
```

### 批量分析多只股票

**调用方式**：
```python
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "batch_analyze",
    "codes": ["600519", "000858", "601318", "600036"]
})
```

**返回数据格式**：
```json
{
    "success": true,
    "data": [
        {"code": "600519", "signal": "A级", "score": 80, ...},
        {"code":000858", "signal": "B级", "score": 65, ...}
    ],
    "count": 2,
    "message": "批量分析完成，共 4 只股票"
}
```

### 扫描通达信本地数据

**调用方式**：
```python
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "scan_tdx",
    "tdx_path": "D:\\new_tdx",
    "max_count": 0
})
```

**返回数据格式**：
```json
{
    "success": true,
    "data": [...],
    "report": "完整文本报告",
    "count": 500,
    "scanned": 4500,
    "valid": 4200,
    "message": "扫描完成: 扫描4500只, 有效4200只"
}
```

### 扫描CSV数据目录

**调用方式**：
```python
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "scan_csv",
    "data_dir": "C:\\data\\stocks"
})
```

### 测试模式

**调用方式**：
```python
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "test"
})
```

## 评分与分级系统

### 评分规则（满分100）

| 条件 | 分值 | 说明 |
|------|------|------|
| GMMA多头排列 | +30 | 短期组>长期组 |
| GMMA离散度>2% | +10 | 确保发散非粘合 |
| 云层上方 | +20 | 价格>云层上轨 |
| 转换>基准 | +15 | 多头动能 |
| TK金叉 | +5 | 当日金叉触发 |
| 云层厚度>3% | +5 | 支撑强度 |
| ADX>40 | +20 | 强趋势 |
| ADX 30-40 | +15 | 中趋势 |
| ADX 20-30 | +10 | 弱趋势 |
| 成交额>10亿 | +5 | 流动性溢价 |

### 四级信号

- **S级(90+分)**：🔥 强烈推荐，仓位20%，立即买入
- **A级(75-89分)**：🟢 推荐，仓位10%，择机买入
- **B级(60-74分)**：🟡 观察，仓位5%，等待确认
- **C级(<60分)**：❌ 放弃，仓位0%

### 止损位计算

```python
stop_loss = max(cloud_bottom, ema_60)  # 云层下轨与60EMA取高者
risk_pct = (close - stop_loss) / close * 100
```

## 算法详解

### 流动性过滤（前置硬性）

```python
turnover_ma20 = df['amount'].rolling(20).mean()
if turnover_ma20 < 100_000_000:  # 1亿门槛
    return {"signal": "REJECT", "reason": "流动性不足"}
```

### ADX趋势强度（无TA-Lib实现）

```python
tr = pd.concat([high-low, abs(high-close.shift(1)), abs(low-close.shift(1))], axis=1).max(axis=1)
atr = tr.ewm(alpha=1/14).mean()
plus_di = 100 * (plus_dm.ewm(alpha=1/14).mean() / atr)
minus_di = 100 * (minus_dm.ewm(alpha=1/14).mean() / atr)
dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
adx = dx.ewm(alpha=1/14).mean()
```

### GMMA顾比均线

```python
short_terms = [3, 5, 8, 10, 12, 15]
long_terms = [30, 35, 40, 45, 50, 60]
gmma_bullish = (ema_15 > ema_30) & (short_avg > long_avg)
```

### 一目均衡图（9-26-52标准参数）

```python
tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
senkou_a = ((tenkan + kijun) / 2).shift(26)
senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
above_cloud = close > max(senkou_a, senkou_b)
```

## 数据格式要求

### 通达信本地数据
- 自动扫描 `vipdoc/sh/lday` 和 `vipdoc/sz/lday` 目录
- 支持 `.day` 二进制格式
- 自动过滤科创板(688)和北交所(8开头)

### CSV数据
- 文件名格式：`{股票代码}.csv`（如 `600519.csv`）
- 支持的列名：date/日期, open/开盘, high/最高, low/最低, close/收盘, volume/成交量, amount/成交额

## 使用示例

### QClaw智能体调用示例

```python
# 示例1：分析单只股票
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "analyze",
    "code": "600519"
})
if result["success"]:
    stock = result["data"]
    print(f"{stock['name']}: {stock['signal']} {stock['desc']}, 评分{stock['score']}")

# 示例2：批量分析
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "batch_analyze",
    "codes": ["600519", "000858", "601318"]
})
if result["success"]:
    for stock in result["data"]:
        if stock.get("score", 0) >= 60:
            print(f"{stock['code']} {stock['name']}: {stock['signal']} 评分{stock['score']}")

# 示例3：通达信全市场扫描
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "scan_tdx",
    "tdx_path": "D:\\new_tdx"
})
if result["success"]:
    print(result["report"])

# 示例4：自定义参数分析
result = call_skill("stock-lianghuafenxi-tdx", {
    "action": "analyze",
    "code": "600519",
    "tdx_path": "D:\\new_tdx",
    "liquidity": 500000000,
    "adx_threshold": 25
})
```

## 注意事项

1. **数据来源**：优先使用通达信本地数据，其次CSV数据
2. **数据时效**：通达信数据需要先在通达信软件中下载日线数据
3. **流动性门槛**：默认1亿，可通过 `liquidity` 参数调整
4. **ADX门槛**：默认20，可通过 `adx_threshold` 参数调整
5. **数据要求**：至少60个交易日数据才能产生有效信号
6. **风险提示**：本系统仅供量化分析参考，不构成投资建议
