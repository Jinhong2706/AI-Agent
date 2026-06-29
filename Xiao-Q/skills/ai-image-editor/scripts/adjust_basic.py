#!/usr/bin/env python3
"""
基础调色脚本：亮度、对比度、饱和度调整
依赖：Pillow (PIL)
用法：
  python adjust_basic.py --input input.jpg --output output.jpg --brightness 30 --contrast 20 --saturation 10
"""

import argparse
import sys
from PIL import Image, ImageEnhance

def adjust_image(input_path, output_path, brightness=0, contrast=0, saturation=0):
    try:
        img = Image.open(input_path).convert("RGB")
    except Exception as e:
        print(f"[错误] 无法打开图片: {e}", file=sys.stderr)
        sys.exit(1)

    # 亮度：范围 0.0~2.0，0 表示不变（factor=1.0）
    if brightness != 0:
        factor = 1.0 + brightness / 100.0
        factor = max(0.0, min(2.0, factor))
        img = ImageEnhance.Brightness(img).enhance(factor)
        print(f"[亮度] 调整因子: {factor:.2f}")

    # 对比度
    if contrast != 0:
        factor = 1.0 + contrast / 100.0
        factor = max(0.0, min(2.0, factor))
        img = ImageEnhance.Contrast(img).enhance(factor)
        print(f"[对比度] 调整因子: {factor:.2f}")

    # 饱和度
    if saturation != 0:
        factor = 1.0 + saturation / 100.0
        factor = max(0.0, min(2.0, factor))
        img = ImageEnhance.Color(img).enhance(factor)
        print(f"[饱和度] 调整因子: {factor:.2f}")

    img.save(output_path, quality=95)
    print(f"[完成] 已保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="基础调色：亮度/对比度/饱和度")
    parser.add_argument("--input", required=True, help="输入图片路径")
    parser.add_argument("--output", required=True, help="输出图片路径")
    parser.add_argument("--brightness", type=int, default=0, help="亮度调整 -100~100，默认0")
    parser.add_argument("--contrast", type=int, default=0, help="对比度调整 -100~100，默认0")
    parser.add_argument("--saturation", type=int, default=0, help="饱和度调整 -100~100，默认0")
    args = parser.parse_args()

    adjust_image(args.input, args.output, args.brightness, args.contrast, args.saturation)

if __name__ == "__main__":
    main()
