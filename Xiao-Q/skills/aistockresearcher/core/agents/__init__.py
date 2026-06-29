#!/usr/bin/env python3
"""7 AI Analysts - zero deps rule engine"""
import math, json

class StockAnalyst:
    def __init__(self, name, role): self.name = name; self.role = role
    def analyze(self, d): raise NotImplementedError

class FundamentalAnalyst(StockAnalyst):
    def __init__(self): super().__init__("基本面分析师", "value")
    def analyze(self, d):
        s, r = 50, []
        pe = d.get("pe", 0) or 0
        pb = d.get("pb", 0) or 0
        roe = d.get("roe", 0) or 0
        dy = d.get("dy", 0) or 0
        if 0 < pe < 15: s += 15; r.append(f"PE={pe:.1f} low")
        elif 15 <= pe < 30: s += 8; r.append(f"PE={pe:.1f} ok")
        elif pe >= 50: s -= 10; r.append(f"PE={pe:.1f} high")
        if 0 < pb < 2: s += 10; r.append(f"PB={pb:.2f} low")
        elif pb > 5: s -= 5
        if roe > 20: s += 15; r.append(f"ROE={roe:.1f}% great")
        elif roe > 10: s += 8; r.append(f"ROE={roe:.1f}% good")
        elif roe < 5: s -= 5
        if dy > 4: s += 10; r.append(f"Div={dy:.1f}% high")
        elif dy > 2: s += 5
        return {"analyst": self.name, "score": min(100, max(0, s)),
                "rating": "BUY" if s >= 70 else ("HOLD" if s >= 50 else "SELL"), "reasons": r}

class TechnicalAnalyst(StockAnalyst):
    def __init__(self): super().__init__("技术分析师", "momentum")
    def analyze(self, d):
        s, r = 50, []
        chg = d.get("change_pct", 0) or 0
        price = d.get("price", 0) or 0
        if chg > 5: s += 15; r.append(f"+{chg:.1f}% strong")
        elif chg > 2: s += 8; r.append(f"+{chg:.1f}% up")
        elif chg < -3: s -= 10; r.append(f"{chg:.1f}% weak")
        if d.get("ma5") and price > d["ma5"]: s += 5; r.append(">MA5")
        if d.get("ma20") and price > d["ma20"]: s += 5; r.append(">MA20")
        if d.get("ma60") and price > d["ma60"]: s += 5; r.append(">MA60")
        return {"analyst": self.name, "score": min(100, max(0, s)),
                "rating": "BUY" if s >= 65 else ("HOLD" if s >= 45 else "SELL"), "reasons": r}

class RiskAnalyst(StockAnalyst):
    def __init__(self): super().__init__("风险分析师", "risk")
    def analyze(self, d):
        s, r = 50, []
        beta = d.get("beta", 1) or 1
        vol = d.get("volatility", 0) or 0
        mdd = d.get("max_drawdown", 0) or 0
        if beta < 0.8: s += 15; r.append(f"Beta={beta:.2f} low")
        elif beta < 1.2: s += 8; r.append(f"Beta={beta:.2f} mid")
        else: s -= 5; r.append(f"Beta={beta:.2f} high")
        if vol < 20: s += 10; r.append(f"Vol={vol:.1f}% low")
        elif vol > 40: s -= 10; r.append(f"Vol={vol:.1f}% high")
        if mdd < 15: s += 10; r.append(f"MDD={mdd:.1f}% low")
        elif mdd > 30: s -= 10; r.append(f"MDD={mdd:.1f}% high")
        return {"analyst": self.name, "score": min(100, max(0, s)),
                "rating": "LOW" if s >= 65 else ("MID" if s >= 45 else "HIGH"), "reasons": r}

class SentimentAnalyst(StockAnalyst):
    def __init__(self): super().__init__("情绪分析师", "sentiment")
    def analyze(self, d):
        s, r = 50, []
        turnover = d.get("turnover_rate", 0) or 0
        vr = d.get("vol_ratio", 1) or 1
        chg = d.get("change_pct", 0) or 0
        if chg > 0 and vr > 1.5: s += 12; r.append("volume up")
        elif chg < 0 and vr > 1.5: s -= 8; r.append("volume down")
        elif vr < 0.5: s += 5; r.append("low vol")
        if turnover > 5: s += 10; r.append(f"turnover={turnover:.1f}%")
        elif turnover < 1: s -= 5; r.append(f"turnover={turnover:.1f}% low")
        return {"analyst": self.name, "score": min(100, max(0, s)),
                "rating": "BULL" if s >= 60 else ("NEUTRAL" if s >= 40 else "BEAR"), "reasons": r}

class GrowthAnalyst(StockAnalyst):
    def __init__(self): super().__init__("成长分析师", "growth")
    def analyze(self, d):
        s, r = 50, []
        rg = d.get("revenue_growth", 0) or 0
        pg = d.get("profit_growth", 0) or 0
        if rg > 30: s += 15; r.append(f"Rev+{rg:.1f}%")
        elif rg > 15: s += 8; r.append(f"Rev+{rg:.1f}%")
        elif rg < 0: s -= 10; r.append(f"Rev{rg:.1f}%")
        if pg > 30: s += 15; r.append(f"Profit+{pg:.1f}%")
        elif pg > 10: s += 8; r.append(f"Profit+{pg:.1f}%")
        elif pg < 0: s -= 10; r.append(f"Profit{pg:.1f}%")
        return {"analyst": self.name, "score": min(100, max(0, s)),
                "rating": "GROWTH" if s >= 70 else ("STABLE" if s >= 50 else "DECLINE"), "reasons": r}

class MacroAnalyst(StockAnalyst):
    def __init__(self): super().__init__("宏观分析师", "macro")
    def analyze(self, d):
        s, r = 50, []
        ind = d.get("industry", "") or ""
        growth = ["半导体", "新能源", "医药", "人工智能", "芯片", "光伏", "储能", "军工"]
        stable = ["银行", "保险", "电力", "交通", "公用事业", "食品饮料", "家电"]
        cyclical = ["钢铁", "煤炭", "有色", "化工", "房地产", "建材"]
        if any(k in ind for k in growth): s += 15; r.append(f"{ind} growth")
        elif any(k in ind for k in stable): s += 5; r.append(f"{ind} stable")
        elif any(k in ind for k in cyclical): s -= 5; r.append(f"{ind} cyclical")
        return {"analyst": self.name, "score": min(100, max(0, s)),
                "rating": "GOOD" if s >= 55 else ("OK" if s >= 45 else "BAD"), "reasons": r}

class ComprehensiveAnalyst(StockAnalyst):
    def __init__(self): super().__init__("综合分析师", "summary")
    def analyze(self, d):
        analysts = [FundamentalAnalyst(), TechnicalAnalyst(), RiskAnalyst(),
                    SentimentAnalyst(), GrowthAnalyst(), MacroAnalyst()]
        weights = [0.25, 0.15, 0.15, 0.15, 0.20, 0.10]
        results = []; total = 0
        for a, w in zip(analysts, weights):
            r = a.analyze(d); results.append(r); total += r["score"] * w
        total = round(total, 1)
        rating = "STRONG BUY" if total >= 70 else ("BUY" if total >= 60 else ("HOLD" if total >= 50 else ("CAUTIOUS" if total >= 40 else "AVOID")))
        return {"analyst": self.name, "final_score": total, "rating": rating,
                "sub_analyses": results,
                "buy_votes": sum(1 for r in results if "BUY" in r.get("rating", "")),
                "total_analysts": len(results)}

def analyze_stock(stock_data):
    return ComprehensiveAnalyst().analyze(stock_data)
