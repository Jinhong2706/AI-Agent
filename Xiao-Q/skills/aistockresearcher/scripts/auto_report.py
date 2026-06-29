#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化报告生成器
支持每日报告、周报、月报
"""
import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from core.cache_manager import CacheManager
from core.data_providers.stock_price import StockPriceProvider
from core.data_providers.akshare_provider import AkShareProvider
from core.agents import AnalystTeam


class AutoReportGenerator:
    """自动化报告生成器"""

    def __init__(self):
        self.cache = CacheManager()
        self.stock_provider = StockPriceProvider()
        self.akshare_provider = AkShareProvider(self.cache)
        self.analyst_team = AnalystTeam()

    def generate_daily_report(self, watchlist=None):
        """生成每日报告"""
        print("=" * 60)
        print("📊 每日投资报告")
        print(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'type': 'daily',
            'market_overview': {},
            'watchlist_analysis': [],
            'hot_sectors': [],
            'summary': ''
        }

        # 1. 市场概览
        print("\n📈 [1/4] 获取市场概览...")
        report['market_overview'] = self._get_market_overview()

        # 2. 自选股分析
        if watchlist:
            print(f"\n🔍 [2/4] 分析自选股 ({len(watchlist)}只)...")
            report['watchlist_analysis'] = self._analyze_watchlist(watchlist)
        else:
            print("\n🔍 [2/4] 无自选股，跳过...")

        # 3. 热门板块
        print("\n🔥 [3/4] 获取热门板块...")
        report['hot_sectors'] = self._get_hot_sectors()

        # 4. 生成摘要
        print("\n📝 [4/4] 生成投资摘要...")
        report['summary'] = self._generate_summary(report)

        return report

    def _get_market_overview(self):
        """获取市场概览"""
        overview = {
            'sh_index': {},
            'sz_index': {},
            'cy_index': {},
            'up_count': 0,
            'down_count': 0,
            'limit_up': 0,
            'limit_down': 0
        }

        try:
            # 获取主要指数
            indices = {
                'sh': '000001',  # 上证指数
                'sz': '399001',  # 深证成指
                'cy': '399006'   # 创业板指
            }

            for name, code in indices.items():
                quote = self.stock_provider.get(code)
                if quote.get('status') == 'success':
                    overview[f'{name}_index'] = {
                        'name': quote.get('name', ''),
                        'price': quote.get('price', 0),
                        'change_pct': quote.get('change_pct', 0)
                    }

        except Exception as e:
            print(f"获取市场概览失败: {e}")

        return overview

    def _analyze_watchlist(self, watchlist):
        """分析自选股"""
        results = []

        for code in watchlist:
            try:
                # 获取行情
                quote = self.stock_provider.get(code)

                if quote.get('status') == 'success':
                    # 分析师评估
                    analysis = self.analyst_team.analyze(code)

                    results.append({
                        'code': code,
                        'name': quote.get('name', ''),
                        'price': quote.get('price', 0),
                        'change_pct': quote.get('change_pct', 0),
                        'score': analysis.get('overall_score', 0),
                        'recommendation': analysis.get('recommendation', 'HOLD')
                    })
                else:
                    results.append({
                        'code': code,
                        'status': 'error',
                        'msg': quote.get('msg', '获取失败')
                    })

            except Exception as e:
                results.append({
                    'code': code,
                    'status': 'error',
                    'msg': str(e)
                })

        return results

    def _get_hot_sectors(self):
        """获取热门板块"""
        sectors = []

        try:
            # 使用akshare获取板块数据
            import akshare as ak

            # 获取行业板块
            df = ak.stock_board_industry_name_em()
            if not df.empty:
                # 按涨跌幅排序
                df = df.sort_values('涨跌幅', ascending=False)

                # 取前5个热门板块
                for _, row in df.head(5).iterrows():
                    sectors.append({
                        'name': row.get('板块名称', ''),
                        'change_pct': row.get('涨跌幅', 0),
                        'lead_stock': row.get('领涨股票', ''),
                        'lead_change': row.get('领涨股票-涨跌幅', 0)
                    })

        except Exception as e:
            print(f"获取热门板块失败: {e}")

        return sectors

    def _generate_summary(self, report):
        """生成投资摘要"""
        summary_parts = []

        # 市场概览
        market = report.get('market_overview', {})
        sh = market.get('sh_index', {})
        if sh:
            change = sh.get('change_pct', 0)
            if change > 0:
                summary_parts.append(f"上证指数上涨{change:.2f}%")
            elif change < 0:
                summary_parts.append(f"上证指数下跌{abs(change):.2f}%")
            else:
                summary_parts.append("上证指数持平")

        # 自选股表现
        watchlist = report.get('watchlist_analysis', [])
        if watchlist:
            up_count = sum(1 for s in watchlist if s.get('change_pct', 0) > 0)
            down_count = sum(1 for s in watchlist if s.get('change_pct', 0) < 0)
            summary_parts.append(f"自选股{up_count}涨{down_count}跌")

        # 热门板块
        sectors = report.get('hot_sectors', [])
        if sectors:
            hot = sectors[0].get('name', '')
            summary_parts.append(f"热门板块：{hot}")

        return "；".join(summary_parts) + "。"

    def save_report(self, report, output_dir=None):
        """保存报告"""
        if output_dir is None:
            output_dir = PROJECT_DIR / "reports"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        date_str = report.get('date', datetime.now().strftime('%Y-%m-%d'))
        report_type = report.get('type', 'daily')
        filename = f"{report_type}_report_{date_str}.json"

        # 保存JSON
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 报告已保存: {filepath}")

        # 生成Markdown版本
        md_content = self._to_markdown(report)
        md_filepath = output_dir / f"{report_type}_report_{date_str}.md"
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"📝 Markdown版本: {md_filepath}")

        return filepath

    def _to_markdown(self, report):
        """转换为Markdown格式"""
        md = f"""# {report.get('type', '每日').upper()}投资报告

**日期**: {report.get('date', '')}

---

## 📈 市场概览

"""

        market = report.get('market_overview', {})
        for index_name, index_data in market.items():
            if isinstance(index_data, dict) and 'name' in index_data:
                change = index_data.get('change_pct', 0)
                emoji = "🟢" if change >= 0 else "🔴"
                md += f"- {emoji} {index_data['name']}: {index_data.get('price', 0):.2f} ({change:+.2f}%)\n"

        md += "\n## 🔍 自选股分析\n\n"

        watchlist = report.get('watchlist_analysis', [])
        if watchlist:
            md += "| 代码 | 名称 | 价格 | 涨跌幅 | 评分 | 建议 |\n"
            md += "|------|------|------|--------|------|------|\n"

            for stock in watchlist:
                if stock.get('status') == 'error':
                    md += f"| {stock['code']} | - | - | - | - | {stock.get('msg', '错误')} |\n"
                else:
                    change = stock.get('change_pct', 0)
                    emoji = "🟢" if change >= 0 else "🔴"
                    md += f"| {stock['code']} | {stock.get('name', '')} | "
                    md += f"¥{stock.get('price', 0):.2f} | {emoji}{change:+.2f}% | "
                    md += f"{stock.get('score', 0)} | {stock.get('recommendation', '')} |\n"

        md += "\n## 🔥 热门板块\n\n"

        sectors = report.get('hot_sectors', [])
        if sectors:
            for sector in sectors:
                change = sector.get('change_pct', 0)
                emoji = "🟢" if change >= 0 else "🔴"
                md += f"- {emoji} {sector.get('name', '')}: {change:+.2f}% (领涨: {sector.get('lead_stock', '')})\n"

        md += f"\n## 📝 投资摘要\n\n{report.get('summary', '')}\n"

        return md


def main():
    """CLI入口"""
    parser = argparse.ArgumentParser(description='自动化报告生成器')
    parser.add_argument('--type', choices=['daily', 'weekly', 'monthly'],
                       default='daily', help='报告类型')
    parser.add_argument('--watchlist', nargs='+', help='自选股列表')
    parser.add_argument('--output', help='输出目录')

    args = parser.parse_args()

    generator = AutoReportGenerator()

    # 加载自选股
    watchlist = args.watchlist
    if not watchlist:
        # 尝试从配置文件加载
        config_path = PROJECT_DIR / "config" / "watchlist.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                watchlist = config.get('stocks', [])

    # 生成报告
    if args.type == 'daily':
        report = generator.generate_daily_report(watchlist)
    else:
        print(f"暂不支持 {args.type} 类型报告")
        return

    # 保存报告
    generator.save_report(report, args.output)

    # 打印摘要
    print("\n" + "=" * 60)
    print("📊 报告摘要")
    print("=" * 60)
    print(report.get('summary', ''))
    print("=" * 60)


if __name__ == "__main__":
    main()
