#!/usr/bin/env python3
"""
环境检查脚本：检测 PPT转视频 流水线所需的所有依赖。

运行方式：
    python check_environment.py
    python check_environment.py --fix  # 尝试自动安装缺失依赖

输出：
    - 绿色 ✅：已安装且可用
    - 黄色 ⚠️：可选但未安装
    - 红色 ❌：必需但缺失

返回码：
    0：所有必需依赖已满足
    1：存在缺失的必需依赖
"""

import argparse
import subprocess
import sys
import shutil
import os
from typing import Tuple, List


# ============================================================
# 颜色输出
# ============================================================

class Colors:
    """终端颜色代码"""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_status(status: str, name: str, message: str = "", detail: str = ""):
    """打印状态信息"""
    if status == "ok":
        icon = f"{Colors.GREEN}✅{Colors.END}"
    elif status == "warn":
        icon = f"{Colors.YELLOW}⚠️{Colors.END}"
    else:
        icon = f"{Colors.RED}❌{Colors.END}"
    
    line = f"  {icon} {name}"
    if message:
        line += f" — {message}"
    print(line)
    if detail:
        print(f"      {Colors.CYAN}{detail}{Colors.END}")


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}  {title}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")


# ============================================================
# 依赖检查函数
# ============================================================

def check_command(cmd: str) -> bool:
    """检查系统命令是否存在"""
    return shutil.which(cmd) is not None


def check_python_package(package: str, import_name: str = None) -> Tuple[bool, str]:
    """
    检查 Python 包是否已安装并可导入。
    
    返回: (是否可用, 版本或错误信息)
    """
    if import_name is None:
        import_name = package.replace("-", "_")
    
    try:
        module = __import__(import_name)
        version = getattr(module, "__version__", "已安装")
        return True, version
    except ImportError as e:
        return False, str(e)


def get_ffmpeg_version() -> Tuple[bool, str]:
    """获取 FFmpeg 版本"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            first_line = result.stdout.split("\n")[0]
            return True, first_line
        return False, "执行失败"
    except Exception as e:
        return False, str(e)


def check_gpu_availability() -> Tuple[str, str]:
    """检测 GPU 可用性"""
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            return "cuda", f"CUDA: {device_name}"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps", "Apple Silicon MPS"
        else:
            return "cpu", "CPU（无 GPU 加速）"
    except ImportError:
        return "unknown", "torch 未安装，无法检测"


def check_model_cache() -> List[Tuple[str, str]]:
    """检查 Qwen3-TTS 模型缓存"""
    models_found = []
    
    # HuggingFace 缓存目录
    hf_cache = os.path.expanduser("~/.cache/huggingface/hub")
    if os.path.exists(hf_cache):
        for item in os.listdir(hf_cache):
            if "Qwen3-TTS" in item:
                model_path = os.path.join(hf_cache, item)
                size = get_dir_size(model_path)
                models_found.append((item, f"{size/1024/1024/1024:.1f} GB"))
    
    # ModelScope 缓存目录
    ms_cache = os.path.expanduser("~/.cache/modelscope/hub")
    if os.path.exists(ms_cache):
        for item in os.listdir(ms_cache):
            if "Qwen3-TTS" in item or "qwen3-tts" in item.lower():
                model_path = os.path.join(ms_cache, item)
                size = get_dir_size(model_path)
                models_found.append((item, f"{size/1024/1024/1024:.1f} GB"))
    
    return models_found


def get_dir_size(path: str) -> int:
    """获取目录大小（字节）"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total


def check_system_font(font_name: str) -> bool:
    """检查系统字体是否存在"""
    try:
        result = subprocess.run(
            ["fc-list", font_name],
            capture_output=True, text=True, timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


# ============================================================
# 安装指令
# ============================================================

INSTALL_INSTRUCTIONS = {
    "ffmpeg": {
        "macOS": "brew install ffmpeg-full",
        "Ubuntu": "sudo apt-get install ffmpeg",
        "Windows": "下载 https://ffmpeg.org/download.html 或使用 choco install ffmpeg",
    },
    "poppler": {
        "macOS": "brew install poppler",
        "Ubuntu": "sudo apt-get install poppler-utils",
        "Windows": "下载 https://github.com/oschwartz10612/poppler-windows/releases",
    },
    "qwen-tts": "pip install -U qwen-tts",
    "edge-tts": "pip install edge-tts",
    "PyMuPDF": "pip install PyMuPDF",
    "numpy": "pip install numpy",
    "openai-whisper": "pip install openai-whisper",
    "demucs": "pip install demucs",
    "pdf2image": "pip install pdf2image",
    "torch": "pip install torch torchaudio",
}


def get_platform() -> str:
    """获取当前平台"""
    import platform
    system = platform.system()
    if system == "Darwin":
        return "macOS"
    elif system == "Linux":
        return "Ubuntu"
    else:
        return "Windows"


def print_install_instruction(name: str):
    """打印安装指令"""
    instr = INSTALL_INSTRUCTIONS.get(name, f"pip install {name}")
    if isinstance(instr, dict):
        platform = get_platform()
        instr = instr.get(platform, list(instr.values())[0])
    print(f"      安装: {Colors.CYAN}{instr}{Colors.END}")


# ============================================================
# 主检查流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="检查 PPT转视频 流水线环境")
    parser.add_argument("--fix", action="store_true", 
                        help="尝试自动安装缺失的 Python 依赖")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="显示详细信息")
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}PPT转视频流水线 — 环境检查{Colors.END}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"平台: {get_platform()}")
    
    all_ok = True
    missing_required = []
    missing_optional = []
    
    # ========================================
    # 1. 系统工具检查
    # ========================================
    print_section("系统工具")
    
    # FFmpeg (必需)
    ok, version = get_ffmpeg_version()
    if ok:
        print_status("ok", "FFmpeg", version.split(" ")[2] if len(version.split(" ")) > 2 else "已安装")
    else:
        print_status("fail", "FFmpeg", "未安装（必需）")
        print_install_instruction("ffmpeg")
        missing_required.append("FFmpeg")
        all_ok = False
    
    # ffprobe (通常与 FFmpeg 一起)
    if check_command("ffprobe"):
        print_status("ok", "ffprobe", "已安装")
    else:
        print_status("fail", "ffprobe", "未安装（必需）")
        print(f"      通常与 FFmpeg 一起安装")
        all_ok = False
    
    # ========================================
    # 2. Python 核心依赖
    # ========================================
    print_section("Python 核心依赖")
    
    # numpy (必需)
    ok, info = check_python_package("numpy")
    if ok:
        print_status("ok", "numpy", info)
    else:
        print_status("fail", "numpy", "未安装（必需）")
        print_install_instruction("numpy")
        missing_required.append("numpy")
        all_ok = False
    
    # PyMuPDF (必需，PDF 转换)
    ok, info = check_python_package("PyMuPDF", "fitz")
    if ok:
        print_status("ok", "PyMuPDF (fitz)", info)
    else:
        print_status("fail", "PyMuPDF (fitz)", "未安装（必需，用于 PDF 转图片）")
        print_install_instruction("PyMuPDF")
        missing_required.append("PyMuPDF")
        all_ok = False
    
    # ========================================
    # 3. TTS 引擎检查（至少一个）
    # ========================================
    print_section("TTS 引擎（至少安装其一）")
    
    has_qwen3 = False
    has_edge = False
    
    # Qwen3-TTS (推荐)
    ok, info = check_python_package("qwen-tts", "qwen_tts")
    if ok:
        print_status("ok", "qwen-tts", f"{info}（推荐，本地高质量，支持声音克隆）")
        has_qwen3 = True
    else:
        print_status("warn", "qwen-tts", "未安装（推荐安装）")
        print_install_instruction("qwen-tts")
    
    # edge-tts (备选)
    ok, info = check_python_package("edge-tts", "edge_tts")
    if ok:
        print_status("ok", "edge-tts", f"{info}（备选，需联网）")
        has_edge = True
    else:
        print_status("warn", "edge-tts", "未安装（备选方案）")
        print_install_instruction("edge-tts")
    
    if not has_qwen3 and not has_edge:
        print(f"\n  {Colors.RED}❌ 错误：至少需要安装一个 TTS 引擎！{Colors.END}")
        print(f"     推荐: pip install -U qwen-tts")
        print(f"     或者: pip install edge-tts")
        missing_required.append("TTS引擎(qwen-tts 或 edge-tts)")
        all_ok = False
    
    # ========================================
    # 4. 可选依赖
    # ========================================
    print_section("可选依赖（增强功能）")
    
    # PyTorch (Qwen3-TTS 依赖)
    ok, info = check_python_package("torch")
    if ok:
        gpu_type, gpu_info = check_gpu_availability()
        print_status("ok", "torch", f"{info} | {gpu_info}")
    else:
        print_status("warn", "torch", "未安装（Qwen3-TTS 需要）")
        print_install_instruction("torch")
        if has_qwen3:
            print(f"      {Colors.YELLOW}注意：qwen-tts 依赖 torch，应已自动安装{Colors.END}")
    
    # openai-whisper (步骤1)
    ok, info = check_python_package("openai-whisper", "whisper")
    if ok:
        print_status("ok", "openai-whisper", f"{info}（语音转文字，步骤1 需要）")
    else:
        print_status("warn", "openai-whisper", "未安装（步骤1 参考片段筛选需要）")
        print_install_instruction("openai-whisper")
        missing_optional.append("openai-whisper")
    
    # demucs (步骤1)
    ok, info = check_python_package("demucs")
    if ok:
        print_status("ok", "demucs", f"{info}（人声分离，步骤1 需要）")
    else:
        print_status("warn", "demucs", "未安装（步骤1 人声分离需要）")
        print_install_instruction("demucs")
        missing_optional.append("demucs")
    
    # pdf2image (备用 PDF 后端)
    ok, info = check_python_package("pdf2image")
    if ok:
        print_status("ok", "pdf2image", f"{info}（备用 PDF 转换器）")
    else:
        print_status("warn", "pdf2image", "未安装（备用，PyMuPDF 优先）")
        missing_optional.append("pdf2image")
    
    # ========================================
    # 5. Qwen3-TTS 模型缓存
    # ========================================
    if has_qwen3:
        print_section("Qwen3-TTS 模型缓存")
        
        models = check_model_cache()
        if models:
            for name, size in models:
                print_status("ok", name, size)
        else:
            print_status("warn", "模型缓存", "未检测到已下载的模型")
            print(f"      首次运行时会自动下载模型（约 2-4 GB）")
            print(f"      下载缓存目录: ~/.cache/huggingface/hub/")
    
    # ========================================
    # 6. 字体检查
    # ========================================
    print_section("字幕字体")
    
    fonts_to_check = [
        ("PingFang SC", "macOS 默认中文字体"),
        ("Noto Sans CJK SC", "Linux 推荐中文字体"),
        ("Microsoft YaHei", "Windows 中文字体"),
    ]
    
    found_font = False
    for font_name, desc in fonts_to_check:
        if check_system_font(font_name):
            print_status("ok", font_name, desc)
            found_font = True
            break
    
    if not found_font:
        print_status("warn", "中文字体", "未检测到推荐字体，字幕可能显示异常")
        print(f"      可以在运行时通过 --font_name 参数指定可用字体")
    
    # ========================================
    # 总结
    # ========================================
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}  检查结果{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    if all_ok:
        print(f"  {Colors.GREEN}✅ 所有必需依赖已满足！{Colors.END}")
        print(f"  流水线可以正常运行。\n")
        
        if missing_optional:
            print(f"  {Colors.YELLOW}⚠️ 以下可选依赖未安装：{Colors.END}")
            for dep in missing_optional:
                print(f"     - {dep}")
            print(f"\n  这些依赖仅影响部分功能（如步骤1人声提取），")
            print(f"  如果不使用相关功能可以忽略。\n")
        
        return 0
    else:
        print(f"  {Colors.RED}❌ 存在缺失的必需依赖：{Colors.END}")
        for dep in missing_required:
            print(f"     - {dep}")
        print(f"\n  请根据上述提示安装缺失的依赖后重试。\n")
        
        if args.fix:
            print(f"  {Colors.CYAN}尝试自动安装 Python 依赖...{Colors.END}\n")
            pip_packages = [
                p for p in missing_required 
                if p not in ["FFmpeg", "ffprobe", "TTS引擎(qwen-tts 或 edge-tts)"]
            ]
            if "TTS引擎(qwen-tts 或 edge-tts)" in missing_required:
                pip_packages.append("qwen-tts")  # 推荐安装 Qwen3-TTS
            
            for pkg in pip_packages:
                install_cmd = INSTALL_INSTRUCTIONS.get(pkg, f"pip install {pkg}")
                if isinstance(install_cmd, str):
                    print(f"  运行: {install_cmd}")
                    subprocess.run(install_cmd.split())
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
