from __future__ import annotations

import json
import logging
import re

import httpx

from collectors.base import BaseCollector, MarketData
from config import SINA_HQ_HEADERS

logger = logging.getLogger(__name__)

INTL_FUTURES_MAP = {
    "CHA50CFD": "富时A50期指",
    "CL": "原油主力",
    "GC": "黄金主力",
    "HG": "铜主力",
    "SI": "白银主力",
}

DOMESTIC_FUTURES_MAP = {
    "I0": "铁矿石",
    "RB0": "螺纹钢",
    "CU0": "沪铜",
    "AL0": "沪铝",
}


class FuturesCollector(BaseCollector):
    category = "期货市场"

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
            items.extend(await self._fetch_eastmoney_futures())
        except Exception as e:
            logger.error("东方财富期货采集失败: %s", e)
        if not items:
            try:
                items.extend(await self._fetch_sina_international())
            except Exception as e:
                logger.error("新浪国际期货采集失败: %s", e)
            try:
                items.extend(await self._fetch_sina_domestic())
            except Exception as e:
                logger.error("新浪国内期货采集失败: %s", e)
        return MarketData(category=self.category, items=items)

    async def _fetch_eastmoney_futures(self) -> list[dict]:
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
        params = {
            "fltt": "2",
            "fields": "f2,f3,f4,f12,f14",
            "secids": "113.A50,113.SC,113.AU,113.CU,113.AG,113.I,113.RB",
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
            logger.error("解析东方财富期货数据失败: %s", e)
        return items

    async def _fetch_sina_international(self) -> list[dict]:
        items = []
        codes_param = ",".join(f"hf_{code}" for code in INTL_FUTURES_MAP)
        url = f"https://hq.sinajs.cn/list={codes_param}"
        try:
            resp = await self.sina_client.get(url)
            resp.raise_for_status()
            text = resp.text
        except Exception as e:
            logger.error("新浪国际期货请求失败: %s", e)
            return items

        lines = text.strip().split("\n")
        for line in lines:
            code_match = re.search(r'hf_([A-Za-z0-9]+)=', line)
            if not code_match:
                continue
            code = code_match.group(1)
            name = INTL_FUTURES_MAP.get(code, code)
            match = re.search(r'="([^"]*)"', line)
            if not match or not match.group(1):
                continue
            parts = match.group(1).split(",")
            if len(parts) < 8:
                continue
            try:
                price = float(parts[0])
                prev_close = float(parts[7])
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0
                items.append({
                    "name": name,
                    "code": code,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "direction": "up" if change > 0 else "down" if change < 0 else "flat",
                })
            except (ValueError, IndexError) as e:
                logger.warning("解析国际期货 %s 失败: %s", code, e)
        return items

    async def _fetch_sina_domestic(self) -> list[dict]:
        items = []
        codes_param = ",".join(DOMESTIC_FUTURES_MAP.keys())
        url = f"https://hq.sinajs.cn/list={codes_param}"
        try:
            resp = await self.sina_client.get(url)
            resp.raise_for_status()
            text = resp.text
        except Exception as e:
            logger.error("新浪国内期货请求失败: %s", e)
            return items

        lines = text.strip().split("\n")
        for line in lines:
            code_match = re.search(r'hq_str_([A-Za-z0-9_]+)=', line)
            if not code_match:
                code_match = re.search(r'([A-Za-z0-9_]+)=', line)
            if not code_match:
                continue
            code = code_match.group(1)
            name = DOMESTIC_FUTURES_MAP.get(code, code)
            match = re.search(r'="([^"]*)"', line)
            if not match or not match.group(1):
                continue
            parts = match.group(1).split(",")
            if len(parts) < 9:
                continue
            try:
                price = float(parts[8])
                prev_close = float(parts[7])
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0
                items.append({
                    "name": name,
                    "code": code,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "direction": "up" if change > 0 else "down" if change < 0 else "flat",
                })
            except (ValueError, IndexError) as e:
                logger.warning("解析国内期货 %s 失败: %s", code, e)
        return items
