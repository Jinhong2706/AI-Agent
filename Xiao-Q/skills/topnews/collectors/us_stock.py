from __future__ import annotations

import json
import logging
import re

import httpx

from collectors.base import BaseCollector, MarketData
from config import SINA_HQ_HEADERS

logger = logging.getLogger(__name__)

US_INDICES = {
    ".DJI": "道琼斯",
    ".IXIC": "纳斯达克",
    ".INX": "标普500",
    "VIX": "VIX恐慌指数",
}

US_ETF_CN = {
    "KWEB": "中概互联网ETF",
    "FXI": "中国大盘ETF",
}


class USStockCollector(BaseCollector):
    category = "美股行情"

    def __init__(self):
        super().__init__()
        self.sina_client = httpx.AsyncClient(
            headers=SINA_HQ_HEADERS,
            timeout=15,
            follow_redirects=True,
        )

    async def close(self):
        await self.client.aclose()
        await self.sina_client.aclose()

    async def collect(self) -> MarketData:
        items = []
        try:
            items.extend(await self._fetch_eastmoney_us())
        except Exception as e:
            logger.error("东方财富美股采集失败: %s", e)
        if not items:
            try:
                items.extend(await self._fetch_sina_indices())
            except Exception as e:
                logger.error("新浪美股采集失败: %s", e)
        try:
            if not items:
                items.extend(await self._fetch_akshare_us())
        except Exception as e:
            logger.error("akshare美股采集失败: %s", e)
        return MarketData(category=self.category, items=items)

    async def _fetch_eastmoney_us(self) -> list[dict]:
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
        params = {
            "fltt": "2",
            "fields": "f2,f3,f4,f12,f14",
            "secids": "100.DJIA,100.NDX,100.SPX,100.VIX",
        }
        data = await self._get_json(url, params=params)
        if not data:
            return []
        items = []
        try:
            diff = data.get("data", {}).get("diff", [])
            for row in diff:
                name = row.get("f14", "")
                price = row.get("f2", 0)
                change_pct = row.get("f3", 0)
                change = row.get("f4", 0)
                if not name or price == "-":
                    continue
                items.append({
                    "name": name,
                    "code": row.get("f12", ""),
                    "price": round(float(price), 2),
                    "change": round(float(change), 2),
                    "change_pct": round(float(change_pct), 2),
                    "direction": "up" if float(change_pct) > 0 else "down" if float(change_pct) < 0 else "flat",
                })
        except Exception as e:
            logger.error("解析东方财富美股数据失败: %s", e)
        return items

    async def _fetch_sina_indices(self) -> list[dict]:
        items = []
        codes_param = ",".join(f"gb_{code.lstrip('.')}" for code in US_INDICES)
        url = f"https://hq.sinajs.cn/list={codes_param}"
        try:
            resp = await self.sina_client.get(url)
            resp.raise_for_status()
            text = resp.text
        except Exception as e:
            logger.error("新浪行情请求失败: %s", e)
            return items

        lines = text.strip().split("\n")
        for line in lines:
            code_match = re.search(r'gb_([A-Za-z0-9.]+)=', line)
            if not code_match:
                continue
            code_raw = code_match.group(1)
            name = US_INDICES.get(f".{code_raw}", US_INDICES.get(code_raw, code_raw))
            match = re.search(r'="([^"]*)"', line)
            if not match or not match.group(1):
                continue
            parts = match.group(1).split(",")
            if len(parts) < 3:
                continue
            try:
                price = float(parts[1])
                prev_close = float(parts[2])
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0
                items.append({
                    "name": name,
                    "code": code_raw,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "direction": "up" if change > 0 else "down" if change < 0 else "flat",
                })
            except (ValueError, IndexError) as e:
                logger.warning("解析美股指数 %s 失败: %s", code_raw, e)
        return items

    async def _fetch_akshare_us(self) -> list[dict]:
        try:
            import akshare as ak
            df = ak.index_us_stock_sina()
            if df is None or df.empty:
                return []
            items = []
            target_names = {"道琼斯", "纳斯达克", "标普500"}
            for _, row in df.iterrows():
                name = str(row.get("名称", ""))
                if name not in target_names:
                    continue
                items.append({
                    "name": name,
                    "code": "",
                    "price": round(float(row.get("最新价", 0)), 2),
                    "change": round(float(row.get("涨跌额", 0)), 2),
                    "change_pct": round(float(row.get("涨跌幅", 0)), 2),
                    "direction": "up" if float(row.get("涨跌幅", 0)) > 0 else "down" if float(row.get("涨跌幅", 0)) < 0 else "flat",
                })
            return items
        except Exception as e:
            logger.error("akshare美股采集失败: %s", e)
            return []
