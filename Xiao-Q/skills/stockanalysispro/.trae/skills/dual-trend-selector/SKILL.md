---
name: "dual-trend-selector"
description: "双趋势共振量化选股系统(GMMA+Ichimoku+ADX+流动性过滤)，输出S/A/B/C四级信号与动态止损。Invoke when user asks for stock screening, quantitative selection, trend analysis, or dual-trend resonance scanning."
---

# 双趋势共振量化选股系统

基于GMMA+一目均衡图+ADX+流动性过滤的三层架构量化选股系统。

## 系统架构

**核心逻辑**：流动性(>1亿) → ADX(>20) → 技术形态(GMMA+Ichimoku)
**输出**：S/A/B/C四级信号 + 动态止损位
**数据要求**：60日+前复权K线（OHLCV+Amount）

## 算法模块详解

### 2.1 流动性过滤（前置硬性）

```python
turnover_ma20 = df['amount'].rolling(20).mean()
if turnover_ma20 < 100_000_000:  # 1亿门槛
    return {"signal": "REJECT", "reason": "流动性不足"}
```

### 2.2 ADX趋势强度（无TA-Lib实现）

```python
# True Range
tr1 = high - low
tr2 = abs(high - close.shift(1))
tr3 = abs(low - close.shift(1))
tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

# Directional Movement
plus_dm = high.diff()
minus_dm = -low.diff()
plus_dm[plus_dm < 0] = 0
minus_dm[minus_dm < 0] = 0
plus_dm[plus_dm <= minus_dm] = 0

# ADX计算
atr = tr.ewm(alpha=1/14).mean()
plus_di = 100 * (plus_dm.ewm(alpha=1/14).mean() / atr)
dx = 100 * abs(plus_di - (100*minus_dm.ewm(alpha=1/14).mean()/atr)) / (plus_di + minus_di)
adx = dx.ewm(alpha=1/14).mean()

# 过滤
if adx < 20: return "震荡市拒绝"
score = 20 if adx > 40 else (15 if adx > 30 else 10)
```

### 2.3 GMMA顾比均线

```python
short_terms = [3, 5, 8, 10, 12, 15]
long_terms = [30, 35, 40, 45, 50, 60]

for p in short_terms + long_terms:
    df[f'ema_{p}'] = df['close'].ewm(span=p, adjust=False).mean()

short_avg = df[[f'ema_{p}' for p in short_terms]].mean(axis=1)
long_avg = df[[f'ema_{p}' for p in long_terms]].mean(axis=1)
dispersion = (short_avg - long_avg) / close

# 多头排列：最快短期(15) > 最慢长期(30) 且 短期均值 > 长期均值
gmma_bullish = (ema_15 > ema_30) & (short_avg > long_avg)
```

### 2.4 一目均衡图（9-26-52标准参数）

```python
# 转换线(9)与基准线(26)
tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2

# 云层（前移26周期）
senkou_a = ((tenkan + kijun) / 2).shift(26)
senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)

# 关键判断
above_cloud = close > max(senkou_a, senkou_b)
cloud_thick = abs(senkou_a - senkou_b) / close
tk_cross = (tenkan > kijun) & (tenkan.shift(1) <= kijun.shift(1))
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

## 完整可运行代码

### dual_trend_selector.py — 核心选股引擎

```python
import pandas as pd
import numpy as np
from datetime import datetime


class DualTrendSelector:
    def __init__(self, liquidity=1e8, adx_th=20):
        self.liq_th = liquidity
        self.adx_th = adx_th
        self.gmma_s = [3, 5, 8, 10, 12, 15]
        self.gmma_l = [30, 35, 40, 45, 50, 60]

    def calc_adx(self, df, period=14):
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1 / period).mean()

        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        cond = plus_dm > minus_dm
        plus_dm[~cond] = 0

        plus_di = 100 * (plus_dm.ewm(alpha=1 / period).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1 / period).mean() / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        return dx.ewm(alpha=1 / period).mean()

    def _calc_gmma(self, df):
        for p in self.gmma_s + self.gmma_l:
            df[f'ema_{p}'] = df['close'].ewm(span=p, adjust=False).mean()
        short_cols = [f'ema_{p}' for p in self.gmma_s]
        long_cols = [f'ema_{p}' for p in self.gmma_l]
        df['gmma_s_avg'] = df[short_cols].mean(axis=1)
        df['gmma_l_avg'] = df[long_cols].mean(axis=1)
        df['gmma_disp'] = (df['gmma_s_avg'] - df['gmma_l_avg']) / df['close']
        df['gmma_bull'] = (df['ema_15'] > df['ema_30']) & (df['gmma_s_avg'] > df['gmma_l_avg'])

    def _calc_ichimoku(self, df):
        df['tenkan'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
        df['kijun'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
        df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
        df['senkou_b'] = ((df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2).shift(26)
        df['cloud_top'] = df[['senkou_a', 'senkou_b']].max(axis=1)
        df['cloud_bot'] = df[['senkou_a', 'senkou_b']].min(axis=1)
        df['above_cloud'] = df['close'] > df['cloud_top']
        df['cloud_thick'] = abs(df['senkou_a'] - df['senkou_b']) / df['close']
        df['tk_cross'] = (df['tenkan'] > df['kijun']) & (df['tenkan'].shift(1) <= df['kijun'].shift(1))
        df['tk_bull'] = df['tenkan'] > df['kijun']

    def _score(self, df):
        last = df.iloc[-1]
        score = 0
        details = []

        if last.get('gmma_bull', False):
            score += 30
            details.append("GMMA多头排列+30")
        else:
            details.append("GMMA非多头排列+0")

        if last.get('gmma_disp', 0) > 0.02:
            score += 10
            details.append(f"GMMA离散度{last['gmma_disp']:.2%}>2%+10")
        else:
            details.append(f"GMMA离散度{last.get('gmma_disp', 0):.2%}<=2%+0")

        if last.get('above_cloud', False):
            score += 20
            details.append("价格在云层上方+20")
        else:
            details.append("价格不在云层上方+0")

        if last.get('tk_bull', False):
            score += 15
            details.append("转换线>基准线+15")
        else:
            details.append("转换线<=基准线+0")

        if last.get('tk_cross', False):
            score += 5
            details.append("TK金叉触发+5")

        if last.get('cloud_thick', 0) > 0.03:
            score += 5
            details.append(f"云层厚度{last['cloud_thick']:.2%}>3%+5")
        else:
            details.append(f"云层厚度{last.get('cloud_thick', 0):.2%}<=3%+0")

        adx_val = last.get('adx', 0)
        if adx_val > 40:
            score += 20
            details.append(f"ADX={adx_val:.1f}>40强趋势+20")
        elif adx_val > 30:
            score += 15
            details.append(f"ADX={adx_val:.1f}30-40中趋势+15")
        elif adx_val > 20:
            score += 10
            details.append(f"ADX={adx_val:.1f}20-30弱趋势+10")

        if last.get('amount_ma20', 0) > 1e9:
            score += 5
            details.append(f"成交额{last['amount_ma20'] / 1e8:.2f}亿>10亿+5")

        return score, details

    @staticmethod
    def _grade(score):
        if score >= 90:
            return "S", "🔥 强烈推荐", "20%"
        elif score >= 75:
            return "A", "🟢 推荐", "10%"
        elif score >= 60:
            return "B", "🟡 观察", "5%"
        else:
            return "C", "❌ 放弃", "0%"

    def analyze(self, kline_dict):
        df = pd.DataFrame(kline_dict['kline'])
        if len(df) < 60:
            return {
                "code": kline_dict.get('code', ''),
                "name": kline_dict.get('name', ''),
                "signal": "ERROR",
                "reason": f"数据不足60日(仅{len(df)}日)"
            }

        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'amount' not in df.columns:
            df['amount'] = df['close'] * df['volume'] * 100
        else:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

        df['amount_ma20'] = df['amount'].rolling(20).mean()

        if df['amount_ma20'].iloc[-1] < self.liq_th:
            return {
                "code": kline_dict.get('code', ''),
                "name": kline_dict.get('name', ''),
                "signal": "❌ 拒绝",
                "reason": f"流动性不足({df['amount_ma20'].iloc[-1] / 1e8:.2f}亿<1亿)",
                "score": 0
            }

        df['adx'] = self.calc_adx(df)

        if df['adx'].iloc[-1] < self.adx_th:
            return {
                "code": kline_dict.get('code', ''),
                "name": kline_dict.get('name', ''),
                "signal": "❌ 拒绝",
                "reason": f"震荡市拒绝(ADX={df['adx'].iloc[-1]:.1f}<{self.adx_th})",
                "score": 0
            }

        self._calc_gmma(df)
        self._calc_ichimoku(df)

        score, details = self._score(df)
        grade, desc, pos = self._grade(score)

        last = df.iloc[-1]
        stop_loss = max(last['cloud_bot'], last['ema_60'])
        risk_pct = (last['close'] - stop_loss) / last['close'] * 100

        return {
            "code": kline_dict.get('code', ''),
            "name": kline_dict.get('name', ''),
            "signal": f"{grade}级",
            "desc": desc,
            "score": score,
            "position": pos,
            "stop_loss": round(stop_loss, 2),
            "risk_pct": round(risk_pct, 2),
            "close": round(last['close'], 2),
            "adx": round(last['adx'], 1),
            "gmma_disp": f"{last['gmma_disp']:.2%}",
            "above_cloud": bool(last['above_cloud']),
            "tk_bull": bool(last['tk_bull']),
            "details": details,
            "date": str(last.get('date', datetime.now().strftime('%Y-%m-%d')))
        }

    def batch_analyze(self, stock_list):
        results = []
        for item in stock_list:
            try:
                result = self.analyze(item)
                results.append(result)
            except Exception as e:
                results.append({
                    "code": item.get('code', ''),
                    "name": item.get('name', ''),
                    "signal": "ERROR",
                    "reason": str(e)
                })
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results

    @staticmethod
    def format_report(results):
        lines = []
        lines.append("=" * 80)
        lines.append("双趋势共振量化选股系统 — 扫描报告")
        lines.append(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"扫描数量: {len(results)}")
        lines.append("=" * 80)

        signals = {"S级": [], "A级": [], "B级": [], "C级": [], "❌ 拒绝": [], "ERROR": []}
        for r in results:
            sig = r.get('signal', 'ERROR')
            if sig in signals:
                signals[sig].append(r)
            elif "拒绝" in sig:
                signals["❌ 拒绝"].append(r)
            else:
                signals["ERROR"].append(r)

        for grade in ["S级", "A级", "B级"]:
            items = signals[grade]
            if not items:
                continue
            lines.append("")
            lines.append(f"【{grade}信号】共{len(items)}只")
            lines.append("-" * 60)
            for r in items:
                lines.append(f"  {r['code']} {r['name']}")
                lines.append(f"    信号: {r['signal']} {r['desc']} | 评分: {r['score']} | 仓位: {r['position']}")
                lines.append(f"    收盘: {r['close']} | 止损: {r['stop_loss']} | 风险: {r['risk_pct']}%")
                lines.append(f"    ADX: {r['adx']} | 离散度: {r['gmma_disp']} | 云上: {r['above_cloud']} | TK多: {r['tk_bull']}")
                for d in r.get('details', []):
                    lines.append(f"    {d}")
                lines.append("")

        reject_count = len(signals["❌ 拒绝"])
        error_count = len(signals["ERROR"])
        c_count = len(signals["C级"])
        if reject_count > 0 or c_count > 0 or error_count > 0:
            lines.append(f"【过滤统计】拒绝:{reject_count} | C级:{c_count} | 错误:{error_count}")

        lines.append("")
        lines.append("=" * 80)
        return "\n".join(lines)
```

### data_loader.py — 数据加载模块

```python
import os
import struct
import pandas as pd
import numpy as np


class TdxDataLoader:
    TDX_DAY_RECORD_SIZE = 32

    def __init__(self, tdx_path=None):
        if tdx_path is None:
            tdx_path = self._find_tdx_path()
        self.tdx_path = tdx_path
        self.vipdoc_sh = os.path.join(tdx_path, 'vipdoc', 'sh', 'lday') if tdx_path else None
        self.vipdoc_sz = os.path.join(tdx_path, 'vipdoc', 'sz', 'lday') if tdx_path else None

    @staticmethod
    def _find_tdx_path():
        common_paths = [
            r'C:\new_tdx',
            r'C:\tdx',
            r'D:\new_tdx',
            r'D:\tdx',
            r'E:\new_tdx',
            r'E:\tdx',
            r'C:\Program Files\new_tdx',
            r'D:\Program Files\new_tdx',
        ]
        for p in common_paths:
            if os.path.isdir(p):
                vipdoc = os.path.join(p, 'vipdoc')
                if os.path.isdir(vipdoc):
                    return p
        return None

    def _parse_day_file(self, filepath):
        records = []
        with open(filepath, 'rb') as f:
            data = f.read()
        record_count = len(data) // self.TDX_DAY_RECORD_SIZE
        for i in range(record_count):
            offset = i * self.TDX_DAY_RECORD_SIZE
            record = data[offset:offset + self.TDX_DAY_RECORD_SIZE]
            date_int, open_p, high_p, low_p, close_p, amount, volume, reserved = struct.unpack(
                'IIIIIfII', record
            )
            records.append({
                'date': str(date_int),
                'open': open_p / 100.0,
                'high': high_p / 100.0,
                'low': low_p / 100.0,
                'close': close_p / 100.0,
                'amount': amount,
                'volume': volume,
            })
        return records

    @staticmethod
    def _format_date(date_str):
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    def load_stock(self, code):
        if code.startswith('6') or code.startswith('9'):
            prefix = 'sh'
            vipdoc = self.vipdoc_sh
        else:
            prefix = 'sz'
            vipdoc = self.vipdoc_sz

        if vipdoc is None or not os.path.isdir(vipdoc):
            return None

        filepath = os.path.join(vipdoc, f'{prefix}{code}.day')
        if not os.path.isfile(filepath):
            return None

        records = self._parse_day_file(filepath)
        if not records:
            return None

        for r in records:
            r['date'] = self._format_date(r['date'])

        return {
            'code': code,
            'name': code,
            'kline': records
        }

    def load_stock_with_name(self, code, name_map=None):
        data = self.load_stock(code)
        if data is None:
            return None
        if name_map and code in name_map:
            data['name'] = name_map[code]
        return data

    def scan_all(self, max_count=0):
        stock_list = []
        for vipdoc, prefix in [(self.vipdoc_sh, 'sh'), (self.vipdoc_sz, 'sz')]:
            if vipdoc is None or not os.path.isdir(vipdoc):
                continue
            for fname in os.listdir(vipdoc):
                if not fname.endswith('.day'):
                    continue
                code = fname.replace(prefix, '').replace('.day', '')
                if not code.isdigit():
                    continue
                if code.startswith('688') or code.startswith('8'):
                    continue
                stock_list.append(code)
                if max_count > 0 and len(stock_list) >= max_count:
                    return stock_list
        return stock_list

    def load_name_map(self):
        name_map = {}
        for base_dir in [self.vipdoc_sh, self.vipdoc_sz]:
            if base_dir is None:
                continue
            parent = os.path.dirname(base_dir)
            for fname in os.listdir(parent):
                if fname.endswith('.txt') and 'min' not in fname.lower():
                    fpath = os.path.join(parent, fname)
                    try:
                        with open(fpath, 'r', encoding='gbk', errors='ignore') as f:
                            for line in f:
                                parts = line.strip().split('|')
                                if len(parts) >= 2:
                                    name_map[parts[0]] = parts[1]
                    except Exception:
                        pass
        return name_map


class CSVDataLoader:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir

    def load_stock(self, code):
        filepath = os.path.join(self.data_dir, f'{code}.csv')
        if not os.path.isfile(filepath):
            return None
        df = pd.read_csv(filepath)
        col_map = {}
        for col in df.columns:
            col_lower = col.strip().lower()
            if col_lower in ('date', '日期', 'trade_date'):
                col_map[col] = 'date'
            elif col_lower in ('open', '开盘', 'open_price'):
                col_map[col] = 'open'
            elif col_lower in ('high', '最高', 'high_price'):
                col_map[col] = 'high'
            elif col_lower in ('low', '最低', 'low_price'):
                col_map[col] = 'low'
            elif col_lower in ('close', '收盘', 'close_price'):
                col_map[col] = 'close'
            elif col_lower in ('volume', '成交量', 'vol'):
                col_map[col] = 'volume'
            elif col_lower in ('amount', '成交额', 'turnover'):
                col_map[col] = 'amount'
        df = df.rename(columns=col_map)
        records = df.to_dict(orient='records')
        for r in records:
            r['date'] = str(r.get('date', ''))
        return {
            'code': code,
            'name': code,
            'kline': records
        }

    def scan_all(self):
        stock_list = []
        if not os.path.isdir(self.data_dir):
            return stock_list
        for fname in os.listdir(self.data_dir):
            if fname.endswith('.csv'):
                code = fname.replace('.csv', '')
                stock_list.append(code)
        return stock_list


def generate_test_data(code='600519', name='贵州茅台', days=120, trend='bull'):
    np.random.seed(hash(code) % 2 ** 31)
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=days)
    base_price = 1800.0 if code == '600519' else 20.0

    if trend == 'bull':
        drift = 0.002
    elif trend == 'bear':
        drift = -0.001
    else:
        drift = 0.0

    returns = np.random.normal(drift, 0.02, days)
    prices = base_price * np.cumprod(1 + returns)

    kline = []
    for i, date in enumerate(dates):
        close = round(prices[i], 2)
        high = round(close * (1 + abs(np.random.normal(0, 0.01))), 2)
        low = round(close * (1 - abs(np.random.normal(0, 0.01))), 2)
        open_p = round(close * (1 + np.random.normal(0, 0.005)), 2)
        volume = int(np.random.uniform(50000, 200000))
        amount = round(close * volume * 100, 0)
        kline.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'amount': amount
        })

    return {
        'code': code,
        'name': name,
        'kline': kline
    }
```

### main.py — 主入口

```python
import argparse
import json
import sys
from datetime import datetime

from dual_trend_selector import DualTrendSelector
from data_loader import TdxDataLoader, CSVDataLoader, generate_test_data


def run_test():
    print("=" * 60)
    print("双趋势共振量化选股系统 — 测试模式")
    print("=" * 60)

    selector = DualTrendSelector()

    test_stocks = [
        generate_test_data('600519', '贵州茅台', 120, 'bull'),
        generate_test_data('000858', '五粮液', 120, 'bull'),
        generate_test_data('601318', '中国平安', 120, 'range'),
        generate_test_data('000001', '平安银行', 120, 'bear'),
        generate_test_data('600036', '招商银行', 120, 'bull'),
    ]

    results = selector.batch_analyze(test_stocks)
    report = selector.format_report(results)
    print(report)

    print("\n--- 详细JSON输出（S/A/B级）---")
    for r in results:
        if r.get('score', 0) >= 60:
            print(json.dumps(r, ensure_ascii=False, indent=2))

    return results


def run_tdx_scan(tdx_path=None, max_count=0, output_file=None):
    print("=" * 60)
    print("双趋势共振量化选股系统 — 通达信数据扫描")
    print("=" * 60)

    loader = TdxDataLoader(tdx_path)
    if loader.tdx_path is None:
        print("错误: 未找到通达信安装目录，请使用 --tdx_path 指定路径")
        print("常见路径: C:\\new_tdx, D:\\new_tdx")
        return None

    print(f"通达信路径: {loader.tdx_path}")
    codes = loader.scan_all(max_count)
    print(f"扫描股票数: {len(codes)}")

    if not codes:
        print("未找到股票数据文件")
        return None

    selector = DualTrendSelector()
    stock_list = []
    for i, code in enumerate(codes):
        if (i + 1) % 100 == 0:
            print(f"  已加载 {i + 1}/{len(codes)}...")
        data = loader.load_stock(code)
        if data is not None:
            stock_list.append(data)

    print(f"有效数据: {len(stock_list)} 只")

    results = selector.batch_analyze(stock_list)
    report = selector.format_report(results)
    print(report)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        json_file = output_file.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存: {output_file}")
        print(f"数据已保存: {json_file}")

    return results


def run_csv_scan(data_dir='data', output_file=None):
    print("=" * 60)
    print("双趋势共振量化选股系统 — CSV数据扫描")
    print("=" * 60)

    loader = CSVDataLoader(data_dir)
    codes = loader.scan_all()
    print(f"扫描股票数: {len(codes)}")

    if not codes:
        print(f"未找到CSV数据文件，请将CSV文件放入 {data_dir}/ 目录")
        return None

    selector = DualTrendSelector()
    stock_list = []
    for code in codes:
        data = loader.load_stock(code)
        if data is not None:
            stock_list.append(data)

    print(f"有效数据: {len(stock_list)} 只")

    results = selector.batch_analyze(stock_list)
    report = selector.format_report(results)
    print(report)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存: {output_file}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='双趋势共振量化选股系统 (GMMA+Ichimoku+ADX+流动性过滤)'
    )
    parser.add_argument('--mode', choices=['test', 'tdx', 'csv'], default='test',
                        help='运行模式: test=测试数据, tdx=通达信数据, csv=CSV数据')
    parser.add_argument('--tdx_path', type=str, default=None,
                        help='通达信安装路径 (如: D:\\new_tdx)')
    parser.add_argument('--max_count', type=int, default=0,
                        help='最大扫描数量 (0=全部)')
    parser.add_argument('--data_dir', type=str, default='data',
                        help='CSV数据目录 (默认: data)')
    parser.add_argument('--output', type=str, default=None,
                        help='输出报告文件名 (如: report.txt)')
    parser.add_argument('--liquidity', type=float, default=1e8,
                        help='流动性门槛 (默认: 1亿)')
    parser.add_argument('--adx_threshold', type=float, default=20,
                        help='ADX趋势强度门槛 (默认: 20)')

    args = parser.parse_args()

    if args.mode == 'test':
        run_test()
    elif args.mode == 'tdx':
        run_tdx_scan(args.tdx_path, args.max_count, args.output)
    elif args.mode == 'csv':
        run_csv_scan(args.data_dir, args.output)


if __name__ == '__main__':
    main()
```

## 使用方式

### 命令行运行

```bash
# 测试模式（内置模拟数据）
python main.py --mode test

# 通达信数据扫描
python main.py --mode tdx --tdx_path "D:\new_tdx"

# CSV数据扫描
python main.py --mode csv --data_dir data

# 完整参数
python main.py --mode tdx --tdx_path "D:\new_tdx" --max_count 500 --output report.txt --liquidity 100000000 --adx_threshold 20
```

### 编程接口调用

```python
from dual_trend_selector import DualTrendSelector

selector = DualTrendSelector(liquidity=1e8, adx_th=20)

# 单只股票分析
result = selector.analyze({
    "code": "600519",
    "name": "贵州茅台",
    "kline": [
        {"date": "2025-01-02", "open": 1800, "high": 1820, "low": 1790, "close": 1815, "volume": 50000, "amount": 9075000000},
        # ... 至少60日数据
    ]
})

# 批量分析
results = selector.batch_analyze(stock_list)
report = selector.format_report(results)
print(report)
```

### 输入数据格式

kline_dict 结构：
```json
{
    "code": "600519",
    "name": "贵州茅台",
    "kline": [
        {"date": "2025-01-02", "open": 1800.0, "high": 1820.0, "low": 1790.0, "close": 1815.0, "volume": 50000, "amount": 9075000000},
        ...
    ]
}
```

必填字段：date, open, high, low, close, volume
可选字段：amount（若无则自动按 close * volume * 100 估算）

### 输出信号格式

```json
{
    "code": "600519",
    "name": "贵州茅台",
    "signal": "S级",
    "desc": "🔥 强烈推荐",
    "score": 105,
    "position": "20%",
    "stop_loss": 1992.91,
    "risk_pct": 16.19,
    "close": 2378.03,
    "adx": 45.5,
    "gmma_disp": "11.60%",
    "above_cloud": true,
    "tk_bull": true,
    "details": ["GMMA多头排列+30", "价格在云层上方+20", ...],
    "date": "2025-04-10"
}
```

## 依赖

```
pandas>=1.5.0
numpy>=1.23.0
```
