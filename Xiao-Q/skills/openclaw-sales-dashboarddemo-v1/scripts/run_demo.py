#!/usr/bin/env python3
"""
OpenClaw 销售演示 - 完整流程执行引擎
用于演示场景中一键启动并展示自动化执行效果
"""

import json
import time
import random
import sys
from datetime import datetime
from typing import Optional


class DemoFlowExecutor:
    """演示流程执行器，模拟完整的自动化流程运行效果"""
    
    # 预设演示模板
    TEMPLATES = {
        "sales-daily": {
            "name": "销售日报自动汇总",
            "description": "从 CRM 拉取销售数据 → 清洗去重 → 聚合计算 → 生成报表 → 推送企微",
            "steps": [
                {"name": "CRM数据拉取", "icon": "📥", "duration_range": (0.8, 2.0), 
                 "detail": "拉取今日销售记录"},
                {"name": "数据清洗与去重", "icon": "🧹", "duration_range": (1.5, 3.0),
                 "detail": "格式校验、字段映射、去除重复记录"},
                {"name": "聚合计算", "icon": "📊", "duration_range": (2.0, 4.0),
                 "detail": "按区域/产品线/人员分组统计"},
                {"name": "生成可视化报表", "icon": "📋", "duration_range": (1.0, 2.5),
                 "detail": "渲染 HTML 报表、导出 Excel 副本"},
                {"name": "推送通知", "icon": "📤", "duration_range": (0.5, 1.5),
                 "detail": "推送至企微群 + 邮件抄送管理层"},
            ],
            "sample_output": {
                "total_records": 1247,
                "total_amount": 3847650.00,
                "regions": ["华东区", "华南区", "华北区", "西南区", "海外"],
                "top_sales": ["张伟", "李娜", "王强", "刘洋", "陈静"],
                "conversion_rate": 23.5,
                "growth_rate": 12.8,
            }
        },
        "inventory-sync": {
            "name": "多渠道库存同步",
            "description": "WMS 读取库存 → 计算可用量 → API 批量更新各平台",
            "steps": [
                {"name": "WMS库存读取", "icon": "🏭", "duration_range": (1.0, 2.5)},
                {"name": "各平台订单锁定量计算", "icon": "🛒", "duration_range": (2.0, 4.0)},
                {"name": "可用库存计算", "icon": "🔢", "duration_range": (0.5, 1.5)},
                {"name": "API批量更新（淘宝/京东/拼多多）", "icon": "🔄", "duration_range": (3.0, 6.0)},
                {"name": "缺货SKU预警检查", "icon": "⚠️", "duration_range": (0.8, 2.0)},
                {"name": "同步日志写入", "icon": "📝", "duration_range": (0.3, 0.8)},
            ],
            "sample_output": {
                "total_skus": 3892,
                "synced_platforms": ["淘宝", "京东", "拼多多", "抖音小店", "线下门店"],
                "low_stock_count": 12,
                "out_of_stock_count": 3,
                "sync_accuracy": 99.97,
            }
        },
        "finance-monthly": {
            "name": "财务月报自动生成",
            "description": "ERP 导出 → 对账 → 合并 → 格式化 → PDF → 邮件发送",
            "steps": [
                {"name": "ERP科目余额导出", "icon": "💰", "duration_range": (3.0, 6.0)},
                {"name": "银行对账单导入与核对", "icon": "🏦", "duration_range": (5.0, 10.0)},
                {"name": "多维度数据合并", "icon": "🔗", "duration_range": (4.0, 8.0)},
                {"name": "汇率自动获取与转换", "icon": "💱", "duration_range": (1.0, 2.0)},
                {"name": "格式化三表（资产负债+利润+现金流）", "icon": "📄", "duration_range": (8.0, 15.0)},
                {"name": "PDF生成与数字签名", "icon": "✍️", "duration_range": (3.0, 6.0)},
                {"name": "邮件发送 + 归档共享盘", "icon": "📧", "duration_range": (2.0, 4.0)},
            ],
            "sample_output": {
                "report_type": "2026年03月财务月报",
                "total_revenue": 52840000.00,
                "total_cost": 34120000.00,
                "net_profit": 18720000.00,
                "profit_rate": 35.4,
                "accounts_reconciled": 342,
                "discrepancies": 0,
            }
        },
    }

    def __init__(self, template_name: str = "sales-daily", simulate_delay: bool = True):
        """
        初始化执行器
        
        Args:
            template_name: 模板名称，默认为销售日报
            simulate_delay: 是否模拟真实延迟（演示时建议开启）
        """
        self.template = self.TEMPLATES.get(template_name)
        if not self.template:
            available = ", ".join(self.TEMPLATES.keys())
            raise ValueError(f"未知模板 '{template_name}'，可选：{available}")
        
        self.template_name = template_name
        self.simulate_delay = simulate_delay
        self.start_time: Optional[datetime] = None
        self.results: list[dict] = []
        self.execution_log: list[dict] = []

    def _print_header(self):
        """打印执行头部信息"""
        print("\n" + "=" * 60)
        print(f"  🤖 OpenClaw 智能自动化助手 — 流程执行引擎")
        print("=" * 60)
        print(f"\n  📋 模板：{self.template['name']}")
        print(f"  📝 描述：{self.template['description']}")
        print(f"  ⏰ 启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  🔢 步骤总数：{len(self.template['steps'])}")
        print("\n" + "-" * 60)

    def _simulate_step(self, step_index: int, step_info: dict) -> dict:
        """模拟单步执行"""
        step_num = step_index + 1
        total_steps = len(self.template["steps"])
        
        # 模拟耗时
        lo, hi = step_info.get("duration_range", (1.0, 2.0))
        duration = random.uniform(lo, hi) if self.simulate_delay else 0.1
        
        # 打印步骤开始
        progress_pct = int((step_num / total_steps) * 100)
        print(f"\n  [{'█' * (progress_pct // 5)}{'░' * (20 - progress_pct // 5)}] "
              f"{progress_pct}%  |  步骤 {step_num}/{total_steps}")
        print(f"  {step_info['icon']} {step_info['name']}")
        if "detail" in step_info:
            print(f"     └─ {step_info['detail']}")
        
        if self.simulate_delay:
            # 显示动态进度点
            dots = 0
            start = time.time()
            while time.time() - start < duration:
                elapsed = time.time() - start
                pct = min(int((elapsed / duration) * 100), 100)
                bar_len = pct // 5
                print(f"\r     执行中 [{'█' * bar_len}{'░' * (20 - bar_len)}] {pct}%"
                      "   ", end="", flush=True)
                time.sleep(0.1)
            print()  # 换行
        
        # 随机生成处理数据量（基于步骤索引递减模拟数据清洗）
        base_count = random.randint(500, 5000)
        record_count = base_count if step_index == 0 else \
                      int(base_count * random.uniform(0.85, 0.98))
        
        result = {
            "step": step_num,
            "name": step_info["name"],
            "status": "success",
            "duration_seconds": round(duration, 2),
            "records_processed": record_count if step_index == 0 else random.randint(100, record_count),
            "timestamp": datetime.now().isoformat(),
        }
        
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"     └─ {status_icon} 完成 · 耗时 {result['duration_seconds']}s "
              f"· 处理 {result.get('records_processed', 'N/A'):,} 条")
        
        return result

    def execute(self) -> dict:
        """执行完整流程"""
        self._print_header()
        self.start_time = datetime.now()
        self.results = []
        self.execution_log = []

        for i, step in enumerate(self.template["steps"]):
            result = self._simulate_step(i, step)
            self.results.append(result)
            self.execution_log.append(result)

        total_duration = (datetime.now() - self.start_time).total_seconds()

        # 输出总结
        print("\n" + "-" * 60)
        print("  ✨ 执行完成！")
        print(f"  ⏱️ 总耗时：{total_duration:.1f}s")
        print(f"  📊 成功率：{len([r for r in self.results if r['status']=='success'])}/{len(self.results)}")
        
        output = {
            "template": self.template_name,
            "flow_name": self.template["name"],
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration_seconds": round(total_duration, 2),
            "steps_result": self.results,
            "output_data": self.template.get("sample_output", {}),
            "summary": {
                "total_steps": len(self.results),
                "success_count": len([r for r in self.results if r["status"] == "success"]),
                "avg_step_duration": round(
                    sum(r["duration_seconds"] for r in self.results) / len(self.results), 2
                ),
            }
        }

        return output

    def generate_report_markdown(self, execution_result: dict) -> str:
        """根据执行结果生成 Markdown 格式的报告"""
        o = execution_result["output_data"]
        sr = execution_result["summary"]
        
        md = f"""# 📊 {execution_result['flow_name']} — 执行报告

> 生成时间：{execution_result['end_time']}  
> 总耗时：{execution_result['total_duration_seconds']}s | 成功率：{sr['success_count']}/{sr['total_steps']}

---

## 执行概览

| 指标 | 数值 |
|------|------|
| 模板名称 | {execution_result['flow_name']} |
| 启动时间 | {execution_result['start_time']} |
| 结束时间 | {execution_result['end_time']} |
| 总耗时 | **{execution_result['total_duration_seconds']}s** |
| 成功步骤 | **{sr['success_count']}/{sr['total_steps']}** |
| 平均步耗时 | {sr['avg_step_duration']}s |

## 执行详情

| # | 步骤名称 | 状态 | 耗时 | 处理记录数 |
|---|---------|------|------|-----------|
"""
        for r in execution_result["steps_result"]:
            icon = "✅" if r["status"] == "success" else "❌"
            md += f"| {r['step']} | {r['name']} | {icon} | {r['duration_seconds']}s | {r.get('records_processed', '-'):,} |\n"

        md += "\n## 输出数据\n\n"
        for key, value in o.items():
            if isinstance(value, float):
                formatted = f"¥{value:,.2f}" if value > 100 else f"{value}%"
            elif isinstance(value, list):
                formatted = "、".join(str(v) for v in value)
            else:
                formatted = str(value)
            md += f"- **{key}**：{formatted}\n"

        md += """
---

*报告由 OpenClaw 智能自动化助手自动生成*
"""
        return md


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 演示流程执行引擎")
    parser.add_argument(
        "-t", "--template",
        choices=list(DemoFlowExecutor.TEMPLATES.keys()),
        default="sales-daily",
        help="选择演示模板（默认：sales-daily）"
    )
    parser.add_argument(
        "--no-delay",
        action="store_true",
        help="跳过延迟模拟，快速执行"
    )
    parser.add_argument(
        "-o", "--output",
        help="将结果输出到指定 JSON 文件"
    )
    parser.add_argument(
        "--report",
        help="将报告输出到指定 Markdown 文件"
    )
    
    args = parser.parse_args()
    
    executor = DemoFlowExecutor(
        template_name=args.template,
        simulate_delay=not args.no_delay
    )
    
    result = executor.execute()
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n  💾 结果已保存至：{args.output}")
    
    if args.report:
        report_md = executor.generate_report_markdown(result)
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"  📄 报告已保存至：{args.report}")

    return result


if __name__ == "__main__":
    main()
