---
name: video-analyzer
description: 分析视频内容，支持今日头条、抖音、B站、西瓜视频等平台。自动下载视频、语音转文字(faster-whisper)、繁简转换、生成内容摘要。当用户提供视频链接并要求分析视频内容、总结视频、看看视频讲什么时使用此技能。
---

# Video Analyzer - 视频内容分析

分析视频链接的内容，自动完成：下载 → 语音转文字 → 繁简转换 → 内容分析。

## 支持平台

所有 yt-dlp 支持的平台，包括：
- 今日头条
- 抖音
- B站
- 西瓜视频
- YouTube
- 微博视频
- 其他 1800+ 平台

## 使用方式

用户提供视频链接，说"分析这个视频"、"看看这个视频讲什么"、"总结这个视频"等。

## 工作流程

```
视频链接 → yt-dlp 下载视频 → faster-whisper 本地转录 → opencc 繁简转换 → AI 总结
```

## 环境要求

### 必需工具
- `yt-dlp`：下载视频
- `faster-whisper`：本地语音转文字（pip install faster-whisper）
- `opencc-python-reimplemented`：繁简转换（pip install opencc-python-reimplemented）

### 无需额外配置
- ❌ 不需要 API Key
- ❌ 不需要 ffmpeg（av 库直接读取视频音轨）
- ❌ 不需要联网（模型下载后离线可用）

### 首次运行
首次运行时 faster-whisper 会从 HuggingFace 下载模型（约 140MB base 模型）。
脚本已内置国内镜像 `hf-mirror.com`，无需手动配置。

## 脚本说明

### scripts/analyze_video.py

主脚本，完成完整流程：

```bash
# 基本用法
python scripts/analyze_video.py <视频URL>

# 指定模型
python scripts/analyze_video.py <视频URL> --model small

# 输出 JSON
python scripts/analyze_video.py <视频URL> --json

# 不显示时间戳
python scripts/analyze_video.py <视频URL> --no-timestamps
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--model` | base | Whisper 模型：tiny/base/small/medium/large-v3 |
| `--lang` | zh | 语言代码 |
| `--no-timestamps` | - | 不显示时间戳 |
| `--json` | - | 输出完整 JSON |
| `--keep-temp` | - | 保留临时视频文件 |

### 模型选择建议

| 模型 | 大小 | 速度 | 精度 | 推荐场景 |
|------|------|------|------|----------|
| tiny | ~75MB | 最快 | 一般 | 快速预览 |
| base | ~140MB | 快 | 较好 | 日常使用 ⭐ |
| small | ~500MB | 中等 | 好 | 需要更高精度 |
| medium | ~1.5GB | 较慢 | 很好 | 专业场景 |
| large-v3 | ~3GB | 最慢 | 最好 | 最高精度需求 |

## AI 总结步骤

拿到转录文本后，AI 应生成结构化总结：
1. 视频基本信息（标题、时长、UP主）
2. 核心内容概述（1-2句话）
3. 关键知识点/要点（分条列出）
4. 重要数据/结论
5. 模型局限性（如适用）

## 错误处理

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| yt-dlp 失败 | 平台不支持/网络问题 | 尝试其他平台或检查网络 |
| HuggingFace 超时 | 首次下载模型网络不通 | 已内置 hf-mirror.com 镜像 |
| 内存不足 | 模型太大 | 换更小的模型（如 tiny） |
| 转录质量差 | base 模型精度有限 | 换 small 或 medium 模型 |

## 注意事项

- 视频下载到临时目录，分析完成后自动清理
- 使用 `--keep-temp` 可保留视频文件
- 全程本地运行，不上传任何数据到外部服务器
- 360p 画质已足够转录，无需下载高清视频
