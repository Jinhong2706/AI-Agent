from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod

import httpx

from config import WECOM_WEBHOOK_URL

logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    @abstractmethod
    async def send(self, content: str) -> bool:
        ...


class WeComNotifier(BaseNotifier):
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url or WECOM_WEBHOOK_URL
        self.client = httpx.AsyncClient(timeout=15)

    async def send(self, content: str) -> bool:
        if not self.webhook_url:
            logger.warning("企业微信Webhook未配置，跳过推送")
            return False
        try:
            payload = {
                "msgtype": "text",
                "text": {"content": content},
            }
            resp = await self.client.post(
                self.webhook_url,
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info("企业微信推送成功")
                return True
            else:
                logger.error("企业微信推送失败: %s", result)
                return False
        except Exception as e:
            logger.error("企业微信推送异常: %s", e)
            return False

    async def send_markdown(self, content: str) -> bool:
        if not self.webhook_url:
            logger.warning("企业微信Webhook未配置，跳过推送")
            return False
        try:
            payload = {
                "msgtype": "markdown",
                "markdown": {"content": content},
            }
            resp = await self.client.post(
                self.webhook_url,
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info("企业微信Markdown推送成功")
                return True
            else:
                logger.error("企业微信Markdown推送失败: %s", result)
                return False
        except Exception as e:
            logger.error("企业微信Markdown推送异常: %s", e)
            return False

    async def close(self):
        await self.client.aclose()


class ConsoleNotifier(BaseNotifier):
    async def send(self, content: str) -> bool:
        import sys
        import io
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        try:
            print(content)
        except UnicodeEncodeError:
            safe = content.encode('utf-8', errors='replace').decode('utf-8')
            print(safe)
        return True


class FileNotifier(BaseNotifier):
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir

    async def send(self, content: str) -> bool:
        import os
        from datetime import datetime

        os.makedirs(self.output_dir, exist_ok=True)
        filename = datetime.now().strftime("%Y-%m-%d_morning_brief.txt")
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("简报已保存到 %s", filepath)
            return True
        except Exception as e:
            logger.error("保存简报失败: %s", e)
            return False
