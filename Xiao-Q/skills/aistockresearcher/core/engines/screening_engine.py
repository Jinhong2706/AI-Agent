#!/usr/bin/env python3
"""Multi-factor screening engine - zero deps"""
import json, math, time
from urllib import request, error

def _mean(a):
    a = [x for x in a if x is not None]
    return sum(a) / len(a) if a else 0

def _std(a):
    a = [x for x in a if x is not None]
    if len(a) < 2: return 0
    m = _mean(a)
    return math.sqrt(sum((x - m) ** 2 for x in a) / (len(a) - 1))

class ScreeningEngine:
    FACTORS = {
        "value": {"pe": -1, "pb": -1, "ps": -1, "dy": 1},
        "growth": {"roe": 1, "profit_growth": 1, "revenue_growth": 1},
        "quality": {"debt_ratio": -1, "current_ratio": 1},
        "momentum": {"ret_1m": 1, "ret_3m": 1},
        "volatility": {"vol_1m": -1, "beta": -1},
    }

    def __init__(self): self._universe = []

    def set_universe(self, stocks): self._universe = stocks

    def _normalize(self, values, reverse=False):
        m, s = _mean(values), _std(values)
        if s == 0: return [0] * len(values)
        sign = -1 if reverse else 1
        return [sign * (v - m) / s for v in values]

    def score(self, factors=None):
        if not self._universe: return []
        use = factors or list(self.FACTORS.keys())
        stocks = self._universe
        n = len(stocks)
        scores = {i: 0.0 for i in range(n)}
        for fn in use:
            if fn not in self.FACTORS: continue
            for fk, dr in self.FACTORS[fn].items():
                vals = [s.get(fk) for s in stocks]
                valid = [(i, v) for i, v in enumerate(vals) if v is not None]
                if len(valid) < n * 0.3: continue
                zs = self._normalize([v for _, v in valid], reverse=(dr == -1))
                for (idx, _), z in zip(valid, zs): scores[idx] += z
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [{**stocks[i], "_score": round(sc, 4), "_rank": j + 1}
                for j, (i, sc) in enumerate(ranked[:min(n, 50)])]

    def fetch_eastmoney_stocks(self, page=1, size=100):
        try:
            url = f"https://push2.eastmoney.com/api/qt/clist/get?pn={page}&pz={size}&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f37,f45,f46,f100,f115"
            hdrs = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
            resp = request.urlopen(request.Request(url, headers=hdrs), timeout=15)
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            results = []
            if data and data.get("data") and data["data"].get("diff"):
                for item in data["data"]["diff"]:
                    results.append({"code": item.get("f12", ""), "name": item.get("f14", ""),
                        "price": item.get("f2"), "change_pct": item.get("f3"),
                        "pe": item.get("f9"), "pb": item.get("f23"),
                        "roe": item.get("f37"), "market_cap": item.get("f20")})
            return results
        except: return []

    def magic_formula(self):
        scored = []
        for s in self._universe:
            roc = s.get("roc") or s.get("roe", 0)
            pe = s.get("pe", 999)
            if roc > 0 and 0 < pe < 100:
                s["_magic"] = roc / pe
                scored.append(s)
        return sorted(scored, key=lambda x: x["_magic"], reverse=True)[:20]
