#!/usr/bin/env python3
"""Skill manager - zero deps risk metrics"""
import math, time, json
from urllib import request, error

def _mean(a):
    a = [x for x in a if x is not None]
    return sum(a) / len(a) if a else 0

def _std(a):
    a = [x for x in a if x is not None]
    if len(a) < 2: return 0
    m = _mean(a)
    return math.sqrt(sum((x - m) ** 2 for x in a) / (len(a) - 1))

class SkillManager:
    def __init__(self): self._health = {}

    def health_check(self):
        tests = {
            "sina": ("https://hq.sinajs.cn/list=sh600519", {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}),
            "tencent": ("https://qt.gtimg.cn/q=sh600519", {"User-Agent": "Mozilla/5.0"}),
            "fund": ("https://fundgz.1234567.com.cn/js/000001.js", {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}),
        }
        results = {}
        for name, (url, hdrs) in tests.items():
            try:
                resp = request.urlopen(request.Request(url, headers=hdrs), timeout=5)
                results[name] = "ok" if resp.status == 200 else "fail"
            except: results[name] = "fail"
        self._health = results
        return results

    def risk_metrics(self, returns):
        if not returns: return {}
        r = [x for x in returns if x is not None]
        if not r: return {}
        ann_ret = _mean(r) * 252
        ann_vol = _std(r) * math.sqrt(252)
        excess = [x - 2.5 / 252 for x in r]
        sr = round(_mean(excess) / _std(excess) * math.sqrt(252), 2) if _std(excess) > 0 else 0
        nav = [1.0]
        for x in r: nav.append(nav[-1] * (1 + x / 100))
        peak = nav[0]; mdd = 0
        for n in nav:
            if n > peak: peak = n
            dd = (n - peak) / peak
            if dd < mdd: mdd = dd
        mdd = round(abs(mdd) * 100, 2)
        rs = sorted(r)
        var95 = rs[int(len(rs) * 0.05)] if len(rs) > 1 else 0
        wr = round(sum(1 for x in r if x > 0) / len(r) * 100, 1)
        return {"annual_return": round(ann_ret, 2), "annual_volatility": round(ann_vol, 2),
                "sharpe_ratio": sr, "max_drawdown": mdd, "var_95": round(var95, 2),
                "calmar_ratio": round(ann_ret / mdd, 2) if mdd > 0 else 0,
                "win_rate": wr, "total_days": len(r)}

    def portfolio_weights(self, returns_matrix, method="equal_weight"):
        n = len(returns_matrix)
        if n == 0: return []
        if method == "min_variance":
            vols = [_std(rt) for rt in returns_matrix]
            inv = [1 / v if v > 0 else 1 for v in vols]
            t = sum(inv)
            return [i / t for i in inv] if t > 0 else [1.0 / n] * n
        if method == "max_sharpe":
            def _sr(rt):
                e = [x - 2.5 / 252 for x in rt]
                s = _std(e)
                return _mean(e) / s * math.sqrt(252) if s > 0 else 0
            ss = [_sr(rt) for rt in returns_matrix]
            adj = [max(0.01, s - min(ss) + 0.5) for s in ss]
            t = sum(adj)
            return [a / t for a in adj] if t > 0 else [1.0 / n] * n
        return [1.0 / n] * n
