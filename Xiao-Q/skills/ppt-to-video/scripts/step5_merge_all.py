#!/usr/bin/env python3
"""
第5步：将视频、音频和字幕合并为最终输出。

功能说明：
1. 从时间数据生成 SRT 字幕文件
2. 将幻灯片视频与演讲音频合并
3. 烧录字幕到视频（硬字幕）或作为软字幕附加
4. 输出最终演讲视频

使用方法：
    python step5_merge_all.py \
        --video <幻灯片视频.mp4> \
        --audio <完整音频.wav> \
        --timing_json <时间数据.json> \
        --output <最终输出.mp4> \
        [--subtitle_style <样式>]

依赖：
    - FFmpeg（系统工具）
"""

import argparse
import json
import os
import subprocess
import sys
import shutil


def check_dependencies():
    """Check required tools."""
    if not shutil.which("ffmpeg"):
        print("[ERROR] FFmpeg not found.", file=sys.stderr)
        sys.exit(1)


def ffmpeg_has_filter(filter_name: str) -> bool:
    """Check if FFmpeg supports a given filter."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            parts = line.split()
            # 滤镜名在第二或第三列
            if len(parts) >= 2 and filter_name in parts:
                return True
        return False
    except Exception:
        return False


def seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(timing_data: dict, output_path: str):
    """
    Generate SRT subtitle file from timing data.
    Each sentence becomes a subtitle entry.
    """
    subtitle_index = 1
    srt_lines = []

    for slide in timing_data["slides"]:
        for sentence in slide["sentences"]:
            start_time = seconds_to_srt_time(sentence["start_time"])
            end_time = seconds_to_srt_time(sentence["end_time"])
            text = sentence["text"]

            srt_lines.append(str(subtitle_index))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")  # Empty line between entries

            subtitle_index += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    print(f"[Step 5] Generated SRT subtitles: {output_path}")
    print(f"  Total entries: {subtitle_index - 1}")

    return output_path


def generate_ass(timing_data: dict, output_path: str,
                  font_name: str = "PingFang SC",
                  font_size: int = 20,
                  primary_color: str = "&H00FFFFFF",
                  outline_color: str = "&H00000000",
                  back_color: str = "&H80000000",
                  resolution: str = "1920x1080"):
    """
    Generate ASS subtitle file with rich styling.
    ASS format allows better positioning and styling.
    """
    width, height = resolution.split("x")

    ass_header = f"""[Script Info]
Title: PPT Presentation Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,1,2,1,2,30,30,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    for slide in timing_data["slides"]:
        for sentence in slide["sentences"]:
            start = seconds_to_ass_time(sentence["start_time"])
            end = seconds_to_ass_time(sentence["end_time"])
            text = sentence["text"].replace("\n", "\\N")
            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.write("\n".join(events))
        f.write("\n")

    print(f"[Step 5] Generated ASS subtitles: {output_path}")
    return output_path


def seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS time format: H:MM:SS.cc"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def merge_video_audio(video_path: str, audio_path: str, output_path: str):
    """Merge video and audio tracks."""
    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.abspath(video_path),
        "-i", os.path.abspath(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-shortest",
        os.path.abspath(output_path)
    ]

    print(f"[Step 5] Merging video and audio...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Merge failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"[Step 5] Merged video+audio: {output_path}")
    return output_path


def burn_subtitles(video_path: str, subtitle_path: str, output_path: str,
                    subtitle_format: str = "ass") -> bool:
    """Burn (hardcode) subtitles into the video. Returns True on success."""
    # FFmpeg 滤镜中路径需要转义特殊字符（: \ '）
    escaped_path = os.path.abspath(subtitle_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    if subtitle_format == "ass":
        sub_filter = f"ass={escaped_path}"
    else:
        sub_filter = (
            f"subtitles={escaped_path}:"
            f"force_style='FontName=PingFang SC,FontSize=22,"
            f"PrimaryColour=&HFFFFFF,OutlineColour=&H000000,"
            f"BackColour=&H80000000,Bold=-1,Outline=2,Shadow=1,"
            f"Alignment=2,MarginV=40'"
        )

    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.abspath(video_path),
        "-vf", sub_filter,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "copy",
        os.path.abspath(output_path)
    ]

    print(f"[Step 5] Burning subtitles ({subtitle_format}) into video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[WARNING] Subtitle burn ({subtitle_format}) failed: {result.stderr[:200]}", file=sys.stderr)
        return False

    print(f"[Step 5] Subtitles burned successfully: {output_path}")
    return True


def add_soft_subtitles(video_path: str, subtitle_path: str, output_path: str):
    """Add subtitles as a separate track (soft subtitles)."""
    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.abspath(video_path),
        "-i", os.path.abspath(subtitle_path),
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=chi",
        os.path.abspath(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[WARNING] Soft subtitle failed: {result.stderr[:200]}", file=sys.stderr)
        return None

    print(f"[Step 5] Soft subtitles added: {output_path}")
    return output_path


def merge_video_audio_subtitles(video_path: str, audio_path: str,
                                 srt_path: str, output_path: str):
    """Merge video + audio + soft subtitles in one step."""
    cmd = [
        "ffmpeg", "-y",
        "-i", os.path.abspath(video_path),
        "-i", os.path.abspath(audio_path),
        "-i", os.path.abspath(srt_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=chi",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-map", "2:0",
        "-shortest",
        os.path.abspath(output_path)
    ]

    print(f"[Step 5] Merging video + audio + soft subtitles...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Merge with subtitles failed: {result.stderr[:300]}", file=sys.stderr)
        # 回退：先合并视频+音频，再添加字幕
        print("[Step 5] 回退：分步合并...")
        merged_path = output_path + ".tmp.mp4"
        merge_video_audio(video_path, audio_path, merged_path)
        result = add_soft_subtitles(merged_path, srt_path, output_path)
        if os.path.exists(merged_path):
            os.remove(merged_path)
        if result is None:
            # 最终回退：只合并视频+音频
            print("[Step 5] 字幕添加失败，输出不含字幕的视频")
            merge_video_audio(video_path, audio_path, output_path)
    else:
        print(f"[Step 5] Merged successfully: {output_path}")

    return output_path


def get_video_info(video_path: str) -> dict:
    """Get video file information."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size:stream=width,height,r_frame_rate,codec_name",
        "-of", "json", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return {}


def main():
    parser = argparse.ArgumentParser(description="Merge video, audio, and subtitles")
    parser.add_argument("--video", required=True, help="Slide video from step 4")
    parser.add_argument("--audio", required=True, help="Speech audio from step 3")
    parser.add_argument("--timing_json", required=True, help="Timing data from step 3")
    parser.add_argument("--output", required=True, help="Final output video path")
    parser.add_argument("--subtitle_mode", choices=["burn", "soft", "both"],
                        default="burn", help="Subtitle mode")
    parser.add_argument("--resolution", default="1920x1080", help="Video resolution")
    parser.add_argument("--font_name", default="PingFang SC", help="Subtitle font")
    parser.add_argument("--font_size", type=int, default=38, help="Subtitle font size")
    args = parser.parse_args()

    check_dependencies()

    # Load timing data
    with open(args.timing_json, "r", encoding="utf-8") as f:
        timing_data = json.load(f)

    output_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(output_dir, exist_ok=True)

    # Generate subtitles
    srt_path = os.path.join(output_dir, "subtitles.srt")
    ass_path = os.path.join(output_dir, "subtitles.ass")

    generate_srt(timing_data, srt_path)
    generate_ass(timing_data, ass_path, 
                  font_name=args.font_name, 
                  font_size=args.font_size,
                  resolution=args.resolution)

    # 检测 FFmpeg 字幕滤镜能力
    has_ass = ffmpeg_has_filter("ass")
    has_subtitles = ffmpeg_has_filter("subtitles")
    can_burn = has_ass or has_subtitles

    if not can_burn:
        print("[Step 5] FFmpeg 未编译 libass/libfreetype，硬字幕不可用")
        print("[Step 5] 自动使用软字幕模式（mov_text）")

    # 决定实际字幕模式
    actual_mode = args.subtitle_mode
    if actual_mode == "burn" and not can_burn:
        actual_mode = "soft"
        print("[Step 5] 已回退至软字幕模式")

    if actual_mode in ("burn", "both"):
        # 先合并视频+音频
        merged_path = os.path.join(output_dir, "merged_no_subs.mp4")
        merge_video_audio(args.video, args.audio, merged_path)

        # 烧录字幕
        success = False
        if has_ass:
            success = burn_subtitles(merged_path, ass_path, args.output, subtitle_format="ass")
        if not success and has_subtitles:
            success = burn_subtitles(merged_path, srt_path, args.output, subtitle_format="srt")

        if not success:
            print("[Step 5] 硬字幕烧录失败，回退为软字幕模式")
            actual_mode = "soft"
        else:
            # 清理中间文件
            if os.path.exists(merged_path):
                os.remove(merged_path)

        if actual_mode == "both":
            soft_output = args.output.replace(".mp4", "_softsub.mp4")
            add_soft_subtitles(merged_path, srt_path, soft_output)

    if actual_mode == "soft":
        # 一步到位：视频 + 音频 + 软字幕
        merge_video_audio_subtitles(args.video, args.audio, srt_path, args.output)

    # Print final info
    info = get_video_info(args.output)
    file_size = os.path.getsize(args.output) / (1024 * 1024)

    print(f"\n{'='*60}")
    print(f"[Step 5 DONE] Final video generated successfully!")
    print(f"{'='*60}")
    print(f"  Output: {args.output}")
    print(f"  File size: {file_size:.1f} MB")
    print(f"  Duration: {timing_data['total_duration']:.1f}s")
    print(f"  Slides: {len(timing_data['slides'])}")
    print(f"  Subtitles: {srt_path}")
    print(f"{'='*60}")

    return args.output


if __name__ == "__main__":
    main()
