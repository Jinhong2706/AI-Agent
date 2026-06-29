---
name: pdf-to-word
description: "PDF转Word(DOC/DOCX)工具，支持Aspose.PDF和纯Python双方案。触发词：(1)PDF转Word/DOC/DOCX (2)PDF转可编辑文档 (3)批量PDF转换 (4)aspose相关操作。模式：Flow易编辑/EnhancedFlow增强流/Textbox高保真。"
---

# PDF 转 Word

将 PDF 转换为可编辑的 Word 文档（DOC / DOCX）。

## 快速使用

### Python 脚本（推荐，无需 Java 环境）
```bash
# 安装依赖
pip install pymupdf python-docx

# 基本转换（Flow 模式，默认）
python scripts/pdf2word.py input.pdf

# 指定输出文件名
python scripts/pdf2word.py input.pdf output.docx

# 指定模式
python scripts/pdf2word.py input.pdf output.docx enhanced
python scripts/pdf2word.py input.pdf output.docx textbox   # 高保真
```

### Java 方案（需要 JDK + lib/pdftool-core-21.8.jar）
```bash
# 直接运行，jar 内置处理，无需额外配置
java -cp "lib/pdftool-core-21.8.jar" com.demo.Pdf2word input.pdf output.docx enhanced
```

## 模式选择

**默认推荐：Flow 模式**

| 模式 | 命令行参数 | 说明 |
|------|-----------|------|
| **Flow** | `flow` | 易编辑，段落清晰，适合大多数文档 |
| EnhancedFlow | `enhanced` | 增强流，复杂表格/多栏排版效果更好 |
| Textbox | `textbox` | 高保真，视觉最接近原 PDF，文本框密集 |

详细对比见 [references/modes.md](references/modes.md)

## 核心代码

### Python（pymupdf + python-docx）
```python
import fitz
from docx import Document

def convert(input_pdf, output_docx, mode="flow"):
    doc = fitz.open(input_pdf)
    docx = Document()
    for page in doc:
        for block in page.get_text("blocks"):
            text = block[4].strip()
            if text:
                docx.add_paragraph(text)
    doc.close()
    docx.save(output_docx)
```

### Java（lib/pdftool-core-21.8.jar）
```java
Document doc = new Document("input.pdf");
DocSaveOptions opts = new DocSaveOptions();
opts.setFormat(1);    // 0=DOC, 1=DOCX
opts.setMode(0);     // 0=Flow, 1=EnhancedFlow, 2=Textbox
opts.setRelativeHorizontalProximity(2.5f);
opts.setRecognizeBullets(true);
doc.save("output.docx", opts);
doc.close();
```

## 批量转换
```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
import pdf2word

pdf_dir = Path("input/")
out_dir = Path("output/")
out_dir.mkdir(exist_ok=True)

for pdf in pdf_dir.glob("*.pdf"):
    out = out_dir / f"{pdf.stem}.docx"
    pdf2word.convert_pdf_python(str(pdf), str(out))
    print(f"OK {pdf.name} -> {out.name}")
```

## 文件结构

```
pdf-to-word/
├── SKILL.md              <- 本文件
├── scripts/
│   └── pdf2word.py        <- 转换脚本（Python 入口）
├── lib/
│   └── pdftool-core-21.8.jar  <- PDF 核心库（已内置处理）
└── references/
    └── modes.md           <- 三种模式详细对比
```

## lib/pdftool-core-21.8.jar 说明

jar 内置了 PDF 转 Word 的核心处理逻辑，无需额外配置即可使用。
如需替换为其他版本，只需将新 jar 放入 lib/ 目录即可。
