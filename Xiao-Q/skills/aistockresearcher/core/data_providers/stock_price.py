#!/usr/bin/env python3
"""Stock quote provider - zero deps (Sina + Tencent fallback)"""
import re, json, math, time
from urllib import request, error

class StockPriceProvider:
    def __init__(self, cache_ttl=5): self._cache = {}; self._cache_ttl = cache_ttl

    def _get(self, url, timeout=8, retries=2, encoding="gbk"):
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
        for i in range(retries + 1):
            try:
                resp = request.urlopen(request.Request(url, headers=headers), timeout=timeout)
                raw = resp.read()
                if "charset=utf" in resp.headers.get("Content-Type", "").lower(): encoding = "utf-8"
                return raw.decode(encoding, errors="replace")
            except Exception as e:
                if i == retries: raise e
                time.sleep(0.3 * (i + 1))

    def _sina(self, code):
        mkt = "sh" if code.startswith(("6", "9")) else "sz"
        try:
            text = self._get(f"https://hq.sinajs.cn/list={mkt}{code}")
            m = re.search(r"\"([^\"]*)\"", text)
            if not m or not m.group(1): return None
            p = m.group(1).split(",")
            if len(p) < 33: return None
            price = float(p[3]) if p[3] else 0
            prev = float(p[2]) if p[2] else 0
            return {"code": code, "market": mkt, "source": "sina", "name": p[0],
                "open": float(p[1]) if p[1] else 0, "prev_close": prev, "price": price,
                "high": float(p[4]) if p[4] else 0, "low": float(p[5]) if p[5] else 0,
                "volume": int(float(p[8])) if p[8] else 0, "amount": float(p[9]) if p[9] else 0,
                "change": round(price - prev, 2), "change_pct": round((price / prev - 1) * 100, 2) if prev > 0 else 0}
        except: return None

    def _tencent(self, code):
        pf = "sh" if code.startswith(("6", "9")) else "sz"
        try:
            text = self._get(f"https://qt.gtimg.cn/q={pf}{code}")
            m = re.search(r"~([^~]*?);", text)
            if not m: return None
            p = m.group(1).split("~")
            if len(p) < 49: return None
            return {"code": code, "market": pf, "source": "tencent", "name": p[1],
                "price": float(p[3]) if p[3] else 0, "prev_close": float(p[4]) if p[4] else 0,
                "open": float(p[5]) if p[5] else 0, "volume": int(p[6]) if p[6] else 0,
                "high": float(p[33]) if p[33] else 0, "low": float(p[34]) if p[34] else 0,
                "amount": float(p[37]) * 10000 if p[37] else 0,
                "change": round(float(p[31]) if p[31] else 0, 2),
                "change_pct": round(float(p[32]) if p[32] else 0, 2)}
        except: return None

    def get(self, code):
        code = str(code).strip(); now = time.time()
        if code in self._cache and now - self._cache[code]["_ts"] < self._cache_ttl:
            return {k: v for k, v in self._cache[code].items() if k != "_ts"}
        r = self._sina(code) or self._tencent(code)
        if r: r["status"] = "success"; r["_ts"] = now; self._cache[code] = r; return {k: v for k, v in r.items() if k != "_ts"}
        return {"code": code, "status": "error", "msg": "failed"}

    def batch(self, codes): return [self.get(c) for c in codes]
