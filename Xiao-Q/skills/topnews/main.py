from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime

from collectors import (
    USStockCollector,
    FuturesCollector,
    CLSNewsCollector,
    MacroNewsCollector,
    CapitalFlowCollector,
)
from notifiers import WeComNotifier, ConsoleNotifier, FileNotifier
from report import ReportGenerator
from scheduler import Scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("morning_brief")


async def collect_all() -> dict:
    collectors = [
        USStockCollector(),
        FuturesCollector(),
        CLSNewsCollector(),
        MacroNewsCollector(),
        CapitalFlowCollector(),
    ]

    all_data = {}
    tasks = []
    for c in collectors:
        tasks.append(c.collect())

    results = await asyncio.gather(*tasks, return_exceptions=True)

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


async def generate_and_notify():
    all_data = await collect_all()

    generator = ReportGenerator()
    report = generator.generate(all_data)

    notifiers = [
        ConsoleNotifier(),
        FileNotifier(),
        WeComNotifier(),
    ]

    for notifier in notifiers:
        try:
            await notifier.send(report)
        except Exception as e:
            logger.error("推送失败 [%s]: %s", type(notifier).__name__, e)

    if isinstance(notifiers[-1], WeComNotifier):
        await notifiers[-1].close()

    logger.info("简报生成完成")
    return report


async def run_once():
    report = await generate_and_notify()
    return report


async def run_scheduled():
    sched = Scheduler(job_func=generate_and_notify)
    sched.start()
    logger.info("调度模式启动，按 Ctrl+C 退出")
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        sched.stop()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        asyncio.run(run_once())
    elif len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        asyncio.run(run_scheduled())
    else:
        print("用法:")
        print("  python main.py --now       立即执行一次")
        print("  python main.py --schedule  启动定时调度")
        print()
        print("默认执行一次...")
        asyncio.run(run_once())


if __name__ == "__main__":
    main()
