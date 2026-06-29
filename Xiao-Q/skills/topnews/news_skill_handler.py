# -*- coding: utf-8 -*-
"""
news-product-stock 舆情分析技能入口

Actions:
  run_now       - 完整执行：采集→分析→生成简报→推送
  pre_market    - 盘前分析（05:00-09:25）
  intraday      - 盘中分析（09:30-15:00）
  midday        - 午盘分析（11:30-13:00）
  after_market  - 盘后分析（15:00-次日盘前）
  weekend       - 周末分析
  holiday       - 假日分析
  collect       - 仅采集原始数据，返回 JSON
  help          - 返回可用 actions 列表
"""
import sys
import os
import asyncio
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("news_product_stock.skill")

PERIOD_MAP = {
    "run_now": "pre_market",
    "pre_market": "pre_market",
    "intraday": "intraday",
    "midday": "midday",
    "after_market": "after_market",
    "weekend": "weekend",
    "holiday": "holiday",
}

PERIOD_INFO = {
    "pre_market": {"name": "盘前", "time": "05:00-09:25", "focus": "开盘预测、隔夜消息消化"},
    "intraday": {"name": "盘中", "time": "09:30-15:00", "focus": "实时舆情、盘中动态"},
    "midday": {"name": "午盘", "time": "11:30-13:00", "focus": "上午复盘、下午前瞻"},
    "after_market": {"name": "盘后", "time": "15:00-次日盘前", "focus": "次日预判、龙虎榜"},
    "weekend": {"name": "周末", "time": "周六周日", "focus": "下周策略制定"},
    "holiday": {"name": "假日", "time": "法定节假日", "focus": "节后策略规划"},
}


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, coro).result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)


async def _collect_all():
    from collectors import (
        USStockCollector,
        FuturesCollector,
        CLSNewsCollector,
        MacroNewsCollector,
        CapitalFlowCollector,
    )
    collectors = [
        USStockCollector(),
        FuturesCollector(),
        CLSNewsCollector(),
        MacroNewsCollector(),
        CapitalFlowCollector(),
    ]
    tasks = [c.collect() for c in collectors]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_data = {}
    for c, result in zip(collectors, results):
        if isinstance(result, Exception):
            logger.error("[%s] 采集异常: %s", c.category, result)
            all_data[c.category] = []
        else:
            all_data[c.category] = result.items
            logger.info("[%s] 采集完成, %d 条数据", c.category, len(result.items))
    for c in collectors:
        await c.close()
    return all_data


def _execute_report(action: str, period: str) -> dict:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        all_data = _run_async(_collect_all())
        from report import ReportGenerator
        generator = ReportGenerator()
        report = generator.generate(all_data, period=period)

        from notifiers import ConsoleNotifier, FileNotifier, WeComNotifier

        console = ConsoleNotifier()
        fnotifier = FileNotifier()
        wecom = WeComNotifier()

        async def _notify():
            await console.send(report)
            await fnotifier.send(report)
            await wecom.send(report)
            await wecom.close()
        _run_async(_notify())

        data_summary = {k: len(v) for k, v in all_data.items()}

        verdict_line = ""
        for line in report.split('\n'):
            if line.startswith('🎯'):
                verdict_line = line
                break

        return {
            'success': True,
            'action': action,
            'period': period,
            'timestamp': timestamp,
            'report': report,
            'data_summary': data_summary,
            'verdict': verdict_line,
            'total_items': sum(data_summary.values()),
        }
    except Exception as e:
        logger.error("%s 执行失败: %s", action, e, exc_info=True)
        return {
            'success': False,
            'action': action,
            'timestamp': timestamp,
            'error': str(e),
        }


def skill_handler(params: dict) -> dict:
    action = params.get('action', 'help')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if action in PERIOD_MAP:
        period = PERIOD_MAP[action]
        return _execute_report(action, period)

    elif action == 'collect':
        try:
            all_data = _run_async(_collect_all())
            data_summary = {k: len(v) for k, v in all_data.items()}
            return {
                'success': True,
                'action': 'collect',
                'timestamp': timestamp,
                'data': all_data,
                'data_summary': data_summary,
                'total_items': sum(data_summary.values()),
            }
        except Exception as e:
            logger.error("collect 执行失败: %s", e, exc_info=True)
            return {
                'success': False,
                'action': 'collect',
                'timestamp': timestamp,
                'error': str(e),
            }

    elif action == 'help':
        period_actions = []
        for key, period in PERIOD_MAP.items():
            info = PERIOD_INFO[period]
            period_actions.append({
                'name': key,
                'description': f"{info['name']}分析（{info['time']}）- {info['focus']}",
                'params': [],
            })
        return {
            'success': True,
            'action': 'help',
            'skill_name': 'news-product-stock',
            'version': '2.0.0',
            'description': '全时段舆情分析：量化情感评分+板块关联+操作建议，支持盘前/盘中/午盘/盘后/周末/假日',
            'available_actions': period_actions + [
                {
                    'name': 'collect',
                    'description': '仅采集原始数据，返回 JSON 格式，不生成报告不推送',
                    'params': [],
                },
                {
                    'name': 'help',
                    'description': '显示帮助信息',
                    'params': [],
                },
            ],
            'analysis_features': [
                '情感量化（连续量表 -1.0 ~ +1.0）',
                '重要性评估（1-10分，含事件级别+来源+紧迫度+时效）',
                '板块关联（自动映射利好/利空板块）',
                '操作建议（保守型/稳健型/激进型）',
                '紧急警报（高影响事件自动提醒）',
            ],
            'data_sources': [
                '东方财富 API (美股指数/期货行情)',
                '新浪财经 (行情备用源)',
                '财联社 API (7×24电报快讯)',
                '新浪 Feed (国际财经新闻)',
                'akshare/Tushare (北向资金)',
            ],
            'config_file': '.env',
        }

    else:
        return {
            'success': False,
            'action': action,
            'timestamp': timestamp,
            'error': f'未知 action: {action}',
            'available_actions': list(PERIOD_MAP.keys()) + ['collect', 'help'],
        }


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='全时段舆情分析技能')
    parser.add_argument('--now', action='store_true', help='立即执行盘前分析')
    parser.add_argument('--period', type=str, default=None,
                        choices=['pre_market', 'intraday', 'midday', 'after_market', 'weekend', 'holiday'],
                        help='指定分析时段')
    parser.add_argument('--collect', action='store_true', help='仅采集数据')
    args = parser.parse_args()

    if args.now:
        r = skill_handler({'action': 'run_now'})
    elif args.period:
        r = skill_handler({'action': args.period})
    elif args.collect:
        r = skill_handler({'action': 'collect'})
    else:
        r = skill_handler({'action': 'help'})
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0)

    print(r.get('report', json.dumps(r, ensure_ascii=False, indent=2)))
