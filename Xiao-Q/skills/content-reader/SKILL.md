---
name: content-reader
description: 内容提取工具。从 PDF/Word 文档中提取文字内容，从 JSON/CSV 文件中读取和分析数据。当用户需要提取文档内容或读取数据文件时使用此技能，包括：(1) 从 PDF 提取文字，(2) 从 Word 提取文字，(3) 读取 JSON 数据，(4) 读取 CSV 数据，(5) 任何涉及内容提取的请求。
---

# Content Reader - 内容提取技能

## 概述

这个技能提供多种内容提取和读取功能，支持以下操作：
- **从 PDF 提取文字** (.pdf → text)
- **从 Word 提取文字** (.docx → text)
- **读取 JSON 数据** (.json)
- **读取 CSV 数据** (.csv)

## 功能分类

### 1. 从 PDF 提取文字

使用 `scripts/extract_pdf_text.py` 脚本：

```bash
python3 scripts/extract_pdf_text.py <input.pdf> [output.txt]
```

如果不指定输出文件，则直接打印到标准输出。

### 2. 从 Word 提取文字

使用 `scripts/extract_word_text.py` 脚本：

```bash
python3 scripts/extract_word_text.py <input.docx> [output.txt]
```

如果不指定输出文件，则直接打印到标准输出。

### 3. 读取 JSON 数据

使用 `scripts/read_json.py` 脚本：

```bash
python3 scripts/read_json.py <input.json> [--summary]
```

选项：
- `--summary`: 显示数据摘要（行数、列数、字段名）

### 4. 读取 CSV 数据

使用 `scripts/read_csv.py` 脚本：

```bash
python3 scripts/read_csv.py <input.csv> [--summary] [--head N]
```

选项：
- `--summary`: 显示数据摘要（行数、列数、列名）
- `--head N`: 只显示前 N 行（默认 10 行）

## 使用流程

1. **识别提取需求**：从用户请求中识别源文件格式和提取目标
2. **检查文件存在**：确认源文件存在且可读
3. **选择提取脚本**：根据文件类型和提取目标选择对应脚本
4. **执行提取**：运行相应的 Python 脚本
5. **返回结果**：输出提取的内容或保存到文件

## 依赖库

脚本需要以下 Python 库：

```bash
pip install pdfplumber python-docx pandas
```

### 依赖说明
- `pdfplumber` - PDF 文字提取
- `python-docx` - Word 文档处理
- `pandas` - 数据读取和处理

## 脚本说明

所有脚本位于 `scripts/` 目录下，每个脚本独立可执行。

### 脚本列表
- `extract_pdf_text.py` - 从 PDF 提取文字
- `extract_word_text.py` - 从 Word 提取文字
- `read_json.py` - 读取 JSON 数据
- `read_csv.py` - 读取 CSV 数据

## 输出格式

### 文字提取
- 默认输出到标准输出
- 可选保存到文本文件
- 保留原始格式（换行、段落）

### 数据读取
- 显示数据预览（前 N 行）
- 可选显示数据摘要（形状、列名、数据类型）
- 支持格式化输出

## 注意事项

- PDF 提取质量取决于 PDF 格式（文本型 PDF 效果最佳，扫描件需要 OCR）
- Word 文档中的图片、表格不会被提取为文字
- JSON 文件应该是有效的 JSON 格式
- CSV 文件应使用 UTF-8 编码
- 大文件处理可能需要较长时间
- 确保有足够的磁盘空间存储输出文件

## 示例用法

### 提取 PDF 文字并保存
```bash
python3 scripts/extract_pdf_text.py document.pdf output.txt
```

### 提取 Word 文字到标准输出
```bash
python3 scripts/extract_word_text.py document.docx
```

### 读取 JSON 数据并显示摘要
```bash
python3 scripts/read_json.py data.json --summary
```

### 读取 CSV 前 20 行
```bash
python3 scripts/read_csv.py data.csv --head 20
```
