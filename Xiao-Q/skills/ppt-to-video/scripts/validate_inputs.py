#!/usr/bin/env python3
"""
输入文件验证脚本：检查用户提供的输入文件是否符合要求。

用于流水线执行前的输入校验，提供友好的错误提示和修复建议。

使用方法：
    python validate_inputs.py --speech_md <演讲稿.md> --slides_pdf <幻灯片.pdf>
    
可选参数：
    --reference_voice <参考音频>  验证参考音频格式
    --strict                      严格模式，警告也视为错误
"""

import argparse
import json
import os
import re
import subprocess
import sys


# ============================================================
# 颜色输出
# ============================================================

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_ok(message: str):
    print(f"  {Colors.GREEN}✅{Colors.END} {message}")


def print_warn(message: str):
    print(f"  {Colors.YELLOW}⚠️{Colors.END} {message}")


def print_error(message: str):
    print(f"  {Colors.RED}❌{Colors.END} {message}")


def print_tip(message: str):
    print(f"      {Colors.CYAN}💡 {message}{Colors.END}")


# ============================================================
# 验证函数
# ============================================================

def validate_file_exists(path: str, name: str) -> bool:
    """验证文件是否存在"""
    if not path:
        print_error(f"{name}：未提供文件路径")
        return False
    
    if not os.path.isfile(path):
        print_error(f"{name}：文件不存在 — {path}")
        print_tip("请检查文件路径是否正确")
        return False
    
    return True


def validate_pdf(pdf_path: str) -> tuple:
    """
    验证 PDF 文件。
    返回: (is_valid, page_count, warnings)
    """
    warnings = []
    
    if not validate_file_exists(pdf_path, "PDF 幻灯片"):
        return False, 0, ["文件不存在"]
    
    # 检查文件扩展名
    if not pdf_path.lower().endswith(".pdf"):
        print_warn(f"文件扩展名不是 .pdf，可能不是有效的 PDF 文件")
        warnings.append("扩展名不正确")
    
    # 检查文件大小
    file_size = os.path.getsize(pdf_path) / 1024 / 1024  # MB
    if file_size < 0.001:
        print_error(f"PDF 文件太小（{file_size:.3f} MB），可能是空文件")
        return False, 0, ["文件太小"]
    
    if file_size > 100:
        print_warn(f"PDF 文件较大（{file_size:.1f} MB），处理可能较慢")
        warnings.append("文件较大")
    
    # 尝试获取页数
    page_count = 0
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        
        if page_count == 0:
            print_error("PDF 文件没有任何页面")
            return False, 0, ["无页面"]
        
        print_ok(f"PDF 有效：{page_count} 页，{file_size:.1f} MB")
        
    except ImportError:
        print_warn("PyMuPDF 未安装，无法验证 PDF 内容")
        print_tip("安装：pip install PyMuPDF")
        warnings.append("无法验证页数")
    except Exception as e:
        print_error(f"无法打开 PDF 文件：{e}")
        return False, 0, [str(e)]
    
    return True, page_count, warnings


def validate_speech_md(md_path: str, expected_pages: int = 0) -> tuple:
    """
    验证演讲稿 Markdown 文件格式。
    返回: (is_valid, detected_pages, warnings, suggestions)
    """
    warnings = []
    suggestions = []
    
    if not validate_file_exists(md_path, "演讲稿"):
        return False, 0, warnings, suggestions
    
    # 读取内容
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print_error(f"无法读取文件：{e}")
        return False, 0, [str(e)], suggestions
    
    if not content.strip():
        print_error("演讲稿文件为空")
        return False, 0, ["文件为空"], suggestions
    
    # 检测页码标题格式
    # 标准格式: ## 第 X 页 标题
    standard_pattern = r'##\s*第\s*(\d+)\s*页'
    standard_matches = re.findall(standard_pattern, content)
    
    # 其他可能的格式
    alt_patterns = [
        (r'##+\s*Page\s*(\d+)', "英文 Page X 格式"),
        (r'##+\s*Slide\s*(\d+)', "英文 Slide X 格式"),
        (r'##+\s*(\d+)[\.、]', "数字编号格式"),
        (r'---+', "分隔线（可能用于分页）"),
    ]
    
    detected_pages = len(standard_matches)
    
    if detected_pages > 0:
        print_ok(f"演讲稿格式正确：检测到 {detected_pages} 页标准格式")
        
        # 检查页码连续性
        page_nums = sorted([int(x) for x in standard_matches])
        if page_nums != list(range(1, len(page_nums) + 1)):
            print_warn(f"页码不连续：{page_nums}")
            warnings.append("页码不连续")
            suggestions.append("确保页码从 1 开始连续编号")
    else:
        # 尝试检测其他格式
        alt_found = False
        for pattern, desc in alt_patterns:
            matches = re.findall(pattern, content)
            if matches:
                print_warn(f"检测到非标准格式：{desc}")
                alt_found = True
                warnings.append(f"非标准格式: {desc}")
        
        if not alt_found:
            print_error("未检测到页面标题格式")
            print_tip("演讲稿需要使用 '## 第 X 页 标题' 格式标记每页")
        
        suggestions.append("建议使用 LLM 整理演讲稿为标准格式（参见 SKILL.md 步骤 0）")
        detected_pages = len(re.findall(r'---+', content)) + 1  # 估算
    
    # 检查与 PDF 页数是否匹配
    if expected_pages > 0 and detected_pages > 0:
        if detected_pages != expected_pages:
            print_warn(f"演讲稿页数（{detected_pages}）与 PDF 页数（{expected_pages}）不匹配")
            warnings.append("页数不匹配")
            suggestions.append("确保演讲稿每一页都有对应的 PDF 幻灯片")
        else:
            print_ok(f"页数匹配：演讲稿 {detected_pages} 页 = PDF {expected_pages} 页")
    
    # 检查内容长度
    content_length = len(content)
    if content_length < 100:
        print_warn("演讲稿内容较少，生成的视频可能很短")
        warnings.append("内容较少")
    
    # 检查特殊字符
    problematic_chars = re.findall(r'[【】「」『』〔〕｛｝]', content)
    if problematic_chars:
        print_warn(f"发现特殊括号字符，可能影响 TTS 发音")
        suggestions.append("建议将特殊括号替换为普通括号或移除")
    
    # 检查数字
    numbers = re.findall(r'\d{4,}', content)
    if numbers:
        print_warn(f"发现较长的数字（如 {numbers[0]}），TTS 可能读法不自然")
        print_tip("流水线会自动将数字转为中文读法")
    
    return True, detected_pages, warnings, suggestions


def validate_audio(audio_path: str) -> tuple:
    """
    验证参考音频文件。
    返回: (is_valid, duration_sec, warnings)
    """
    warnings = []
    
    if not validate_file_exists(audio_path, "参考音频"):
        return False, 0, ["文件不存在"]
    
    # 检查扩展名
    valid_exts = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac"}
    ext = os.path.splitext(audio_path)[1].lower()
    if ext not in valid_exts:
        print_warn(f"音频扩展名 {ext} 可能不受支持")
        warnings.append("扩展名不常见")
    
    # 使用 ffprobe 获取详细信息
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration,bit_rate:stream=sample_rate,channels",
             "-of", "json", audio_path],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            print_error(f"无法分析音频文件：{result.stderr}")
            return False, 0, ["无法分析"]
        
        info = json.loads(result.stdout)
        format_info = info.get("format", {})
        streams = info.get("streams", [{}])
        stream = streams[0] if streams else {}
        
        duration = float(format_info.get("duration", 0))
        sample_rate = int(stream.get("sample_rate", 0))
        channels = int(stream.get("channels", 0))
        
        # 检查时长
        if duration < 3:
            print_warn(f"参考音频较短（{duration:.1f}秒），声音克隆效果可能不佳")
            print_tip("建议使用 5-15 秒的清晰人声片段")
            warnings.append("时长过短")
        elif duration > 30:
            print_warn(f"参考音频较长（{duration:.1f}秒），将自动截取前 15 秒")
            warnings.append("时长较长")
        
        # 检查采样率
        if sample_rate > 0 and sample_rate < 16000:
            print_warn(f"采样率较低（{sample_rate}Hz），音质可能不佳")
            print_tip("建议使用 16kHz 以上的音频")
            warnings.append("采样率较低")
        
        print_ok(f"参考音频：{duration:.1f}秒，{sample_rate}Hz，{channels}声道")
        return True, duration, warnings
        
    except FileNotFoundError:
        print_warn("ffprobe 未找到，无法详细验证音频")
        print_tip("安装 FFmpeg 以获得完整验证")
        return True, 0, ["无法详细验证"]
    except Exception as e:
        print_error(f"验证音频时出错：{e}")
        return False, 0, [str(e)]


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="验证 PPT转视频 输入文件")
    parser.add_argument("--speech_md", required=True, help="演讲稿 Markdown 文件")
    parser.add_argument("--slides_pdf", required=True, help="PDF 幻灯片文件")
    parser.add_argument("--reference_voice", default="", help="参考音频（可选）")
    parser.add_argument("--strict", action="store_true", help="严格模式（警告也视为错误）")
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}PPT转视频流水线 — 输入文件验证{Colors.END}\n")
    
    all_valid = True
    all_warnings = []
    all_suggestions = []
    
    # 1. 验证 PDF
    print(f"{Colors.BOLD}1. PDF 幻灯片{Colors.END}")
    pdf_valid, pdf_pages, pdf_warnings = validate_pdf(args.slides_pdf)
    all_valid = all_valid and pdf_valid
    all_warnings.extend(pdf_warnings)
    
    # 2. 验证演讲稿
    print(f"\n{Colors.BOLD}2. 演讲稿{Colors.END}")
    md_valid, md_pages, md_warnings, md_suggestions = validate_speech_md(
        args.speech_md, pdf_pages
    )
    all_valid = all_valid and md_valid
    all_warnings.extend(md_warnings)
    all_suggestions.extend(md_suggestions)
    
    # 3. 验证参考音频（如果提供）
    if args.reference_voice:
        print(f"\n{Colors.BOLD}3. 参考音频{Colors.END}")
        audio_valid, duration, audio_warnings = validate_audio(args.reference_voice)
        all_valid = all_valid and audio_valid
        all_warnings.extend(audio_warnings)
    
    # 总结
    print(f"\n{Colors.BOLD}{'='*50}{Colors.END}")
    print(f"{Colors.BOLD}  验证结果{Colors.END}")
    print(f"{Colors.BOLD}{'='*50}{Colors.END}\n")
    
    if all_valid and not all_warnings:
        print(f"  {Colors.GREEN}✅ 所有输入文件验证通过！{Colors.END}")
        print(f"  可以运行流水线了。\n")
        return 0
    elif all_valid and all_warnings:
        print(f"  {Colors.YELLOW}⚠️ 文件基本有效，但存在以下警告：{Colors.END}")
        for w in all_warnings:
            print(f"     - {w}")
        
        if all_suggestions:
            print(f"\n  {Colors.CYAN}💡 建议：{Colors.END}")
            for s in all_suggestions:
                print(f"     - {s}")
        
        if args.strict:
            print(f"\n  {Colors.RED}严格模式：警告视为错误{Colors.END}\n")
            return 1
        
        print(f"\n  流水线可以运行，但可能影响输出质量。\n")
        return 0
    else:
        print(f"  {Colors.RED}❌ 验证失败，请修复上述错误后重试。{Colors.END}\n")
        
        if all_suggestions:
            print(f"  {Colors.CYAN}💡 建议：{Colors.END}")
            for s in all_suggestions:
                print(f"     - {s}")
            print()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
