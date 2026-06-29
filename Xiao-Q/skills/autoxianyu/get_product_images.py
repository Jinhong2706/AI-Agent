"""闲鱼商品图片获取 - 滚动触发懒加载 + aiohttp 下载"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

from stealth import get_chromium_args, create_stealth_context

BASE_DIR = Path(__file__).parent
COOKIE_FILE = BASE_DIR / "cookies.json"
IMAGES_DIR = BASE_DIR / "images" / "products"

CHROME_PATH = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe").exists()
    else None
)

# 坏机关键词命中 → 直接跳过（分值 -999）
BROKEN_KEYWORDS = [
    "屏幕碎", "后盖碎", "碎屏", "爆屏", "屏破", "碎裂",
    "机身弯", "弯曲", "变形", "压过", "摔过",
    "磕碰", "磕破", "裂", "裂纹",
    "划痕", "有划", "屏幕划", "轻微划",
    "亮斑", "黑点", "烧屏", "屏幕老化",
    "进水", "受潮", "泡水",
    "维修", "修过", "动过主板",
    "面容不能用", "面容损", "FaceID坏",
    "电池0", "电池效率0", "电池效率低",
    "喇叭坏", "听筒坏", "摄像头坏", "摄像头裂",
    "不能开机", "开不了机", "卡贴", "有锁",
    "外观成色差", "成色差", "伊拉克", "战损",
    "便宜处理", "亏本出",
]
# 疑似非商品关键词 → 扣分
NOISE_KEYWORDS = [
    "便宜出", "换钱", "求购", "回收", "租赁",
    "手机壳", "手机膜", "贴膜", "配件", "套餐", "样机", "展示机",
]


def score_title(title: str, brand: str, model: str, category: str) -> int:
    """标题匹配打分。-999 = 坏机跳过，40+ = 候选"""
    t = title.lower()
    if any(kw in t for kw in BROKEN_KEYWORDS):
        return -999
    score = 0
    if category and category in t:
        score += 10
    if brand and brand.lower() in t:
        score += 30
    if model:
        ml = model.lower()
        if ml in t:
            score += 40
        elif any(re.search(rf"\b{n}\b", t) for n in re.findall(r"\d+", model)):
            score += 40
    if any(kw in t for kw in NOISE_KEYWORDS):
        score -= 20
    return score


def _thumb_to_full(url: str) -> str:
    """将缩略图 URL 转大图（去掉尺寸后缀，加 _!!600x600.jpg）"""
    if not url or "alicdn" not in url:
        return url
    for suffix in ["_110x10000", "_!!600x600", "_!!400x400", "_!!200x200"]:
        if url.endswith(suffix):
            url = url[: -len(suffix)]
            break
    for pattern in [r"_\d+-\w+-tps-\d+-\d+$", r"_\d+$"]:
        m = re.search(pattern, url)
        if m:
            url = url[: -len(m.group())]
    return (url.rstrip("_") + "_!!600x600.jpg") if not url.endswith("_") else url + "!!600x600.jpg"


async def _download_image(session: aiohttp.ClientSession, url: str, dest: Path, min_size: int = 20000) -> tuple[bool, int]:
    """下载单张图片，返回 (是否成功, 文件KB数)"""
    try:
        async with session.get(
            url,
            headers={
                "Referer": "https://www.goofish.com/",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                ),
            },
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                return False, 0
            body = await resp.read()
            if len(body) < min_size:
                return False, 0
            dest.write_bytes(body)
            return True, len(body) // 1024
    except Exception:
        return False, 0


async def get_product_images(
    keyword: str,
    max_images: int = 3,
    brand: str = "",
    model: str = "",
    category: str = "",
    skip_validation: bool = False,
) -> list[str]:
    """搜索商品 → 评分过滤坏机 → 滚动触发懒加载 → 下载商品图"""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    search_url = f"https://www.goofish.com/search?q={keyword}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    downloaded: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=False,
            args=get_chromium_args(),
        )
        ctx = await create_stealth_context(browser)

        if COOKIE_FILE.exists():
            cd = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
            if "cookies" in cd:
                await ctx.add_cookies(cd["cookies"])

        page = await ctx.new_page()
        await page.set_extra_http_headers({
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

        # ── 1. 搜索页 ──
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        product_links: list[dict] = await page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll("a").forEach(function(a) {
                    const href = a.href || "";
                    const text = (a.innerText || "").trim();
                    if (href.includes("/item?id=") && text.length > 20) {
                        links.push({href, title: text});
                    }
                });
                return links.slice(0, 10);
            }
        """)
        print(f"[搜图] 找到 {len(product_links)} 个商品")

        # 限流检测
        if len(product_links) == 0:
            body_text = (
                await page.inner_text("body") if await page.query_selector("body") else ""
            )
            if any(kw in body_text for kw in ["繁忙", "用量已达上限", "稍后重试"]):
                print("⚠️ 闲鱼限流了！请手动操作闲鱼或等待几小时后重试")
            else:
                print("⚠️ 未找到商品，可能是搜索无结果或账号异常")
            return []

        # ── 2. 评分排序 ──
        scored = [
            (score_title(p["title"], brand, model, category), p)
            for p in product_links
        ]
        scored.sort(key=lambda x: -x[0])

        print("[搜图] 评分结果:")
        for s, p in scored:
            if s == -999:
                tag = "❌坏机"
            elif s >= 40:
                tag = "✅候选"
            else:
                tag = "   噪音"
            print(f"  {tag} [{s:3d}] {p['title'][:60]}")

        candidates = [p for s, p in scored if s >= 40][:max_images]

        # ── 3. 访问详情页下载图片（共用一个 session）──
        async with aiohttp.ClientSession() as sess:
            for product in candidates:
                if len(downloaded) >= max_images:
                    break

                s = score_title(product["title"], brand, model, category)
                print(f"\n[搜图] 访问: {product['title'][:50]}... (score={s})")

                try:
                    await page.goto(product["href"], wait_until="domcontentloaded", timeout=30000)
                    # 滚动触发懒加载
                    await page.evaluate("window.scrollTo(0, 900)")
                    await asyncio.sleep(2)

                    # 从 DOM 提取商品图（自然宽 >= 400px）
                    img_infos = await page.evaluate("""
                        () => {
                            return Array.from(document.querySelectorAll("img"))
                                .filter(i => i.naturalWidth >= 400 && i.naturalHeight >= 300)
                                .map(i => ({src: i.src || "", w: i.naturalWidth, h: i.naturalHeight}))
                                .slice(0, 6);
                        }
                    """)
                    print(f"  发现 {len(img_infos)} 张商品图")

                    if not img_infos:
                        print("  ❌ 无有效商品图，跳过")
                        continue

                    for idx, ii in enumerate(img_infos):
                        if len(downloaded) >= max_images:
                            break
                        thumb = ii["src"]
                        if not thumb or "alicdn" not in thumb:
                            continue
                        # 第一张尝试大图，其余用原始尺寸
                        url = _thumb_to_full(thumb) if idx == 0 else thumb
                        fname = f"{keyword.replace(' ', '_')}_{timestamp}_{len(downloaded)+1}.jpg"
                        img_path = IMAGES_DIR / fname

                        ok, size_kb = await _download_image(sess, url, img_path)
                        if ok and size_kb >= 30:
                            print(f"  ✅ {fname} ({size_kb}KB)")
                            downloaded.append(str(img_path))
                        else:
                            # 缩略图兜底
                            ok2, size2 = await _download_image(sess, thumb, img_path)
                            if ok2 and size2 >= 15:
                                print(f"  ✅ {fname} 缩略图 ({size2}KB)")
                                downloaded.append(str(img_path))
                            else:
                                print(f"  ❌ 下载失败: {url[:60]}")

                    # 返回搜索页
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(1)

                except Exception as e:
                    print(f"  ❌ 异常: {e}")
                    try:
                        await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                    except Exception:
                        pass

        await browser.close()

    print(f"\n[搜图] 完成，下载 {len(downloaded)} 张图片")
    return downloaded
