#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""
html_to_image.py
将 HTML 文件转换为 PNG 图片（使用 Playwright Chromium）

用法:
    python html_to_image.py <input.html> [output.png] [--width 1600] [--wait 2000]

依赖:
    pip install playwright
    playwright install chromium
"""
import sys, argparse, pathlib

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright 未安装，请运行: pip install playwright && playwright install chromium")
    sys.exit(1)


def html_to_image(html_path, out_path=None, *, viewport_width=1600, wait_ms=2000):
    """
    将 HTML 文件渲染为 PNG。

    Parameters
    ----------
    html_path : str or Path
        输入 HTML 文件路径
    out_path : str or Path, optional
        输出 PNG 路径，默认与 html 同名，扩展名改为 .png
    viewport_width : int
        视口宽度（默认 1600px）
    wait_ms : int
        等待渲染时间（默认 2000ms）
    """
    # H-6 FIX: 删除无效的 scale 参数，Playwright 只接受 "css"/"device" 字符串
    html_path = pathlib.Path(html_path)
    if not html_path.exists():
        print(f"ERROR: 文件不存在: {html_path}")
        sys.exit(1)

    if out_path is None:
        out_path = SCRIPT_DIR.parent / "output" / html_path.name.replace(".html", ".png")
    else:
        out_path = pathlib.Path(out_path)

    abs_path = str(html_path.resolve())
    if not abs_path.startswith("/"):
        abs_path = "file:///" + abs_path.replace("\\", "/")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": viewport_width, "height": 800})
        page.goto(abs_path, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(wait_ms)

        # Measure real content height with a small viewport first
        content_height = page.evaluate("""
            () => {
                // Temporarily remove min-height constraints to get true content size
                document.body.style.minHeight = '0';
                document.documentElement.style.minHeight = '0';
                return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
            }
        """)
        # Clamp to reasonable bounds
        content_height = max(600, min(content_height, 8000))
        page.set_viewport_size({"width": viewport_width, "height": content_height})
        page.wait_for_timeout(500)
        page.screenshot(path=str(out_path), full_page=True, type="png", scale="css")
        browser.close()

    size_kb = out_path.stat().st_size // 1024
    print(f"OK: {out_path} ({size_kb} KB, {viewport_width}x{content_height}px)")
    return str(out_path)


def main():
    parser = argparse.ArgumentParser(description="HTML → PNG 转换（Playwright）")
    parser.add_argument("input", help="输入 HTML 文件")
    parser.add_argument("output", nargs="?", help="输出 PNG 文件（默认自动命名）")
    parser.add_argument("--width", type=int, default=1600, help="视口宽度（默认1600）")
    parser.add_argument("--wait", type=int, default=2000, help="渲染等待时间ms（默认2000）")
    args = parser.parse_args()

    html_to_image(args.input, args.output, viewport_width=args.width, wait_ms=args.wait)


if __name__ == "__main__":
    main()
