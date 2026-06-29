---
name: markitdown
description: 将各种文件格式（PDF、Word、Excel、PPT、图片等）转换为 Markdown 格式，专为 LLM 和文本分析管道设计
---

## markitdown（文件转 Markdown）

将各种文件格式转换为 Markdown，专为 LLM 和文本分析管道设计。支持 PDF、Word、Excel、PPT、图片（OCR）、音频、HTML、CSV、JSON、XML、YouTube 等格式。

### 触发条件

- 用户上传文件并要求转换为 Markdown
- 用户提到"转 markdown"、"转 md"、"转换成 markdown"、"提取内容"、"转成文本"
- 用户要求处理文档、提取文件内容、转换格式等
- 关键词：markdown、md、转换、提取、文档转、文件转

### 调用示例

通过 exec 工具调用执行

**转换单个文件：**
```bash
markitdown --parameters '{
  "file_path": "/sandbox/workspace/uploads/file.pdf",
  "output_path": "/sandbox/workspace/outputs/file.md"
}'
```

**转换并存入知识库：**
```bash
markitdown --parameters '{
  "file_path": "/sandbox/workspace/uploads/file.docx",
  "upload_to_kb": true,
  "kb_id": "目标知识库ID"
}'
```

**批量转换：**
```bash
markitdown --parameters '{
  "file_paths": ["/path/to/file1.pdf", "/path/to/file2.docx"],
  "output_dir": "/sandbox/workspace/outputs/"
}'
```

**仅返回内容（不保存文件）：**
```bash
markitdown --parameters '{
  "file_path": "/sandbox/workspace/uploads/file.xlsx",
  "return_content": true
}'
```

### 参数说明
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_path | string | 是* | 要转换的单个文件路径（与 file_paths 二选一） |
| file_paths | array[string] | 是* | 要批量转换的文件路径列表（与 file_path 二选一） |
| output_path | string | 否 | 输出文件路径，默认为原文件路径加 .md 后缀 |
| output_dir | string | 否 | 批量转换时的输出目录，默认为 `/sandbox/workspace/outputs/` |
| return_content | boolean | 否 | 是否直接返回 Markdown 内容，默认 false（保存为文件） |
| upload_to_kb | boolean | 否 | 是否上传到知识库，默认 false |
| kb_id | string | 否 | 目标知识库 ID（upload_to_kb=true 时必填） |

### 参数填充规则

1. **file_path / file_paths**：从用户上传的文件或对话上下文中提取文件路径
2. **output_path**：用户指定输出路径时使用；否则自动生成（原文件名 + .md）
3. **output_dir**：批量转换时，用户指定则使用，否则用默认目录
4. **return_content**：用户说"直接给我内容"、"返回文本"时设为 true
5. **upload_to_kb**：用户明确要求存入知识库时设为 true
6. **kb_id**：从用户提供的知识库信息中提取

### 完整 parameters 输入参数的 JSON Schema 定义

```json
{
  "name": "markitdown",
  "description": "将各种文件格式（PDF、Word、Excel、PPT、图片等）转换为 Markdown 格式",
  "input_schema": {
    "type": "object",
    "properties": {
      "file_path": {
        "type": "string",
        "description": "要转换的单个文件路径"
      },
      "file_paths": {
        "type": "array",
        "items": {"type": "string"},
        "description": "要批量转换的文件路径列表"
      },
      "output_path": {
        "type": "string",
        "description": "输出文件路径，默认为原文件路径加 .md 后缀"
      },
      "output_dir": {
        "type": "string",
        "description": "批量转换时的输出目录",
        "default": "/sandbox/workspace/outputs/"
      },
      "return_content": {
        "type": "boolean",
        "description": "是否直接返回 Markdown 内容而不保存文件",
        "default": false
      },
      "upload_to_kb": {
        "type": "boolean",
        "description": "是否上传到知识库",
        "default": false
      },
      "kb_id": {
        "type": "string",
        "description": "目标知识库 ID"
      }
    }
  }
}
```

### 返回结构

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 执行状态：`success` 或 `failed` |
| result.message | string | 执行结果描述 |
| result.output_path | string | 转换后的文件路径（return_content=false 时） |
| result.content | string | 转换后的 Markdown 内容（return_content=true 时） |
| result.files | array | 批量转换时的文件列表 |
| result.upload_status | string | 上传状态（upload_to_kb=true 时） |

**成功（保存文件）：**
```json
{
  "status": "success",
  "result": {
    "message": "转换完成",
    "output_path": "/sandbox/workspace/outputs/file.md"
  }
}
```

**成功（返回内容）：**
```json
{
  "status": "success",
  "result": {
    "message": "转换完成",
    "content": "# 文档标题\n\n正文内容..."
  }
}
```

**成功（批量转换）：**
```json
{
  "status": "success",
  "result": {
    "message": "批量转换完成：3 成功，0 失败",
    "files": [
      {"input": "file1.pdf", "output": "/sandbox/workspace/outputs/file1.md", "status": "success"},
      {"input": "file2.docx", "output": "/sandbox/workspace/outputs/file2.md", "status": "success"},
      {"input": "file3.xlsx", "output": "/sandbox/workspace/outputs/file3.md", "status": "success"}
    ]
  }
}
```

**失败：**
```json
{
  "status": "failed",
  "result": {
    "error_code": "FILE_NOT_FOUND",
    "error_message": "文件不存在：/path/to/file.pdf"
  }
}
```

### ⚠️ 注意事项

1. **Python 版本**：需要 Python 3.10+ 环境
2. **首次使用**：技能会自动安装 `markitdown[pdf,docx,pptx,xlsx]` 依赖
3. **支持格式**：PDF、PowerPoint、Word、Excel、图片（EXIF+OCR）、音频（EXIF+语音转写）、HTML、CSV、JSON、XML、ZIP、YouTube、EPub 等
4. **输出目录**：默认输出到 `/sandbox/workspace/outputs/`，如不存在会自动创建
5. **安全提示**：不可信来源的文件需注意路径安全，避免目录遍历
6. **OCR 功能**：如需 OCR 识别图片中的文字，需额外安装 `markitdown-ocr` 插件并配置 LLM 客户端
7. **Azure 增强**：如需更高精度的转换，可配置 Azure Document Intelligence 或 Content Understanding endpoint
8. **大文件处理**：超大文件可能需要较长处理时间，请耐心等待
9. **批量转换**：批量转换时如有部分文件失败，会返回成功文件列表和失败原因

### 相关技能

- `understand_image` — 图片理解和分析
- `word-docx` — Word 文档创建和编辑
- `pptx-2-0.1.1` — PowerPoint 演示文稿处理
