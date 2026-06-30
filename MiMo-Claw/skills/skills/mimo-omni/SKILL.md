---
name: mimo-omni
description: 使用小米 MiMo 的多模态模型分析和理解图片、视频和音频。当用户发送图片/视频/音频附件，询问视觉内容，请求图片描述、OCR、物体检测、场景理解、视频分析或音频转录/理解时使用。
---

# 视觉与音频理解（MiMo API）

通过 `mimo_api.sh`（Curl）或 `mimo_api.py`（Python）调用小米 MiMo 多模态模型，支持图片、视频、音频输入。两个工具参数完全一致。

> **优先使用 `bash mimo_api.sh`**，仅当 bash/curl 不可用时才回退到 `python mimo_api.py`。


---

## 通用调用格式

问题参数支持任意自然语言，直接传入用户的原始 query 即可：

```bash
# 用户问什么就传什么，不需要改写
bash mimo_api.sh image /path/to/photo.jpg "<用户的问题>"
bash mimo_api.sh video /path/to/video.mp4 "<用户的问题>" --fps 1
bash mimo_api.sh audio /path/to/audio.wav "<用户的问题>"

# 示例：用户问「这张图里的猫是什么品种？」
bash mimo_api.sh image /path/to/cat.jpg "这张图里的猫是什么品种？"

# 示例：用户问「视频里的人在做什么运动？从几分几秒开始的？」
bash mimo_api.sh video /path/to/clip.mp4 "视频里的人在做什么运动？从几分几秒开始的？" --fps 2

# 示例：用户问「帮我把这段录音翻译成英文」
bash mimo_api.sh audio /path/to/recording.mp3 "帮我把这段录音翻译成英文"
```

---

## 图片

```bash
# 单图（URL）
bash mimo_api.sh image "https://example.com/photo.jpg" "描述这张图片" --max-tokens 65536
python mimo_api.py image "https://example.com/photo.jpg" "描述这张图片" --max-tokens 65536  # fallback

# 单图（本地文件）
bash mimo_api.sh image /path/to/image.png "图中有哪些物体？" --max-tokens 65536
python mimo_api.py image /path/to/image.png "图中有哪些物体？" --max-tokens 65536  # fallback

# 图片 OCR
bash mimo_api.sh image /path/to/screenshot.png "提取图中所有文字，保持排版结构" --max-tokens 262144
python mimo_api.py image /path/to/screenshot.png "提取图中所有文字，保持排版结构" --max-tokens 262144  # fallback

# 图表分析
bash mimo_api.sh image /path/to/chart.png "分析图表的趋势和关键数据点" --max-tokens 262144
python mimo_api.py image /path/to/chart.png "分析图表的趋势和关键数据点" --max-tokens 262144  # fallback

# 多图对比
bash mimo_api.sh images /path/to/img1.jpg /path/to/img2.jpg --question "比较这两张图片的异同" --max-tokens 65536
python mimo_api.py images /path/to/img1.jpg /path/to/img2.jpg --question "比较这两张图片的异同" --max-tokens 65536  # fallback
```

---

## 视频

参数说明：`--fps` 每秒采样帧数，`--resolution` 分辨率模式（default/max）

```bash
# 通用视频描述
bash mimo_api.sh video /path/to/video.mp4 "描述视频内容" --fps 1 --max-tokens 65536
python mimo_api.py video /path/to/video.mp4 "描述视频内容" --fps 1 --max-tokens 65536  # fallback

# 短视频（<30s，信息密度高）
bash mimo_api.sh video /path/to/short.mp4 "详细描述视频内容" --fps 2 --max-tokens 65536
python mimo_api.py video /path/to/short.mp4 "详细描述视频内容" --fps 2 --max-tokens 65536  # fallback

# 长视频摘要（>5min，控制 token）
bash mimo_api.sh video /path/to/long.mp4 "用3-5句话概括核心内容" --fps 0.5 --max-tokens 262144
python mimo_api.py video /path/to/long.mp4 "用3-5句话概括核心内容" --fps 0.5 --max-tokens 262144  # fallback

# 动作识别 / 体育赛事（高帧率）
bash mimo_api.sh video /path/to/sports.mp4 "识别视频中的关键动作" --fps 4 --max-tokens 65536
python mimo_api.py video /path/to/sports.mp4 "识别视频中的关键动作" --fps 4 --max-tokens 65536  # fallback

# 视频 OCR / 字幕提取（高分辨率）
bash mimo_api.sh video /path/to/video.mp4 "识别视频中所有文字" --fps 2 --resolution max --max-tokens 262144
python mimo_api.py video /path/to/video.mp4 "识别视频中所有文字" --fps 2 --resolution max --max-tokens 262144  # fallback

# 教学视频 / PPT 录屏（画面慢但文字多）
bash mimo_api.sh video /path/to/tutorial.mp4 "提取视频中的知识点" --fps 0.5 --resolution max --max-tokens 262144
python mimo_api.py video /path/to/tutorial.mp4 "提取视频中的知识点" --fps 0.5 --resolution max --max-tokens 262144  # fallback

# 视频中的图表分析
bash mimo_api.sh video /path/to/data.mp4 "分析视频中的图表数据" --fps 1 --resolution max --max-tokens 262144
python mimo_api.py video /path/to/data.mp4 "分析视频中的图表数据" --fps 1 --resolution max --max-tokens 262144  # fallback

# 多语言字幕翻译
bash mimo_api.sh video /path/to/foreign.mp4 "翻译视频中的字幕为中文" --fps 2 --resolution max --max-tokens 262144
python mimo_api.py video /path/to/foreign.mp4 "翻译视频中的字幕为中文" --fps 2 --resolution max --max-tokens 262144  # fallback
```

### 视频推荐配置速查

| 场景 | `--fps` | `--resolution` | `--max-tokens` |
|------|---------|----------------|----------------|
| 通用描述 | `1` | default | 65536 |
| 短视频 (<30s) | `2` | default | 65536 |
| 长视频摘要 (>5min) | `0.5` | default | 262144 |
| 动作识别 / 体育 | `4`~`8` | default | 65536 |
| OCR / 字幕提取 | `2` | max | 262144 |
| 教学 / PPT 录屏 | `0.5` | max | 262144 |
| 图表 / 数据分析 | `1` | max | 262144 |
| 字幕翻译 | `2` | max | 262144 |

> **Token 参考：** fps=1 → ~3168 tokens，fps=4 → ~6408 tokens（同一视频）。fps 翻倍 ≈ token 翻倍。

---

## 音频

```bash
# 音频转录（URL 直传）
bash mimo_api.sh audio "https://example.com/audio.wav" "转录音频内容" --max-tokens 65536
python mimo_api.py audio "https://example.com/audio.wav" "转录音频内容" --max-tokens 65536  # fallback

# 本地音频转录
bash mimo_api.sh audio /path/to/audio.mp3 "转录这段音频，区分说话人" --max-tokens 65536
python mimo_api.py audio /path/to/audio.mp3 "转录这段音频，区分说话人" --max-tokens 65536  # fallback

# 音频内容描述
bash mimo_api.sh audio /path/to/audio.wav "描述音频中的声音，包括语音、音乐和环境音" --max-tokens 65536
python mimo_api.py audio /path/to/audio.wav "描述音频中的声音，包括语音、音乐和环境音" --max-tokens 65536  # fallback
```

---

## 视频 + 音频联合

```bash
# 同时分析视频画面和音频内容
bash mimo_api.sh mixed --video /path/to/video.mp4 --audio /path/to/audio.mp3 "描述视频内容并转录音频" --max-tokens 262144
python mimo_api.py mixed --video /path/to/video.mp4 --audio /path/to/audio.mp3 "描述视频内容并转录音频" --max-tokens 262144  # fallback

# URL 也可以
bash mimo_api.sh mixed --video "https://example.com/v.mp4" --audio "https://example.com/a.wav" "视频讲了什么？音频说了什么？" --fps 1 --max-tokens 262144
python mimo_api.py mixed --video "https://example.com/v.mp4" --audio "https://example.com/a.wav" "视频讲了什么？音频说了什么？" --fps 1 --max-tokens 262144  # fallback
```

---

## 返回格式

API 原始返回为 JSON：
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "这张图片展现了一个充满自然质感的场景。画面主体是..."
      }
    }
  ],
  "usage": {
    "prompt_tokens": 4026,
    "completion_tokens": 474,
    "total_tokens": 4500
  }
}
```

脚本已自动解析，输出分为两部分：

- **stderr**（调试信息）：`[9.0s | prompt=4026, completion=474]`
- **stdout**（模型回复）：`choices[0].message.content` 的纯文本

处理方式：将 stdout 的内容直接作为回答返回给用户即可。

---

## 文件大小限制

- 本地文件会被 base64 编码后上传，**API 限制 base64 数据最大 10MB**
- 图片和音频通常不超限；**视频文件容易超限**
- 超限时 API 返回：`exceeded maximum size limit for video base64 data (max: 10MB)`
- **解决方案：** 大文件优先使用 URL 方式传入，而非本地路径：
  ```bash
  # 本地大视频会超限
  bash mimo_api.sh video /path/to/large.mp4 "描述内容"  # ❌ 可能超 10MB

  # 改用 URL
  bash mimo_api.sh video "https://example.com/large.mp4" "描述内容"  # ✅
  ```

---

## 超时与重试

- 默认超时 300s（5 分钟），适用于图片、短视频、音频
- **长视频（>2min）建议加 `--timeout 600`**（10 分钟）：
  ```bash
  bash mimo_api.sh video /path/to/long.mp4 "概括内容" --fps 0.5 --timeout 600
  ```
- 如果超时，按以下顺序重试：
  1. 降低 `--fps`（如 1 → 0.5）
  2. 改用 `--resolution default`（如果之前用了 max）
  3. 如果仍然超时，建议用户截取视频片段

---

## 文件说明

| 文件 | 用途 |
|------|------|
| `mimo_api.py` | Python CLI 调用工具 |
| `mimo_api.sh` | Bash/Curl CLI 调用工具（参数与 py 版一致） |
| `examples_mimo.py` | Python SDK 风格的函数库 |
| `examples_mimo_curl.sh` | Curl 调用示例集 |
