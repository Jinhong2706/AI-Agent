#!/usr/bin/env python3
"""
第4步：根据音频时间数据从 PDF 幻灯片生成视频。

功能说明：
1. 将 PDF 幻灯片转换为图片（每页一张）
2. 根据时间数据为每页创建视频片段
3. 拼接所有页面视频为完整演示视频

使用方法：
    python step4_generate_video.py \
        --pdf <幻灯片.pdf> \
        --timing_json <时间数据.json> \
        --output_dir <输出目录> \
        --resolution 1920x1080

依赖：
    - FFmpeg（系统工具）
    - pdf2image / Poppler（PDF 转图片）
      或 PyMuPDF (fitz) 作为备选
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


def pdf_to_images_pymupdf(pdf_path: str, output_dir: str, 
                           dpi: int = 200) -> list:
    """Convert PDF to images using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("[ERROR] PyMuPDF not installed. Install: pip install PyMuPDF", file=sys.stderr)
        return []

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Use high DPI for crisp slides
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        img_path = os.path.join(output_dir, f"slide_{page_num + 1:03d}.png")
        pix.save(img_path)
        image_paths.append(img_path)
        print(f"  Converted page {page_num + 1}/{len(doc)}: {img_path}")

    doc.close()
    return image_paths


def pdf_to_images_pdf2image(pdf_path: str, output_dir: str, 
                             dpi: int = 200) -> list:
    """Convert PDF to images using pdf2image (requires poppler)."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        return []

    images = convert_from_path(pdf_path, dpi=dpi)
    image_paths = []

    for idx, image in enumerate(images):
        img_path = os.path.join(output_dir, f"slide_{idx + 1:03d}.png")
        image.save(img_path, "PNG")
        image_paths.append(img_path)
        print(f"  Converted page {idx + 1}/{len(images)}: {img_path}")

    return image_paths


def pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 500) -> list:
    """Convert PDF to high-quality images. Tries multiple backends."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"[Step 4] Converting PDF to images: {pdf_path}")

    # Try PyMuPDF first (faster, no system deps)
    images = pdf_to_images_pymupdf(pdf_path, output_dir, dpi)
    if images:
        return images

    # Try pdf2image (requires poppler)
    images = pdf_to_images_pdf2image(pdf_path, output_dir, dpi)
    if images:
        return images

    print("[ERROR] No PDF conversion backend available.", file=sys.stderr)
    print("  Install one of: pip install PyMuPDF  OR  pip install pdf2image", file=sys.stderr)
    sys.exit(1)


def create_slide_video(image_path: str, duration: float, output_path: str,
                        resolution: str = "1920x1080", fps: int = 30):
    """
    Create a video segment from a single slide image.
    The slide is displayed for the specified duration.
    """
    width, height = resolution.split("x")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-t", str(duration),
        "-vf", (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
        ),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-preset", "medium",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Video creation failed: {result.stderr}", file=sys.stderr)
        return False
    return True


def concatenate_videos(video_files: list, output_path: str):
    """Concatenate video segments using FFmpeg."""
    list_path = output_path + ".filelist.txt"
    with open(list_path, "w") as f:
        for vf in video_files:
            # 使用绝对路径避免 FFmpeg concat 路径解析问题
            abs_path = os.path.abspath(vf)
            f.write(f"file '{abs_path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Video concatenation failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    os.remove(list_path)


def main():
    parser = argparse.ArgumentParser(description="Generate video from PDF slides")
    parser.add_argument("--pdf", required=True, help="Path to PDF slides")
    parser.add_argument("--timing_json", required=True, help="Timing data JSON from step 3")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--resolution", default="1920x1080", help="Video resolution (WxH)")
    parser.add_argument("--fps", type=int, default=30, help="Video FPS")
    parser.add_argument("--dpi", type=int, default=200, help="PDF render DPI")
    args = parser.parse_args()

    check_dependencies()

    # Load timing data
    with open(args.timing_json, "r", encoding="utf-8") as f:
        timing_data = json.load(f)

    slides_timing = timing_data["slides"]
    os.makedirs(args.output_dir, exist_ok=True)

    # Convert PDF to images
    images_dir = os.path.join(args.output_dir, "slide_images")
    slide_images = pdf_to_images(args.pdf, images_dir, dpi=args.dpi)

    if len(slide_images) < len(slides_timing):
        print(f"[WARNING] PDF has {len(slide_images)} pages but timing has {len(slides_timing)} slides.")
        print("  Using available images, repeating last slide if needed.")

    # Create video for each slide
    videos_dir = os.path.join(args.output_dir, "slide_videos")
    os.makedirs(videos_dir, exist_ok=True)
    slide_video_files = []

    for slide_info in slides_timing:
        slide_num = slide_info["slide_number"]
        duration = slide_info["duration"]

        # Map slide number to image (1-indexed)
        img_idx = min(slide_num - 1, len(slide_images) - 1)
        image_path = slide_images[img_idx]

        # Account for slide pause (add to next slide transition)
        # Add a small buffer for the pause between slides
        slide_idx = slides_timing.index(slide_info)
        if slide_idx < len(slides_timing) - 1:
            # Include the inter-slide pause in this slide's video
            next_start = slides_timing[slide_idx + 1]["start_time"]
            actual_duration = next_start - slide_info["start_time"]
        else:
            actual_duration = duration

        video_path = os.path.join(videos_dir, f"slide{slide_num}_video.mp4")
        print(f"[Step 4] Creating video for slide {slide_num}: {actual_duration:.2f}s")

        success = create_slide_video(
            image_path, actual_duration, video_path,
            resolution=args.resolution, fps=args.fps
        )
        if success:
            slide_video_files.append(video_path)

    # Concatenate all slide videos
    full_video_path = os.path.join(args.output_dir, "slides_video.mp4")
    print(f"\n[Step 4] Concatenating {len(slide_video_files)} slide videos...")
    concatenate_videos(slide_video_files, full_video_path)

    video_duration = timing_data["total_duration"]
    print(f"\n[Step 4 DONE] Video generated successfully.")
    print(f"  Output: {full_video_path}")
    print(f"  Duration: {video_duration:.2f}s")
    print(f"  Resolution: {args.resolution}")
    print(f"  Slides: {len(slide_video_files)}")

    return full_video_path


if __name__ == "__main__":
    main()
