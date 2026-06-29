#!/usr/bin/env python3
"""
换背景脚本：扣除主体 + 替换背景
依赖：Pillow (PIL), numpy, rembg(可选)
用法：
  python change_bg.py --input input.jpg --output output.jpg --bg-color white
  python change_bg.py --input input.jpg --output output.jpg --bg-color "#00FF00"
  python change_bg.py --input input.jpg --output output.jpg --bg-image bg.jpg
"""

import argparse
import sys
from PIL import Image
import numpy as np

def remove_bg_simple(img):
    """
    简单抠图：用白色/接近白色背景作为透明区域
    适合背景较纯色的图片，复杂背景建议用 rembg
    """
    arr = np.array(img).astype(np.float32)
    # 计算接近白色的程度
    white_dist = np.sqrt(np.sum((arr - 255) ** 2, axis=2))
    # 距离 < 50 视为背景
    alpha = np.where(white_dist < 50, 0, 255).astype(np.uint8)
    result = img.convert("RGBA")
    result.putalpha(Image.fromarray(alpha))
    return result

def remove_bg_rembg(img):
    """用 rembg 做智能抠图（如已安装）"""
    try:
        from rembg import remove
        return remove(img)
    except ImportError:
        print("[警告] rembg 未安装，使用简单抠图模式", file=sys.stderr)
        return remove_bg_simple(img)

def change_background(input_path, output_path, bg_color=None, bg_image_path=None):
    try:
        img = Image.open(input_path).convert("RGB")
    except Exception as e:
        print(f"[错误] 无法打开图片: {e}", file=sys.stderr)
        sys.exit(1)

    # 尝试用 rembg，失败则回退简单模式
    try:
        from rembg import remove
        fg = remove(img)
        print("[抠图] 使用 rembg 智能抠图")
    except ImportError:
        fg = remove_bg_simple(img)
        print("[抠图] 使用简单模式（纯色背景效果更佳）")
        print("[提示] 安装 rembg 可获得更好效果: pip install rembg")

    # 准备背景
    if bg_image_path:
        try:
            bg = Image.open(bg_image_path).convert("RGB")
            bg = bg.resize(fg.size)
            print(f"[背景] 使用图片背景: {bg_image_path}")
        except Exception as e:
            print(f"[错误] 无法打开背景图片: {e}", file=sys.stderr)
            sys.exit(1)
    elif bg_color:
        color = bg_color.strip()
        # 解析颜色
        if color.startswith("#") and len(color) == 7:
            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        elif color.lower() == "white":
            rgb = (255, 255, 255)
        elif color.lower() == "black":
            rgb = (0, 0, 0)
        elif color.lower() == "red":
            rgb = (255, 0, 0)
        elif color.lower() == "blue":
            rgb = (0, 0, 255)
        elif color.lower() == "green":
            rgb = (0, 255, 0)
        else:
            rgb = (255, 255, 255)
        bg = Image.new("RGB", fg.size, rgb)
        print(f"[背景] 使用纯色背景: {color}")
    else:
        bg = Image.new("RGB", fg.size, (255, 255, 255))
        print("[背景] 默认使用白色背景")

    # 合成
    bg.paste(fg, (0, 0), fg if fg.mode == "RGBA" else None)
    bg.save(output_path, quality=95)
    print(f"[完成] 已换背景，保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="换背景：抠图 + 替换背景")
    parser.add_argument("--input", required=True, help="输入图片路径")
    parser.add_argument("--output", required=True, help="输出图片路径")
    parser.add_argument("--bg-color", default=None,
                        help="背景颜色: white/black/red/blue/green 或 #RRGGBB")
    parser.add_argument("--bg-image", default=None,
                        help="背景图片路径（优先于 --bg-color）")
    args = parser.parse_args()

    change_background(args.input, args.output, args.bg_color, args.bg_image)

if __name__ == "__main__":
    main()
