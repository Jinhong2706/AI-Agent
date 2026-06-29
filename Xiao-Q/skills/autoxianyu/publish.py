"""闲鱼商品发布"""
import asyncio
import argparse
import sys
import json
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from stealth import get_chromium_args, create_stealth_context

BASE_DIR = Path(__file__).parent
COOKIE_FILE = BASE_DIR / "cookies.json"
IMAGES_DIR = BASE_DIR / "images" / "products"

CHROME_PATH = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe").exists()
    else None
)

# 滑块选择器
SLIDER_SELECTORS = [
    ".nc_wrapper", "#nc_1_n1z", ".slider-mask",
    "[class*='nc_slide']", "[class*='slider-track']",
]
HANDLE_SELECTORS = [
    "#nc_1_n1z", ".slider-mask [class*='handle']",
    "[class*='slider'] [class*='btn']", ".slider-mask",
]


async def _try_slider(page, max_retries=2):
    for attempt in range(max_retries):
        slider = await page.query_selector(", ".join(SLIDER_SELECTORS))
        if not slider:
            return False
        print(f"  [滑块] 检测到滑块，正在滑动... ({attempt + 1}/{max_retries})")
        box = await slider.bounding_box()
        if not box or box["width"] <= 0:
            await asyncio.sleep(1)
            continue
        handle = await page.query_selector(", ".join(HANDLE_SELECTORS))
        handle_box = (await handle.bounding_box()) if handle else box
        start_x = handle_box["x"] + handle_box["width"] / 2
        start_y = handle_box["y"] + handle_box["height"] / 2
        slide_dist = max(box["width"] - 55, int(box["width"] * 0.85))
        await page.mouse.move(start_x, start_y)
        await page.mouse.down()
        await asyncio.sleep(0.1)
        for seg in range(3):
            seg_x = start_x + (slide_dist / 3) * (seg + 1)
            jitter_y = start_y + (2 if seg % 2 == 0 else -2)
            await page.mouse.move(seg_x, jitter_y, steps=6)
            await asyncio.sleep(0.12)
        await page.mouse.up()
        await asyncio.sleep(2)
        if not await page.query_selector(", ".join(SLIDER_SELECTORS)):
            print("  [滑块] 已通过 ✓")
            return True
    print("  [滑块] 处理失败，请手动处理")
    return False


def generate_description(brand, model, condition, price):
    """生成商品描述，每行用换行分隔（适合 contenteditable）"""
    cond_map = {
        "全新": "全新未拆封，支持验货",
        "99新": "99新仅试用，功能全部正常",
        "98新": "98新成色很好，无明显使用痕迹",
        "95新": "95新轻微使用痕迹，功能正常无暗病",
        "9成新": "9成新正常使用，轻微磨损",
        "85新": "85新有明显使用痕迹，功能正常",
        "8成新": "8成新重度使用，功能正常可验机",
    }
    cond_text = cond_map.get(condition, condition)
    lines = [
        f"{brand} {model}",
        f"【回收】{brand} {model} {condition}",
        "",
        f"成色：{cond_text}",
        f"型号：{model}",
        f"回收价：{price} 元（可小刀）",
        "",
        "支持线上验机，包邮出",
        "功能正常，无暗病，欢迎来问",
        "（监管机提前说明，报价另议）",
    ]
    return "\n".join(lines)


async def publish(brand, model, price, condition="95新", images=None) -> bool:
    print(f"发布: {brand} {model} {condition} - {price}元")

    if not COOKIE_FILE.exists():
        print("请先运行 python login.py 登录")
        return False

    # 确保图片目录存在
    if images:
        for img in images:
            if not Path(img).exists():
                print(f"图片不存在: {img}")
                return False
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                executable_path=CHROME_PATH,
                args=get_chromium_args(),
            )
            ctx = await create_stealth_context(browser)

            cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8")).get("cookies", [])
            await ctx.add_cookies(cookies)

            page = await ctx.new_page()
            await page.set_extra_http_headers({
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            })

            await page.goto(
                "https://www.goofish.com/publish",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await asyncio.sleep(3)

            # Cookie 失效检测
            if "login" in page.url:
                print("Cookie 失效，请重新运行 python login.py")
                await browser.close()
                return False

            await _try_slider(page, max_retries=2)

            # 上传图片
            if images:
                print(f"上传 {len(images)} 张图片...")
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(images)
                await asyncio.sleep(3)

            # 填写描述（逐行输入，每行后按 Enter 换行）
            print("填写描述...")
            desc = generate_description(brand, model, condition, price)
            desc_div = page.locator('div[contenteditable="true"]').first
            await desc_div.click()
            await asyncio.sleep(0.5)
            await desc_div.press("Control+a")
            await asyncio.sleep(0.3)

            # 逐行输入，用 Shift+Enter 或直接 type 带换行
            for line in desc.split("\n"):
                if line:
                    await page.keyboard.type(line, delay=15)
                await page.keyboard.press("Enter")
                await asyncio.sleep(0.15)
            await asyncio.sleep(1)

            # 填写价格
            print(f"填写价格: {price}元")
            await page.locator('input[placeholder="0.00"]').first.fill(str(price))
            await asyncio.sleep(1)

            # 点击发布
            print("发布中...")
            await page.locator('button:has-text("发布")').first.click()
            await asyncio.sleep(4)

            # 确认弹窗
            confirm_btn = page.locator('button:has-text("确定")').first
            if await confirm_btn.count() > 0:
                await confirm_btn.click()
                await asyncio.sleep(3)

            final_url = page.url
            await browser.close()

            if "/item?id=" in final_url:
                item_id = final_url.split("id=")[1].split("&")[0]
                print(f"发布成功! 链接: https://www.goofish.com/item?id={item_id}")
                return True
            else:
                print("发布状态不确定，请手动检查页面")
                return False

    except Exception as e:
        print(f"发布失败: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="闲鱼商品发布")
    parser.add_argument("--brand", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--price", type=int, required=True)
    parser.add_argument("--condition", default="95新")
    parser.add_argument("--images", nargs="+")
    args = parser.parse_args()
    await publish(args.brand, args.model, args.price, args.condition, args.images)


if __name__ == "__main__":
    asyncio.run(main())
