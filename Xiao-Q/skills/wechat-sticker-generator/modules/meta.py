import os
import json
from PIL import Image

from modules.config import load_config, get_api_key
from modules.constants import STYLE_MAPPING
from modules.api import remote_draw_trigger
from modules.prompts import (
    build_meta_text_prompt,
    build_banner_prompt,
    build_cover_prompt,
)


def generate_text(prompt, api_key, provider, text_model):
    if provider == "qwen":
        import dashscope

        dashscope.api_key = api_key
        response = dashscope.Generation.call(
            model=text_model, prompt=prompt, result_format="message"
        )
        content = response.output.choices[0].message.content.strip()
        for prefix in ("```json", "```"):
            if content.startswith(prefix):
                content = content[len(prefix) :]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())
    else:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            print("[!] 请安装 google-genai: pip install google-genai")
            return {}
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=text_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)


def generate_meta(target_dir, provider=None, skill_dir=None):
    print(f"\n========================================")
    print(f"🎬 生成微信补充物料: {target_dir}")
    print(f"========================================")

    params_path = os.path.join(target_dir, "params.json")
    if not os.path.exists(params_path):
        print(f"[!] 找不到 {params_path}，跳过该目录。")
        return False

    with open(params_path, "r", encoding="utf-8") as f:
        params = json.load(f)

    config = load_config()
    if not provider:
        provider = config.get("default_provider", "gemini")

    api_key, provider = get_api_key(provider)
    if not api_key:
        print("[!] 找不到 API Key，无法生成文本/图片。")
        return False

    provider_cfg = config.get("providers", {}).get(provider, {})
    text_model = provider_cfg.get("text_model", "gemini-2.5-flash")
    print(f"[*] 文本模型: {provider}/{text_model}")

    set_name = params.get("set_name", "未命名合集")
    char_name = params.get("character_name", "")
    scene_theme = params.get("scene_theme", "")
    character_prompt = params.get("character_prompt", "")
    expressions = params.get("expressions", [])
    style_preset = params.get("style_preset", "MEME_STYLE")
    ref_img = params.get("reference_image", "")

    if ref_img and not os.path.isabs(ref_img):
        local_ref = os.path.join(target_dir, os.path.basename(ref_img))
        if os.path.exists(local_ref):
            ref_img = os.path.abspath(local_ref)
        elif skill_dir:
            ref_img = os.path.abspath(os.path.join(skill_dir, ref_img))

    if ref_img and not os.path.exists(ref_img):
        print(f"[*] 警告: 找不到参考图 {ref_img}")
        ref_img = None

    print("\n[*] 正在召唤 AI 编写合集故事与表情含义...")

    text_prompt = build_meta_text_prompt(
        set_name, char_name, scene_theme, character_prompt, expressions
    )

    try:
        text_result = generate_text(text_prompt, api_key, provider, text_model)

        description = text_result.get(
            "description", params.get("set_description", "微信表情包")
        )[:80]
        meanings = text_result.get("meanings", [])
        styles = text_result.get("styles", [])
        theme = text_result.get("theme", "")

        if len(meanings) < len(expressions):
            for i in range(len(meanings), len(expressions)):
                meanings.append(expressions[i].get("text", "表情")[:4])

        meanings = [str(m)[:4] for m in meanings]
        print(f"  -> 故事简介: {description}")
        print(f"  -> 提取了 {len(meanings)} 个表情含义标签。")
        print(f"  -> 表情风格: {styles}")
        print(f"  -> 表情主题: {theme}")
    except Exception as e:
        print(f"[!] AI 文本生成失败: {e}，将使用降级方案。")
        description = params.get("set_description", "微信表情包")[:80]
        meanings = [e.get("text", "表情")[:4] for e in expressions]
        styles = []
        theme = ""

    export_root = os.path.join(target_dir, "wechat_export")
    os.makedirs(export_root, exist_ok=True)

    copy_info = params.get("copyright_info", "")

    info_path = os.path.join(export_root, "upload_info.txt")
    with open(info_path, "w", encoding="utf-8") as txt:
        txt.write("【微信表情包后台上传资料库】（可直接复制粘贴到微信后台）\n")
        txt.write("=" * 50 + "\n")
        txt.write(f"表情包名称 (不超过8字): {set_name}\n")
        txt.write(f"表情包介绍 (不超过80字): {description}\n")
        txt.write(f"表情风格: {', '.join(styles) if styles else '未选择'}\n")
        txt.write(f"表情主题: {theme if theme else '未选择'}\n")
        txt.write(f"版权信息 / 艺术家: {copy_info}\n")
        txt.write("=" * 50 + "\n")
        txt.write("【表情含义 (最多4字)】\n")
        for i, m in enumerate(meanings):
            txt.write(f"第 {i + 1:02d} 个: {m}\n")
    print(f"[✓] 资料文档已生成: {info_path}")

    print("\n[*] 正在召唤 AI 绘制表情包横幅(Banner)与封面(Cover)...")

    banner_prompt = build_banner_prompt(
        set_name, char_name, character_prompt, scene_theme, description, style_preset
    )
    banner_prompt += "\nIMPORTANT FOR BANNER: Keep the main character strictly in the center 50% of the image. Leave a MASSIVE amount of empty space on the left, right, top, and bottom. The character must NOT touch any edges. Safe area is critical because this image will be aggressively cropped to a 750x400 panorama."

    cover_prompt = build_cover_prompt(
        set_name, char_name, character_prompt, scene_theme, description, style_preset
    )
    cover_prompt += "\nIMPORTANT FOR COVER: Keep the character's face/body entirely within the center of the image. Leave plenty of empty safe margin around the edges, as this will be scaled down to a 240x240 icon. Do not let any part of the character touch the borders."

    banner_prompt_file = os.path.join(target_dir, "temp_banner_prompt.txt")
    cover_prompt_file = os.path.join(target_dir, "temp_cover_prompt.txt")
    banner_raw = os.path.join(target_dir, "raw_banner.png")
    cover_raw = os.path.join(target_dir, "raw_cover.png")

    with open(banner_prompt_file, "w", encoding="utf-8") as f:
        f.write(banner_prompt)
    with open(cover_prompt_file, "w", encoding="utf-8") as f:
        f.write(cover_prompt)

    print("  -> 画 Banner 中...")
    if not os.path.exists(banner_raw):
        remote_draw_trigger(
            banner_prompt_file, banner_raw, ref_img, provider, size="1280*720"
        )
    else:
        print("  -> (缓存已存在跳过生成)")

    print("  -> 画 Cover 中...")
    if not os.path.exists(cover_raw):
        remote_draw_trigger(
            cover_prompt_file, cover_raw, ref_img, provider, size="512*512"
        )
    else:
        print("  -> (缓存已存在跳过生成)")

    print("\n[*] 正在按微信规范裁切与缩放图片...")

    if os.path.exists(banner_raw):
        try:
            with Image.open(banner_raw) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                w, h = img.size
                target_ratio = 750 / 400
                current_ratio = w / h

                if current_ratio > target_ratio:
                    new_w = int(h * target_ratio)
                    left = (w - new_w) // 2
                    img = img.crop((left, 0, left + new_w, h))
                else:
                    new_h = int(w / target_ratio)
                    top = (h - new_h) // 2
                    img = img.crop((0, top, w, top + new_h))

                img.resize((750, 400), Image.Resampling.LANCZOS).save(
                    os.path.join(export_root, "banner.png"), "PNG"
                )
                print("[✓] 微信 Banner (750x400) 制作完成！")
        except Exception as e:
            print(f"[!] Banner 处理失败: {e}")

    if os.path.exists(cover_raw):
        try:
            with Image.open(cover_raw) as img:
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                w, h = img.size
                min_dim = min(w, h)
                left = (w - min_dim) // 2
                top = (h - min_dim) // 2
                img = img.crop((left, top, left + min_dim, top + min_dim))

                img.resize((240, 240), Image.Resampling.LANCZOS).save(
                    os.path.join(export_root, "cover.png"), "PNG"
                )
                img.resize((50, 50), Image.Resampling.LANCZOS).save(
                    os.path.join(export_root, "icon.png"), "PNG"
                )
                print("[✓] 微信 Cover (240x240) & Icon (50x50) 制作完成！")
        except Exception as e:
            print(f"[!] Cover 处理失败: {e}")

    if os.path.exists(banner_prompt_file):
        os.remove(banner_prompt_file)
    if os.path.exists(cover_prompt_file):
        os.remove(cover_prompt_file)

    print(f"🎉 目录 {target_dir} 物料补全完毕！")
    return True


def process_all_meta(output_dir, provider=None, skill_dir=None):
    if not os.path.exists(output_dir):
        print(f"[!] 找不到 {output_dir} 目录")
        return

    dirs = [
        os.path.join(output_dir, d)
        for d in os.listdir(output_dir)
        if os.path.isdir(os.path.join(output_dir, d))
    ]
    dirs.sort(key=os.path.getmtime, reverse=True)

    for d in dirs:
        if os.path.exists(os.path.join(d, "params.json")):
            generate_meta(d, provider=provider, skill_dir=skill_dir)
