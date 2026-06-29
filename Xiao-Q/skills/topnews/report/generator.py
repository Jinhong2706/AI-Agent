from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from analysis.importance import ImportanceEvaluator
from analysis.sector import SectorMapper

logger = logging.getLogger(__name__)

ARROW = {"up": "📈", "down": "📉", "flat": "➡️"}
SENTIMENT_ICON = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}
SENTIMENT_CN = {"positive": "利好", "negative": "利空", "neutral": "中性"}
VERDICT_CN = {"bullish": "偏多", "bearish": "偏空", "neutral": "震荡"}
SENTIMENT_LABEL_ICON = {"乐观": "🟢", "偏暖": "🟢", "中性": "🟡", "偏冷": "🔴", "悲观": "🔴"}


class ReportGenerator:
    def __init__(self):
        self._importance = ImportanceEvaluator()
        self._sector = SectorMapper()

    def generate(self, all_data: dict[str, list[dict]], period: str = "pre_market") -> str:
        all_news = []
        for category, items in all_data.items():
            if category in ("宏观与国际", "财联社新闻"):
                for item in items:
                    imp = self._importance.evaluate(item)
                    item["importance"] = imp["importance"]
                    item["importance_level"] = imp["level"]
                    item["importance_level_desc"] = imp["level_desc"]
                    item["action_hint"] = imp["action_hint"]
                    text = item.get("title", "") + " " + item.get("content", "")
                    sector_info = self._sector.map_sectors(text, item.get("sentiment_score", 0.0))
                    item["positive_sectors"] = sector_info["positive_sectors"]
                    item["negative_sectors"] = sector_info["negative_sectors"]
                    item["sector_hint"] = self._sector.format_sector_hint(text, item.get("sentiment_score", 0.0))
                    all_news.append(item)

        all_news.sort(key=lambda x: x.get("importance", 0), reverse=True)

        verdict_result = self._calc_verdict(all_data, all_news)

        sections = []
        sections.append(self._header(period))
        sections.append(self._verdict_section(verdict_result))
        sections.append(self._important_news_section(all_news[:5]))
        sections.append(self._alert_section(all_news))
        sections.append(self._us_stock_section(all_data.get("美股行情", [])))
        sections.append(self._futures_section(all_data.get("期货市场", [])))
        sections.append(self._intl_section(all_data.get("宏观与国际", [])))
        sections.append(self._cls_news_section(all_data.get("财联社新闻", [])))
        sections.append(self._capital_section(all_data.get("资金面", [])))
        sections.append(self._trading_suggestions_section(verdict_result["verdict"]))
        sections.append(self._risk_section(all_news))
        sections.append(self._footer())
        return "\n".join(sections)

    def generate_markdown(self, all_data: dict[str, list[dict]], period: str = "pre_market") -> str:
        return self.generate(all_data, period)

    def _header(self, period: str) -> str:
        now = datetime.now()
        weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_map[now.weekday()]
        date_str = now.strftime("%Y-%m-%d")
        period_names = {
            "pre_market": "盘前舆情简报",
            "intraday": "盘中舆情简报",
            "midday": "午盘舆情简报",
            "after_market": "盘后舆情简报",
            "weekend": "周末舆情简报",
            "holiday": "假日舆情简报",
        }
        period_name = period_names.get(period, "早盘舆情简报")
        return (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 {period_name} | {date_str} {weekday}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    def _calc_verdict(self, all_data: dict, all_news: list[dict]) -> dict:
        score = 0
        sentiment_scores = []

        us_items = all_data.get("美股行情", [])
        for item in us_items:
            if item.get("direction") == "up":
                score += 1
            elif item.get("direction") == "down":
                score -= 1

        futures_items = all_data.get("期货市场", [])
        for item in futures_items:
            name = item.get("name", "")
            if "A50" in name:
                if item.get("direction") == "up":
                    score += 2
                elif item.get("direction") == "down":
                    score -= 2
            elif "原油" in name or "铁矿石" in name:
                if item.get("direction") == "up":
                    score += 0.5
                elif item.get("direction") == "down":
                    score -= 0.5

        for item in all_news:
            ss = item.get("sentiment_score", 0.0)
            if ss != 0:
                sentiment_scores.append(ss)
                score += ss

        if score >= 3:
            verdict = "bullish"
        elif score <= -3:
            verdict = "bearish"
        else:
            verdict = "neutral"

        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
        avg_sentiment = round(avg_sentiment, 2)

        high_impact = [n for n in all_news if n.get("importance", 0) >= 8]
        mid_impact = [n for n in all_news if 5 <= n.get("importance", 0) < 8]
        impact_level = len(high_impact) * 2 + len(mid_impact)
        if impact_level >= 6:
            impact_grade = "高"
        elif impact_level >= 3:
            impact_grade = "中"
        else:
            impact_grade = "低"

        return {
            "verdict": verdict,
            "verdict_text": VERDICT_CN[verdict],
            "score": score,
            "avg_sentiment": avg_sentiment,
            "sentiment_label": self._score_to_sentiment_label(avg_sentiment),
            "impact_grade": impact_grade,
            "high_impact_count": len(high_impact),
            "mid_impact_count": len(mid_impact),
            "us_items": us_items,
            "futures_items": futures_items,
            "all_news": all_news,
        }

    def _score_to_sentiment_label(self, score: float) -> str:
        if score >= 0.3:
            return "乐观"
        elif score >= 0.1:
            return "偏暖"
        elif score > -0.1:
            return "中性"
        elif score > -0.3:
            return "偏冷"
        else:
            return "悲观"

    def _verdict_section(self, result: dict) -> str:
        verdict_text = result["verdict_text"]
        avg_sentiment = result["avg_sentiment"]
        sentiment_label = result["sentiment_label"]
        impact_grade = result["impact_grade"]
        sentiment_icon = SENTIMENT_LABEL_ICON.get(sentiment_label, "🟡")

        detail_parts = []
        us_items = result["us_items"]
        futures_items = result["futures_items"]
        all_news = result["all_news"]

        if us_items:
            up_count = sum(1 for i in us_items if i.get("direction") == "up")
            down_count = sum(1 for i in us_items if i.get("direction") == "down")
            detail_parts.append(f"美股{'涨多跌少' if up_count > down_count else '跌多涨少'}")
        a50 = [i for i in futures_items if "A50" in i.get("name", "")]
        if a50:
            a50_item = a50[0]
            detail_parts.append(f"A50期指{'微涨' if a50_item.get('direction') == 'up' else '微跌' if a50_item.get('direction') == 'down' else '平盘'}")

        neg_news = [i for i in all_news if i.get("sentiment") == "negative"]
        pos_news = [i for i in all_news if i.get("sentiment") == "positive"]
        if neg_news:
            detail_parts.append(f"有{len(neg_news)}条利空")
        if pos_news:
            detail_parts.append(f"有{len(pos_news)}条利好")

        detail = "，".join(detail_parts) if detail_parts else "数据不足"

        return (
            f"\n🎯 市场定性：{verdict_text} | "
            f"{sentiment_icon} 情感分 {avg_sentiment:+.2f}（{sentiment_label}） | "
            f"💥 影响等级 {impact_grade}\n"
            f"   {detail}"
        )

    def _important_news_section(self, items: list[dict]) -> str:
        if not items:
            return "\n\n━━━ ⭐ 重要新闻 TOP 5 ━━━\n  暂无重要新闻"
        lines = ["\n━━━ ⭐ 重要新闻 TOP 5 ━━━"]
        for item in items:
            icon = SENTIMENT_ICON.get(item.get("sentiment", "neutral"), "🟡")
            title = item.get("title", "")
            time_str = item.get("time", "")
            imp = item.get("importance", 0)
            level = item.get("importance_level", "")
            time_prefix = f"[{time_str}] " if time_str else ""
            sector_hint = item.get("sector_hint", "")
            sector_str = f" → {sector_hint}" if sector_hint else ""
            lines.append(f"{icon} [{imp:.0f}分·{level}] {time_prefix}{title}{sector_str}")
        return "\n".join(lines)

    def _alert_section(self, all_news: list[dict]) -> str:
        alerts = [n for n in all_news if n.get("importance", 0) >= 8]
        if not alerts:
            return ""
        lines = ["\n━━━ 🚨 紧急警报 ━━━"]
        for item in alerts[:3]:
            icon = SENTIMENT_ICON.get(item.get("sentiment", "neutral"), "🟡")
            title = item.get("title", "")
            sector_hint = item.get("sector_hint", "")
            sector_str = f" → {sector_hint}" if sector_hint else ""
            lines.append(f"{icon} {title}{sector_str}")
        return "\n".join(lines)

    def _us_stock_section(self, items: list[dict]) -> str:
        if not items:
            return "\n━━━ 🇺🇸 美股收盘 ━━━\n  暂无数据"
        lines = ["\n━━━ 🇺🇸 美股收盘 ━━━"]
        for item in items:
            arrow = ARROW.get(item.get("direction", "flat"), "➡️")
            name = item.get("name", "")
            change_pct = item.get("change_pct", 0)
            price = item.get("price", 0)
            lines.append(f"• {name}  {change_pct:+.2f}%  {arrow}  (价格: {price})")
        return "\n".join(lines)

    def _futures_section(self, items: list[dict]) -> str:
        if not items:
            return "\n━━━ 📈 期货市场 ━━━\n  暂无数据"
        lines = ["\n━━━ 📈 期货市场 ━━━"]
        for item in items:
            arrow = ARROW.get(item.get("direction", "flat"), "➡️")
            name = item.get("name", "")
            change_pct = item.get("change_pct", 0)
            price = item.get("price", 0)
            lines.append(f"• {name}  {change_pct:+.2f}%  {arrow}  (价格: {price})")
        return "\n".join(lines)

    def _intl_section(self, items: list[dict]) -> str:
        if not items:
            return "\n━━━ 🌍 宏观与国际 ━━━\n  暂无数据"

        macro_items = [i for i in items if i.get("sub_category") == "宏观政策"]
        intl_items = [i for i in items if i.get("sub_category") == "国际要闻"]
        other_items = [i for i in items if i.get("sub_category") not in ("宏观政策", "国际要闻")]

        lines = []
        if macro_items:
            lines.append("\n━━━ 🏛️ 宏观政策 ━━━")
            for item in macro_items[:8]:
                icon = SENTIMENT_ICON.get(item.get("sentiment", "neutral"), "🟡")
                title = item.get("title", "")
                time_str = item.get("time", "")
                time_prefix = f"[{time_str}] " if time_str else ""
                sector_hint = item.get("sector_hint", "")
                sector_str = f" → {sector_hint}" if sector_hint else ""
                lines.append(f"{icon} {time_prefix}{title}{sector_str}")

        if intl_items:
            lines.append("\n━━━ 🌍 国际要闻 ━━━")
            for item in intl_items[:8]:
                icon = SENTIMENT_ICON.get(item.get("sentiment", "neutral"), "🟡")
                title = item.get("title", "")
                time_str = item.get("time", "")
                time_prefix = f"[{time_str}] " if time_str else ""
                sector_hint = item.get("sector_hint", "")
                sector_str = f" → {sector_hint}" if sector_hint else ""
                lines.append(f"{icon} {time_prefix}{title}{sector_str}")

        if other_items:
            lines.append("\n━━━ 📰 其他要闻 ━━━")
            for item in other_items[:5]:
                icon = SENTIMENT_ICON.get(item.get("sentiment", "neutral"), "🟡")
                title = item.get("title", "")
                lines.append(f"{icon} {title}")

        return "\n".join(lines) if lines else "\n━━━ 🌍 宏观与国际 ━━━\n  暂无数据"

    def _cls_news_section(self, items: list[dict]) -> str:
        if not items:
            return "\n━━━ ⚡ 财联社快讯 ━━━\n  暂无数据"

        positive = [i for i in items if i.get("sentiment") == "positive"]
        negative = [i for i in items if i.get("sentiment") == "negative"]
        neutral = [i for i in items if i.get("sentiment") == "neutral"]

        lines = ["\n━━━ ⚡ 财联社快讯 ━━━"]
        if negative:
            lines.append("  ▸ 利空消息：")
            for item in negative[:5]:
                title = item.get("title", "")
                time_str = item.get("time", "")
                time_prefix = f"[{time_str}] " if time_str else ""
                sector_hint = item.get("sector_hint", "")
                sector_str = f" → {sector_hint}" if sector_hint else ""
                lines.append(f"    🔴 {time_prefix}{title}{sector_str}")
        if positive:
            lines.append("  ▸ 利好消息：")
            for item in positive[:5]:
                title = item.get("title", "")
                time_str = item.get("time", "")
                time_prefix = f"[{time_str}] " if time_str else ""
                sector_hint = item.get("sector_hint", "")
                sector_str = f" → {sector_hint}" if sector_hint else ""
                lines.append(f"    🟢 {time_prefix}{title}{sector_str}")
        if neutral:
            lines.append("  ▸ 其他快讯：")
            for item in neutral[:3]:
                title = item.get("title", "")
                lines.append(f"    🟡 {title}")
        return "\n".join(lines)

    def _capital_section(self, items: list[dict]) -> str:
        if not items:
            return "\n━━━ 💰 资金面 ━━━\n  暂无数据"
        lines = ["\n━━━ 💰 资金面 ━━━"]
        for item in items:
            name = item.get("name", "")
            value = item.get("value", 0)
            unit = item.get("unit", "")
            date = item.get("date", "")
            arrow = ARROW.get(item.get("direction", "flat"), "➡️")
            lines.append(f"• {name}  {value:+.2f}{unit}  {arrow}  ({date})")
        return "\n".join(lines)

    def _trading_suggestions_section(self, verdict: str) -> str:
        suggestions = self._sector.get_trading_suggestions(verdict)
        lines = ["\n━━━ 📋 操作建议 ━━━"]
        for style, actions in suggestions.items():
            lines.append(f"  {style}：{'；'.join(actions)}")
        return "\n".join(lines)

    def _risk_section(self, all_news: list[dict]) -> str:
        risks = [n for n in all_news if n.get("sentiment") == "negative" and n.get("importance", 0) >= 5]
        lines = ["\n━━━ ⚠️ 风险提示 ━━━"]
        if risks:
            for item in risks[:5]:
                title = item.get("title", "")
                imp = item.get("importance", 0)
                lines.append(f"• [{imp:.0f}分] {title}")
        else:
            lines.append("• 暂无明显风险信号")
        return "\n".join(lines)

    def _footer(self) -> str:
        return "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💡 以上信息仅供参考，不构成投资建议"
