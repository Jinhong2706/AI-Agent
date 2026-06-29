---
name: doc-converter
description: 文档格式转换工具。支持 PDF ↔ Word 互转、Markdown → HTML/PDF、HTML → Markdown 转换。当用户需要转换文档格式时使用此技能，包括：(1) PDF 转 Word 或 Word 转 PDF，(2) Markdown 转 HTML 或 PDF，(3) HTML 转 Markdown，(4) 任何涉及这些格式转换的请求。
---

# Document Converter - 文档格式转换技能

## 概述

这个技能提供多种文档格式之间的转换功能，支持以下转换方向：
- **PDF ↔ Word** (.pdf ↔ .docx)
- **Markdown → HTML/PDF** (.md → .html / .pdf)
- **HTML → Markdown** (.html → .md)

## 功能分类

### 1. PDF ↔ Word 互转

#### PDF 转 Word
使用 `scripts/pdf_to_word.py` 脚本：

```bash
python3 scripts/pdf_to_word.py <input.pdf> <output.docx>
```

#### Word 转 PDF
根据操作系统选择脚本：

**Windows/Mac (需要 Microsoft Word):**
```bash
python3 scripts/word_to_pdf.py <input.docx> <output.pdf>
```

**Linux (需要 LibreOffice):**
```bash
python3 scripts/word_to_pdf_libre.py <input.docx> <output.pdf>
```

### 2. Markdown → HTML/PDF

#### Markdown 转 HTML
使用 `scripts/md_to_html.py` 脚本：

```bash
python3 scripts/md_to_html.py <input.md> <output.html>
```

#### Markdown 转 PDF
使用 `scripts/md_to_pdf.py` 脚本：

```bash
python3 scripts/md_to_pdf.py <input.md> <output.pdf>
```

### 3. HTML → Markdown

使用 `scripts/html_to_md.py` 脚本：

```bash
python3 scripts/html_to_md.py <input.html> <output.md>
```

## 使用流程

1. **识别转换需求**：从用户请求中识别源文件格式和目标格式
2. **检查文件存在**：确认源文件存在且可读
3. **选择正确脚本**：根据操作系统选择合适的转换脚本
4. **执行转换脚本**：运行对应的 Python 脚本
5. **验证输出**：检查输出文件是否成功生成
6. **返回结果**：提供转换后的文件路径

## 依赖库

### 基础依赖（所有平台）
```bash
pip install pdf2docx python-docx markdown weasyprint html2text
```

### Windows/Mac 额外依赖
```bash
pip install docx2pdf
```

### Linux 额外依赖
需要安装 LibreOffice：
```bash
apt-get install libreoffice-writer  # Debian/Ubuntu
# 或
yum install libreoffice-writer      # CentOS/RHEL
```

## 脚本说明

所有转换脚本位于 `scripts/` 目录下，每个脚本独立可执行，接受命令行参数：
- 第一个参数：输入文件路径
- 第二个参数：输出文件路径

### 脚本列表
- `pdf_to_word.py` - PDF 转 Word
- `word_to_pdf.py` - Word 转 PDF (Windows/Mac)
- `word_to_pdf_libre.py` - Word 转 PDF (Linux)
- `md_to_html.py` - Markdown 转 HTML
- `md_to_pdf.py` - Markdown 转 PDF
- `html_to_md.py` - HTML 转 Markdown

## 注意事项

- 转换质量取决于源文件格式和内容复杂度
- 复杂排版可能在转换过程中丢失部分样式
- 建议转换后检查输出文件
- 大文件转换可能需要较长时间
- 确保有足够的磁盘空间存储输出文件
- Linux 下 Word 转 PDF 需要 LibreOffice，不支持 Microsoft Word
