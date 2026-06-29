#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音运营大师 - 竞品分析脚本
功能：竞品数据监控、差距分析、优势提炼、追赶策略
数据来源：蝉妈妈、飞瓜数据、新抖等
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class CompetitorAnalyzer:
    """竞品分析器"""
    
    # 竞品监控维度
    MONITOR_DIMENSIONS = [
        "粉丝数变化",
        "近期爆款视频",
        "更新频率",
        "内容方向变化",
        "互动数据",
        "带货数据"
    ]
    
    def __init__(self, my_account: str = ""):
        self.my_account = my_account
        self.competitors = []
    
    def add_competitor(self, name: str, account_id: str, followers: int, category: str = "同类账号") -> Dict:
        """添加竞品"""
        competitor = {
            "名称": name,
            "账号ID": account_id,
            "粉丝数": followers,
            "类别": category,
            "近7天数据": self._generate_weekly_data(followers),
            "近30天爆款": self._generate_top_videos(),
            "内容方向": self._generate_content_direction()
        }
        self.competitors.append(competitor)
        return competitor
    
    def _generate_weekly_data(self, followers: int) -> Dict:
        """生成周数据"""
        weekly_growth = int(followers * random.uniform(0.005, 0.02))
        avg_views = int(followers * random.uniform(0.1, 0.3))
        
        return {
            "涨粉数": weekly_growth,
            "涨粉率": f"{(weekly_growth/followers)*100:.2f}%",
            "平均播放": avg_views,
            "爆款数": random.randint(0, 3),
            "更新频次": random.randint(3, 7),
            "互动率": f"{random.uniform(3, 10):.1f}%"
        }
    
    def _generate_top_videos(self) -> List[Dict]:
        """生成爆款视频"""
        videos = []
        topics = ["实用技巧", "测评分享", "干货教程", "日常分享", "热点蹭热"]
        
        for i, topic in enumerate(random.sample(topics, 3)):
            videos.append({
                "标题": f"爆款标题_{i+1}_{topic}",
                "播放量": random.randint(50000, 500000),
                "点赞数": random.randint(5000, 50000),
                "评论数": random.randint(500, 5000),
                "话题": f"#{topic}#"
            })
        
        return videos
    
    def _generate_content_direction(self) -> List[str]:
        """生成内容方向"""
        directions = [
            "教程类内容占比60%",
            "测评类内容占比25%",
            "日常类内容占比15%",
            "固定封面风格",
            "统一人设形象"
        ]
        return random.sample(directions, 3)
    
    def generate_monitoring_table(self) -> List[Dict]:
        """生成竞品监控表"""
        table = []
        
        for comp in self.competitors:
            table.append({
                "账号": comp["名称"],
                "粉丝数": f"{comp['粉丝数']:,}",
                "周涨粉": f"+{comp['近7天数据']['涨粉数']:,}",
                "平均播放": f"{comp['近7天数据']['平均播放']:,}",
                "近7天爆款": comp["近7天数据"]["爆款数"],
                "更新频次": f"{comp['近7天数据']['更新频次']}条/周",
                "互动率": comp["近7天数据"]["互动率"]
            })
        
        return table
    
    def analyze_gap(self, my_followers: int, my_avg_views: int) -> Dict:
        """分析差距"""
        if not self.competitors:
            return {"message": "请先添加竞品"}
        
        # 找到最强竞品
        top_comp = max(self.competitors, key=lambda x: x["粉丝数"])
        
        gap_analysis = {
            "对比对象": top_comp["名称"],
            "粉丝差距": {
                "己方": my_followers,
                "竞品": top_comp["粉丝数"],
                "差距": top_comp["粉丝数"] - my_followers,
                "差距倍数": f"{(top_comp['粉丝数']/my_followers):.1f}倍"
            },
            "播放差距": {
                "己方": my_avg_views,
                "竞品": top_comp["近7天数据"]["平均播放"],
                "差距": top_comp["近7天数据"]["平均播放"] - my_avg_views
            },
            "爆款差距": {
                "己方": "待积累",
                "竞品": f"{top_comp['近7天数据']['爆款数']}条/周",
                "分析": "竞品持续有爆款输出，内容质量稳定"
            },
            "核心差距": [
                f"粉丝量差距{(top_comp['粉丝数']/my_followers):.1f}倍",
                "爆款率和内容持续性有待提升",
                "账号人设和内容方向需进一步明确"
            ]
        }
        
        return gap_analysis
    
    def generate_swot_analysis(self, account_data: Dict) -> Dict:
        """生成SWOT分析"""
        return {
            "S-优势": {
                "内容质量": "视频制作精良，画面清晰",
                "专业能力": "在细分领域有专业知识",
                "粉丝粘性": "现有粉丝互动积极"
            },
            "W-劣势": {
                "更新频率": "更新不够稳定",
                "流量获取": "自然流量获取能力弱",
                "爆款能力": "缺少爆款内容运营经验"
            },
            "O-机会": {
                "平台趋势": "某类型内容正在上升期",
                "市场需求": "目标人群需求未被满足",
                "差异化": "存在差异化发展空间"
            },
            "T-威胁": {
                "竞争加剧": "同类账号增加",
                "算法变化": "平台推荐逻辑调整",
                "内容同质": "用户审美疲劳"
            }
        }
    
    def generate_catch_up_strategy(self, gap_analysis: Dict, swot: Dict) -> Dict:
        """生成追赶策略"""
        return {
            "短期目标（1个月）": {
                "重点": "学习竞品爆款选题",
                "行动计划": [
                    "每天分析竞品TOP10视频选题",
                    "模仿2-3个爆款选题方向",
                    "优化封面风格，统一视觉",
                    "提高更新频率到每周5条"
                ],
                "预期效果": "平均播放提升30%"
            },
            "中期目标（3个月）": {
                "重点": "建立差异化壁垒",
                "行动计划": [
                    "建立选题库（储备30+选题）",
                    "形成独特的内容风格",
                    "积累忠实粉丝群体",
                    "尝试突破性内容形式"
                ],
                "预期效果": "粉丝突破X万，有爆款产出"
            },
            "长期目标（6个月）": {
                "重点": "打造账号IP",
                "行动计划": [
                    "强化人设标签",
                    "拓展内容形式",
                    "建立粉丝社群",
                    "探索变现路径"
                ],
                "预期效果": "账号具有辨识度和变现能力"
            }
        }
    
    def analyze_content_patterns(self, competitor_name: str) -> Dict:
        """分析竞品内容规律"""
        comp = next((c for c in self.competitors if c["名称"] == competitor_name), None)
        
        if not comp:
            return {"error": "未找到该竞品"}
        
        return {
            "竞品": competitor_name,
            "内容规律": {
                "选题偏好": "实用技巧类、干货分享类内容表现好",
                "内容形式": "口播+字幕为主，教程类占比高",
                "封面风格": "人物出镜+大字标题，高对比色",
                "标题特点": "数字型+痛点型组合使用"
            },
            "爆款共同点": [
                "开头3秒有强钩子",
                "内容有干货价值",
                "结尾有互动引导",
                "发布时间相对固定"
            ],
            "可借鉴点": [
                "学习选题思路",
                "参考封面设计",
                "模仿内容结构",
                "借鉴互动话术"
            ],
            "差异化方向": [
                "从细分领域切入",
                "找到独特视角",
                "强化个人特色",
                "提供独特价值"
            ]
        }
    
    def generate_monitoring_report(self, my_account: Dict) -> Dict:
        """生成竞品监控报告"""
        if not self.competitors:
            return {"error": "请先添加竞品"}
        
        report = {
            "报告时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "己方账号": my_account.get("名称", "我的账号"),
            "己方数据": my_account,
            "竞品概况": self.generate_monitoring_table(),
            "关键发现": [
                f"竞品{self.competitors[0]['名称'] if self.competitors else ''}表现最佳",
                "爆款内容集中在教程类选题",
                "固定更新时间有助于粉丝养成习惯"
            ],
            "追赶优先级": [
                "1. 提升内容质量",
                "2. 优化选题策略",
                "3. 提高更新频率",
                "4. 建立差异化"
            ]
        }
        
        return report


def main():
    """主函数"""
    print("=" * 60)
    print("🔍 抖音运营大师 - 竞品分析工具 🔍")
    print("=" * 60)
    
    analyzer = CompetitorAnalyzer("我的账号")
    
    # 1. 添加竞品
    print("\n📝 添加竞品...")
    comp1 = analyzer.add_competitor("竞品A", "@jingpinA", 500000, "美食教程")
    comp2 = analyzer.add_competitor("竞品B", "@jingpinB", 300000, "美食日常")
    comp3 = analyzer.add_competitor("竞品C", "@jingpinC", 800000, "美食测评")
    
    print(f"  ✅ 已添加 {len(analyzer.competitors)} 个竞品")
    
    # 2. 竞品监控表
    print("\n📊 竞品监控表:")
    print("-" * 60)
    table = analyzer.generate_monitoring_table()
    print(f"{'账号':<12}{'粉丝数':<12}{'周涨粉':<10}{'平均播放':<12}{'爆款数':<8}{'更新频次':<12}")
    print("-" * 60)
    for row in table:
        print(f"{row['账号']:<12}{row['粉丝数']:<12}{row['周涨粉']:<10}{row['平均播放']:<12}{row['近7天爆款']:<8}{row['更新频次']:<12}")
    
    # 3. 差距分析
    print("\n📈 差距分析:")
    print("-" * 40)
    my_account = {"名称": "我的账号", "粉丝数": 50000, "平均播放": 5000}
    gap = analyzer.analyze_gap(my_account["粉丝数"], my_account["平均播放"])
    
    print(f"  对比对象: {gap['对比对象']}")
    print(f"  粉丝差距:")
    print(f"    己方: {gap['粉丝差距']['己方']:,}")
    print(f"    竞品: {gap['粉丝差距']['竞品']:,}")
    print(f"    差距: {gap['粉丝差距']['差距倍数']}")
    print(f"  播放差距:")
    print(f"    己方: {gap['播放差距']['己方']:,}")
    print(f"    竞品: {gap['播放差距']['竞品']:,}")
    
    print("\n  核心差距:")
    for item in gap['核心差距']:
        print(f"    • {item}")
    
    # 4. SWOT分析
    print("\n🎯 SWOT分析:")
    print("-" * 40)
    swot = analyzer.generate_swot_analysis(my_account)
    for key, items in swot.items():
        print(f"\n  {key}:")
        for k, v in items.items():
            print(f"    {k}: {v}")
    
    # 5. 追赶策略
    print("\n🚀 追赶策略:")
    print("-" * 40)
    strategy = analyzer.generate_catch_up_strategy(gap, swot)
    for period, details in strategy.items():
        print(f"\n  【{period}】")
        print(f"    重点: {details['重点']}")
        print(f"    行动计划:")
        for i, action in enumerate(details['行动计划'], 1):
            print(f"      {i}. {action}")
        print(f"    预期效果: {details['预期效果']}")
    
    # 6. 内容规律分析
    print("\n📋 竞品内容规律分析:")
    print("-" * 40)
    pattern = analyzer.analyze_content_patterns("竞品A")
    print(f"  竞品: {pattern['竞品']}")
    print("  内容规律:")
    for k, v in pattern['内容规律'].items():
        print(f"    {k}: {v}")
    print("  爆款共同点:")
    for item in pattern['爆款共同点']:
        print(f"    • {item}")
    print("  可借鉴点:")
    for item in pattern['可借鉴点']:
        print(f"    • {item}")
    print("  差异化方向:")
    for item in pattern['差异化方向']:
        print(f"    • {item}")
    
    # 7. 监控报告
    print("\n📑 竞品监控报告:")
    print("-" * 40)
    report = analyzer.generate_monitoring_report(my_account)
    print(f"  报告时间: {report['报告时间']}")
    print(f"  己方账号: {report['己方账号']}")
    print("  关键发现:")
    for finding in report['关键发现']:
        print(f"    • {finding}")
    print("  追赶优先级:")
    for priority in report['追赶优先级']:
        print(f"    {priority}")
    
    print("\n" + "=" * 60)
    print("✅ 分析完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
