---
name: excel-chart
description: 从 Excel 文件读取数据并生成统计图表，支持柱状图、折线图、饼图、散点图、箱线图、热力图等多种图表类型，输出 HTML 交互图表或静态图片。
agent_created: true
---

# excel-chart - Excel 统计图生成 Skill

## 功能概述

从 Excel 文件（.xlsx / .xls）读取数据，自动识别数据结构，生成高质量的统计图表。支持多种图表类型和两种输出格式。

## 触发条件

当用户提出以下意图时使用此 skill：
- 「从这个 Excel 生成图表」「根据 Excel 画图」「Excel 数据可视化」
- 「帮我做一张柱状图/折线图/饼图/散点图/箱线图/热力图」
- 「把这份 Excel 数据变成图表」
- 「Excel 数据分析」「统计图」「数据图表」
- 泛化表述：涉及 Excel 文件 + 图表/可视化/统计图

## 前置环境检查

使用此 skill 前，确保以下 Python 库已安装：

```bash
python -m pip install pandas openpyxl plotly matplotlib kaleido --quiet
```

一键检查：

```bash
python -c "import pandas; import openpyxl; import plotly; import matplotlib; import kaleido; print('OK')"
```

如果报错 `ModuleNotFoundError`，先执行安装命令。

## 使用流程

### 第一步：读取并理解 Excel 数据结构

调用 `scripts/generate_chart.py` 的预览模式来查看 Excel 内容：

```bash
python <skill_path>/scripts/generate_chart.py <excel_path> --mode preview
```

脚本会输出：
- 所有 sheet 名称
- 每个 sheet 的前 5 行数据
- 列名和数据类型
- 数据统计摘要（数值列的最大/最小/均值等）

### 第二步：与用户确认图表参数

基于预览结果，与用户确认：
1. 使用哪个 sheet（如果有多张表）
2. 用作 X 轴的列（通常为分类/时间列）
3. 用作 Y 轴的列（通常为数值列）
4. 图表类型（柱状图/折线图/饼图/散点图/箱线图/热力图）
5. 输出格式（HTML 交互图表 / PNG 静态图片）

如果用户没有明确指定，根据数据结构自动推荐最合适的图表类型：
- 1 个分类列 + 1 个数值列 → 柱状图 或 饼图
- 1 个时间列 + 1 个数值列 → 折线图
- 2 个数值列 → 散点图
- 多个数值列 → 箱线图 或 热力图

### 第三步：生成图表

根据确认的参数生成图表：

```bash
python <skill_path>/scripts/generate_chart.py <excel_path> \
    --sheet "Sheet1" \
    --chart-type bar \
    --x-column "列名1" \
    --y-column "列名2" \
    --title "图表标题" \
    --output <输出路径> \
    --output-format html
```

图表类型参数 `--chart-type` 的可选值：
- `bar` — 柱状图（竖直）/ 条形图（水平）
- `line` — 折线图/趋势图
- `pie` — 饼图/环形图
- `scatter` — 散点图
- `box` — 箱线图
- `heatmap` — 热力图（需要至少两个数值列）
- `auto` — 自动推荐最合适的图表类型

输出格式参数 `--output-format`：
- `html` — 生成 Plotly 交互式 HTML 图表（默认）
- `png` — 生成 Matplotlib 静态 PNG 图片

### 第四步：展示结果

- **HTML 输出**：使用 `preview_url` 工具预览生成的 HTML 文件
- **PNG 输出**：使用 `open_result_view` 或直接发送文件给用户

## 脚本详细用法

```bash
python <skill_path>/scripts/generate_chart.py <excel_path> [options]

位置参数：
  excel_path             Excel 文件路径

选项：
  --mode preview         仅预览数据，不生成图表
  --sheet SHEET_NAME     指定使用的 sheet 名称（默认：第一个 sheet）
  --chart-type TYPE      图表类型：bar|line|pie|scatter|box|heatmap|auto
  --x-column COL         指定 X 轴列名
  --y-column COL         指定 Y 轴列名（多个列用逗号分隔，用于箱线图和热力图）
  --title TITLE          图表标题
  --subtitle SUBTITLE    图表副标题
  --output PATH          输出文件路径（不含扩展名）
  --output-format FORMAT 输出格式：html|png（默认：html）
  --width WIDTH          图表宽度（像素，默认：1000）
  --height HEIGHT        图表高度（像素，默认：600）
  --palette THEME        配色方案：default|vivid|pastel|dark（默认：default）
  --horizontal           生成水平条形图（仅对 bar 类型有效）
  --sort                 对类别数据进行排序（按数值降序）
  --top N                仅显示前 N 条数据
```

## 数据预处理

脚本会自动进行以下预处理：
1. 尝试将日期字符串解析为 datetime 类型
2. 自动识别数值列和分类列
3. 忽略完全为空的列
4. 缺失值标记但不填充（由图表类型决定处理方式）
5. 如果数据量过大（超过 1000 行），自动提示分批或采样

## 文件结构

```
excel-chart/
├── SKILL.md              # 本文件 - skill 主说明
├── scripts/
│   └── generate_chart.py # 核心脚本 - 读取 Excel 并生成图表
└── references/
    └── chart_types.md    # 图表类型参考指南
```
