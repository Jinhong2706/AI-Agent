from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta

from collectors.base import BaseCollector, MarketData
from analysis.sentiment import SentimentAnalyzer

logger = logging.getLogger(__name__)

_sentiment_analyzer = SentimentAnalyzer()

MACRO_KEYWORDS = [
    "央行", "LPR", "MLF", "逆回购", "降准", "降息", "GDP", "CPI", "PPI",
    "PMI", "社融", "M2", "财政", "国债", "地方债", "汇率", "人民币",
    "国务院", "发改委", "证监会", "银保监", "金稳委", "政治局",
]

INTERNATIONAL_KEYWORDS = [
    "美联储", "鲍威尔", "非农", "通胀", "关税", "贸易", "制裁",
    "地缘", "冲突", "战争", "OPEC", "原油", "北约", "G7", "G20",
    "拜登", "特朗普", "中美", "中欧", "脱钩", "芯片",
]


class MacroNewsCollector(BaseCollector):
    category = "宏观与国际"

    async def collect(self) -> MarketData:
        items = []
        try:
            items.extend(await self._fetch_eastmoney_macro())
        except Exception as e:
            logger.error("东方财富宏观新闻采集失败: %s", e)
        try:
            items.extend(await self._fetch_sina_finance())
        except Exception as e:
            logger.error("新浪财经新闻采集失败: %s", e)
        return MarketData(category=self.category, items=items)

    async def _fetch_eastmoney_macro(self) -> list[dict]:
        url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
        params = {
            "client": "web",
            "biz": "web_news_col",
            "column": "350",
            "order": "1",
            "needInteractData": "0",
            "page_index": "1",
            "page_size": "30",
            "req_trace": str(int(datetime.now().timestamp() * 1000)),
        }
        data = await self._get_json(url, params=params)
        if not data:
            return []
        items = []
        try:
            news_list = data.get("data", {}).get("list", [])
            cutoff = datetime.now() - timedelta(hours=24)
            for news in news_list[:30]:
                title = news.get("title", "").strip()
                if not title:
                    continue
                content = news.get("summary", news.get("content", "")).strip()
                pub_time = news.get("showTime", news.get("show_time", ""))
                time_str = str(pub_time) if pub_time else ""
                
                # 时间过滤
                try:
                    if isinstance(pub_time, (int, float)) and pub_time > 0:
                        pub_time_obj = datetime.fromtimestamp(pub_time / 1000 if pub_time > 1e10 else pub_time)
                        if pub_time_obj < cutoff:
                            continue
                    elif isinstance(pub_time, str):
                        # 处理不同格式的时间字符串
                        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%m-%d %H:%M"]:
                            try:
                                pub_time_obj = datetime.strptime(pub_time, fmt)
                                if fmt == "%m-%d %H:%M":
                                    pub_time_obj = pub_time_obj.replace(year=datetime.now().year)
                                    if pub_time_obj > datetime.now():
                                        pub_time_obj = pub_time_obj.replace(year=datetime.now().year - 1)
                                if pub_time_obj < cutoff:
                                    continue
                                break
                            except ValueError:
                                continue
                except Exception:
                    pass
                
                sent = _sentiment_analyzer.analyze(title + " " + content)
                category = self._classify_category(title + " " + content)
                items.append({
                    "title": title,
                    "content": content[:200],
                    "time": time_str,
                    "source": "东方财富",
                    "sentiment": self._score_to_label(sent["score"]),
                    "sentiment_score": sent["score"],
                    "sentiment_label": sent["label"],
                    "sub_category": category,
                })
        except Exception as e:
            logger.error("解析东方财富宏观新闻失败: %s", e)
        return items

    async def _fetch_sina_finance(self) -> list[dict]:
        url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {
            "pageid": "153",
            "lid": "2516",
            "k": "",
            "num": "30",
            "page": "1",
        }
        data = await self._get_json(url, params=params)
        if not data:
            return []
        items = []
        try:
            news_list = data.get("result", {}).get("data", [])
            cutoff = datetime.now() - timedelta(hours=24)
            for news in news_list[:30]:
                title = news.get("title", "").strip()
                if not title:
                    continue
                content = news.get("digest", news.get("intro", "")).strip()
                ctime = news.get("ctime", "")
                try:
                    ctime_num = float(ctime) if ctime else 0
                except (ValueError, TypeError):
                    ctime_num = 0
                if ctime_num > 0:
                    try:
                        pub_time = datetime.fromtimestamp(ctime_num)
                        if pub_time < cutoff:
                            continue
                        time_str = pub_time.strftime("%m-%d %H:%M")
                    except Exception:
                        time_str = str(ctime)
                else:
                    time_str = str(ctime) if ctime else ""
                    # 尝试从时间字符串解析
                    try:
                        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%m-%d %H:%M"]:
                            try:
                                pub_time_obj = datetime.strptime(time_str, fmt)
                                if fmt == "%m-%d %H:%M":
                                    pub_time_obj = pub_time_obj.replace(year=datetime.now().year)
                                    if pub_time_obj > datetime.now():
                                        pub_time_obj = pub_time_obj.replace(year=datetime.now().year - 1)
                                if pub_time_obj < cutoff:
                                    continue
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                
                sent = _sentiment_analyzer.analyze(title + " " + content)
                category = self._classify_category(title + " " + content)
                items.append({
                    "title": title,
                    "content": content[:200],
                    "time": time_str,
                    "source": "新浪财经",
                    "sentiment": self._score_to_label(sent["score"]),
                    "sentiment_score": sent["score"],
                    "sentiment_label": sent["label"],
                    "sub_category": category,
                })
        except Exception as e:
            logger.error("解析新浪财经新闻失败: %s", e)
        return items

    def _score_to_label(self, score: float) -> str:
        if score >= 0.1:
            return "positive"
        elif score <= -0.1:
            return "negative"
        return "neutral"

    def _classify_category(self, text: str) -> str:
        macro_count = sum(1 for kw in MACRO_KEYWORDS if kw in text)
        intl_count = sum(1 for kw in INTERNATIONAL_KEYWORDS if kw in text)
        if macro_count >= intl_count and macro_count > 0:
            return "宏观政策"
        elif intl_count > 0:
            return "国际要闻"
        return "其他"
