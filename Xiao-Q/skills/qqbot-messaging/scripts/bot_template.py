#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_template.py  ——  QQ 机器人完整模板

使用方法：
  1. 复制此文件到你的项目
  2. 实现 handle_command() 函数，替换其中的业务逻辑
  3. 修改 config.yaml 填入 appid / secret
  4. pip install qq-botpy
  5. python bot_template.py

支持三种消息场景：
  - 频道 @ 消息（on_at_message_create）
  - C2C 私聊消息（on_c2c_message_create）
  - 群 @ 消息（on_group_at_message_create）
"""

import asyncio
import os

import botpy
from botpy import logging
from botpy.message import Message, C2CMessage, GroupMessage
from botpy.ext.cog_yaml import read

_log = logging.get_logger()

# ──────────────────────────────────────────────
# 订阅管理（key -> asyncio.Task + meta）
# ──────────────────────────────────────────────
_guild_sub: dict[str, str] = {}   # user_id -> channel_id
_guild_tasks: dict[str, asyncio.Task] = {}

_c2c_sub: dict[str, str] = {}     # user_openid -> last_msg_id
_c2c_tasks: dict[str, asyncio.Task] = {}

_group_sub: dict[str, str] = {}   # group_openid -> last_msg_id
_group_tasks: dict[str, asyncio.Task] = {}

PUSH_INTERVAL = 3600  # 推送间隔（秒）


# ──────────────────────────────────────────────
# 业务逻辑入口：替换为你的实现
# ──────────────────────────────────────────────
def handle_command(cmd: str) -> str | None:
    """
    根据指令文本返回回复内容。
    返回 None 表示不处理（由调用方决定是否发帮助文本）。

    示例：
      "查询行情" -> 返回行情字符串
      "开始订阅" -> 返回 None（由框架处理订阅逻辑）
    """
    if "查询" in cmd or "行情" in cmd:
        return "这里返回你的业务数据"
    return None


def get_push_content() -> str:
    """定时推送时调用，返回要推送的内容。"""
    return "这里是定时推送内容"


HELP_TEXT = (
    "支持以下指令：\n"
    "• 开始订阅 —— 定时推送\n"
    "• 取消订阅 —— 停止推送\n"
    "• 查询行情 —— 立即查询"
)


def parse_cmd(content: str) -> str:
    """去除频道消息的 @mention 前缀"""
    parts = content.strip().split()
    return " ".join(p for p in parts if not p.startswith("<@")).strip()


# ──────────────────────────────────────────────
# Bot 主体
# ──────────────────────────────────────────────
class MyBot(botpy.Client):

    async def on_ready(self):
        _log.info(f"[Bot] {self.robot.name} 已上线")

    # ── 频道 @ 消息 ─────────────────────────
    async def on_at_message_create(self, message: Message):
        user_id = message.author.id
        channel_id = message.channel_id
        cmd = parse_cmd(message.content)
        _log.info(f"[频道] user={user_id} cmd={cmd!r}")

        if "开始订阅" in cmd:
            if user_id in _guild_sub:
                await message.reply(content="您已订阅。")
                return
            _guild_sub[user_id] = channel_id
            _guild_tasks[user_id] = asyncio.create_task(
                self._guild_push(user_id, channel_id, message)
            )
            await message.reply(content="订阅成功！")

        elif "取消订阅" in cmd or "停止订阅" in cmd:
            if user_id not in _guild_sub:
                await message.reply(content="您尚未订阅。")
                return
            t = _guild_tasks.pop(user_id, None)
            if t:
                t.cancel()
            _guild_sub.pop(user_id)
            await message.reply(content="已取消订阅。")

        else:
            reply = handle_command(cmd)
            await message.reply(content=reply or HELP_TEXT)

    async def _guild_push(self, user_id: str, channel_id: str, message: Message):
        try:
            while True:
                await asyncio.sleep(PUSH_INTERVAL)
                if user_id not in _guild_sub:
                    break
                content = get_push_content()
                _log.info(f"[频道推送] -> user={user_id}")
                try:
                    await self.api.post_message(
                        channel_id=channel_id,
                        content=f"<@{user_id}>\n{content}",
                        msg_id=message.id,
                    )
                except Exception as e:
                    _log.error(f"[频道推送] 失败: {e}")
        except asyncio.CancelledError:
            pass

    # ── C2C 私聊 ────────────────────────────
    async def on_c2c_message_create(self, message: C2CMessage):
        openid = message.author.user_openid
        cmd = message.content.strip()
        _log.info(f"[C2C] openid={openid} cmd={cmd!r}")

        async def reply(text: str):
            await message._api.post_c2c_message(
                openid=openid, msg_type=0, msg_id=message.id, content=text
            )

        if "开始订阅" in cmd:
            if openid in _c2c_sub:
                await reply("您已订阅。")
                return
            _c2c_sub[openid] = message.id
            _c2c_tasks[openid] = asyncio.create_task(self._c2c_push(openid, message))
            await reply("订阅成功！")

        elif "取消订阅" in cmd or "停止订阅" in cmd:
            if openid not in _c2c_sub:
                await reply("您尚未订阅。")
                return
            t = _c2c_tasks.pop(openid, None)
            if t:
                t.cancel()
            _c2c_sub.pop(openid)
            await reply("已取消订阅。")

        else:
            result = handle_command(cmd)
            await reply(result or HELP_TEXT)

    async def _c2c_push(self, openid: str, message: C2CMessage):
        try:
            while True:
                await asyncio.sleep(PUSH_INTERVAL)
                if openid not in _c2c_sub:
                    break
                content = get_push_content()
                _log.info(f"[C2C推送] -> openid={openid}")
                try:
                    await message._api.post_c2c_message(
                        openid=openid, msg_type=0,
                        msg_id=_c2c_sub.get(openid, message.id),
                        content=content,
                    )
                except Exception as e:
                    _log.error(f"[C2C推送] 失败: {e}")
        except asyncio.CancelledError:
            pass

    # ── 群 @ 消息 ────────────────────────────
    async def on_group_at_message_create(self, message: GroupMessage):
        group_openid = message.group_openid
        cmd = message.content.strip()
        _log.info(f"[群] group={group_openid} cmd={cmd!r}")

        async def reply(text: str):
            await message._api.post_group_message(
                group_openid=group_openid, msg_type=0, msg_id=message.id, content=text
            )

        if "开始订阅" in cmd:
            if group_openid in _group_sub:
                await reply("本群已订阅。")
                return
            _group_sub[group_openid] = message.id
            _group_tasks[group_openid] = asyncio.create_task(
                self._group_push(group_openid, message)
            )
            await reply("订阅成功！")

        elif "取消订阅" in cmd or "停止订阅" in cmd:
            if group_openid not in _group_sub:
                await reply("本群尚未订阅。")
                return
            t = _group_tasks.pop(group_openid, None)
            if t:
                t.cancel()
            _group_sub.pop(group_openid)
            await reply("已取消订阅。")

        else:
            result = handle_command(cmd)
            await reply(result or HELP_TEXT)

    async def _group_push(self, group_openid: str, message: GroupMessage):
        try:
            while True:
                await asyncio.sleep(PUSH_INTERVAL)
                if group_openid not in _group_sub:
                    break
                content = get_push_content()
                _log.info(f"[群推送] -> group={group_openid}")
                try:
                    await message._api.post_group_message(
                        group_openid=group_openid, msg_type=0,
                        msg_id=_group_sub.get(group_openid, message.id),
                        content=content,
                    )
                except Exception as e:
                    _log.error(f"[群推送] 失败: {e}")
        except asyncio.CancelledError:
            pass


# ──────────────────────────────────────────────
# 启动入口
# ──────────────────────────────────────────────
def main():
    # Python 3.10+ 必须显式创建 event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    config = read(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
    intents = botpy.Intents(public_guild_messages=True, public_messages=True)
    client = MyBot(intents=intents)
    client.run(appid=config["appid"], secret=config["secret"])


if __name__ == "__main__":
    main()
