#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音运营大师 - 视频脚本生成脚本
功能：生成口播稿、剧本、知识科普文案、情感文案等
覆盖：黄金开头、内容结构、结尾引导全流程
"""

import random
from typing import Dict, List, Optional


class VideoScriptGenerator:
    """视频脚本生成器"""
    
    # 黄金开头模板
    OPENING_TEMPLATES = {
        "痛点型": [
            "你是不是也{problem}？",
            "你有没有遇到过{problem}的情况？",
            "{problem}，这是不是你最头疼的问题？"
        ],
        "利益型": [
            "学会这{method}，{problem}变得超简单",
            "今天教你{result}，错过你会后悔",
            "{method}，让你轻松搞定{problem}"
        ],
        "反差型": [
            "别人都{common}，只有我{unique}",
            "同样是{field}，为什么你总是{bad}？",
            "同样是{method}，效果差距怎么这么大"
        ],
        "提问型": [
            "为什么{result}？答案出乎意料",
            "{problem}到底是什么原因？",
            "你觉得{method}对不对？"
        ],
        "数字型": [
            "{num}个{method}，最后一个太重要了",
            "只要掌握这{num}点，{result}不是问题",
            "{num}分钟教会你{method}"
        ]
    }
    
    # 结尾引导模板
    ENDING_TEMPLATES = {
        "关注引导": [
            "关注我，每天分享{field}干货",
            "点关注不迷路，主页还有更多{method}教程",
            "这么实用的内容，不关注就亏了",
            "想知道更多{method}吗？关注我，下期告诉你"
        ],
        "互动引导": [
            "你们还有什么问题，评论区告诉我",
            "觉得这期有用，点个赞支持一下",
            "有同感的小伙伴扣个666",
            "你们遇到过{method}吗？说说你的经历"
        ],
        "行动引导": [
            "赶紧试试这个{method}，记得回来告诉我效果",
            "把这期内容转发给需要的朋友",
            "收藏起来，慢慢学习",
            "抓紧时间行动，别再{problem}了"
        ]
    }
    
    # 脚本结构模板
    SCRIPT_STRUCTURES = {
        "知识干货": {
            "开场": "设问引入痛点",
            "正文": "分点讲解要点",
            "案例": "实操演示展示效果",
            "总结": "要点回顾强化记忆",
            "引导": "关注话术+互动"
        },
        "口播分享": {
            "开场": "3秒抓住注意力",
            "正文": "核心内容（每5-8秒一个信息点）",
            "高潮": "反转或金句",
            "结尾": "总结+引导"
        },
        "剧情反转": {
            "铺垫": "建立常规场景",
            "冲突": "制造矛盾点",
            "反转": "出人意料的结果",
            "升华": "点题或金句"
        },
        "教程演示": {
            "开场": "展示最终效果",
            "材料": "介绍工具材料",
            "步骤": "分步骤讲解",
            "要点": "注意事项提醒",
            "结尾": "效果对比+引导"
        }
    }
    
    def __init__(self, theme: str = ""):
        self.theme = theme
    
    def generate_opening(self, opening_type: str = "痛点型", **kwargs) -> str:
        """生成黄金开头"""
        templates = self.OPENING_TEMPLATES.get(opening_type, self.OPENING_TEMPLATES["痛点型"])
        template = random.choice(templates)
        
        # 填充模板
        fill_dict = {
            "problem": kwargs.get("problem", "这个问题"),
            "method": kwargs.get("method", "这个方法"),
            "result": kwargs.get("result", "这个结果"),
            "common": kwargs.get("common", "一般人"),
            "unique": kwargs.get("unique", "我"),
            "bad": kwargs.get("bad", "做不好"),
            "field": kwargs.get("field", "这个领域"),
            "num": kwargs.get("num", "3")
        }
        
        return template.format(**fill_dict)
    
    def generate_body(self, structure_type: str = "知识干货", duration: int = 60, **kwargs) -> List[Dict]:
        """生成脚本正文"""
        structure = self.SCRIPT_STRUCTURES.get(structure_type, self.SCRIPT_STRUCTURES["知识干货"])
        
        body_points = []
        
        if structure_type == "知识干货":
            points = [
                {"time": f"0:0{5+i*10}-{0:0(5+i*10+10)}", "content": f"第{i+1}点：{kwargs.get(f'point{i+1}', '核心知识点')}", "画面": "PPT/字幕+讲解"}
                for i in range(3)
            ]
            body_points = points
        elif structure_type == "教程演示":
            steps = [
                {"time": "0:05-0:15", "content": "准备材料/工具", "画面": "全景展示"},
                {"time": "0:15-0:35", "content": "分步骤操作演示", "画面": "中景+特写切换"},
                {"time": "0:35-0:45", "content": "效果展示", "画面": "前后对比"},
                {"time": "0:45-0:50", "content": "注意事项提醒", "画面": "字幕提示"}
            ]
            body_points = steps
        elif structure_type == "口播分享":
            content_num = max(3, duration // 15)
            points = [
                {"time": f"{5+i*12}", "content": f"观点{i+1}：{kwargs.get(f'point{i+1}', '核心观点')}", "画面": "主播出镜"}
                for i in range(content_num)
            ]
            body_points = points
        
        return body_points
    
    def generate_ending(self, ending_type: str = "关注引导", **kwargs) -> str:
        """生成结尾引导"""
        templates = self.ENDING_TEMPLATES.get(ending_type, self.ENDING_TEMPLATES["关注引导"])
        template = random.choice(templates)
        
        fill_dict = {
            "field": kwargs.get("field", "这个领域"),
            "method": kwargs.get("method", "这个方法"),
            "problem": kwargs.get("problem", "拖延")
        }
        
        return template.format(**fill_dict)
    
    def generate_script(self, theme: str, duration: int = 60, script_type: str = "口播分享", **kwargs) -> Dict:
        """生成完整视频脚本"""
        result = {
            "基本信息": {
                "主题": theme,
                "时长": f"{duration}秒",
                "类型": script_type,
                "结构": self.SCRIPT_STRUCTURES.get(script_type, {})
            },
            "脚本内容": {}
        }
        
        # 生成开场
        opening_type = kwargs.get("opening_type", "痛点型")
        result["脚本内容"]["开场"] = {
            "时长": "3秒",
            "内容": self.generate_opening(opening_type, 
                                          problem=kwargs.get("problem", "效率低"),
                                          method=kwargs.get("method", "时间管理")),
            "画面": "特写/字幕"
        }
        
        # 生成正文
        body = self.generate_body(script_type, duration, **kwargs)
        result["脚本内容"]["正文"] = body
        
        # 生成结尾
        result["脚本内容"]["结尾"] = {
            "时长": "5秒",
            "内容": self.generate_ending("关注引导", field=kwargs.get("field", theme)),
            "画面": "主播+字幕"
        }
        
        # 添加BGM建议
        result["BGM建议"] = {
            "类型": kwargs.get("bgm_type", "轻快/励志"),
            "节奏": "前缓后快，高潮在结尾前10秒",
            "推荐风格": ["抖音热门BGM", "轻音乐", "正能量"]
        }
        
        # 添加拍摄要点
        result["拍摄要点"] = {
            "景别": "中景为主，重点处特写",
            "运镜": "固定+推镜头结合",
            "光线": "自然光或补光灯",
            "声音": "清晰无杂音"
        }
        
        return result
    
    def generate_oral_script(self, theme: str, duration: int = 60) -> str:
        """生成口播稿"""
        script = f"""
【口播稿】{theme}
时长：约{duration}秒

{'='*40}
【开场3秒】
{self.generate_opening("痛点型", problem="每天忙得不行，但回头看什么都没做成")}

{'='*40}
【正文】
{self.generate_opening("数字型", num="3", method="时间管理方法", result="效率翻倍")}

第一，重要紧急矩阵...
把事情分成四象限，先做重要紧急的

第二，番茄工作法...
专注25分钟，休息5分钟

第三，两分钟原则...
能两分钟解决的事，立刻做

{'='*40}
【结尾】
{self.generate_ending("关注引导", field="效率提升")}

{'='*40}
"""
        return script.strip()
    
    def generate_script_table(self, theme: str, duration: int = 60) -> List[Dict]:
        """生成分镜脚本表格"""
        table = []
        elapsed = 0
        
        # 开场
        table.append({
            "镜号": 1,
            "景别": "特写",
            "运镜": "固定",
            "画面": "人物表情+字幕",
            "台词": self.generate_opening("痛点型", problem="效率低"),
            "时长": "3s"
        })
        elapsed += 3
        
        # 正文镜头
        segment_duration = (duration - 10) // 4
        for i in range(3):
            table.append({
                "镜号": i + 2,
                "景别": random.choice(["中景", "近景", "特写"]),
                "运镜": random.choice(["固定", "推", "拉"]),
                "画面": f"第{i+1}点讲解",
                "台词": f"第{i+1}点核心内容...",
                "时长": f"{segment_duration}s"
            })
            elapsed += segment_duration
        
        # 结尾
        table.append({
            "镜号": 5,
            "景别": "中景",
            "运镜": "固定",
            "画面": "人物+字幕",
            "台词": self.generate_ending("互动引导"),
            "时长": f"{duration - elapsed}s"
        })
        
        return table


def main():
    """主函数"""
    print("=" * 60)
    print("🎬 抖音运营大师 - 视频脚本生成工具 🎬")
    print("=" * 60)
    
    generator = VideoScriptGenerator()
    
    # 1. 生成口播稿
    print("\n📝 生成口播稿:")
    print("-" * 40)
    oral_script = generator.generate_oral_script("时间管理技巧", duration=60)
    print(oral_script)
    
    # 2. 生成完整脚本
    print("\n" + "=" * 40)
    print("📋 完整视频脚本:")
    print("-" * 40)
    full_script = generator.generate_script(
        theme="职场沟通技巧",
        duration=60,
        script_type="口播分享",
        problem="说话没人听",
        method="沟通技巧",
        field="职场"
    )
    
    print(f"主题: {full_script['基本信息']['主题']}")
    print(f"时长: {full_script['基本信息']['时长']}")
    print(f"类型: {full_script['基本信息']['类型']}")
    print()
    
    print("【开场】")
    print(f"  {full_script['脚本内容']['开场']['内容']}")
    
    print("\n【分镜脚本】")
    print("-" * 40)
    print(f"{'镜号':<6}{'景别':<8}{'运镜':<8}{'画面':<15}{'时长':<6}")
    print("-" * 40)
    
    table = generator.generate_script_table("职场沟通技巧", 60)
    for row in table:
        print(f"{row['镜号']:<6}{row['景别']:<8}{row['运镜']:<8}{row['画面']:<15}{row['时长']:<6}")
    
    print("\n【结尾】")
    print(f"  {full_script['脚本内容']['结尾']['内容']}")
    
    print("\n【BGM建议】")
    print(f"  类型: {full_script['BGM建议']['类型']}")
    print(f"  节奏: {full_script['BGM建议']['节奏']}")
    
    print("\n【拍摄要点】")
    for key, value in full_script['拍摄要点'].items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ 脚本生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
