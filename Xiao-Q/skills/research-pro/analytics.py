#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ResearchPro 数据分析模块 - PostHog 异步集成
优化点：
1. 采用后台线程异步发送，确保零阻塞。
2. 增强隐私脱敏逻辑，自动过滤敏感查询词。
3. 彻底静默的错误处理，不产生任何控制台输出。
"""

import os
import platform
import uuid
import threading
import hashlib

try:
    import posthog
    _HAS_POSTHOG = True
except ImportError:
    _HAS_POSTHOG = False

# 配置 - 强制从环境变量读取，禁止硬编码
POSTHOG_API_KEY = os.getenv("RESEARCHPRO_POSTHOG_KEY")
POSTHOG_HOST = "https://us.i.posthog.com"

# 若环境变量未配置，直接禁用埋点
_HAS_POSTHOG = _HAS_POSTHOG and POSTHOG_API_KEY is not None

def _get_device_id():
    """生成一个匿名的设备 ID"""
    return str(uuid.getnode())

def _sanitize_query(query, max_len=10):
    """对查询关键词进行脱敏处理，仅保留哈希值和长度信息"""
    if not query:
        return ""
    return f"len:{len(query)}_hash:{hashlib.md5(query.encode()).hexdigest()[:8]}"

def _send_event(event_name, properties):
    """在后台线程中执行的实际发送逻辑"""
    if not _HAS_POSTHOG or not POSTHOG_API_KEY:
        return
    try:
        posthog.project_api_key = POSTHOG_API_KEY
        posthog.host = POSTHOG_HOST
        posthog.capture(
            distinct_id=_get_device_id(),
            event=event_name,
            properties=properties
        )
    except Exception:
        # 彻底静默，不打印任何错误
        pass

def track_event(event_name, properties=None):
    """
    非阻塞式事件追踪
    :param event_name: 事件名
    :param properties: 属性字典
    """
    base_props = {
        "os": platform.system(),
        "python_version": platform.python_version(),
        "app_version": "1.1.0"
    }
    if properties:
        # 如果包含 query 字段，自动进行脱敏处理
        if "query" in properties:
            properties["query_info"] = _sanitize_query(properties.pop("query"))
        base_props.update(properties)
    
    # 启动后台线程发送，完全不阻塞主程序
    t = threading.Thread(target=_send_event, args=(event_name, base_props), daemon=True)
    t.start()
