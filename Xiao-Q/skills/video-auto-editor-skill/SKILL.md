---
name: video-auto-editor
description: "视频剪辑自动化处理工具。支持本地视频截取、字幕生成(Whisper)、字幕嵌入、视频拼接、格式转换/缩放、添加水印、音频提取/替换、直播切片、JSON工作流编排等功能。适用于录屏后期、直播回放切片、短视频批量处理等场景。"
author: WorkBuddy
agent_created: true
commands:
  - trim: "截取视频片段 (需指定 start/end/duration)"
  - subtitle: "Whisper语音识别生成SRT字幕"
  - burn: "将SRT字幕硬编码嵌入视频"
  - concat: "拼接多个视频文件"
  - convert: "格式转换/分辨率缩放"
  - watermark: "叠加图片水印"
  - audio: "提取音频文件"
  - replace-audio: "替换或混合视频音频"
  - slice: "直播回放按时长切分"
  - workflow: "从JSON配置批量执行多步骤"
---

# 视频剪辑自动化处理技能 (video-auto-editor)

## 前置条件

### 必要依赖

1. **FFmpeg** — 核心视频处理引擎
   - Windows: 下载后加入 `PATH`，或放在 `~/.workbuddy/binaries/ffmpeg/bin/`
   - 验证: `ffmpeg -version`
   - 本技能默认查找的系统 `PATH` 中的 `ffmpeg`

2. **Python 3.8+** 及以下包:
   ```bash
   pip install openai-whisper moviepy pillow
   ```

### 可选依赖
   - `openpyxl` — 如需写入Excel格式报告

## 用法

### 命令行方式

```bash
# 环境检查
python scripts/video_auto_editor.py check

# 查看视频信息
python scripts/video_auto_editor.py info input.mp4

# 截取片段
python scripts/video_auto_editor.py trim input.mp4 -s 00:05:00 -e 00:10:00 -o clip.mp4

# 生成字幕(Whisper)
python scripts/video_auto_editor.py subtitle input.mp4 --model base

# 嵌入字幕
python scripts/video_auto_editor.py burn input.mp4 -s input.srt -o output.mp4

# 拼接视频
python scripts/video_auto_editor.py concat "video1.mp4,video2.mp4" -o merged.mp4

# 格式转换
python scripts/video_auto_editor.py convert input.mp4 -o output.mp4 -r 1920x1080

# 添加水印
python scripts/video_auto_editor.py watermark input.mp4 logo.png -o output.mp4

# 提取音频
python scripts/video_auto_editor.py audio input.mp4 -f mp3

# 替换音频
python scripts/video_auto_editor.py replace-audio video.mp4 audio.mp3 -o output.mp4 --mix

# 直播切片(每5分钟一段)
python scripts/video_auto_editor.py slice input.mp4 -d 300 -o ./clips/

# JSON工作流(批量执行多步骤)
python scripts/video_auto_editor.py workflow config.json
```

### Python API 方式

```python
from scripts.video_auto_editor import (
    check_ffmpeg, get_video_info,
    trim_video, generate_subtitles, burn_subtitles,
    concat_videos, convert_video,
    add_watermark, add_intro_outro,
    extract_audio, replace_audio,
    live_slice, live_slice_by_markers,
    run_from_json
)

# 查看信息
info = get_video_info("input.mp4")
print(info)

# 截取
trim_video("input.mp4", "clip.mp4", start_time="00:05:00", end_time="00:10:00")

# 字幕生成+嵌入
generate_subtitles("input.mp4", model_size="base")
burn_subtitles("input.mp4", "output.mp4", "input.srt")
```

## 工作流配置 (JSON)

通过 `workflow` 命令可批量执行多步骤流水线:

```json
{
  "input": "input_video.mp4",
  "output": "output/final.mp4",
  "work_dir": "output",
  "steps": [
    {"action": "trim", "params": {"start": "00:05:00", "end": "00:10:00"}},
    {"action": "subtitle", "params": {"model": "base"}},
    {"action": "burn_subtitle", "params": {"font_size": 28}},
    {"action": "convert", "params": {"resolution": "1920x1080", "bitrate": "5M"}},
    {"action": "watermark", "params": {"image": "logo.png", "position": "top-right"}},
    {"action": "extract_audio", "params": {"format": "mp3"}}
  ]
}
```

## 安全说明

- 本工具仅操作**本地视频文件**，不联网、不上传数据
- Whisper 语音识别为本地模型，音频数据不出本机
- 所有 FFmpeg 命令仅作用于用户指定的文件路径，不涉及系统级操作
- 请确保输入文件来源可信，避免处理恶意构造的媒体文件
