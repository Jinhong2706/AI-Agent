from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from collectors.base import BaseCollector, MarketData

logger = logging.getLogger(__name__)


class CapitalFlowCollector(BaseCollector):
    category = "资金面"

    async def collect(self) -> MarketData:
        items = []
        try:
            items.extend(await self._fetch_north_bound())
        except Exception as e:
            logger.error("北向资金采集失败: %s", e)
        try:
            items.extend(await self._fetch_margin_trading())
        except Exception as e:
            logger.error("融资融券采集失败: %s", e)
        return MarketData(category=self.category, items=items)

    async def _fetch_north_bound(self) -> list[dict]:
        try:
            import akshare as ak
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向")
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                items = [{
                    "name": "北向资金",
                    "value": round(float(latest.get("当日净流入", latest.iloc[-1])), 2),
                    "unit": "亿元",
                    "date": str(latest.get("日期", latest.iloc[0]))[:10],
                    "direction": "up" if float(latest.get("当日净流入", latest.iloc[-1])) > 0 else "down",
                }]
                return items
        except ImportError:
            logger.warning("akshare未安装，使用备用数据源")
        except Exception as e:
            logger.warning("akshare北向资金获取失败: %s, 尝试备用", e)

        return await self._fetch_north_bound_eastmoney()

    async def _fetch_north_bound_eastmoney(self) -> list[dict]:
        url = "https://push2his.eastmoney.com/api/qt/kamt.kline/get"
        params = {
            "fields1": "f1,f3",
            "fields2": "f51,f52,f53,f54,f55,f56",
            "klt": "101",
            "lmt": "1",
            "ut": "b955e6154c27a7de8ee4dc42d7ba41cc",
        }
        data = await self._get_json(url, params=params)
        if not data:
            return []
        items = []
        try:
            klines = data.get("data", {}).get("s2n", [])
            if klines:
                latest = klines[-1]
                parts = latest.split(",")
                if len(parts) >= 3:
                    net_flow = float(parts[1])
                    items.append({
                        "name": "北向资金(沪股通+深股通)",
                        "value": round(net_flow / 10000, 2),
                        "unit": "亿元",
                        "date": parts[0],
                        "direction": "up" if net_flow > 0 else "down",
                    })
        except Exception as e:
            logger.error("解析东方财富北向资金失败: %s", e)
        return items

    async def _fetch_margin_trading(self) -> list[dict]:
        try:
            import akshare as ak
            df = ak.stock_margin_underlying_info_sz_sh(date=datetime.now().strftime("%Y%m%d"))
            if df is not None and not df.empty:
                total_buy = df.get("融资买入额(元)", pd.Series([0])).sum()
                items = [{
                    "name": "融资买入额(合计)",
                    "value": round(total_buy / 1e8, 2),
                    "unit": "亿元",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "direction": "flat",
                }]
                return items
        except Exception:
            pass
        return []
