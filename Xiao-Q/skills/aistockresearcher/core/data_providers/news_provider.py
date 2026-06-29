#!/usr/bin/env python3
import json, time, re
from urllib import request, error

FILTER_KW = ["私募", "ETF龙虎榜", "资金净流入", "融资融券", "大宗交易"]

class NewsProvider:
    def __init__(self):
        self._cache = {}
        self._ttl = 300

    def _get_json(self, url, timeout=10):
        hdrs = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
        resp = request.urlopen(request.Request(url, headers=hdrs), timeout=timeout)
        return json.loads(resp.read().decode("utf-8", errors="replace"))

    def _ok(self, title):
        for kw in FILTER_KW:
            if kw in title:
                return False
        return True

    def get_fund_news(self, page=1, size=20):
        ck = "fn_" + str(page) + "_" + str(size)
        now = time.time()
        if ck in self._cache and now - self._cache[ck]["_ts"] < self._ttl:
            return self._cache[ck]["data"]
        try:
            url = "https://fund.eastmoney.com/api/News/NewsList?pageIndex=" + str(page) + "&pageSize=" + str(size) + "&column=jjxw"
            data = self._get_json(url)
            results = []
            if data and data.get("Data") and data["Data"].get("List"):
                for item in data["Data"]["List"]:
                    t = item.get("Title", "")
                    if self._ok(t):
                        results.append({
                            "title": t,
                            "url": "https://fund.eastmoney.com/a/" + item.get("Url", ""),
                            "source": item.get("Source", ""),
                            "date": (item.get("ShowDate", "") or "")[:10],
                            "summary": item.get("Summary", "")
                        })
            self._cache[ck] = {"data": results, "_ts": now}
            return results
        except:
            return []

    def search_news(self, keyword, days=7):
        try:
            url = "https://searchapi.eastmoney.com/bussiness/Web/GetCMSSearchResult?type=8196&pageindex=1&pagesize=50&keyword=" + keyword + "&name=zixun"
            data = self._get_json(url)
            results = []
            if data and data.get("Data"):
                for item in data["Data"]:
                    t = item.get("Title", "")
                    if self._ok(t):
                        results.append({
                            "title": t,
                            "url": item.get("Url", ""),
                            "date": (item.get("ShowDate", "") or "")[:10],
                            "source": item.get("SourceName", "")
                        })
            return results
        except:
            return []
