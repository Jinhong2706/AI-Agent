#!/usr/bin/env python3
"""
第3步：使用 Qwen3-TTS 或 edge-tts 生成演讲音频。

功能说明：
1. 读取第2步生成的结构化演讲数据
2. 使用 Qwen3-TTS（优先）或 edge-tts（备选）进行语音合成
3. 为每页幻灯片生成音频并记录时间元数据
4. 拼接为完整的演讲音频
5. 记录每页幻灯片和每个句子的精确时间信息

TTS 引擎说明：
    - Qwen3-TTS（推荐）：
      · 声音克隆（Base 模型）：提供参考音频即可克隆音色
      · 预设音色（CustomVoice 模型）：9 种内置音色 + instruct 情感/语调控制
      · 语音设计（VoiceDesign 模型）：用自然语言描述"设计"全新音色
      · 方案B策略：声音克隆严格用 Base 模型，预设音色严格用 CustomVoice 模型，不混用
    - edge-tts（备选）：微软在线 TTS，仅使用预设音色，不支持声音克隆

使用方法：
    # 使用 Qwen3-TTS 克隆音色（推荐，需参考音频）
    python step3_clone_voice.py \
        --speech_json <演讲数据.json> \
        --output_dir <输出目录> \
        --tts_engine qwen3 \
        --reference_voice <参考音频.wav>

    # 使用 Qwen3-TTS 预设音色 + instruct 指令控制（推荐，无参考音频时）
    # 默认已使用 Vivian 音色 + 推荐 instruct，无需手动指定
    python step3_clone_voice.py \
        --speech_json <演讲数据.json> \
        --output_dir <输出目录> \
        --tts_engine qwen3

    # 自定义音色和 instruct
    python step3_clone_voice.py \
        --speech_json <演讲数据.json> \
        --output_dir <输出目录> \
        --tts_engine qwen3 \
        --speaker "Vivian" \
        --instruct "用温柔的语气朗读，语速稍慢"

    # 使用 Qwen3-TTS 语音设计模式（需下载 VoiceDesign 模型）
    python step3_clone_voice.py \
        --speech_json <演讲数据.json> \
        --output_dir <输出目录> \
        --tts_engine qwen3 \
        --voice_design "成熟稳重的男性声音，语速适中"

    # 使用 edge-tts（不克隆音色）
    python step3_clone_voice.py \
        --speech_json <演讲数据.json> \
        --output_dir <输出目录> \
        --tts_engine edge \
        --edge_voice "zh-CN-XiaoxiaoNeural"

依赖（至少安装其一）：
    - Qwen3-TTS: pip install -U qwen-tts
    - edge-tts:  pip install edge-tts
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time


# ============================================================
# Qwen3-TTS 预设音色（CustomVoice 模型）
# ============================================================
QWEN3_SPEAKERS = {
    "Vivian": "明亮的年轻女声",
    "Serena": "温暖、温柔的年轻女声",
    "Uncle_Fu": "成熟的男性声音，醇厚音色",
    "Dylan": "年轻的北京男声",
    "Eric": "活泼的成都男声",
    "Ryan": "富有节奏感的英文男声",
    "Aiden": "阳光的美国男声",
    "Ono_Anna": "俏皮的日本女声",
    "Sohee": "温暖的韩国女声",
}

# edge-tts 中文推荐语音
EDGE_VOICES = {
    "zh-CN-XiaoxiaoNeural": "晓晓（女，温暖自然）",
    "zh-CN-XiaoyiNeural": "晓伊（女，亲切活泼）",
    "zh-CN-YunjianNeural": "云健（男，沉稳大气）",
    "zh-CN-YunxiNeural": "云希（男，年轻阳光）",
    "zh-CN-YunyangNeural": "云扬（男，新闻播报）",
}


# ============================================================
# TTS 引擎检测
# ============================================================

def check_qwen3_tts() -> bool:
    """检查 Qwen3-TTS 是否可用。"""
    try:
        from qwen_tts import Qwen3TTSModel  # noqa: F401
        return True
    except ImportError:
        return False


def check_edge_tts() -> bool:
    """检查 edge-tts 是否可用。"""
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


def detect_tts_engine(preferred: str = "auto") -> str:
    """
    检测可用的 TTS 引擎。

    参数：
        preferred: "auto"（自动选择）、"qwen3"（强制 Qwen3）、"edge"（强制 edge-tts）

    返回：
        "qwen3" 或 "edge"

    异常：
        如果没有任何引擎可用，打印错误并退出
    """
    has_qwen3 = check_qwen3_tts()
    has_edge = check_edge_tts()

    if preferred == "qwen3":
        if has_qwen3:
            return "qwen3"
        print("[错误] 指定使用 Qwen3-TTS 但未安装。请运行: pip install -U qwen-tts", file=sys.stderr)
        sys.exit(1)
    elif preferred == "edge":
        if has_edge:
            return "edge"
        print("[错误] 指定使用 edge-tts 但未安装。请运行: pip install edge-tts", file=sys.stderr)
        sys.exit(1)
    else:  # auto
        if has_qwen3:
            return "qwen3"
        if has_edge:
            return "edge"
        print("[错误] 未检测到任何 TTS 引擎！请至少安装其一：", file=sys.stderr)
        print("  方式一（推荐，本地高质量）: pip install -U qwen-tts", file=sys.stderr)
        print("  方式二（在线，需联网）:     pip install edge-tts", file=sys.stderr)
        sys.exit(1)


# ============================================================
# Qwen3-TTS 引擎
# ============================================================

def _get_ref_audio_duration(audio_path: str) -> float:
    """获取参考音频的时长（秒）。"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _trim_leading_noise(audio_data, sr: int, text: str):
    """
    检测并裁剪音频开头的杂音/无关音节。

    Qwen3-TTS（尤其是声音克隆模式）经常在音频开头产生：
    1. 短促的噪声/杂音 burst
    2. 来自参考音频泄漏的无关音节
    3. 模型"预热"产生的含糊音

    策略：
    - 用短时能量分析检测开头区域
    - 找到第一个"有效语音起始点"：连续稳定语音能量的位置
    - 如果起始点前存在孤立的噪声突刺，则裁掉它们
    - 保护性裁剪：最多裁掉 0.8 秒，避免误切有效内容

    参数：
        audio_data: numpy 音频数组
        sr: 采样率
        text: 原始文本（用于判断预期内容长度）

    返回：
        (trimmed_audio, trimmed_ms) - 裁剪后的音频和裁掉的毫秒数
    """
    import numpy as np

    total_samples = len(audio_data)
    total_duration = total_samples / sr

    # 太短的音频不处理
    if total_duration < 0.5:
        return audio_data, 0

    # 分析区间：只检测前 1.2 秒（杂音一般出现在前 0.3-0.8 秒）
    analyze_sec = min(1.2, total_duration * 0.5)
    analyze_samples = int(analyze_sec * sr)
    segment = audio_data[:analyze_samples].astype(np.float64)

    # 计算短时能量（帧级别）
    frame_ms = 10   # 10ms 一帧
    frame_size = int(sr * frame_ms / 1000)
    hop = frame_size  # 无重叠

    frame_energies = []
    for i in range(0, len(segment) - frame_size, hop):
        frame = segment[i:i + frame_size]
        rms = np.sqrt(np.mean(frame ** 2))
        frame_energies.append(rms)

    if len(frame_energies) < 5:
        return audio_data, 0

    frame_energies = np.array(frame_energies)

    # 计算全局参考：用音频中段（更稳定）的能量作为基准
    mid_start = int(total_samples * 0.3)
    mid_end = int(total_samples * 0.7)
    mid_segment = audio_data[mid_start:mid_end].astype(np.float64)
    if len(mid_segment) > sr * 0.2:
        mid_rms = np.sqrt(np.mean(mid_segment ** 2))
    else:
        mid_rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))

    # 动态阈值：有效语音帧的 RMS 应该 >= 基准的 15%
    voice_threshold = mid_rms * 0.15

    # 标记每帧为：静音 / 可能杂音 / 有效语音
    # 静音帧：能量 < silence_threshold
    # 杂音帧：孤立的短时高能量脉冲
    # 有效语音帧：持续稳定的语音能量

    # 找到第一个"稳定语音段"的起始帧
    # 定义"稳定"：连续 N 帧中至少 70% 超过 voice_threshold
    min_stable_frames = 5  # 至少 50ms 连续语音
    stable_start_frame = None

    for i in range(len(frame_energies) - min_stable_frames):
        window = frame_energies[i:i + min_stable_frames]
        voice_ratio = np.mean(window >= voice_threshold)
        if voice_ratio >= 0.7:
            stable_start_frame = i
            break

    if stable_start_frame is None or stable_start_frame == 0:
        # 没找到明确的语音起始，或者语音直接从头开始
        return audio_data, 0

    # 检查稳定语音段之前是否有"杂音突刺"
    pre_frames = frame_energies[:stable_start_frame]

    # 统计前导区域中高于 voice_threshold 的帧（可能是杂音脉冲）
    noise_frames = np.sum(pre_frames >= voice_threshold)

    # 如果前导区域全是静音，不需要裁剪（正常的前置静音）
    if noise_frames == 0:
        # 但如果前导静音过长（> 200ms），也可以裁一下
        silent_ms = stable_start_frame * frame_ms
        if silent_ms > 200:
            # 保留 50ms 的前置静音
            trim_frames = max(0, stable_start_frame - 5)
            trim_samples = trim_frames * hop
            trimmed = audio_data[trim_samples:]
            return trimmed, trim_frames * frame_ms
        return audio_data, 0

    # 前导区域有能量脉冲 → 很可能是杂音
    # 从稳定语音起始帧往前回退一点（保留 30ms 过渡）
    safe_margin_frames = 3  # 30ms
    cut_frame = max(0, stable_start_frame - safe_margin_frames)
    cut_sample = cut_frame * hop

    # 安全限制：最多裁剪 0.8 秒
    max_cut_samples = int(0.8 * sr)
    if cut_sample > max_cut_samples:
        cut_sample = max_cut_samples

    if cut_sample <= 0:
        return audio_data, 0

    trimmed = audio_data[cut_sample:]
    trimmed_ms = int(cut_sample / sr * 1000)

    return trimmed, trimmed_ms


def _trim_ref_audio(audio_path: str, max_duration: float) -> str:
    """截取参考音频的前 N 秒，返回临时文件路径。"""
    trimmed_path = os.path.join(
        os.path.dirname(audio_path),
        f"_ref_trimmed_{max_duration:.0f}s.wav"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-t", str(max_duration),
        "-acodec", "pcm_s16le",
        "-ar", "24000",
        "-ac", "1",
        trimmed_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and os.path.isfile(trimmed_path):
        return trimmed_path
    return audio_path  # 截取失败则返回原文件


def _transcribe_ref_audio(audio_path: str) -> str:
    """使用 Whisper 自动转录参考音频文字（用于声音克隆 ICL 模式）。"""
    try:
        import whisper
        print("[Whisper] 正在转录参考音频...")
        model = whisper.load_model("base")  # 使用 base 模型，够快够准
        result = model.transcribe(audio_path, language="zh")
        text = result.get("text", "").strip()
        if text:
            print(f"[Whisper] 转录结果: {text[:100]}{'...' if len(text) > 100 else ''}")
        else:
            print("[Whisper] 转录结果为空")
        return text
    except ImportError:
        print("[Whisper] whisper 未安装，无法自动转录")
        return ""
    except Exception as e:
        print(f"[Whisper] 转录失败: {e}")
        return ""


class Qwen3TTSEngine:
    """Qwen3-TTS 语音合成引擎。

    支持三种模式（对应三种模型）：

    1. 声音克隆模式（Base 模型）：
       提供参考音频，使用 generate_voice_clone() 克隆音色。
       - ICL 模式（需要 ref_text + 短参考音频 ≤15s，效果最好）
       - x_vector_only 模式（长参考音频或无 ref_text）：仅使用声纹嵌入
       - Base 模型仅支持声音克隆，不支持预设音色和指令控制。

    2. 预设音色模式（CustomVoice 模型）：
       使用 generate_custom_voice() + 9 种内置音色。
       支持 instruct 参数进行情感/语调控制（如 "用标准的普通话朗读"）。
       推荐：无参考音频时的首选方案。

    3. 语音设计模式（VoiceDesign 模型）：
       使用 generate_voice_design() + 自然语言描述"设计"全新音色。
       无需预设 speaker，用文字描述即可控制音色特征。
       注意：VoiceDesign 模型是独立模型，Base/CustomVoice 不支持此接口。

    注意事项：
    - ICL 模式要求参考音频较短（≤15s），过长会导致内容泄漏和音色不稳定
    - 对于长参考音频，自动使用 x_vector_only 模式（仅声纹嵌入）
    - CustomVoice 的 instruct 参数可有效控制朗读风格（普通话标准度、语调等）
    """

    # ICL 模式参考音频最大时长（秒）。超过此值自动使用 x_vector_only 模式
    ICL_MAX_DURATION = 15.0

    # 声音克隆模式：优先 1.7B Base 模型（效果更好）
    # 接口：generate_voice_clone()
    BASE_MODEL_CANDIDATES = [
        "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    ]

    # 预设音色模式：优先 1.7B CustomVoice 模型（效果更好）
    # 接口：generate_custom_voice(speaker, instruct)
    CUSTOM_MODEL_CANDIDATES = [
        "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
    ]

    # 语音设计模式：VoiceDesign 模型（用自然语言描述控制音色）
    # 接口：generate_voice_design(instruct)
    VOICE_DESIGN_MODEL_CANDIDATES = [
        "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    ]

    # CustomVoice 模式下的推荐默认 instruct 指令
    # 适合 PPT 讲解 / 技术分享场景：专业播音腔，语气平稳统一
    DEFAULT_INSTRUCT = "用标准的新闻播音腔朗读，字正腔圆，语速稍快，节奏稳定，语调平稳，适合专业技术讲解"

    # ---- 采样参数（控制语气一致性）----
    # 关键原理：Qwen3-TTS 是生成式模型，使用随机采样生成 codec tokens。
    # 默认的高 temperature 会导致每句话的韵律/语气随机变化很大。
    # 降低 temperature 可以大幅减少随机性，使语气在句间保持一致。
    #
    # temperature=0.3: 低随机性，语气稳定一致（适合 PPT 讲解等需要统一风格的场景）
    # temperature=0.7: 中等随机性（适合需要一定表现力但仍相对稳定的场景）
    # temperature=1.0: 默认值，高随机性（每句语气差异大）
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_TOP_K = 30
    DEFAULT_TOP_P = 0.8
    # 固定随机种子：确保同样的文本 + 参数 → 每次生成结果一致
    DEFAULT_SEED = 42

    def __init__(self, speaker: str = "Vivian", reference_voice: str = "",
                 ref_text: str = "", voice_design: str = "",
                 instruct: str = ""):
        """
        初始化 Qwen3-TTS 引擎。

        参数：
            speaker: 预设音色名称（CustomVoice 模式使用，默认 Vivian）
            reference_voice: 参考音频路径（Base 模型声音克隆模式）
            ref_text: 参考音频中说话内容的文字（可选，
                      为空时自动用 Whisper 转录，
                      转录失败则降级为 x_vector_only 模式）
            voice_design: 语音设计指令，使用 VoiceDesign 模型的
                          generate_voice_design() 接口。
                          传入自然语言描述（如 "成熟稳重的男性声音"）
                          来"设计"全新音色，无需预设 speaker。
            instruct: CustomVoice 模式的情感/语调控制指令（可选）。
                      如 "用标准的普通话朗读，语调自然流畅"。
                      仅在 CustomVoice 模式下生效。
        """
        import torch
        from qwen_tts import Qwen3TTSModel

        self.speaker = speaker
        self.reference_voice = reference_voice
        self.ref_text = ref_text
        self.voice_design = voice_design
        self.instruct = instruct
        self.model = None
        self.model_name = ""
        self.is_clone_mode = False
        self.is_voice_design_mode = bool(voice_design)  # 是否使用 VoiceDesign 模型
        self.x_vector_only = False  # 是否使用仅声纹嵌入模式
        self.sample_rate = 24000  # 默认值，加载后会更新
        self._voice_clone_prompt = None  # 缓存声音克隆 prompt

        # ---- 定期重载机制 ----
        # 连续生成大量句子后，模型状态（MPS 浮点精度累积、Python 内存碎片）
        # 会逐渐漂移，导致后期音频质量下降（语速变慢、音色不稳定）。
        # 每生成 N 句主动重载一次模型，彻底清理状态，保证全程质量一致。
        self._periodic_reload_interval = 30  # 每 30 句重载一次（可通过 set_periodic_reload 调整）
        self._sentences_since_reload = 0     # 自上次重载以来已生成的句子数

        # 确定设备和精度
        if torch.cuda.is_available():
            device_map = "cuda:0"
            dtype = torch.bfloat16
            attn_impl = "flash_attention_2"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device_map = "mps"
            # PyTorch 2.8+ 的 MPS 后端已支持 bfloat16（matmul/softmax/LayerNorm/SDPA 均通过测试）
            # bfloat16 相比 float32：内存减半，推理更快
            dtype = torch.bfloat16
            # SDPA (Scaled Dot Product Attention) 在 MPS 上已可用，比 eager 更快
            attn_impl = "sdpa"
        else:
            device_map = "cpu"
            dtype = torch.float32
            attn_impl = "eager"

        print(f"[Qwen3-TTS] 计算设备: {device_map}, 精度: {dtype}")

        # 判断模式：有参考音频 → 声音克隆(Base)，voice_design → VoiceDesign 模型，否则 → 预设音色(CustomVoice)
        has_ref = reference_voice and os.path.isfile(reference_voice)
        if has_ref:
            print(f"[Qwen3-TTS] 检测到参考音频: {reference_voice}")
            print("[Qwen3-TTS] 将使用声音克隆模式（Base 模型）")
            model_candidates = self.BASE_MODEL_CANDIDATES
        elif self.is_voice_design_mode:
            print(f"[Qwen3-TTS] 将使用语音设计模式（VoiceDesign 模型）")
            print(f"[Qwen3-TTS] 设计指令: {voice_design}")
            model_candidates = self.VOICE_DESIGN_MODEL_CANDIDATES
        else:
            if reference_voice:
                print(f"[警告] 参考音频不存在: {reference_voice}，降级为预设音色模式")
            print("[Qwen3-TTS] 将使用预设音色模式（CustomVoice 模型）")
            # 未显式指定 instruct 时，自动使用推荐默认值
            # instruct 可有效控制普通话标准度和朗读稳定性，减少口音漂移
            if not self.instruct:
                self.instruct = self.DEFAULT_INSTRUCT
                print(f"[Qwen3-TTS] 使用默认 instruct: {self.instruct}")
            else:
                print(f"[Qwen3-TTS] instruct 指令: {self.instruct}")
            model_candidates = self.CUSTOM_MODEL_CANDIDATES

        # 依次尝试加载模型
        for model_id in model_candidates:
            try:
                print(f"[Qwen3-TTS] 尝试加载模型: {model_id}")
                self.model = Qwen3TTSModel.from_pretrained(
                    model_id,
                    device_map=device_map,
                    dtype=dtype,
                    attn_implementation=attn_impl,
                )
                self.model_name = model_id
                print(f"[Qwen3-TTS] 模型加载成功: {model_id}")
                break
            except Exception as e:
                print(f"[Qwen3-TTS] 加载失败: {model_id} — {e}")
                continue

        if self.model is None:
            raise RuntimeError("无法加载任何 Qwen3-TTS 模型")

        is_base_model = "Base" in self.model_name
        is_custom_model = "CustomVoice" in self.model_name

        # 设置工作模式
        if has_ref and is_base_model:
            # 声音克隆模式
            self.is_clone_mode = True

            # 检测参考音频时长，决定使用 ICL 还是 x_vector_only
            ref_duration = _get_ref_audio_duration(reference_voice)
            print(f"[Qwen3-TTS] 参考音频时长: {ref_duration:.1f}秒")

            # 实际用于声音克隆的参考音频路径（可能是截取后的）
            effective_ref_audio = reference_voice

            if ref_duration > self.ICL_MAX_DURATION:
                # 长参考音频 → 强制使用 x_vector_only 模式
                # ICL 模式对长音频会导致：内容泄漏、音色不稳定
                self.x_vector_only = True
                print(f"[Qwen3-TTS] 参考音频 ({ref_duration:.0f}s) 超过 ICL 上限 "
                      f"({self.ICL_MAX_DURATION:.0f}s)")
                print("[Qwen3-TTS] 自动切换为 x_vector_only 模式"
                      "（仅声纹嵌入，避免内容泄漏）")
                # 截取前 N 秒用于声纹提取（更精准）
                print(f"[Qwen3-TTS] 截取前 {self.ICL_MAX_DURATION:.0f}s "
                      "用于声纹特征提取...")
                effective_ref_audio = _trim_ref_audio(
                    reference_voice, self.ICL_MAX_DURATION
                )
                if effective_ref_audio != reference_voice:
                    print(f"[Qwen3-TTS] 截取完成: {effective_ref_audio}")
            else:
                # 短参考音频 → 尝试 ICL 模式（需要 ref_text）
                if not self.ref_text:
                    self.ref_text = _transcribe_ref_audio(reference_voice)

                if self.ref_text:
                    self.x_vector_only = False
                    print(f"[Qwen3-TTS] 模式: 声音克隆 ICL"
                          f"（参考: {reference_voice}）")
                    print(f"[Qwen3-TTS] 参考文本: "
                          f"{self.ref_text[:80]}...")
                else:
                    self.x_vector_only = True
                    print(f"[Qwen3-TTS] 模式: 声音克隆 x_vector"
                          f"（参考: {reference_voice}）")
                    print("[Qwen3-TTS] 注意: 无参考文本，仅使用声纹嵌入")

            # 预先创建 voice_clone_prompt 以加速后续合成
            try:
                print("[Qwen3-TTS] 正在分析参考音频特征...")
                self._voice_clone_prompt = self.model.create_voice_clone_prompt(
                    ref_audio=effective_ref_audio,
                    ref_text=self.ref_text if not self.x_vector_only else None,
                    x_vector_only_mode=self.x_vector_only,
                )
                print("[Qwen3-TTS] 参考音频特征提取成功")
            except Exception as e:
                print(f"[警告] 参考音频特征提取失败: {e}")
                if not self.x_vector_only:
                    # ICL 失败 → 降级到 x_vector_only
                    print("[Qwen3-TTS] 降级为 x_vector_only 模式重试...")
                    self.x_vector_only = True
                    try:
                        self._voice_clone_prompt = (
                            self.model.create_voice_clone_prompt(
                                ref_audio=effective_ref_audio,
                                x_vector_only_mode=True,
                            )
                        )
                        print("[Qwen3-TTS] x_vector_only 特征提取成功")
                    except Exception as e2:
                        print(f"[警告] x_vector_only 也失败: {e2}")
                        print("[Qwen3-TTS] 将在合成时直接传入参考音频")
                else:
                    print("[Qwen3-TTS] 将在合成时直接传入参考音频")
        elif self.is_voice_design_mode and "VoiceDesign" in self.model_name:
            # voice_design 模式：使用 VoiceDesign 模型 + 语音设计指令
            self.is_clone_mode = False
            print("[Qwen3-TTS] 模式: 语音设计 voice_design（VoiceDesign 模型）")
            print(f"[Qwen3-TTS] 设计指令: {self.voice_design}")
        elif is_custom_model:
            # 预设音色模式（CustomVoice 模型）
            self.is_clone_mode = False
            speakers = self.model.get_supported_speakers()
            if speakers:
                print(f"[Qwen3-TTS] 可用预设音色: {speakers}")
                # 先尝试原始名称匹配，再尝试小写匹配
                if self.speaker not in speakers:
                    lower_speaker = self.speaker.lower()
                    matched = [s for s in speakers if s.lower() == lower_speaker]
                    if matched:
                        print(f"[Qwen3-TTS] 音色名称大小写修正: "
                              f"'{self.speaker}' → '{matched[0]}'")
                        self.speaker = matched[0]
                    else:
                        print(f"[警告] 音色 '{self.speaker}' 不可用，使用 '{speakers[0]}'")
                        self.speaker = speakers[0]
            if self.instruct:
                print(f"[Qwen3-TTS] 模式: 预设音色（{self.speaker}）+ instruct 指令")
                print(f"[Qwen3-TTS] instruct: {self.instruct}")
            else:
                print(f"[Qwen3-TTS] 模式: 预设音色（{self.speaker}）")
        else:
            # 降级情况：voice_design 指定了但 VoiceDesign 模型加载失败，
            # 或 Base 模型无参考音频 → 降级为 CustomVoice 预设音色
            self.is_clone_mode = False
            self.is_voice_design_mode = False
            if is_base_model:
                # Base 模型只能做声音克隆，无法做预设音色或语音设计
                print("[警告] Base 模型无参考音频，无法进行声音克隆。")
                print("[警告] Base 模型不支持 generate_custom_voice 或 generate_voice_design。")
                print("[警告] 请提供参考音频，或改用 CustomVoice/VoiceDesign 模型。")
            else:
                print(f"[Qwen3-TTS] 模式: 降级为预设音色（{self.speaker}）")

    # 每个中文字符的预期最大朗读时长（秒）
    MAX_SECONDS_PER_CHAR = 0.45
    # 最大重试次数（遇到杂音时重新生成）
    MAX_RETRIES = 3

    # ---- 自参考 (self-reference) 机制 ----
    # 核心思路：第一句用 CustomVoice/VoiceDesign 正常生成，确立语气"基调"。
    # 然后切换到 Base 模型，用第一句的输出音频作为参考音频进行声音克隆。
    # 后续所有句子都基于这个"基调参考"生成，确保全片语气一致。
    #
    # 流程：
    # 1. 第一句 → CustomVoice generate_custom_voice()
    # 2. 保存第一句音频 → 释放 CustomVoice 模型 → 加载 Base 模型
    # 3. 用第一句音频创建 voice_clone_prompt
    # 4. 后续句子 → Base generate_voice_clone(voice_clone_prompt)

    def enable_self_reference(self):
        """启用自参考模式（第一句做参考，后续克隆）。"""
        self._self_ref_enabled = True
        self._self_ref_ready = False  # 是否已完成参考音频提取
        self._self_ref_first_audio = None  # 第一句的音频数据
        self._self_ref_first_sr = None  # 第一句的采样率
        self._self_ref_first_text = None  # 第一句的文本（用于 ICL）
        print("[自参考] 已启用：第一句将作为后续所有句子的语气参考")

    def _switch_to_clone_mode(self):
        """
        释放当前模型，加载 Base 模型，用第一句音频创建 voice_clone_prompt。
        """
        import torch
        from qwen_tts import Qwen3TTSModel

        if self._self_ref_first_audio is None:
            print("[自参考] 警告：无第一句音频，无法切换到克隆模式")
            return False

        original_model_name = self.model_name
        print(f"[自参考] 释放模型 {original_model_name}...")

        # 释放当前模型
        del self.model
        self.model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        import gc
        gc.collect()

        # 确定设备和精度（与 __init__ 一致）
        if torch.cuda.is_available():
            device_map = "cuda:0"
            dtype = torch.bfloat16
            attn_impl = "flash_attention_2"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device_map = "mps"
            dtype = torch.bfloat16
            attn_impl = "sdpa"
        else:
            device_map = "cpu"
            dtype = torch.float32
            attn_impl = "eager"

        # 加载 Base 模型
        for model_id in self.BASE_MODEL_CANDIDATES:
            try:
                print(f"[自参考] 加载 Base 模型: {model_id}")
                self.model = Qwen3TTSModel.from_pretrained(
                    model_id,
                    device_map=device_map,
                    dtype=dtype,
                    attn_implementation=attn_impl,
                )
                self.model_name = model_id
                print(f"[自参考] Base 模型加载成功: {model_id}")
                break
            except Exception as e:
                print(f"[自参考] 加载失败: {model_id} — {e}")
                continue

        if self.model is None:
            print("[自参考] 无法加载 Base 模型，恢复原始模式")
            return False

        # 用第一句音频创建 voice_clone_prompt（ICL 模式，效果最好）
        try:
            audio_tuple = (self._self_ref_first_audio, self._self_ref_first_sr)
            ref_text = self._self_ref_first_text

            print(f"[自参考] 用第一句音频创建声音克隆参考 "
                  f"(时长: {len(self._self_ref_first_audio) / self._self_ref_first_sr:.2f}s, "
                  f"文本: {ref_text[:30] if ref_text else '无'}...)")

            self._voice_clone_prompt = self.model.create_voice_clone_prompt(
                ref_audio=audio_tuple,
                ref_text=ref_text,
                x_vector_only_mode=False,  # 使用 ICL 模式（有文本参考，效果最好）
            )
            self.is_clone_mode = True
            self.x_vector_only = False
            self._self_ref_ready = True
            print("[自参考] 声音克隆参考创建成功！后续句子将使用克隆模式")
            return True
        except Exception as e:
            print(f"[自参考] ICL 模式创建失败: {e}")
            # 降级到 x_vector_only 模式
            try:
                print("[自参考] 降级为 x_vector_only 模式...")
                self._voice_clone_prompt = self.model.create_voice_clone_prompt(
                    ref_audio=audio_tuple,
                    x_vector_only_mode=True,
                )
                self.is_clone_mode = True
                self.x_vector_only = True
                self._self_ref_ready = True
                print("[自参考] x_vector_only 参考创建成功")
                return True
            except Exception as e2:
                print(f"[自参考] x_vector_only 也失败: {e2}，继续使用原始模式")
                return False

    # Qwen3-TTS 12Hz 模型每秒音频 = 12 个 codec tokens
    CODEC_TOKENS_PER_SECOND = 12
    # 当生成的 token 数超过上限的此比例时，判定为 EOS 失败（"跑飞"了）
    RUNAWAY_THRESHOLD_RATIO = 0.9
    # 当音频时长超过「合理预期」的此倍数时，判定为"即将跑飞"，预防性重载
    # 合理预期 = 字数 × MAX_SECONDS_PER_CHAR（没有安全系数）
    PREEMPTIVE_RELOAD_RATIO = 1.5

    def _calc_max_new_tokens(self, text: str) -> int:
        """
        根据文本长度计算合理的 max_new_tokens 上限。

        防止模型推理不收敛时无限生成（模型默认 8192 tokens = 682秒音频，
        在 MPS 上需要 30+ 分钟才能生成完毕，导致进程看似"卡死"）。

        算法：
        - 按每个中文字 MAX_SECONDS_PER_CHAR 秒 + 安全余量计算最大时长
        - 转换为 codec tokens 数量
        - 最小 120 tokens（约 10 秒），确保短句也有足够空间
        - 最大 2400 tokens（约 200 秒），防止极端情况
        """
        import re
        # 有效文字数（排除标点和空格）
        content_chars = len(re.sub(
            r'[，。！？、；：\u201c\u201d\u2018\u2019（）…\s\.\,\!\?\;\:\'\"\-]',
            '', text
        ))
        # 预期最大朗读时长（秒）= 字数 × 每字最大时长 × 安全系数
        max_duration_sec = max(5.0, content_chars * self.MAX_SECONDS_PER_CHAR * 2.0)
        # 转换为 codec tokens
        max_tokens = int(max_duration_sec * self.CODEC_TOKENS_PER_SECOND)
        # 限制范围：[120, 2400]
        max_tokens = max(120, min(2400, max_tokens))
        return max_tokens

    def _is_runaway_generation(self, audio_data, sr: int, text: str) -> bool:
        """
        检测本次生成是否"跑飞"了（模型 EOS 检测失败，一路生成到 max_new_tokens 上限）。

        判定标准：生成的音频时长 ≥ max_new_tokens 对应时长的 90%。
        正常生成的音频远远不会触及 max_new_tokens 上限（因为有 2x 安全系数）。

        返回：True 表示跑飞了，需要重载模型重试
        """
        max_tokens = self._calc_max_new_tokens(text)
        max_duration = max_tokens / self.CODEC_TOKENS_PER_SECOND
        actual_duration = len(audio_data) / sr
        threshold = max_duration * self.RUNAWAY_THRESHOLD_RATIO
        return actual_duration >= threshold

    def _needs_preemptive_reload(self, audio_data, sr: int,
                                 text: str) -> bool:
        """
        检测本次生成虽然成功了，但音频偏长，模型状态有"漂移"趋势。

        判定标准：音频时长 > 合理预期时长 × PREEMPTIVE_RELOAD_RATIO。
        合理预期 = 字数 × MAX_SECONDS_PER_CHAR（无安全系数）。

        触发此条件时，虽然当前音频质量可能是 OK 的（通过了质量检测），
        但说明模型内部的 KV cache 可能已经开始膨胀/漂移，
        预防性地重载可以避免下一句真的跑飞。

        返回：True 表示建议在本句完成后重载模型
        """
        import re
        content_chars = len(re.sub(
            r'[，。！？、；：\u201c\u201d\u2018\u2019（）…\s\.\,\!\?\;\:\'\"\-]',
            '', text
        ))
        expected_duration = max(2.0, content_chars * self.MAX_SECONDS_PER_CHAR)
        actual_duration = len(audio_data) / sr
        threshold = expected_duration * self.PREEMPTIVE_RELOAD_RATIO
        return actual_duration > threshold

    def _reload_model(self):
        """
        释放当前模型并重新加载，清理膨胀的 KV cache 内存。

        调用场景：
        1. 预防性重载：本句音频偏长（通过了质量检测但超过合理预期 1.5x），
           说明模型状态在漂移，主动重载防止下一句跑飞。
        2. 跑飞后兜底：本句已确认跑飞（音频触及 token 上限 90%），
           丢弃结果后重载，用干净状态重试。

        耗费加载时间（~10-20s）但能释放 GB 级膨胀内存。
        """
        import gc
        import torch
        from qwen_tts import Qwen3TTSModel

        model_name = self.model_name
        print(f"    [重载] 释放模型 {model_name}，清理 KV cache 内存...")

        # 保存需要恢复的状态
        saved_voice_clone_prompt = self._voice_clone_prompt

        # 释放模型和 GPU 缓存
        del self.model
        self.model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            # MPS 没有 explicit empty_cache，但 gc + del 可以触发释放
            pass
        gc.collect()

        # 确定设备和精度（与 __init__ 一致）
        if torch.cuda.is_available():
            device_map = "cuda:0"
            dtype = torch.bfloat16
            attn_impl = "flash_attention_2"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device_map = "mps"
            dtype = torch.bfloat16
            attn_impl = "sdpa"
        else:
            device_map = "cpu"
            dtype = torch.float32
            attn_impl = "eager"

        # 重新加载模型
        print(f"    [重载] 重新加载模型 {model_name}...")
        reload_start = time.time()
        self.model = Qwen3TTSModel.from_pretrained(
            model_name,
            device_map=device_map,
            dtype=dtype,
            attn_implementation=attn_impl,
        )
        reload_time = time.time() - reload_start
        print(f"    [重载] 模型加载完成（耗时 {reload_time:.1f}s）")

        # 恢复 voice_clone_prompt（已在 GPU/MPS 上的 tensor 需要重建）
        if saved_voice_clone_prompt is not None:
            # voice_clone_prompt 引用了旧模型的 tensor，
            # 但 create_voice_clone_prompt 的结果是纯数据（不绑定模型），
            # 通常可以直接复用。如果不行再重建。
            self._voice_clone_prompt = saved_voice_clone_prompt
            print("    [重载] 已恢复 voice_clone_prompt")

    def set_periodic_reload(self, interval: int):
        """
        设置定期重载间隔（每生成 N 句后自动重载模型）。

        参数：
            interval: 重载间隔（句数）。设为 0 或负数表示禁用定期重载。
        """
        self._periodic_reload_interval = max(0, interval)
        if interval > 0:
            print(f"[定期重载] 已设置：每 {interval} 句自动重载模型")
        else:
            print("[定期重载] 已禁用")

    def _maybe_periodic_reload(self):
        """
        检查是否需要定期重载模型。

        在每句生成完成后调用。如果自上次重载以来已生成句数
        达到 _periodic_reload_interval，则触发重载。

        重载后重置计数器，并重建 voice_clone_prompt（如果有参考音频）。
        """
        if self._periodic_reload_interval <= 0:
            return False

        self._sentences_since_reload += 1

        if self._sentences_since_reload >= self._periodic_reload_interval:
            print(f"\n    [定期重载] 已连续生成 {self._sentences_since_reload} 句，"
                  f"触发定期重载以保持音频质量...")
            self._reload_model()
            self._sentences_since_reload = 0
            print(f"    [定期重载] 重载完成，计数器已重置\n")
            return True

        return False

    def _generate_once(self, text: str):
        """
        调用模型生成一次音频，返回 (wavs, sr)。

        参数：
            text: 要合成的文本
        """
        # 固定随机种子：确保每句生成的韵律/语气一致
        import torch
        torch.manual_seed(self.DEFAULT_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.DEFAULT_SEED)

        # 根据文本长度计算合理的 max_new_tokens 上限
        # 防止模型推理不收敛时无限生成导致"卡死"
        max_tokens = self._calc_max_new_tokens(text)

        if self.is_clone_mode:
            # Base 模型：声音克隆
            if self._voice_clone_prompt is not None:
                return self.model.generate_voice_clone(
                    text=text,
                    language="Chinese",
                    voice_clone_prompt=self._voice_clone_prompt,
                    temperature=self.DEFAULT_TEMPERATURE,
                    top_k=self.DEFAULT_TOP_K,
                    top_p=self.DEFAULT_TOP_P,
                    max_new_tokens=max_tokens,
                )
            else:
                return self.model.generate_voice_clone(
                    text=text,
                    language="Chinese",
                    ref_audio=self.reference_voice,
                    ref_text=self.ref_text if not self.x_vector_only else None,
                    x_vector_only_mode=self.x_vector_only,
                    temperature=self.DEFAULT_TEMPERATURE,
                    top_k=self.DEFAULT_TOP_K,
                    top_p=self.DEFAULT_TOP_P,
                    max_new_tokens=max_tokens,
                )
        elif self.is_voice_design_mode:
            # VoiceDesign 模型：语音设计（自然语言描述控制音色）
            return self.model.generate_voice_design(
                text=text,
                instruct=self.voice_design,
                language="Chinese",
                temperature=self.DEFAULT_TEMPERATURE,
                top_k=self.DEFAULT_TOP_K,
                top_p=self.DEFAULT_TOP_P,
                max_new_tokens=max_tokens,
            )
        elif "CustomVoice" in self.model_name:
            # CustomVoice 模型：预设音色 + 可选 instruct 指令
            kwargs = dict(
                text=text,
                language="Chinese",
                speaker=self.speaker,
                temperature=self.DEFAULT_TEMPERATURE,
                top_k=self.DEFAULT_TOP_K,
                top_p=self.DEFAULT_TOP_P,
                max_new_tokens=max_tokens,
            )
            if self.instruct:
                kwargs["instruct"] = self.instruct
            return self.model.generate_custom_voice(**kwargs)
        else:
            # 不应该到这里（Base 模型无参考音频时应在 __init__ 中报错）
            raise RuntimeError(
                f"模型 {self.model_name} 不支持当前模式。"
                "Base 模型需要参考音频（声音克隆），"
                "CustomVoice 模型用于预设音色，"
                "VoiceDesign 模型用于语音设计。"
            )

    @staticmethod
    def _audio_quality_ok(audio_data, sr: int, text: str,
                          max_duration: float) -> tuple:
        """
        检测音频质量，返回 (is_ok, reason)。

        检查项：
        1. 时长是否合理
        2. 是否存在大段静音（杂音的常见特征）
        3. 能量是否过低或过高（乱码音频通常能量异常）
        """
        import numpy as np

        duration = len(audio_data) / sr

        # 检查 1：时长合理性
        if duration > max_duration:
            return False, f"时长 {duration:.2f}s 超过上限 {max_duration:.1f}s"

        # 文本有效字数（排除标点）
        import re
        content_chars = len(re.sub(r'[，。！？、；：\u201c\u201d\u2018\u2019（）…\s]', '', text))
        # 每个字至少 0.1 秒
        min_duration = max(0.3, content_chars * 0.1)
        if duration < min_duration:
            return False, f"时长 {duration:.2f}s 太短（预期至少 {min_duration:.1f}s）"

        # 检查 2：静音比例（短窗口 RMS 低于阈值的比例）
        frame_size = int(sr * 0.025)  # 25ms 帧
        hop = int(sr * 0.010)         # 10ms 步进
        frames = []
        for i in range(0, len(audio_data) - frame_size, hop):
            frame = audio_data[i:i + frame_size].astype(np.float64)
            rms = np.sqrt(np.mean(frame ** 2))
            frames.append(rms)

        if not frames:
            return False, "音频帧数为零"

        frames = np.array(frames)
        silence_threshold = 0.005  # RMS 阈值
        silence_ratio = np.mean(frames < silence_threshold)
        if silence_ratio > 0.7:
            return False, f"静音比例过高 {silence_ratio:.0%}"

        # 检查 3：整体能量 — 太低说明全是噪音
        overall_rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))
        if overall_rms < 0.001:
            return False, f"整体能量过低 RMS={overall_rms:.6f}"

        # 检查 4：高能噪声突刺（乱码特征：能量骤变）
        if len(frames) > 10:
            energy_diff = np.abs(np.diff(frames))
            median_diff = np.median(energy_diff)
            if median_diff > 0:
                spike_ratio = np.mean(energy_diff > median_diff * 15)
                if spike_ratio > 0.15:
                    return False, f"能量突刺比例过高 {spike_ratio:.0%}（疑似杂音）"

        # 检查 5：开头区域异常检测（前导杂音/泄漏音节）
        # 如果音频 > 0.5s，检查前 0.15s 和后续正文的能量对比
        if duration > 0.5 and len(frames) > 30:
            # 前 150ms（约 15 帧 @10ms 步进）
            head_frames = frames[:15]
            # 正文区域：0.2s 到 0.5s
            body_start = 20
            body_end = min(50, len(frames))
            body_frames = frames[body_start:body_end]

            if len(body_frames) > 5:
                head_max = np.max(head_frames)
                body_mean = np.mean(body_frames)
                body_std = np.std(body_frames)

                # 如果开头有一个孤立的能量脉冲，远超正文平均水平
                # 且正文能量本身比较稳定（标准差低），则判定为前导杂音
                if (body_mean > 0 and head_max > body_mean * 4.0
                        and body_std < body_mean * 0.8):
                    # 检查这个高能量是否只出现在最前面几帧（孤立脉冲）
                    high_head = np.sum(head_frames > body_mean * 3.0)
                    if high_head <= 5:  # 只有少数几帧异常高
                        return False, (
                            f"开头存在孤立高能脉冲 "
                            f"(head_max={head_max:.4f}, "
                            f"body_mean={body_mean:.4f})")

        return True, "OK"

    def synthesize(self, text: str, output_path: str) -> float:
        """
        合成单个句子的音频（含重试和质量检测）。

        自参考模式：第一句成功生成后，自动切换到 Base 模型的声音克隆模式，
        用第一句的音频作为参考，确保后续所有句子的语气与第一句一致。

        参数：
            text: 要合成的文本
            output_path: 输出 WAV 文件路径

        返回：生成音频的时长（秒）
        """
        import soundfile as sf

        # 预处理文本：将数字、特殊符号等转为 TTS 友好的形式
        original_text = text
        text = _normalize_text_for_tts(text)
        if text != original_text:
            print(f"    [预处理] {original_text[:50]} → {text[:50]}")

        # 正文的最大预期时长（基于文本长度，用于质量检测和截断）
        text_max_duration = max(
            2.5, len(text) * self.MAX_SECONDS_PER_CHAR
        )

        # 日志：显示 max_new_tokens 限制
        max_tokens = self._calc_max_new_tokens(text)
        max_audio_sec = max_tokens / self.CODEC_TOKENS_PER_SECOND
        print(f"    [tokens] max_new_tokens={max_tokens} "
              f"(上限≈{max_audio_sec:.0f}s音频)")

        best_audio = None
        best_sr = self.sample_rate
        best_duration = 0.0
        best_reason = ""
        reloaded_this_sentence = False  # 每句最多重载一次模型

        for attempt in range(self.MAX_RETRIES):
            try:
                wavs, sr = self._generate_once(text)
                self.sample_rate = sr

                if not wavs or len(wavs) == 0:
                    best_reason = "模型未生成音频"
                    continue

                audio_data = wavs[0]

                # ---- 跑飞检测：音频时长接近 max_new_tokens 上限 ----
                # 说明模型 EOS 检测失败，一路生成到 token 上限。
                # 此时 KV cache 已膨胀，内存压力大。
                # 策略：释放模型 → gc → 重新加载 → 用"干净"状态重试。
                if self._is_runaway_generation(audio_data, sr, text):
                    actual_dur = len(audio_data) / sr
                    print(f"    [跑飞] 第 {attempt + 1} 次生成疑似 EOS 失败"
                          f"（音频 {actual_dur:.1f}s ≈ token 上限），"
                          "丢弃结果")
                    if not reloaded_this_sentence:
                        reloaded_this_sentence = True
                        self._reload_model()
                        self._sentences_since_reload = 0  # 跑飞重载也重置计数器
                        print("    [跑飞] 已重载模型，用干净状态重试")
                    else:
                        print("    [跑飞] 本句已重载过模型，不再重复重载")
                    # 不保存跑飞的音频作为兜底（质量极差）
                    best_reason = f"EOS失败，音频{actual_dur:.1f}s触及上限"
                    continue

                # 质量检测
                is_ok, reason = self._audio_quality_ok(
                    audio_data, sr, text, text_max_duration
                )

                if is_ok:
                    # 质量合格 → 裁剪头部杂音
                    audio_data, trimmed_ms = _trim_leading_noise(
                        audio_data, sr, text
                    )
                    if trimmed_ms > 0:
                        print(f"    [头部清洗] 裁掉前 {trimmed_ms}ms 杂音")
                    sf.write(output_path, audio_data, sr)
                    duration = len(audio_data) / sr
                    if attempt > 0:
                        print(f"    [重试成功] 第 {attempt + 1} 次生成通过质量检测")

                    # ---- 自参考：第一句成功后，保存音频并切换到克隆模式 ----
                    if (hasattr(self, '_self_ref_enabled') and self._self_ref_enabled
                            and not self._self_ref_ready):
                        print(f"\n    [自参考] 第一句生成成功（{duration:.2f}s），"
                              "将以此为基调参考后续所有句子")
                        self._self_ref_first_audio = audio_data.copy()
                        self._self_ref_first_sr = sr
                        self._self_ref_first_text = text
                        self._switch_to_clone_mode()

                    # ---- 预防性重载：音频虽合格但偏长，模型可能在漂移 ----
                    # 主动重载以防止下一句跑飞，相当于"治未病"
                    if (not reloaded_this_sentence
                            and self._needs_preemptive_reload(
                                audio_data, sr, text)):
                        print(f"    [预防] 音频 {duration:.1f}s 偏长，"
                              "主动重载模型防止下一句跑飞")
                        self._reload_model()
                        self._sentences_since_reload = 0  # 预防性重载也重置计数器
                        reloaded_this_sentence = True

                    # ---- 定期重载：每 N 句主动重载一次，防止后期质量退化 ----
                    if not reloaded_this_sentence:
                        if self._maybe_periodic_reload():
                            reloaded_this_sentence = True

                    return duration
                else:
                    print(f"    [质量检测] 第 {attempt + 1} 次不合格: {reason}")
                    # 保存当前最优结果作为兜底
                    duration = len(audio_data) / sr
                    if best_audio is None or duration > best_duration:
                        best_audio = audio_data
                        best_sr = sr
                        best_duration = duration
                        best_reason = reason

            except Exception as e:
                print(f"    [重试] 第 {attempt + 1} 次生成异常: {e}")
                best_reason = str(e)

        # 所有重试都不合格，使用最优兜底结果并截断
        if best_audio is not None:
            print(f"    [兜底] 使用最佳结果（原因: {best_reason}），"
                  f"截断到 {text_max_duration:.1f}s")
            # 先裁剪头部杂音
            best_audio, trimmed_ms = _trim_leading_noise(
                best_audio, best_sr, text
            )
            if trimmed_ms > 0:
                print(f"    [头部清洗] 裁掉前 {trimmed_ms}ms 杂音")
            # 再截断过长的尾部
            truncated_samples = int(text_max_duration * best_sr)
            if len(best_audio) > truncated_samples:
                best_audio = best_audio[:truncated_samples]
            sf.write(output_path, best_audio, best_sr)
            return len(best_audio) / best_sr
        else:
            print(f"[警告] Qwen3-TTS 合成完全失败: {text[:30]}...")
            return 0.0


# ============================================================
# edge-tts 引擎
# ============================================================

class EdgeTTSEngine:
    """edge-tts 语音合成引擎（微软在线 TTS）。"""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        self.voice = voice
        self.sample_rate = 24000  # edge-tts 默认输出采样率

        print(f"[edge-tts] 使用语音: {voice}")
        if voice in EDGE_VOICES:
            print(f"[edge-tts] 语音描述: {EDGE_VOICES[voice]}")

    def synthesize(self, text: str, output_path: str) -> float:
        """
        合成单个句子的音频。

        参数：
            text: 要合成的文本
            output_path: 输出 WAV 文件路径

        返回：生成音频的时长（秒）
        """
        import edge_tts

        try:
            # edge-tts 生成 MP3，需要转换为 WAV
            mp3_path = output_path.rsplit(".", 1)[0] + ".mp3"

            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
            )
            communicate.save_sync(mp3_path)

            # 使用 FFmpeg 转换为 WAV（24kHz 单声道 16bit PCM）
            cmd = [
                "ffmpeg", "-y",
                "-i", mp3_path,
                "-acodec", "pcm_s16le",
                "-ar", str(self.sample_rate),
                "-ac", "1",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[错误] MP3→WAV 转换失败: {result.stderr}", file=sys.stderr)
                return 0.0

            # 清理临时 MP3
            if os.path.exists(mp3_path):
                os.remove(mp3_path)

            # 获取音频时长
            duration = get_audio_duration(output_path)
            return duration

        except Exception as e:
            print(f"[错误] edge-tts 合成失败 '{text[:30]}...': {e}", file=sys.stderr)
            return 0.0


# ============================================================
# 文本预处理（减少 TTS 杂音/幻觉）
# ============================================================

def _normalize_text_for_tts(text: str) -> str:
    """
    对输入文本做预处理，减少 Qwen3-TTS 在遇到数字、英文、特殊符号时的
    杂音/乱码/幻觉重复问题。

    处理策略：
    1. 将纯数字转为中文读法（如 15 → 十五）
    2. 将带单位的数字保留自然读法（如 140KB → 一百四十 KB）
    3. 将百分号转为"百分之"
    4. 将常见技术缩写保留但确保与数字分离
    5. 清除多余符号
    """
    import re

    # ---- 辅助：数字转中文 ----
    _DIGITS = "零一二三四五六七八九"
    _UNITS_SMALL = ["", "十", "百", "千"]
    _UNITS_BIG = ["", "万", "亿"]

    def _int_to_chinese(n: int) -> str:
        """整数转中文（支持到亿级别）。"""
        if n == 0:
            return "零"
        if n < 0:
            return "负" + _int_to_chinese(-n)

        result = ""
        s = str(n)
        length = len(s)

        # 按4位分组
        groups = []
        while s:
            groups.append(s[-4:] if len(s) >= 4 else s)
            s = s[:-4]
        groups.reverse()

        for gi, group in enumerate(groups):
            group_val = int(group)
            if group_val == 0:
                continue

            big_unit = _UNITS_BIG[len(groups) - 1 - gi] if (len(groups) - 1 - gi) < len(_UNITS_BIG) else ""

            # 需要补零的情况
            if gi > 0 and int(group) < 1000 and len(group) == len(str(int(group))):
                if result and not result.endswith("零"):
                    result += "零"

            g_str = ""
            for di, ch in enumerate(group):
                d = int(ch)
                pos = len(group) - 1 - di  # 千百十个
                if d == 0:
                    if g_str and not g_str.endswith("零") and pos > 0:
                        g_str += "零"
                else:
                    # 特殊处理：十位为1时省略"一"（如 15 → 十五，而非一十五）
                    if d == 1 and pos == 1 and not g_str:
                        g_str += _UNITS_SMALL[pos]
                    else:
                        g_str += _DIGITS[d] + _UNITS_SMALL[pos]

            g_str = g_str.rstrip("零")
            result += g_str + big_unit

        return result

    def _number_to_chinese(match_str: str) -> str:
        """将数字字符串转为中文读法。"""
        # 处理小数
        if "." in match_str:
            parts = match_str.split(".", 1)
            integer_part = _int_to_chinese(int(parts[0])) if parts[0] else "零"
            decimal_part = "".join(_DIGITS[int(d)] for d in parts[1])
            return integer_part + "点" + decimal_part
        else:
            return _int_to_chinese(int(match_str))

    result = text

    # 1. 处理百分比：98% → 百分之九十八
    result = re.sub(
        r'(\d+(?:\.\d+)?)\s*%',
        lambda m: "百分之" + _number_to_chinese(m.group(1)),
        result
    )

    # 2. 处理带单位的数字：15万 → 十五万，140KB → 一百四十KB
    result = re.sub(
        r'(\d+(?:\.\d+)?)\s*(万|亿|千|百|美元|元|块钱|块|分钟|秒|小时|天|年|月|步|条|个|次|倍|级)',
        lambda m: _number_to_chinese(m.group(1)) + m.group(2),
        result
    )

    # 3. 处理带英文单位的数字：140KB → 一百四十 KB，保留英文单位
    result = re.sub(
        r'(\d+(?:\.\d+)?)\s*(KB|MB|GB|TB|token|Token|tokens|Tokens)',
        lambda m: _number_to_chinese(m.group(1)) + " " + m.group(2),
        result,
        flags=re.IGNORECASE
    )

    # 4. 处理剩余的纯数字（前后不紧邻字母的）
    result = re.sub(
        r'(?<![a-zA-Z])(\d+(?:\.\d+)?)(?![a-zA-Z%])',
        lambda m: _number_to_chinese(m.group(1)),
        result
    )

    # 5. 清理：将多余的空格、破折号等标准化
    result = re.sub(r'——', '，', result)  # 中文破折号转逗号（TTS 更稳定）
    result = re.sub(r'—', '，', result)
    result = re.sub(r'\s+', ' ', result).strip()

    return result


# ============================================================
# 工具函数
# ============================================================

def get_audio_duration(audio_path: str) -> float:
    """使用 ffprobe 获取音频文件时长（秒）。"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def speed_up_audio(input_path: str, speed_factor: float) -> float:
    """
    对音频文件进行变速处理（保持音调不变），原地替换。

    参数：
        input_path: 音频文件路径
        speed_factor: 加速倍率（如 1.2 表示加速 20%）

    返回：变速后的时长（秒）
    """
    if speed_factor <= 1.0:
        return get_audio_duration(input_path)

    tmp_path = input_path + ".tmp.wav"
    # ffmpeg atempo 支持范围 [0.5, 100.0]，对大于 2.0 的需要链式
    atempo_filters = []
    remaining = speed_factor
    while remaining > 2.0:
        atempo_filters.append("atempo=2.0")
        remaining /= 2.0
    atempo_filters.append(f"atempo={remaining:.4f}")
    filter_str = ",".join(atempo_filters)

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-filter:a", filter_str,
             "-loglevel", "error",
             tmp_path],
            check=True, capture_output=True
        )
        os.replace(tmp_path, input_path)
        return get_audio_duration(input_path)
    except Exception as e:
        # 变速失败则保留原文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        print(f"    [警告] 变速失败: {e}")
        return get_audio_duration(input_path)


def add_silence(duration_sec: float, sample_rate: int = 24000) -> str:
    """生成指定时长的静音 WAV 文件。"""
    import wave

    samples = int(duration_sec * sample_rate)
    tmp_path = f"/tmp/silence_{duration_sec:.2f}s.wav"

    # 使用标准库生成静音 WAV，避免依赖 torch
    with wave.open(tmp_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * samples)

    return tmp_path


def concatenate_audio_files(audio_files: list, output_path: str, sample_rate: int = 24000):
    """使用 FFmpeg 拼接多个音频文件。"""
    if not audio_files:
        return

    list_path = output_path + ".filelist.txt"
    with open(list_path, "w") as f:
        for af in audio_files:
            abs_path = os.path.abspath(af)
            f.write(f"file '{abs_path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-acodec", "pcm_s16le",
        "-ar", str(sample_rate),
        "-ac", "1",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[错误] 音频拼接失败: {result.stderr}", file=sys.stderr)

    # 清理临时文件列表
    if os.path.exists(list_path):
        os.remove(list_path)


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="使用 Qwen3-TTS 或 edge-tts 生成演讲音频")
    parser.add_argument("--speech_json", required=True, help="第2步生成的结构化演讲 JSON")
    parser.add_argument("--output_dir", required=True, help="输出目录")
    parser.add_argument("--tts_engine", choices=["auto", "qwen3", "edge"], default="auto",
                        help="TTS 引擎选择：auto（自动）、qwen3（Qwen3-TTS）、edge（edge-tts）")
    parser.add_argument("--reference_voice", default="",
                        help="（可选）参考音频文件路径，用于 Qwen3-TTS 声音克隆。"
                             "提供此参数时 Qwen3-TTS 将克隆参考音频的音色；"
                             "不提供则使用预设音色。edge-tts 不支持声音克隆，此参数对其无效。")
    parser.add_argument("--ref_text", default="",
                        help="（可选）参考音频中说话人的文字内容。"
                             "用于声音克隆 ICL 模式（效果最好）。"
                             "为空时自动使用 Whisper 转录；"
                             "Whisper 不可用则降级为仅声纹嵌入模式。")
    parser.add_argument("--speaker", default="Vivian",
                        help="Qwen3-TTS 预设音色（无参考音频时使用，默认: Vivian）。可选: " +
                             ", ".join(f"{k}({v})" for k, v in QWEN3_SPEAKERS.items()))
    parser.add_argument("--voice_design", default="",
                        help="（可选）使用 VoiceDesign 模型的语音设计模式。"
                             "传入自然语言描述（如 '成熟稳重的男性声音，语速适中'），"
                             "将加载 VoiceDesign 模型用自然语言'设计'全新音色，无需预设 speaker。"
                             "注意：此模式需要下载 VoiceDesign 模型（约 3.4GB）。")
    parser.add_argument("--instruct", default="",
                        help="（可选）CustomVoice 模式的语气/语调控制指令。"
                             "仅在 CustomVoice 预设音色模式下生效。"
                             "默认值为专业播音腔风格（适合 PPT 讲解），"
                             "确保全片语气统一平稳。"
                             "自定义示例：'用温暖亲切的声音朗读' 或 '用充满科技感的语调朗读'。")
    parser.add_argument("--edge_voice", default="zh-CN-XiaoxiaoNeural",
                        help="edge-tts 语音名称（默认: zh-CN-XiaoxiaoNeural）。可选: " +
                             ", ".join(f"{k}({v})" for k, v in EDGE_VOICES.items()))
    parser.add_argument("--sample_rate", type=int, default=24000, help="音频采样率（默认: 24000）")
    parser.add_argument("--sentence_pause", type=float, default=0.4,
                        help="句子间停顿时长（秒，默认: 0.4）")
    parser.add_argument("--slide_pause", type=float, default=1.0,
                        help="页面间停顿时长（秒，默认: 1.0）")
    parser.add_argument("--speed_factor", type=float, default=1.0,
                        help="语速倍率（默认: 1.0，建议 1.15-1.3 加快语速）")
    parser.add_argument("--temperature", type=float, default=None,
                        help="TTS 采样温度（默认: 0.3）。越低语气越稳定一致，"
                             "越高越有表现力但句间差异大。"
                             "PPT 讲解推荐 0.2-0.4，有声读物推荐 0.6-0.8。")
    parser.add_argument("--periodic_reload", type=int, default=30,
                        help="Qwen3-TTS 定期重载间隔（句数，默认: 30）。"
                             "每生成 N 句后自动重载模型，清理累积状态，"
                             "防止后期音频质量退化（语速变慢、音色不稳定）。"
                             "设为 0 禁用定期重载。推荐值: 25-35。")
    parser.add_argument("--self_reference", action="store_true", default=True,
                        help="启用自参考模式（默认启用）。"
                             "第一句用 CustomVoice 生成确立语气基调，"
                             "然后自动切换到 Base 模型，用第一句音频作为参考，"
                             "后续所有句子都克隆第一句的语气风格。"
                             "这能有效解决句间语气不一致的问题。")
    parser.add_argument("--no_self_reference", action="store_true",
                        help="禁用自参考模式（使用纯 CustomVoice 逐句生成）。")
    parser.add_argument("--regenerate", nargs="+", default=[],
                        help="只重新生成指定的句子，其余复用已有音频。"
                             "格式: slide<页码>_sent<句号> 或 <页码>:<句号> 或 <页码>-<句号>。"
                             "示例: --regenerate slide1_sent000 slide3_sent002  "
                             "或    --regenerate 1:0 3:2  "
                             "或    --regenerate 1-0 3-2  "
                             "多个句子用空格分隔。"
                             "也支持只指定页码（重新生成该页所有句子）: --regenerate slide2 或 2")
    # 保留但忽略旧参数（向后兼容）
    parser.add_argument("--default_speaker", default="", help=argparse.SUPPRESS)
    parser.add_argument("--prompt_text", default="", help=argparse.SUPPRESS)
    args = parser.parse_args()

    # ---- 解析 --regenerate 参数 ----
    regenerate_set = set()   # 存储 (slide_num, sent_idx) 元组
    regenerate_slides = set()  # 存储需要整页重新生成的 slide_num
    is_regenerate_mode = bool(args.regenerate)

    if is_regenerate_mode:
        import re as _re
        for token in args.regenerate:
            token = token.strip()
            # 格式1: slide3_sent002
            m = _re.match(r'^slide(\d+)_sent(\d+)$', token, _re.IGNORECASE)
            if m:
                regenerate_set.add((int(m.group(1)), int(m.group(2))))
                continue
            # 格式2: 3:2 或 3-2
            m = _re.match(r'^(\d+)[:：\-](\d+)$', token)
            if m:
                regenerate_set.add((int(m.group(1)), int(m.group(2))))
                continue
            # 格式3: slide2（整页重新生成）
            m = _re.match(r'^slide(\d+)$', token, _re.IGNORECASE)
            if m:
                regenerate_slides.add(int(m.group(1)))
                continue
            # 格式4: 纯数字（整页重新生成）
            m = _re.match(r'^(\d+)$', token)
            if m:
                regenerate_slides.add(int(m.group(1)))
                continue
            print(f"[警告] 无法解析 --regenerate 参数: '{token}'，"
                  "支持格式: slide1_sent000, 1:0, 1-0, slide1, 1",
                  file=sys.stderr)

        if regenerate_set or regenerate_slides:
            regen_desc = []
            for s, i in sorted(regenerate_set):
                regen_desc.append(f"slide{s}_sent{i:03d}")
            for s in sorted(regenerate_slides):
                regen_desc.append(f"slide{s}(整页)")
            print(f"\n[第3步] 🔄 重新生成模式：只重新生成 {', '.join(regen_desc)}，"
                  "其余复用已有音频")
        else:
            print("[警告] --regenerate 指定了但未解析出有效目标，将全量生成",
                  file=sys.stderr)
            is_regenerate_mode = False

    def _should_regenerate(slide_num: int, sent_idx: int) -> bool:
        """判断指定的句子是否被强制要求重新生成（忽略已有文件）。
        
        返回 True  → 强制重新生成（regenerate 模式下指定的目标）
        返回 False → 不强制，由外层文件存在性检查决定是否跳过（断点续传）
        """
        if not is_regenerate_mode:
            return False  # 非重新生成模式：不强制，断点续传由文件存在性决定
        if slide_num in regenerate_slides:
            return True  # 整页重新生成
        if (slide_num, sent_idx) in regenerate_set:
            return True  # 指定句子重新生成
        return False

    # 检测 TTS 引擎
    engine_name = detect_tts_engine(args.tts_engine)
    print(f"\n[第3步] TTS 引擎: {engine_name}")

    # 加载演讲数据
    with open(args.speech_json, "r", encoding="utf-8") as f:
        speech_data = json.load(f)

    slides = speech_data["slides"]
    os.makedirs(args.output_dir, exist_ok=True)

    # ---- Acquire process lock to prevent concurrent step3 runs ----
    lock_path = os.path.join(args.output_dir, ".step3.lock")
    lock_fd = None

    def _is_pid_alive(pid_str: str) -> bool:
        """Check if a process with the given PID string is still alive."""
        try:
            pid = int(pid_str)
            os.kill(pid, 0)
            return True
        except (ValueError, ProcessLookupError):
            return False
        except PermissionError:
            return True  # process exists but we can't signal it

    for _lock_attempt in range(2):
        try:
            lock_fd = open(lock_path, "w")
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_fd.write(str(os.getpid()))
            lock_fd.flush()
            break  # acquired successfully
        except (IOError, OSError):
            try:
                with open(lock_path, "r") as f:
                    other_pid = f.read().strip()
            except Exception:
                other_pid = "unknown"

            if _is_pid_alive(other_pid):
                print(
                    f"[错误] 另一个 step3 进程 (PID {other_pid}) 正在运行中。\n"
                    f"       请等待其完成，或手动终止后重试。\n"
                    f"       锁文件: {lock_path}",
                    file=sys.stderr,
                )
                sys.exit(1)
            else:
                # Stale lock — previous process is dead, clean up and retry
                print(f"[第3步] 检测到残留锁文件（PID {other_pid} 已不存在），自动清理后继续。")
                try:
                    if lock_fd is not None:
                        lock_fd.close()
                        lock_fd = None
                    os.remove(lock_path)
                except OSError:
                    pass
                continue
    else:
        print("[错误] 无法获取 step3 进程锁，终止。", file=sys.stderr)
        sys.exit(1)

    def _release_lock():
        nonlocal lock_fd
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
            except Exception:
                pass
            lock_fd = None
        try:
            os.remove(lock_path)
        except OSError:
            pass

    import atexit
    atexit.register(_release_lock)

    # ---- Engine consistency check ----
    # Prevent mixing audio from different TTS engines in the same output dir.
    engine_marker_path = os.path.join(args.output_dir, ".tts_engine")
    if not is_regenerate_mode:
        if os.path.isfile(engine_marker_path):
            with open(engine_marker_path, "r") as f:
                prev_engine = f.read().strip()
            if prev_engine and prev_engine != engine_name:
                print(
                    f"[警告] 检测到引擎不一致：之前使用 '{prev_engine}'，"
                    f"本次使用 '{engine_name}'。\n"
                    f"       为避免混用不同引擎的音频，将清除已有的句子音频并重新生成。",
                )
                # Clean up stale audio from the previous engine
                sentences_dir_tmp = os.path.join(args.output_dir, "sentences")
                slides_dir_tmp = os.path.join(args.output_dir, "slides")
                for d in [sentences_dir_tmp, slides_dir_tmp]:
                    if os.path.isdir(d):
                        for fname in os.listdir(d):
                            fpath = os.path.join(d, fname)
                            if os.path.isfile(fpath):
                                os.remove(fpath)
                # Also remove full_speech.wav and timing_data.json
                for fname in ["full_speech.wav", "timing_data.json"]:
                    fpath = os.path.join(args.output_dir, fname)
                    if os.path.isfile(fpath):
                        os.remove(fpath)
        # Write current engine marker
        with open(engine_marker_path, "w") as f:
            f.write(engine_name)

    # 创建子目录
    sentences_dir = os.path.join(args.output_dir, "sentences")
    slides_audio_dir = os.path.join(args.output_dir, "slides")
    os.makedirs(sentences_dir, exist_ok=True)
    os.makedirs(slides_audio_dir, exist_ok=True)

    # Check whether we actually need to load the TTS engine.
    # In regenerate mode: only if there are sentences to regenerate.
    # In normal mode: only if some sentences are missing valid audio (resume).
    need_tts_engine = False
    _resume_skipped = 0
    _resume_total = 0
    for slide in slides:
        slide_num = slide["slide_number"]
        for idx in range(len(slide["sentences"])):
            _resume_total += 1
            should_regen = _should_regenerate(slide_num, idx)
            sent_file = os.path.join(sentences_dir, f"slide{slide_num}_sent{idx:03d}.wav")
            if not should_regen and os.path.isfile(sent_file) and get_audio_duration(sent_file) > 0:
                _resume_skipped += 1
            else:
                need_tts_engine = True
    if _resume_skipped > 0 and not is_regenerate_mode:
        print(f"[第3步] 断点续传：已有 {_resume_skipped}/{_resume_total} 个句子的有效音频，将跳过这些句子")

    if need_tts_engine:
        if engine_name == "qwen3":
            print("[第3步] 正在加载 Qwen3-TTS 模型...")
            engine = Qwen3TTSEngine(
                speaker=args.speaker,
                reference_voice=args.reference_voice,
                ref_text=args.ref_text,
                voice_design=args.voice_design,
                instruct=args.instruct,
            )
            # 应用用户指定的 temperature（覆盖默认值）
            if args.temperature is not None:
                engine.DEFAULT_TEMPERATURE = args.temperature
                print(f"[Qwen3-TTS] 采样温度: {args.temperature}"
                      f"（{'低随机性，语气稳定' if args.temperature <= 0.4 else '较高随机性，语气多变'}）")
            else:
                print(f"[Qwen3-TTS] 采样温度: {engine.DEFAULT_TEMPERATURE}（默认，低随机性，语气稳定）")

            # 设置定期重载间隔
            engine.set_periodic_reload(args.periodic_reload)

            # 启用自参考模式（仅限 CustomVoice/VoiceDesign 非克隆模式）
            # 自参考：第一句用原始模型生成确立语气基调，然后切换到 Base 模型克隆
            use_self_ref = args.self_reference and not args.no_self_reference
            # regenerate 模式下禁用自参考（只生成少数句子，不需要重新确立基调）
            if is_regenerate_mode:
                use_self_ref = False
            if use_self_ref and not engine.is_clone_mode:
                engine.enable_self_reference()
            elif use_self_ref and engine.is_clone_mode:
                print("[自参考] 已有参考音频，无需自参考模式")

            sample_rate = engine.sample_rate
            if engine.is_clone_mode:
                clone_type = "ICL" if not engine.x_vector_only else "x_vector"
                voice_desc = (f"Qwen3-TTS 声音克隆/{clone_type}"
                              f"（参考: {os.path.basename(args.reference_voice)}，"
                              f"模型: {engine.model_name}）")
            elif engine.is_voice_design_mode:
                voice_desc = (f"Qwen3-TTS 语音设计（指令: {engine.voice_design[:40]}，"
                              f"模型: {engine.model_name}）")
            else:
                instruct_info = f"，instruct: {engine.instruct[:30]}" if engine.instruct else ""
                voice_desc = (f"Qwen3-TTS 预设音色（{engine.speaker}{instruct_info}，"
                              f"模型: {engine.model_name}）")
        else:
            engine = EdgeTTSEngine(voice=args.edge_voice)
            sample_rate = engine.sample_rate
            voice_desc = f"edge-tts 预设音色（{args.edge_voice}）"
    else:
        # regenerate 模式下没有需要重新生成的句子，不需要加载 TTS 引擎
        engine = None
        sample_rate = args.sample_rate
        voice_desc = "无（纯复用模式）"
        print("[第3步] 所有指定句子均已存在且不需要重新生成，跳过 TTS 引擎加载")

    print(f"[第3步] 使用音色: {voice_desc}")
    print(f"[第3步] 采样率: {sample_rate}Hz")
    if args.speed_factor > 1.0:
        print(f"[第3步] 语速倍率: x{args.speed_factor:.2f}")

    # 时间元数据
    _is_qwen3 = engine_name == "qwen3" and engine is not None
    timing_data = {
        "sample_rate": sample_rate,
        "voice_mode": ("clone" if (_is_qwen3 and engine.is_clone_mode)
                       else "voice_design" if (_is_qwen3 and engine.is_voice_design_mode)
                       else "preset"),
        "tts_engine": engine_name,
        "speaker": engine.speaker if _is_qwen3 else (args.edge_voice if engine is not None else ""),
        "instruct": engine.instruct if (_is_qwen3 and not engine.is_clone_mode) else "",
        "voice_design": engine.voice_design if (_is_qwen3 and engine.is_voice_design_mode) else "",
        "reference_voice": args.reference_voice if (_is_qwen3 and engine.is_clone_mode) else "",
        "slides": [],
        "total_duration": 0.0
    }

    all_audio_files = []
    current_time = 0.0

    for slide in slides:
        slide_num = slide["slide_number"]
        slide_title = slide["title"]
        sentences = slide["sentences"]
        # tts_sentences: pronunciation-normalized text for TTS
        # Falls back to sentences if not present (backward compat)
        tts_sentences = slide.get("tts_sentences", sentences)

        print(f"\n[第3步] 处理第 {slide_num} 页: {slide_title}")
        print(f"  句子数: {len(sentences)}")

        slide_start_time = current_time
        slide_audio_files = []
        sentence_timings = []

        for idx, sentence in enumerate(sentences):
            # Use tts_text for audio synthesis, original sentence for subtitles
            tts_text = tts_sentences[idx] if idx < len(tts_sentences) else sentence
            sent_file = os.path.join(sentences_dir, f"slide{slide_num}_sent{idx:03d}.wav")

            # ---- Resume / regenerate: reuse existing valid audio ----
            should_regen = _should_regenerate(slide_num, idx)
            if os.path.isfile(sent_file) and not should_regen:
                # Reuse existing audio (both regenerate-skip and resume modes)
                duration = get_audio_duration(sent_file)
                if duration > 0:
                    label = "♻️ 复用" if is_regenerate_mode else "⏩ 跳过(已有)"
                    print(f"  {label}: [{idx+1}/{len(sentences)}] {sentence[:40]}..."
                          f" ({duration:.2f}s)")
                    sentence_timings.append({
                        "index": idx,
                        "text": sentence,
                        "start_time": current_time,
                        "duration": duration,
                        "end_time": current_time + duration,
                        "audio_file": sent_file
                    })
                    slide_audio_files.append(sent_file)
                    all_audio_files.append(sent_file)
                    current_time += duration

                    # 句子间添加停顿（最后一句不加）
                    if idx < len(sentences) - 1:
                        pause_file = add_silence(args.sentence_pause, sample_rate)
                        slide_audio_files.append(pause_file)
                        all_audio_files.append(pause_file)
                        current_time += args.sentence_pause
                    continue
                else:
                    print(f"  ⚠️ 已有文件无效，将重新生成: {sent_file}")

            print(f"  🔊 生成中: [{idx+1}/{len(sentences)}] {sentence[:40]}..."
                  f"{'  (重新生成)' if is_regenerate_mode else ''}")
            if tts_text != sentence:
                print(f"    [TTS文本] {tts_text[:60]}...")
            start_t = time.time()

            duration = engine.synthesize(text=tts_text, output_path=sent_file)

            # 变速处理（保持音调不变）
            if duration > 0 and args.speed_factor > 1.0:
                original_dur = duration
                duration = speed_up_audio(sent_file, args.speed_factor)
                if abs(duration - original_dur) > 0.01:
                    print(f"    [变速] {original_dur:.2f}s → {duration:.2f}s "
                          f"(x{args.speed_factor:.2f})")

            # Qwen3-TTS 可能在第一次合成时更新采样率
            if engine_name == "qwen3" and engine is not None and engine.sample_rate != sample_rate:
                sample_rate = engine.sample_rate
                timing_data["sample_rate"] = sample_rate
                print(f"[第3步] 采样率更新为: {sample_rate}Hz")

            gen_time = time.time() - start_t
            print(f"    时长: {duration:.2f}秒（生成耗时 {gen_time:.1f}秒）")

            if duration > 0:
                sentence_timings.append({
                    "index": idx,
                    "text": sentence,
                    "start_time": current_time,
                    "duration": duration,
                    "end_time": current_time + duration,
                    "audio_file": sent_file
                })
                slide_audio_files.append(sent_file)
                all_audio_files.append(sent_file)
                current_time += duration

                # 句子间添加停顿（最后一句不加）
                if idx < len(sentences) - 1:
                    pause_file = add_silence(args.sentence_pause, sample_rate)
                    slide_audio_files.append(pause_file)
                    all_audio_files.append(pause_file)
                    current_time += args.sentence_pause

        # 拼接本页音频
        slide_audio_path = os.path.join(slides_audio_dir, f"slide{slide_num}_audio.wav")
        concatenate_audio_files(slide_audio_files, slide_audio_path, sample_rate)

        slide_end_time = current_time
        slide_duration = slide_end_time - slide_start_time

        timing_data["slides"].append({
            "slide_number": slide_num,
            "title": slide_title,
            "start_time": slide_start_time,
            "end_time": slide_end_time,
            "duration": slide_duration,
            "audio_file": slide_audio_path,
            "sentences": sentence_timings
        })

        print(f"  第 {slide_num} 页时长: {slide_duration:.2f}秒")

        # 页面间添加停顿
        if slide != slides[-1]:
            pause_file = add_silence(args.slide_pause, sample_rate)
            all_audio_files.append(pause_file)
            current_time += args.slide_pause

    # 拼接完整音频
    full_audio_path = os.path.join(args.output_dir, "full_speech.wav")
    concatenate_audio_files(all_audio_files, full_audio_path, sample_rate)

    timing_data["total_duration"] = current_time

    # 保存时间数据
    timing_path = os.path.join(args.output_dir, "timing_data.json")
    with open(timing_path, "w", encoding="utf-8") as f:
        json.dump(timing_data, f, ensure_ascii=False, indent=2)

    print("\n[第3步完成] 语音合成完成。")
    if is_regenerate_mode:
        print(f"  模式: 🔄 部分重新生成")
    print(f"  TTS 引擎: {engine_name}")
    print(f"  使用音色: {voice_desc}")
    print(f"  完整音频: {full_audio_path}")
    print(f"  总时长: {current_time:.2f}秒")
    print(f"  时间数据: {timing_path}")

    return timing_data


if __name__ == "__main__":
    main()
