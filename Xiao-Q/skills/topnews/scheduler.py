from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import REPORT_TIME

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, job_func, report_time: str = ""):
        self.job_func = job_func
        time_str = report_time or REPORT_TIME
        parts = time_str.split(":")
        self.hour = int(parts[0]) if len(parts) > 0 else 6
        self.minute = int(parts[1]) if len(parts) > 1 else 30
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.add_job(
            self._wrapped_job,
            CronTrigger(hour=self.hour, minute=self.minute),
            id="morning_brief",
            replace_existing=True,
        )
        logger.info("定时任务已注册: 每天 %02d:%02d 执行", self.hour, self.minute)
        self.scheduler.start()
        logger.info("调度器已启动")

    def stop(self):
        self.scheduler.shutdown()
        logger.info("调度器已停止")

    async def _wrapped_job(self):
        logger.info("开始执行早盘简报任务...")
        try:
            await self.job_func()
            logger.info("早盘简报任务完成")
        except Exception as e:
            logger.error("早盘简报任务失败: %s", e, exc_info=True)

    async def run_once(self):
        logger.info("手动执行一次早盘简报任务...")
        await self._wrapped_job()
