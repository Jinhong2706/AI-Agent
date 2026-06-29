---
name: comic-style-image
description: >
  将用户上传的照片转换为漫画/插画风格图像。当用户提到"漫画风格"、"卡通化"、"插画风格"、"二次元风格"、"anime"、"comic"、"把照片变成漫画"、"漫画效果"、"手绘风格"、"赛璐璐风格"，或上传照片并希望进行艺术风格转化时，必须使用此技能。即使用户描述模糊（如"让照片好看一些"、"风格化处理"、"艺术化"），也应优先考虑触发此技能。支持多种漫画子风格：日式动漫、美式漫画、水彩插画、像素艺术、赛博朋克、吉卜力等。
---

# 漫画风格图像生成技能

## 核心能力

本技能通过 **Claude Artifacts + Anthropic API** 构建一个交互式的漫画风格转换工具。用户上传照片后，系统会分析图像内容，并生成对应漫画风格的详细提示词（Prompt），同时提供多种主流 AI 绘图平台的调用接口或可直接使用的提示词。

---

## 工作流程

### 第一步：接收用户输入

1. 用户上传一张或多张照片
2. 用户指定（或未指定）目标漫画风格
3. 如果用户未指定风格，**展示风格选择器**让用户选择

### 第二步：图像分析

使用 Claude Vision 分析上传的图像，提取：
- **主体信息**：人物/场景/物体的核心特征（发型、服装、表情、姿势等）
- **构图信息**：视角、景深、画面比例
- **色调信息**：主色调、光线方向、阴影风格
- **场景信息**：背景环境、氛围

### 第三步：生成漫画化提示词

根据分析结果 + 目标风格，生成：
1. **英文主提示词**（适配主流 AI 绘图工具）
2. **中文描述**（供用户理解）
3. **负面提示词**（排除不想要的元素）
4. **推荐参数**（适用于 Stable Diffusion / Midjourney / DALL-E）

### 第四步：交付成果

通过 Artifact 展示：
- 生成的提示词（可复制）
- 风格预览说明
- 各平台使用指南
- 可选：直接调用 DALL-E 3 API 生成预览图

---

## 支持的漫画风格

| 风格名称 | 关键词 | 代表作品 |
|---------|--------|---------|
| 日式动漫（Anime） | anime style, cel shading, vibrant colors | 进击的巨人、鬼灭之刃 |
| 吉卜力风格 | ghibli style, watercolor, soft lighting | 千与千寻、龙猫 |
| 美式漫画 | comic book style, bold outlines, halftone | 漫威、DC |
| 水彩插画 | watercolor illustration, soft edges | 绘本、概念艺术 |
| 赛璐璐风格 | cel animation, flat colors, ink outline | 经典动画 |
| 赛博朋克漫画 | cyberpunk comic, neon colors, dark atmosphere | 攻壳机动队 |
| 像素艺术 | pixel art, 8-bit, retro game style | 复古游戏风 |
| 黑白漫画 | black and white manga, screentone, dramatic | 少年漫画 |
| 欧式插画 | european illustration, ligne claire | 丁丁历险记 |
| 国风水墨 | Chinese ink painting, traditional, brushstroke | 中国传统水墨 |

---

## 实现方式

### 方式 A：生成提示词（推荐）

构建一个 **React Artifact**，功能包括：
1. 图片上传界面
2. 风格选择器（卡片式 UI）
3. 调用 Claude API 分析图像并生成提示词
4. 展示结果 + 一键复制功能

```jsx
// Artifact 核心结构示例
// 1. 上传图片 → base64 编码
// 2. 调用 /v1/messages API，传入图片 + 分析指令
// 3. 解析返回的提示词结构
// 4. 展示多平台适配的提示词
```

### 方式 B：直接生成图像（需要 DALL-E 3）

如果用户希望直接预览效果，可通过 Claude API 的图像生成能力（当可用时）直接输出漫画化图像。

---

## 提示词生成模板

### 系统提示词（发给 Claude API）

```
你是一位专业的 AI 绘图提示词工程师，擅长将真实照片描述转化为高质量的漫画/插画风格提示词。

用户将提供一张照片，你需要：
1. 仔细分析图像中的所有视觉元素
2. 根据指定的漫画风格，生成适配的提示词

请严格按照以下 JSON 格式返回，不要有任何额外文字：
{
  "style_name": "风格名称（中文）",
  "main_prompt_en": "主提示词（英文，200词以内）",
  "main_prompt_zh": "主提示词（中文翻译）",
  "negative_prompt": "负面提示词（英文）",
  "midjourney_command": "完整的 Midjourney 命令（包含 --style --ar 等参数）",
  "sd_settings": {
    "steps": 30,
    "cfg_scale": 7,
    "sampler": "DPM++ 2M Karras"
  },
  "style_tips": "使用此风格的3个关键技巧（中文）"
}
```

### 风格专属提示词片段

见 `references/style-prompts.md` 获取每种风格的专属关键词库。

---

## Artifact 构建指南

当用户请求此功能时，创建一个完整的 React Artifact：

### UI 组件结构

```
ComicConverter (主组件)
├── ImageUploader       # 拖拽上传 + 预览
├── StyleSelector       # 风格选择卡片网格
├── AnalysisProgress    # 分析进度指示器
└── ResultPanel         # 结果展示
    ├── PromptDisplay   # 提示词展示 + 复制按钮
    ├── PlatformGuide   # 各平台使用说明
    └── StylePreview    # 风格效果说明
```

### API 调用示例

```javascript
const analyzeAndConvert = async (imageBase64, selectedStyle) => {
  const styleGuide = STYLE_CONFIGS[selectedStyle];
  
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      messages: [{
        role: "user",
        content: [
          {
            type: "image",
            source: {
              type: "base64",
              media_type: "image/jpeg",
              data: imageBase64
            }
          },
          {
            type: "text",
            text: `请分析这张图片，并生成 ${styleGuide.name} 风格的漫画转换提示词。${SYSTEM_PROMPT}`
          }
        ]
      }]
    })
  });
  
  const data = await response.json();
  return JSON.parse(data.content[0].text);
};
```

### 关键设计原则

1. **响应式布局**：支持手机和桌面端
2. **实时反馈**：上传后立即显示预览，分析时显示动画
3. **一键复制**：所有提示词都有复制按钮
4. **多语言**：界面中文，提示词中英双语
5. **错误处理**：网络失败、格式错误时友好提示

---

## 输出标准

完成分析后，必须向用户提供：

### ✅ 必须包含
- [ ] 英文主提示词（可直接粘贴到 Midjourney/DALL-E）
- [ ] 中文说明（让用户理解提示词内容）
- [ ] 负面提示词（提升生成质量）
- [ ] 至少 2 个平台的使用说明

### ✅ 推荐包含
- [ ] Midjourney 完整命令（含参数）
- [ ] Stable Diffusion WebUI 参数推荐
- [ ] 风格调整建议（如何微调效果）

### ❌ 避免
- 过于通用的提示词（如仅写 "anime style"）
- 忽略原图的关键特征（发型、服装颜色等）
- 不提供负面提示词

---

## 常见场景示例

### 场景 1：人像照片 → 日式动漫
**用户输入**：上传一张戴眼镜的年轻女性照片，要求动漫风格

**输出示例**：
```
主提示词：anime style portrait, young woman with glasses, 
large expressive eyes, smooth skin, detailed hair, 
school uniform, soft lighting, vibrant colors, 
high quality illustration, cel shading, 
Makoto Shinkai art style

负面提示词：realistic, photo, 3d render, ugly, 
deformed, blurry, low quality, watermark
```

### 场景 2：风景照片 → 吉卜力风格
**用户输入**：一张山间小屋的照片

**输出示例**：
```
主提示词：Studio Ghibli style landscape, cozy cottage 
in mountains, lush green trees, soft watercolor texture, 
warm golden light, peaceful atmosphere, detailed nature, 
hand-painted look, Hayao Miyazaki inspired
```

---

## 参考资源

- 详细风格提示词库：`references/style-prompts.md`
- 平台参数指南：`references/platform-guide.md`
- 提示词优化技巧：`references/prompt-tips.md`
