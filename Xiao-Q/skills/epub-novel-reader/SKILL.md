---
name: epub-novel-reader
summary: "EPUB电子书阅读器 + Edge TTS 自然语音朗读"
description: >
  将任意 EPUB 电子书转换为带目录导航的 HTML 阅读器，并支持微软 Azure Neural 语音（TTS）朗读。
  触发词：阅读EPUB小说、epub阅读、语音朗读小说、电子书转阅读器、EPUB转HTML、小说语音朗读、Edge TTS朗读

trigger:
  - "阅读EPUB小说"
  - "epub阅读"
  - "语音朗读小说"
  - "电子书转阅读器"
  - "EPUB转HTML"
  - "小说语音朗读"
  - "Edge TTS朗读"

scripts:
  - scripts/extract_epub.py
  - scripts/build_reader.py
  - scripts/tts_server.py

requirements:
  - edge-tts

base_dir: "C:/Users/zxk/.workbuddy/skills/epub-novel-reader"
output_dir: "C:/Users/zxk/WorkBuddy/20260424105359"
---

# EPUB 小说阅读器 Skill

## 功能概述

1. **解析 EPUB** → 提取全部章节（JSON）
2. **生成 HTML 阅读器** → 带目录、搜索、翻页、主题、进度记忆
3. **Edge TTS 语音朗读** → 微软 Azure Neural 语音，中文自然度高，免费
4. **TTS 代理服务器** → 本地 HTTP 服务，支持语音选择、语速调节、自动缓存

## 工作流程

### Step 1: 启动 TTS 服务器（首次或重启后）

```bash
cd C:/Users/zxk/.workbuddy/skills/epub-novel-reader/scripts
python tts_server.py
```

或双击运行 `start_tts.bat`

> **后台运行**：服务器默认占用端口 8766，首次合成需要联网等待（约10-30秒），之后自动缓存到 `.tts_cache/` 目录。

### Step 2: 启动阅读器 HTTP 服务器

```bash
python -m http.server 8765 --directory <输出目录>
```

### Step 3: 打开阅读器

访问：`http://127.0.0.1:8765/读书器.html`

## 核心脚本

### extract_epub.py

解析 EPUB 文件，提取章节文本。

```bash
python extract_epub.py <epub文件路径> <输出JSON路径>
```

参数：
- `epub_path`: EPUB 文件路径
- `output_json`: 输出 JSON 路径（可选，默认 `chapters.json`）

输出格式：
```json
[
  {"id": 0, "title": "第一章 黑暗中的光", "content": ["第一段文字...", "第二段..."]},
  ...
]
```

### build_reader.py

从章节 JSON 生成 HTML 阅读器。

```bash
python build_reader.py <chapters.json> <输出HTML路径>
```

### tts_server.py

Edge TTS 本地代理服务器。

```bash
python tts_server.py [--port 8766]
```

API 接口：
- `GET /voices` → 返回 11 个可用语音列表
- `POST /tts` → body: `{text, voice, rate, volume}` → 返回 `audio/mpeg`
- `GET /tts?text=...&voice=...&rate=1.0` → 直接 GET 合成

## 语音列表

| ID | 名称 | 性别 | 推荐场景 |
|----|------|------|---------|
| zh-CN-XiaoxiaoNeural | 晓晓（标准女声） | 女 | **阅读首选** |
| zh-CN-XiaoyiNeural | 晓伊（柔和女声） | 女 | 情感小说 |
| zh-CN-YunxiNeural | 云希（情感男声） | 男 | 男性视角 |
| zh-CN-YunjianNeural | 云健（清晰男声） | 男 | 知识类 |
| zh-CN-YunxiaNeural | 云夏（男声） | 男 | 备用 |
| zh-CN-YunyangNeural | 云扬（男声） | 男 | 备用 |
| zh-HK-HiuGaaiNeural | 香港-晓积 | 女 | 粤语 |
| zh-TW-HsiaoChenNeural | 台湾-晓臻 | 女 | 台语 |
| zh-TW-YunJheNeural | 台湾-云哲 | 男 | 台语 |
| zh-CN-shaanxi-XiaoniNeural | 陕西话-小妮 | 女 | 方言趣味 |
| zh-CN-liaoning-XiaobeiNeural | 东北话-小北 | 女 | 方言趣味 |

## 踩坑经验

- tts_server.py 用 Python 3.14 运行时，必须先 `pip install edge-tts` 安装到该版本
- edge-tts 合成首次较慢（网络请求），建议先预热；结果自动缓存到 `.tts_cache/`
- HTML 阅读器的 TTS JS 中 `TTS_SERVER` 变量必须指向实际运行的服务器地址
- 多个 TTS 服务器同时运行会导致端口冲突，务必先 `Stop-Process python` 清场再启动
- Windows 下用 `python` 命令默认指向 uv 管理的 Python 3.11，TTS 服务器用 Python 3.14 时需明确指定路径
