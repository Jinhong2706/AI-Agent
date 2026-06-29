#!/usr/bin/env python3
"""
html-to-image 渲染脚本
将 HTML 文件通过 Playwright 浏览器截图输出为 PNG

用法:
  python3 render.py <html文件路径> [--output <输出PNG路径>] [--wait <ms>] [--scale <2>]
"""

import argparse
import os
import sys
import json

# Playwright 路径（从 /tmp/node_modules 加载）
PLAYWRIGHT_PATH = '/tmp/node_modules/playwright'
sys.path.insert(0, PLAYWRIGHT_PATH)

from playwright.sync_api import sync_playwright

# Chrome 路径（macOS 系统已安装的 Chromium）
CHROME_PATH = '/Users/huanghaifeng/Library/Caches/ms-playwright/chromium-1208/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'


def render_html_to_png(
    html_path: str,
    output_path: str = None,
    wait_ms: int = 300,
    scale: int = 2,
):
    """
    将 HTML 文件渲染为 PNG 图片

    Args:
        html_path: HTML 文件路径（可以是绝对路径或相对路径）
        output_path: 输出 PNG 路径，默认与 HTML 同名扩展名为 .png
        wait_ms: 等待渲染时间（毫秒）
        scale: 设备像素比，2=Retina 高清
    """
    html_path = os.path.abspath(html_path)
    if not os.path.exists(html_path):
        raise FileNotFoundError(f"HTML 文件不存在: {html_path}")

    if output_path is None:
        output_path = os.path.splitext(html_path)[0] + '.png'
    output_path = os.path.abspath(output_path)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME_PATH)
        page = browser.new_page(viewport={'width': 1280, 'height': 900}, device_scale_factor=scale)

        # 打开 HTML 文件
        file_url = f'file://{html_path}'
        page.goto(file_url, wait_until='networkidle')
        page.wait_for_timeout(wait_ms)

        # 获取 .container 元素的精确区域
        box = page.evaluate('''() => {
            const el = document.querySelector('.container');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: r.left, y: r.top, w: r.width, h: r.height };
        }''')

        if box is None:
            # 没有 .container，用整个页面
            page.screenshot(path=output_path, full_page=True)
            print(f"⚠️ 未找到 .container 元素，截取整页: {output_path}")
        else:
            # 截图指定区域（留 16px 边距）
            page.screenshot(
                path=output_path,
                clip={
                    'x': box['x'] - 16,
                    'y': box['y'] - 16,
                    'width': box['w'] + 32,
                    'height': box['h'] + 32,
                }
            )
            print(f"✅ {output_path} ({box['w']:.0f}x{box['h']:.0f})")

        browser.close()

    return output_path


def main():
    parser = argparse.ArgumentParser(description='HTML 转 PNG 图片（Playwright 浏览器渲染）')
    parser.add_argument('html_path', help='HTML 文件路径')
    parser.add_argument('--output', '-o', help='输出 PNG 路径（默认与 HTML 同名）')
    parser.add_argument('--wait', '-w', type=int, default=300, help='等待渲染时间 ms（默认 300）')
    parser.add_argument('--scale', '-s', type=int, default=2, help='设备像素比（默认 2）')
    args = parser.parse_args()

    try:
        result = render_html_to_png(
            html_path=args.html_path,
            output_path=args.output,
            wait_ms=args.wait,
            scale=args.scale,
        )
        print(f"输出文件: {result}")
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 渲染失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
