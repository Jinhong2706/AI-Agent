#!/usr/bin/env python3
"""AkShare provider - optional, auto fallback to East Money"""
import json, time, re, math
from urllib import request, error

_HAS_AK = None
def _check_ak():
    global _HAS_AK
    if _HAS_AK is None:
        try:
            import akshare
            _HAS_AK = True
        except: _HAS_AK = False
    return _HAS_AK

class AkShareProvider:
    def __init__(self): self._has_ak = _check_ak()

    def stock_daily(self, code):
        if self._has_ak:
            try:
                import akshare as ak
                mk = "sh" if code.startswith(("6", "9")) else "sz"
                df = ak.stock_zh_a_hist(symbol=f"{mk}{code}", period="daily",
                    start_date="20240101", end_date=time.strftime("%Y%m%d"), adjust="qfq")
                return [{"date": str(r["日期"]), "open": r["开盘"], "close": r["收盘"],
                    "high": r["最高"], "low": r["最低"], "volume": r["成交量"],
                    "change_pct": r["涨跌幅"]} for _, r in df.iterrows()]
            except: pass
        return self._fallback(code)

    def _fallback(self, code):
        try:
            mkt = "1" if code.startswith(("6", "9")) else "0"
            url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={mkt}.{code}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=365"
            hdrs = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}
            resp = request.urlopen(request.Request(url, headers=hdrs), timeout=15)
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            results = []
            if data and data.get("data") and data["data"].get("klines"):
                for line in data["data"]["klines"]:
                    p = line.split(",")
                    if len(p) >= 11:
                        results.append({"date": p[0], "open": float(p[1]), "close": float(p[2]),
                            "high": float(p[3]), "low": float(p[4]), "volume": int(p[5]),
                            "amount": float(p[6]), "change_pct": float(p[8]) if p[8] else 0})
            return results
        except: return []

    def fund_info(self, code):
        try:
            url = f"https://fundgz.1234567.com.cn/js/{code}.js"
            resp = request.urlopen(request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}), timeout=8)
            text = resp.read().decode("utf-8", errors="replace")
            m = re.search(r"jsonpgz\((.*?)\)", text, re.S)
            if m: return json.loads(m.group(1))
        except: pass
        return {}
