#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音运营大师 - 直播复盘脚本
功能：数据复盘、话术复盘、货品复盘、问题诊断、改进建议
"""

import random
from datetime import datetime
from typing import Dict, List, Optional


class LiveStreamReview:
    """直播复盘工具"""
    
    def __init__(self):
        self.review_data = {}
    
    def input_live_data(self, basic_data: Dict) -> None:
        """输入直播基础数据"""
        self.review_data["基本信息"] = {
            "直播日期": basic_data.get("日期", datetime.now().strftime("%Y-%m-%d")),
            "直播时长": basic_data.get("时长", "2小时"),
            "GMV目标": basic_data.get("GMV目标", 0),
            "实际GMV": basic_data.get("实际GMV", 0),
            "在线峰值": basic_data.get("在线峰值", 0),
            "平均在线": basic_data.get("平均在线", 0),
            "观看人数": basic_data.get("观看人数", 0),
            "下单人数": basic_data.get("下单人数", 0),
            "客单价": basic_data.get("客单价", 0),
            "退货率": basic_data.get("退货率", 0)
        }
    
    def input_product_data(self, products: List[Dict]) -> None:
        """输入商品数据"""
        self.review_data["商品数据"] = products
    
    def input_script_review(self, script_review: Dict) -> None:
        """输入话术复盘数据"""
        self.review_data["话术复盘"] = script_review
    
    def calculate_data_review(self) -> Dict:
        """计算数据复盘"""
        basic = self.review_data.get("基本信息", {})
        
        gmv_target = basic.get("GMV目标", 1)
        gmv_actual = basic.get("实际GMV", 0)
        gmv_rate = (gmv_actual / gmv_target * 100) if gmv_target > 0 else 0
        
        viewers = basic.get("观看人数", 1)
        orders = basic.get("下单人数", 0)
        conversion_rate = (orders / viewers * 100) if viewers > 0 else 0
        
        return {
            "数据复盘": {
                "GMV": {
                    "目标": f"¥{gmv_target:,.0f}",
                    "实际": f"¥{gmv_actual:,.0f}",
                    "完成率": f"{gmv_rate:.1f}%",
                    "状态": self._get_status(gmv_rate, 100)
                },
                "在线数据": {
                    "峰值": f"{basic.get('在线峰值', 0)}人",
                    "均值": f"{basic.get('平均在线', 0)}人",
                    "分析": self._analyze_online_data(basic.get('在线峰值', 0), basic.get('平均在线', 0))
                },
                "转化": {
                    "观看人数": basic.get('观看人数', 0),
                    "下单人数": orders,
                    "转化率": f"{conversion_rate:.2f}%",
                    "客单价": f"¥{basic.get('客单价', 0):.2f}",
                    "状态": self._get_status(conversion_rate, 5)
                },
                "退货": {
                    "退货率": f"{basic.get('退货率', 0):.1f}%",
                    "分析": "正常范围" if basic.get('退货率', 0) < 15 else "偏高，需关注"
                }
            }
        }
    
    def _get_status(self, value: float, target: float) -> str:
        """获取状态"""
        rate = (value / target * 100) if target > 0 else 0
        if rate >= 100:
            return "✅ 达标"
        elif rate >= 80:
            return "⚠️ 接近"
        else:
            return "❌ 未达标"
    
    def _analyze_online_data(self, peak: int, avg: int) -> str:
        """分析在线数据"""
        if peak == 0:
            return "数据异常"
        ratio = avg / peak
        if ratio >= 0.5:
            return "留存良好，粉丝粘性高"
        elif ratio >= 0.3:
            return "留存一般，有提升空间"
        else:
            return "流失较快，需优化内容和节奏"
    
    def calculate_product_review(self) -> Dict:
        """计算货品复盘"""
        products = self.review_data.get("商品数据", [])
        
        if not products:
            # 生成模拟数据
            products = [
                {"name": "引流款A", "sales": 500, "gmv": 15000, "转化率": 15.2},
                {"name": "主推款B", "sales": 200, "gmv": 40000, "转化率": 8.5},
                {"name": "利润款C", "sales": 80, "gmv": 12000, "转化率": 3.2},
                {"name": "滞销款D", "sales": 10, "gmv": 500, "转化率": 0.5}
            ]
        
        total_gmv = sum(p.get("gmv", 0) for p in products)
        
        product_analysis = []
        for p in products:
            gmv_ratio = (p.get("gmv", 0) / total_gmv * 100) if total_gmv > 0 else 0
            product_analysis.append({
                "商品": p.get("name", "商品"),
                "销量": p.get("sales", 0),
                "销售额": f"¥{p.get('gmv', 0):,.0f}",
                "GMV占比": f"{gmv_ratio:.1f}%",
                "转化率": f"{p.get('转化率', 0):.1f}%",
                "状态": self._get_product_status(p.get("转化率", 0))
            })
        
        # 排序
        product_analysis = sorted(product_analysis, key=lambda x: int(x["销售额"].replace("¥", "").replace(",", "")), reverse=True)
        
        return {
            "货品复盘": {
                "总商品数": len(products),
                "总销售额": f"¥{total_gmv:,.0f}",
                "TOP商品": product_analysis[:2],
                "滞销商品": [p for p in product_analysis if "滞销" in p["状态"] or "低" in p["状态"]],
                "选品建议": self._get_product_suggestions(product_analysis)
            }
        }
    
    def _get_product_status(self, conversion_rate: float) -> str:
        """获取商品状态"""
        if conversion_rate >= 10:
            return "🔥 爆款"
        elif conversion_rate >= 5:
            return "✅ 正常"
        elif conversion_rate >= 2:
            return "⚠️ 低转化"
        else:
            return "❌ 滞销"
    
    def _get_product_suggestions(self, products: List[Dict]) -> List[str]:
        """获取选品建议"""
        suggestions = []
        
        # 爆款建议
        hot_products = [p for p in products if "爆款" in p["状态"]]
        if hot_products:
            suggestions.append(f"继续主推: {', '.join(p['商品'] for p in hot_products)}")
        
        # 滞销建议
        cold_products = [p for p in products if "滞销" in p["状态"]]
        if cold_products:
            suggestions.append(f"优化或下架: {', '.join(p['商品'] for p in cold_products)}")
        
        return suggestions
    
    def calculate_script_review(self) -> Dict:
        """计算话术复盘"""
        script_review = self.review_data.get("话术复盘", {})
        
        # 模拟话术数据
        effective_scripts = script_review.get("有效话术", [
            {"话术": "价格对比话术", "效果": "转化提升20%"},
            {"话术": "限时限量话术", "效果": "促单成功率提升"}
        ])
        
        ineffective_scripts = script_review.get("无效话术", [
            {"话术": "过于复杂的讲解", "问题": "用户流失"}
        ])
        
        return {
            "话术复盘": {
                "有效话术": effective_scripts,
                "无效话术": ineffective_scripts,
                "改进点": [
                    "讲解节奏可以更快",
                    "促单时机要更精准",
                    "互动频率要提高"
                ]
            }
        }
    
    def generate_diagnosis(self) -> Dict:
        """生成问题诊断"""
        return {
            "问题诊断": {
                "人员配合": {
                    "状态": "✅ 良好",
                    "问题": [],
                    "建议": ["继续优化配合默契"]
                },
                "话术问题": {
                    "状态": "⚠️ 有待改进",
                    "问题": [
                        "部分话术转化效果一般",
                        "促单节奏需要调整"
                    ],
                    "建议": [
                        "精简话术，突出卖点",
                        "增加促单频次"
                    ]
                },
                "产品问题": {
                    "状态": "⚠️ 需优化",
                    "问题": [
                        "个别商品转化率低",
                        "库存准备不足"
                    ],
                    "建议": [
                        "下次精选转化率高的品",
                        "提前备足库存"
                    ]
                },
                "场景问题": {
                    "状态": "✅ 良好",
                    "问题": [],
                    "建议": ["保持当前场景布置"]
                },
                "流量问题": {
                    "状态": "⚠️ 需关注",
                    "问题": [
                        "开场流量较少",
                        "引流款承接不够好"
                    ],
                    "建议": [
                        "提前发布预热视频",
                        "优化引流款讲解"
                    ]
                }
            }
        }
    
    def generate_improvement_plan(self) -> Dict:
        """生成改进计划"""
        return {
            "下次改进计划": {
                "话术调整": [
                    "精简产品讲解，每款控制在3分钟内",
                    "增加促单话术频次，每10分钟促单一次",
                    "优化开场话术，提升留人能力"
                ],
                "选品调整": [
                    "增加引流款数量至2-3款",
                    "下架转化率低于2%的商品",
                    "提前测试新品反应"
                ],
                "流程优化": [
                    "固定时间节点，严格把控节奏",
                    "增加粉丝互动环节",
                    "优化抽奖时间安排"
                ],
                "人员配合": [
                    "明确分工，各司其职",
                    "增加场控培训",
                    "优化助理配合话术"
                ],
                "目标设定": {
                    "GMV目标": "在本次基础上提升20%",
                    "在线峰值": "突破本次峰值50%",
                    "转化率": "整体提升至5%以上",
                    "客单价": "提升至¥150以上"
                }
            }
        }
    
    def generate_full_review_report(self) -> Dict:
        """生成完整复盘报告"""
        return {
            "直播复盘报告": {
                "报告时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "基本信息": self.review_data.get("基本信息", {}),
                **self.calculate_data_review(),
                **self.calculate_product_review(),
                **self.calculate_script_review(),
                **self.generate_diagnosis(),
                **self.generate_improvement_plan()
            }
        }
    
    def generate_review_template(self) -> str:
        """生成复盘模板"""
        return """
【直播复盘模板】

【基本信息】
- 直播日期：
- 直播时长：
- GMV目标：
- 实际GMV：

【数据复盘】
- GMV目标完成率：___%（目标___元，实际___元）
- 在线峰值：___人
- 平均在线：___人
- 观看人数：___人（UV）
- 转化率：___%（下单人数/观看人数）
- 客单价：___元
- 退货率：___%

【话术复盘】
- 有效话术：
  * 「___话术」 → 转化___单
  * 「___话术」 → 互动增加___%
- 无效话术：
  * 「___话术」 → 无人响应
- 改进点：
  1. ...
  2. ...

【货品复盘】
- 爆款：___（占GMV ___%）
- 滞销：___（需下架或优化）
- 库存问题：___
- 选品调整：

【互动复盘】
- 高光时刻：___分钟峰值在线
- 互动峰值：___分钟弹幕最多

【下次改进】
1. 话术调整：...
2. 选品调整：...
3. 流程优化：...
4. 人员配合：...
"""


def main():
    """主函数"""
    print("=" * 60)
    print("📋 抖音运营大师 - 直播复盘工具 📋")
    print("=" * 60)
    
    review = LiveStreamReview()
    
    # 1. 输入数据
    print("\n📝 输入直播数据...")
    review.input_live_data({
        "日期": "2024-05-15",
        "时长": "2小时",
        "GMV目标": 50000,
        "实际GMV": 58000,
        "在线峰值": 850,
        "平均在线": 420,
        "观看人数": 12500,
        "下单人数": 380,
        "客单价": 152.63,
        "退货率": 8.5
    })
    
    review.input_script_review({
        "有效话术": [
            {"话术": "价格对比话术", "效果": "转化提升20%"},
            {"话术": "限时限量话术", "效果": "促单成功率提升"}
        ],
        "无效话术": [
            {"话术": "过于复杂的讲解", "问题": "用户流失"}
        ]
    })
    
    print("  ✅ 数据已录入")
    
    # 2. 数据复盘
    print("\n📊 数据复盘:")
    print("-" * 40)
    data_review = review.calculate_data_review()["数据复盘"]
    
    print(f"  【GMV】")
    print(f"    目标: {data_review['GMV']['目标']}")
    print(f"    实际: {data_review['GMV']['实际']}")
    print(f"    完成率: {data_review['GMV']['完成率']} {data_review['GMV']['状态']}")
    
    print(f"\n  【在线数据】")
    print(f"    峰值: {data_review['在线数据']['峰值']}")
    print(f"    均值: {data_review['在线数据']['均值']}")
    print(f"    分析: {data_review['在线数据']['分析']}")
    
    print(f"\n  【转化】")
    print(f"    观看人数: {data_review['转化']['观看人数']}")
    print(f"    下单人数: {data_review['转化']['下单人数']}")
    print(f"    转化率: {data_review['转化']['转化率']} {data_review['转化']['状态']}")
    print(f"    客单价: {data_review['转化']['客单价']}")
    
    # 3. 货品复盘
    print("\n📦 货品复盘:")
    print("-" * 40)
    product_review = review.calculate_product_review()["货品复盘"]
    print(f"  总销售额: {product_review['总销售额']}")
    
    print("\n  TOP商品:")
    for p in product_review["TOP商品"]:
        print(f"    {p['商品']}: {p['销售额']} ({p['GMV占比']}) {p['状态']}")
    
    print("\n  选品建议:")
    for suggestion in product_review['选品建议']:
        print(f"    • {suggestion}")
    
    # 4. 话术复盘
    print("\n🗣️ 话术复盘:")
    print("-" * 40)
    script_review = review.calculate_script_review()["话术复盘"]
    
    print("  有效话术:")
    for s in script_review["有效话术"]:
        print(f"    ✅ {s['话术']}: {s['效果']}")
    
    print("\n  无效话术:")
    for s in script_review["无效话术"]:
        print(f"    ❌ {s['话术']}: {s['问题']}")
    
    print("\n  改进点:")
    for point in script_review["改进点"]:
        print(f"    • {point}")
    
    # 5. 问题诊断
    print("\n🔍 问题诊断:")
    print("-" * 40)
    diagnosis = review.generate_diagnosis()["问题诊断"]
    
    for category, details in diagnosis.items():
        print(f"\n  【{category}】{details['状态']}")
        if details.get('问题'):
            print(f"    问题: {', '.join(details['问题'])}")
        if details.get('建议'):
            print(f"    建议: {', '.join(details['建议'][:2])}")
    
    # 6. 改进计划
    print("\n🚀 改进计划:")
    print("-" * 40)
    improvement = review.generate_improvement_plan()["下次改进计划"]
    
    for category, items in improvement.items():
        if isinstance(items, list) and category != "目标设定":
            print(f"\n  【{category}】")
            for i, item in enumerate(items[:3], 1):
                print(f"    {i}. {item}")
        elif isinstance(items, dict):
            print(f"\n  【{category}】")
            for key, value in items.items():
                print(f"    {key}: {value}")
    
    # 7. 完整报告
    print("\n📑 完整复盘报告:")
    print("-" * 40)
    full_report = review.generate_full_review_report()
    print(f"  报告时间: {full_report['直播复盘报告']['报告时间']}")
    print(f"  GMV完成率: {full_report['直播复盘报告']['数据复盘']['GMV']['完成率']}")
    print(f"  转化率: {full_report['直播复盘报告']['数据复盘']['转化']['转化率']}")
    
    print("\n" + "=" * 60)
    print("✅ 复盘完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
