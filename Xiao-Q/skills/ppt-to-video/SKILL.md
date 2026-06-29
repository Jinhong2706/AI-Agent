---
name: ppt-to-video
description: "This skill converts PDF presentation slides, a speech manuscript, and a reference voice into a complete narrated presentation video with synchronized subtitles. It should be used when the user wants to generate a presentation video from PPT/PDF slides with voice cloning, text-to-speech, and subtitle generation. Trigger phrases include PPT to video, generate presentation video, slides to video, 演讲视频, PPT转视频, 幻灯片生成视频, voice cloning presentation, or any request involving converting slide decks into narrated videos with speech synthesis."
---

# PPT转视频：演讲视频生成器

## 概述

本技能将 PDF 幻灯片 + 演讲稿转换为带同步字幕的完整演讲视频。所有处理均在本地运行（Qwen3-TTS）或使用免费在线服务（edge-tts），无需付费 API。

**TTS 引擎（二选一，优先 Qwen3-TTS）：**
- **Qwen3-TTS**（推荐）：阿里通义千问团队开源语音合成模型，本地运行，**支持声音克隆**（提供参考音频即可复刻音色），也支持预设音色
- **edge-tts**（备选）：微软免费在线 TTS 服务，无需 GPU，需联网，仅支持预设音色（不支持声音克隆）

**核心流水线**：演讲稿处理 → 语音合成（可选声音克隆） → 视频生成 → 最终合并

---

## 🎬 Remotion 模式（原生组件）

> 当用户明确要求使用 **Remotion** 生成视频时，启用此模式。

### 核心规则（强制）

**禁止使用 PPT/PDF 截图作为视频内容。必须用 Remotion 原生 TSX 组件重新设计每一页的视觉内容。**

**动画触发帧必须与 `timing_data.json` 中对应句子的时间戳对齐。禁止使用固定帧数或固定循环触发动画。**

原因：截图分辨率低、有白边、无法动画、无法响应字幕节奏；原生组件全矢量、动画精确可控、体积更小。

### 工作流差异

| 步骤 | 传统模式（FFmpeg）| Remotion 模式 |
|------|-----------------|--------------|
| 步骤 0-3 | 相同（演讲稿处理 + TTS 合成）| 相同 |
| 步骤 4 | PDF → 截图 → FFmpeg 合成 | **TSX 组件设计每页 + Remotion 渲染** |
| 字幕 | ASS/SRT 烧录 | **Remotion 原生字幕组件（精确逐句同步）** |
| 音频 | FFmpeg 混流 | **`<Audio>` 组件（每页独立音频）** |

### 详细规范

完整的设计规范、布局模板、hooks 使用规则、字幕同步机制见：

**[references/remotion-guide.md](references/remotion-guide.md)**

---

## 前置条件

开始前，请确认以下工具和模型已安装。

### 🔍 一键环境检查（推荐）

**首次使用前，运行环境检查脚本确认所有依赖已就绪：**

```bash
python {SKILL_DIR}/scripts/check_environment.py
```

该脚本会检查：
- ✅ 系统工具（FFmpeg、ffprobe）
- ✅ Python 核心依赖（numpy、PyMuPDF）
- ✅ TTS 引擎（qwen-tts 或 edge-tts）
- ⚠️ 可选依赖（whisper、demucs 等）
- 📦 已缓存的 Qwen3-TTS 模型
- 🔤 系统字体

如果检测到缺失依赖，脚本会给出具体的安装命令。

### 必需的系统工具
- **FFmpeg**（含 ffprobe）：`brew install ffmpeg-full`（macOS，完整版）或系统包管理器
- **Python 3.8+** 及 pip

### 必需的 Python 包
```bash
pip install numpy PyMuPDF
```

### TTS 引擎（至少安装其一）
```bash
# 方式一（推荐）：Qwen3-TTS — 本地高质量语音合成
pip install -U qwen-tts

# 方式二：edge-tts — 微软在线 TTS，无需 GPU
pip install edge-tts
```

### 可选（增强功能）
- **openai-whisper**（`pip install openai-whisper`）：语音转文字（步骤1筛选参考片段时需要）
- **Demucs**（`pip install demucs`）：人声分离（仅需从视频中提取人声时使用）
- **pdf2image** + Poppler：备用 PDF 转换后端

### ⚡ 快速安装所有推荐依赖

```bash
# 核心依赖
pip install numpy PyMuPDF

# 推荐 TTS 引擎
pip install -U qwen-tts

# 可选：完整功能
pip install edge-tts openai-whisper demucs
```

## 工作流程

### 步骤 0（必需）：LLM 整理演讲稿格式

**重要**：用户提供的演讲稿可能是各种格式（Word 导出、笔记软件导出、手动编写等），在调用 `step2_process_speech.py` 之前，**必须先使用 LLM 将演讲稿整理成标准格式**。

#### 整理标准

演讲稿必须符合以下 Markdown 结构：

```markdown
## 第 1 页 幻灯片标题

第 1 页的演讲内容第一段。

第 1 页的演讲内容第二段。

---

## 第 2 页 另一页标题

第 2 页的演讲内容。
```

#### LLM 整理提示词

当用户提供了演讲稿但格式不符合标准时，执行以下步骤：

**1. 调用 LLM 整理格式：**

```
你是一个专业的演讲稿整理助手。请将用户输入的演讲稿整理成标准格式。

## 输出格式要求
1. 使用 ## 第 X 页 标题 的格式来标识每一页幻灯片的开始
2. 每页内容放在标题下方，使用连续的自然段落
3. 删除所有与演讲内容无关的元信息（如备注、作者、时间戳、邮箱等）
4. 保留演讲的核心文字内容和标点符号
5. 清理特殊格式字符，但保留标点
6. 如果原稿件没有明确的页码划分，请根据内容逻辑合理分页（每页建议200-400字）
7. 保持原文语义不变，不要添加或删减实质内容
8. 使用 --- 作为页面之间的分隔符

## 示例

### 示例输入（混乱格式）：
各位朋友大家好
Page 1
欢迎致辞
今天非常高兴...

### 示例输出：
## 第 1 页 欢迎致辞
各位朋友大家好，今天非常高兴。

---

## 第 2 页 主题介绍
...
```

**2. 将 LLM 返回的标准格式内容写入文件**（如 `output/step0_manuscript_formatted.md`）

**3. 后续步骤使用整理后的文件**，而非原始文件

### 输入要求

| 输入 | 必需 | 说明 | 示例 |
|------|------|------|------|
| **演讲稿** | ✅ 必需 | 按页划分的 Markdown 演讲稿 | `slides-speech.md` |
| **PDF 幻灯片** | ✅ 必需 | 演示文稿 PDF 文件 | `slides.pdf` |
| **参考音频** | ❌ 可选 | 用于 Qwen3-TTS 声音克隆的参考音频 | `reference_voice.wav` |

#### 📋 输入文件校验（推荐）

**运行流水线前，可使用校验脚本检查输入文件格式：**

```bash
python {SKILL_DIR}/scripts/validate_inputs.py \
    --speech_md <演讲稿.md> \
    --slides_pdf <幻灯片.pdf> \
    --reference_voice <参考音频.wav>  # 可选
```

该脚本会检查：
- PDF 文件有效性和页数
- 演讲稿格式是否符合标准（`## 第 X 页` 格式）
- 演讲稿页数与 PDF 页数是否匹配
- 参考音频时长和格式（如果提供）
- 特殊字符和数字的 TTS 兼容性

如果发现问题，脚本会给出具体的修复建议。

### 快速开始 — 一键运行

**使用 Qwen3-TTS + 声音克隆（推荐，需提供参考音频）**

```bash
python {SKILL_DIR}/scripts/run_pipeline.py \
    --speech_md <演讲稿.md> \
    --slides_pdf <幻灯片.pdf> \
    --output_dir <输出目录> \
    --tts_engine qwen3 \
    --reference_voice <参考音频.wav>
```

**使用 Qwen3-TTS + 预设音色（无参考音频时）**

```bash
python {SKILL_DIR}/scripts/run_pipeline.py \
    --speech_md <演讲稿.md> \
    --slides_pdf <幻灯片.pdf> \
    --output_dir <输出目录> \
    --tts_engine qwen3 \
    --speaker "Vivian"
```

**指定使用 edge-tts**

```bash
python {SKILL_DIR}/scripts/run_pipeline.py \
    --speech_md <演讲稿.md> \
    --slides_pdf <幻灯片.pdf> \
    --output_dir <输出目录> \
    --tts_engine edge \
    --edge_voice "zh-CN-XiaoxiaoNeural"
```

将 `{SKILL_DIR}` 替换为本技能目录的绝对路径。

**常用选项：**

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `--tts_engine` | `auto` | TTS 引擎：`auto`（自动选择）/ `qwen3` / `edge` |
| `--reference_voice` | 无 | 参考音频路径（Qwen3-TTS 声音克隆用，提供即克隆） |
| `--speaker` | `Vivian` | Qwen3-TTS 预设音色（无参考音频时使用） |
| `--edge_voice` | `zh-CN-XiaoxiaoNeural` | edge-tts 语音名称 |
| `--resolution` | `1920x1080` | 视频分辨率 |
| `--sentence_pause` | `0.4` | 句子间停顿（秒） |
| `--slide_pause` | `1.0` | 页面间停顿（秒） |
| `--subtitle_mode` | `burn` | `burn`（烧录）/`soft`（软字幕）/`both`（两者） |
| `--font_name` | `PingFang SC` | 字幕字体 |
| `--font_size` | `38` | 字幕字号 |
| `--skip_steps` | 无 | 跳过的步骤（如 `1` 跳过声音提取） |
| `--dpi` | `200` | PDF 渲染质量 |

### Qwen3-TTS 可用音色

| 音色名称 | 描述 | 母语 |
|----------|------|------|
| **Vivian** | 明亮的年轻女声 | 中文 |
| **Serena** | 温暖、温柔的年轻女声 | 中文 |
| **Uncle_Fu** | 成熟的男性声音，醇厚音色 | 中文 |
| **Dylan** | 年轻的北京男声 | 中文（北京） |
| **Eric** | 活泼的成都男声 | 中文（四川） |
| **Ryan** | 富有节奏感的男声 | 英文 |
| **Aiden** | 阳光的美国男声 | 英文 |

### edge-tts 推荐语音

| 语音名称 | 描述 |
|----------|------|
| `zh-CN-XiaoxiaoNeural` | 晓晓（女，温暖自然） |
| `zh-CN-XiaoyiNeural` | 晓伊（女，亲切活泼） |
| `zh-CN-YunjianNeural` | 云健（男，沉稳大气） |
| `zh-CN-YunxiNeural` | 云希（男，年轻阳光） |
| `zh-CN-YunyangNeural` | 云扬（男，新闻播报） |

### 分步执行

如需更精细控制，可逐步运行：

**（步骤 0 在上方"步骤 0（必需）"中说明，推荐在所有步骤之前执行）**

#### 步骤 1：提取人声并筛选参考片段（可选）

从参考视频/音频中提取纯净人声，自动筛选最佳参考片段（5~10秒）。

**处理流程**：
1. 仅提取前 3 分钟音频（避免长视频全量处理）
2. 使用 Demucs 分离人声与背景噪声
3. 使用 Whisper 转录人声为带时间戳的文字
4. 自动筛选一句 5~10 秒、语句独立、声音清晰的片段
5. 截取该片段的音频与文字，传给第3步声音克隆

```bash
python {SKILL_DIR}/scripts/step1_extract_voice.py \
    --input <视频或音频路径> \
    --output_dir <输出目录>/step1_voice
```

**脚本位置**：`scripts/step1_extract_voice.py`

**筛选评分维度**：
- 时长适中（接近 7 秒最佳，满分 30）
- 语句完整（以句号结尾更佳，满分 20）
- 声音清晰（RMS 能量 + 静音比例，满分 30）
- 文字长度合理（20~80字，满分 10）
- 位置偏好（靠前片段通常更好，满分 10）

**输出**：
- `reference_voice.wav` — 最佳参考音频片段（5~10秒）
- `reference_text.txt` — 对应的转录文字
- `reference_info.json` — 片段详细信息（时间、文字、评分等）

#### 步骤 2：处理演讲稿

解析并清洗 Markdown 演讲稿，生成结构化 TTS 数据。

```bash
python {SKILL_DIR}/scripts/step2_process_speech.py \
    --input <演讲稿.md> \
    --output <输出目录>/step2_speech_data.json
```

**脚本位置**：`scripts/step2_process_speech.py`

**处理流程**：
1. 从 `## 第 X 页` 标题解析页面边界
2. 清洗 Markdown 格式：移除 `**粗体**`、`*斜体*`、时间标注、引用
3. 将破折号转换为逗号以符合自然语流
4. 在标点处拆分句子
5. 处理超长句子（>80字符）在逗号处拆分
6. 生成 TTS 友好的发音文本（`tts_sentences`），包括：
   - 术语发音规范化（从 `config/pronunciation_map.json` 加载）
   - **目录路径读音转换**：自动将路径转为口语化表达

**目录路径读音规则**：

字幕（`sentences`）保持原始书面写法不变，TTS 文本（`tts_sentences`）按以下规则转换：

| 书面写法 | TTS 读音 | 规则 |
|----------|----------|------|
| `~/.codebuddy/skills/` | 家目录下 codebuddy skills 目录 | `~/` → "家目录下"，末尾 `/` → "目录" |
| `.codebuddy/skills/` | codebuddy skills 目录 | 隐藏目录去掉前导 `.`，末尾 `/` → "目录" |
| `./config/` | 当前目录下 config 目录 | `./` → "当前目录下" |
| `references/api.md` | references api点md | 文件扩展名用"点"连接 |

> 💡 智能去重：如果路径后面已有"目录"或"下"等字样，不会重复追加"目录"。例如 `scripts/ 目录下` → "scripts 目录下"。

**输出**：包含每页句子的结构化 JSON

#### 步骤 3：语音合成

使用 Qwen3-TTS（支持声音克隆）或 edge-tts（预设音色）生成演讲音频。

```bash
# Qwen3-TTS + 声音克隆
python {SKILL_DIR}/scripts/step3_clone_voice.py \
    --speech_json <演讲数据.json> \
    --output_dir <输出目录>/step3_tts \
    --tts_engine qwen3 \
    --reference_voice <参考音频.wav>

# Qwen3-TTS + 预设音色
python {SKILL_DIR}/scripts/step3_clone_voice.py \
    --speech_json <演讲数据.json> \
    --output_dir <输出目录>/step3_tts \
    --tts_engine qwen3 \
    --speaker "Vivian"

# edge-tts（预设音色）
python {SKILL_DIR}/scripts/step3_clone_voice.py \
    --speech_json <演讲数据.json> \
    --output_dir <输出目录>/step3_tts \
    --tts_engine edge \
    --edge_voice "zh-CN-XiaoxiaoNeural"
```

**脚本位置**：`scripts/step3_clone_voice.py`

**处理流程**：
1. 自动检测可用的 TTS 引擎（Qwen3-TTS 优先，edge-tts 备选）
2. Qwen3-TTS 模式：
   - 有参考音频 → 声音克隆模式（使用 Base 模型，克隆参考音色）
   - 无参考音频 → 预设音色模式（使用 CustomVoice 模型，内置音色）
3. edge-tts 模式：使用微软在线预设音色（不支持声音克隆）
4. 逐句生成音频
5. 插入句子间停顿（0.4秒）和页面间停顿（1.0秒）
6. 记录精确的时间元数据
7. 拼接为完整演讲音频

**输出**：
- `full_speech.wav` — 完整演讲音频
- `timing_data.json` — 精确时间数据（含 tts_engine 字段标记引擎）
- `sentences/` — 逐句音频文件
- `slides/` — 逐页音频文件

#### 步骤 4：生成幻灯片视频

将 PDF 幻灯片转换为与音频时长匹配的视频。

```bash
python {SKILL_DIR}/scripts/step4_generate_video.py \
    --pdf <幻灯片.pdf> \
    --timing_json <时间数据.json> \
    --output_dir <输出目录>/step4_video
```

**脚本位置**：`scripts/step4_generate_video.py`

**输出**：`slides_video.mp4` — 无声幻灯片视频

#### 步骤 5：合并视频、音频和字幕

将所有组件合并为最终演讲视频。

```bash
python {SKILL_DIR}/scripts/step5_merge_all.py \
    --video <幻灯片视频.mp4> \
    --audio <完整音频.wav> \
    --timing_json <时间数据.json> \
    --output <最终输出.mp4>
```

**脚本位置**：`scripts/step5_merge_all.py`

**字幕样式**：白色文字，PingFang SC 字体，黑色描边，半透明阴影，底部居中。

**输出**：`final_presentation.mp4` — 带字幕的完整演讲视频

### 🔄 重新生成单句 TTS 音频

如果对某一句的 TTS 效果不满意，可以使用 `--regenerate` 参数只重新生成指定的句子，其余句子复用已有音频，然后自动重新拼接并合成最终视频。

**查看当前所有句子**：

```bash
# 查看 timing_data.json 中的句子列表
cat <输出目录>/step3_tts/timing_data.json | python3 -c "
import json,sys
data=json.load(sys.stdin)
for s in data['slides']:
    for sent in s['sentences']:
        print(f\"slide{s['slide_number']}_sent{sent['index']:03d}: {sent['text'][:60]}\")
"
```

**重新生成指定句子**（支持多种格式）：

```bash
# 格式1: slide<页码>_sent<句号>
python {SKILL_DIR}/scripts/run_pipeline.py \
    --speech_md <演讲稿.md> \
    --slides_pdf <幻灯片.pdf> \
    --output_dir <输出目录> \
    --reference_voice <参考音频.wav> \
    --regenerate slide1_sent000 slide3_sent002

# 格式2: <页码>:<句号>（更简洁）
python {SKILL_DIR}/scripts/run_pipeline.py \
    --speech_md <演讲稿.md> \
    --slides_pdf <幻灯片.pdf> \
    --output_dir <输出目录> \
    --regenerate 1:0 3:2

# 格式3: 整页重新生成
python {SKILL_DIR}/scripts/run_pipeline.py \
    --speech_md <演讲稿.md> \
    --slides_pdf <幻灯片.pdf> \
    --output_dir <输出目录> \
    --regenerate slide2
```

**注意事项**：
- 使用 `--regenerate` 时，步骤 1（声音提取）和步骤 2（演讲稿处理）会自动跳过
- 指定句子的音频文件会被新生成的文件覆盖
- 所有页面音频和完整音频会自动重新拼接
- `timing_data.json` 会自动更新
- 由于固定了随机种子（seed=42），同样的文本会生成一样的结果；如需不同效果，可配合 `--temperature 0.5` 使用
- 也可直接调用 step3 脚本单独使用 `--regenerate`

## 演讲稿格式

演讲稿应遵循标准 Markdown 结构（详见上方"步骤 0"）。`step2_process_speech.py` 会自动清洗以下格式：

**自动清洗处理**：
- Markdown 粗体/斜体：`**文字**` → `文字`
- 时间标注：`**（约 1 分钟）**` → 移除
- 引用块：`> 文字` → `文字`
- 代码反引号：`` `代码` `` → `代码`
- 破折号：`——` → `，`（符合自然语流）

## 常见问题排查

### 进程安全与断点续传

流水线内置了三重防护机制，避免并发冲突和重复工作：

1. **进程锁（Process Lock）**：`run_pipeline.py` 和 `step3_clone_voice.py` 均使用 `fcntl.flock()` 文件锁。同一输出目录下只允许一个流水线实例运行，重复启动会立即报错退出，不会产生多个进程竞争写入的问题。
2. **断点续传（Resume）**：步骤 3（TTS 生成）会自动检测已有的有效音频文件。如果流水线中途中断后重新运行，已成功生成的句子音频会被跳过，只生成缺失的部分，大幅节省时间。
3. **引擎一致性检查（Engine Consistency）**：输出目录会记录上次使用的 TTS 引擎。如果本次运行切换了引擎（如从 `qwen3` 切换到 `edge`），会自动清除旧引擎生成的音频并重新生成，避免混用不同引擎的音频导致音色不一致。

### TTS 引擎问题
- **Qwen3-TTS 加载失败**：确保已安装 `pip install -U qwen-tts`，需要较大内存（建议 8GB+）
- **edge-tts 连接失败**：检查网络连接，edge-tts 需要访问微软 TTS 服务
- **两个引擎都没安装**：至少安装一个 — `pip install -U qwen-tts` 或 `pip install edge-tts`

### PDF 转换
- 安装 PyMuPDF（`pip install PyMuPDF`）作为主后端
- 降级方案：`pip install pdf2image` + 安装 poppler

### 字幕渲染
- 验证字体存在：`fc-list | grep "PingFang"`
- Linux 系统：使用 `Noto Sans CJK SC` 替代 `PingFang SC`
- Windows 系统：使用 `Microsoft YaHei` 替代

### 音视频同步
- 确保 `timing_data.json` 时间数据一致
- 验证整个流水线使用 24kHz 采样率
- 检查 FFmpeg 版本支持 AAC 编码

## 相关资源

- **流水线技术指南**：`references/pipeline_guide.md` — 详细技术架构与设计
- **脚本目录**：`scripts/` — 所有可执行的流水线脚本
