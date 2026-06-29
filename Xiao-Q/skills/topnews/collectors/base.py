from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

from config import REQUEST_HEADERS, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    category: str
    items: list[dict[str, Any]] = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "items": self.items,
            "fetched_at": self.fetched_at,
        }


class BaseCollector(ABC):
    category: str = ""

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )

    async def close(self):
        await self.client.aclose()

    @abstractmethod
    async def collect(self) -> MarketData:
        ...

    async def _get(self, url: str, params: dict | None = None, **kwargs) -> str:
        try:
            resp = await self.client.get(url, params=params, **kwargs)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.error("[%s] 请求失败 %s: %s", self.category, url, e)
            return ""

    async def _get_json(self, url: str, params: dict | None = None, **kwargs) -> Any:
        try:
            resp = await self.client.get(url, params=params, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("[%s] 请求JSON失败 %s: %s", self.category, url, e)
            return None
