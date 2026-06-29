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
