"""反检测引擎 - 覆盖浏览器自动化特征"""
from playwright.async_api import BrowserContext


def get_chromium_args() -> list:
    return [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-first-run",
        "--no-service-autorun",
        "--password-store=basic",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        "--hide-scrollbars",
        "--mute-audio",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--start-maximized",
        "--use-mock-keychain",
        "--window-size=1920,1080",
    ]


STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
window.navigator.chrome = { runtime: {} };
window.chrome = { runtime: {} };
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
"""


async def create_stealth_context(browser, **kwargs) -> BrowserContext:
    ctx = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        permissions=["geolocation"],
        **kwargs,
    )
    await ctx.add_init_script(STEALTH_JS)
    return ctx
