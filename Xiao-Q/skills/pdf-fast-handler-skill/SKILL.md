---
name: pdf-fast-handler
description: PDF 终极全能处理工具 - 转换、编辑、OCR、加密解密、水印、页眉页脚、旋转、删页、提取页、图片互转、Word互转、压缩、修复、批量
homepage: https://github.com/QClaw/skills
metadata:
  {
    "clawdbot":
      {
        "emoji": "📄",
        "requires":
          {
            "bins": ["python3"],
            "packages": ["PyPDF2", "pdf2docx", "pdf2image", "pytesseract", "Pillow", "docx2pdf"]
          },
        "primaryEnv": "python3",
        "systemDeps":
          {
            "linux": ["poppler-utils", "tesseract-ocr"],
            "macos": ["poppler", "tesseract"],
            "windows": ["poppler", "tesseract"]
          },
        "autoInstall": true
      }
  }
---

# 📄 PDF 终极全能处理 Skill

> 一站式 PDF 解决方案：转换、编辑、OCR、加密解密、水印、页眉页脚、批量处理

---

## 🤖 Agent 执行指令

**执行本技能后，代理必须：**

### 1. 理解用户需求
- 识别 PDF 处理意图（转换/编辑/提取/加密/批量等）
- 解析关键参数（文件路径、输出路径、操作选项）

### 2. 执行命令示例

```bash
# 基础操作
python pdf_fast_handler_skill.py info input.pdf
python pdf_fast_handler_skill.py extract input.pdf
python pdf_fast_handler_skill.py merge file1.pdf file2.pdf -o merged.pdf

# 格式转换
python pdf_fast_handler_skill.py to-word input.pdf -o output.docx
python pdf_fast_handler_skill.py to-image input.pdf -o ./images
python pdf_fast_handler_skill.py to-txt input.pdf -o output.txt
python pdf_fast_handler_skill.py to-md input.pdf -o output.md

# 页面编辑
python pdf_fast_handler_skill.py rotate input.pdf 90 -o rotated.pdf
python pdf_fast_handler_skill.py delete-pages input.pdf 1,3,5 -o output.pdf
python pdf_fast_handler_skill.py extract-pages input.pdf 1,2,3 -o output.pdf

# 安全操作
python pdf_fast_handler_skill.py encrypt input.pdf -p 123456 -o encrypted.pdf
python pdf_fast_handler_skill.py decrypt input.pdf -p 123456 -o decrypted.pdf

# 图片/Word 互转
python pdf_fast_handler_skill.py images2pdf img1.jpg img2.jpg -o output.pdf
python pdf_fast_handler_skill.py word2pdf input.docx -o output.pdf

# 批量处理
python pdf_fast_handler_skill.py batch ./pdf_folder to-word
```

### 3. 依赖安装（脚本会自动检测并提示）
```bash
pip install PyPDF2 pdf2image pillow pytesseract pdf2docx docx2pdf
```

**注意**：Windows 下还需安装：
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/) - 用于 PDF 转图片
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) - 用于 OCR 识别

---

## 📋 支持的命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `info` | PDF 信息（页数、大小、加密状态） | `info input.pdf` |
| `extract` | 提取文本 | `extract input.pdf` |
| `merge` | 合并多个 PDF | `merge f1.pdf f2.pdf -o out.pdf` |
| `split` | 拆分 PDF | `split input.pdf 3` |
| `watermark` | 添加文字水印 | `watermark input.pdf "机密" -o out.pdf` |
| `to-word` | 转 Word | `to-word input.pdf -o out.docx` |
| `to-image` | 转图片 | `to-image input.pdf -o ./folder` |
| `to-html` | 转 HTML | `to-html input.pdf -o out.html` |
| `to-txt` | 转 TXT | `to-txt input.pdf -o out.txt` |
| `to-md` | 转 Markdown | `to-md input.pdf -o out.md` |
| `ocr` | OCR 识别（扫描件转文字） | `ocr input.pdf -o text.txt` |
| `encrypt` | 加密 PDF | `encrypt input.pdf -p 123456` |
| `decrypt` | 解密 PDF | `decrypt input.pdf -p 123456` |
| `rotate` | 旋转页面 | `rotate input.pdf 90` |
| `delete-pages` | 删除页 | `delete-pages input.pdf 1,3,5` |
| `extract-pages` | 提取页 | `extract-pages input.pdf 1,2` |
| `insert-page` | 插入 PDF | `insert-page input.pdf 2 insert.pdf` |
| `replace-page` | 替换页 | `replace-page input.pdf 3 new.pdf` |
| `add-header` | 添加页眉 | `add-header input.pdf "公司名称"` |
| `add-footer` | 添加页脚 | `add-footer input.pdf "第几页"` |
| `add-page-num` | 添加页码 | `add-page-num input.pdf` |
| `extract-images` | 提取图片 | `extract-images input.pdf -o ./imgs` |
| `extract-bookmarks` | 提取书签 | `extract-bookmarks input.pdf` |
| `reverse-pages` | 反转页面顺序 | `reverse-pages input.pdf` |
| `compress` | 压缩 PDF | `compress input.pdf high` |
| `repair` | 修复损坏 PDF | `repair input.pdf` |
| `images2pdf` | 图片转 PDF | `images2pdf a.jpg b.jpg -o out.pdf` |
| `word2pdf` | Word 转 PDF | `word2pdf input.docx` |
| `batch` | 批量处理 | `batch ./folder to-word` |

---

## 🐛 故障排查

### 问题：poppler 或 tesseract 找不到
- **Windows**：下载安装后添加到 PATH，或指定完整路径
- **Linux**：`sudo apt install poppler-utils tesseract-ocr`
- **Mac**：`brew install poppler tesseract`

### 问题：pip 安装失败
- 确保 Python 3.8+
- 尝试：`pip install --upgrade pip`

---

## 📝 更新日志

- **v1.0.0**：初始版本，支持完整 PDF 处理功能