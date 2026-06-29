from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SectorMapper:

    KEYWORD_SECTOR_MAP = {
        "原油": {
            "positive": ["石油石化", "煤化工", "页岩气", "油气服务"],
            "negative": ["航空运输", "化工", "塑料", "橡胶"],
        },
        "燃油": {
            "positive": ["石油石化"],
            "negative": ["航空运输", "物流"],
        },
        "黄金": {
            "positive": ["贵金属", "黄金珠宝", "有色金属"],
            "negative": [],
        },
        "白银": {
            "positive": ["贵金属", "有色金属"],
            "negative": [],
        },
        "铜": {
            "positive": ["有色金属", "电线电缆"],
            "negative": ["家电", "电力设备"],
        },
        "铝": {
            "positive": ["有色金属"],
            "negative": ["汽车", "建筑"],
        },
        "铁矿石": {
            "positive": ["钢铁"],
            "negative": [],
        },
        "螺纹钢": {
            "positive": ["钢铁", "建筑"],
            "negative": [],
        },
        "A50": {
            "positive": ["金融", "白酒", "核心资产"],
            "negative": [],
        },
        "半导体": {
            "positive": ["电子", "半导体", "芯片设计"],
            "negative": [],
        },
        "芯片": {
            "positive": ["电子", "半导体", "国产替代"],
            "negative": [],
        },
        "AI": {
            "positive": ["计算机", "人工智能", "算力", "大模型"],
            "negative": [],
        },
        "人工智能": {
            "positive": ["计算机", "人工智能", "算力", "大模型"],
            "negative": [],
        },
        "新能源": {
            "positive": ["光伏", "风电", "储能", "新能源车"],
            "negative": ["煤炭", "火电"],
        },
        "光伏": {
            "positive": ["光伏", "新能源"],
            "negative": [],
        },
        "锂": {
            "positive": ["锂电池", "新能源车"],
            "negative": [],
        },
        "房地产": {
            "positive": ["房地产", "建材", "家居"],
            "negative": [],
        },
        "降准": {
            "positive": ["银行", "券商", "房地产", "基建"],
            "negative": [],
        },
        "降息": {
            "positive": ["银行", "券商", "房地产", "高负债行业"],
            "negative": ["保险"],
        },
        "LPR": {
            "positive": ["银行", "房地产", "基建"],
            "negative": [],
        },
        "战争": {
            "positive": ["军工", "国防", "黄金", "原油"],
            "negative": ["航空", "旅游", "出口贸易"],
        },
        "制裁": {
            "positive": ["国产替代", "自主可控", "军工"],
            "negative": ["出口贸易", "跨境电商"],
        },
        "关税": {
            "positive": ["国产替代", "内需消费"],
            "negative": ["出口贸易", "跨境电商", "纺织服装"],
        },
        "人民币贬值": {
            "positive": ["出口贸易", "纺织服装", "电子代工"],
            "negative": ["航空", "造纸", "外资重仓"],
        },
        "人民币升值": {
            "positive": ["航空", "造纸", "外资重仓"],
            "negative": ["出口贸易"],
        },
        "消费": {
            "positive": ["食品饮料", "家电", "零售", "旅游"],
            "negative": [],
        },
        "医药": {
            "positive": ["医药生物", "医疗器械", "CXO"],
            "negative": [],
        },
        "军工": {
            "positive": ["国防军工", "航空航天", "船舶"],
            "negative": [],
        },
        "碳中和": {
            "positive": ["新能源", "环保", "节能"],
            "negative": ["煤炭", "钢铁", "化工"],
        },
        "数字经济": {
            "positive": ["计算机", "通信", "传媒", "数据中心"],
            "negative": [],
        },
        "新质生产力": {
            "positive": ["高端制造", "人工智能", "量子计算", "生物技术"],
            "negative": [],
        },
        "特斯拉": {
            "positive": ["新能源车", "锂电池", "汽车零部件"],
            "negative": [],
        },
        "苹果": {
            "positive": ["消费电子", "果链", "半导体"],
            "negative": [],
        },
        "美联储": {
            "positive": [],
            "negative": [],
            "note": "加息利空成长股，降息利好",
        },
    }

    TRADING_STYLE_MAP = {
        "保守型": {
            "bullish": ["低仓位持有", "加仓防御板块（公用事业/医药/高股息）"],
            "neutral": ["维持现有仓位", "观望为主"],
            "bearish": ["减仓至3成以下", "持有现金和黄金"],
        },
        "稳健型": {
            "bullish": ["主线趋势跟随", "关注量价配合的板块龙头"],
            "neutral": ["持仓不动", "关注结构性机会"],
            "bearish": ["减仓至5成", "切换至防御品种"],
        },
        "激进型": {
            "bullish": ["高标接力", "情绪博弈，关注连板股和龙头"],
            "neutral": ["精选个股短线操作", "快进快出"],
            "bearish": ["做空或空仓", "等待恐慌盘出清后抄底"],
        },
    }

    def map_sectors(self, text: str, sentiment_score: float = 0.0) -> dict:
        positive_sectors = set()
        negative_sectors = set()

        for keyword, mapping in self.KEYWORD_SECTOR_MAP.items():
            if keyword in text:
                for sector in mapping.get("positive", []):
                    positive_sectors.add(sector)
                for sector in mapping.get("negative", []):
                    negative_sectors.add(sector)

        positive_sectors = positive_sectors - negative_sectors
        negative_sectors = negative_sectors - positive_sectors

        return {
            "positive_sectors": list(positive_sectors)[:5],
            "negative_sectors": list(negative_sectors)[:5],
        }

    def get_trading_suggestions(self, verdict: str) -> dict:
        suggestions = {}
        for style, verdict_map in self.TRADING_STYLE_MAP.items():
            suggestions[style] = verdict_map.get(verdict, ["观望为主"])
        return suggestions

    def format_sector_hint(self, text: str, sentiment_score: float = 0.0) -> str:
        result = self.map_sectors(text, sentiment_score)
        parts = []
        if result["positive_sectors"]:
            parts.append("利好: " + "/".join(result["positive_sectors"][:3]))
        if result["negative_sectors"]:
            parts.append("利空: " + "/".join(result["negative_sectors"][:3]))
        return " | ".join(parts) if parts else ""
