"""
闲鱼回收发布 - 全自动流程
用法:
    python main.py "小米12"
    python main.py "小米12 99新 2500"
    python main.py "iPhone 15 Pro"
"""
import asyncio
import sys
import argparse
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from product_info import auto_fill, describe_product
from get_product_images import get_product_images
from publish import publish


async def main(raw_input: str):
    print("=" * 50)
    print("闲鱼回收发布 - 全自动流程")
    print("=" * 50)

    # ── 1. 解析 + 补全 ──
    print(f"\n📦 输入: {raw_input}")
    info = auto_fill(raw_input)
    print(f"\n✅ 自动补全:")
    print(describe_product(info))

    # 搜索关键词（避免 "小米 小米 12" → "小米12"）
    brand, model = info["brand"], info["model"]
    kw_raw = f"{brand} {model}"
    if kw_raw.startswith(f"{brand} {brand}"):
        kw_raw = f"{brand}{model.replace(brand, '')}"

    # ── 2. 搜索商品图片 ──
    print(f"\n🔍 搜索图片: {kw_raw}")
    images = await get_product_images(
        keyword=kw_raw,
        max_images=3,
        brand=brand,
        model=model,
        category=info["category"],
        skip_validation=False,
    )

    # 无图片 → 降级重试（跳过 AI 验证）
    if not images:
        print("\n⚠️ 未找到图片，降级重试（跳过验证）...")
        images = await get_product_images(
            keyword=kw_raw,
            max_images=3,
            brand=brand,
            model=model,
            category=info["category"],
            skip_validation=True,
        )

    if not images:
        print("❌ 没有可用图片，无法发布！")
        return

    print(f"\n📸 使用图片: {images}")

    # ── 3. 发布 ──
    print(f"\n🚀 开始发布...")
    try:
        ok = await publish(
            brand=brand,
            model=model,
            price=info["sell_price"],
            condition=info["condition"],
            images=images,
        )
    except Exception as exc:
        print(f"❌ 发布异常: {exc}")
        import traceback
        traceback.print_exc()
        return

    if ok:
        print("\n🎉 发布成功!")
    else:
        print("\n❌ 发布失败")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="闲鱼回收发布")
    parser.add_argument("keyword", nargs="+", help="商品描述，如: 小米12 99新 2500")
    args = parser.parse_args()
    asyncio.run(main(" ".join(args.keyword)))
