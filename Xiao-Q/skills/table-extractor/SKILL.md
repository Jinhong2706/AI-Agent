---
name: table-extractor
description: 表格数据处理工具。支持 Excel ↔ CSV 互转、JSON → CSV/Excel 数据导出、从 PDF/Word 提取表格到 Excel。当用户需要处理表格数据或转换表格格式时使用此技能，包括：(1) Excel 和 CSV 互相转换，(2) JSON 数据导出为 CSV 或 Excel，(3) 从 PDF 或 Word 文档中提取表格数据到 Excel。
---

# Table Extractor - 表格数据处理技能

## 概述

这个技能提供多种表格数据处理功能，支持以下操作：
- **Excel ↔ CSV** (.xlsx ↔ .csv)
- **JSON → CSV/Excel** (.json → .csv / .xlsx)
- **从 PDF/Word 提取表格** (→ .xlsx)

## 功能分类

### 1. Excel ↔ CSV 互转

#### Excel 转 CSV
使用 `scripts/excel_to_csv.py` 脚本：

```bash
python3 scripts/excel_to_csv.py <input.xlsx> <output.csv>
```

#### CSV 转 Excel
使用 `scripts/csv_to_excel.py` 脚本：

```bash
python3 scripts/csv_to_excel.py <input.csv> <output.xlsx>
```

### 2. JSON → CSV/Excel

#### JSON 转 CSV
使用 `scripts/json_to_csv.py` 脚本：

```bash
python3 scripts/json_to_csv.py <input.json> <output.csv>
```

#### JSON 转 Excel
使用 `scripts/json_to_excel.py` 脚本：

```bash
python3 scripts/json_to_excel.py <input.json> <output.xlsx>
```

### 3. 从 PDF/Word 提取表格

#### 从 PDF 提取表格
使用 `scripts/extract_pdf_table.py` 脚本：

```bash
python3 scripts/extract_pdf_table.py <input.pdf> <output.xlsx>
```

#### 从 Word 提取表格
使用 `scripts/extract_word_table.py` 脚本：

```bash
python3 scripts/extract_word_table.py <input.docx> <output.xlsx>
```

## 使用流程

1. **识别数据类型**：从用户请求中识别源文件格式和目标格式
2. **检查文件存在**：确认源文件存在且可读
3. **选择转换脚本**：根据数据方向和格式选择对应脚本
4. **执行转换**：运行相应的 Python 脚本
5. **验证输出**：检查输出文件是否成功生成
6. **返回结果**：提供转换后的文件路径

## 依赖库

脚本需要以下 Python 库：

```bash
pip install pandas openpyxl csvkit tabula-py pdfplumber python-docx
```

### 依赖说明
- `pandas` - 数据处理核心库
- `openpyxl` - Excel 文件读写
- `csvkit` - CSV 文件处理
- `tabula-py` - PDF 表格提取（需要 Java）
- `pdfplumber` - PDF 表格提取（纯 Python）
- `python-docx` - Word 文档处理

## 脚本说明

所有脚本位于 `scripts/` 目录下，每个脚本独立可执行，接受命令行参数：
- 第一个参数：输入文件路径
- 第二个参数：输出文件路径

### 脚本列表
- `excel_to_csv.py` - Excel 转 CSV
- `csv_to_excel.py` - CSV 转 Excel
- `json_to_csv.py` - JSON 转 CSV
- `json_to_excel.py` - JSON 转 Excel
- `extract_pdf_table.py` - 从 PDF 提取表格
- `extract_word_table.py` - 从 Word 提取表格

## 注意事项

- JSON 数据应是数组格式或包含数组字段
- PDF 表格提取质量取决于 PDF 格式（文本型 PDF 效果最佳）
- 复杂表格可能需要手动调整
- 大文件处理可能需要较长时间
- 确保有足够的磁盘空间存储输出文件
- tabula-py 需要 Java 环境，如无 Java 可使用 pdfplumber

## JSON 数据格式要求

### 支持的 JSON 格式

**格式 1：数组直接作为根元素**
```json
[
  {"name": "Alice", "age": 30},
  {"name": "Bob", "age": 25}
]
```

**格式 2：数组嵌套在字段中**
```json
{
  "data": [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
  ]
}
```

**格式 3：每行一个 JSON 对象（JSON Lines）**
```json
{"name": "Alice", "age": 30}
{"name": "Bob", "age": 25}
```
