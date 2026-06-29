#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_utils.py  ——  QQ 机器人通用工具函数
"""

import asyncio
from typing import Dict


def parse_cmd(content: str) -> str:
    """
    去除频道消息中的 @mention 前缀（如 <@!12345>），返回纯指令文本。
    频道消息内容格式通常为：'<@!botid> 你好'
    C2C / 群消息不含此前缀，直接传入无影响。
    """
    parts = content.strip().split()
    filtered = [p for p in parts if not p.startswith("<@")]
    return " ".join(filtered).strip()


class SubscriptionManager:
    """
    通用订阅管理器，维护 key -> asyncio.Task 的映射。
    key 可以是 user_id / user_openid / group_openid 等任意字符串。
    """

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        # 可存储任意附加数据（如 msg_id / channel_id）
        self._meta: Dict[str, str] = {}

    def is_subscribed(self, key: str) -> bool:
        return key in self._tasks

    def subscribe(self, key: str, task: asyncio.Task, meta: str = ""):
        self._tasks[key] = task
        self._meta[key] = meta

    def unsubscribe(self, key: str) -> bool:
        task = self._tasks.pop(key, None)
        self._meta.pop(key, None)
        if task:
            task.cancel()
            return True
        return False

    def get_meta(self, key: str, default: str = "") -> str:
        return self._meta.get(key, default)

    def update_meta(self, key: str, meta: str):
        if key in self._tasks:
            self._meta[key] = meta
