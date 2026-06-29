#!/usr/bin/env python3
"""
图片变换脚本：裁剪、旋转、翻转
依赖：Pillow (PIL)
用法：
  python transform.py --input input.jpg --output output.jpg --rotate 90
  python transform.py --input input.jpg --output output.jpg --crop 100 50 400 300
  python transform.py --input input.jpg --output output.jpg --flip horizontal
"""

import argparse
import sys
from PIL import Image

def transform_image(input_path, output_path, rotate=0, crop=None, flip=None):
    try:
        img = Image.open(input_path).convert("RGB")
    except Exception as e:
        print(f"[错误] 无法打开图片: {e}", file=sys.stderr)
        sys.exit(1)

    # 旋转
    if rotate != 0:
        img = img.rotate(-rotate, expand=True)  # PIL 顺时针为正，用户输入也是顺时针
        print(f"[旋转] {rotate}°")

    # 裁剪
    if crop:
        x, y, w, h = crop
        # 确保不越界
        img_w, img_h = img.size
        left = max(0, x)
        top = max(0, y)
        right = min(img_w, x + w)
        bottom = min(img_h, y + h)
        if right <= left or bottom <= top:
            print("[警告] 裁剪区域无效，跳过裁剪", file=sys.stderr)
        else:
            img = img.crop((left, top, right, bottom))
            print(f"[裁剪] 区域: ({left},{top}) -> ({right},{bottom})")

    # 翻转
    if flip:
        if flip == "horizontal":
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            print("[翻转] 水平翻转")
        elif flip == "vertical":
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            print("[翻转] 垂直翻转")

    img.save(output_path, quality=95)
    print(f"[完成] 已保存到: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="图片变换：裁剪/旋转/翻转")
    parser.add_argument("--input", required=True, help="输入图片路径")
    parser.add_argument("--output", required=True, help="输出图片路径")
    parser.add_argument("--rotate", type=float, default=0, help="旋转角度（顺时针，度）")
    parser.add_argument("--crop", type=int, nargs=4, default=None,
                        metavar=("X", "Y", "W", "H"),
                        help="裁剪区域: x y width height")
    parser.add_argument("--flip", choices=["horizontal", "vertical"], default=None,
                        help="翻转方向: horizontal 或 vertical")
    args = parser.parse_args()

    transform_image(args.input, args.output, args.rotate, args.crop, args.flip)

if __name__ == "__main__":
    main()
