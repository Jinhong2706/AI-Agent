from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class ImportanceEvaluator:

    EVENT_TIER = {
        "战争": 5.0, "军事行动": 5.0, "冲突升级": 4.5, "制裁加码": 4.5,
        "航道封锁": 5.0, "霍尔木兹": 5.0, "地缘冲突": 4.5,
        "伊朗": 4.5, "以色列": 4.0, "中东": 4.0, "俄乌": 4.5,
        "降准": 5.0, "降息": 5.0, "LPR": 4.5, "MLF": 4.0, "逆回购": 3.5,
        "美联储": 4.5, "鲍威尔": 4.0, "非农": 4.0, "加息": 4.5,
        "国务院": 4.5, "政治局": 4.5, "中央经济": 4.5,
        "GDP": 4.0, "CPI": 3.5, "PPI": 3.5, "PMI": 3.5,
        "社融": 4.0, "M2": 3.5, "进出口": 3.5,
        "新质生产力": 4.0, "人工智能": 3.5, "AI": 3.5, "芯片": 3.5,
        "新能源": 3.0, "碳中和": 3.0, "数字经济": 3.0,
        "原油": 3.5, "黄金": 3.0, "铁矿石": 2.5, "铜": 2.5,
        "北向": 3.0, "融资融券": 2.5, "龙虎榜": 3.0,
        "超预期": 4.0, "不及预期": 4.0, "大超预期": 4.5, "远不及预期": 4.5,
        "重组": 3.5, "并购": 3.0, "借壳": 3.5, "IPO": 3.0,
        "涨停": 3.0, "跌停": 3.5, "一字板": 3.0, "炸板": 3.0,
        "退市": 4.0, "ST": 3.0, "暴雷": 4.0,
    }

    SOURCE_WEIGHT = {
        "国务院": 5.0, "央行": 5.0, "政治局": 5.0, "发改委": 4.5,
        "证监会": 4.0, "财政部": 4.0, "银保监": 4.0, "工信部": 3.5,
        "商务部": 3.5, "交通运输部": 3.0,
        "财联社": 3.5, "东方财富": 3.0, "新浪财经": 3.0, "证券时报": 3.0,
        "券商": 2.5, "公司公告": 2.0,
    }

    URGENCY_KEYWORDS = {
        "已发生": 1.0,
        "突破": 1.2, "创": 1.1, "首次": 1.2, "历史": 1.3,
        "紧急": 1.5, "突发": 1.5, "刚刚": 1.3, "立即": 1.4,
        "即将": 1.3, "预计": 0.9, "可能": 0.8, "传闻": 0.7,
    }

    def evaluate(self, item: dict) -> dict:
        text = item.get("title", "") + " " + item.get("content", "")
        source = item.get("source", "")
        time_str = item.get("time", "")
        sentiment_score = item.get("sentiment_score", 0.0)

        event_score = self._calc_event_score(text)
        source_score = self._calc_source_score(source)
        urgency_score = self._calc_urgency_score(text)
        recency_score = self._calc_recency_score(time_str)
        sentiment_magnitude = abs(sentiment_score)

        importance = (
            event_score * 0.8
            + source_score * 0.4
            + urgency_score * 0.4
            + recency_score * 0.3
            + sentiment_magnitude * 1.0
        )
        importance = max(1.0, min(10.0, importance))

        if importance >= 8:
            level = "高影响"
            level_desc = "改变趋势/引发变盘"
            action_hint = "立即调整仓位"
        elif importance >= 5:
            level = "中影响"
            level_desc = "板块/个股机会"
            action_hint = "精选标的参与"
        else:
            level = "低影响"
            level_desc = "噪音/短期波动"
            action_hint = "忽略或套利"

        return {
            "importance": round(importance, 1),
            "level": level,
            "level_desc": level_desc,
            "action_hint": action_hint,
            "event_score": round(event_score, 2),
            "source_score": round(source_score, 2),
            "urgency_score": round(urgency_score, 2),
            "recency_score": round(recency_score, 2),
        }

    def _calc_event_score(self, text: str) -> float:
        max_score = 0.0
        for kw, weight in self.EVENT_TIER.items():
            if kw in text:
                max_score = max(max_score, weight)
        if max_score == 0:
            return 2.0
        return max_score

    def _calc_source_score(self, source: str) -> float:
        for key, weight in self.SOURCE_WEIGHT.items():
            if key in source:
                return weight
        return 2.0

    def _calc_urgency_score(self, text: str) -> float:
        score = 1.0
        for kw, factor in self.URGENCY_KEYWORDS.items():
            if kw in text:
                score = max(score, factor)
        return score

    def _calc_recency_score(self, time_str: str) -> float:
        if not time_str or len(time_str) < 5:
            return 3.0
        try:
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m-%d %H:%M", "%Y/%m/%d %H:%M"]:
                try:
                    pub_time = datetime.strptime(time_str, fmt)
                    if fmt == "%m-%d %H:%M":
                        pub_time = pub_time.replace(year=datetime.now().year)
                        if pub_time > datetime.now():
                            pub_time = pub_time.replace(year=datetime.now().year - 1)
                    hours = (datetime.now() - pub_time).total_seconds() / 3600
                    if hours <= 2:
                        return 5.0
                    elif hours <= 6:
                        return 4.0
                    elif hours <= 12:
                        return 3.0
                    elif hours <= 24:
                        return 2.0
                    else:
                        return 1.0
                except ValueError:
                    continue
        except Exception:
            pass
        return 3.0
