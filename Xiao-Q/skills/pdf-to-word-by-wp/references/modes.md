# PDF 转 Word 模式对比

## 三种识别模式

| 模式 | 常量 | 输出效果 | 编辑友好度 | 适用场景 |
|------|------|---------|-----------|---------|
| **Flow** | `MODE_FLOW` = 0 | 引擎做文字分组+多级分析 | ✅ 高 | 日常文档，推荐默认 |
| **EnhancedFlow** | `MODE_ENHANCED` = 1 | 在 Flow 基础上进一步优化 | ✅ 高 | 复杂表格、多栏排版 |
| **Textbox** | `MODE_TEXTBOX` = 2 | 输出文本框密集，视觉保真 | ❌ 低 | 原样复现、打印输出 |

## 使用示例

### Python（推荐）
```python
from pdf2word import convert_pdf_python
convert_pdf_python("resume.pdf", "resume.docx", mode="flow")
```

### Java / Aspose.PDF
```java
import com.aspose.pdf.DocSaveOptions;

// Flow（默认，易编辑）
DocSaveOptions opts = new DocSaveOptions();
opts.setFormat(DocSaveOptions.DocFormat.DocX);  // 1=DOCX, 0=DOC
opts.setMode(0);  // 0=Flow, 1=EnhancedFlow, 2=Textbox
opts.setRelativeHorizontalProximity(2.5f);
opts.setRecognizeBullets(true);
doc.save("output.docx", opts);
```

## 实际测试数据（简历.pdf）

| 模式 | 耗时 | 特点 |
|------|------|------|
| Flow | ~10s | 文字清晰可编辑，段落结构好 |
| EnhancedFlow | ~23s | 复杂排版处理更好 |
| Textbox | ~23s | 视觉最接近原 PDF，文本框密集 |
