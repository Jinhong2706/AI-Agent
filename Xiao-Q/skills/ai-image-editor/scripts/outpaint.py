#!/usr/bin/env python3
"""
AI扩图脚本：扩展画布并用邻域像素填充新区域
依赖：Pillow (PIL), numpy
用法：
  python outpaint.py --input input.jpg --output output.jpg --direction right --amount 200
  python outpaint.py --input input.jpg --output output.jpg --left 50 --right 50 --top 30 --bottom 30
扩图方向：left/right/top/bottom，amount 为扩展像素数
填充方式：边缘像素镜像 + 轻微模糊（简单版，无AI模型）
"""

import argparse
import sys
from PIL import Image, ImageFilter
import numpy as np

def outpaint(img, left=0, right=0, top=0, bottom=0):
    w, h = img.size
    new_w = w + left + right
    new_h = h + top + bottom

    if new_w <= 0 or new_h <= 0:
        print("[错误] 扩展尺寸无效", file=sys.stderr)
        sys.exit(1)

    # 创建新画布（先用边缘色填充）
    arr = np.array(img)
    edge_color = arr[0, 0]  # 左上角边缘色
    new_arr = np.tile(edge_color, (new_h, new_w, 1))

    # 放入原图
    new_arr[top:top+h, left:left+w] = arr

    result = Image.fromarray(new_arr.astype(np.uint8))

    # 用轻微模糊过渡边缘，让扩展区域更自然
    result = result.filter(ImageFilter.SMOOTH_MORE)

    print(f"[扩图] 原尺寸: {w}x{h} -> 新尺寸: {new_w}x{new_h}")
    print(f"[扩图] 左:{left} 右:{right} 上:{top} 下:{bottom}")

    return result

def outpaint_simple_ai(img, left=0, right=0, top=0, bottom=0):
    """
    简单 AI 扩图：用镜像边缘 + 随机纹理填充
    真实 AI 扩图需要 Stable Diffusion Inpainting / GLIGEN 等模型
    此处为轻量占位实现
    """
    w, h = img.size
    new_w = w + left + right
    new_h = h + top + bottom

    arr = np.array(img).astype(np.float32)

    # 构建新画布
    new_arr = np.zeros((new_h, new_w, 3), dtype=np.float32)

    # 填充原图区域
    new_arr[top:top+h, left:left+w] = arr

    # 各方向用边缘行/列镜像填充
    if left > 0:
        edge = arr[:, 0:1, :]  # 最左列
        mirror = np.flip(edge, axis=1)
        repeat_count = (left + h - 1) // h
        tiled = np.tile(mirror, (1, repeat_count, 1))[:, :left, :]
        new_arr[top:top+h, :left, :] = tiled

    if right > 0:
        edge = arr[:, -1:, :]  # 最右列
        mirror = np.flip(edge, axis=1)
        repeat_count = (right + h - 1) // h
        tiled = np.tile(mirror, (1, repeat_count, 1))[:, :right, :]
        new_arr[top:top+h, left+w:, :] = tiled

    if top > 0:
        edge = arr[0:1, :, :]  # 最上行
        mirror = np.flip(edge, axis=0)
        repeat_count = (top + w - 1) // w
        tiled = np.tile(mirror, (repeat_count, 1, 1))[:top, :, :]
        new_arr[:top, :, :] = tiled

    if bottom > 0:
        edge = arr[-1:, :, :]  # 最下行
        mirror = np.flip(edge, axis=0)
        repeat_count = (bottom + w - 1) // w
        tiled = np.tile(mirror, (repeat_count, 1, 1))[:bottom, :, :]
        new_arr[top+h:, :, :] = tiled

    # 轻微随机噪声，模拟 AI 纹理
    noise = np.random.normal(0, 3, new_arr.shape).astype(np.float32)
    new_arr = np.clip(new_arr + noise, 0, 255)

    result = Image.fromarray(new_arr.astype(np.uint8))
    result = result.filter(ImageFilter.SMOOTH_MORE)

    print(f"[扩图-AI] 原尺寸: {w}x{h} -> 新尺寸: {new_h}x{new_w}")
    print("[提示] 此为轻量实现；真实 AI 扩图建议接入 Stable Diffusion Inpainting")

    return result

def main():
    parser = argparse.ArgumentParser(description="AI扩图：扩展画布并填充")
    parser.add_argument("--input", required=True, help="输入图片路径")
    parser.add_argument("--output", required=True, help="输出图片路径")
    parser.add_argument("--direction", choices=["left", "right", "top", "bottom"],
                        default=None, help="扩图方向（与 --amount 配合使用）")
    parser.add_argument("--amount", type=int, default=100,
                        help="扩展像素数（配合 --direction 使用）")
    parser.add_argument("--left", type=int, default=0, help="左扩展像素")
    parser.add_argument("--right", type=int, default=0, help="右扩展像素")
    parser.add_argument("--top", type=int, default=0, help="上扩展像素")
    parser.add_argument("--bottom", type=int, default=0, help="下扩展像素")
    parser.add_argument("--ai", action="store_true",
                        help="使用简单 AI 扩图（镜像+噪声填充）")
    args = parser.parse_args()

    try:
        img = Image.open(args.input).convert("RGB")
    except Exception as e:
        print(f"[错误] 无法打开图片: {e}", file=sys.stderr)
        sys.exit(1)

    # 解析方向参数
    left = args.left
    right = args.right
    top = args.top
    bottom = args.bottom
    if args.direction:
        if args.direction == "left":
            left = args.amount
        elif args.direction == "right":
            right = args.amount
        elif args.direction == "top":
            top = args.amount
        elif args.direction == "bottom":
            bottom = args.amount

    if args.ai:
        result = outpaint_simple_ai(img, left, right, top, bottom)
    else:
        result = outpaint(img, left, right, top, bottom)

    result.save(args.output, quality=95)
    print(f"[完成] 已保存到: {args.output}")

if __name__ == "__main__":
    main()
