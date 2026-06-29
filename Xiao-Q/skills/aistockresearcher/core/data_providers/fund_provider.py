#!/usr/bin/env python3
"""Fund provider - zero deps (Tiantian Fund API)"""
import json, math, time, re
from urllib import request, error

class FundProvider:
    def __init__(self): self._cache = {}

    def _get_json(self, url, timeout=10, retries=2):
        hdrs = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
        for i in range(retries + 1):
            try:
                resp = request.urlopen(request.Request(url, headers=hdrs), timeout=timeout)
                return json.loads(resp.read().decode("utf-8", errors="replace"))
            except Exception as e:
                if i == retries: raise e
                time.sleep(0.5 * (i + 1))

    def realtime(self, code):
        try:
            url = f"https://fundgz.1234567.com.cn/js/{code}.js"
            resp = request.urlopen(request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}), timeout=8)
            text = resp.read().decode("utf-8", errors="replace")
            m = re.search(r"jsonpgz\((.*?)\)", text, re.S)
            if m:
                d = json.loads(m.group(1))
                return {"code": d.get("fundcode", code), "name": d.get("name", ""),
                    "net_value": float(d.get("dwjz", 0) or 0), "est_value": float(d.get("gsz", 0) or 0),
                    "est_pct": float(d.get("gszzl", 0) or 0), "date": d.get("jzrq", ""), "status": "success"}
        except: pass
        return {"code": code, "status": "error"}

    def history(self, code, days=30):
        try:
            data = self._get_json(f"https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize={days}")
            records = []
            if data and data.get("Data") and data["Data"].get("LSJZList"):
                for item in data["Data"]["LSJZList"]:
                    records.append({"date": item.get("FSRQ", ""), "nav": float(item.get("DWJZ", 0) or 0),
                        "acc_nav": float(item.get("LJJZ", 0) or 0), "change_pct": item.get("JZZZL", "0")})
            return {"code": code, "status": "success", "data": records}
        except: return {"code": code, "status": "error"}

    def search(self, keyword):
        try:
            url = f"https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?callback=jQuery&m=1&key={keyword}"
            resp = request.urlopen(request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}), timeout=8)
            text = resp.read().decode("utf-8", errors="replace")
            m = re.search(r"jQuery\((.*)\)", text, re.S)
            if m: return {"status": "success", "data": [{"code": d.get("CODE", ""), "name": d.get("NAME", ""),
                "type": d.get("CATEGORYDESC", ""), "pinyin": d.get("PINYIN", "")} for d in json.loads(m.group(1)).get("Datas", [])]}
        except: pass
        return {"status": "error"}
