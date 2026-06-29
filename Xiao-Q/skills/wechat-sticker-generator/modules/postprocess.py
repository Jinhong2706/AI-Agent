import os
import sys
import json
import shutil
from PIL import Image

from modules.background import apply_background_removal
from modules.constants import GRID_CONFIG, DEFAULT_GRID_SIZE


def _resolve_bg_processing_config(target_dir):
    params_path = os.path.join(target_dir, "params.json")
    default_config = {
        "enabled": False,
        "method": "rembg",
        "model": "isnet-anime",
        "alpha_matting": True,
        "sharpen_edges": False,
        "sharpen_threshold": 200,
        "grid_size": DEFAULT_GRID_SIZE,
    }

    if not os.path.exists(params_path):
        return default_config

    try:
        with open(params_path, "r", encoding="utf-8") as f:
            params = json.load(f)
    except Exception as e:
        print(f"[!] Failed to parse params.json: {e}", file=sys.stderr)
        return default_config

    background_type = params.get("background_type", "transparent")
    enabled = params.get("enable_bg_removal", background_type == "transparent")
    method = params.get("bg_removal_method", "rembg")
    model = params.get("bg_removal_model", "isnet-anime")
    alpha_matting = params.get("bg_alpha_matting", True)
    sharpen_edges = params.get("bg_sharpen_edges", False)
    sharpen_threshold = params.get("bg_sharpen_threshold", 200)
    grid_size = params.get("grid_size", DEFAULT_GRID_SIZE)

    return {
        "enabled": bool(enabled),
        "method": method,
        "model": model,
        "alpha_matting": bool(alpha_matting),
        "sharpen_edges": bool(sharpen_edges),
        "sharpen_threshold": int(sharpen_threshold),
        "grid_size": grid_size,
    }


def _slice_grid_to_cells_original(img, width, height, grid_size=None):
    grid_size = grid_size or DEFAULT_GRID_SIZE
    config = GRID_CONFIG.get(grid_size, GRID_CONFIG[DEFAULT_GRID_SIZE])
    rows = config["rows"]
    cols = config["cols"]

    item_width = width // cols
    item_height = height // rows
    cells = []
    for row in range(rows):
        for col in range(cols):
            left = col * item_width
            upper = row * item_height
            box = (left, upper, left + item_width, upper + item_height)
            cells.append(img.crop(box))
    return cells


def _cleanup_obsolete_flat_sticker_outputs(target_dir):
    try:
        for name in os.listdir(target_dir):
            path = os.path.join(target_dir, name)
            if not os.path.isfile(path):
                continue
            if name.startswith("sticker_") and name.endswith(".png"):
                os.remove(path)
            elif name.startswith("animated_sticker") and name.endswith(".gif"):
                os.remove(path)
    except OSError:
        pass


def process_single_grid(target_dir, bg_cfg=None):
    grid_path = os.path.join(target_dir, "original_grid.png")
    if not os.path.exists(grid_path):
        print(f"Skipping {target_dir}: original_grid.png not found", file=sys.stderr)
        return False

    bg_cfg = bg_cfg or {
        "enabled": False,
        "method": "rembg",
        "model": "isnet-anime",
        "grid_size": DEFAULT_GRID_SIZE,
    }

    prompt_path = os.path.join(target_dir, "prompt.txt")
    is_animated = False
    grid_size = bg_cfg.get("grid_size", DEFAULT_GRID_SIZE)

    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
            if (
                "16-frame animation" in content
                or "16-frame animation sprite sheet" in content
            ):
                grid_size = 16
                is_animated = True
            elif (
                "9-frame animation" in content
                or "9-frame animation sprite sheet" in content
                or "A HIGHLY DYNAMIC 9-frame animation" in content
            ):
                grid_size = 9
                is_animated = True
            elif "16 different expressions" in content or "SIXTEEN" in content:
                grid_size = 16
            elif "9 different expressions" in content or "NINE" in content:
                grid_size = 9

    grid_config = GRID_CONFIG.get(grid_size, GRID_CONFIG[DEFAULT_GRID_SIZE])
    total_frames = grid_config["total_frames"]
    rows = grid_config["rows"]
    cols = grid_config["cols"]
    gif_duration = grid_config["gif_duration_ms"]

    try:
        img = Image.open(grid_path)
    except Exception as e:
        print(f"Error opening {grid_path}: {e}")
        return False

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    width, height = img.size

    if width != height:
        size = min(width, height)
        c_left = (width - size) // 2
        c_top = (height - size) // 2
        img = img.crop((c_left, c_top, c_left + size, c_top + size))
        width, height = size, size
        print(
            f"[*] Post-process: Auto-cropped non-square canvas into a {size}x{size} square before grid slicing."
        )

    img_original = img.copy()

    cells_original_high_res = _slice_grid_to_cells_original(
        img_original, width, height, grid_size
    )
    cells_original = [
        c.resize((240, 240), Image.Resampling.LANCZOS) for c in cells_original_high_res
    ]

    cells_nobg = None
    if bg_cfg.get("enabled"):
        any_modified = False
        cells_nobg_high_res = []
        method = str(bg_cfg.get("method", "rembg")).strip().lower()

        if method == "opencv":
            print(f"[*] Using OpenCV to process the whole grid at once...")
            try:
                img_nobg = apply_background_removal(img_original, bg_cfg)
                if img_nobg is not img_original:
                    nobg_path = os.path.join(target_dir, "original_grid_nobg.png")
                    img_nobg.save(nobg_path, "PNG")
                    print(
                        f"[✓] Saved full grid after OpenCV background removal: {nobg_path}"
                    )

                    cells_nobg_high_res = _slice_grid_to_cells_original(
                        img_nobg, width, height, grid_size
                    )
                    any_modified = True
            except Exception as e:
                print(
                    f"[!] OpenCV background removal failed on full grid: {e}. Falling back to cell-by-cell.",
                    file=sys.stderr,
                )

        if not any_modified:
            print(
                f"[*] Extracting {total_frames} individual bounding-boxes before background removal for ultimate precision..."
            )
            for cell in cells_original_high_res:
                nobg_cell = apply_background_removal(cell, bg_cfg)
                cells_nobg_high_res.append(nobg_cell)
                if nobg_cell is not cell:
                    any_modified = True

            if any_modified:
                stitched = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                item_w = width // cols
                item_h = height // rows
                for i, cell in enumerate(cells_nobg_high_res):
                    row = i // cols
                    col = i % cols
                    stitched.paste(cell, (col * item_w, row * item_h))

                nobg_path = os.path.join(target_dir, "original_grid_nobg.png")
                stitched.save(nobg_path, "PNG")
                print(
                    f"[✓] Saved stitched full grid after precise cell-by-cell background removal: {nobg_path}"
                )

        if any_modified:
            cells_nobg = [
                c.resize((240, 240), Image.Resampling.LANCZOS)
                for c in cells_nobg_high_res
            ]
        else:
            print(
                "[!] Background removal skipped or failed for all cells; not writing original_grid_nobg.png",
                file=sys.stderr,
            )

    _cleanup_obsolete_flat_sticker_outputs(target_dir)
    legacy_white = os.path.join(target_dir, "white")
    if os.path.isdir(legacy_white):
        shutil.rmtree(legacy_white, ignore_errors=True)
    dir_origin = os.path.join(target_dir, "origin")
    os.makedirs(dir_origin, exist_ok=True)
    for i in range(total_frames):
        idx = i + 1
        cells_original[i].save(
            os.path.join(dir_origin, f"sticker_{idx:02d}.png"), "PNG"
        )
    if is_animated:
        cells_original[0].save(
            os.path.join(dir_origin, "animated_sticker.gif"),
            save_all=True,
            append_images=cells_original[1:],
            duration=gif_duration,
            loop=0,
            disposal=2,
        )

    dir_nobg = os.path.join(target_dir, "nobg")
    if cells_nobg is not None:
        os.makedirs(dir_nobg, exist_ok=True)
        for i in range(total_frames):
            idx = i + 1
            cells_nobg[i].save(os.path.join(dir_nobg, f"sticker_{idx:02d}.png"), "PNG")
        if is_animated:
            cells_nobg[0].save(
                os.path.join(dir_nobg, "animated_sticker.gif"),
                save_all=True,
                append_images=cells_nobg[1:],
                duration=gif_duration,
                loop=0,
                disposal=2,
            )
        print(
            f"[✓] Outputs: {dir_origin}/ (origin, crop only) + {dir_nobg}/ (transparent)"
        )
    else:
        if os.path.isdir(dir_nobg):
            shutil.rmtree(dir_nobg, ignore_errors=True)
        print(f"[✓] Outputs: {dir_origin}/ (origin only; no nobg/)")
    return True


def _collect_export_gifs(workspace_root):
    if not os.path.isdir(workspace_root):
        return

    anim_dirs = [
        item
        for item in sorted(os.listdir(workspace_root))
        if item.startswith("anim_")
        and os.path.isdir(os.path.join(workspace_root, item))
    ]
    export_root = os.path.join(workspace_root, "export_gifs")

    if len(anim_dirs) < 2:
        if os.path.isdir(export_root):
            shutil.rmtree(export_root, ignore_errors=True)
            print("[*] export_gifs/ omitted (only one anim_* in workspace)")
        return

    shutil.rmtree(export_root, ignore_errors=True)
    origin_out = os.path.join(export_root, "origin")
    nobg_out = os.path.join(export_root, "nobg")
    os.makedirs(origin_out, exist_ok=True)

    nobg_any = False
    for anim in anim_dirs:
        src_o = os.path.join(workspace_root, anim, "origin", "animated_sticker.gif")
        if os.path.isfile(src_o):
            shutil.copy2(src_o, os.path.join(origin_out, f"{anim}.gif"))
        src_n = os.path.join(workspace_root, anim, "nobg", "animated_sticker.gif")
        if os.path.isfile(src_n):
            if not nobg_any:
                os.makedirs(nobg_out, exist_ok=True)
                nobg_any = True
            shutil.copy2(src_n, os.path.join(nobg_out, f"{anim}.gif"))

    parts = [f"{origin_out}/"]
    if nobg_any:
        parts.append(f"{nobg_out}/")
    print(
        f"[✓] export_gifs: {' + '.join(parts)} — copies of animated_sticker.gif for export"
    )


def _pack_wechat_export(workspace_root, is_static):
    if not os.path.isdir(workspace_root):
        return

    export_root = os.path.join(workspace_root, "wechat_export")
    shutil.rmtree(export_root, ignore_errors=True)
    os.makedirs(export_root, exist_ok=True)

    main_dir = os.path.join(export_root, "main")
    thumb_dir = os.path.join(export_root, "thumb")
    os.makedirs(main_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)

    items = []

    if is_static:
        static_dirs = sorted(
            [d for d in os.listdir(workspace_root) if d.startswith("static_")]
        )
        for d in static_dirs:
            base = os.path.join(workspace_root, d)
            target = os.path.join(base, "nobg")
            if not os.path.exists(target):
                target = os.path.join(base, "origin")
            if os.path.exists(target):
                for i in range(1, 17):
                    fpath = os.path.join(target, f"sticker_{i:02d}.png")
                    if os.path.exists(fpath):
                        items.append(fpath)
    else:
        anim_dirs = sorted(
            [d for d in os.listdir(workspace_root) if d.startswith("anim_")]
        )
        for d in anim_dirs:
            base = os.path.join(workspace_root, d)
            target = os.path.join(base, "nobg")
            if not os.path.exists(target):
                target = os.path.join(base, "origin")
            gif_path = os.path.join(target, "animated_sticker.gif")
            frame_path = os.path.join(target, "sticker_01.png")
            if os.path.exists(gif_path) and os.path.exists(frame_path):
                items.append((gif_path, frame_path))

    items = items[:24]

    first_frame = None

    for idx, item in enumerate(items):
        file_idx = idx + 1
        thumb_name = f"{file_idx:02d}.png"

        if is_static:
            src_png = item
            main_name = f"{file_idx:02d}.png"
            shutil.copy2(src_png, os.path.join(main_dir, main_name))

            with Image.open(src_png) as img:
                thumb = img.resize((120, 120), Image.Resampling.LANCZOS)
                thumb.save(os.path.join(thumb_dir, thumb_name), "PNG")
                if first_frame is None:
                    first_frame = img.copy()
        else:
            src_gif, src_frame = item
            main_name = f"{file_idx:02d}.gif"
            shutil.copy2(src_gif, os.path.join(main_dir, main_name))

            with Image.open(src_frame) as img:
                thumb = img.resize((120, 120), Image.Resampling.LANCZOS)
                thumb.save(os.path.join(thumb_dir, thumb_name), "PNG")
                if first_frame is None:
                    first_frame = img.copy()

    if first_frame:
        cover_path = os.path.join(export_root, "cover.png")
        first_frame.resize((240, 240), Image.Resampling.LANCZOS).save(cover_path, "PNG")

        icon_path = os.path.join(export_root, "icon.png")
        first_frame.resize((50, 50), Image.Resampling.LANCZOS).save(icon_path, "PNG")

    banner_path = os.path.join(export_root, "banner.png")
    banner = Image.new("RGB", (750, 400), (255, 248, 231))
    if first_frame:
        scaled = first_frame.resize((240, 240), Image.Resampling.LANCZOS)
        if scaled.mode == "RGBA":
            banner.paste(scaled, (255, 80), scaled)
        else:
            banner.paste(scaled, (255, 80))
    banner.save(banner_path, "PNG")

    warnings = []

    def check_size(filepath, max_kb, name_desc):
        if os.path.exists(filepath):
            size_kb = os.path.getsize(filepath) / 1024.0
            if size_kb > max_kb:
                warnings.append(
                    f"⚠️ {name_desc} 体积超标: {size_kb:.1f}KB (限制 < {max_kb}KB)"
                )

    for f in os.listdir(main_dir):
        check_size(os.path.join(main_dir, f), 500, f"主图 {f}")
    if os.path.exists(thumb_dir):
        for f in os.listdir(thumb_dir):
            check_size(os.path.join(thumb_dir, f), 50, f"缩略图 {f}")
    check_size(os.path.join(export_root, "cover.png"), 80, "封面图 cover.png")
    check_size(os.path.join(export_root, "icon.png"), 30, "图标 icon.png")
    check_size(os.path.join(export_root, "banner.png"), 80, "横幅 banner.png")

    print(f"\n[✓] WeChat standard export package created at: {export_root}")
    print(f"    Total expressions: {len(items)}")
    print(f"    - main/ (240x240 {'PNG' if is_static else 'GIF'})")
    print(f"    - thumb/ (120x120 PNG)")
    print(f"    - cover.png (240x240 PNG)")
    print(f"    - icon.png (50x50 PNG)")
    print(f"    - banner.png (750x400 JPG/PNG, Default Light Ivory)")

    params_path = os.path.join(workspace_root, "params.json")
    if os.path.exists(params_path):
        with open(params_path, "r", encoding="utf-8") as f:
            try:
                params = json.load(f)
                set_name = params.get("set_name", "未命名表情包")
                set_desc = params.get(
                    "set_description", "微信官方表情包套件自动生成产物"
                )
                copy_info = params.get("copyright_info", "AI Generated")
                info_path = os.path.join(export_root, "upload_info.txt")
                with open(info_path, "w", encoding="utf-8") as txt:
                    txt.write(
                        "【微信表情包后台上传资料库】（可直接复制粘贴到微信后台）\n"
                    )
                    txt.write("=" * 50 + "\n")
                    txt.write(f"表情包名称 (不超过8字): {set_name}\n")
                    txt.write(f"表情包介绍 (不超过60字): {set_desc}\n")
                    txt.write(f"版权信息 / 艺术家: {copy_info}\n")
                    txt.write("=" * 50 + "\n")
                print(
                    f"    - upload_info.txt (包含供直接复制粘贴的 表情包名称/介绍/版权 等填单材料)"
                )
            except Exception as e:
                pass

    if warnings:
        print("\n[!] 微信体积限制体检警告:")
        for w in warnings:
            print("   " + w)
        print("   (提示：若GIF超标，请尝试在外部压制降低帧数或色彩断层)\n")
    else:
        print("\n[✓] 产物体检通过: 所有文件体积均符合微信官方限制。\n")


def process_workspace(target_dir):
    bg_cfg = _resolve_bg_processing_config(target_dir)
    if bg_cfg.get("enabled"):
        print(
            f"[*] Background removal enabled: method={bg_cfg.get('method')} model={bg_cfg.get('model')}"
        )

    is_static = False

    if os.path.exists(os.path.join(target_dir, "prompt.txt")):
        is_static = True
        process_single_grid(target_dir, bg_cfg=bg_cfg)
    else:
        for item in sorted(os.listdir(target_dir)):
            sub_dir = os.path.join(target_dir, item)
            if os.path.isdir(sub_dir) and (
                item.startswith("anim_") or item.startswith("static_")
            ):
                if item.startswith("static_"):
                    is_static = True
                process_single_grid(sub_dir, bg_cfg=bg_cfg)
        _collect_export_gifs(target_dir)

    _pack_wechat_export(target_dir, is_static)

    print(f"Batch process complete for workspace: {os.path.abspath(target_dir)}")
