#!/usr/bin/env python3
"""
视频剪辑自动化处理工具 - Video Auto Editor
===========================================
支持功能：视频截取、字幕生成与嵌入、视频拼接、格式转换、片头片尾/水印、音频处理、直播切片

依赖：pip install openai-whisper moviepy pillow openpyxl
需安装 FFmpeg 并加入系统 PATH
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Optional, List, Tuple, Dict


# ============================================================
# 1. 基础工具 - 检查环境 / 获取视频信息
# ============================================================

def check_ffmpeg() -> bool:
    """检查 FFmpeg 是否可用"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, text=True)
        print("[✓] FFmpeg 可用")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[✗] FFmpeg 未安装，请先安装 FFmpeg 并加入系统 PATH")
        return False


def get_video_info(video_path: str) -> Dict:
    """获取视频基本信息（时长、分辨率、编码等）"""
    try:
        import json as _json
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = _json.loads(result.stdout)
        streams = info.get("streams", [])
        video_stream = next((s for s in streams if s["codec_type"] == "video"), None)
        audio_stream = next((s for s in streams if s["codec_type"] == "audio"), None)

        duration = float(info.get("format", {}).get("duration", 0))
        return {
            "duration": duration,
            "duration_str": _format_duration(duration),
            "video": {
                "codec": video_stream.get("codec_name") if video_stream else None,
                "width": video_stream.get("width") if video_stream else None,
                "height": video_stream.get("height") if video_stream else None,
                "fps": eval(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0,
            } if video_stream else None,
            "audio": {
                "codec": audio_stream.get("codec_name") if audio_stream else None,
                "sample_rate": audio_stream.get("sample_rate") if audio_stream else None,
            } if audio_stream else None,
            "size": info.get("format", {}).get("size", "0"),
            "bit_rate": info.get("format", {}).get("bit_rate", "0"),
        }
    except Exception as e:
        return {"error": str(e)}


def _format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# ============================================================
# 2. 视频截取 / 裁剪
# ============================================================

def trim_video(
    input_path: str,
    output_path: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    duration: Optional[str] = None,
) -> str:
    """截取视频片段
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        start_time: 起始时间 (格式 HH:MM:SS 或 SS)
        end_time: 结束时间
        duration: 持续时间 (与 end_time 二选一)
    """
    cmd = ["ffmpeg", "-i", input_path, "-c", "copy"]
    
    if start_time:
        cmd.extend(["-ss", start_time])
    if end_time:
        cmd.extend(["-to", end_time])
    if duration:
        cmd.extend(["-t", duration])
    
    cmd.append(output_path)
    
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"[✓] 视频截取完成: {output_path}")
    return output_path


# ============================================================
# 3. 语音识别 & 字幕生成
# ============================================================

def generate_subtitles(
    video_path: str,
    output_srt: Optional[str] = None,
    model_size: str = "base",
    language: Optional[str] = None,
) -> str:
    """使用 Whisper 自动生成字幕文件 (SRT 格式)
    
    Args:
        video_path: 视频文件路径
        output_srt: 输出 SRT 文件路径 (默认同目录同名.srt)
        model_size: 模型大小 (tiny/base/small/medium/large)
        language: 语言代码 (zh/en 等)，None 则自动检测
    Returns:
        SRT 文件路径
    """
    import whisper

    if output_srt is None:
        output_srt = str(Path(video_path).with_suffix(".srt"))

    if os.path.exists(output_srt):
        print(f"[!] 字幕文件已存在: {output_srt}，跳过生成")
        return output_srt

    print(f"[*] 加载 Whisper 模型 ({model_size})...")
    model = whisper.load_model(model_size)

    print(f"[*] 开始语音识别: {video_path}")
    transcribe_kwargs = {}
    if language:
        transcribe_kwargs["language"] = language
    
    result = model.transcribe(video_path, **transcribe_kwargs)

    # 写入 SRT 文件
    with open(output_srt, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], 1):
            start = _srt_time(segment["start"])
            end = _srt_time(segment["end"])
            text = segment["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    print(f"[✓] 字幕生成完成: {output_srt}")
    return output_srt


def _srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def burn_subtitles(
    video_path: str,
    output_path: str,
    srt_path: str,
    font_size: int = 24,
    font_color: str = "white",
) -> str:
    """将字幕硬编码嵌入视频
    
    Args:
        video_path: 原视频
        output_path: 输出视频路径
        srt_path: SRT 字幕文件路径
        font_size: 字体大小
        font_color: 字体颜色
    """
    # 创建一个带中文字体的字幕样式
    subtitle_filter = (
        f"subtitles={srt_path}:force_style="
        f"'FontName=Noto Sans CJK SC,FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,Outline=1,Shadow=1'"
    )
    
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", subtitle_filter,
        "-c:a", "aac", "-b:a", "192k",
        "-y", output_path
    ]
    
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"[✓] 字幕嵌入完成: {output_path}")
    return output_path


# ============================================================
# 4. 视频拼接
# ============================================================

def concat_videos(
    input_paths: List[str],
    output_path: str,
) -> str:
    """合并多个视频文件
    
    Args:
        input_paths: 输入视频路径列表
        output_path: 输出视频路径
    """
    # 创建文件列表
    file_list_path = str(Path(output_path).parent / "_concat_list.txt")
    with open(file_list_path, "w", encoding="utf-8") as f:
        for path in input_paths:
            # 需要转义特殊字符
            escaped = path.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")
    
    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", file_list_path,
        "-c", "copy",
        "-y", output_path
    ]
    
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    os.remove(file_list_path)
    print(f"[✓] 视频拼接完成: {output_path}")
    return output_path


def concat_videos_reencode(
    input_paths: List[str],
    output_path: str,
) -> str:
    """合并视频（当编码不一致时采用重新编码方式）"""
    filter_parts = []
    for i, path in enumerate(input_paths):
        filter_parts.append(f"[{i}:v:0][{i}:a:0]")
    
    filter_complex = "".join(f"[{i}:v:0][{i}:a:0]" for i in range(len(input_paths)))
    filter_complex += f"concat=n={len(input_paths)}:v=1:a=1[outv][outa]"
    
    cmd = ["ffmpeg"]
    for path in input_paths:
        cmd.extend(["-i", path])
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-y", output_path
    ])
    
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"[✓] 视频拼接（重编码）完成: {output_path}")
    return output_path


# ============================================================
# 5. 格式转换 / 分辨率调整
# ============================================================

def convert_video(
    input_path: str,
    output_path: str,
    resolution: Optional[str] = None,
    bitrate: Optional[str] = None,
    codec: str = "libx264",
    crf: int = 23,
    preset: str = "medium",
) -> str:
    """视频格式转换与参数调整
    
    Args:
        input_path: 输入
        output_path: 输出 (扩展名决定格式)
        resolution: 分辨率 WxH (如 1920x1080)
        bitrate: 视频码率 (如 5M)
        codec: 视频编码器
        crf: CRF 质量 (0-51, 越低越好)
        preset: 编码预设 ( ultrafast/fast/medium/slow/veryslow)
    """
    cmd = ["ffmpeg", "-i", input_path]
    
    # 视频滤镜
    vf_parts = []
    if resolution:
        vf_parts.append(f"scale={resolution}:flags=lanczos")
    
    if vf_parts:
        cmd.extend(["-vf", ",".join(vf_parts)])
    
    cmd.extend(["-c:v", codec, "-preset", preset, "-crf", str(crf)])
    
    if bitrate:
        cmd.extend(["-b:v", bitrate])
    
    cmd.extend(["-c:a", "aac", "-b:a", "192k", "-y", output_path])
    
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"[✓] 格式转换完成: {output_path}")
    return output_path


# ============================================================
# 6. 添加片头 / 片尾 / 水印
# ============================================================

def add_intro_outro(
    main_video: str,
    output_path: str,
    intro_video: Optional[str] = None,
    outro_video: Optional[str] = None,
) -> str:
    """添加片头片尾
    
    Args:
        main_video: 主视频
        output_path: 输出路径
        intro_video: 片头视频路径
        outro_video: 片尾视频路径
    """
    parts = []
    if intro_video:
        parts.append(intro_video)
    parts.append(main_video)
    if outro_video:
        parts.append(outro_video)
    
    if len(parts) == 1:
        print("[!] 未指定片头或片尾，无需处理")
        return main_video
    
    return concat_videos_reencode(parts, output_path)


def add_watermark(
    video_path: str,
    output_path: str,
    image_path: str,
    position: str = "bottom-right",
    scale_ratio: float = 0.1,
    opacity: float = 1.0,
) -> str:
    """添加图片水印
    
    Args:
        video_path: 输入视频
        output_path: 输出视频
        image_path: 水印图片路径
        position: 位置 (top-left/top-right/bottom-left/bottom-right/center)
        scale_ratio: 水印相对视频宽度的比例
        opacity: 透明度 (0-1)
    """
    position_map = {
        "top-left": "10:10",
        "top-right": "W-w-10:10",
        "bottom-left": "10:H-h-10",
        "bottom-right": "W-w-10:H-h-10",
        "center": "(W-w)/2:(H-h)/2",
    }
    pos = position_map.get(position, "W-w-10:H-h-10")
    
    filter_complex = (
        f"movie={image_path}[wm];"
        f"[in][wm]overlay={pos}:format=auto,format=yuv420p[out]"
    )
    
    if opacity < 1.0:
        filter_complex = (
            f"[0:v]format=rgba[main];"
            f"movie={image_path},format=rgba,colorchannelmixer=aa={opacity}[wm];"
            f"[main][wm]overlay={pos}:format=auto,format=yuv420p[outv]"
        )
        cmd = [
            "ffmpeg", "-i", video_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "0:a",
            "-c:a", "aac",
            "-y", output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-i", video_path, "-i", image_path,
            "-filter_complex", f"[0:v][1:v]overlay={pos}:format=auto",
            "-c:a", "aac",
            "-y", output_path
        ]
    
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"[✓] 水印添加完成: {output_path}")
    return output_path


# ============================================================
# 7. 音频处理
# ============================================================

def extract_audio(
    video_path: str,
    output_path: Optional[str] = None,
    format: str = "mp3",
    bitrate: str = "192k",
) -> str:
    """提取视频中的音频
    
    Args:
        video_path: 输入视频
        output_path: 输出音频路径
        format: 音频格式 (mp3/wav/aac/flac)
        bitrate: 音频码率
    """
    if output_path is None:
        output_path = str(Path(video_path).with_suffix(f".{format}"))
    
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn", "-c:a", _audio_codec(format),
        "-b:a", bitrate,
        "-y", output_path
    ]
    
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"[✓] 音频提取完成: {output_path}")
    return output_path


def _audio_codec(fmt: str) -> str:
    mapping = {"mp3": "libmp3lame", "wav": "pcm_s16le", "aac": "aac", "flac": "flac"}
    return mapping.get(fmt, "libmp3lame")


def replace_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    keep_original_audio: bool = False,
    volume: float = 1.0,
) -> str:
    """替换/混合视频音频
    
    Args:
        video_path: 输入视频
        audio_path: 新音频文件
        output_path: 输出视频
        keep_original_audio: 是否保留原音频并混合
        volume: 新音频音量倍率
    """
    if keep_original_audio:
        # 混合原音和新音频
        cmd = [
            "ffmpeg", "-i", video_path, "-i", audio_path,
            "-filter_complex",
            f"[0:a]volume=0.3[orig];[1:a]volume={volume}[new];"
            f"[orig][new]amix=inputs=2:duration=first[outa]",
            "-map", "0:v", "-map", "[outa]",
            "-c:v", "copy",
            "-y", output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-i", video_path, "-i", audio_path,
            "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            "-y", output_path
        ]
    
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    print(f"[✓] 音频替换完成: {output_path}")
    return output_path


# ============================================================
# 8. 直播切片
# ============================================================

def live_slice(
    input_path: str,
    output_dir: str,
    slice_duration: int = 300,
    output_prefix: str = "clip",
) -> List[str]:
    """将长视频/直播回放切分为多个短片段
    
    Args:
        input_path: 输入长视频
        output_dir: 输出目录
        slice_duration: 每个片段时长（秒），默认5分钟
        output_prefix: 输出文件前缀
    Returns:
        切片文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取视频总时长
    info = get_video_info(input_path)
    total_duration = info.get("duration", 0)
    if total_duration == 0:
        print("[✗] 无法获取视频时长")
        return []
    
    output_files = []
    start = 0
    index = 1
    
    while start < total_duration:
        output_file = os.path.join(output_dir, f"{output_prefix}_{index:04d}.mp4")
        trim_video(input_path, output_file, 
                   start_time=str(start), 
                   duration=str(slice_duration))
        output_files.append(output_file)
        start += slice_duration
        index += 1
    
    print(f"[✓] 直播切片完成，共 {len(output_files)} 个片段")
    return output_files


def live_slice_by_markers(
    input_path: str,
    output_dir: str,
    markers: List[Tuple[str, str]],
    output_prefix: str = "clip",
) -> List[str]:
    """按标记时间点切片（适用于直播高光时刻提取）
    
    Args:
        input_path: 输入视频
        output_dir: 输出目录
        markers: 标记列表 [(start_time, end_time), ...]
        output_prefix: 输出前缀
    Returns:
        切片文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    output_files = []
    
    for i, (start, end) in enumerate(markers, 1):
        output_file = os.path.join(output_dir, f"{output_prefix}_{i:04d}.mp4")
        trim_video(input_path, output_file, start_time=start, end_time=end)
        output_files.append(output_file)
    
    print(f"[✓] 标记切片完成，共 {len(output_files)} 个片段")
    return output_files


# ============================================================
# 9. JSON 工作流模式 - 从配置文件批量执行
# ============================================================

def run_from_json(json_path: str) -> None:
    """从 JSON 配置文件批量执行处理任务
    
    JSON 格式示例:
    {
        "steps": [
            {"action": "trim", "params": {"start": "00:05:00", "end": "00:10:00"}},
            {"action": "subtitle", "params": {"model": "base"}},
            {"action": "burn_subtitle", "params": {"font_size": 28}},
            {"action": "convert", "params": {"resolution": "1920x1080", "bitrate": "5M"}},
            {"action": "watermark", "params": {"image": "logo.png", "position": "top-right"}},
            {"action": "extract_audio", "params": {"format": "mp3"}}
        ],
        "input": "input_video.mp4",
        "output": "output/final.mp4",
        "work_dir": "output"
    }
    """
    with open(json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    input_file = config.get("input", "")
    output_file = config.get("output", "output.mp4")
    work_dir = config.get("work_dir", "output")
    os.makedirs(work_dir, exist_ok=True)
    
    current_input = input_file
    steps = config.get("steps", [])
    
    action_map = {
        "trim": _step_trim,
        "subtitle": _step_subtitle,
        "burn_subtitle": _step_burn_subtitle,
        "concat": _step_concat,
        "convert": _step_convert,
        "intro_outro": _step_intro_outro,
        "watermark": _step_watermark,
        "extract_audio": _step_extract_audio,
        "replace_audio": _step_replace_audio,
        "live_slice": _step_live_slice,
        "info": _step_info,
    }
    
    for i, step in enumerate(steps):
        action = step.get("action", "")
        params = step.get("params", {})
        
        handler = action_map.get(action)
        if handler is None:
            print(f"[!] 步骤 {i+1}: 未知操作 '{action}'，跳过")
            continue
        
        print(f"\n{'='*50}")
        print(f"[*] 步骤 {i+1}/{len(steps)}: {action}")
        print(f"{'='*50}")
        
        result = handler(current_input, output_file, work_dir, params)
        if result and action != "live_slice" and action != "info":
            current_input = result
        elif action == "live_slice":
            print(f"[✓] 切片输出目录: {result}")
    
    if steps:
        final = config.get("output", "")
        print(f"\n{'='*50}")
        print(f"[✓] 所有步骤完成！最终输出: {final}")


def _step_trim(current: str, output: str, work_dir: str, params: Dict) -> str:
    out = os.path.join(work_dir, "_trimmed.mp4")
    return trim_video(current, out, 
                      params.get("start"), params.get("end"), params.get("duration"))


def _step_subtitle(current: str, output: str, work_dir: str, params: Dict) -> str:
    generate_subtitles(current, 
                       model_size=params.get("model", "base"),
                       language=params.get("language"))
    return current


def _step_burn_subtitle(current: str, output: str, work_dir: str, params: Dict) -> str:
    srt_path = str(Path(current).with_suffix(".srt"))
    out = os.path.join(work_dir, "_subtitled.mp4")
    return burn_subtitles(current, out, srt_path,
                          font_size=params.get("font_size", 24),
                          font_color=params.get("font_color", "white"))


def _step_concat(current: str, output: str, work_dir: str, params: Dict) -> str:
    videos = params.get("videos", [current])
    out = output if params.get("is_final") else os.path.join(work_dir, "_concat.mp4")
    return concat_videos(videos, out)


def _step_convert(current: str, output: str, work_dir: str, params: Dict) -> str:
    out = output if params.get("is_final") else os.path.join(work_dir, "_converted.mp4")
    return convert_video(current, out,
                         resolution=params.get("resolution"),
                         bitrate=params.get("bitrate"),
                         crf=params.get("crf", 23))


def _step_intro_outro(current: str, output: str, work_dir: str, params: Dict) -> str:
    out = os.path.join(work_dir, "_intro_outro.mp4")
    return add_intro_outro(current, out,
                           intro_video=params.get("intro"),
                           outro_video=params.get("outro"))


def _step_watermark(current: str, output: str, work_dir: str, params: Dict) -> str:
    out = output if params.get("is_final") else os.path.join(work_dir, "_watermarked.mp4")
    return add_watermark(current, out, params["image"],
                         position=params.get("position", "bottom-right"),
                         scale_ratio=params.get("scale", 0.1),
                         opacity=params.get("opacity", 1.0))


def _step_extract_audio(current: str, output: str, work_dir: str, params: Dict) -> str:
    return extract_audio(current,
                         format=params.get("format", "mp3"),
                         bitrate=params.get("bitrate", "192k"))


def _step_replace_audio(current: str, output: str, work_dir: str, params: Dict) -> str:
    out = os.path.join(work_dir, "_replaced_audio.mp4")
    return replace_audio(current, params["audio"], out,
                         keep_original_audio=params.get("mix", False),
                         volume=params.get("volume", 1.0))


def _step_live_slice(current: str, output: str, work_dir: str, params: Dict) -> str:
    markers = params.get("markers")
    if markers:
        live_slice_by_markers(current, work_dir, markers,
                              output_prefix=params.get("prefix", "clip"))
    else:
        live_slice(current, work_dir,
                   slice_duration=params.get("duration", 300),
                   output_prefix=params.get("prefix", "clip"))
    return work_dir


def _step_info(current: str, output: str, work_dir: str, params: Dict) -> str:
    info = get_video_info(current)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return current


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="视频剪辑自动化处理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 截取片段
  python video_auto_editor.py trim input.mp4 -s 00:05:00 -e 00:10:00 -o clip.mp4

  # 生成字幕
  python video_auto_editor.py subtitle input.mp4 --model base

  # 嵌入字幕
  python video_auto_editor.py burn input.mp4 -s input.srt -o output.mp4

  # 拼接多个视频
  python video_auto_editor.py concat "video1.mp4,video2.mp4" -o merged.mp4

  # 格式转换+缩放
  python video_auto_editor.py convert input.mp4 -o output.mp4 -r 1920x1080

  # 添加水印
  python video_auto_editor.py watermark input.mp4 logo.png -o output.mp4

  # 提取音频
  python video_auto_editor.py audio input.mp4 -f mp3

  # 直播切片（每5分钟一段）
  python video_auto_editor.py slice input.mp4 -d 300 -o ./clips/

  # 查看视频信息
  python video_auto_editor.py info input.mp4

  # JSON 工作流
  python video_auto_editor.py workflow config.json

  # 检查环境
  python video_auto_editor.py check
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # check
    p_check = subparsers.add_parser("check", help="检查环境")

    # info
    p_info = subparsers.add_parser("info", help="查看视频信息")
    p_info.add_argument("input", help="输入视频路径")

    # trim
    p_trim = subparsers.add_parser("trim", help="截取视频片段")
    p_trim.add_argument("input", help="输入视频路径")
    p_trim.add_argument("-o", "--output", required=True, help="输出路径")
    p_trim.add_argument("-s", "--start", help="起始时间 HH:MM:SS 或秒")
    p_trim.add_argument("-e", "--end", help="结束时间")
    p_trim.add_argument("-d", "--duration", help="持续时间")

    # subtitle
    p_sub = subparsers.add_parser("subtitle", help="自动生成字幕 (Whisper)")
    p_sub.add_argument("input", help="输入视频路径")
    p_sub.add_argument("-o", "--output", help="输出SRT路径")
    p_sub.add_argument("--model", default="base", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper 模型大小")
    p_sub.add_argument("--lang", help="语言代码 (zh/en/ja等)")

    # burn
    p_burn = subparsers.add_parser("burn", help="将字幕嵌入视频")
    p_burn.add_argument("input", help="输入视频路径")
    p_burn.add_argument("-s", "--srt", required=True, help="字幕 SRT 路径")
    p_burn.add_argument("-o", "--output", required=True, help="输出路径")
    p_burn.add_argument("--font-size", type=int, default=24, help="字体大小")
    p_burn.add_argument("--font-color", default="white", help="字体颜色")

    # concat
    p_concat = subparsers.add_parser("concat", help="拼接多个视频")
    p_concat.add_argument("input", help="视频列表，用逗号分隔")
    p_concat.add_argument("-o", "--output", required=True, help="输出路径")

    # convert
    p_conv = subparsers.add_parser("convert", help="格式转换/分辨率调整")
    p_conv.add_argument("input", help="输入视频路径")
    p_conv.add_argument("-o", "--output", required=True, help="输出路径")
    p_conv.add_argument("-r", "--resolution", help="分辨率 WxH (如 1920x1080)")
    p_conv.add_argument("-b", "--bitrate", help="视频码率 (如 5M)")
    p_conv.add_argument("--crf", type=int, default=23, help="CRF 质量 (0-51)")

    # watermark
    p_wm = subparsers.add_parser("watermark", help="添加水印")
    p_wm.add_argument("input", help="输入视频路径")
    p_wm.add_argument("image", help="水印图片路径")
    p_wm.add_argument("-o", "--output", required=True, help="输出路径")
    p_wm.add_argument("-p", "--position", default="bottom-right",
                      choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"],
                      help="水印位置")
    p_wm.add_argument("--opacity", type=float, default=1.0, help="透明度")

    # audio
    p_audio = subparsers.add_parser("audio", help="音频处理")
    p_audio.add_argument("input", help="输入视频路径")
    p_audio.add_argument("-o", "--output", help="输出路径")
    p_audio.add_argument("-f", "--format", default="mp3",
                        choices=["mp3", "wav", "aac", "flac"],
                        help="音频格式")
    p_audio.add_argument("--bitrate", default="192k", help="音频码率")

    # replace audio
    p_rap = subparsers.add_parser("replace-audio", help="替换/混合音频")
    p_rap.add_argument("input", help="输入视频路径")
    p_rap.add_argument("audio", help="新音频文件路径")
    p_rap.add_argument("-o", "--output", required=True, help="输出路径")
    p_rap.add_argument("--mix", action="store_true", help="与原音频混合")
    p_rap.add_argument("--volume", type=float, default=1.0, help="新音频音量倍率")

    # slice
    p_slice = subparsers.add_parser("slice", help="直播切片")
    p_slice.add_argument("input", help="输入视频路径")
    p_slice.add_argument("-o", "--output-dir", default="./clips", help="输出目录")
    p_slice.add_argument("-d", "--duration", type=int, default=300, help="每段时长(秒)")

    # workflow
    p_wf = subparsers.add_parser("workflow", help="从 JSON 配置文件执行工作流")
    p_wf.add_argument("json", help="JSON 配置文件路径")

    args = parser.parse_args()

    if args.command is None or args.command == "check":
        check_ffmpeg()
        print(f"[*] Python: {sys.version}")
        # 验证核心模块
        try:
            import whisper
            print("[✓] openai-whisper 可用")
        except ImportError:
            print("[✗] openai-whisper 未安装")
        try:
            import moviepy
            print(f"[✓] moviepy 可用 (v{moviepy.__version__})")
        except ImportError:
            print("[✗] moviepy 未安装")
        return

    if args.command == "info":
        info = get_video_info(args.input)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    if args.command == "trim":
        trim_video(args.input, args.output, args.start, args.end, args.duration)
    elif args.command == "subtitle":
        generate_subtitles(args.input, args.output, args.model, args.lang)
    elif args.command == "burn":
        burn_subtitles(args.input, args.output, args.srt, args.font_size, args.font_color)
    elif args.command == "concat":
        videos = [v.strip() for v in args.input.split(",")]
        concat_videos(videos, args.output)
    elif args.command == "convert":
        convert_video(args.input, args.output, args.resolution, args.bitrate, crf=args.crf)
    elif args.command == "watermark":
        add_watermark(args.input, args.output, args.image, args.position, opacity=args.opacity)
    elif args.command == "audio":
        extract_audio(args.input, args.output, args.format, args.bitrate)
    elif args.command == "replace-audio":
        replace_audio(args.input, args.audio, args.output, args.mix, args.volume)
    elif args.command == "slice":
        live_slice(args.input, args.output_dir, args.duration)
    elif args.command == "workflow":
        run_from_json(args.json)


if __name__ == "__main__":
    main()