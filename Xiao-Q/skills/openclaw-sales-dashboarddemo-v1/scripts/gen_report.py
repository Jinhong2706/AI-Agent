#!/usr/bin/env python3
"""
OpenClaw 销售演示 - 业务报表生成器
根据场景自动生成逼真的业务报表（HTML/PDF/Excel 格式）
"""

import json
import random
import sys
import os
from datetime import datetime, timedelta
from typing import Optional


class ReportGenerator:
    """业务报表生成器，支持多种行业场景"""

    # 场景数据模板库
    SCENARIOS = {
        "sales": {
            "title": "销售日报",
            "headers": ["区域", "签约金额(万)", "目标完成率", "新增线索", "转化率", "环比增长"],
            "regions": [
                "华东区", "华南区", "华北区", "西南区", "华中区", "东北区", "海外"
            ],
            "generate_row": lambda region, i: {
                "区域": region,
                "签约金额(万)": round(random.uniform(80, 500), 1),
                "目标完成率": f"{random.randint(65, 135)}%",
                "新增线索": random.randint(15, 120),
                "转化率": f"{round(random.uniform(12, 35), 1)}%",
                "环比增长": f"{random.choice(['+', '-'])}{random.uniform(2, 25):.1f}%",
            }
        },
        "finance": {
            "title": "财务月报摘要",
            "headers": ["科目", "本月发生额(万)", "累计发生额(万)", "预算执行率", "同比变动"],
            "items": [
                "营业收入", "营业成本", "销售费用", "管理费用",
                "研发费用", "财务费用", "利润总额", "净利润",
                "经营现金流", "投资现金流", "筹资现金流"
            ],
            "generate_row": lambda item, i: {
                "科目": item,
                "本月发生额(万)": round(random.uniform(50, 3000), 1),
                "累计发生额(万)": round(random.uniform(200, 15000), 1),
                "预算执行率": f"{random.randint(45, 115)}%",
                "同比变动": f"{random.choice(['+', '-'])}{random.uniform(3, 30):.1f}%",
            }
        },
        "operations": {
            "title": "运营数据看板",
            "headers": ["平台", "GMV(万)", "订单量", "客单价", "退款率", "ROI"],
            "platforms": ["淘宝天猫", "京东", "拼多多", "抖音电商", "小红书", "微信小程序"],
            "generate_row": lambda platform, i: {
                "平台": platform,
                "GMV(万)": round(random.uniform(30, 400), 1),
                "订单量": random.randint(200, 8000),
                "客单价": round(random.uniform(80, 600), 0),
                "退款率": f"{round(random.uniform(0.5, 6), 2)}%",
                "ROI": f"{random.uniform(1.2, 4.8):.2f}",
            }
        },
        "inventory": {
            "title": "库存同步报告",
            "headers": ["SKU编码", "商品名称", "WMS库存", "可用库存", "锁定数量", "状态"],
            "products": [
                ("SKU001", "智能手表Pro Max"),
                ("SKU002", "无线蓝牙耳机X3"),
                ("SKU003", "便携充电宝20000mAh"),
                ("SKU004", "机械键盘RGB版"),
                ("SKU005", "4K高清摄像头"),
                ("SKU006", "智能家居中控屏"),
                ("SKU007", "运动手环Lite"),
                ("SKU008", "Type-C扩展坞"),
                ("SKU009", "降噪耳罩式耳机"),
                ("SKU010", "桌面台灯护眼版"),
            ],
            "generate_row": lambda sku_name, i: {
                "SKU编码": sku_name[0],
                "商品名称": sku_name[1],
                "WMS库存": random.randint(50, 5000),
                "可用库存": random.randint(10, 2000),
                "锁定数量": random.randint(0, 100),
                "状态": random.choice(["正常 ⬇️", "偏低 ⚠️", "缺货 🔴", "充足 ✅"]),
            }
        },
    }

    def __init__(self, scenario: str = "sales"):
        if scenario not in self.SCENARIOS:
            available = ", ".join(self.SCENARIOS.keys())
            raise ValueError(f"未知场景 '{scenario}'，可选：{available}")
        self.scenario = scenario
        self.template = self.SCENARIOS[scenario]
        self.generated_at = datetime.now()
        self.data = []

    def generate_data(self, rows: Optional[int] = None) -> list:
        """生成模拟数据"""
        count = rows or len(self.template.get("regions", []) or 
                            self.template.get("items", []) or 
                            self.template.get("platforms", []) or 
                            self.template.get("products", []))
        
        labels = (self.template.get("regions") or
                  self.template.get("items") or
                  self.template.get("platforms") or
                  self.template.get("products") or
                  [f"项目{i+1}" for i in range(count)])
        
        gen_fn = self.template["generate_row"]
        self.data = [gen_fn(label, i) for i, label in enumerate(labels[:count])]
        return self.data

    def to_html(self) -> str:
        """生成 HTML 格式报表"""
        t = self.template
        data = self.data or self.generate_data()

        # 计算汇总行
        summary_html = ""
        if self.scenario == "sales":
            total_amount = sum(float(row["签约金额(万)"]) for row in data)
            avg_rate = sum(float(row["目标完成率"].rstrip("%")) for row in data) / len(data)
            total_leads = sum(row["新增线索"] for row in data)
            summary_html = (
                '<tr class="summary-row">'
                '<td><strong>合计</strong></td>'
                f'<td><strong>{total_amount:.1f}</strong></td>'
                f'<td><strong>{avg_rate:.1f}%</strong></td>'
                f'<td><strong>{total_leads}</strong></td>'
                "<td>-</td>"
                "<td>-</td>"
                "</tr>"
            )

        rows_html = ""
        for row in data:
            cells = "".join(f"<td>{v}</td>" for v in row.values())
            # 根据数据添加条件样式
            status_class = ""
            status_val = str(row.get("状态", ""))
            if "缺货" in status_val:
                status_class = ' style="background:rgba(239,68,68,0.1);"'
            elif "正常" in status_val.replace(" ", ""):
                status_class = ' style="background:rgba(16,185,129,0.08);"'
            
            rows_html += f"<tr{status_class}>{cells}</tr>\n"

        header_cells = "".join(f"<th>{h}</th>" for h in t["headers"])
        gen_time = self.generated_at.strftime("%Y年%m月%d日 %H:%M")

        html = (
            "<!DOCTYPE html>\n"
            '<html lang="zh-CN">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f"<title>{t['title']} — OpenClaw 自动生成</title>\n"
            "<style>\n"
            "  * { margin:0; padding:0; box-sizing:border-box; }\n"
            "  body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;\n"
            "         background:#f0f2f5; padding:24px; color:#1a1a2e; }\n"
            "  .report-container { max-width:1100px; margin:0 auto; }\n"
            "  .report-header {\n"
            "    background:linear-gradient(135deg,#2563eb,#7c3aed);\n"
            "    color:white; padding:28px 32px; border-radius:12px 12px 0 0;\n"
            "    display:flex; justify-content:space-between; align-items:flex-start;\n"
            "  }\n"
            "  .report-title { font-size:22px; font-weight:700; margin-bottom:6px; }\n"
            "  .report-meta { font-size:13px; opacity:0.85; }\n"
            "  .badge { background:rgba(255,255,255,0.2); padding:4px 14px; border-radius:20px; font-size:12px; }\n"
            "  .report-body { background:white; padding:24px; border-radius:0 0 12px 12px;\n"
            "                  box-shadow:0 4px 20px rgba(0,0,0,0.08); }\n"
            "  table { width:100%; border-collapse:collapse; font-size:14px; }\n"
            "  th { text-align:left; padding:12px 14px; background:#f8fafc; font-weight:600;\n"
            "       color:#475569; border-bottom:2px solid #e2e8f0; font-size:13px; white-space:nowrap; }\n"
            "  td { padding:11px 14px; border-bottom:1px solid #f1f5f9; }\n"
            "  tr:hover td { background:#f8fafc; }\n"
            "  .summary-row { background:#eff6ff !important; font-weight:600; border-top:2px solid #2563eb; }\n"
            "  .summary-row td { border-bottom:none; padding-top:14px; padding-bottom:14px; }\n"
            "  .footer { text-align:center; margin-top:16px; color:#94a3b8; font-size:12px; }\n"
            "</style>\n"
            "</head>\n<body>\n"
            '<div class="report-container">\n'
            '  <div class="report-header">\n'
            "    <div>\n"
            f'      <div class="report-title">{t["title"]}</div>\n'
            '      <div class="report-meta">\n'
            f"        📅 {gen_time} · \n"
            "        🤖 OpenClaw 智能自动化助手自动生成\n"
            "      </div>\n"
            "    </div>\n"
            '    <div class="badge">✅ 已自动生成</div>\n'
            "  </div>\n"
            '  <div class="report-body">\n'
            "    <table>\n"
            "      <thead>\n"
            f"        <tr>{header_cells}</tr>\n"
            "      </thead>\n"
            "      <tbody>\n"
            f"        {rows_html}"
            f"        {summary_html}"
            "      </tbody>\n"
            "    </table>\n"
            "  </div>\n"
            f"  <p class='footer'>本报告由 OpenClaw 自动化流程生成 · 数据更新周期：{self.scenario}</p>\n"
            "</div>\n"
            "</body>\n"
            "</html>"
        )
        return html

    def to_markdown(self) -> str:
        """生成 Markdown 格式报表"""
        t = self.template
        data = self.data or self.generate_data()

        header_line = " | ".join(t["headers"])
        divider = "|".join(["---" for _ in t["headers"]])

        lines = [
            f"# {t['title']}",
            "",
            f"> 📅 生成时间：{self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "> 🤖 由 **OpenClaw 智能自动化助手** 自动生成",
            "",
            "---",
            "",
            "## 数据明细",
            "",
            f"| {header_line} |",
            f"|{divider}|",
        ]

        for row in data:
            line = "|" + "|".join(str(v) for v in row.values()) + "|"
            lines.append(line)

        lines.append("")
        lines.append("---")
        lines.append("*报告由 OpenClaw 自动化流程自动生成*")

        return "\n".join(lines)

    def save(self, output_path: str, fmt: str = "html") -> str:
        """
        保存报表到文件
        
        Args:
            output_path: 输出路径
            fmt: 输出格式 (html / markdown / json)
        
        Returns:
            实际保存的文件路径
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        if fmt == "html":
            content = self.to_html()
        elif fmt in ("md", "markdown"):
            content = self.to_markdown()
        elif fmt == "json":
            content = json.dumps({
                "title": self.template["title"],
                "generated_at": self.generated_at.isoformat(),
                "scenario": self.scenario,
                "data": self.data,
            }, ensure_ascii=False, indent=2)
        else:
            content = self.to_html()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return output_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 报表生成器")
    parser.add_argument("-s", "--scenario", choices=list(ReportGenerator.SCENARIOS.keys()),
                        default="sales", help="选择场景（默认：sales）")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径")
    parser.add_argument("-f", "--format", choices=["html", "markdown", "json"],
                        default="html", help="输出格式（默认：html）")
    parser.add_argument("--rows", type=int, help="指定数据行数")
    
    args = parser.parse_args()
    
    gen = ReportGenerator(scenario=args.scenario)
    gen.generate_data(rows=args.rows)
    
    saved_path = gen.save(output_path=args.output, fmt=args.format)
    print(f"\n📄 报表已生成：{saved_path}")
    print(f"   场景：{args.scenario}")
    print(f"   格式：{args.format}")
    print(f"   记录数：{len(gen.data)} 条")


if __name__ == "__main__":
    main()
