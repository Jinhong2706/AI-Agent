#!/usr/bin/env python3
"""
视频封面图生成脚本
根据用户上传的图片，生成适配各大视频平台的封面图。

核心策略：
- 若原图比例与目标比例相差较小（≤10%），直接等比缩放裁剪（无需扩图）。
- 若比例差异较大，使用 OpenAI gpt-image-2 进行 AI 扩图（outpainting），
  将原图完整嵌入目标画布，对留白区域进行 AI 内容补全，保证主体完整。

用法：
    python generate_covers.py <input_image> [output_dir] [--platforms p1 p2 ...]
                              [--text "封面文案"] [--style "装饰风格描述"]

平台 key 列表：
    wechat_profile_card          微信视频号个人主页卡片（横版/竖版通用）810x1080  (3:4)
    wechat_share_card_horizontal 微信视频号分享卡片（横版专用）          1440x1080 (4:3)
    douyin_vertical              抖音竖版        810x1080  (3:4)
    douyin_horizontal            抖音横版        1440x1080 (4:3)
    kuaishou_vertical            快手竖版        1080x1920 (9:16)
    kuaishou_horizontal          快手横版        1920x1080 (16:9)
    bilibili                     B站首页推荐封面  1280x960  (4:3)
    bilibili_profile             B站个人主页封面  1920x1080 (16:9)
    xiaohongshu_vertical         小红书竖版      1080x1440 (3:4)
    xiaohongshu_horizontal       小红书横版      1440x1080 (4:3)

微信视频号说明：
    - 横版：同时生成 wechat_profile_card（3:4）和 wechat_share_card_horizontal（4:3）
    - 竖版：只需生成 wechat_profile_card（3:4），同时用于个人主页和分享卡片
"""

import sys
import os
import argparse
import base64
import io
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps

# 各平台封面规格
PLATFORM_SPECS = {
    "wechat_profile_card":          {"name": "微信视频号个人主页卡片",       "width": 810,  "height": 1080},
    "wechat_share_card_horizontal": {"name": "微信视频号分享卡片（横版）",    "width": 1440, "height": 1080},
    "douyin_vertical":              {"name": "抖音竖版",                    "width": 810,  "height": 1080},
    "douyin_horizontal":            {"name": "抖音横版",                    "width": 1440, "height": 1080},
    "kuaishou_vertical":            {"name": "快手竖版",                    "width": 1080, "height": 1920},
    "kuaishou_horizontal":          {"name": "快手横版",                    "width": 1920, "height": 1080},
    "bilibili":                     {"name": "B站首页推荐封面",              "width": 1280, "height": 960},
    "bilibili_profile":             {"name": "B站个人主页封面",              "width": 1920, "height": 1080},
    "xiaohongshu_vertical":         {"name": "小红书竖版",                  "width": 1080, "height": 1440},
    "xiaohongshu_horizontal":       {"name": "小红书横版",                  "width": 1440, "height": 1080},
}

ALL_PLATFORMS = list(PLATFORM_SPECS.keys())

# OpenAI images.edit 支持的尺寸（取最接近的）
OPENAI_SIZES = [
    (1024, 1024),
    (1536, 1024),
    (1024, 1536),
]

# 比例差异阈值：超过此值才使用 AI 扩图（否则直接裁剪）
RATIO_DIFF_THRESHOLD = 0.15


def get_openai_size(target_w: int, target_h: int) -> str:
    """选择最接近目标比例的 OpenAI 支持尺寸。"""
    target_ratio = target_w / target_h
    best = min(OPENAI_SIZES, key=lambda s: abs(s[0] / s[1] - target_ratio))
    return f"{best[0]}x{best[1]}", best[0], best[1]


def smart_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """等比缩放后居中裁剪，适用于比例相近的情况。"""
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        new_h = target_h
        new_w = int(new_h * src_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / src_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def build_outpaint_canvas(img: Image.Image, target_w: int, target_h: int):
    """
    构建 outpainting 所需的画布和 mask：
    - 将原图等比缩放（contain）居中放置在目标画布上
    - mask：原图区域为黑色（保留），留白区域为白色（待 AI 填充）
    返回 (canvas_rgba, mask_rgba, paste_x, paste_y, fg_w, fg_h)
    """
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        fg_w = target_w
        fg_h = int(fg_w / src_ratio)
    else:
        fg_h = target_h
        fg_w = int(fg_h * src_ratio)

    fg = img.copy().convert("RGBA")
    fg = fg.resize((fg_w, fg_h), Image.LANCZOS)

    paste_x = (target_w - fg_w) // 2
    paste_y = (target_h - fg_h) // 2

    # 画布：透明背景（OpenAI 要求 mask 区域透明表示"待填充"）
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    canvas.paste(fg, (paste_x, paste_y), fg)

    return canvas, paste_x, paste_y, fg_w, fg_h


def ai_outpaint(
    img: Image.Image,
    target_w: int,
    target_h: int,
    platform_name: str,
    extra_prompt: str = "",
) -> Image.Image:
    """
    使用 OpenAI gpt-image-2 对图片进行 AI 扩图（outpainting）。
    原图完整保留居中，留白区域由 AI 自然补全。
    """
    from openai import OpenAI
    client = OpenAI()

    # 构建画布（原图居中，留白透明）
    canvas, paste_x, paste_y, fg_w, fg_h = build_outpaint_canvas(img, target_w, target_h)

    # 选择最接近的 OpenAI 支持尺寸
    size_str, api_w, api_h = get_openai_size(target_w, target_h)

    # 如果目标尺寸与 API 尺寸不同，先缩放画布到 API 尺寸
    if (api_w, api_h) != (target_w, target_h):
        canvas_for_api = canvas.resize((api_w, api_h), Image.LANCZOS)
    else:
        canvas_for_api = canvas

    # 将画布转为 PNG bytes（RGBA，透明区域为待填充区域）
    canvas_bytes = io.BytesIO()
    canvas_for_api.save(canvas_bytes, format="PNG")
    canvas_bytes.seek(0)

    # 构建 prompt
    base_prompt = (
        f"This is a video cover image for {platform_name}. "
        "The center area contains the original image. "
        "Seamlessly extend the background to fill the transparent areas, "
        "maintaining consistent style, lighting, color tone, and visual continuity. "
        "Do not alter the original image content in the center."
    )
    if extra_prompt:
        base_prompt += f" Additional requirements: {extra_prompt}"

    response = client.images.edit(
        model="gpt-image-2",
        image=("canvas.png", canvas_bytes, "image/png"),
        prompt=base_prompt,
        size=size_str,
        quality="medium",
    )

    # 解码结果
    img_b64 = response.data[0].b64_json
    result_bytes = base64.b64decode(img_b64)
    result_img = Image.open(io.BytesIO(result_bytes)).convert("RGB")

    # 如果 API 返回尺寸与目标不同，缩放到目标尺寸
    if result_img.size != (target_w, target_h):
        result_img = result_img.resize((target_w, target_h), Image.LANCZOS)

    return result_img


def fallback_blur_bg(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    备用方案（AI 扩图失败时）：模糊背景 + 完整前景。
    """
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    # 背景层
    bg = img.copy().convert("RGB")
    if src_ratio > tgt_ratio:
        bg_h = target_h
        bg_w = int(bg_h * src_ratio)
    else:
        bg_w = target_w
        bg_h = int(bg_w / src_ratio)
    bg = bg.resize((bg_w, bg_h), Image.LANCZOS)
    left = (bg_w - target_w) // 2
    top = (bg_h - target_h) // 2
    bg = bg.crop((left, top, left + target_w, top + target_h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
    bg = bg.point(lambda p: int(p * 0.55))

    # 前景层
    if src_ratio > tgt_ratio:
        fg_w = target_w
        fg_h = int(fg_w / src_ratio)
    else:
        fg_h = target_h
        fg_w = int(fg_h * src_ratio)
    fg = img.copy().convert("RGBA")
    fg = fg.resize((fg_w, fg_h), Image.LANCZOS)

    result = bg.convert("RGBA")
    paste_x = (target_w - fg_w) // 2
    paste_y = (target_h - fg_h) // 2
    result.paste(fg, (paste_x, paste_y), fg)
    return result.convert("RGB")


def generate_covers(
    input_path: str,
    output_dir: str,
    platforms: list,
    extra_prompt: str = "",
    use_ai: bool = True,
) -> list:
    """
    生成指定平台的封面图，返回生成的文件路径列表。

    参数：
        input_path   - 输入图片路径
        output_dir   - 输出目录
        platforms    - 平台 key 列表
        extra_prompt - 附加给 AI 的文案/装饰描述（如"添加标题文字'旅行日记'"）
        use_ai       - 是否使用 AI 扩图（默认 True，失败时自动降级为模糊背景）
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"输入图片不存在：{input_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    stem = input_path.stem
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    generated = []

    for platform_key in platforms:
        if platform_key not in PLATFORM_SPECS:
            print(f"[警告] 未知平台：{platform_key}，已跳过")
            continue
        spec = PLATFORM_SPECS[platform_key]
        w, h = spec["width"], spec["height"]
        name = spec["name"]
        tgt_ratio = w / h

        ratio_diff = abs(src_ratio - tgt_ratio) / max(src_ratio, tgt_ratio)

        if ratio_diff <= RATIO_DIFF_THRESHOLD:
            # 比例相近，直接裁剪
            result = smart_crop(img.convert("RGB"), w, h)
            method = "裁剪"
        elif use_ai:
            # 比例差异较大，使用 AI 扩图
            try:
                result = ai_outpaint(img, w, h, name, extra_prompt)
                method = "AI扩图"
            except Exception as e:
                print(f"[警告] AI 扩图失败（{e}），降级为模糊背景")
                result = fallback_blur_bg(img, w, h)
                method = "模糊背景(降级)"
        else:
            result = fallback_blur_bg(img, w, h)
            method = "模糊背景"

        out_filename = f"{stem}_{platform_key}_{w}x{h}.jpg"
        out_path = output_dir / out_filename
        result.save(str(out_path), "JPEG", quality=95, optimize=True)
        print(f"[OK] {name} ({w}x{h}) [{method}] -> {out_path}")
        generated.append(str(out_path))

    return generated


def main():
    parser = argparse.ArgumentParser(description="视频封面图生成工具")
    parser.add_argument("input", help="输入图片路径")
    parser.add_argument("output_dir", nargs="?", default=None,
                        help="输出目录（默认为输入图片所在目录下的 covers/ 子目录）")
    parser.add_argument("--platforms", nargs="+", default=ALL_PLATFORMS,
                        choices=ALL_PLATFORMS + ["all"],
                        help="要生成的平台列表，默认全部平台")
    parser.add_argument("--text", default="",
                        help="封面文案（传递给 AI 扩图的附加 prompt，如'添加标题文字\"旅行日记\"'）")
    parser.add_argument("--style", default="",
                        help="装饰风格描述（传递给 AI 扩图，如'添加简约几何边框装饰'）")
    parser.add_argument("--no-ai", action="store_true",
                        help="禁用 AI 扩图，改用模糊背景填充")
    args = parser.parse_args()

    platforms = ALL_PLATFORMS if "all" in args.platforms else args.platforms

    if args.output_dir is None:
        output_dir = str(Path(args.input).parent / "covers")
    else:
        output_dir = args.output_dir

    extra_prompt_parts = []
    if args.text:
        extra_prompt_parts.append(args.text)
    if args.style:
        extra_prompt_parts.append(args.style)
    extra_prompt = ". ".join(extra_prompt_parts)

    print(f"输入图片：{args.input}")
    print(f"输出目录：{output_dir}")
    print(f"目标平台：{', '.join(platforms)}")
    if extra_prompt:
        print(f"附加描述：{extra_prompt}")
    print(f"AI 扩图：{'禁用' if args.no_ai else '启用'}")
    print("-" * 60)

    generated = generate_covers(
        args.input,
        output_dir,
        platforms,
        extra_prompt=extra_prompt,
        use_ai=not args.no_ai,
    )
    print("-" * 60)
    print(f"共生成 {len(generated)} 张封面图，保存至：{output_dir}")


if __name__ == "__main__":
    main()
