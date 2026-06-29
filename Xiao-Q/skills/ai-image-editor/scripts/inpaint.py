#!/usr/bin/env python3
"""
去水印/去物体脚本（简单版：用邻域修复）
依赖：Pillow (PIL), numpy
用法：
  python inpaint.py --input input.jpg --output output.jpg --mask mask.png
  python inpaint.py --input input.jpg --output output.jpg --box 100 50 300 200

mask.png：白色区域为待修复区域，黑色为背景
--box：直接指定矩形区域 x y w h
"""

import argparse
import sys
from PIL import Image, ImageFilter
import numpy as np

def create_mask_from_box(img_size, box):
    """根据 box(x, y, w, h) 创建二值 mask"""
    mask = np.zeros(img_size[::-1], dtype=np.uint8)  # H x W
    x, y, w, h = box
    mask[y:y+h, x:x+w] = 255
    return mask

def simple_inpaint(img, mask):
    """
    简单修复：用周围像素的中值模糊替代选中区域
    适合小面积水印/物体去除
    """
    img_arr = np.array(img).astype(np.uint8)
    mask_arr = np.array(mask)  # H x W

    # 膨胀 mask，让修复更自然
    mask_img = Image.fromarray(mask_arr)
    mask_img = mask_img.filter(ImageFilter.MaxFilter(5))
    mask_arr = np.array(mask_img)

    # 用中值模糊处理整个图像，再替换 mask 区域
    img_obj = Image.fromarray(img_arr)
    blurred = img_obj.filter(ImageFilter.MedianFilter(size=5))
    blurred_arr = np.array(blurred)

    # 将 mask 区域替换为模糊后的像素
    result = img_arr.copy()
    result[mask_arr > 127] = blurred_arr[mask_arr > 127]

    return Image.fromarray(result)

def inpaint_image(input_path, output_path, mask_path=None, box=None):
    try:
        img = Image.open(input_path).convert("RGB")
    except Exception as e:
        print(f"[错误] 无法打开图片: {e}", file=sys.stderr)
        sys.exit(1)

    if mask_path:
        try:
            mask = Image.open(mask_path).convert("L")
            mask = mask.resize(img.size)
        except Exception as e:
            print(f"[错误] 无法打开 mask: {e}", file=sys.stderr)
            sys.exit(1)
    elif box:
        mask = create_mask_from_box(img.size, box)
        mask = Image.fromarray(mask)
    else:
        print("[错误] 必须提供 --mask 或 --box 参数", file=sys.stderr)
        sys.exit(1)

    result = simple_inpaint(img, mask)
    result.save(output_path, quality=95)
    print(f"[完成] 已去水印/去物体，保存到: {output_path}")
    print("[提示] 简单修复适用于小面积水印；大面积物体建议用 OpenCV inpaint 或 AI 模型")

def main():
    parser = argparse.ArgumentParser(description="去水印/去物体（简单版）")
    parser.add_argument("--input", required=True, help="输入图片路径")
    parser.add_argument("--output", required=True, help="输出图片路径")
    parser.add_argument("--mask", default=None, help="mask 图片路径（白色=待修复区域）")
    parser.add_argument("--box", type=int, nargs=4, default=None,
                        metavar=("X", "Y", "W", "H"),
                        help="直接指定矩形区域: x y width height")
    args = parser.parse_args()

    if not args.mask and not args.box:
        print("[错误] 请至少提供 --mask 或 --box", file=sys.stderr)
        sys.exit(1)

    inpaint_image(args.input, args.output, args.mask, args.box)

if __name__ == "__main__":
    main()
