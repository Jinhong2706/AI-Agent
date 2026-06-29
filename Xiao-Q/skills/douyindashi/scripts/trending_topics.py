#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音运营大师 - 热门话题分析脚本
功能：追踪热点选题、分析热度趋势、推荐蹭热点方式
来源：抖音热榜、微博热搜、百度指数、知乎热榜
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class TrendingTopicsAnalyzer:
    """热门话题分析器"""
    
    # 标题公式库
    TITLE_FORMULAS = {
        "数字型": "学会这X招，快速搞定XX",
        "疑问型": "为什么XX？XX了你就知道了",
        "悬念型": "原来XX这么简单，后悔现在才知道",
        "感叹型": "太绝了！这道菜我能吃一周！",
        "痛点型": "你是不是也XX？",
        "利益型": "学会这3招，XX变得超简单",
        "反差型": "别人都XX，只有我XX",
        "从众型": "XX%的人都不知道XX"
    }
    
    # 行业热点关键词
    INDUSTRY_KEYWORDS = {
        "美妆": ["早C晚A", "成分党", "平替", "素颜霜", "粉底液", "春季限定", "新品发布"],
        "美食": ["家常菜", "甜点", "饮品", "探店", "打卡", "食材测评", "摆摊"],
        "知识": ["Excel技巧", "设计教程", "摄影技巧", "求职干货", "学习方法"],
        "职场": ["职场沟通", "加薪技巧", "同事关系", "领导力", "工作效率"],
        "健身": ["减脂餐", "马甲线", "居家健身", "瑜伽", "体态纠正"],
        "穿搭": ["春季穿搭", "显高", "显白", "学生党", "通勤装"]
    }
    
    def __init__(self, industry: str = "通用"):
        self.industry = industry
        self.trending_cache = []
        
    def get_douyin_trending(self) -> List[Dict]:
        """获取抖音热榜话题"""
        # 模拟数据，实际使用时应调用真实API
        trending = [
            {"rank": 1, "topic": "#春季穿搭灵感#", "heat": 9856000, "trend": "↑"},
            {"rank": 2, "topic": "#打工人的周一早餐#", "heat": 8523000, "trend": "↑"},
            {"rank": 3, "topic": "#居家健身30天挑战#", "heat": 7632000, "trend": "↓"},
            {"rank": 4, "topic": "#职场沟通技巧#", "heat": 6541000, "trend": "↑"},
            {"rank": 5, "topic": "#美食探店打卡#", "heat": 5987000, "trend": "→"},
            {"rank": 6, "topic": "#美妆新品测评#", "heat": 5432000, "trend": "↑"},
            {"rank": 7, "topic": "#存钱打卡计划#", "heat": 4876000, "trend": "↑"},
            {"rank": 8, "topic": "#读书分享#", "heat": 4321000, "trend": "↓"},
            {"rank": 9, "topic": "#宠物日常#", "heat": 3987000, "trend": "→"},
            {"rank": 10, "topic": "#新手摄影教程#", "heat": 3562000, "trend": "↑"}
        ]
        return trending
    
    def get_industry_trending(self, industry: Optional[str] = None) -> List[Dict]:
        """获取行业垂直热点"""
        ind = industry or self.industry
        keywords = self.INDUSTRY_KEYWORDS.get(ind, self.INDUSTRY_KEYWORDS["知识"])
        
        trending = []
        for i, keyword in enumerate(keywords[:5]):
            trending.append({
                "keyword": keyword,
                "heat_score": random.randint(6000, 10000),
                "rising_speed": random.choice(["快速上升", "平稳", "略有下降"]),
                "suggested_angles": self._generate_angles(keyword)
            })
        return trending
    
    def _generate_angles(self, keyword: str) -> List[str]:
        """生成内容切入角度"""
        return [
            f"「{keyword}，这几点必须注意」",
            f"「{keyword}的正确打开方式」",
            f"「{keyword}避坑指南」",
            f"「新手必看：{keyword}入门」"
        ]
    
    def analyze_trending(self, topic: str) -> Dict:
        """分析热点蹭法"""
        # 判断蹭热点适合性
        suitability = {
            "情感/娱乐/职场": ["适合蹭", "可适度参与"],
            "带货/美食/知识": ["可蹭", "需结合自身内容"],
            "政治/负面/争议": ["不建议蹭", "风险较高"]
        }
        
        # 蹭法公式
        formula = "热点关联 + 自身领域 + 独特视角"
        
        return {
            "topic": topic,
            "suitability": suitability,
            "蹭法公式": formula,
            "示例话术": f"「{topic}让我想到...」",
            "注意事项": [
                "蹭热点要结合自身内容，不能硬蹭",
                "政治/负面/争议热点不要蹭",
                "时效性热点要快，越早蹭效果越好"
            ]
        }
    
    def generate_topic_title(self, topic: str, formula_type: str = "数字型") -> str:
        """使用标题公式生成标题"""
        formula = self.TITLE_FORMULAS.get(formula_type, self.TITLE_FORMULAS["数字型"])
        # 简单替换演示
        return formula.replace("XX", topic).replace("X", str(random.randint(3, 9)))
    
    def recommend_topics(self, count: int = 5) -> List[Dict]:
        """推荐选题"""
        recommendations = []
        
        # 抖音热榜选题
        douyin_top = self.get_douyin_trending()[:3]
        for item in douyin_top:
            recommendations.append({
                "类型": "抖音热榜蹭热点",
                "话题": item["topic"],
                "热度": item["heat"],
                "建议": "结合自身领域快速出内容",
                "选题角度": self._generate_angles(item["topic"].replace("#", ""))
            })
        
        # 行业热点选题
        industry_top = self.get_industry_trending()[:2]
        for item in industry_top:
            recommendations.append({
                "类型": "行业垂直热点",
                "话题": item["keyword"],
                "热度": item["heat_score"],
                "建议": "深耕垂直领域",
                "选题角度": item["suggested_angles"]
            })
        
        return recommendations[:count]
    
    def generate_monthly_calendar(self, month: str, industry: Optional[str] = None) -> Dict:
        """生成月度选题日历"""
        ind = industry or self.industry
        
        # 模拟节日节点
        festival_nodes = {
            "5月": [
                {"date": "5.1-5.3", "主题": "劳动节特别内容"},
                {"date": "5.4", "主题": "青年节热点"},
                {"date": "5.11", "主题": "母亲节特别"},
                {"date": "5.20", "主题": "520表白日"}
            ],
            "6月": [
                {"date": "6.1", "主题": "儿童节内容"},
                {"date": "6.18", "主题": "618大促"},
                {"date": "6.22", "主题": "端午节"}
            ]
        }
        
        monthly_plan = festival_nodes.get(month, [])
        
        return {
            "month": month,
            "industry": ind,
            "festival_nodes": monthly_plan,
            "regular_topics": self.get_industry_trending(ind)[:4],
            "content_ratio": {
                "节日热点": "20%",
                "行业热点": "30%",
                "常规选题": "50%"
            }
        }


def main():
    """主函数"""
    print("=" * 60)
    print("🔥 抖音运营大师 - 热门话题分析工具 🔥")
    print("=" * 60)
    
    analyzer = TrendingTopicsAnalyzer(industry="美食")
    
    # 1. 获取抖音热榜
    print("\n📊 抖音热榜 TOP 10:")
    print("-" * 40)
    trending = analyzer.get_douyin_trending()
    for item in trending[:5]:
        print(f"  {item['rank']}. {item['topic']} (热度: {item['heat']:,}) {item['trend']}")
    
    # 2. 获取行业热点
    print("\n📈 美食行业热点:")
    print("-" * 40)
    industry_data = analyzer.get_industry_trending("美食")
    for item in industry_data:
        print(f"  • {item['keyword']} (热度: {item['heat_score']}) - {item['rising_speed']}")
    
    # 3. 生成选题推荐
    print("\n💡 选题推荐:")
    print("-" * 40)
    recommendations = analyzer.recommend_topics(5)
    for i, rec in enumerate(recommendations, 1):
        print(f"\n  [{i}] {rec['类型']}: {rec['话题']}")
        print(f"      热度: {rec['热度']:,}")
        print(f"      建议: {rec['建议']}")
        print(f"      角度: {rec['选题角度'][0]}")
    
    # 4. 分析热点蹭法
    print("\n🎯 热点蹭法指南:")
    print("-" * 40)
    analysis = analyzer.analyze_trending("#职场干货")
    print(f"  话题: {analysis['topic']}")
    print(f"  蹭法公式: {analysis['蹭法公式']}")
    print(f"  示例话术: {analysis['示例话术']}")
    print("  注意事项:")
    for note in analysis['注意事项']:
        print(f"    • {note}")
    
    # 5. 生成月度日历
    print("\n📅 5月选题日历:")
    print("-" * 40)
    calendar = analyzer.generate_monthly_calendar("5月")
    print(f"  节日节点:")
    for node in calendar['festival_nodes']:
        print(f"    • {node['date']}: {node['主题']}")
    
    print("\n" + "=" * 60)
    print("✅ 分析完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
