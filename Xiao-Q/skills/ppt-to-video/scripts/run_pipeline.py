#!/usr/bin/env python3
"""
PPT转视频流水线：端到端全自动流水线。

按顺序执行 4 个步骤：
1. 从参考音频/视频中提取人声（可选，用于 Qwen3-TTS 声音克隆）
2. 将演讲稿处理为结构化字幕数据
3. 使用 Qwen3-TTS（支持声音克隆）或 edge-tts（预设音色）生成演讲音频
4. 根据时间数据从 PDF 生成幻灯片视频
5. 合并视频、音频和字幕

使用方法：
    # 基础用法（自动选择 TTS 引擎）
    python run_pipeline.py \
        --speech_md <演讲稿.md> \
        --slides_pdf <幻灯片.pdf> \
        --output_dir <输出目录>

    # 使用 Qwen3-TTS + 声音克隆（推荐）
    python run_pipeline.py \
        --speech_md <演讲稿.md> \
        --slides_pdf <幻灯片.pdf> \
        --output_dir <输出目录> \
        --tts_engine qwen3 \
        --reference_voice <参考音频.wav>

    # 使用 edge-tts（预设音色，不克隆）
    python run_pipeline.py \
        --speech_md <演讲稿.md> \
        --slides_pdf <幻灯片.pdf> \
        --output_dir <输出目录> \
        --tts_engine edge \
        --edge_voice "zh-CN-XiaoxiaoNeural"
"""

import argparse
import json
import os
import sys
import time
import subprocess
import fcntl
import atexit


# Get the directory where this script lives
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================
# Process lock: prevent multiple pipeline instances on same output dir
# ============================================================

_lock_fd = None  # Global reference to keep the lock file descriptor alive


def _get_lock_path(output_dir: str) -> str:
    """Return the lock file path for a given output directory."""
    return os.path.join(output_dir, ".pipeline.lock")


def _is_process_alive(pid_str: str) -> bool:
    """Check if a process with the given PID string is still alive."""
    try:
        pid = int(pid_str)
        os.kill(pid, 0)  # signal 0: just check existence
        return True
    except (ValueError, ProcessLookupError):
        return False
    except PermissionError:
        return True  # process exists but we can't signal it


def acquire_pipeline_lock(output_dir: str) -> bool:
    """
    Acquire an exclusive lock on the output directory.

    Uses fcntl.flock() so the lock is automatically released when the
    process exits (even on crash / SIGKILL).  Returns True on success.
    If another pipeline instance is alive and holds the lock, prints an error
    and returns False.  If the previous holder is dead (stale lock), cleans
    up and re-acquires automatically.
    """
    global _lock_fd
    os.makedirs(output_dir, exist_ok=True)
    lock_path = _get_lock_path(output_dir)

    for attempt in range(2):  # at most 2 attempts (normal + after stale-lock cleanup)
        try:
            _lock_fd = open(lock_path, "w")
            fcntl.flock(_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Write our PID for debugging
            _lock_fd.write(str(os.getpid()))
            _lock_fd.flush()
            return True
        except (IOError, OSError):
            # Read the PID from the lock file
            try:
                with open(lock_path, "r") as f:
                    other_pid = f.read().strip()
            except Exception:
                other_pid = "unknown"

            if _is_process_alive(other_pid):
                # The other process is genuinely running
                print(
                    f"[错误] 另一个流水线进程 (PID {other_pid}) 正在使用输出目录: {output_dir}\n"
                    f"       请等待其完成，或手动终止后重试。\n"
                    f"       锁文件: {lock_path}",
                    file=sys.stderr,
                )
                return False
            else:
                # Stale lock — previous process is dead, clean up and retry
                print(
                    f"[流水线] 检测到残留锁文件（PID {other_pid} 已不存在），自动清理后继续。"
                )
                try:
                    if _lock_fd is not None:
                        _lock_fd.close()
                        _lock_fd = None
                    os.remove(lock_path)
                except OSError:
                    pass
                # retry
                continue

    # Should not reach here
    return False


def release_pipeline_lock(output_dir: str):
    """Release the pipeline lock (called automatically at exit)."""
    global _lock_fd
    if _lock_fd is not None:
        try:
            fcntl.flock(_lock_fd, fcntl.LOCK_UN)
            _lock_fd.close()
        except Exception:
            pass
        _lock_fd = None
    lock_path = _get_lock_path(output_dir)
    try:
        os.remove(lock_path)
    except OSError:
        pass


def run_step(step_num: int, script_name: str, args_list: list, 
             description: str) -> int:
    """运行一个流水线步骤并报告耗时。"""
    print(f"\n{'='*70}")
    print(f"  步骤 {step_num}: {description}")
    print(f"{'='*70}\n")

    script_path = os.path.join(SCRIPT_DIR, script_name)
    if not os.path.isfile(script_path):
        print(f"[错误] 脚本未找到: {script_path}", file=sys.stderr)
        return 1

    cmd = [sys.executable, script_path] + args_list
    start_time = time.time()

    result = subprocess.run(cmd)

    elapsed = time.time() - start_time
    status = "成功" if result.returncode == 0 else "失败"
    print(f"\n[步骤 {step_num}] {status}（耗时 {elapsed:.1f}秒）")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="PPT转视频：全自动流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 自动选择 TTS 引擎
  python run_pipeline.py \\
    --speech_md workspace/project/slides-speech.md \\
    --slides_pdf workspace/project/slides.pdf \\
    --output_dir output/presentation

  # Qwen3-TTS + 声音克隆（推荐）
  python run_pipeline.py \\
    --speech_md workspace/project/slides-speech.md \\
    --slides_pdf workspace/project/slides.pdf \\
    --output_dir output/presentation \\
    --tts_engine qwen3 \\
    --reference_voice reference_voice.wav

  # Qwen3-TTS + 预设音色（无参考音频时，默认 Vivian + instruct）
  python run_pipeline.py \\
    --speech_md workspace/project/slides-speech.md \\
    --slides_pdf workspace/project/slides.pdf \\
    --output_dir output/presentation \\
    --tts_engine qwen3

  # Qwen3-TTS + 自定义音色和 instruct
  python run_pipeline.py \\
    --speech_md workspace/project/slides-speech.md \\
    --slides_pdf workspace/project/slides.pdf \\
    --output_dir output/presentation \\
    --tts_engine qwen3 \\
    --speaker "Vivian" \\
    --instruct "用温柔的语气朗读"

  # edge-tts（预设音色，不支持克隆）
  python run_pipeline.py \\
    --speech_md workspace/project/slides-speech.md \\
    --slides_pdf workspace/project/slides.pdf \\
    --output_dir output/presentation \\
    --tts_engine edge \\
    --edge_voice "zh-CN-YunjianNeural"
        """
    )

    parser.add_argument("--speech_md", required=True,
                        help="演讲稿 Markdown 文件")
    parser.add_argument("--slides_pdf", required=True,
                        help="幻灯片 PDF 文件")
    parser.add_argument("--output_dir", required=True,
                        help="所有生成文件的输出目录")
    parser.add_argument("--tts_engine", choices=["auto", "qwen3", "edge"], default="auto",
                        help="TTS 引擎：auto（自动选择）、qwen3（Qwen3-TTS）、edge（edge-tts）")
    parser.add_argument("--speaker", default="Vivian",
                        help="Qwen3-TTS 预设音色（默认: Vivian）")
    parser.add_argument("--instruct", default="",
                        help="Qwen3-TTS CustomVoice 模式的 instruct 指令（默认自动使用推荐值）")
    parser.add_argument("--edge_voice", default="zh-CN-XiaoxiaoNeural",
                        help="edge-tts 语音名称（默认: zh-CN-XiaoxiaoNeural）")
    parser.add_argument("--resolution", default="1920x1080",
                        help="视频分辨率（默认: 1920x1080）")
    parser.add_argument("--fps", type=int, default=30,
                        help="视频帧率（默认: 30）")
    parser.add_argument("--sample_rate", type=int, default=24000,
                        help="音频采样率（默认: 24000）")
    parser.add_argument("--sentence_pause", type=float, default=0.4,
                        help="句子间停顿时长，秒（默认: 0.4）")
    parser.add_argument("--slide_pause", type=float, default=1.0,
                        help="页面间停顿时长，秒（默认: 1.0）")
    parser.add_argument("--subtitle_mode", choices=["burn", "soft", "both"],
                        default="burn", help="字幕模式（默认: burn 烧录）")
    parser.add_argument("--font_name", default="PingFang SC",
                        help="字幕字体名称（默认: PingFang SC）")
    parser.add_argument("--font_size", type=int, default=38,
                        help="字幕字号（默认: 20）")
    parser.add_argument("--skip_steps", nargs="*", type=int, default=[],
                        help="跳过的步骤编号（如 --skip_steps 1 跳过声音提取）")
    parser.add_argument("--voice_source", default="",
                        help="（可选）用于提取人声的视频或音频文件，仅步骤1使用")
    parser.add_argument("--reference_voice", default="",
                        help="（可选）参考音频文件路径，用于 Qwen3-TTS 声音克隆。"
                             "提供参考音频后，Qwen3-TTS 将克隆该音色生成语音。"
                             "不提供则使用预设音色。edge-tts 不支持声音克隆。"
                             "可直接指定已有的 WAV 文件，也可由步骤1提取。")
    parser.add_argument("--dpi", type=int, default=200,
                        help="PDF 渲染 DPI（默认: 200）")
    parser.add_argument("--regenerate", nargs="+", default=[],
                        help="只重新生成指定的句子 TTS 音频，其余复用已有音频。"
                             "格式: slide<页码>_sent<句号> 或 <页码>:<句号>。"
                             "示例: --regenerate slide1_sent000 3:2。"
                             "使用此参数时，默认自动跳过步骤 1、2，只重跑步骤 3~5。")
    # 保留旧参数兼容性（忽略）
    parser.add_argument("--default_speaker", default="", help=argparse.SUPPRESS)

    args = parser.parse_args()

    # 验证必要的输入文件
    for path_arg, name in [
        (args.speech_md, "speech_md（演讲稿）"),
        (args.slides_pdf, "slides_pdf（幻灯片）")
    ]:
        if not os.path.isfile(path_arg):
            if not os.path.isfile(os.path.abspath(path_arg)):
                print(f"[错误] 文件未找到: {path_arg} ({name})", file=sys.stderr)
                sys.exit(1)

    # 设置目录
    os.makedirs(args.output_dir, exist_ok=True)

    # ---- Acquire process lock to prevent concurrent runs ----
    if not acquire_pipeline_lock(args.output_dir):
        sys.exit(1)
    atexit.register(release_pipeline_lock, args.output_dir)
    step1_dir = os.path.join(args.output_dir, "step1_voice")
    step2_output = os.path.join(args.output_dir, "step2_speech_data.json")
    step3_dir = os.path.join(args.output_dir, "step3_tts")
    step4_dir = os.path.join(args.output_dir, "step4_video")
    final_output = os.path.join(args.output_dir, "final_presentation.mp4")

    pipeline_start = time.time()
    engine_desc = {"auto": "自动选择", "qwen3": "Qwen3-TTS", "edge": "edge-tts"}[args.tts_engine]

    # ---- regenerate 模式：自动跳过步骤 1、2 ----
    is_regenerate_mode = bool(args.regenerate)
    if is_regenerate_mode:
        # 自动跳过步骤 1 和 2（演讲稿和声音提取不需要重新执行）
        if 1 not in args.skip_steps:
            args.skip_steps.append(1)
        if 2 not in args.skip_steps:
            args.skip_steps.append(2)
        regen_desc = " ".join(args.regenerate)
        print(f"\n{'#'*70}")
        print(f"  PPT转视频流水线 — 🔄 重新生成模式")
        print(f"  重新生成目标: {regen_desc}")
        print(f"  自动跳过步骤 1、2，重跑步骤 3~5")
        print(f"{'#'*70}")
    else:
        print(f"\n{'#'*70}")
        print(f"  PPT转视频流水线")
        print(f"{'#'*70}")

    print(f"  TTS 引擎: {engine_desc}")
    print(f"  演讲稿: {args.speech_md}")
    print(f"  幻灯片: {args.slides_pdf}")
    print(f"  输出目录: {args.output_dir}")
    print(f"{'#'*70}")

    # ===============================
    # 步骤 1: 提取人声并筛选参考片段（可选）
    # ===============================
    has_voice_source = args.voice_source and os.path.isfile(args.voice_source)
    if has_voice_source and 1 not in args.skip_steps:
        rc = run_step(1, "step1_extract_voice.py", [
            "--input", args.voice_source,
            "--output_dir", step1_dir
        ], "提取人声并筛选最佳参考片段")

        if rc != 0:
            print("[流水线] 步骤 1 失败，但不影响后续步骤。可通过 --reference_voice 手动指定参考音频。")
    else:
        if has_voice_source:
            print(f"[流水线] 跳过步骤 1")
        else:
            print(f"[流水线] 未提供参考声音源，跳过步骤 1")

    # ===============================
    # 步骤 2: 处理演讲稿
    # ===============================
    if 2 not in args.skip_steps:
        rc = run_step(2, "step2_process_speech.py", [
            "--input", args.speech_md,
            "--output", step2_output
        ], "处理演讲稿")

        if rc != 0:
            print("[流水线] 步骤 2 失败，终止。", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"[流水线] 跳过步骤 2，使用: {step2_output}")

    # ===============================
    # 步骤 3: 语音合成（Qwen3-TTS / edge-tts）
    # ===============================
    if 3 not in args.skip_steps:
        step3_args = [
            "--speech_json", step2_output,
            "--output_dir", step3_dir,
            "--tts_engine", args.tts_engine,
            "--speaker", args.speaker,
            "--edge_voice", args.edge_voice,
            "--sample_rate", str(args.sample_rate),
            "--sentence_pause", str(args.sentence_pause),
            "--slide_pause", str(args.slide_pause),
        ]

        # 传递 instruct 指令（CustomVoice 预设音色模式下使用）
        if args.instruct:
            step3_args.extend(["--instruct", args.instruct])

        # 传递参考音频（用于 Qwen3-TTS 声音克隆）
        ref_voice = args.reference_voice
        ref_text = ""
        # 如果步骤1提取了参考声音和文本，且用户未手动指定，则自动使用
        step1_voice = os.path.join(step1_dir, "reference_voice.wav")
        step1_text = os.path.join(step1_dir, "reference_text.txt")
        if not ref_voice and os.path.isfile(step1_voice):
            ref_voice = step1_voice
            print(f"[流水线] 自动使用步骤1筛选的参考声音: {ref_voice}")
            # 同时读取参考文本
            if os.path.isfile(step1_text):
                with open(step1_text, "r", encoding="utf-8") as f:
                    ref_text = f.read().strip()
                print(f"[流水线] 自动使用步骤1转录的参考文本: {ref_text[:50]}...")
        if ref_voice:
            step3_args.extend(["--reference_voice", ref_voice])
        if ref_text:
            step3_args.extend(["--ref_text", ref_text])

        # 透传 --regenerate 参数
        if args.regenerate:
            step3_args.extend(["--regenerate"] + args.regenerate)

        rc = run_step(3, "step3_clone_voice.py", step3_args,
                      "语音合成（Qwen3-TTS 声音克隆 / edge-tts 预设音色）")

        if rc != 0:
            print("[流水线] 步骤 3 失败，终止。", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"[流水线] 跳过步骤 3")

    timing_json = os.path.join(step3_dir, "timing_data.json")
    full_speech_audio = os.path.join(step3_dir, "full_speech.wav")

    # ===============================
    # 步骤 4: 生成幻灯片视频
    # ===============================
    if 4 not in args.skip_steps:
        rc = run_step(4, "step4_generate_video.py", [
            "--pdf", args.slides_pdf,
            "--timing_json", timing_json,
            "--output_dir", step4_dir,
            "--resolution", args.resolution,
            "--fps", str(args.fps),
            "--dpi", str(args.dpi)
        ], "从 PDF 生成幻灯片视频")

        if rc != 0:
            print("[流水线] 步骤 4 失败，终止。", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"[流水线] 跳过步骤 4")

    slides_video = os.path.join(step4_dir, "slides_video.mp4")

    # ===============================
    # 步骤 5: 合并所有内容
    # ===============================
    if 5 not in args.skip_steps:
        rc = run_step(5, "step5_merge_all.py", [
            "--video", slides_video,
            "--audio", full_speech_audio,
            "--timing_json", timing_json,
            "--output", final_output,
            "--subtitle_mode", args.subtitle_mode,
            "--resolution", args.resolution,
            "--font_name", args.font_name,
            "--font_size", str(args.font_size)
        ], "合并视频、音频和字幕")

        if rc != 0:
            print("[流水线] 步骤 5 失败，终止。", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"[流水线] 跳过步骤 5")

    # ===============================
    # 总结
    # ===============================
    total_time = time.time() - pipeline_start
    print(f"\n{'#'*70}")
    print(f"  流水线完成")
    print(f"{'#'*70}")
    print(f"  TTS 引擎: {engine_desc}")
    print(f"  总耗时: {total_time:.1f}秒（{total_time/60:.1f}分钟）")
    print(f"  最终视频: {final_output}")

    if os.path.exists(final_output):
        file_size = os.path.getsize(final_output) / (1024 * 1024)
        print(f"  文件大小: {file_size:.1f} MB")

    print(f"\n  生成的文件:")
    print(f"    演讲数据:  {step2_output}")
    print(f"    完整音频:  {full_speech_audio}")
    print(f"    时间数据:  {timing_json}")
    print(f"    幻灯片视频: {slides_video}")
    print(f"    最终视频:  {final_output}")
    print(f"    字幕(SRT): {os.path.join(os.path.dirname(final_output), 'subtitles.srt')}")
    print(f"    字幕(ASS): {os.path.join(os.path.dirname(final_output), 'subtitles.ass')}")
    print(f"{'#'*70}\n")


if __name__ == "__main__":
    main()
