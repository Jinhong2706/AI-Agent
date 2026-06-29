#!/usr/bin/env python3
"""
第1步：从视频/音频中提取人声，筛选最佳参考片段。

功能说明：
1. 使用 FFmpeg 从视频中提取音频（仅处理前 3 分钟，节省时间）
2. 使用 Demucs 分离人声与背景音乐/噪声
3. 使用 Whisper 将人声转为文字（带时间戳）
4. 自动筛选一句 5~10 秒、语句独立、声音清晰的参考片段
5. 输出：参考音频 WAV + 参考文本，供第3步声音克隆使用

使用方法：
    python step1_extract_voice.py --input <视频或音频路径> --output_dir <输出目录>

输出文件：
    reference_voice.wav  — 最佳参考音频片段（5~10秒）
    reference_text.txt   — 对应的文字内容
    reference_info.json  — 片段详细信息（时间、文字、评分等）

依赖：
    - FFmpeg（系统工具）
    - demucs（pip install demucs）
    - openai-whisper（pip install openai-whisper）
"""

import argparse
import json
import os
import re
import subprocess
import sys
import shutil


# 只处理输入音频的前 N 秒（避免长视频全量处理）
MAX_PROCESS_DURATION = 180  # 3 分钟

# 参考片段时长范围（秒）
REF_MIN_DURATION = 5.0
REF_MAX_DURATION = 10.0

# 理想时长（评分偏好）
REF_IDEAL_DURATION = 7.0


def check_dependencies():
    """检查必要的工具是否可用。"""
    errors = []
    if not shutil.which("ffmpeg"):
        errors.append("FFmpeg 未找到。安装方法: brew install ffmpeg")
    if not shutil.which("ffprobe"):
        errors.append("ffprobe 未找到。安装方法: brew install ffmpeg")
    try:
        import demucs  # noqa: F401
    except ImportError:
        errors.append("demucs 未找到。安装方法: pip install demucs")
    try:
        import whisper  # noqa: F401
    except ImportError:
        errors.append("openai-whisper 未找到。安装方法: pip install openai-whisper")
    if errors:
        for e in errors:
            print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)


def is_video_file(filepath: str) -> bool:
    """检测文件是否为视频（是否包含视频流）。"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-count_packets", "-show_entries", "stream=nb_read_packets",
             "-of", "csv=p=0", filepath],
            capture_output=True, text=True, timeout=30
        )
        return (result.returncode == 0
                and result.stdout.strip() not in ("", "0"))
    except Exception:
        ext = os.path.splitext(filepath)[1].lower()
        return ext in (
            ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"
        )


def get_audio_duration(audio_path: str) -> float:
    """获取音频文件时长（秒）。"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def extract_audio(input_path: str, output_dir: str,
                  max_duration: float = MAX_PROCESS_DURATION) -> str:
    """
    从输入文件提取音频（仅前 max_duration 秒）。

    如果输入是视频，先提取音频轨道；如果是音频，直接转换格式。
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, "extracted_audio.wav")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-t", str(max_duration),   # 只处理前 N 秒
        "-vn",                      # 不要视频
        "-acodec", "pcm_s16le",     # PCM 16位
        "-ar", "24000",             # 24kHz（TTS 标准采样率）
        "-ac", "1",                 # 单声道
        audio_path
    ]

    print(f"[第1步] 提取音频（最多 {max_duration}s）: {input_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[错误] FFmpeg 提取失败:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    duration = get_audio_duration(audio_path)
    print(f"[第1步] 音频已提取: {audio_path}（{duration:.1f}s）")
    return audio_path


def separate_vocals(audio_path: str, output_dir: str) -> str:
    """
    使用 Demucs 分离人声与背景。
    返回分离后的纯净人声文件路径。
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"[第1步] 使用 Demucs 分离人声...")

    cmd = [
        sys.executable, "-m", "demucs",
        "--two-stems", "vocals",
        "-n", "htdemucs",
        "--out", output_dir,
        audio_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("[警告] htdemucs 失败，尝试 mdx_extra...")
        cmd[cmd.index("htdemucs")] = "mdx_extra"
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[错误] Demucs 分离失败:\n{result.stderr}",
                  file=sys.stderr)
            sys.exit(1)

    # 查找人声输出文件（排除 no_vocals.wav）
    vocals_candidates = []
    for root, dirs, files in os.walk(output_dir):
        for f in files:
            if (f.lower().endswith(".wav")
                    and "vocals" in f.lower()
                    and "no_vocals" not in f.lower()):
                vocals_candidates.append(os.path.join(root, f))

    if not vocals_candidates:
        print("[错误] Demucs 未生成人声输出。", file=sys.stderr)
        sys.exit(1)

    vocals_path = max(vocals_candidates, key=os.path.getmtime)
    print(f"[第1步] 人声文件: {vocals_path}")

    # 转换为 TTS 标准格式（24kHz 单声道 16位）
    clean_vocals_path = os.path.join(output_dir, "clean_vocals.wav")
    convert_cmd = [
        "ffmpeg", "-y",
        "-i", vocals_path,
        "-ar", "24000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        clean_vocals_path
    ]
    subprocess.run(convert_cmd, capture_output=True, text=True, check=True)

    print(f"[第1步] 纯净人声: {clean_vocals_path}")
    return clean_vocals_path


def transcribe_with_whisper(audio_path: str) -> list:
    """
    使用 Whisper 转录音频，返回带时间戳的句子列表。

    返回格式：
    [
        {
            "text": "句子文本",
            "start": 开始时间（秒），
            "end": 结束时间（秒），
            "duration": 时长（秒）
        },
        ...
    ]
    """
    import whisper

    print("[第1步] 使用 Whisper 转录人声...")

    model = whisper.load_model("base")
    result = model.transcribe(
        audio_path,
        language="zh",
        word_timestamps=False,
    )

    segments = []
    for seg in result.get("segments", []):
        text = seg["text"].strip()
        start = seg["start"]
        end = seg["end"]
        duration = end - start

        if text and duration > 0:
            segments.append({
                "text": text,
                "start": start,
                "end": end,
                "duration": duration,
            })

    print(f"[第1步] Whisper 转录完成: {len(segments)} 个片段")
    return segments


def score_segment(segment: dict, audio_path: str,
                  sample_rate: int = 24000) -> float:
    """
    为每个候选片段打分，综合评估：
    1. 时长适中（接近 7s 最佳）
    2. 语句完整（以句号/问号/感叹号结尾更佳）
    3. 声音清晰（RMS 能量 + 信噪比）
    4. 文字长度合理

    返回：0~100 的评分
    """
    import numpy as np
    import wave

    score = 0.0
    duration = segment["duration"]
    text = segment["text"]

    # ---- 1. 时长评分（满分 30 分）----
    # 理想时长 7s，越偏离越低分
    dur_diff = abs(duration - REF_IDEAL_DURATION)
    if dur_diff < 1.0:
        score += 30
    elif dur_diff < 2.0:
        score += 25
    elif dur_diff < 3.0:
        score += 15
    else:
        score += 5

    # ---- 2. 语句完整性（满分 20 分）----
    # 以句号/问号/感叹号结尾 → 完整句子
    if re.search(r'[。！？!?]$', text):
        score += 20
    elif re.search(r'[，,；;：:]$', text):
        score += 8    # 逗号结尾 → 不够完整
    else:
        score += 12   # 无标点 → 中等

    # 文字长度合理（20~80字最佳）
    text_len = len(text)
    if 20 <= text_len <= 80:
        score += 10
    elif 10 <= text_len <= 120:
        score += 5

    # ---- 3. 声音质量（满分 30 分）----
    try:
        start_sample = int(segment["start"] * sample_rate)
        end_sample = int(segment["end"] * sample_rate)

        with wave.open(audio_path, "rb") as wf:
            wf.readframes(start_sample)
            n_frames = end_sample - start_sample
            raw = wf.readframes(n_frames)

        audio_data = np.frombuffer(raw, dtype=np.int16).astype(np.float64)

        if len(audio_data) > 0:
            # RMS 能量
            rms = np.sqrt(np.mean(audio_data ** 2))
            # 归一化到 0-1 范围（16bit 最大 32768）
            rms_norm = min(rms / 3000, 1.0)

            # 能量适中（不太低不太高）加分
            if 0.1 < rms_norm < 0.8:
                score += 20
            elif 0.05 < rms_norm <= 0.1:
                score += 10
            else:
                score += 5

            # 静音比例低加分
            frame_size = int(sample_rate * 0.025)
            frames_rms = []
            for i in range(0, len(audio_data) - frame_size, frame_size):
                frame = audio_data[i:i + frame_size]
                frames_rms.append(np.sqrt(np.mean(frame ** 2)))

            if frames_rms:
                silence_ratio = np.mean(
                    np.array(frames_rms) < 100
                )
                if silence_ratio < 0.1:
                    score += 10
                elif silence_ratio < 0.3:
                    score += 5
    except Exception:
        score += 10  # 无法分析时给中间分

    # ---- 4. 位置偏好（满分 10 分）----
    # 稍偏前的片段通常音质更好（说话人刚开始，状态好）
    if segment["start"] < 60:
        score += 10
    elif segment["start"] < 120:
        score += 7
    else:
        score += 3

    return score


def select_best_segment(segments: list,
                        audio_path: str) -> dict:
    """
    从 Whisper 转录结果中筛选最佳参考片段。

    策略：
    1. 先筛选时长在 5~10 秒的片段
    2. 如果不够，尝试合并相邻短句
    3. 对候选片段打分，选择最高分的
    """
    candidates = []

    # ---- 方案 A：直接找 5~10 秒的单句 ----
    for seg in segments:
        if REF_MIN_DURATION <= seg["duration"] <= REF_MAX_DURATION:
            seg["score"] = score_segment(seg, audio_path)
            candidates.append(seg)

    # ---- 方案 B：合并相邻短句到 5~10 秒 ----
    if len(candidates) < 3:
        print("[第1步] 单句候选不足，尝试合并相邻句子...")
        for i in range(len(segments)):
            merged_text = segments[i]["text"]
            merged_start = segments[i]["start"]
            merged_end = segments[i]["end"]

            for j in range(i + 1, min(i + 4, len(segments))):
                # 检查间隔不要太大（< 1 秒）
                gap = segments[j]["start"] - merged_end
                if gap > 1.0:
                    break

                merged_text += segments[j]["text"]
                merged_end = segments[j]["end"]
                merged_duration = merged_end - merged_start

                if REF_MIN_DURATION <= merged_duration <= REF_MAX_DURATION:
                    merged_seg = {
                        "text": merged_text,
                        "start": merged_start,
                        "end": merged_end,
                        "duration": merged_duration,
                        "merged": True,
                    }
                    merged_seg["score"] = score_segment(
                        merged_seg, audio_path
                    )
                    candidates.append(merged_seg)
                    break
                elif merged_duration > REF_MAX_DURATION:
                    break

    if not candidates:
        # ---- 方案 C：放宽条件，选最接近理想时长的 ----
        print("[第1步] 放宽时长限制，选择最接近 7s 的片段...")
        for seg in segments:
            if seg["duration"] >= 3.0:
                seg["score"] = score_segment(seg, audio_path)
                candidates.append(seg)

    if not candidates:
        print("[警告] 未找到任何合适的参考片段", file=sys.stderr)
        return None

    # 按评分降序排列
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 打印 top 3 候选
    print(f"\n[第1步] 候选片段（Top {min(3, len(candidates))}）：")
    for i, c in enumerate(candidates[:3]):
        merged_tag = " [合并]" if c.get("merged") else ""
        print(f"  #{i+1} 评分={c['score']:.0f} "
              f"时长={c['duration']:.1f}s "
              f"时间={c['start']:.1f}-{c['end']:.1f}s"
              f"{merged_tag}")
        print(f"      文本: {c['text'][:60]}...")

    return candidates[0]


def extract_audio_segment(audio_path: str, start: float,
                          end: float, output_path: str):
    """截取音频片段。"""
    duration = end - start
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-ss", str(start),
        "-t", str(duration),
        "-acodec", "pcm_s16le",
        "-ar", "24000",
        "-ac", "1",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[错误] 截取音频片段失败: {result.stderr}",
              file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="提取人声并筛选最佳参考片段"
    )
    parser.add_argument("--input", required=True,
                        help="视频或音频文件路径")
    parser.add_argument("--output_dir", required=True,
                        help="输出目录")
    parser.add_argument("--max_duration", type=float,
                        default=MAX_PROCESS_DURATION,
                        help=f"最大处理时长（秒，默认: {MAX_PROCESS_DURATION}）")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"[错误] 输入文件未找到: {args.input}", file=sys.stderr)
        sys.exit(1)

    check_dependencies()
    os.makedirs(args.output_dir, exist_ok=True)

    # ---- 步骤 1a: 提取音频（仅前 N 分钟）----
    audio_path = extract_audio(
        args.input, args.output_dir, args.max_duration
    )

    # ---- 步骤 1b: 分离人声 ----
    demucs_output_dir = os.path.join(args.output_dir, "demucs_output")
    clean_vocals = separate_vocals(audio_path, demucs_output_dir)

    # ---- 步骤 1c: Whisper 转录 ----
    segments = transcribe_with_whisper(clean_vocals)

    if not segments:
        print("[错误] Whisper 未识别出任何语音内容", file=sys.stderr)
        sys.exit(1)

    # ---- 步骤 1d: 筛选最佳参考片段 ----
    best = select_best_segment(segments, clean_vocals)

    if best is None:
        print("[错误] 无法找到合适的参考片段", file=sys.stderr)
        sys.exit(1)

    # ---- 步骤 1e: 截取参考片段 ----
    ref_voice_path = os.path.join(args.output_dir, "reference_voice.wav")
    extract_audio_segment(
        clean_vocals, best["start"], best["end"], ref_voice_path
    )

    ref_text = best["text"]
    ref_text_path = os.path.join(args.output_dir, "reference_text.txt")
    with open(ref_text_path, "w", encoding="utf-8") as f:
        f.write(ref_text)

    # 保存详细信息
    ref_info = {
        "text": ref_text,
        "start": best["start"],
        "end": best["end"],
        "duration": best["duration"],
        "score": best["score"],
        "merged": best.get("merged", False),
        "total_segments": len(segments),
        "audio_file": ref_voice_path,
        "text_file": ref_text_path,
    }
    ref_info_path = os.path.join(args.output_dir, "reference_info.json")
    with open(ref_info_path, "w", encoding="utf-8") as f:
        json.dump(ref_info, f, ensure_ascii=False, indent=2)

    # ---- 输出摘要 ----
    duration = get_audio_duration(ref_voice_path)
    print(f"\n[第1步完成] 最佳参考片段已提取。")
    print(f"  参考音频: {ref_voice_path}")
    print(f"  参考文本: {ref_text}")
    print(f"  时长: {duration:.2f}秒")
    print(f"  评分: {best['score']:.0f}/100")
    print(f"  时间范围: {best['start']:.1f}s - {best['end']:.1f}s")
    print(f"  详细信息: {ref_info_path}")
    print(f"  格式: 24kHz 单声道 16位 PCM WAV")

    return ref_voice_path, ref_text


if __name__ == "__main__":
    main()
