#!/usr/bin/env python3
"""
滤镜脚本：复古、黑白、暖色、冷色、胶片、鲜艳
依赖：Pillow (PIL), numpy
用法：
  python filter.py --input input.jpg --output output.jpg --filter vintage
  python filter.py --input input.jpg --output output.jpg --filter grayscale
"""

import argparse
import sys
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

def apply_grayscale(img):
    return img.convert("L").convert("RGB")

def apply_vintage(img):
    # 降低饱和度 + 暖色偏移 + 轻微模糊
    img = ImageEnhance.Color(img).enhance(0.5)
    arr = np.array(img).astype(np.float32)
    # 加暖色（红通道增强，蓝通道减弱）
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.1, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.9, 0, 255)
    img = Image.fromarray(arr.astype(np.uint8))
    # 加一点模糊模拟胶片感
    img = img.filter(ImageFilter.SMOOTH_MORE)
    return img

def apply_warm(img):
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.2)
    arr = np.array(img).astype(np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.08, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.95, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

def apply_cool(img):
    arr = np.array(img).astype(np.float32)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 0.95, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.08, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))

def apply_film(img):
    # 胶片感：轻微降饱和 + 加对比 + 颗粒感
    img = ImageEnhance.Color(img).enhance(0.85)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    # 简单颗粒感：加少量随机噪声
    arr = np.array(img).astype(np.int16)
    noise = np.random.normal(0, 8, arr.shape).astype(np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def apply_vivid(img):
    img = ImageEnhance.Color(img).enhance(1.4)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    return img

FILTERS = {
    "grayscale": apply_grayscale,
    "vintage": apply_vintage,
    "warm": apply_warm,
    "cool": apply_cool,
    "film": apply_film,
    "vivid": apply_vivid,
}

def apply_filter(input_path, output_path, filter_name):
    try:
        img = Image.open(input_path).convert("RGB")
    except Exception as e:
        print(f"[错误] 无法打开图片: {e}", file=sys.stderr)
        sys.exit(1)

    if filter_name not in FILTERS:
        print(f"[错误] 未知滤镜: {filter_name}", file=sys.stderr)
        print(f"        可用滤镜: {', '.join(FILTERS.keys())}", file=sys.stderr)
        sys.exit(1)

    img = FILTERS[filter_name](img)
    img.save(output_path, quality=95)
    print(f"[完成] 已应用滤镜「{filter_name}」，保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="图片滤镜：复古/黑白/暖色/冷色/胶片/鲜艳")
    parser.add_argument("--input", required=True, help="输入图片路径")
    parser.add_argument("--output", required=True, help="输出图片路径")
    parser.add_argument("--filter", required=True,
                        choices=list(FILTERS.keys()),
                        help="滤镜名称")
    args = parser.parse_args()

    apply_filter(args.input, args.output, args.filter)

if __name__ == "__main__":
    main()
