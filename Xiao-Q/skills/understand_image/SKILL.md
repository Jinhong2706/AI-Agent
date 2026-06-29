---
name: understand_image
description: 图片理解与分析。⚠️【强制】主Agent完全无法看图，绝对禁止对图片内容直接回复或猜测！①用户消息仅含图片（包括仅有图片URL或markdown图片链接如[图片](url)，无其他实质文字）→必须调用此skill；②有图片+文字且意图为看图/识别/描述/解题→必须调用此skill。每条含图消息均需调用，无论上下文多长、无论之前是否调用过，不调用就是错误。
version: v0.0.1
author: qqai
---

## understand_image（图片理解）

智能图片理解助手，能够分析图片内容并回答用户问题。支持识别物体、场景、文字等多种内容。支持 1-5 张图片同时分析。

### 触发条件

- 用户发送图片并提问
- 用户只发送图片，不附带任何文字
- 用户消息仅包含图片 URL 或 markdown 图片链接（如 `[图片](url)`），无其他实质文字内容，视同"仅发图片"
- 用户要求描述、识别、分析图片
- 关键词：看看、识别、描述、分析、这张图、图里、图中、什么图片

### 调用示例

通过 exec 工具调用执行

用户提问图片内容：
```bash
  understand_image --parameters '{
    \"images\": [\"https://example.com/photo.jpg\"], 
    \"question\": \"图里有什么动物？\",
    \"is_patching\": true
  }'
```

用户只发图片无文字（统一使用兜底 question，由识图 Agent 自行判断该解题还是描述）：
```bash
  understand_image --parameters '{
    \"images\": [\"https://example.com/photo.jpg\"], 
    \"question\": \"请先观察这张图片：如果图片主体是学科题目（数学、物理、化学、生物、语文、英语等的试题/作业/练习），请直接解答并给出详细步骤和最终答案；否则请描述图中的主要内容。\",
    \"is_patching\": true
  }'
```

详细描述模式：
```bash
 understand_image --parameters '{
    \"images\": [\"https://example.com/photo.jpg\"], 
    \"question\": \"仔细描述一下这张图\", 
    \"detailed\": true,
    \"is_patching\": true
  }'
```

多图分析：
```bash
 understand_image --parameters '{
    \"images\": [\"https://example.com/1.jpg\", \"https://example.com/2.jpg\"], 
    \"question\": \"这两张图有什么区别？\",
    \"is_patching\": true
  }'
```

### 参数说明
| 参数       | 类型 | 必填 | 说明 |
|----------|------|------|------|
| images   | array[string] | 是 | 图片URL列表，至少1张，最多5张 |
| question | string | 否 | 传给 vision 模型的问题。用户有明确文字时直接使用用户问题；用户只发图片无文字时使用默认兜底 question（由识图 Agent 自行判断分支） |
| detailed | boolean | 否 | 是否需要详细描述，默认 false。用户说"详细描述"、"仔细看看"时设为 true |
| is_patching | boolean | 是 | 是否批量发送图片，必须显式传 true |

### 参数填充规则
1. **images**：从用户上传的图片或对话上下文中提取图片 URL
2. **question**：
   - **用户有明确文字提问时**：直接使用用户的问题作为 question
   - **用户只发图片没有文字时**：直接使用默认兜底 question（即 JSON Schema 中的 default 值），不要让主 Agent 去猜测或判断图片内容。这个兜底 question 已经内置了"如果是题目就解题、否则就描述"的分支指令，识图 Agent 会自行看图分支处理
3. **detailed**：用户要求"详细描述"、"仔细看看"、"完整分析"时设为 true
4. **is_patching**：必须显式传 `true`，不可省略


### 完整 parameters **输入参数** 的 JSON Schema 定义

```json
{
  "name": "understand_images",
  "description": "针对图片内容进行分析与问答，支持识别图片中的物体、场景、文字等，回答用户关于图片的问题.",
  "input_schema": {
    "type": "object",
    "description": "技能输入参数的 JSON Schema 约束",
    "properties": {
      "images": {
        "type": "array",
        "description": "需要分析和理解的图片链接列表，至少1张，最多5张",
        "items": {
          "type": "string",
          "description": "需要分析和问答的图片链接"
        }
      },
      "question": {
        "type": "string",
        "description": "传给 vision 模型的问题。用户有明确文字时直接使用用户问题；用户只发图片无文字时使用默认值（default 已内置分支判断指令，由识图 Agent 自行决定解题或描述）",
        "default": "请先观察这张图片：如果图片主体是学科题目（数学、物理、化学、生物、语文、英语等的试题/作业/练习），请直接解答并给出详细步骤和最终答案；否则请描述图中的主要内容。"
      },
      "detailed": {
        "type": "boolean",
        "description": "是否需要详细描述，用户表示'详细描述'、'仔细看看'语义时设为 true",
        "default": false
      },
      "is_patching": {
        "type": "boolean",
        "description": "是否批量发送图片，必须显式传 true"
      }
    }
  }
}
```

### 返回结构

| 字段                             | 类型     | 说明                         |
|--------------------------------|--------|----------------------------|
| `status`                       | string | 执行状态 success/failed        |
| `result.answer`                | string | 汇总回答文本（主 Agent 展示给用户的核心内容） |
| `result.total_understad_result`| string | 整体回答（is_patching=true 时返回） |
| `result.results[]`             | array  | 逐图结果列表                     |
| `result.results[].description` | string | 单张图片的描述                    |
| `result.results[].image_url`   | string | 对应的图片 URL                  |
| `result.results[].success`     | bool   | 该图片是否分析成功                  |

**成功（单图）**：
```json
{"status": "success", "result": {"answer": "图片中是一头棕色的牛站在绿色草地上...", "total_understad_result": "图片中是一头棕色的牛...", "results": [{"description": "图片中是一头棕色的牛...", "image_url": "https://example.com/photo.jpg", "success": true}]}}
```

**成功（多图）**：
```json
{"status": "success", "result": {"answer": "...", "total_understad_result": "综合来看，第一张图是...第二张图是...", "results": [{"description": "...", "image_url": "https://example.com/1.jpg", "success": true}, {"description": "...", "image_url": "https://example.com/2.jpg", "success": true}]}}
```

**失败**：
```json
{"status": "failed", "result": {"error_code": "MISSING_IMAGE_URL", "error_message": "未提供图片URL", "success": false}}
```

### ⚠️ 注意事项（必须严格遵守）

1. `images` 至少 1 张，最多 5 张，超出范围不调用
2. 用户只发图片没有文字时，**直接使用 question 的 default 值**，不要让主 Agent 去猜测或编造图片内容；default 本身已经包含"如果是题目就解题、否则描述"的分支指令，识图 Agent 会自行处理
3. 当用户有明确文字提问时，直接使用用户的问题作为 question
4. **`is_patching` 始终设为 true**，无需根据图片数量判断
5. **🚫 绝对禁止主 Agent 在不调用此 skill 的情况下回复任何与图片内容相关的信息。你看不到图片，任何直接回复都是编造！**
6. **🔁 无论对话多长、无论之前已经调用过多少次，只要当前消息含图片，就必须再次调用。跳过 = 错误。**
7. **🔄 调用失败时，必须使用与上次完全相同的参数重试，严禁自行修改 question、detailed 等参数。重试应还原用户原始请求，不得擅自切换为详细描述模式或改写用户问题。**