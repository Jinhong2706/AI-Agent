#!/usr/bin/env python3
"""
基金实时估值抓取工具
====================
通过 Playwright 自动化访问同花顺基金页面，抓取基金重仓持股数据，
基于持仓股票的实时涨跌幅加权计算基金的预计涨跌幅度。

数据来源：同花顺爱基金 (fund.10jqka.com.cn)

用法:
    # 查询单只基金
    python fund_scraper.py --code 519674

    # 批量查询多只基金
    python fund_scraper.py --codes 519674,002190,161725

    # 输出 JSON 格式
    python fund_scraper.py --code 519674 --format json

    # 自定义输出路径
    python fund_scraper.py --codes 519674,002190 --output result.json
"""

import asyncio
import argparse
import json
import sys
import os
import random
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any

try:
    from playwright_stealth import Stealth
    _STEALTH_INSTANCE = Stealth()
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("[WARNING] playwright-stealth 未安装，已跳过反检测功能。pip install playwright-stealth 以提升抓取成功率。")

# Windows 控制台 UTF-8 编码兼容
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


# ============================================================
# 数据模型
# ============================================================

@dataclass
class StockHolding:
    """重仓持股数据"""
    序号: int
    股票名称: str
    日涨幅: float          # 百分比数值，如 1.06 表示 +1.06%
    占净资产比: float      # 百分比数值，如 9.78 表示 9.78%
    市值: float            # 单位：万元


@dataclass
class FundRealtimeData:
    """基金实时数据"""
    基金代码: str
    基金名称: str = ""
    抓取时间: str = ""
    重仓持股: List[StockHolding] = field(default_factory=list)
    预计涨跌幅: Optional[float] = None   # 加权平均后的预计涨跌幅（%）
    状态: str = "success"                 # success / partial / error
    错误信息: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "基金代码": self.基金代码,
            "基金名称": self.基金名称,
            "抓取时间": self.抓取时间,
            "预计涨跌幅": round(self.预计涨跌幅, 2) if self.预计涨跌幅 is not None else None,
            "状态": self.状态,
            "重仓持股": [
                {
                    "序号": s.序号,
                    "股票名称": s.股票名称,
                    "日涨幅": f"{s.日涨幅:+.2f}%",
                    "占净资产比": f"{s.占净资产比:.2f}%",
                    "市值": f"{s.市值:.2f}万元"
                } for s in self.重仓持股
            ]
        }
        if self.错误信息:
            d["错误信息"] = self.错误信息
        return d


# ============================================================
# 核心抓取逻辑
# ============================================================

async def scrape_fund_realtime(
    page,
    fund_code: str,
    timeout: int = 60000,
    render_wait: float = 5.0,
    max_retries: int = 3,
    base_delay: float = 2.0,
) -> FundRealtimeData:
    """
    抓取单只基金的实时估值数据。

    通过访问同花顺基金页面，提取：
    - 基金名称
    - 重仓持股明细（股票名、日涨幅、占净资产比、市值）
    - 基于加权算法计算预计涨跌幅

    Args:
        page: Playwright 页面对象
        fund_code: 基金代码（6位数字）
        timeout: 页面加载超时（毫秒）
        render_wait: JS 渲染等待时间（秒）

    Returns:
        FundRealtimeData 对象，包含完整的基金实时估值数据
    """

    url = f"https://fund.10jqka.com.cn/{fund_code}/"
    result = FundRealtimeData(
        基金代码=fund_code,
        抓取时间=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # ---- 反爬重试循环 ----
    last_error = ""
    for attempt in range(1, max_retries + 1):
        try:
            # 访问页面（每次重试刷新页面，避免缓存）
            await page.goto(url, wait_until='networkidle', timeout=timeout)

            # 等待 JavaScript 动态渲染完成
            await asyncio.sleep(render_wait)

            # ---- 检测 403 拦截 ----
            page_title = await page.title()
            page_content = await page.content()
            if "403" in page_title or "Forbidden" in page_title or "访问被拒绝" in page_content:
                raise Exception("403_FORBIDDEN")

            # ---- 检测"服务异常"或反爬页面 ----
            body_text = await page.inner_text('body')
            if any(keyword in body_text for keyword in ["访问频率", "请输入验证码", "系统繁忙", "too many requests"]):
                raise Exception("RATE_LIMITED")

            # ---- 提取基金名称 ----
            fund_name = await extract_fund_name(page)
            if not fund_name:
                result.基金名称 = f"未知基金({fund_code})"
                result.状态 = "partial"
            else:
                result.基金名称 = fund_name

            # ---- 提取重仓持股数据 ----
            holdings = await extract_holdings(page)
            if holdings:
                result.重仓持股 = holdings
            else:
                result.状态 = "partial"
                result.错误信息 = "未能提取到重仓持股数据"

            # ---- 计算预计涨跌幅（加权平均） ----
            if holdings:
                estimated_change = calculate_weighted_change(holdings)
                result.预计涨跌幅 = estimated_change

            # 成功，跳出重试循环
            break

        except asyncio.TimeoutError:
            last_error = f"页面加载超时 ({timeout//1000}秒)"
            result.状态 = "error"
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0.5, 2)
                print(f"  ⏎ 第 {attempt}/{max_retries} 次尝试超时，等待 {delay:.1f}s 后重试...")
                await asyncio.sleep(delay)
            else:
                result.错误信息 = last_error

        except Exception as e:
            error_msg = str(e)
            if error_msg in ("403_FORBIDDEN", "RATE_LIMITED"):
                last_error = "403 Forbidden / 访问频率限制（反爬拦截）"
                result.状态 = "error"
                if attempt < max_retries:
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(1.0, 3.0)
                    print(f"  ⛔ 被拦截（{error_msg}），第 {attempt}/{max_retries} 次重试，"
                          f"等待 {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    # 重试前刷新页面
                    await page.reload(wait_until='networkidle', timeout=timeout)
                    await asyncio.sleep(render_wait)
                else:
                    result.错误信息 = last_error
            else:
                last_error = error_msg
                result.状态 = "error"
                if attempt < max_retries:
                    delay = base_delay + random.uniform(0.5, 1.5)
                    print(f"  ⏎ 错误: {error_msg}，第 {attempt}/{max_retries} 次重试...")
                    await asyncio.sleep(delay)
                else:
                    result.错误信息 = last_error

    return result


# ============================================================
# 数据提取函数
# ============================================================

async def extract_fund_name(page) -> str:
    """从页面提取基金名称。按优先级尝试多个选择器。"""

    selectors = [
        '.name',           # 同花顺主选择器（优先）
        'h1',              # 备用：h1 标签
        '.fund-name',
        '.title'
    ]

    for selector in selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                text = (await element.inner_text()).strip()
                # 过滤掉太短或明显不是基金名的文本
                if text and len(text) >= 2 and text not in ['热点推荐']:
                    return text
        except Exception:
            continue

    return ""


async def extract_holdings(page) -> List[StockHolding]:
    """
    从同花顺基金页面提取重仓持股数据。

    DOM 结构（已验证 2026-04）：
        <div id="czContent">
            <ul>
                <li>序号</li>
                <li>股票名称</li>
                <li>日涨幅</li>
                <li>占净资产比</li>
                <li>市值/万元</li>
            </ul>
            ...（后续每支股票一行）
        </div>

    Returns:
        StockHolding 列表
    """

    holdings: List[StockHolding] = []

    try:
        # 等待持仓容器出现
        try:
            await page.wait_for_selector('#czContent ul', timeout=15000)
        except Exception:
            # 尝试备用等待策略
            await page.wait_for_selector('.c-zstroe, .cartogram, [id*="cz"]', timeout=10000)

        # 使用 JavaScript 在浏览器中高效提取数据
        raw_data = await page.evaluate('''() => {
            const results = [];
            const container = document.querySelector('#czContent');
            if (!container) return results;

            const rows = container.querySelectorAll('ul');
            let rowIndex = 0;
            rows.forEach((row) => {
                const cells = row.querySelectorAll('li');

                // 跳过表头行（第一行的文本通常是标题）
                if (cells.length >= 5) {
                    const seqText = cells[0].innerText.trim();
                    // 表头检测：表头行的第一个单元格是"序号"
                    if (seqText === '序号' || seqText === '股票名称') {
                        return;  // 跳过表头
                    }

                    const seq = parseInt(seqText);
                    const stockName = cells[1].innerText.trim();
                    const changeText = cells[2].innerText.trim();     // 如 "+1.06%" 或 "-2.3%"
                    const ratioText = cells[3].innerText.trim();       // 如 "9.78%"
                    const valueText = cells[4].innerText.trim();       // 如 "138266.10"

                    // 解析日涨幅百分比
                    let dayChange = parseFloat(changeText.replace('%', ''));
                    if (isNaN(dayChange)) dayChange = 0;

                    // 解析占净资产比
                    let ratio = parseFloat(ratioText.replace('%', ''));
                    if (isNaN(ratio)) ratio = 0;

                    // 解析市值
                    let value = parseFloat(valueText.replace(/,/g, ''));
                    if (isNaN(value)) value = 0;

                    results.push({
                        序号: seq || (rowIndex + 1),
                        股票名称: stockName,
                        日涨幅: dayChange,
                        占净资产比: ratio,
                        市值: value
                    });
                    rowIndex++;
                }
            });
            return results;
        }''')

        # 转换为 StockHolding 对象
        for item in raw_data:
            holdings.append(StockHolding(
                序号=item['序号'],
                股票名称=item['股票名称'],
                日涨幅=item['日涨幅'],
                占净资产比=item['占净资产比'],
                市值=item['市值']
            ))

    except Exception as e:
        print(f"[WARNING] 提取持仓数据时出错: {e}")

    return holdings


def calculate_weighted_change(holdings: List[StockHolding]) -> Optional[float]:
    """
    基于重仓持股计算基金的预计涨跌幅。

    算法：以各股票的「占净资产比」为权重，
         加权平均各股票的「日涨幅」得到预计涨跌幅。

    公式：Σ(股票日涨幅 × 占净资产比) / Σ(占净资产比)

    Args:
        holdings: 重仓持股列表

    Returns:
        预计涨跌幅（%），None 表示无法计算
    """

    if not holdings:
        return None

    total_weight = 0.0
    weighted_sum = 0.0

    for stock in holdings:
        weight = stock.占净资产比
        change = stock.日涨幅
        weighted_sum += change * weight
        total_weight += weight

    if total_weight == 0:
        return None

    estimated = weighted_sum / total_weight
    return round(estimated, 4)


# ============================================================
# 批量查询
# ============================================================

async def scrape_funds_batch(
    fund_codes: List[str],
    headless: bool = True,
    output_format: str = "table",
    output_file: Optional[str] = None,
    max_retries: int = 3,
) -> List[FundRealtimeData]:
    """
    批量查询多只基金的实时估值。

    Args:
        fund_codes: 基金代码列表
        headless: 是否无头模式运行浏览器
        output_format: 输出格式 ('table' | 'json')
        output_file: 输出文件路径（可选）
        max_retries: 单只基金最大重试次数（默认3次）

    Returns:
        基金实时数据列表
    """
    from playwright.async_api import async_playwright

    results: List[FundRealtimeData] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)

        try:
            for idx, code in enumerate(fund_codes):
                code = code.strip()

                # 基金间随机间隔（1~3秒），避免批量请求触发风控
                if idx > 0:
                    gap = random.uniform(3.0, 6.0)
                    print(f"\n  💤 间隔 {gap:.1f}s 后继续...")
                    await asyncio.sleep(gap)

                # 创建新页面上下文（隔离环境）
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 2000},
                    user_agent=(
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/124.0.0.0 Safari/537.36'
                    ),
                    extra_http_headers={
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                        "Accept": (
                            "text/html,application/xhtml+xml,application/xml;"
                            "q=0.9,image/avif,image/webp,*/*;q=0.8"
                        ),
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Cache-Control": "max-age=0",
                    }
                )
                page = await context.new_page()

                # ---- 应用 stealth 模式：绕过 headless 检测 ----
                if STEALTH_AVAILABLE:
                    await _STEALTH_INSTANCE.apply_stealth_async(page)
                else:
                    print("[HINT] pip install playwright-stealth 可进一步提升抓取成功率")

                print(f"正在查询 {code}...", end=" ", flush=True)
                data = await scrape_fund_realtime(
                    page,
                    code,
                    max_retries=max_retries,
                )
                results.append(data)

                status_icon = "✅" if data.状态 == "success" else ("⚠️" if data.状态 == "partial" else "❌")
                change_str = f"{data.预计涨跌幅:+.2f}%" if data.预计涨跌幅 is not None else "N/A"
                print(f"{status_icon} {data.基金名称} → 预计涨跌幅: {change_str}")

                await context.close()

        finally:
            await browser.close()

    # ---- 输出结果 ----
    _print_results(results, output_format)

    # ---- 可选：保存到文件 ----
    if output_file:
        save_results(results, output_file)
        print(f"\n💾 结果已保存至: {output_file}")

    return results


# ============================================================
# 格式化输出
# ============================================================

def _print_results(results: List[FundRealtimeData], fmt: str):
    """格式化输出结果。"""

    if fmt == "json":
        output = [r.to_dict() for r in results]
        print("\n" + json.dumps(output, ensure_ascii=False, indent=2))
        return

    # 表格格式（默认）
    print("\n" + "=" * 80)
    print(f"{'基金代码':<10} {'基金名称':<18} {'预计涨跌幅':<12} {'状态':<8} {'持仓数':<6}")
    print("=" * 80)

    for r in results:
        change_str = f"{r.预计涨跌幅:+.2f}%" if r.预计涨跌幅 is not None else "N/A"
        status_map = {"success": "✅正常", "partial": "⚠️部分", "error": "❌失败"}
        print(
            f"{r.基金代码:<10} "
            f"{r.基金名称:<18} "
            f"{change_str:<12} "
            f"{status_map.get(r.状态, r.状态):<8} "
            f"{len(r.重仓持股):<6}"
        )

    print("=" * 80)

    # 详细持仓信息
    for r in results:
        if r.重仓持股 and r.状态 != "error":
            print(f"\n📊 {r.基金名称}({r.基金代码}) 重仓持股明细:")
            print(f"  {'序号':<5}{'股票名称':<10}{'日涨幅':<10}{'占比':<8}{'市值(万)':<12}")
            print(f"  {'─'*45}")
            for s in r.重仓持股:
                change_color = "+" if s.日涨幅 >= 0 else ""
                print(
                    f"  {s.序号:<5}"
                    f"{s.股票名称:<10}"
                    f"{change_color}{s.日涨幅:.2f}%{'':<6}"
                    f"{s.占净资产比:.2f}%{'':<4}"
                    f"{s.市值:>12.2f}"
                )


def save_results(results: List[FundRealtimeData], filepath: str):
    """将结果保存为 JSON 文件。"""
    data = [r.to_dict() for r in results]

    # 确保目录存在
    dir_path = os.path.dirname(filepath)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='基金实时估值抓取工具 — 从同花顺抓取基金持仓并计算预计涨跌幅',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --code 519674
  %(prog)s --codes 519674,002190,161725,161726
  %(prog)s --codes 519674,002190 --format json
  %(prog)s --code 519674 --output my_funds.json
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--code', '-c', type=str, help='单只基金代码（6位）')
    group.add_argument('--codes', type=str, help='多只基金代码，逗号分隔')

    parser.add_argument('--format', '-f', choices=['table', 'json'], default='table',
                        help='输出格式（默认：table）')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出文件路径（JSON格式）')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='无头模式（默认开启）')
    parser.add_argument('--no-headless', dest='headless', action='store_false',
                        help='显示浏览器窗口（调试用）')
    parser.add_argument('--timeout', type=int, default=60000,
                        help='页面加载超时毫秒数（默认：60000）')
    parser.add_argument('--max-retries', type=int, default=3,
                        help='单只基金最大重试次数（默认：3）')

    args = parser.parse_args()

    # 解析基金代码列表
    if args.code:
        fund_codes = [args.code]
    else:
        fund_codes = [c.strip() for c in args.codes.split(',')]

    # 校验基金代码格式
    for code in fund_codes:
        if not code.isdigit() or len(code) != 6:
            print(f"⚠️ 无效的基金代码: {code}（应为6位数字）")
            sys.exit(1)

    # 运行批量查询
    results = asyncio.run(scrape_funds_batch(
        fund_codes=fund_codes,
        headless=args.headless,
        output_format=args.format,
        output_file=args.output or (f'fund_result_{"_".join(fund_codes)}.json' if len(fund_codes) > 1 else f'fund_{fund_codes[0]}_result.json'),
        max_retries=args.max_retries,
    ))

    # 返回退出码
    error_count = sum(1 for r in results if r.状态 == 'error')
    sys.exit(min(error_count, 1))


if __name__ == '__main__':
    main()
