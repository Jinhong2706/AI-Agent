"""闲鱼扫码登录 - 带滑块验证处理"""
import asyncio
import sys
import json
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from stealth import get_chromium_args, create_stealth_context

BASE_DIR = Path(__file__).parent
COOKIE_FILE = BASE_DIR / "cookies.json"

CHROME_PATH = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe").exists()
    else None
)

SLIDER_SELECTORS = [
    ".nc_wrapper", "#nc_1_n1z", ".slider-mask",
    "[class*='nc_slide']", "[class*='slider-track']",
]
HANDLE_SELECTORS = [
    "#nc_1_n1z", ".slider-mask [class*='handle']",
    "[class*='slider'] [class*='btn']", ".slider-mask",
]


async def _try_slider(page, max_retries=2):
    """检测并处理滑块验证。返回是否成功通过"""
    for attempt in range(max_retries):
        slider = await page.query_selector(", ".join(SLIDER_SELECTORS))
        if not slider:
            return False  # 没滑块，正常继续

        print(f"  [滑块] 检测到滑块，正在滑动... ({attempt + 1}/{max_retries})")
        box = await slider.bounding_box()
        if not box or box["width"] <= 0:
            await asyncio.sleep(1)
            continue

        # 找 handle
        handle = await page.query_selector(", ".join(HANDLE_SELECTORS))
        handle_box = (await handle.bounding_box()) if handle else box

        start_x = handle_box["x"] + handle_box["width"] / 2
        start_y = handle_box["y"] + handle_box["height"] / 2
        slide_dist = max(box["width"] - 55, int(box["width"] * 0.85))

        await page.mouse.move(start_x, start_y)
        await page.mouse.down()
        await asyncio.sleep(0.1)

        # 分3段滑动，带轻微上下抖动
        for seg in range(3):
            seg_x = start_x + (slide_dist / 3) * (seg + 1)
            jitter_y = start_y + (2 if seg % 2 == 0 else -2)
            await page.mouse.move(seg_x, jitter_y, steps=6)
            await asyncio.sleep(0.12)

        await page.mouse.up()
        await asyncio.sleep(2)

        # 检查是否滑过
        still = await page.query_selector(", ".join(SLIDER_SELECTORS))
        if not still:
            print("  [滑块] 已通过 ✓")
            return True

    print("  [滑块] 处理失败，请手动处理")
    return False


async def login():
    """扫码登录闲鱼并保存 Cookie"""
    print("打开闲鱼登录页...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            executable_path=CHROME_PATH,
            args=get_chromium_args(),
        )
        ctx = await create_stealth_context(browser)
        page = await ctx.new_page()

        await page.goto(
            "https://www.goofish.com/login",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        await asyncio.sleep(2)

        # 处理登录页初始滑块
        if await page.query_selector(", ".join(SLIDER_SELECTORS)):
            print("检测到初始滑块，先处理...")
            await _try_slider(page, max_retries=2)

        print("请扫码登录（最多等待 120 秒）...")

        # 轮询等待登录完成
        start = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start) < 120:
            if "login" not in page.url.lower() and "goofish.com" in page.url:
                print("登录成功！")
                break
            # 有滑块就处理
            if await page.query_selector(", ".join(SLIDER_SELECTORS)):
                await _try_slider(page, max_retries=2)
            await asyncio.sleep(3)
        else:
            print("登录超时，请重试")
            await browser.close()
            return False

        await ctx.storage_state(path=str(COOKIE_FILE))
        print(f"Cookie 已保存: {COOKIE_FILE}")
        await browser.close()
        return True


if __name__ == "__main__":
    asyncio.run(login())
