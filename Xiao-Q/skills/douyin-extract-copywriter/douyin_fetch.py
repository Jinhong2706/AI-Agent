#!/usr/bin/env python3
"""
抖音视频采集技能 v2
用法:
  python douyin_fetch.py filter [--min-digg N] [--min-comment N] [--min-share N] [--keyword 关键字]
  python douyin_fetch.py download <video_id> [--keyword 关键字]
  python douyin_fetch.py transcript <video_id> [--file /path/to/video.mp4]
  python douyin_fetch.py info <video_id>

产物结构:
  output_dir/关键字/
    ├── yyyy-MM-dd 关键字.mp4
    └── yyyy-MM-dd 关键字.txt
"""

import asyncio
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# ============================================================
# 配置模块
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    "output_dir": "",
    "ffmpeg_path": "",
    "filter": {
        "rules": {
            "min_digg": 20000,
            "min_comment": 5000,
            "min_share": 5000,
            "logic": "digg AND (comment OR share)",
        },
        "process_count": 1,
        "candidates": [],
    },
    "browser": {
        "wait_timeout": 10,
        "api_pattern": "aweme/v1/web/aweme/detail/",
    },
    "download": {
        "timeout": 90,
        "chunk_size": 65536,
    },
    "subtitle": {
        "method": "api_first",
        "max_length": 200,
    },
}


def load_config() -> dict:
    """加载配置文件，缺失字段用默认值补全"""
    config = json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        _deep_merge(config, user_config)
    return config


def _deep_merge(base: dict, override: dict):
    """递归合并字典，override 的值覆盖 base"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def get_output_dir(config: dict, keyword: str = "") -> str:
    """
    获取输出目录，按搜索关键字分组。

    结构: output_base/关键字/
    如果 keyword 为空，则使用日期作为默认目录名。
    """
    output_base = config.get("output_dir", "").strip()
    if not output_base:
        output_base = os.path.join(os.path.expanduser("~"), "抖音下载")

    if keyword:
        group_dir = os.path.join(output_base, sanitize_filename(keyword))
    else:
        group_dir = os.path.join(output_base, date.today().strftime("%Y-%m-%d"))

    os.makedirs(group_dir, exist_ok=True)
    return group_dir


def get_video_filename(keyword: str, video_info: dict) -> str:
    """
    生成视频和文案文件名：yyyy-MM-dd 关键字

    从 video_info 中提取发布日期，格式化为 yyyy-MM-dd。
    """
    # 尝试从视频信息中获取发布时间（Unix 时间戳，秒级或毫秒级）
    create_time = video_info.get("create_time", 0)
    if create_time:
        # 抖音 create_time 通常是秒级时间戳
        if create_time > 1e12:
            create_time = create_time // 1000
        from datetime import datetime
        date_str = datetime.fromtimestamp(create_time).strftime("%Y-%m-%d")
    else:
        date_str = date.today().strftime("%Y-%m-%d")

    return f"{date_str} {keyword}"


def get_ffmpeg_path(config: dict) -> str:
    """获取 ffmpeg 可执行路径"""
    path = config.get("ffmpeg_path", "").strip()
    if path:
        return path
    # 尝试系统 PATH
    for cmd in ["ffmpeg", "ffmpeg.exe"]:
        if shutil.which(cmd):
            return cmd
    return "ffmpeg"


# ============================================================
# 工具函数
# ============================================================


def extract_keyword(desc: str) -> str:
    """从标题提取关键字作为文件名前缀：去#标签，去emoji，取前12字"""
    text = re.sub(r"#\S+", "", desc).strip()
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)
    keyword = text[:12].strip()
    if keyword and keyword[-1] in "的了是在和与":
        keyword = keyword[:-1]
    return keyword or "视频"


def sanitize_filename(name: str) -> str:
    """清理文件名，移除不合法字符"""
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def format_stats(stats: dict) -> str:
    """格式化互动数据"""
    return (
        f"👍{stats.get('digg_count', 0):,} "
        f"💬{stats.get('comment_count', 0):,} "
        f"⭐{stats.get('collect_count', 0):,} "
        f"🔗{stats.get('share_count', 0):,}"
    )


# ============================================================
# 浏览器模块 (Chrome MCP 交互)
# ============================================================

# 说明：本脚本设计为被 WorkBuddy AI 通过 Chrome MCP 调用。
# AI 负责操作浏览器（打开页面、拦截API、获取数据），
# 脚本负责后续的下载、文案提取等本地处理。
#
# get_video_info_from_mcp() 接收 AI 从 MCP 拿到的 API 响应数据，
# 解析出结构化的视频信息。

def parse_aweme_api_response(api_data: dict) -> dict:
    """
    解析抖音 aweme/v1/web/aweme/detail/ API 的响应数据。

    参数 api_data 应该是从 Chrome DevTools 的网络请求中拦截到的 JSON 响应体。
    返回结构化的视频信息字典。
    """
    aweme = (
        api_data.get("aweme_detail")
        or (api_data.get("aweme_list", [{}])[0] if "aweme_list" in api_data else None)
        or (api_data.get("item_list", [{}])[0] if "item_list" in api_data else None)
        or {}
    )

    stats = aweme.get("statistics", {})
    video_info = aweme.get("video", {})
    play_addr = video_info.get("play_addr", {}) or video_info.get("download_addr", {})
    urls = play_addr.get("url_list", []) or video_info.get("url_list", [])

    # 提取字幕轨道信息
    subtitle_infos = aweme.get("subtitle_infos", [])
    if not subtitle_infos:
        subtitle_infos = video_info.get("subtitle", {}).get("subtitleInfos", [])

    # 找最佳视频 URL（优先含音频的）
    best_url = _find_best_video_url(urls)

    return {
        "desc": aweme.get("desc", ""),
        "author": aweme.get("author", {}).get("nickname", ""),
        "stats": {
            "digg_count": stats.get("digg_count", 0),
            "comment_count": stats.get("comment_count", 0),
            "collect_count": stats.get("collect_count", 0),
            "share_count": stats.get("share_count", 0),
        },
        "duration": video_info.get("duration", 0) // 1000,
        "video_url": best_url,
        "all_video_urls": urls,
        "subtitle_infos": subtitle_infos,
        "aweme_id": aweme.get("aweme_id", ""),
        "author_id": aweme.get("author", {}).get("uid", ""),
        "create_time": aweme.get("create_time", 0),
    }


def _find_best_video_url(urls: list) -> str:
    """找到最佳视频URL（优先选含音频的混合流）"""
    if not urls:
        return ""
    # 优先: 包含 ve、audio、playwm 的 URL（通常是视频+音频混合流）
    priority_keywords = ["ve", "audio", "playwm", "play_addr", "douyinvod"]
    for kw in priority_keywords:
        for u in urls:
            if kw in u.lower():
                return u
    return urls[0]


async def get_video_info_via_script(video_id: str, config: dict) -> dict:
    """
    备用方案：当没有 MCP 环境时，用 Python 脚本直接获取视频信息。
    需要 httpx，通过请求抖音页面获取 SSR 数据。

    返回与 parse_aweme_api_response 相同格式的字典。
    """
    import httpx

    url = f"https://www.douyin.com/video/{video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            html = resp.text

        # 尝试从 SSR 渲染的 HTML 中提取 JSON 数据
        # 抖音会在 <script id="RENDER_DATA"> 中嵌入页面数据
        match = re.search(r'<script id="RENDER_DATA"[^>]*>([^<]+)</script>', html)
        if match:
            import urllib.parse
            raw_data = urllib.parse.unquote(match.group(1))
            ssr_data = json.loads(raw_data)

            # 遍历查找视频详情
            for key, value in ssr_data.items():
                if isinstance(value, dict):
                    # 可能在不同的 key 下
                    for item in [value] + list(value.values()):
                        if isinstance(item, dict) and "aweme_detail" in item:
                            return parse_aweme_api_response(item)
                        if isinstance(item, dict) and "awemeId" in item:
                            # 另一种 SSR 数据结构
                            stats = item.get("statistics", {})
                            video_info = item.get("video", {})
                            play_addr = video_info.get("playAddr", {})
                            urls = play_addr.get("urlList", []) if isinstance(play_addr, dict) else []

                            subtitle_infos = item.get("subtitleInfos", [])

                            return {
                                "desc": item.get("desc", ""),
                                "author": item.get("author", {}).get("nickname", ""),
                                "stats": {
                                    "digg_count": stats.get("diggCount", 0),
                                    "comment_count": stats.get("commentCount", 0),
                                    "collect_count": stats.get("collectCount", 0),
                                    "share_count": stats.get("shareCount", 0),
                                },
                                "duration": (video_info.get("duration", 0) or 0) // 1000,
                                "video_url": _find_best_video_url(urls),
                                "all_video_urls": urls,
                                "subtitle_infos": subtitle_infos,
                                "aweme_id": item.get("awemeId", ""),
                                "author_id": item.get("author", {}).get("uid", ""),
                                "create_time": item.get("createTime", 0),
                            }

        print("⚠️ 未能从页面提取到视频数据（SSR 数据解析失败）")
        return {}

    except Exception as e:
        print(f"❌ 获取视频信息失败: {e}")
        return {}


# ============================================================
# 下载模块
# ============================================================


async def download_video(video_url: str, out_file: str, config: dict) -> bool:
    """下载视频文件到指定路径"""
    import httpx

    timeout = config.get("download", {}).get("timeout", 90)
    chunk_size = config.get("download", {}).get("chunk_size", 65536)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(video_url, headers=headers, follow_redirects=True)
            total = int(resp.headers.get("content-length", 0))

            downloaded = 0
            with open(out_file, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100 // total
                        mb = downloaded / 1024 / 1024
                        print(f"\r  下载: {pct}% ({mb:.1f}MB)", end="", flush=True)
            print()

        size = os.path.getsize(out_file)
        print(f"  下载完成: {size / 1024 / 1024:.1f}MB → {out_file}")
        return True

    except Exception as e:
        print(f"  ❌ 下载失败: {e}")
        return False


# ============================================================
# 字幕/文案提取模块（双层方案）
# ============================================================


async def extract_subtitle_from_api(subtitle_infos: list) -> str:
    """
    方案一：从抖音 API 返回的 subtitle_infos 中提取字幕。

    subtitle_infos 格式示例:
    [
      {
        "LanguageCodeName": "zh",
        "Url": "https://...",
        "Format": "vtt",
        "SourceType": 1
      }
    ]
    返回字幕纯文本，失败返回空字符串。
    """
    if not subtitle_infos:
        return ""

    import httpx

    # 优先找中文字幕
    zh_subtitle = None
    any_subtitle = None

    for info in subtitle_infos:
        url = info.get("Url", "") or info.get("url", "")
        lang = info.get("LanguageCodeName", "") or info.get("languageCodeName", "")
        fmt = info.get("Format", "") or info.get("format", "vtt")

        if not url:
            continue

        if "zh" in lang.lower() or "cn" in lang.lower() or "chinese" in lang.lower():
            zh_subtitle = url
            break
        any_subtitle = url

    subtitle_url = zh_subtitle or any_subtitle
    if not subtitle_url:
        return ""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(subtitle_url)
            content = resp.text

        # 解析 VTT/SRT 格式
        text = _parse_subtitle_content(content)
        return text

    except Exception as e:
        print(f"  ⚠️ API字幕下载失败: {e}")
        return ""


def _parse_subtitle_content(content: str) -> str:
    """解析 VTT 或 SRT 字幕文件，返回纯文本"""
    lines = content.strip().split("\n")
    text_lines = []

    for line in lines:
        line = line.strip()
        # 跳过 VTT 头部、SRT 序号、时间戳
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if line.startswith("NOTE"):
            continue
        # 跳过纯时间戳行 (00:00:01.000 --> 00:00:03.000)
        if re.match(r"^\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[\.,]\d{3}", line):
            continue
        # 跳过纯数字序号
        if re.match(r"^\d+$", line):
            continue
        # 跳过 <c> 等标签行
        if line.startswith("<") and not re.search(r"[\u4e00-\u9fff]", line):
            continue

        # 清理 HTML 标签
        clean = re.sub(r"<[^>]+>", "", line).strip()
        # 只保留含中文或有实际内容的行
        if clean and len(clean) > 1:
            text_lines.append(clean)

    return "\n".join(text_lines)


async def extract_subtitle_via_asr(video_path: str, config: dict) -> str:
    """
    方案二：使用 faster-whisper 进行本地 ASR 语音转文字。

    流程：FFmpeg 提取音频 → faster-whisper 推理 → 返回文本
    """
    ffmpeg_path = get_ffmpeg_path(config)

    # 检查是否有音频轨道
    ffprobe_cmd = ffmpeg_path.replace("ffmpeg", "ffprobe", 1) if "ffmpeg" in ffmpeg_path else "ffprobe"
    try:
        probe = subprocess.run(
            [ffprobe_cmd, "-v", "quiet", "-print_format", "json", "-show_streams", video_path],
            capture_output=True, text=True, timeout=10,
        )
        if probe.returncode == 0:
            streams = json.loads(probe.stdout).get("streams", [])
            has_audio = any(s.get("codec_type") == "audio" for s in streams)
            if not has_audio:
                print("  ⚠️ 视频无音频轨道，跳过 ASR")
                return ""
    except Exception:
        pass

    # 提取音频到临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.wav")

        print("  🔊 提取音频中...")
        cmd = [ffmpeg_path, "-i", video_path, "-vn", "-acodec", "pcm_s16le",
               "-ar", "16000", "-ac", "1", "-y", audio_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            print(f"  ⚠️ FFmpeg 提取音频失败: {result.stderr[:200]}")
            return ""

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            print("  ⚠️ 音频文件太小，可能无音轨")
            return ""

        # 调用 faster-whisper
        print("  🤖 Whisper 语音识别中...")
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_path, language="zh", beam_size=5)

            print(f"     检测语言: {info.language} (概率: {info.language_probability:.2f})")

            lines = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    lines.append(text)

            result_text = " ".join(lines)
            return result_text

        except ImportError:
            print("  ⚠️ faster-whisper 未安装，请运行: pip install faster-whisper")
            return ""
        except Exception as e:
            print(f"  ⚠️ ASR 失败: {e}")
            return ""

    return ""


async def extract_transcript(video_info: dict, video_path: str = None, config: dict = None) -> str:
    """
    双层文案提取：API 字幕优先，ASR 兜底。

    返回提取到的文本内容。
    """
    if config is None:
        config = load_config()

    method = config.get("subtitle", {}).get("method", "api_first")
    max_length = config.get("subtitle", {}).get("max_length", 200)

    # 第一层：尝试 API 字幕
    if method == "api_first":
        subtitle_infos = video_info.get("subtitle_infos", [])
        if subtitle_infos:
            print("  📝 尝试 API 字幕提取...")
            text = await extract_subtitle_from_api(subtitle_infos)
            if text and len(text) > 10:
                print(f"  ✅ API 字幕提取成功 ({len(text)}字)")
                return text[:max_length] if max_length > 0 else text
            else:
                print("  ⚠️ API 字幕内容为空或太短，尝试 ASR")

    # 第二层：ASR 兜底
    if video_path and os.path.exists(video_path):
        print("  🎙️ 进入 ASR 语音识别模式...")
        text = await extract_subtitle_via_asr(video_path, config)
        if text:
            print(f"  ✅ ASR 提取成功 ({len(text)}字)")
            return text[:max_length] if max_length > 0 else text
        else:
            print("  ❌ ASR 也未能提取到文案")
    elif not video_path:
        print("  ⚠️ 无视频文件路径，无法执行 ASR")

    return ""


# ============================================================
# 文案保存模块
# ============================================================


def save_transcript_to_file(
    filepath: str,
    vid: str,
    desc: str,
    author: str,
    stats: dict,
    transcript_text: str,
    source: str = "unknown",
) -> str:
    """保存文案到指定文件路径，返回文件路径"""
    lines = [
        f"视频ID: {vid}",
        f"标题: {desc}",
        f"作者: {author}",
        f"互动: {format_stats(stats)}",
        f"文案来源: {source}",
        "=" * 50,
        "【口播文案】",
        "",
        transcript_text,
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


# ============================================================
# 筛选模块
# ============================================================


def filter_candidates(config: dict) -> list:
    """根据筛选规则过滤候选视频列表"""
    rules = config.get("filter", {}).get("rules", {})
    min_digg = rules.get("min_digg", 0)
    min_comment = rules.get("min_comment", 0)
    min_share = rules.get("min_share", 0)

    candidates = config.get("filter", {}).get("candidates", [])

    if not candidates:
        print("⚠️ 配置文件中没有候选视频列表（filter.candidates）")
        print("   请在 config.json 中添加候选视频，或直接使用 download 模式指定 video_id")
        return []

    print("=" * 60)
    print(f"筛选规则：点赞≥{min_digg:,} AND (评论≥{min_comment:,} OR 分享≥{min_share:,})")
    print("=" * 60)

    passed = []
    for item in candidates:
        vid = item.get("video_id", item[0] if isinstance(item, (list, tuple)) else "")
        desc = item.get("desc", item[1] if isinstance(item, (list, tuple)) else "")
        author = item.get("author", item[2] if isinstance(item, (list, tuple)) else "")
        digg = item.get("digg_count", item[3] if isinstance(item, (list, tuple)) and len(item) > 3 else 0)
        comment = item.get("comment_count", item[4] if isinstance(item, (list, tuple)) and len(item) > 4 else 0)
        collect = item.get("collect_count", item[5] if isinstance(item, (list, tuple)) and len(item) > 5 else 0)
        share = item.get("share_count", item[6] if isinstance(item, (list, tuple)) and len(item) > 6 else 0)

        ok = digg >= min_digg and (comment >= min_comment or share >= min_share)
        status = "✅" if ok else ("⚠️" if digg >= min_digg else "❌")

        print(f"{status} [{vid}] {desc[:40]}")
        print(f"   作者: {author}  👍{digg:,}  💬{comment:,}  ⭐{collect:,}  🔗{share:,}")

        if ok:
            passed.append({"video_id": vid, "desc": desc, "author": author})

    return passed


# ============================================================
# 主流程
# ============================================================


async def process_video(vid: str, config: dict, output_dir: str = None, keyword: str = "") -> dict:
    """
    完整处理一个视频：获取信息 → 下载 → 提取文案 → 保存。

    keyword 参数用于指定搜索关键字，决定输出目录和文件命名。
    如果为空，则从视频标题自动提取关键字。

    返回处理结果字典。
    """
    # 如果指定了 keyword，用它来确定输出目录；否则用默认目录
    if keyword and output_dir is None:
        output_dir = get_output_dir(config, keyword=keyword)
    elif output_dir is None:
        output_dir = get_output_dir(config)

    print(f"\n{'='*60}")
    print(f"处理视频: {vid}")
    print(f"{'='*60}")

    # 获取视频信息
    print("📡 获取视频信息...")
    video_info = await get_video_info_via_script(vid, config)

    if not video_info or not video_info.get("desc"):
        print("❌ 无法获取视频信息")
        return {"success": False, "error": "无法获取视频信息"}

    desc = video_info["desc"]
    author = video_info["author"]
    stats = video_info["stats"]
    duration = video_info.get("duration", 0)
    video_url = video_info.get("video_url", "")

    # 如果没有外部指定 keyword，从标题提取
    if not keyword:
        keyword = extract_keyword(desc)

    # 生成文件名前缀：yyyy-MM-dd 关键字
    file_prefix = get_video_filename(keyword, video_info)
    safe_prefix = sanitize_filename(file_prefix)

    print(f"  搜索关键字: {keyword}")
    print(f"  文件前缀: {safe_prefix}")
    print(f"  标题: {desc[:60]}")
    print(f"  作者: {author}")
    print(f"  时长: {duration}秒")
    print(f"  互动: {format_stats(stats)}")
    print(f"  字幕轨: {len(video_info.get('subtitle_infos', []))}个")

    result = {
        "success": True,
        "video_id": vid,
        "keyword": keyword,
        "desc": desc,
        "author": author,
        "stats": stats,
        "duration": duration,
    }

    # 下载视频
    mp4_file = None
    if video_url:
        mp4_file = os.path.join(output_dir, f"{safe_prefix}.mp4")

        if os.path.exists(mp4_file):
            print(f"  ⏭️  视频已存在，跳过下载: {mp4_file}")
        else:
            print("📥 下载视频...")
            ok = await download_video(video_url, mp4_file, config)
            if not ok:
                mp4_file = None
                print("  ⚠️ 视频下载失败，继续尝试提取文案")
    else:
        print("  ⚠️ 未获取到视频下载URL")

    # 提取文案
    print("\n📝 提取文案...")
    transcript = await extract_transcript(video_info, mp4_file, config)
    source = "未知"

    if transcript:
        # 判断来源
        if video_info.get("subtitle_infos"):
            source = "API字幕"
        else:
            source = "faster-whisper ASR"

        wenan_file = os.path.join(output_dir, f"{safe_prefix}.txt")
        save_transcript_to_file(wenan_file, vid, desc, author, stats, transcript, source)
        print(f"  ✅ 文案已保存: {wenan_file} ({len(transcript)}字)")
        result["transcript_file"] = wenan_file
        result["transcript_text"] = transcript
        result["transcript_source"] = source
    else:
        print("  ❌ 未能提取到文案")

    if mp4_file:
        result["video_file"] = mp4_file

    print(f"\n✅ 完成: {safe_prefix}")
    return result


# ============================================================
# 子命令入口
# ============================================================


async def cmd_filter(config: dict, args: list):
    """筛选+下载模式"""
    # 命令行参数覆盖筛选规则
    keyword = ""
    i = 0
    while i < len(args):
        if args[i] == "--min-digg" and i + 1 < len(args):
            config["filter"]["rules"]["min_digg"] = int(args[i + 1])
            i += 2
        elif args[i] == "--min-comment" and i + 1 < len(args):
            config["filter"]["rules"]["min_comment"] = int(args[i + 1])
            i += 2
        elif args[i] == "--min-share" and i + 1 < len(args):
            config["filter"]["rules"]["min_share"] = int(args[i + 1])
            i += 2
        elif args[i] == "--keyword" and i + 1 < len(args):
            keyword = args[i + 1]
            i += 2
        else:
            i += 1

    output_dir = get_output_dir(config, keyword=keyword) if keyword else get_output_dir(config)
    passed = filter_candidates(config)

    if not passed:
        print("\n无满足条件的候选视频")
        return

    process_count = config.get("filter", {}).get("process_count", 1)
    to_process = passed[:process_count]

    print(f"\n将处理 {len(to_process)} 个视频 → 输出目录: {output_dir}")
    results = []
    for item in to_process:
        result = await process_video(item["video_id"], config, output_dir=output_dir, keyword=keyword)
        results.append(result)

    return results


async def cmd_download(config: dict, args: list):
    """下载指定视频"""
    if not args:
        print("用法: python douyin_fetch.py download <video_id> [--keyword 关键字]")
        return

    vid = args[0]
    keyword = ""
    if "--keyword" in args:
        idx = args.index("--keyword")
        if idx + 1 < len(args):
            keyword = args[idx + 1]

    output_dir = get_output_dir(config, keyword=keyword) if keyword else get_output_dir(config)
    result = await process_video(vid, config, output_dir=output_dir, keyword=keyword)
    return result


async def cmd_transcript(config: dict, args: list):
    """仅提取文案"""
    if not args:
        print("用法: python douyin_fetch.py transcript <video_id> [--file /path/to/video.mp4]")
        return

    vid = args[0]
    video_path = None

    # 检查是否有 --file 参数
    if "--file" in args:
        idx = args.index("--file")
        if idx + 1 < len(args):
            video_path = args[idx + 1]

    print(f"提取文案: {vid}")

    video_info = await get_video_info_via_script(vid, config)
    if not video_info:
        print("❌ 无法获取视频信息")
        return

    transcript = await extract_transcript(video_info, video_path, config)
    if transcript:
        print(f"\n{'='*60}")
        print(f"📋 文案内容（{len(transcript)}字）：")
        print(f"{'='*60}")
        print(transcript)
        return {"transcript": transcript}
    else:
        print("❌ 未能提取到文案")
        return None


async def cmd_info(config: dict, args: list):
    """仅查看视频信息，不下载"""
    if not args:
        print("用法: python douyin_fetch.py info <video_id>")
        return

    vid = args[0]
    print(f"查询视频信息: {vid}\n")

    video_info = await get_video_info_via_script(vid, config)
    if not video_info:
        print("❌ 无法获取视频信息")
        return

    keyword = extract_keyword(video_info.get("desc", ""))
    print(f"视频ID: {vid}")
    print(f"关键字: {keyword}")
    print(f"标题: {video_info.get('desc', '')[:80]}")
    print(f"作者: {video_info.get('author', '')}")
    print(f"时长: {video_info.get('duration', 0)}秒")
    print(f"互动: {format_stats(video_info.get('stats', {}))}")
    print(f"视频URL: {'有' if video_info.get('video_url') else '无'}")
    print(f"字幕轨: {len(video_info.get('subtitle_infos', []))}个")

    if video_info.get("subtitle_infos"):
        for i, sub in enumerate(video_info["subtitle_infos"]):
            lang = sub.get("LanguageCodeName", sub.get("languageCodeName", "unknown"))
            url = sub.get("Url", sub.get("url", ""))
            print(f"  字幕[{i}]: 语言={lang}, URL={'有' if url else '无'}")

    return video_info


def print_usage():
    print("""
抖音视频采集技能 v2

用法:
  python douyin_fetch.py filter [--min-digg N] [--min-comment N] [--min-share N] [--keyword 关键字]
      从配置文件的候选列表中筛选并下载高互动视频
      --keyword 指定搜索关键字，决定输出目录分组

  python douyin_fetch.py download <video_id> [--keyword 关键字]
      下载指定视频 + 提取文案
      --keyword 指定搜索关键字，决定输出目录分组

  python douyin_fetch.py transcript <video_id> [--file /path/to/video.mp4]
      仅提取视频文案（API字幕优先，ASR兜底）

  python douyin_fetch.py info <video_id>
      仅查看视频信息，不下载

输出结构:
  output_dir/关键字/
    ├── yyyy-MM-dd 关键字.mp4
    └── yyyy-MM-dd 关键字.txt

配置文件: config.json（与本脚本同目录）
""")


async def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    config = load_config()
    command = sys.argv[1].lower()
    args = sys.argv[2:]

    commands = {
        "filter": cmd_filter,
        "download": cmd_download,
        "transcript": cmd_transcript,
        "info": cmd_info,
    }

    if command in commands:
        await commands[command](config, args)
    else:
        print(f"未知命令: {command}")
        print_usage()


if __name__ == "__main__":
    asyncio.run(main())
