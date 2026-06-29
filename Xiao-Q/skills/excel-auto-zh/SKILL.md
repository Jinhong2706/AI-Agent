---
name: excel-auto-zh
description: >
  Excel / WPS 表格自动化处理工具。用 openpyxl 创建格式专业的报表、解析含宏的复杂 xlsm
  文件、批量合并多工作表数据。适用于财务报表生成、考勤汇总、销售数据整理、人力资源
  批量处理等场景。解决"Excel重复操作太耗时"、"WPS自动化"、"批量处理表格"、
  "xlsm文件解析"等问题。兼容 Windows / macOS，WPS Office 与 Microsoft Excel 均适用。
tags: [excel自动化, WPS, 表格处理, openpyxl, 数据整理, office自动化, excel-automation]
---

# Excel / WPS 表格自动化工具

用 Python 自动创建、解析和批量处理 Excel / WPS 表格文件，告别重复手动操作。

## Tools Required
- exec

## 核心能力

**1. 创建格式化报表**
用 `openpyxl` 生成带专业格式的 Excel 文件，支持自定义颜色（蓝色=输入项、黑色=计算值、绿色=跨表引用），适合财务报表、数据汇总等场景。

**2. 解析复杂 xlsm 文件**
用标准库 `zipfile + xml.etree` 解析 openpyxl 无法处理的复杂 xlsm 文件（含 VBA 宏、超过 1MB 的大型财务模型），提取数据无需安装额外依赖。

**3. 批量数据处理**
自动读取多工作表、合并数据、生成汇总报告，适合考勤汇总、销售数据整理、人力资源批量处理等重复性工作。

## Setup

```bash
pip install openpyxl
```

WPS Office 用户：openpyxl 生成的 `.xlsx` 文件可直接用 WPS 打开，格式完全兼容。

## Usage

- "帮我用 openpyxl 生成一份财务报表，区分输入项和计算项的颜色"
- "这个 xlsm 文件 openpyxl 打不开，帮我用 zipfile 解析里面的数据"
- "帮我写脚本把 20 个考勤表自动合并成一份月度汇总表"

## Examples

输入：`帮我生成一份销售月报，包含每个销售员的业绩、完成率、排名，蓝色标注目标值，黑色标注实际值`

输出：
- 生成 `sales_monthly_report.xlsx`，含格式化表头、自动排名列、汇总行（SUM/AVERAGE）
- 颜色规则：蓝色=目标，黑色=实际，绿色=完成率公式
- 附带可直接运行的 Python 代码，Windows/WPS 环境直接可用
