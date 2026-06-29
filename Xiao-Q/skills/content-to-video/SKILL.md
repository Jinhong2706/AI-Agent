---
name: content-to-video
description: >
  一键将内容转换成带讲解的视频。自动根据输入内容生成演讲稿、配图、语音讲解和视频。
  适用场景：用户想要快速生成讲解视频，包括教学视频、知识科普、内容讲解等。
  当用户说"帮我做个视频"、"生成讲解视频"、"把这段内容做成视频"、"我需要视频讲解"等类似请求时，使用此技能。
  也适用于需要将文档、文章、知识点转换成视频格式的场景。
---

# Content to Video - 一键内容转视频

## 概述

这个技能可以自动将任何内容转换成带讲解的视频，无需手动操作中间流程。

**输入：** 任何想要讲解的内容（主题、文章、知识点等）
**输出：** 完整的讲解视频（包含配图、语音讲解、字幕）

## 工作流程

### 第一步：理解内容并生成演讲稿

当用户提供内容后：

1. **分析内容结构**
   - 识别内容的核心主题和关键点
   - 确定合适的讲解风格（教学、科普、演示等）
   - 规划视频的大致时长和节奏

2. **生成演讲稿**
   - 将内容组织成适合视频讲解的结构
   - 每页/每段配一个核心要点
   - 演讲稿格式：
     ```markdown
     ## 第 1 页 [标题]
     [讲解内容，3-5句话，适合30-60秒讲解]
     
     ## 第 2 页 [标题]
     ...
     ```

### 第二步：生成配图（PPT或图片）

根据演讲稿自动生成配图：

**方案 A：使用 ppt-generator-skill（推荐）**
- 调用 ppt-generator-skill 生成带配图的PPT
- 自动根据内容选择合适的配图和布局
- 输出 .pptx 文件

**方案 B：使用 generate_image 生成独立图片**
- 为每一页演讲稿生成对应的配图
- 使用 generate_image 技能根据页面内容生成图片
- 保存为图片文件序列

### 第三步：生成语音讲解

使用 edge-tts 或类似工具生成语音：

```bash
edge-tts --text "演讲稿内容" --voice zh-CN-XiaoxiaoNeural --write-media output.mp3
```

- 为每一页生成对应的语音片段
- 自动选择合适的语音角色
- 确保语音与文字同步

### 第四步：合成视频

**如果使用PPT：**
- 将 PPT 转换为 PDF（使用 LibreOffice）
- 使用 ppt-to-video 技能的流程合成视频
- 自动添加字幕

**如果使用独立图片：**
- 使用 FFmpeg 将图片序列与音频合成
- 添加字幕和转场效果

## 使用示例

### 示例 1：简单主题讲解

**用户输入：**
```
帮我做一个关于"量子力学基础"的讲解视频
```

**技能执行：**
1. 生成演讲稿（10页，每页讲一个核心概念）
2. 使用 ppt-generator-skill 生成带配图的PPT
3. 将演讲稿转换成语音
4. 合成最终视频

### 示例 2：文章转视频

**用户输入：**
```
把这篇文章转换成视频讲解：[文章内容]
```

**技能执行：**
1. 提取文章核心要点
2. 重新组织成演讲稿
3. 生成配图和语音
4. 输出视频

### 示例 3：快速测试

**用户输入：**
```
快速生成一个关于"光合作用"的教学视频，5分钟
```

**技能执行：**
1. 按照5分钟时长规划内容（约8-10页）
2. 自动生成完整视频

## 技术实现细节

### 依赖的技能和工具

- **ppt-generator-skill**：生成PPT配图
- **ppt-to-video**：PPT转视频（如果使用PPT方案）
- **generate_image**：生成独立配图（如果使用图片方案）
- **edge-tts**：语音合成
- **LibreOffice**：PPT转PDF
- **FFmpeg**：视频合成

### 自动化脚本

创建一个自动化脚本来串联整个流程：

```bash
#!/bin/bash
# scripts/generate_video.sh

CONTENT="$1"
OUTPUT_DIR="$2"

# 1. 生成演讲稿
python3 scripts/generate_script.py "$CONTENT" > "$OUTPUT_DIR/script.md"

# 2. 生成PPT配图
node /path/to/ppt-generator-skill/scripts/generate.js \
  --topic "$CONTENT" \
  --pages 10 \
  --output "$OUTPUT_DIR/slides.pptx"

# 3. 转换PPT为PDF
libreoffice --headless --convert-to pdf \
  --outdir "$OUTPUT_DIR" "$OUTPUT_DIR/slides.pptx"

# 4. 生成语音
python3 scripts/generate_audio.py "$OUTPUT_DIR/script.md" "$OUTPUT_DIR/audio/"

# 5. 合成视频
python3 /path/to/ppt-to-video/scripts/run_pipeline.py \
  --speech_md "$OUTPUT_DIR/script.md" \
  --slides_pdf "$OUTPUT_DIR/slides.pdf" \
  --output_dir "$OUTPUT_DIR/video_output"
```

## 配置选项

用户可以通过参数控制视频生成：

- **--style**：视频风格（教学/科普/商务等）
- **--duration**：目标时长（分钟）
- **--voice**：语音角色
- **--pages**：PPT页数
- **--output**：输出路径

## 注意事项

1. **内容质量**：输入内容越清晰，生成的视频质量越高
2. **时长控制**：建议单次生成视频不超过10分钟
3. **配图风格**：可以根据内容自动选择合适的配图风格
4. **语音选择**：中文推荐使用 Xiaoxiao 或 Yunxi 语音

## 故障排查

### 问题：生成的演讲稿不理想
**解决：** 在输入时提供更详细的内容大纲或要点

### 问题：配图不符合预期
**解决：** 可以手动指定配图风格或使用 generate_image 单独生成

### 问题：语音合成失败
**解决：** 检查 edge-tts 是否正确安装，或切换到其他 TTS 引擎

## 未来改进

- [ ] 支持多种语音角色自动切换
- [ ] 支持视频片段的拼接
- [ ] 支持用户上传自己的PPT模板
- [ ] 支持直接生成竖屏视频（适合短视频平台）
- [ ] 支持自动添加背景音乐

---

**触发词示例：**
- "帮我做个视频"
- "生成讲解视频"
- "把这段内容做成视频"
- "我需要视频讲解"
- "make a video about..."
- "create a presentation video"

当用户表达类似意图时，自动触发此技能。
