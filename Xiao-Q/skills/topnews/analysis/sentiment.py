from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    POSITIVE_DICT = {
        "利好": 0.8, "大涨": 0.7, "突破": 0.7, "放量": 0.6, "反弹": 0.5,
        "上涨": 0.4, "新高": 0.6, "增长": 0.4, "超预期": 0.8, "大超预期": 1.0,
        "降息": 0.7, "降准": 0.8, "刺激": 0.5, "扶持": 0.5, "支持": 0.4,
        "获批": 0.5, "签约": 0.3, "合作": 0.3, "盈利": 0.5, "增持": 0.5,
        "回购": 0.5, "流入": 0.5, "宽松": 0.6, "复苏": 0.5, "回暖": 0.4,
        "一字板": 0.9, "地天板": 0.8, "反包": 0.6, "弱转强": 0.6,
        "龙头": 0.5, "放量板": 0.5, "连板": 0.6, "涨停": 0.7,
        "业绩大增": 0.7, "订单暴增": 0.6, "产能扩张": 0.5,
    }

    NEGATIVE_DICT = {
        "利空": -0.8, "暴跌": -0.9, "跌停": -0.9, "崩盘": -1.0, "恐慌": -0.7,
        "大跌": -0.7, "破位": -0.6, "新低": -0.6, "下滑": -0.4, "不及预期": -0.8,
        "远不及预期": -1.0, "加息": -0.6, "紧缩": -0.6, "制裁": -0.7, "限制": -0.5,
        "处罚": -0.5, "违约": -0.7, "退市": -0.8, "减持": -0.5, "流出": -0.5,
        "风险": -0.5, "战争": -0.7, "冲突": -0.5, "衰退": -0.7, "危机": -0.8,
        "炸板": -0.7, "核按钮": -0.9, "天地板": -0.9, "强转弱": -0.6,
        "闷杀": -0.8, "缩量板": -0.3, "破发": -0.6, "闪崩": -0.9,
        "业绩暴雷": -0.9, "商誉减值": -0.7, "质押爆仓": -0.8,
    }

    INTENSIFIERS = {
        "大幅": 1.3, "急剧": 1.4, "猛烈": 1.4, "罕见": 1.3,
        "历史性": 1.5, "史诗级": 1.5, "前所未有": 1.5,
        "微幅": 0.6, "小幅": 0.7, "略微": 0.6,
    }

    NEGATORS = ["不", "未", "无", "非", "没有", "难以"]

    LABEL_MAP = {
        (0.3, 1.0): "乐观",
        (0.1, 0.3): "偏暖",
        (-0.1, 0.1): "中性",
        (-0.3, -0.1): "偏冷",
        (-1.0, -0.3): "悲观",
    }

    def analyze(self, text: str) -> dict:
        if not text or not text.strip():
            return {"score": 0.0, "label": "中性", "positive_hits": [], "negative_hits": []}

        positive_hits = []
        negative_hits = []

        for kw, weight in self.POSITIVE_DICT.items():
            if kw in text:
                adjusted = self._adjust_weight(kw, weight, text)
                positive_hits.append({"keyword": kw, "weight": adjusted})

        for kw, weight in self.NEGATIVE_DICT.items():
            if kw in text:
                adjusted = self._adjust_weight(kw, weight, text)
                negative_hits.append({"keyword": kw, "weight": adjusted})

        pos_sum = sum(h["weight"] for h in positive_hits)
        neg_sum = sum(abs(h["weight"]) for h in negative_hits)

        total = pos_sum + neg_sum
        if total == 0:
            score = 0.0
        else:
            score = (pos_sum - neg_sum) / total
            score = max(-1.0, min(1.0, score))

        label = self._score_to_label(score)

        return {
            "score": round(score, 2),
            "label": label,
            "positive_hits": positive_hits[:5],
            "negative_hits": negative_hits[:5],
        }

    def _adjust_weight(self, keyword: str, base_weight: float, text: str) -> float:
        weight = base_weight
        for neg in self.NEGATORS:
            idx = text.find(keyword)
            if idx > 0:
                prefix = text[max(0, idx - 2):idx]
                if neg in prefix:
                    weight = -weight * 0.6
                    return weight

        for intensifier, factor in self.INTENSIFIERS.items():
            idx = text.find(keyword)
            if idx > 0:
                prefix = text[max(0, idx - len(intensifier)):idx]
                if intensifier in prefix:
                    weight *= factor
                    break

        return weight

    def _score_to_label(self, score: float) -> str:
        for (low, high), label in self.LABEL_MAP.items():
            if low <= score < high:
                return label
        if score >= 0.3:
            return "乐观"
        if score <= -0.3:
            return "悲观"
        return "中性"

    def quick_score(self, text: str) -> float:
        result = self.analyze(text)
        return result["score"]

    def quick_label(self, text: str) -> str:
        result = self.analyze(text)
        return result["label"]
