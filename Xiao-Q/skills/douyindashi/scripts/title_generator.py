#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音运营大师 - 标题与文案生成脚本
功能：爆款标题生成、标题优化、标题公式库、AB测试
"""

import random
from typing import Dict, List, Optional


class TitleGenerator:
    """标题生成器"""
    
    # 标题公式库
    TITLE_FORMULAS = {
        "数字型": [
            "学会这{num}招，快速搞定{topic}",
            "{num}个{topic}技巧，学会了你就是高手",
            "只要{num}分钟，轻松掌握{topic}",
            "关于{topic}，你需要知道的{num}件事",
            "{num}年经验总结的{topic}方法"
        ],
        "疑问型": [
            "为什么你的{topic}总是不成功？",
            "{topic}到底难在哪里？",
            "你的{topic}方法是对的吗？",
            "怎么做{topic}才有效？",
            "为什么别人{topic}那么容易？"
        ],
        "悬念型": [
            "原来{topic}这么简单，后悔现在才知道",
            "这个{topic}秘密，99%的人不知道",
            "没想到{topic}还能这样操作",
            "{topic}的真相，让你大开眼界",
            "学会了{topic}，生活完全不一样"
        ],
        "感叹型": [
            "太绝了！{topic}竟然这么简单",
            "天呐！{topic}原来这么简单",
            "绝了！用了这个方法，{topic}轻松搞定",
            "太牛了！这个{topic}技巧太管用了",
            "OMG！{topic}这样做效果翻倍"
        ],
        "痛点型": [
            "还在为{topic}烦恼？试试这个方法",
            "{topic}问题多？可能是你方法不对",
            "你还在为{topic}发愁吗？",
            "{topic}做不好？看完你就知道了",
            "总是{topic}？多半是没找对方法"
        ],
        "利益型": [
            "学会这个方法，{topic}效率翻倍",
            "这个技巧让你的{topic}效率提升10倍",
            "快速搞定{topic}，只需这一招",
            "手把手教你{topic}，一看就会",
            "零基础也能学会的{topic}方法"
        ],
        "反差型": [
            "别人都{common}，只有我{unique}",
            "同样{topic}，为什么差距这么大？",
            "同样是{topic}，效果差距不是一点点",
            "为什么你总是{common}？看完就明白了",
            "别人不知道的{topic}秘密"
        ],
        "从众型": [
            "{percent}%的人都不知道的{topic}方法",
            "看过这个{topic}方法的，都收藏了",
            "全网都在用的{topic}技巧",
            "{num}万人都在学的{topic}方法",
            "这个{topic}方法，让{many}人受益"
        ],
        "身份型": [
            "{identity}必看的{topic}攻略",
            "作为一个{identity}，{topic}必须了解",
            "{identity}都在用的{topic}方法",
            "给{identity}的{topic}建议",
            "{identity}应该如何{topic}？"
        ],
        "时间型": [
            "{time}学会{topic}，你也可以",
            "每天{timing}，一个月后{topic}完全不一样",
            "{time}搞定{topic}，效率翻倍",
            "坚持{time}，你的{topic}会有惊人变化",
            "{time}学会{topic}，终身受用"
        ]
    }
    
    # 常用替换词
    REPLACEMENT_WORDS = {
        "num": ["3", "5", "7", "10", "99%"],
        "topic": ["高效学习", "职场沟通", "时间管理", "减肥", "护肤"],
        "common": ["做不好", "失败", "放弃", "焦虑", "迷茫"],
        "unique": ["成功了", "突破", "逆袭", "成长", "进步"],
        "identity": ["职场人", "新手妈妈", "学生党", "打工人", "考证党"],
        "time": ["7天", "21天", "30天", "100天"],
        "timing": ["早起", "每天10分钟", "坚持一个月"],
        "many": ["10万", "100万", "1000万"],
        "percent": ["90", "95", "99"]
    }
    
    def __init__(self, industry: str = "通用"):
        self.industry = industry
    
    def generate_title(self, formula_type: str = "数字型", topic: str = "高效工作", **kwargs) -> str:
        """使用公式生成标题"""
        formulas = self.TITLE_FORMULAS.get(formula_type, self.TITLE_FORMULAS["数字型"])
        formula = random.choice(formulas)
        
        # 填充模板
        replacements = {
            "num": kwargs.get("num", random.choice(self.REPLACEMENT_WORDS["num"])),
            "topic": topic,
            "common": kwargs.get("common", random.choice(self.REPLACEMENT_WORDS["common"])),
            "unique": kwargs.get("unique", random.choice(self.REPLACEMENT_WORDS["unique"])),
            "identity": kwargs.get("identity", random.choice(self.REPLACEMENT_WORDS["identity"])),
            "time": kwargs.get("time", random.choice(self.REPLACEMENT_WORDS["time"])),
            "timing": kwargs.get("timing", random.choice(self.REPLACEMENT_WORDS["timing"])),
            "many": kwargs.get("many", random.choice(self.REPLACEMENT_WORDS["many"])),
            "percent": kwargs.get("percent", random.choice(self.REPLACEMENT_WORDS["percent"]))
        }
        
        return formula.format(**replacements)
    
    def optimize_title(self, original_title: str, topic: str = "") -> List[Dict]:
        """优化现有标题"""
        # 分析原标题
        analysis = {
            "原标题": original_title,
            "字数": len(original_title),
            "问题": []
        }
        
        # 判断问题
        if len(original_title) > 30:
            analysis["问题"].append("字数偏多，建议精简")
        if "？" not in original_title and len(original_title) < 15:
            analysis["问题"].append("缺乏悬念或疑问")
        if not any(word in original_title for word in ["这", "如何", "为什么", "原来"]):
            analysis["问题"].append("缺乏引导性词汇")
        
        # 生成优化版本
        optimized = []
        
        # 方案1：数字型优化
        optimized.append({
            "类型": "数字型",
            "标题": self.generate_title("数字型", topic or "这个技能"),
            "点击率预估": "较高",
            "适用场景": "干货教程类内容"
        })
        
        # 方案2：疑问型优化
        optimized.append({
            "类型": "疑问型",
            "标题": self.generate_title("疑问型", topic or "这个技能"),
            "点击率预估": "高",
            "适用场景": "引发好奇的内容"
        })
        
        # 方案3：感叹型优化
        optimized.append({
            "类型": "感叹型",
            "标题": self.generate_title("感叹型", topic or "这个技能"),
            "点击率预估": "高",
            "适用场景": "有惊艳效果的内容"
        })
        
        return {
            "分析": analysis,
            "优化方案": optimized
        }
    
    def generate_ab_test_titles(self, topic: str, count: int = 4) -> List[Dict]:
        """生成AB测试标题"""
        formula_types = ["数字型", "疑问型", "感叹型", "悬念型"]
        titles = []
        
        for i, formula_type in enumerate(formula_types[:count]):
            titles.append({
                "版本": chr(65 + i),  # A, B, C, D
                "公式": formula_type,
                "标题": self.generate_title(formula_type, topic),
                "预估点击率": self._estimate_ctr(formula_type),
                "适用内容": self._get_suitable_content(formula_type)
            })
        
        return titles
    
    def _estimate_ctr(self, formula_type: str) -> str:
        """预估点击率"""
        estimates = {
            "数字型": "8-12%",
            "疑问型": "10-15%",
            "感叹型": "9-14%",
            "悬念型": "12-18%",
            "痛点型": "8-11%",
            "利益型": "9-13%",
            "反差型": "11-16%",
            "从众型": "10-14%"
        }
        return estimates.get(formula_type, "8-12%")
    
    def _get_suitable_content(self, formula_type: str) -> str:
        """获取适用内容类型"""
        contents = {
            "数字型": "教程、干货、技巧类",
            "疑问型": "科普、解惑、揭秘类",
            "感叹型": "好物、效果、惊艳类",
            "悬念型": "揭秘、反转、秘密类",
            "痛点型": "问题、困扰、解决方案类",
            "利益型": "效率、方法、捷径类",
            "反差型": "对比、PK、对比类",
            "从众型": "推荐、热门、必学类"
        }
        return contents.get(formula_type, "通用")
    
    def get_formula_library(self) -> Dict:
        """获取标题公式库"""
        return {
            formula_type: {
                "公式示例": [f.format(**{k: random.choice(v) for k, v in self.REPLACEMENT_WORDS.items() if k in f})
                            for f in formulas[:3]],
                "适用场景": self._get_suitable_content(formula_type),
                "使用技巧": self._get_tips(formula_type)
            }
            for formula_type, formulas in self.TITLE_FORMULAS.items()
        }
    
    def _get_tips(self, formula_type: str) -> List[str]:
        """获取使用技巧"""
        tips = {
            "数字型": ["数字要具体", "数字放前面"],
            "疑问型": ["问题要痛点", "引发好奇"],
            "感叹型": ["情绪要真实", "不要过度夸张"],
            "悬念型": ["留有悬念", "不要剧透"],
            "痛点型": ["痛点要真实", "提供希望"],
            "利益型": ["利益要明确", "突出效果"],
            "反差型": ["反差要明显", "对比要真实"],
            "从众型": ["数据要真实", "不要虚假夸大"]
        }
        return tips.get(formula_type, ["配合内容使用"])
    
    def batch_generate_titles(self, topic: str, count: int = 10, formula_types: List[str] = None) -> List[str]:
        """批量生成标题"""
        if formula_types is None:
            formula_types = list(self.TITLE_FORMULAS.keys())
        
        titles = []
        for i in range(count):
            formula_type = random.choice(formula_types)
            titles.append(self.generate_title(formula_type, topic))
        
        return titles


def main():
    """主函数"""
    print("=" * 60)
    print("📝 抖音运营大师 - 标题生成工具 📝")
    print("=" * 60)
    
    generator = TitleGenerator()
    
    # 1. 使用公式生成标题
    print("\n🔥 爆款标题生成:")
    print("-" * 40)
    
    topics = ["时间管理", "职场沟通", "护肤技巧", "高效学习"]
    for topic in topics:
        print(f"\n  主题: {topic}")
        for formula in ["数字型", "疑问型", "感叹型"]:
            title = generator.generate_title(formula, topic)
            print(f"    [{formula}] {title}")
    
    # 2. 标题公式库
    print("\n\n📚 标题公式库:")
    print("-" * 40)
    library = generator.get_formula_library()
    for formula_type, details in library.items():
        print(f"\n  【{formula_type}】")
        print(f"    公式示例:")
        for example in details["公式示例"]:
            print(f"      • {example}")
        print(f"    适用场景: {details['适用场景']}")
        print(f"    使用技巧: {', '.join(details['使用技巧'])}")
    
    # 3. 标题优化
    print("\n\n✨ 标题优化:")
    print("-" * 40)
    original = "如何做红烧肉"
    result = generator.optimize_title(original, "红烧肉")
    print(f"  原标题: {result['分析']['原标题']}")
    print(f"  字数: {result['分析']['字数']}")
    if result['分析']['问题']:
        print(f"  问题: {', '.join(result['分析']['问题'])}")
    
    print("\n  优化方案:")
    for opt in result['优化方案']:
        print(f"    【{opt['类型']}】{opt['标题']}")
        print(f"      点击率预估: {opt['点击率预估']}")
        print(f"      适用场景: {opt['适用场景']}")
    
    # 4. AB测试标题
    print("\n\n📊 标题AB测试:")
    print("-" * 40)
    print(f"{'版本':<8}{'公式':<10}{'预估点击率':<12}{'标题':<30}")
    print("-" * 80)
    
    ab_titles = generator.generate_ab_test_titles("职场沟通技巧", 4)
    for item in ab_titles:
        print(f"{item['版本']:<8}{item['公式']:<10}{item['预估点击率']:<12}{item['标题'][:28]}...")
    
    print("\n  适用内容:")
    for item in ab_titles:
        print(f"    {item['版本']}: {item['适用内容']}")
    
    # 5. 批量生成
    print("\n\n📋 批量生成标题:")
    print("-" * 40)
    batch_titles = generator.batch_generate_titles("高效学习", 8)
    for i, title in enumerate(batch_titles, 1):
        print(f"  {i}. {title}")
    
    print("\n" + "=" * 60)
    print("✅ 标题生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
