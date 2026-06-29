from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta

from collectors.base import BaseCollector, MarketData
from analysis.sentiment import SentimentAnalyzer

logger = logging.getLogger(__name__)

_sentiment_analyzer = SentimentAnalyzer()


class CLSNewsCollector(BaseCollector):
    category = "财联社新闻"

    async def collect(self) -> MarketData:
        items = []
        try:
            items.extend(await self._fetch_cls_roll())
        except Exception as e:
            logger.error("财联社电报采集失败: %s", e)
        if not items:
            try:
                items.extend(await self._fetch_eastmoney_live())
            except Exception as e:
                logger.error("东方财富7x24采集失败: %s", e)
        return MarketData(category=self.category, items=items)

    async def _fetch_cls_roll(self) -> list[dict]:
        url = "https://www.cls.cn/nodeapi/telegraphList"
        params = {
            "app": "CailianpressWeb",
            "os": "web",
            "sv": "8.4.6",
            "rn": "50",
        }
        data = await self._get_json(url, params=params)
        if not data or not isinstance(data, dict):
            return []
        items = []
        try:
            news_list = data.get("data", {}).get("roll_data", [])
            cutoff = datetime.now() - timedelta(hours=24)
            for news in news_list:
                ts = news.get("ctime", news.get("publish_time", 0))
                if isinstance(ts, (int, float)) and ts > 0:
                    pub_time = datetime.fromtimestamp(ts)
                    if pub_time < cutoff:
                        continue
                    time_str = pub_time.strftime("%m-%d %H:%M")
                else:
                    time_str = str(ts)[:16] if ts else ""

                title = news.get("title", "").strip()
                content = news.get("content", news.get("brief", "")).strip()
                brief = news.get("brief", "").strip()
                if not title and not content and not brief:
                    continue
                display_title = title or brief or content[:50]
                full_text = display_title + " " + (content or "")
                sent = _sentiment_analyzer.analyze(full_text)
                items.append({
                    "title": display_title,
                    "content": (content or brief)[:200],
                    "time": time_str,
                    "source": "财联社",
                    "sentiment": self._score_to_label(sent["score"]),
                    "sentiment_score": sent["score"],
                    "sentiment_label": sent["label"],
                })
        except Exception as e:
            logger.error("解析财联社数据失败: %s", e)
        return items

    async def _fetch_eastmoney_live(self) -> list[dict]:
        url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
        params = {
            "client": "web",
            "biz": "web_news_col",
            "column": "350",
            "order": "1",
            "needInteractData": "0",
            "page_index": "1",
            "page_size": "20",
            "req_trace": str(int(datetime.now().timestamp() * 1000)),
        }
        data = await self._get_json(url, params=params)
        if not data:
            return []
        items = []
        try:
            news_list = data.get("data", {}).get("list", [])
            for news in news_list[:20]:
                title = news.get("title", "").strip()
                if not title:
                    continue
                content = news.get("summary", news.get("content", "")).strip()
                pub_time = news.get("showTime", news.get("show_time", ""))
                full_text = title + " " + content
                sent = _sentiment_analyzer.analyze(full_text)
                items.append({
                    "title": title,
                    "content": content[:200],
                    "time": str(pub_time) if pub_time else "",
                    "source": "东方财富7x24",
                    "sentiment": self._score_to_label(sent["score"]),
                    "sentiment_score": sent["score"],
                    "sentiment_label": sent["label"],
                })
        except Exception as e:
            logger.error("解析东方财富7x24数据失败: %s", e)
        return items

    def _score_to_label(self, score: float) -> str:
        if score >= 0.1:
            return "positive"
        elif score <= -0.1:
            return "negative"
        return "neutral"
