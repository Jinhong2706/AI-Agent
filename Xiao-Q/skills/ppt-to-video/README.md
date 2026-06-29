# PPT转视频 (ppt-to-video) — CodeBuddy Skill

将 PDF 幻灯片 + 演讲稿转换为带同步字幕的完整演讲视频。

## ✨ 特性

- 🎙️ **声音克隆**：使用 Qwen3-TTS 克隆任意人声（提供参考音频即可）
- 🎨 **多种音色**：内置 9 种预设音色 + 微软 edge-tts 备选
- 📖 **智能字幕**：自动生成同步字幕（支持烧录/软字幕）
- 🔄 **全自动流程**：一键从演讲稿生成完整视频
- 💻 **本地运行**：无需付费 API，隐私数据不出本机

## 📦 安装

### 1. 将 skill 目录复制到 CodeBuddy skills 位置

```bash
# macOS / Linux
cp -r ppt-to-video ~/.codebuddy/skills/

# 或复制到项目目录
cp -r ppt-to-video <your-project>/.codebuddy/skills/
```

### 2. 安装依赖

**方式一：运行环境检查脚本（推荐）**

```bash
python ~/.codebuddy/skills/ppt-to-video/scripts/check_environment.py
```

脚本会检测缺失依赖并给出安装命令。

**方式二：手动安装**

```bash
# 系统工具
brew install ffmpeg-full  # macOS（完整版，更多编解码器）
# 或 apt-get install ffmpeg  # Linux

# Python 核心依赖
pip install numpy PyMuPDF

# TTS 引擎（至少安装其一）
pip install -U qwen-tts    # 推荐：本地高质量，支持声音克隆
pip install edge-tts       # 备选：需联网，仅预设音色

# 可选：完整功能
pip install openai-whisper demucs
```

## 🚀 快速开始

### 准备文件

1. **PDF 幻灯片**：将 PPT/Keynote 导出为 PDF
2. **演讲稿**：按页划分的 Markdown 文件（格式见下方）
3. **参考音频**（可选）：用于声音克隆的 5-15 秒人声片段

### 演讲稿格式

```markdown
## 第 1 页 欢迎致辞

各位朋友大家好，今天非常高兴能和大家分享这个话题。

---

## 第 2 页 主题介绍

今天我们要讨论的是人工智能的发展趋势。
```

### 运行

在 CodeBuddy 中使用自然语言触发：

> "帮我把 slides.pdf 和 speech.md 生成演讲视频"

或直接运行脚本：

```bash
python scripts/run_pipeline.py \
    --speech_md speech.md \
    --slides_pdf slides.pdf \
    --output_dir output/
```

## 📂 目录结构

```
ppt-to-video/
├── SKILL.md                 # Skill 主文件（CodeBuddy 读取）
├── README.md                # 本说明文件
├── scripts/
│   ├── run_pipeline.py      # 一键运行入口
│   ├── check_environment.py # 环境检查脚本
│   ├── validate_inputs.py   # 输入文件校验
│   ├── step1_extract_voice.py
│   ├── step2_process_speech.py
│   ├── step3_clone_voice.py
│   ├── step4_generate_video.py
│   └── step5_merge_all.py
├── references/
│   └── pipeline_guide.md    # 技术架构文档
└── assets/                  # 资源文件（如有）
```

## ⚙️ 常用参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--tts_engine` | `auto` | TTS 引擎：`auto`/`qwen3`/`edge` |
| `--reference_voice` | 无 | 参考音频路径（声音克隆用） |
| `--speaker` | `Vivian` | Qwen3-TTS 预设音色 |
| `--edge_voice` | `zh-CN-XiaoxiaoNeural` | edge-tts 语音 |
| `--resolution` | `1920x1080` | 视频分辨率 |
| `--subtitle_mode` | `burn` | `burn`/`soft`/`both` |

完整参数列表见 `run_pipeline.py --help`。

## 🎤 可用音色

### Qwen3-TTS 预设音色

| 音色 | 描述 |
|------|------|
| Vivian | 明亮的年轻女声（默认） |
| Serena | 温暖、温柔的年轻女声 |
| Uncle_Fu | 成熟的男性声音，醇厚音色 |
| Dylan | 年轻的北京男声 |
| Eric | 活泼的成都男声 |

### edge-tts 推荐语音

| 语音 | 描述 |
|------|------|
| zh-CN-XiaoxiaoNeural | 晓晓（女，温暖自然） |
| zh-CN-YunjianNeural | 云健（男，沉稳大气） |
| zh-CN-YunxiNeural | 云希（男，年轻阳光） |

## ❓ 常见问题

### Qwen3-TTS 模型下载慢？

首次运行会自动下载模型（约 2-4 GB）。可设置镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 字幕显示乱码？

检查系统字体，可通过 `--font_name` 指定：

```bash
--font_name "Noto Sans CJK SC"  # Linux
--font_name "Microsoft YaHei"   # Windows
```

### 音视频不同步？

确保整个流水线使用一致的采样率（默认 24kHz）。

## 📄 许可证

MIT License

## 🙏 致谢

- [Qwen3-TTS](https://github.com/QwenLM/Qwen2-Audio) — 阿里通义千问团队
- [edge-tts](https://github.com/rany2/edge-tts) — 微软 TTS 接口
- [FFmpeg](https://ffmpeg.org/) — 音视频处理
