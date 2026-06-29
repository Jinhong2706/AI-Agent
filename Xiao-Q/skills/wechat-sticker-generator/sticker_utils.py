import os
import sys
import glob as glob_module
from datetime import datetime

from modules.config import config_command
from modules.prompts import (
    build_prompts_workspace,
    build_transform_photo_prompt,
    build_character_reference_prompt,
)
from modules.api import (
    transform_photo_to_chibi,
    draw_character_reference,
    remote_draw_trigger,
)
from modules.postprocess import process_workspace
from modules.meta import generate_meta, process_all_meta

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))


def normalize_path(path_str):
    """跨平台路径规范化"""
    path_str = os.path.expanduser(path_str)
    path_str = os.path.normpath(path_str)
    return os.path.abspath(path_str)


OUTPUT_DIR = normalize_path("~/Documents/wechat-sticker-output")


def create_dir(provider=None):
    """在 ~/Documents/wechat-sticker-output/ 中创建时间戳工作空间"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
    if provider:
        timestamp_dir = f"{timestamp_dir}_{provider}"
    full_path = os.path.join(OUTPUT_DIR, timestamp_dir)
    os.makedirs(full_path, exist_ok=True)
    out_dir_abs = os.path.abspath(full_path)
    print(out_dir_abs)
    return out_dir_abs


def batch_draw(target_dir, provider=None, max_concurrent=3, delay_between=1.0):
    """批量生成所有 anim_* 或 static_* 目录下的图片（并发执行）"""
    import json
    import concurrent.futures
    import time

    # 读取 params.json 获取 reference_image
    params_path = os.path.join(target_dir, "params.json")
    reference_image = None
    if os.path.exists(params_path):
        with open(params_path, "r", encoding="utf-8") as f:
            params = json.load(f)
            ref = params.get("reference_image", "")
            if ref and os.path.isfile(ref):
                reference_image = ref

    # 查找所有 anim_* 或 static_* 子目录
    subdirs = sorted(
        [
            d
            for d in os.listdir(target_dir)
            if os.path.isdir(os.path.join(target_dir, d))
            and (d.startswith("anim_") or d.startswith("static_"))
        ]
    )

    if not subdirs:
        print(f"No anim_* or static_* directories found in {target_dir}")
        return False

    print(
        f"Found {len(subdirs)} directories to process (max_concurrent={max_concurrent})"
    )

    def process_single(subdir):
        """处理单个子目录"""
        subdir_path = os.path.join(target_dir, subdir)
        prompt_path = os.path.join(subdir_path, "prompt.txt")
        output_path = os.path.join(subdir_path, "original_grid.png")

        if not os.path.exists(prompt_path):
            return (subdir, None, "prompt.txt not found")

        if os.path.exists(output_path):
            return (subdir, True, "already exists, skipped")

        if reference_image:
            result = remote_draw_trigger(
                prompt_path, output_path, reference_image, provider=provider
            )
        else:
            result = remote_draw_trigger(prompt_path, output_path, provider=provider)

        return (subdir, result, "success" if result else "failed")

    results = []
    success_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = {}
        for i, subdir in enumerate(subdirs):
            # 频率限制：每批之间加延迟
            if i > 0 and i % max_concurrent == 0:
                time.sleep(delay_between)

            future = executor.submit(process_single, subdir)
            futures[future] = subdir

        for future in concurrent.futures.as_completed(futures):
            subdir, result, message = future.result()
            if result is True:
                success_count += 1
                print(f"[✓] {subdir}: {message}")
            elif result is None:
                print(f"[!] {subdir}: {message}")
            else:
                print(f"[✗] {subdir}: {message}")
            results.append((subdir, result, message))

    print(f"\n[✓] Batch draw complete: {success_count}/{len(subdirs)} succeeded")
    return success_count == len(subdirs)


def _parse_provider_arg(args):
    """从参数列表中解析 --provider 参数"""
    provider = None
    remaining = []
    i = 0
    while i < len(args):
        if args[i] == "--provider" and i + 1 < len(args):
            provider = args[i + 1]
            i += 2
        else:
            remaining.append(args[i])
            i += 1
    return provider, remaining


if __name__ == "__main__":
    # 先解析 --provider 参数
    provider_arg, remaining_argv = _parse_provider_arg(sys.argv[1:])

    if not remaining_argv:
        print("Usage:")
        print("  python3 sticker_utils.py create_dir")
        print(
            "  python3 sticker_utils.py transform_photo <photo_path> <style_preset> <output_path> [additional_description]"
        )
        print(
            "  python3 sticker_utils.py draw_character <character_prompt> <style_preset> <output_path>"
        )
        print("  python3 sticker_utils.py build_prompts <target_directory_path>")
        print(
            "  python3 sticker_utils.py batch_draw <target_directory_path> [--concurrent N] [--delay S]"
        )
        print(
            "  python3 sticker_utils.py draw <prompt.txt> <output_original_grid.png> [reference_image]"
        )
        print(
            "  python3 sticker_utils.py draw_with_ref <prompt.txt> <output.png> <reference_image>"
        )
        print("  python3 sticker_utils.py process <target_directory_path>")
        print("  python3 sticker_utils.py wechat_meta <target_directory_path|all>")
        print("")
        print("可选参数:")
        print("  --provider <gemini|qwen>  指定 API 提供商（默认从配置或环境变量读取）")
        print("")
        print("环境变量:")
        print("  GEMINI_API_KEY     Gemini API Key")
        print("  DASHSCOPE_API_KEY  千问 API Key")
        print("")
        print("配置管理:")
        print("  python3 sticker_utils.py config                    # 显示当前配置")
        print("  python3 sticker_utils.py config set <provider>     # 设置 API Key")
        print(
            "  python3 sticker_utils.py config default <provider> # 设置默认 provider"
        )
        sys.exit(1)

    cmd = remaining_argv[0]

    if cmd == "config":
        config_command(remaining_argv[1:])
    elif cmd == "create_dir":
        create_dir(provider=provider_arg)
    elif cmd == "transform_photo":
        if len(remaining_argv) < 4:
            print(
                "Usage: python3 sticker_utils.py transform_photo <photo_path> <style_preset> <output_path> [additional_description] [--provider gemini|qwen]"
            )
            sys.exit(1)
        photo_path = normalize_path(remaining_argv[1])
        style_preset = remaining_argv[2]
        output_path = normalize_path(remaining_argv[3])
        additional_desc = remaining_argv[4] if len(remaining_argv) > 4 else ""
        prompt = build_transform_photo_prompt(style_preset, additional_desc)
        transform_photo_to_chibi(photo_path, prompt, output_path, provider=provider_arg)
    elif cmd == "draw_character":
        if len(remaining_argv) < 4:
            print(
                "Usage: python3 sticker_utils.py draw_character <character_prompt> <style_preset> <output_path> [--provider gemini|qwen]"
            )
            sys.exit(1)
        prompt = build_character_reference_prompt(remaining_argv[1], remaining_argv[2])
        draw_character_reference(
            prompt, normalize_path(remaining_argv[3]), provider=provider_arg
        )
    elif cmd == "build_prompts":
        build_prompts_workspace(normalize_path(remaining_argv[1]))
    elif cmd == "batch_draw":
        if len(remaining_argv) < 2:
            print(
                "Usage: python3 sticker_utils.py batch_draw <target_directory_path> [--provider gemini|qwen] [--concurrent N] [--delay S]"
            )
            sys.exit(1)
        # 解析额外参数
        max_concurrent = 3
        delay_between = 1.0
        for i, arg in enumerate(remaining_argv):
            if arg == "--concurrent" and i + 1 < len(remaining_argv):
                max_concurrent = int(remaining_argv[i + 1])
            elif arg == "--delay" and i + 1 < len(remaining_argv):
                delay_between = float(remaining_argv[i + 1])
        batch_draw(
            normalize_path(remaining_argv[1]),
            provider=provider_arg,
            max_concurrent=max_concurrent,
            delay_between=delay_between,
        )
    elif cmd == "draw":
        if len(remaining_argv) < 3:
            print(
                "Usage: python3 sticker_utils.py draw <prompt.txt> <output.png> [reference_image] [--provider gemini|qwen]"
            )
            sys.exit(1)
        ref_image = (
            normalize_path(remaining_argv[3]) if len(remaining_argv) > 3 else None
        )
        remote_draw_trigger(
            normalize_path(remaining_argv[1]),
            normalize_path(remaining_argv[2]),
            ref_image,
            provider=provider_arg,
        )
    elif cmd == "draw_with_ref":
        if len(remaining_argv) < 4:
            print(
                "Usage: python3 sticker_utils.py draw_with_ref <prompt.txt> <output.png> <reference_image> [--provider gemini|qwen]"
            )
            sys.exit(1)
        remote_draw_trigger(
            normalize_path(remaining_argv[1]),
            normalize_path(remaining_argv[2]),
            normalize_path(remaining_argv[3]),
            provider=provider_arg,
        )
    elif cmd == "process":
        process_workspace(normalize_path(remaining_argv[1]))
    elif cmd == "wechat_meta":
        if len(remaining_argv) < 2:
            print(
                "Usage: python3 sticker_utils.py wechat_meta <target_dir|all> [--provider gemini|qwen]"
            )
            sys.exit(1)
        target = remaining_argv[1]
        if target.lower() == "all":
            process_all_meta(OUTPUT_DIR, provider=provider_arg, skill_dir=SKILL_DIR)
        else:
            generate_meta(
                normalize_path(target), provider=provider_arg, skill_dir=SKILL_DIR
            )
