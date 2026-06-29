#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音运营大师 - 直播话术脚本
功能：生成开场话术、产品话术、促单话术、互动话术、直播脚本
"""

import random
from typing import Dict, List, Optional


class LiveStreamScriptGenerator:
    """直播话术生成器"""
    
    # 开场话术模板
    OPENING_SCRIPTS = {
        "暖场": [
            "欢迎{username}进入直播间！（读名字）感谢关注！",
            "刚进来的小伙伴打个招呼～今天直播间有{benefit}，先别走开！",
            "欢迎{username}，你是第{count}个进来的，太给力了！",
            '来来来，新进来的家人们把"到我"打在评论区！'
        ],
        "价值预告": [
            "今天给大家带来{count}款{product}，{benefit}！",
            "直播间专属价，只有今天有！错过不再来！",
            "今天准备了很多{product}，保证让你们买到赚到！",
            "家人们，今天我们直播间有{activity}，力度超级大！"
        ],
        "互动": [
            "刚进来的扣个1，让我看看有多少人！",
            "觉得今天福利可以的扣666！",
            "想要{product}的扣想要！",
            '来，把"想要"打在公屏上！'
        ]
    }
    
    # 产品话术模板
    PRODUCT_SCRIPTS = {
        "痛点引入": [
            "你们是不是也有{problem}的烦恼？",
            "之前很多粉丝问我，{problem}怎么办？",
            "今天就给你们解决{problem}这个问题！"
        ],
        "产品介绍": [
            "今天给大家介绍这款{product}，它有{count}个亮点：",
            "来来来，给大家看看这个{product}，这是我们{feature}的{product}！",
            "这款{product}是我们今年的爆款，好多明星都在用！"
        ],
        "卖点讲解": [
            "第一，{feature1}，解决你的{problem1}！",
            "第二，{feature2}，{benefit2}！",
            "第三，{feature3}，现在下单还送{gift}！"
        ],
        "效果展示": [
            "看看用过的粉丝怎么说...（展示评论）",
            "这是我们实拍的效果图，真的{result}！",
            "你们看，这是使用前和使用后的对比！（展示）"
        ],
        "价格包装": [
            "官方价{original_price}，今天直播间专属价只要{price}！",
            "今天不要{original_price}，也不要{price}，只要{final_price}！",
            "直播间价格历史最低，错过要等一年！"
        ]
    }
    
    # 促单话术模板
    PROMOTE_SCRIPTS = {
        "紧迫感": [
            "库存只剩{count}件了！",
            "价格只限今天直播间！",
            "这波福利结束就没了！",
            "最后{time}分钟！抓紧下单！"
        ],
        "限量": [
            "每个ID限购{count}件！",
            "今天只准备了{count}份！抢完为止！",
            "限量{count}件，先到先得！"
        ],
        "福利": [
            "拍2件送{gift1}，拍3件送{gift2}！",
            "今天下单的粉丝额外送{gift}！",
            "现在下单的粉丝参与抽奖，100%中奖！"
        ],
        "从众": [
            "已经{count}人下单了！",
            "刚才那个姐姐一下拍了{count}件！",
            "后台显示又有{count}人下单了！"
        ]
    }
    
    # 互动话术模板
    INTERACTION_SCRIPTS = {
        "抽奖": [
            "点赞到{count}抽{gift}！",
            "关注主播参与抽奖，{gift}免费送！",
            "扣666参与抽奖，下一个幸运儿就是你！"
        ],
        "问答": [
            "有什么问题打在公屏上！",
            "{question}问得最多，给大家统一回复...",
            "来，专业的问题我来回答..."
        ],
        "引导": [
            "帮主播点点关注，下期更精彩！",
            "关注主播，每天分享{content}！",
            "加入粉丝团还有{gift}送！"
        ]
    }
    
    # 感谢话术
    THANK_SCRIPTS = [
        "感谢{count}位来到直播间！",
        "感谢{username}的关注！",
        "感谢家人们今天的陪伴！",
        "今天的直播就到这里，下期见！",
        "拜拜～记得点关注不迷路！"
    ]
    
    def __init__(self, host_name: str = "主播"):
        self.host_name = host_name
    
    def generate_opening(self, script_type: str = "暖场", **kwargs) -> str:
        """生成开场话术"""
        templates = self.OPENING_SCRIPTS.get(script_type, self.OPENING_SCRIPTS["暖场"])
        template = random.choice(templates)
        
        fill_dict = {
            "username": kwargs.get("username", "家人"),
            "benefit": kwargs.get("benefit", "超多福利"),
            "count": kwargs.get("count", "5"),
            "product": kwargs.get("product", "好物"),
            "activity": kwargs.get("activity", "大促活动")
        }
        
        return template.format(**fill_dict)
    
    def generate_product_script(self, product: Dict) -> str:
        """生成完整产品话术"""
        script = []
        
        # 痛点引入
        script.append("【痛点引入】")
        template = random.choice(self.PRODUCT_SCRIPTS["痛点引入"])
        script.append(template.format(problem=product.get("problem", "这个问题")))
        
        # 产品介绍
        script.append("\n【产品介绍】")
        template = random.choice(self.PRODUCT_SCRIPTS["产品介绍"])
        script.append(template.format(
            product=product.get("name", "产品"),
            count=len(product.get("features", ["亮点1", "亮点2", "亮点3"])),
            feature=product.get("highlight", "主打")
        ))
        
        # 卖点讲解
        script.append("\n【卖点讲解】")
        features = product.get("features", ["亮点1", "亮点2", "亮点3"])
        for i, feature in enumerate(features[:3], 1):
            template = random.choice(self.PRODUCT_SCRIPTS["卖点讲解"])
            script.append(template.format(
                feature1=feature,
                problem1=product.get("problem", "需求"),
                feature2=feature,
                benefit2="效果很好",
                feature3=feature,
                gift="配件礼包"
            ))
        
        # 效果展示
        script.append("\n【效果展示】")
        template = random.choice(self.PRODUCT_SCRIPTS["效果展示"])
        script.append(template.format(result=product.get("result", "非常棒")))
        
        # 价格包装
        script.append("\n【价格包装】")
        template = random.choice(self.PRODUCT_SCRIPTS["价格包装"])
        script.append(template.format(
            original_price=product.get("original_price", "99"),
            price=product.get("price", "59"),
            final_price=product.get("final_price", "49")
        ))
        
        return "\n".join(script)
    
    def generate_promote_script(self, promote_type: str = "紧迫感", **kwargs) -> str:
        """生成促单话术"""
        templates = self.PROMOTE_SCRIPTS.get(promote_type, self.PROMOTE_SCRIPTS["紧迫感"])
        template = random.choice(templates)
        
        fill_dict = {
            "count": kwargs.get("count", "10"),
            "time": kwargs.get("time", "5"),
            "gift": kwargs.get("gift", "精美礼品"),
            "gift1": kwargs.get("gift1", "配件"),
            "gift2": kwargs.get("gift2", "礼包")
        }
        
        return template.format(**fill_dict)
    
    def generate_interaction_script(self, interaction_type: str = "抽奖", **kwargs) -> str:
        """生成互动话术"""
        templates = self.INTERACTION_SCRIPTS.get(interaction_type, self.INTERACTION_SCRIPTS["抽奖"])
        template = random.choice(templates)
        
        fill_dict = {
            "count": kwargs.get("count", "1000"),
            "gift": kwargs.get("gift", "神秘大奖"),
            "question": kwargs.get("question", "价格"),
            "content": kwargs.get("content", "实用干货")
        }
        
        return template.format(**fill_dict)
    
    def generate_full_live_script(self, duration: int = 120, products: List[Dict] = None) -> Dict:
        """生成完整直播脚本"""
        if products is None:
            products = [
                {"name": "引流款产品", "problem": "想要省钱", "original_price": 99, "price": 29},
                {"name": "主推款产品", "problem": "品质要好", "original_price": 299, "price": 199},
                {"name": "利润款产品", "problem": "性价比", "original_price": 199, "price": 129}
            ]
        
        script = {
            "基本信息": {
                "直播时长": f"{duration}分钟",
                "产品数量": len(products),
                "脚本结构": "开场→引流款→主推款→利润款→收尾"
            },
            "时间节点": {}
        }
        
        # 开场暖场 0-10分钟
        script["时间节点"]["0-10分钟"] = {
            "阶段": "开场暖场",
            "目标": "留人、预热",
            "话术": [
                self.generate_opening("暖场", benefit="超多福利"),
                self.generate_opening("价值预告", product="好物", activity="大促"),
                self.generate_opening("互动")
            ]
        }
        
        # 引流款 10-30分钟
        script["时间节点"]["10-30分钟"] = {
            "阶段": "引流款讲解",
            "产品": products[0]["name"] if len(products) > 0 else "引流款",
            "话术": [
                self.generate_product_script(products[0] if len(products) > 0 else {}),
                self.generate_promote_script("紧迫感", count="50"),
                self.generate_promote_script("福利", gift="精美配件")
            ]
        }
        
        # 主推款 30-60分钟
        script["时间节点"]["30-60分钟"] = {
            "阶段": "主推款讲解",
            "产品": products[1]["name"] if len(products) > 1 else "主推款",
            "话术": [
                self.generate_product_script(products[1] if len(products) > 1 else {}),
                self.generate_promote_script("限量", count="30"),
                self.generate_interaction_script("抽奖", count="5000", gift="免单")
            ]
        }
        
        # 福利抽奖 60-70分钟
        script["时间节点"]["60-70分钟"] = {
            "阶段": "福利抽奖",
            "目标": "活跃气氛、增加互动",
            "话术": [
                self.generate_interaction_script("抽奖", count="10000", gift="大礼包"),
                self.generate_interaction_script("互动"),
                "来，把666打在公屏上！"
            ]
        }
        
        # 利润款 70-100分钟
        script["时间节点"]["70-100分钟"] = {
            "阶段": "利润款讲解",
            "产品": products[2]["name"] if len(products) > 2 else "利润款",
            "话术": [
                self.generate_product_script(products[2] if len(products) > 2 else {}),
                self.generate_promote_script("从众", count="50"),
                self.generate_promote_script("紧迫感", time="10")
            ]
        }
        
        # 逼单收尾 100-120分钟
        script["时间节点"]["100-120分钟"] = {
            "阶段": "逼单收尾",
            "目标": "促成下单",
            "话术": [
                "最后倒计时！5...4...3...2...1...！",
                self.generate_promote_script("紧迫感", count="10"),
                "还在犹豫什么！直接下单！"
            ]
        }
        
        # 感谢下播
        script["时间节点"]["下播"] = {
            "阶段": "感谢下播",
            "话术": self.THANK_SCRIPTS
        }
        
        return script
    
    def generate_control_script(self) -> Dict:
        """生成控场技巧"""
        return {
            "冷场应对": {
                "方法": ["抛问题", "送福利", "换产品", "讲故事", "请助理配合"],
                "话术": [
                    "大家觉得这个价格贵不贵？",
                    "来，点赞到XXX抽免单！",
                    "我们先来看下一款..."
                ]
            },
            "突发状况": {
                "产品缺货": {
                    "话术": "XX卖完了，老板加库存！",
                    "备选": "给大家推荐另一款..."
                },
                "价格报错": {
                    "话术": "抱歉，刚才价格报错，以现在这个为准！",
                    "处理": "第一时间承认，不要拖延"
                },
                "负面弹幕": {
                    "话术": "忽略或转移话题",
                    "注意": "不要正面回应，不要争论"
                },
                "网络卡顿": {
                    "话术": "网络有点卡，稍等一下",
                    "备选": "准备录制的备用视频"
                }
            },
            "状态调整": {
                "疲惫时": ["深呼吸调整", "喝口水休息", "换首歌调动情绪"],
                "紧张时": ["放慢语速", "对着镜头微笑", "想象观众是朋友"]
            }
        }


def main():
    """主函数"""
    print("=" * 60)
    print("🎬 抖音运营大师 - 直播话术工具 🎬")
    print("=" * 60)
    
    generator = LiveStreamScriptGenerator()
    
    # 1. 开场话术
    print("\n📢 开场话术:")
    print("-" * 40)
    print("【暖场】")
    print(f"  {generator.generate_opening('暖场', username='新进来的家人', benefit='超多福利')}")
    print(f"\n【价值预告】")
    print(f"  {generator.generate_opening('价值预告', product='美妆好物', count='5', activity='母亲节大促')}")
    print(f"\n【互动】")
    print(f"  {generator.generate_opening('互动', product='这款产品')}")
    
    # 2. 产品话术
    print("\n\n💄 产品话术示例:")
    print("-" * 40)
    product = {
        "name": "保湿面霜",
        "problem": "皮肤干燥起皮",
        "features": ["深层补水", "持久保湿", "温和不刺激"],
        "original_price": "199",
        "price": "99",
        "final_price": "79",
        "result": "皮肤水润有光泽"
    }
    print(generator.generate_product_script(product))
    
    # 3. 促单话术
    print("\n\n💰 促单话术:")
    print("-" * 40)
    print(f"【紧迫感】")
    print(f"  {generator.generate_promote_script('紧迫感', count='20', time='5分钟')}")
    print(f"\n【限量】")
    print(f"  {generator.generate_promote_script('限量', count='50')}")
    print(f"\n【福利】")
    print(f"  {generator.generate_promote_script('福利', gift1='化妆包', gift2='豪华礼包')}")
    print(f"\n【从众】")
    print(f"  {generator.generate_promote_script('从众', count='30')}")
    
    # 4. 互动话术
    print("\n\n🎉 互动话术:")
    print("-" * 40)
    print(f"【抽奖】")
    print(f"  {generator.generate_interaction_script('抽奖', count='10000', gift='免单大奖')}")
    print(f"\n【问答】")
    print(f"  {generator.generate_interaction_script('问答', question='效果')}")
    print(f"\n【引导】")
    print(f"  {generator.generate_interaction_script('引导', content='美妆技巧')}")
    
    # 5. 完整直播脚本
    print("\n\n📋 2小时直播脚本:")
    print("-" * 40)
    live_script = generator.generate_full_live_script(duration=120)
    print(f"  直播时长: {live_script['基本信息']['直播时长']}")
    print(f"  产品数量: {live_script['基本信息']['产品数量']}")
    print(f"  脚本结构: {live_script['基本信息']['脚本结构']}")
    
    print("\n  时间节点:")
    for time_range, details in live_script["时间节点"].items():
        if time_range != "下播":
            print(f"\n    [{time_range}] {details['阶段']}")
            if "产品" in details:
                print(f"      产品: {details['产品']}")
    
    # 6. 控场技巧
    print("\n\n🎯 控场技巧:")
    print("-" * 40)
    control = generator.generate_control_script()
    print("【冷场应对】")
    print(f"  方法: {', '.join(control['冷场应对']['方法'])}")
    print("【突发状况处理】")
    for situation, solution in control['突发状况'].items():
        if isinstance(solution, dict):
            print(f"  {situation}: {solution.get('话术', solution)}")
    
    print("\n" + "=" * 60)
    print("✅ 话术生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
