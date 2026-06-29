#!/usr/bin/env python3
"""
视频内容分析脚本（增强版）
下载视频 → 语音转文字(faster-whisper) → 简繁转换(opencc) → 输出内容

优势：
- 本地离线运行，无需 API Key
- faster-whisper 转录，自动 VAD 过滤静音
- opencc 自动繁体→简体转换
- 不依赖 ffmpeg（av 库直接读取视频音轨）
- 支持 yt-dlp 所有平台
"""

import os
import sys
import json
import subprocess
import tempfile
import argparse
from pathlib import Path

# HuggingFace 国内镜像
os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')


def download_video(video_url, output_dir, format_selector="360p"):
    """下载视频（低画质即可，只需音频）"""
    output_path = os.path.join(output_dir, "video.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", format_selector,
        "-o", output_path,
        "--no-playlist",
        "--quiet",
        video_url,
    ]
    print(f"[1/4] 正在下载视频...", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"下载失败: {result.stderr}")

    # 找到下载的文件
    for f in os.listdir(output_dir):
        if f.startswith("video."):
            return os.path.join(output_dir, f)

    raise Exception("未找到下载的视频文件")


def get_video_info(video_url):
    """获取视频信息"""
    cmd = ["yt-dlp", "--dump-json", "--no-playlist", video_url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return {}


def transcribe_video(video_path, model_size="base", language="zh", beam_size=5):
    """使用 faster-whisper 转录视频"""
    print(f"[2/4] 加载 Whisper 模型 ({model_size})...", flush=True)
    from faster_whisper import WhisperModel
    
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print(f"[3/4] 正在转录音频...", flush=True)
    segments, info = model.transcribe(
        video_path,
        language=language,
        beam_size=beam_size,
        vad_filter=True,           # 过滤静音段
        vad_parameters=dict(
            min_silence_duration_ms=500,
        ),
    )
    
    # 收集所有片段
    transcript_lines = []
    for seg in segments:
        transcript_lines.append({
            "start": round(seg.start, 1),
            "end": round(seg.end, 1),
            "text": seg.text.strip(),
        })
    
    return transcript_lines, info


def convert_to_simplified(text_lines):
    """繁体转简体"""
    try:
        from opencc import OpenCC
        cc = OpenCC('t2s')  # 繁体→简体
        for line in text_lines:
            line["text"] = cc.convert(line["text"])
        return text_lines
    except ImportError:
        print("[警告] opencc 未安装，跳过繁简转换", flush=True)
        return text_lines


def format_transcript(text_lines, with_timestamps=True):
    """格式化转录文本"""
    if with_timestamps:
        lines = []
        for seg in text_lines:
            start_min = int(seg["start"]) // 60
            start_sec = seg["start"] % 60
            lines.append(f"[{start_min:02d}:{start_sec:05.2f}] {seg['text']}")
        return "\n".join(lines)
    else:
        return "\n".join(seg["text"] for seg in text_lines)


def analyze_video(video_url, model_size="base", language="zh", keep_temp=False):
    """完整分析流程"""
    result = {
        "url": video_url,
        "title": "",
        "duration": 0,
        "uploader": "",
        "transcript": "",
        "transcript_plain": "",
        "segments": [],
        "success": False,
        "error": None,
    }

    # 获取视频信息
    print("[0/4] 获取视频信息...", flush=True)
    video_info = get_video_info(video_url)
    result["title"] = video_info.get("title", "未知")
    result["duration"] = video_info.get("duration", 0)
    result["uploader"] = video_info.get("uploader", video_info.get("channel", "未知"))

    # 下载并转录
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            video_path = download_video(video_url, temp_dir)
            
            # 转录
            segments, info = transcribe_video(video_path, model_size=model_size, language=language)
            
            # 简繁转换
            segments = convert_to_simplified(segments)
            
            result["segments"] = segments
            result["transcript"] = format_transcript(segments, with_timestamps=True)
            result["transcript_plain"] = format_transcript(segments, with_timestamps=False)
            result["language"] = info.language
            result["language_probability"] = round(info.language_probability, 2)
            result["success"] = True

            if keep_temp:
                import shutil
                keep_dir = os.path.join(tempfile.gettempdir(), "video-analyzer-keep")
                os.makedirs(keep_dir, exist_ok=True)
                shutil.copy2(video_path, keep_dir)
                print(f"[保留] 视频已保存到: {keep_dir}")

        except Exception as e:
            result["error"] = str(e)
            print(f"处理失败: {e}", flush=True)

    return result


def main():
    parser = argparse.ArgumentParser(description="视频内容分析工具")
    parser.add_argument("url", help="视频 URL")
    parser.add_argument("--model", default="base", 
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper 模型大小 (默认: base)")
    parser.add_argument("--lang", default="zh", help="语言代码 (默认: zh)")
    parser.add_argument("--no-timestamps", action="store_true", help="不显示时间戳")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON")
    parser.add_argument("--keep-temp", action="store_true", help="保留临时视频文件")
    
    args = parser.parse_args()

    print(f"[4/4] 生成结果...", flush=True)
    result = analyze_video(args.url, model_size=args.model, language=args.lang, keep_temp=args.keep_temp)

    print("\n" + "=" * 60)
    print("📺 视频分析结果")
    print("=" * 60)
    print(f"标题: {result['title']}")
    print(f"时长: {result['duration']} 秒 ({result['duration']//60}分{result['duration']%60}秒)")
    print(f"上传者: {result['uploader']}")
    if result.get("language"):
        print(f"语言: {result['language']} (置信度: {result.get('language_probability', 'N/A')})")
    print("-" * 60)
    
    if result["success"]:
        if args.no_timestamps:
            print(result["transcript_plain"])
        else:
            print(result["transcript"])
    else:
        print(f"❌ 分析失败: {result['error']}")
    print("=" * 60)

    if args.json:
        print("\n📄 JSON 输出:")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
